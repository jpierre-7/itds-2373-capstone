"""Review sentiment: sentence-level VADER scores per review (#6).

Owner: Leonardo (Market Intelligence & Visualization Analyst).

Each review is split into sentences, every sentence gets a VADER compound score (-1 to +1),
and the review's sentiment is the average over its sentences. Scoring a whole review at once
saturates: long texts pile up positive words and land near +1 regardless of the reviewer's opinion.
"""

import math
import re
from functools import cache
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from capstone.features import PRIOR_REVIEWS

# Review text has no line breaks, so sentences end at ., ! or ? followed by whitespace.
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
# About 1.6% of reviews barely use punctuation, so one "sentence" can be a whole review and saturate like
# whole-text scoring. Longer runs are cut into pieces of this many words (a typical sentence is ~18).
MAX_SENTENCE_WORDS = 40

# A review counts as positive at sentiment >= 0.12, not VADER's default 0.05. Tuned in
# notebooks/leonardo/01-sentiment.ipynb: it best separates reviews scored 7+ from those scored 4 or lower
# (balanced accuracy 0.80 vs 0.76), and cuts low-scored reviews called positive from 38% to 20%.
POSITIVE_CUTOFF = 0.12

# Part of the review-score cache's file name. Bump it after changing how a review is scored
# (split_sentences, review_sentiment) so every review is rescored. Cutoff or aggregation changes don't need it.
SCORING_VERSION = 1

SENTIMENT_COLUMNS = ["mean_review_sentiment", "adjusted_review_sentiment", "positive_review_share", "adjusted_positive_share"]


@cache
def _analyzer() -> SentimentIntensityAnalyzer:
    """One shared analyzer: building it loads VADER's word list, so do that once."""
    return SentimentIntensityAnalyzer()


def split_sentences(text: str) -> list[str]:
    """The non-blank sentences of a review, with run-ons over MAX_SENTENCE_WORDS cut into word chunks."""
    pieces = []
    for sentence in SENTENCE_END.split(text):
        words = sentence.split()
        pieces += [" ".join(words[i : i + MAX_SENTENCE_WORDS]) for i in range(0, len(words), MAX_SENTENCE_WORDS)]
    return pieces


def review_sentiment(text: str) -> float:
    """Average VADER compound score over a review's sentences, -1 (negative) to +1 (positive). NaN if no text."""
    sentences = split_sentences(text) if isinstance(text, str) else []
    if not sentences:
        return math.nan
    analyzer = _analyzer()
    return sum(analyzer.polarity_scores(s)["compound"] for s in sentences) / len(sentences)


def score_reviews(reviews: pd.DataFrame) -> pd.DataFrame:
    """One row per review: its uid, anime_uid and sentence-averaged sentiment. Slow: about 4-5 minutes on all reviews."""
    return pd.DataFrame({
        "uid": reviews["uid"].to_numpy(),
        "anime_uid": reviews["anime_uid"].to_numpy(),
        "sentiment": reviews["text"].map(review_sentiment).to_numpy(),
    })


def cached_review_sentiment(reviews: pd.DataFrame, cache_path: Path) -> pd.DataFrame:
    """score_reviews() output, reusing the scores saved in cache_path for reviews whose text is unchanged.

    Only new or edited reviews are scored (all of them on the first run, ~5 minutes), then the cache is updated.
    """
    current = reviews[["uid", "anime_uid", "text"]].assign(
        text_hash=pd.util.hash_pandas_object(reviews["text"], index=False).to_numpy()
    )
    saved = pd.read_parquet(cache_path) if cache_path.exists() else pd.DataFrame(
        {"uid": pd.Series(dtype=current["uid"].dtype), "text_hash": pd.Series(dtype="uint64"), "sentiment": pd.Series(dtype=float)}
    )
    merged = current.merge(saved[["uid", "text_hash", "sentiment"]], on=["uid", "text_hash"], how="left", indicator=True)

    # Rescore only reviews absent from the cache. A cached NaN (a review with no text) is a stored answer, not a gap.
    missing = merged["_merge"] == "left_only"
    if missing.any():
        merged.loc[missing, "sentiment"] = score_reviews(merged[missing])["sentiment"].to_numpy()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        merged[["uid", "anime_uid", "text_hash", "sentiment"]].to_parquet(cache_path, index=False)
    return merged[["uid", "anime_uid", "sentiment"]]


def sentiment_by_anime(scored: pd.DataFrame, cutoff: float = POSITIVE_CUTOFF, prior: int = PRIOR_REVIEWS) -> pd.DataFrame:
    """One row per reviewed anime (column uid) with its sentiment columns, from score_reviews() output.

    The adjusted columns blend each anime's value with `prior` imaginary reviews at the catalog-wide value,
    the same way adjusted_review_score does, so titles with only one or two reviews are pulled toward the average.
    """
    scored = scored.dropna(subset=["sentiment"]).assign(positive=lambda d: d["sentiment"] >= cutoff)
    per_anime = scored.groupby("anime_uid").agg(
        n=("sentiment", "size"),
        mean_review_sentiment=("sentiment", "mean"),
        positive_review_share=("positive", "mean"),
    )
    n = per_anime["n"]
    # Catalog values are taken over all reviews, matching adjusted_review_score's catalog mean.
    per_anime["adjusted_review_sentiment"] = _shrink(per_anime["mean_review_sentiment"], n, scored["sentiment"].mean(), prior)
    per_anime["adjusted_positive_share"] = _shrink(per_anime["positive_review_share"], n, scored["positive"].mean(), prior)
    return per_anime.rename_axis("uid").reset_index()[["uid", *SENTIMENT_COLUMNS]]


def add_sentiment(anime: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    """The anime table plus the sentiment columns. Anime with no reviews get blanks (NaN), not a neutral 0."""
    return anime.merge(sentiment_by_anime(scored), on="uid", how="left")


def _shrink(value: pd.Series, n: pd.Series, catalog_value: float, prior: int) -> pd.Series:
    """(n * value + prior * catalog_value) / (n + prior)."""
    return (n * value + prior * catalog_value) / (n + prior)

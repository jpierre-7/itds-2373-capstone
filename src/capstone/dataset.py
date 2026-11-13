"""Build and load the team's cleaned datasets in data/processed/."""

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from capstone.clean import build_anime_table, clean_animes, clean_reviews
from capstone.data import RAW_DIR, fetch_raw_data
from capstone.features import add_features
from capstone.sentiment import SCORING_VERSION, add_sentiment, cached_review_sentiment

PROCESSED_DIR = RAW_DIR.parent / "processed"
ANIME_PATH = PROCESSED_DIR / "anime.parquet"
REVIEWS_PATH = PROCESSED_DIR / "reviews.parquet"
# Per-review sentiment scores. Scoring every review takes ~5 minutes, so rebuilds reuse this file.
SENTIMENT_CACHE = PROCESSED_DIR / f"review_sentiment_v{SCORING_VERSION}.parquet"
# The code that produces the tables: a change to any of it makes the built files out of date.
SOURCES = sorted(Path(__file__).parent.glob("*.py"))


def build_dataset() -> dict[str, tuple[int, int]]:
    """Clean the raw files and write anime.parquet and reviews.parquet. Returns {table: (raw rows, clean rows)}."""
    fetch_raw_data()
    raw_animes = pd.read_csv(RAW_DIR / "animes.csv")
    raw_reviews = pd.read_csv(RAW_DIR / "reviews.csv")
    profiles = pd.read_csv(RAW_DIR / "profiles.csv")

    reviews = clean_reviews(raw_reviews)
    anime = add_features(build_anime_table(clean_animes(raw_animes), reviews, profiles))
    anime = add_sentiment(anime, cached_review_sentiment(reviews, SENTIMENT_CACHE))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    anime.to_parquet(ANIME_PATH, index=False)
    reviews.to_parquet(REVIEWS_PATH, index=False)
    return {"anime": (len(raw_animes), len(anime)), "reviews": (len(raw_reviews), len(reviews))}


def needs_rebuild(output: Path, sources: Iterable[Path]) -> bool:
    """True if output doesn't exist or is older than any of the code that builds it."""
    return not output.exists() or output.stat().st_mtime < max(s.stat().st_mtime for s in sources)


def load_anime() -> pd.DataFrame:
    """The cleaned one-row-per-anime table, (re)built first if missing or older than the code."""
    if needs_rebuild(ANIME_PATH, SOURCES):
        build_dataset()
    return pd.read_parquet(ANIME_PATH)


def load_reviews() -> pd.DataFrame:
    """The cleaned one-row-per-review table, (re)built first if missing or older than the code."""
    if needs_rebuild(REVIEWS_PATH, SOURCES):
        build_dataset()
    return pd.read_parquet(REVIEWS_PATH)


def main() -> None:
    for table, (raw_rows, clean_rows) in build_dataset().items():
        print(f"{table}: {raw_rows:,} raw rows -> {clean_rows:,} clean rows")
    for path in (ANIME_PATH, REVIEWS_PATH):
        print(f"{path}  ({path.stat().st_size / 1e6:.1f} MB)")

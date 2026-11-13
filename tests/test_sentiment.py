import math

import pandas as pd
import pytest

from capstone.sentiment import (
    MAX_SENTENCE_WORDS,
    SENTIMENT_COLUMNS,
    add_sentiment,
    cached_review_sentiment,
    review_sentiment,
    score_reviews,
    sentiment_by_anime,
    split_sentences,
)


def test_split_sentences_breaks_on_end_punctuation():
    assert split_sentences("Great show. Loved it!  Would I rewatch? Yes") == [
        "Great show.", "Loved it!", "Would I rewatch?", "Yes",
    ]


def test_split_sentences_keeps_decimals_and_ratings_together():
    assert split_sentences("Story 7/10 was fine. I give it 8.5 overall.") == ["Story 7/10 was fine.", "I give it 8.5 overall."]


def test_split_sentences_cuts_unpunctuated_run_ons_into_word_chunks():
    run_on = " ".join(f"w{i}" for i in range(MAX_SENTENCE_WORDS * 2 + 5))
    pieces = split_sentences(run_on + ". Short one.")

    assert [len(p.split()) for p in pieces] == [MAX_SENTENCE_WORDS, MAX_SENTENCE_WORDS, 5, 2]


def test_review_sentiment_is_the_average_over_sentences():
    one_good, one_bad = review_sentiment("I loved it."), review_sentiment("I hated it.")
    assert one_good > 0 > one_bad
    assert review_sentiment("I loved it. I hated it.") == pytest.approx((one_good + one_bad) / 2)


def test_long_praise_does_not_saturate_like_whole_text_scoring():
    # Many mildly positive sentences: whole-text VADER would push this to ~1, the sentence average stays moderate.
    text = " ".join(["The animation was good."] * 30)
    assert review_sentiment(text) == pytest.approx(review_sentiment("The animation was good."))


@pytest.mark.parametrize("text", ["", "   ", None])
def test_review_sentiment_is_blank_without_text(text):
    assert math.isnan(review_sentiment(text))


def test_score_reviews_returns_one_row_per_review():
    reviews = pd.DataFrame({"uid": [1, 2], "anime_uid": [10, 10], "text": ["Amazing!", "Terrible."], "score": [9, 2]})
    scored = score_reviews(reviews)

    assert scored.columns.tolist() == ["uid", "anime_uid", "sentiment"]
    assert scored["uid"].tolist() == [1, 2]
    assert scored.loc[0, "sentiment"] > 0 > scored.loc[1, "sentiment"]


def scored(*rows):
    """score_reviews() output from (anime_uid, sentiment) pairs."""
    return pd.DataFrame([{"uid": i, "anime_uid": a, "sentiment": s} for i, (a, s) in enumerate(rows)])


def test_sentiment_by_anime_raw_mean_and_positive_share():
    table = sentiment_by_anime(scored((1, 0.5), (1, 0.1), (1, 0.3), (2, -0.2)), cutoff=0.2).set_index("uid")

    assert table.loc[1, "mean_review_sentiment"] == pytest.approx(0.3)
    assert table.loc[1, "positive_review_share"] == pytest.approx(2 / 3)  # 0.5 and 0.3 are >= 0.2
    assert table.loc[2, "positive_review_share"] == 0


def test_cutoff_is_inclusive():
    table = sentiment_by_anime(scored((1, 0.2)), cutoff=0.2)
    assert table.loc[0, "positive_review_share"] == 1


def test_adjusted_columns_shrink_toward_the_catalog_over_all_reviews():
    table = sentiment_by_anime(scored((1, 0.9), (2, 0.1), (2, 0.1), (2, 0.1), (2, 0.1)), cutoff=0.5, prior=5).set_index("uid")

    # catalog mean over all 5 reviews = (0.9 + 4 * 0.1) / 5 = 0.26; catalog positive share = 1 / 5
    assert table.loc[1, "adjusted_review_sentiment"] == pytest.approx((0.9 + 5 * 0.26) / 6)
    assert table.loc[2, "adjusted_review_sentiment"] == pytest.approx((4 * 0.1 + 5 * 0.26) / 9)
    # one positive review is 100% raw, but only (1 + 5 * 0.2) / 6 = 33% adjusted
    assert table.loc[1, "adjusted_positive_share"] == pytest.approx((1 + 5 * 0.2) / 6)
    assert table.loc[2, "adjusted_positive_share"] == pytest.approx((0 + 5 * 0.2) / 9)


def test_reviews_without_a_score_are_ignored():
    table = sentiment_by_anime(scored((1, 0.4), (1, math.nan)), cutoff=0.2, prior=0)
    assert table.loc[0, "mean_review_sentiment"] == pytest.approx(0.4)
    assert table.loc[0, "positive_review_share"] == 1


def test_add_sentiment_leaves_anime_without_reviews_blank():
    anime = pd.DataFrame({"uid": [1, 2, 3], "title": ["A", "B", "C"]})
    table = add_sentiment(anime, scored((1, 0.5), (3, -0.5))).set_index("uid")

    assert len(table) == 3
    assert table.loc[2, SENTIMENT_COLUMNS].isna().all()  # no reviews: blank, not neutral 0
    assert table.loc[[1, 3], SENTIMENT_COLUMNS].notna().all().all()


def test_cached_review_sentiment_only_scores_new_or_edited_reviews(tmp_path, monkeypatch):
    import capstone.sentiment as sentiment

    cache = tmp_path / "review_sentiment.parquet"
    reviews = pd.DataFrame({"uid": [1, 2], "anime_uid": [10, 20], "text": ["Amazing!", "Terrible."]})
    first = cached_review_sentiment(reviews, cache)
    assert cache.exists()

    scored_texts = []
    real_score_reviews = sentiment.score_reviews
    monkeypatch.setattr(sentiment, "score_reviews", lambda r: scored_texts.extend(r["text"]) or real_score_reviews(r))

    assert cached_review_sentiment(reviews, cache).equals(first)
    assert scored_texts == []  # nothing changed: everything comes from the cache

    edited = pd.DataFrame({"uid": [1, 2, 3], "anime_uid": [10, 20, 30], "text": ["Amazing!", "Wonderful!", "Boring."]})
    again = cached_review_sentiment(edited, cache)
    assert scored_texts == ["Wonderful!", "Boring."]  # review 2 was edited, review 3 is new
    assert again["uid"].tolist() == [1, 2, 3]
    assert again.loc[1, "sentiment"] > 0 > again.loc[2, "sentiment"]


def test_cached_review_sentiment_does_not_rescore_reviews_without_text(tmp_path, monkeypatch):
    import capstone.sentiment as sentiment

    cache = tmp_path / "review_sentiment.parquet"
    reviews = pd.DataFrame({"uid": [1, 2], "anime_uid": [10, 20], "text": ["Amazing!", ""]})
    first = cached_review_sentiment(reviews, cache)
    assert math.isnan(first.loc[1, "sentiment"])  # no text: scored once, as blank

    def fail(_):
        raise AssertionError("a cached review was scored again")

    monkeypatch.setattr(sentiment, "score_reviews", fail)
    written = cache.stat().st_mtime_ns
    again = cached_review_sentiment(reviews, cache)

    assert again.equals(first)
    assert cache.stat().st_mtime_ns == written  # cache not rewritten

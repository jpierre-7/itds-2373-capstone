from datetime import date

import pandas as pd
import pytest

from capstone.clean import build_anime_table, clean_animes, clean_reviews, parse_aired


def raw_anime(uid, members=100, popularity=50, **overrides):
    """One row shaped like animes.csv."""
    row = {
        "uid": uid, "title": f"Anime {uid}", "synopsis": "A story.",
        "genre": "['Action', 'Comedy']", "aired": "Apr 6, 2019 to Jun 22, 2019",
        "episodes": 12.0, "members": members, "popularity": popularity,
        "ranked": 10.0, "score": 7.5, "img_url": "https://img", "link": f"https://myanimelist.net/anime/{uid}",
    }
    return row | overrides


SCORES = "{'Overall': '8', 'Story': '7', 'Animation': '9', 'Sound': '10', 'Character': '6', 'Enjoyment': '8'}"


def raw_review(uid, anime_uid=1, score=8, scores=SCORES, body="Great show.", **overrides):
    """One row shaped like reviews.csv, including the scraped page boilerplate around the text."""
    text = (
        "\n           \n         more pics \n         \n           Overall \n           8 \n"
        "           Story \n           7 \n             Animation \n             9 \n"
        "             Sound \n             10 \n             Character \n             6 \n"
        f"             Enjoyment \n             8 \n   {body}\n\n          \n       Helpful \n   \n      "
    )
    row = {
        "uid": uid, "profile": "someone", "anime_uid": anime_uid, "text": text,
        "score": score, "scores": scores, "link": f"https://myanimelist.net/reviews.php?id={uid}",
    }
    return row | overrides


def test_parse_aired_full_date_range():
    aired = parse_aired("Oct 4, 2015 to Mar 27, 2016")

    assert (aired.start, aired.end, aired.airing) == (date(2015, 10, 4), date(2016, 3, 27), False)


def test_parse_aired_single_date_is_both_start_and_end():
    aired = parse_aired("Jul 20, 2001")

    assert (aired.start, aired.end, aired.airing) == (date(2001, 7, 20), date(2001, 7, 20), False)


def test_parse_aired_open_range_is_still_airing():
    aired = parse_aired("Oct 12, 2019 to ?")

    assert (aired.start, aired.end, aired.airing) == (date(2019, 10, 12), None, True)


@pytest.mark.parametrize(
    ("text", "start", "end"),
    [
        ("Apr, 2010", date(2010, 4, 1), date(2010, 4, 30)),
        ("2007 to 2013", date(2007, 1, 1), date(2013, 12, 31)),
        ("Feb 18, 2008 to 2009", date(2008, 2, 18), date(2009, 12, 31)),
        ("Jul 5, 1992 to 1992", date(1992, 7, 5), date(1992, 12, 31)),
    ],
)
def test_parse_aired_partial_dates_span_their_whole_period(text, start, end):
    aired = parse_aired(text)

    assert (aired.start, aired.end) == (start, end)


def test_parse_aired_drops_an_end_date_before_the_start():
    aired = parse_aired("Sep 3, 1981 to Jul 15, 1981")  # a data-entry error on MyAnimeList

    assert (aired.start, aired.end) == (date(1981, 9, 3), None)


def test_parse_aired_not_available_has_no_dates():
    aired = parse_aired("Not available")

    assert (aired.start, aired.end, aired.airing) == (None, None, False)


def test_clean_animes_keeps_one_row_per_anime_preferring_most_members():
    raw = pd.DataFrame([
        raw_anime(1, members=100, popularity=50),
        raw_anime(1, members=100, popularity=50),  # exact duplicate
        raw_anime(1, members=120, popularity=48),  # later snapshot, more members
        raw_anime(2, members=10, popularity=900),
    ])

    animes = clean_animes(raw)

    assert sorted(animes["uid"]) == [1, 2]
    assert animes.set_index("uid").loc[1, ["members", "popularity"]].tolist() == [120, 48]


def test_clean_animes_splits_aired_into_date_columns():
    raw = pd.DataFrame([
        raw_anime(1, aired="Oct 4, 2015 to Mar 27, 2016"),
        raw_anime(2, aired="Dec 1, 2018 to ?"),
        raw_anime(3, aired="Not available"),
    ])

    animes = clean_animes(raw).set_index("uid")

    assert "aired" not in animes.columns
    assert animes.loc[1, "start_date"] == pd.Timestamp("2015-10-04")
    assert animes.loc[1, "end_date"] == pd.Timestamp("2016-03-27")
    assert animes["start_year"].tolist() == [2015, 2018, pd.NA]
    assert animes["is_airing"].tolist() == [False, True, False]
    assert pd.isna(animes.loc[2, "end_date"]) and pd.isna(animes.loc[3, "start_date"])


def test_clean_animes_parses_genre_lists():
    raw = pd.DataFrame([raw_anime(1, genre="['Action', 'Comedy']"), raw_anime(2, genre="[]")])

    animes = clean_animes(raw).set_index("uid")

    assert animes.loc[1, "genre"] == ["Action", "Comedy"]
    assert animes.loc[2, "genre"] == []


def test_clean_animes_keeps_missing_episodes_blank():
    raw = pd.DataFrame([raw_anime(1, episodes=25.0), raw_anime(2, episodes=float("nan"))])

    animes = clean_animes(raw)

    assert str(animes["episodes"].dtype) == "Int64"
    assert animes["episodes"].tolist() == [25, pd.NA]


def test_clean_reviews_strips_page_boilerplate_from_text():
    raw = pd.DataFrame([raw_review(1, body="Loved it.\r\n \r\nThe ending   was perfect.")])

    reviews = clean_reviews(raw)

    assert reviews.loc[0, "text"] == "Loved it. The ending was perfect."


def test_clean_reviews_drops_duplicates_and_out_of_range_scores():
    zeros = "{'Overall': '0', 'Story': '0', 'Animation': '0', 'Sound': '0', 'Character': '0', 'Enjoyment': '0'}"
    elevens = zeros.replace("'0'", "'11'")
    raw = pd.DataFrame([
        raw_review(1, score=8),
        raw_review(1, score=8),  # exact duplicate
        raw_review(2, score=1),
        raw_review(3, score=10),
        raw_review(4, score=0, scores=zeros),
        raw_review(5, score=11, scores=elevens),
    ])

    reviews = clean_reviews(raw)

    assert sorted(reviews["uid"]) == [1, 2, 3]


def test_clean_reviews_splits_sub_scores_into_columns():
    reviews = clean_reviews(pd.DataFrame([raw_review(1, score=8, scores=SCORES)]))

    sub = ["story_score", "animation_score", "sound_score", "character_score", "enjoyment_score"]
    assert "scores" not in reviews.columns
    assert reviews.loc[0, sub].tolist() == [7, 9, 10, 6, 8]
    assert reviews.loc[0, "score"] == 8


def raw_profile(profile, favorites="[]"):
    return {"profile": profile, "gender": "Female", "birthday": "Oct 2, 1994",
            "favorites_anime": favorites, "link": f"https://myanimelist.net/profile/{profile}"}


NO_PROFILES = pd.DataFrame([raw_profile("someone")])


def test_build_anime_table_adds_review_aggregates_and_keeps_unreviewed_anime():
    animes = clean_animes(pd.DataFrame([raw_anime(1), raw_anime(2)]))
    reviews = clean_reviews(pd.DataFrame([
        raw_review(10, anime_uid=1, score=6),
        raw_review(11, anime_uid=1, score=9),
    ]))

    table = build_anime_table(animes, reviews, NO_PROFILES).set_index("uid")

    assert len(table) == 2
    assert table.loc[1, "n_reviews"] == 2
    assert table.loc[1, "mean_review_score"] == 7.5
    assert table.loc[1, "mean_story_score"] == 7.0  # both fixture reviews give Story 7
    assert table.loc[2, "n_reviews"] == 0
    assert pd.isna(table.loc[2, "mean_review_score"])


def test_build_anime_table_counts_favorites_once_per_profile():
    animes = clean_animes(pd.DataFrame([raw_anime(1), raw_anime(2), raw_anime(3)]))
    reviews = clean_reviews(pd.DataFrame([raw_review(10, anime_uid=1)]))
    profiles = pd.DataFrame([
        raw_profile("ana", favorites="['1']"),
        raw_profile("ana", favorites="['1', '2']"),  # later scrape of ana: longer list wins
        raw_profile("ana", favorites="['1', '2']"),  # exact duplicate
        raw_profile("ben", favorites="['1', '999']"),  # 999 is not in the anime table
    ])

    table = build_anime_table(animes, reviews, profiles).set_index("uid")

    assert table["n_favorites"].to_dict() == {1: 2, 2: 1, 3: 0}


def test_clean_reviews_treats_zero_sub_scores_as_not_rated():
    partly_rated = "{'Overall': '8', 'Story': '7', 'Animation': '0', 'Sound': '0', 'Character': '6', 'Enjoyment': '9'}"

    reviews = clean_reviews(pd.DataFrame([raw_review(1, score=8, scores=partly_rated)]))

    assert reviews.loc[0, ["story_score", "animation_score", "sound_score"]].tolist() == [7, pd.NA, pd.NA]


def test_clean_animes_drops_repeated_genre_tags():
    raw = pd.DataFrame([raw_anime(1, genre="['Hentai', 'Hentai', 'School', 'School']")])  # as scraped for uid 5154

    assert clean_animes(raw).loc[0, "genre"] == ["Hentai", "School"]

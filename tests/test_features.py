import pandas as pd
import pytest

from capstone.features import add_features, franchise_root


def anime(uid, title=None, members=1000, genre=("Action",), start: str | None = "2015-04-01", n_reviews=0, mean_review_score=None):
    """One row shaped like the cleaned anime table, with only the columns the features use."""
    return {
        "uid": uid, "title": title or f"Anime {uid}", "members": members, "genre": list(genre),
        "start_date": pd.Timestamp(start) if start else pd.NaT,
        "n_reviews": n_reviews, "mean_review_score": mean_review_score,
    }


@pytest.mark.parametrize(
    ("title", "root"),
    [
        ("Shingeki no Kyojin", "shingeki no kyojin"),
        ("Shingeki no Kyojin Season 2", "shingeki no kyojin"),
        ("Boku no Hero Academia 2nd Season", "boku no hero academia"),
        ("Sword Art Online II", "sword art online"),
        ("Code Geass: Hangyaku no Lelouch R2", "code geass"),
        ("Naruto: Shippuuden", "naruto"),
        ("Hunter x Hunter (2011)", "hunter x hunter"),
        ("Steins;Gate Movie: Fuka Ryouiki no Déjà vu", "steins;gate"),
        ("Fairy Tail OVA", "fairy tail"),
        ("Haikyuu!! Second Season", "haikyuu!!"),
        ("Detective Conan (TV)", "detective conan"),
        ("Major S2", "major"),
        ("Taiho Shichau zo The Movie", "taiho shichau zo"),
        ("Shingeki no Kyojin Season 3 Part 2", "shingeki no kyojin"),
        ("Re:Zero kara Hajimeru Isekai Seikatsu", "re:zero kara hajimeru isekai seikatsu"),
    ],
)
def test_franchise_root_strips_sequel_and_subtitle_markers(title, root):
    assert franchise_root(title) == root


def test_popularity_index_is_the_members_percentile():
    table = add_features(pd.DataFrame([anime(1, members=10), anime(2, members=500), anime(3, members=20), anime(4, members=20)]))

    # share of the catalog with at most as many members, as 0-100
    assert table.set_index("uid")["popularity_index"].to_dict() == {1: 25.0, 2: 100.0, 3: 75.0, 4: 75.0}


def test_adjusted_review_score_pulls_few_reviews_toward_the_catalog_mean():
    table = add_features(pd.DataFrame([
        anime(1, n_reviews=1, mean_review_score=10.0),
        anime(2, n_reviews=4, mean_review_score=5.0),
        anime(3, n_reviews=0),
    ])).set_index("uid")

    # catalog mean over all 5 reviews = (10 + 4 * 5) / 5 = 6, weighted as 5 extra reviews
    assert table.loc[1, "adjusted_review_score"] == pytest.approx((10 + 5 * 6) / 6)
    assert table.loc[2, "adjusted_review_score"] == pytest.approx((4 * 5 + 5 * 6) / 9)
    assert pd.isna(table.loc[3, "adjusted_review_score"])  # no reviews stays "no data"


def test_genre_count_and_one_hot_flags():
    table = add_features(pd.DataFrame([
        anime(1, genre=["Action", "Slice of Life"]),
        anime(2, genre=["Sci-Fi"]),
        anime(3, genre=[]),
    ])).set_index("uid")

    assert table["genre_count"].to_dict() == {1: 2, 2: 1, 3: 0}
    flags = ["genre_action", "genre_sci_fi", "genre_slice_of_life"]
    assert sorted(c for c in table.columns if c.startswith("genre_") and c != "genre_count") == flags
    assert table[flags].to_numpy().tolist() == [
        [True, False, True],
        [False, True, False],
        [False, False, False],
    ]


def test_franchise_columns_group_titles_by_root():
    table = add_features(pd.DataFrame([
        anime(1, title="Shingeki no Kyojin", members=900, start="2013-04-07"),
        anime(2, title="Shingeki no Kyojin Season 2", members=500, start="2017-04-01"),
        anime(3, title="Shingeki no Kyojin Movie", members=100, start=None),  # no date: can't be the original
        anime(4, title="Kimi no Na wa.", members=800, start="2016-08-26"),
    ])).set_index("uid")

    assert table["franchise"].to_dict() == {1: "shingeki no kyojin", 2: "shingeki no kyojin", 3: "shingeki no kyojin", 4: "kimi no na wa."}
    assert table["franchise_size"].to_dict() == {1: 3, 2: 3, 3: 3, 4: 1}
    assert table["franchise_members"].to_dict() == {1: 1500, 2: 1500, 3: 1500, 4: 800}
    # the earliest-starting entry is the original; every other entry is a sequel or side story
    assert table["is_sequel"].to_dict() == {1: False, 2: True, 3: True, 4: False}

"""Engineered features on the cleaned anime table."""

import re

import pandas as pd

# Trailing markers that set a sequel, side story or remake apart from its franchise.
SEQUEL_MARKER = re.compile(
    r"\s+(Season \d+|(\d+(st|nd|rd|th)|Second|Third|Fourth|Fifth|Final) Season|Part \d+|S\d+|I{2,}|R2|\d+"
    r"|(The )?Movie|OVA|Specials?|TV)$"
)
EDITION_SUFFIX = re.compile(r"\s*\((\d{4}|TV)\)$")  # "Hunter x Hunter (2011)", "Detective Conan (TV)"

# How many catalog-average reviews an anime's mean review score is blended with (IMDb-style weighted rating).
PRIOR_REVIEWS = 5


def franchise_root(title: str) -> str:
    """The franchise a title belongs to: its title without the subtitle, year, "(TV)" or sequel markers."""
    root = EDITION_SUFFIX.sub("", title).split(": ")[0]
    while (stripped := SEQUEL_MARKER.sub("", root)) != root:
        root = stripped
    return root.strip().lower()


def add_features(anime: pd.DataFrame) -> pd.DataFrame:
    """The cleaned anime table plus the engineered features the clustering, modeling and ranking use."""
    table = anime.copy()
    # Share of the catalog with at most as many members, as 0-100.
    table["popularity_index"] = table["members"].rank(method="max", pct=True) * 100

    n, mean = table["n_reviews"], table["mean_review_score"]
    catalog_mean = (n * mean).sum() / max(n.sum(), 1)
    # mean_review_score is blank when there are no reviews, so the adjusted score stays blank too.
    table["adjusted_review_score"] = (n * mean + PRIOR_REVIEWS * catalog_mean) / (n + PRIOR_REVIEWS)

    table["genre_count"] = table["genre"].map(len)
    flags = pd.get_dummies(table.explode("genre")["genre"]).groupby(level=0).any()
    flags.columns = [_genre_column(g) for g in flags.columns]
    table = table.join(flags.reindex(table.index, fill_value=False))

    table["franchise"] = table["title"].map(franchise_root)
    franchises = table.groupby("franchise")
    table["franchise_size"] = franchises["uid"].transform("size")
    table["franchise_members"] = franchises["members"].transform("sum")
    # The earliest-starting entry is the original (undated entries last, ties by uid); the rest are sequels.
    by_start = table.sort_values(["start_date", "uid"], na_position="last")
    table["is_sequel"] = by_start["franchise"].duplicated().reindex(table.index)
    return table


def _genre_column(genre: str) -> str:
    """"Slice of Life" -> "genre_slice_of_life", "Sci-Fi" -> "genre_sci_fi"."""
    return "genre_" + re.sub(r"[^a-z0-9]+", "_", genre.lower())

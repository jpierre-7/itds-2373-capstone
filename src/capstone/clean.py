"""Clean the raw MyAnimeList files and merge them into one row per anime."""

import ast
import calendar
import re
from datetime import date, datetime
from typing import NamedTuple

import pandas as pd


class Aired(NamedTuple):
    start: date | None
    end: date | None
    airing: bool


def _parse_date(part: str, period_end: bool = False) -> date:
    """Parse "Oct 4, 2015", "Oct, 2015" or "2015". A partial date covers its whole month or
    year, so it resolves to the first day of that period, or the last when period_end is set."""
    for fmt, period in (("%b %d, %Y", "day"), ("%b, %Y", "month"), ("%Y", "year")):
        try:
            parsed = datetime.strptime(part, fmt).date()
        except ValueError:
            continue
        if period_end and period == "month":
            return parsed.replace(day=calendar.monthrange(parsed.year, parsed.month)[1])
        if period_end and period == "year":
            return parsed.replace(month=12, day=31)
        return parsed
    raise ValueError(f"Unrecognised aired date: {part!r}")


def parse_aired(text: str) -> Aired:
    if text == "Not available":
        return Aired(None, None, airing=False)
    start_text, _, end_text = text.partition(" to ")
    start = _parse_date(start_text)
    if end_text == "?":
        return Aired(start, None, airing=True)
    end = _parse_date(end_text or start_text, period_end=True)
    if end < start:  # data-entry error on MyAnimeList: keep the start, distrust the end
        end = None
    return Aired(start, end, airing=False)


def clean_animes(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per anime: where scrapes disagree, keep the copy with the most members."""
    animes = (
        raw.sort_values("members", ascending=False, kind="stable")
        .drop_duplicates(subset="uid")
        .sort_values("uid")
        .reset_index(drop=True)
    )

    animes["genre"] = animes["genre"].map(lambda text: list(dict.fromkeys(ast.literal_eval(text))))  # uid 5154 lists each tag twice
    animes["episodes"] = animes["episodes"].astype("Int64")

    aired = animes.pop("aired").map(parse_aired)
    animes["start_date"] = pd.to_datetime(aired.map(lambda a: a.start))
    animes["end_date"] = pd.to_datetime(aired.map(lambda a: a.end))
    animes["start_year"] = animes["start_date"].dt.year.astype("Int64")
    animes["is_airing"] = aired.map(lambda a: a.airing)
    return animes


# Every scraped review starts with "more pics" + the six sub-scores and ends with "Helpful".
REVIEW_HEADER = re.compile(
    r"^more pics Overall \d+ Story \d+ Animation \d+ Sound \d+ Character \d+ Enjoyment \d+ "
)
REVIEW_FOOTER = re.compile(r" ?Helpful$")
SUB_SCORES = ("Story", "Animation", "Sound", "Character", "Enjoyment")


def _review_body(text: str) -> str:
    collapsed = " ".join(text.split())
    return REVIEW_FOOTER.sub("", REVIEW_HEADER.sub("", collapsed))


def clean_reviews(raw: pd.DataFrame) -> pd.DataFrame:
    """One row per review, scores within MyAnimeList's 1-10 scale, text without page boilerplate."""
    reviews = raw.drop_duplicates(subset="uid")
    reviews = reviews.loc[reviews["score"].between(1, 10)].reset_index(drop=True)
    reviews["text"] = reviews["text"].map(_review_body)

    # 'Overall' always equals `score`, so only the five other sub-scores get columns.
    # A sub-score of 0 means the reviewer left that category unrated.
    sub_scores = pd.DataFrame(reviews.pop("scores").map(ast.literal_eval).tolist()).astype(int)
    sub_scores = sub_scores.astype("Int64").mask(sub_scores == 0)
    for name in SUB_SCORES:
        reviews[f"{name.lower()}_score"] = sub_scores[name]
    return reviews


def build_anime_table(animes: pd.DataFrame, reviews: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Merge review aggregates onto the cleaned anime, keeping anime that have no reviews."""
    sub_cols = [f"{name.lower()}_score" for name in SUB_SCORES]
    aggregates = reviews.groupby("anime_uid").agg(
        n_reviews=("uid", "size"),
        mean_review_score=("score", "mean"),
        **{f"mean_{col}": (col, "mean") for col in sub_cols},
    ).astype({f"mean_{col}": "float64" for col in sub_cols})  # plain floats, so scikit-learn accepts them

    table = animes.merge(aggregates, left_on="uid", right_index=True, how="left")
    table["n_reviews"] = table["n_reviews"].fillna(0).astype(int)

    favorites = _favorites_by_profile(profiles).explode().dropna().astype(int)
    table["n_favorites"] = favorites.value_counts().reindex(table["uid"], fill_value=0).to_numpy()
    return table


def _favorites_by_profile(profiles: pd.DataFrame) -> pd.Series:
    """Each profile's favorite anime IDs; where scrapes disagree, keep the longest list."""
    lists = profiles.set_index("profile")["favorites_anime"].map(ast.literal_eval)
    longest_first = lists.iloc[lists.map(len).argsort(kind="stable")[::-1]]
    return longest_first[~longest_first.index.duplicated()]

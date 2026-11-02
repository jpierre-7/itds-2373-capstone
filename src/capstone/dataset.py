"""Build and load the team's cleaned datasets in data/processed/."""

import pandas as pd

from capstone.clean import build_anime_table, clean_animes, clean_reviews
from capstone.data import RAW_DIR, fetch_raw_data

PROCESSED_DIR = RAW_DIR.parent / "processed"
ANIME_PATH = PROCESSED_DIR / "anime.parquet"
REVIEWS_PATH = PROCESSED_DIR / "reviews.parquet"


def build_dataset() -> dict[str, tuple[int, int]]:
    """Clean the raw files and write anime.parquet and reviews.parquet. Returns {table: (raw rows, clean rows)}."""
    fetch_raw_data()
    raw_animes = pd.read_csv(RAW_DIR / "animes.csv")
    raw_reviews = pd.read_csv(RAW_DIR / "reviews.csv")
    profiles = pd.read_csv(RAW_DIR / "profiles.csv")

    reviews = clean_reviews(raw_reviews)
    anime = build_anime_table(clean_animes(raw_animes), reviews, profiles)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    anime.to_parquet(ANIME_PATH, index=False)
    reviews.to_parquet(REVIEWS_PATH, index=False)
    return {"anime": (len(raw_animes), len(anime)), "reviews": (len(raw_reviews), len(reviews))}


def load_anime() -> pd.DataFrame:
    """The cleaned one-row-per-anime table, built first if it doesn't exist yet."""
    if not ANIME_PATH.exists():
        build_dataset()
    return pd.read_parquet(ANIME_PATH)


def load_reviews() -> pd.DataFrame:
    """The cleaned one-row-per-review table, built first if it doesn't exist yet."""
    if not REVIEWS_PATH.exists():
        build_dataset()
    return pd.read_parquet(REVIEWS_PATH)


def main() -> None:
    for table, (raw_rows, clean_rows) in build_dataset().items():
        print(f"{table}: {raw_rows:,} raw rows -> {clean_rows:,} clean rows")
    for path in (ANIME_PATH, REVIEWS_PATH):
        print(f"{path}  ({path.stat().st_size / 1e6:.1f} MB)")

"""Fetch the MyAnimeList Kaggle dataset into data/raw/."""

import shutil
from collections.abc import Callable
from pathlib import Path

# Pinned so every teammate gets identical data even if the author republishes.
KAGGLE_DATASET = "marlesson/myanimelist-dataset-animes-profiles-reviews/versions/1"
RAW_FILES = ("animes.csv", "profiles.csv", "reviews.csv")
RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def download_from_kaggle() -> Path:
    import kagglehub

    return Path(kagglehub.dataset_download(KAGGLE_DATASET))


def fetch_raw_data(dest: Path = RAW_DIR, download: Callable[[], Path] = download_from_kaggle) -> list[Path]:
    """Copy the raw CSVs into dest, downloading only if any are missing."""
    dest_paths = [dest / name for name in RAW_FILES]
    if all(p.exists() for p in dest_paths):
        return dest_paths

    src = download()
    missing = [name for name in RAW_FILES if not (src / name).exists()]
    if missing:
        raise FileNotFoundError(f"Download from {src} is missing: {', '.join(missing)}")

    dest.mkdir(parents=True, exist_ok=True)
    return [Path(shutil.copy2(src / name, dest / name)) for name in RAW_FILES]


def main() -> None:
    for path in fetch_raw_data():
        print(f"{path}  ({path.stat().st_size / 1e6:.1f} MB)")

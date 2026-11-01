from pathlib import Path

import pytest

from capstone.data import fetch_raw_data


def fake_download(tmp_path: Path, files=("animes.csv", "profiles.csv", "reviews.csv")):
    """Stand-in for the Kaggle download: a directory holding the given CSVs."""
    src = tmp_path / "kaggle-cache"
    src.mkdir()
    for name in files:
        (src / name).write_text(f"contents of {name}\n")
    return lambda: src


def test_copies_the_three_csvs_into_dest(tmp_path):
    dest = tmp_path / "raw"

    paths = fetch_raw_data(dest, download=fake_download(tmp_path))

    assert sorted(p.name for p in paths) == ["animes.csv", "profiles.csv", "reviews.csv"]
    assert (dest / "reviews.csv").read_text() == "contents of reviews.csv\n"


def test_skips_download_when_files_already_present(tmp_path):
    dest = tmp_path / "raw"
    fetch_raw_data(dest, download=fake_download(tmp_path))

    def must_not_download():
        raise AssertionError("downloaded again")

    paths = fetch_raw_data(dest, download=must_not_download)

    assert sorted(p.name for p in paths) == ["animes.csv", "profiles.csv", "reviews.csv"]


def test_names_missing_files_when_download_is_incomplete(tmp_path):
    dest = tmp_path / "raw"
    download = fake_download(tmp_path, files=("animes.csv",))

    with pytest.raises(FileNotFoundError, match=r"profiles\.csv.*reviews\.csv"):
        fetch_raw_data(dest, download=download)

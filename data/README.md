# data/

Everything in this folder except this README is gitignored. Do not commit data files.

- `raw/`: the three MyAnimeList CSVs (`animes.csv`, `profiles.csv`, `reviews.csv`), exactly as Kaggle ships them. Get them with `uv run download-data`, and treat them as read-only.
- `processed/`: the cleaned tables `anime.parquet` and `reviews.parquet`. Build them with `uv run build-dataset`, or let `load_anime()` / `load_reviews()` build them on first use. Never edit them by hand; change the cleaning code and rebuild instead.

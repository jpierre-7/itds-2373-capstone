# data/

Everything in this folder except this README is gitignored. Do not commit data files.

- `raw/`: the three MyAnimeList CSVs (`animes.csv`, `profiles.csv`, `reviews.csv`), exactly as Kaggle ships them. Get them with `uv run download-data`, and treat them as read-only.

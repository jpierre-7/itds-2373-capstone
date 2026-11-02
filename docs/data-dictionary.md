# Data dictionary

Source: Kaggle [`marlesson/myanimelist-dataset-animes-profiles-reviews`](https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews), version 1, fetched with `uv run download-data`. All figures come from `notebooks/john/01-data-dictionary.ipynb`.

**% Missing is measured after removing duplicate keys** (one row per anime, profile, or review). The raw files contain many duplicate rows; see [Data-quality notes](#data-quality-notes).

## How the files relate

```
profiles.profile ──< reviews.profile      (one profile writes many reviews)
animes.uid       ──< reviews.anime_uid    (one anime receives many reviews)
animes.uid       ──< profiles.favorites_anime   (list of anime IDs stored as text)
```

| Relationship | References (de-duplicated) | Resolve to a record |
|---|---|---|
| `reviews.anime_uid` → `animes.uid` | 130,519 | 100% |
| `reviews.profile` → `profiles.profile` | 130,519 | 100% |
| `profiles.favorites_anime` → `animes.uid` | 216,695 | 99.82% (34 distinct IDs unresolved) |

## `animes.csv`

19,311 rows; **16,216 unique anime**. Key: `uid`.

| Column | Type | % Missing | Example | Meaning |
|---|---|---|---|---|
| `uid` | int | 0 | 28891 | MyAnimeList anime ID. Primary key; matches the ID in `link`. |
| `title` | text | 0 | Haikyuu!! Second Season | Romanized title as listed on MyAnimeList. Not unique: two titles ("Hinamatsuri", "Youkoso! Ecolo Shima") belong to two different `uid`s each, so join on `uid`, never on title. Sequels and seasons are separate entries. |
| `synopsis` | text | 4.71 | Following their participation at the Inter-High, the Karasuno… | Plot summary from the anime's MyAnimeList page. |
| `genre` | text (list) | 0 | ['Comedy', 'Sports', 'Drama', 'School', 'Shounen'] | Genre tags, stored as a Python list written as text. 43 distinct genres; 0–13 per anime (mean 2.9); 82 anime have an empty list. Includes demographic tags such as Shounen and Seinen. |
| `aired` | text | 0 | Oct 4, 2015 to Mar 27, 2016 | Airing date or date range as free text. Formats vary: a single date, a range, a year only, an open range ending in "to ?" (still airing at scrape time), or "Not available" (273 anime). |
| `episodes` | number | 3.03 | 25 | Number of episodes. 1 for movies and one-shot specials. Missing mostly for shows still airing (73% of missing rows have an open-ended `aired`). Ranges up to 3,057 for long-running children's and educational shows. |
| `members` | int | 0 | 489,888 | Number of MyAnimeList users who added the anime to their list (any status). This is the platform's measure of audience size. |
| `popularity` | int | 0 | 141 | Popularity **rank** by `members`: 1 is the most-listed anime (Death Note, 1.87M members). Lower is more popular. Almost exactly the reverse ordering of `members` (Spearman ρ = −0.998). |
| `ranked` | number | 10.26 | 25 | Rank by `score`: 1 is the highest-rated (Fullmetal Alchemist: Brotherhood). Lower is better. Missing for 1,663 anime, including 1,322 that do have a score. The dataset does not record why MyAnimeList leaves a title unranked. |
| `score` | number | 2.10 | 8.82 | MyAnimeList's average user rating on a 1–10 scale (observed 1.25–9.23). Missing where the anime has no score. |
| `img_url` | text | 1.02 | https://cdn.myanimelist.net/images/anime/9/76662.jpg | Cover image URL. Not used in analysis. |
| `link` | text | 0 | https://myanimelist.net/anime/28891/Haikyuu_Second_Season | MyAnimeList page URL. |

## `profiles.csv`

81,727 rows; **47,885 unique profiles**. Key: `profile`.

Every profile in this file has written at least one review. It is the set of **reviewers**, not a sample of all MyAnimeList users.

| Column | Type | % Missing | Example | Meaning |
|---|---|---|---|---|
| `profile` | text | 0 | DesolatePsyche | MyAnimeList username. Primary key; joins to `reviews.profile`. |
| `gender` | text | 35.52 | Male | Self-reported gender: Male, Female, or Non-Binary. Optional on MyAnimeList, so often blank. |
| `birthday` | text | 43.93 | Oct 2, 1994 | Self-reported birthday as free text. Often partial: month and day without a year, a year alone, or a month alone. |
| `favorites_anime` | text (list) | 0 | ['33352', '25013', '5530', …] | The user's favorited anime, as a list of anime IDs (as strings) written as text. Joins to `animes.uid`. 10,422 profiles have an empty list. |
| `link` | text | 0 | https://myanimelist.net/profile/DesolatePsyche | Profile page URL. |

## `reviews.csv`

192,112 rows; **130,519 unique reviews**. Key: `uid`.

| Column | Type | % Missing | Example | Meaning |
|---|---|---|---|---|
| `uid` | int | 0 | 255938 | MyAnimeList review ID. Primary key; matches the ID in `link`. |
| `profile` | text | 0 | DesolatePsyche | Username of the reviewer. Joins to `profiles.profile`. |
| `anime_uid` | int | 0 | 34096 | ID of the anime being reviewed. Joins to `animes.uid`. |
| `text` | text | 0 | more pics Overall 8 Story 8 Animation 8 … | Full review text as scraped. Every review starts with page boilerplate ("more pics" followed by the six sub-scores) and ends with the word "Helpful". Both must be stripped before text analysis. Median length 360 words. |
| `score` | int | 0 | 8 | The reviewer's overall rating, nominally 1–10. Identical to `scores['Overall']` in 100% of rows. |
| `scores` | text (dict) | 0 | {'Overall': '8', 'Story': '8', 'Animation': '8', 'Sound': '10', 'Character': '9', 'Enjoyment': '8'} | The reviewer's six sub-ratings (Overall, Story, Animation, Sound, Character, Enjoyment), stored as a Python dict of strings written as text. Every review has all six keys. |
| `link` | text | 0 | https://myanimelist.net/reviews.php?id=255938 | Review page URL. |

## Data-quality notes

Findings for the cleaning step (#4). Each note states what was measured and what cleaning has to decide.

1. **Heavy duplication.** Exact duplicate rows: 2,943 in `animes` (15%), 33,825 in `profiles` (41%), 61,593 in `reviews` (32%). Every figure in the analysis must be computed after de-duplication, or counts like "reviews per anime" will be inflated.
2. **Conflicting copies of the same anime.** 152 anime IDs have copies that differ. The differences are in `members` (138 IDs), `popularity` (53), and `ranked` (10), consistent with the same page scraped on different dates. *Decision for #4:* which copy to keep. Keeping the highest `members` value is the natural "latest snapshot" choice. 17 profiles also have conflicting copies. All 17 differ in `favorites_anime`, and one also differs in `birthday`.
3. **Review coverage is thin and uneven.** Only 8,113 of 16,216 anime (50%) have any reviews. Among those, the median is 3 reviews and the maximum is 1,292. Any review-based metric (sentiment, average review score) is missing for half the catalog and unreliable for titles with very few reviews. *Decision for #4/#6:* a minimum review count before a review-based metric is trusted.
4. **Out-of-range review scores.** One review (uid 6424) has every score set to 0, and one (uid 252847) has every score set to 11. All other reviews are 1–10. Treat both as invalid.
5. **Missing anime fields.** `ranked` 10.26%, `synopsis` 4.71%, `episodes` 3.03%, `score` 2.10%. `score` and `ranked` are core success measures. *Decision for #4:* drop, impute, or flag these rows. Imputing a success measure would bias the analysis, so dropping or flagging is safer.
6. **Unranked titles that have a score.** 1,322 anime have a `score` but no `ranked`, so `ranked` cannot stand in for `score`. Use `score` as the rating measure.
7. **Fields stored as text.** `genre` and `favorites_anime` are lists, `scores` is a dict, and `aired` is a free-text date range. All need parsing. `aired` needs a parser that handles single dates, ranges, year-only values, "to ?", and "Not available". Extracting a start year works for 98.3% of anime.
8. **Review text boilerplate.** Every `text` value begins with "more pics" and the sub-score breakdown, ends with "Helpful", and is padded with whitespace. Strip these before sentiment analysis (#6), or the sub-score numbers and fixed words will distort the results.
9. **Extreme episode counts.** 15 anime have more than 500 episodes (up to 3,057, Lan Mao). These are real long-running children's and educational shows, not errors, but they will dominate any unscaled clustering or regression on `episodes`. Consider a log transform or a cap.
10. **Unresolved favorites.** 34 distinct anime IDs in `favorites_anime` (0.18% of references) have no matching anime record. They are harmless if dropped when favorites are counted.
11. **Sparse demographics.** `gender` is missing for 35.52% of profiles and `birthday` for 43.93%, and many birthdays have no year. Demographic analysis would rest on a self-selected minority of reviewers. Profiles are reviewers only, so they don't represent MyAnimeList's general audience.
12. **Snapshot timing is unrecorded.** The dataset has no scrape date. First-air years run 1917–2021, with a sharp drop after 2019 (610 titles in 2019, 187 in 2020, 6 in 2021). This suggests a snapshot from around 2020, so recent titles have had less time to gather members and reviews.

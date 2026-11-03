# Dataset Description

*Author: John (Data Engineering & Acquisition Analyst). Figures come from `notebooks/john/01-data-dictionary.ipynb`; column-level detail is in `docs/data-dictionary.md`.*

## Source

The analysis uses the **Anime Dataset with Reviews – MyAnimeList** dataset, published on Kaggle by user *marlesson* (version 1). It was scraped from MyAnimeList, the largest English-language anime database and community, where users track what they watch, rate titles from 1 to 10, and write reviews. The dataset records no scrape date. Airing years drop off sharply after 2019, with only 6 titles listed for 2021, which places the snapshot around 2020.

## Files and contents

The dataset has three CSV files. Each contains a large share of duplicate rows, so the table gives both the raw row count and the number of unique records.

| File | Raw rows | Unique records | One record is… | Key fields |
|---|---|---|---|---|
| `animes.csv` | 19,311 | 16,216 | an anime title (series, movie, OVA, special) | ID, title, synopsis, genres, air dates, episodes, members, popularity rank, score, score rank |
| `reviews.csv` | 192,112 | 130,519 | a user review of one anime | reviewer, anime ID, full review text, overall score, six sub-scores |
| `profiles.csv` | 81,727 | 47,885 | a reviewer's user profile | username, gender, birthday, list of favorite anime |

## How the files relate

Reviews link the other two files: each review names the anime it covers (`anime_uid` → `animes.uid`) and the user who wrote it (`profile` → `profiles.profile`). Both links resolve for 100% of reviews, so no review is orphaned. Profiles also link back to anime through each user's list of favorites, and 99.82% of those IDs match an anime record.

```
profiles ──< reviews >── animes
    └──── favorites ────────┘
```

## What the data can tell us

The business question asks which anime will attract large audiences, have strong review sentiment, and could grow into franchises. The dataset gives a measure for each part:

- **Audience size.** `members` counts how many users added a title to their list, and `popularity` ranks titles by that count. These are the clearest audience measures in the data. Death Note leads with 1.87 million members.
- **Quality.** `score` is the average user rating (1.25–9.23 across the catalog), and `ranked` orders titles by it. Fullmetal Alchemist: Brotherhood ranks first at 9.23.
- **Sentiment.** 130,519 review texts (median 360 words) can be scored for sentiment. Each review also carries six numeric sub-ratings (Overall, Story, Animation, Sound, Character, Enjoyment), which allows a check of text sentiment against what reviewers scored.
- **Loyalty.** Users' favorite lists show which titles inspire strong attachment, beyond simple viewing.
- **Franchise signals.** The dataset has no explicit "related titles" or franchise field. However, MyAnimeList lists every season, sequel, movie, and spin-off as a separate entry (e.g. "Haikyuu!! Second Season"). Franchise membership therefore has to be inferred from titles. Feature engineering does this by grouping titles that share a root; see the Data Cleaning and Preparation section for the method and its limits.

## Limitations

- **Duplicates.** 15% of anime rows, 41% of profile rows, and 32% of review rows are exact duplicates. 152 anime appear more than once with different `members` and `popularity` values, likely captured at different times. All analysis uses de-duplicated data.
- **Uneven review coverage.** Only half of the catalog (8,113 of 16,216 anime) has any reviews, and the median reviewed title has just 3. Sentiment measures are only reliable for well-reviewed titles. Coverage follows popularity, though (Spearman ρ = 0.80 between members and review count): 98.8% of the 500 most popular anime have at least 10 reviews, with a median of 91.5. Most of the titles this acquisition decision focuses on are covered, but not all. Some popular titles have few or no reviews in this dataset because of how it was collected. *Hunter x Hunter (2011)* has none, so review counts are not a reliable measure of review volume (see Data Cleaning and Preparation, section 6).
- **Reviewers are not the general audience.** Every profile belongs to someone who wrote a review. Reviewers are a small, engaged minority of MyAnimeList's users, and gender and birthday are blank for 36–44% of them. The data does not support demographic conclusions about the platform's audience.
- **A single point in time.** The figures are a snapshot from around 2020. Titles released close to the snapshot have had less time to build members and reviews, so their numbers understate their eventual reach.
- **Missing values.** Among anime, `ranked` is missing for 10.3%, `synopsis` for 4.7%, `episodes` for 3.0%, and `score` for 2.1%. The cleaning step explains how each is handled.

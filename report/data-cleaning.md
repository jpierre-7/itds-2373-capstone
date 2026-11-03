# Data Cleaning and Preparation

*Author: John (Data Engineering & Acquisition Analyst). Figures come from `notebooks/john/02-cleaning.ipynb` (cleaning) and `notebooks/john/03-features.ipynb` (engineered features). The code is `src/capstone/clean.py` and `src/capstone/features.py`, covered by automated tests in `tests/`.*

## Overview

The three raw files were cleaned and merged into two tables that the whole team works from:

| Table | Rows | One row is… | Used for |
|---|---|---|---|
| `anime.parquet` | 16,216 | an anime, with review and favorites figures merged in and engineered features added | EDA, clustering, modeling, final ranking |
| `reviews.parquet` | 130,517 | a review, with cleaned text and sub-scores | sentiment analysis |

Cleaning is fully automated and reproducible. Anyone on the team runs `uv run build-dataset` and gets identical tables, and a notebook check confirms every rule below held on the real data. Nothing is edited by hand.

## 1. Duplicates removed

| File | Raw rows | After exact duplicates | One row per record |
|---|---|---|---|
| anime | 19,311 | 16,368 | **16,216** |
| reviews | 192,112 | 130,519 | **130,519** |
| profiles | 81,727 | 47,902 | **47,885** |

Exact duplicate rows were removed first. Some records then still appeared more than once with *different* values, the same page captured at different times:

- **152 anime** had copies that differed in `members`, `popularity`, or `ranked`. We kept the copy with the **most members**. Membership counts on MyAnimeList rise over time, so the highest count is almost certainly the most recent snapshot.
- **17 profiles** had copies with different favorites lists. We kept the **longest list**, as the most complete record.

## 2. Invalid values

- **Two reviews dropped.** One review had every score set to 0 and another had every score set to 11, outside MyAnimeList's 1–10 scale. Both were removed, leaving 130,517 reviews.
- **Unrated sub-scores blanked.** 7,495 reviews (5.7%) had a sub-score of 0 next to a valid overall score. For example, an Overall of 8 with Sound and Character at 0. A 0 here means the reviewer did not rate that category, so it was set to blank rather than counted as a score of zero. Counting it would have dragged those averages down.
- **Six impossible airing ranges.** Six anime list an end date earlier than their start date (e.g. "Sep 3, 1981 to Jul 15, 1981"). These are data-entry errors on MyAnimeList. The start date was kept and the end date blanked.

## 3. Formats corrected

| Raw field | Problem | Cleaned to |
|---|---|---|
| `aired` | free text in 24 different layouts ("Oct 4, 2015 to Mar 27, 2016", "Apr, 2010", "2014", "2020 to ?", "Not available") | `start_date`, `end_date`, `start_year`, `is_airing`. A partial date covers its whole period: "Apr, 2010" runs Apr 1–30, and "2013" as an end date means Dec 31, 2013. "… to ?" marks a show still airing when the data was collected (438 anime). |
| `genre` | a list written as text | a real list (46,587 genre tags across all anime). One anime listed every tag twice; repeats are removed. |
| `scores` | a dictionary written as text, e.g. `{'Overall': '8', 'Story': '7', …}` | five whole-number columns: `story_score`, `animation_score`, `sound_score`, `character_score`, `enjoyment_score`. Overall already equals `score` in every row, so it gets no extra column. |
| review `text` | every review wrapped in page text: "more pics", the six sub-scores, then the review, then "Helpful", padded with blank lines | the review alone, whitespace tidied (median 345 words) |
| `episodes` | decimal numbers (25.0) | whole numbers, blank where unknown |

## 4. Review data merged in

Each anime gets the following from the cleaned reviews and profiles:

- `n_reviews`: number of reviews in the dataset (0 if none)
- `mean_review_score` and the five `mean_<category>_score` columns: average reviewer ratings
- `n_favorites`: number of reviewers who list the anime as a favorite

Anime without reviews are **kept**, with `n_reviews = 0` and blank averages. Half the catalog (8,103 anime) has no reviews, and dropping those titles would remove popular titles along with obscure ones.

## 5. Missing values: one strategy, applied per column

**No values were imputed.** Every number in this analysis is evidence for an investment decision. A filled-in `score` or `members` value would be an invented number presented as data. Missing values are left blank, and each analysis filters to the rows it can use.

| Column | Missing | Why it's missing | How to handle it |
|---|---|---|---|
| `ranked` | 10.26% | MyAnimeList leaves some titles unranked | Use `score` as the rating measure instead |
| `synopsis` | 4.71% | no summary on the anime's page | Text only; not used as a number |
| `end_date` | 4.42% | still airing, not available, or an impossible range | Use `start_date`/`start_year` for timing |
| `episodes` | 3.03% | mostly shows still airing (73% of these rows) | Filter out when episodes is an input |
| `score` | 2.10% | no score listed on MyAnimeList | Exclude from rating-based analysis. These titles are not acquisition candidates. |
| `start_date`, `start_year` | 1.68% | "Not available" on MyAnimeList | Exclude from time-based analysis |
| `img_url` | 1.02% | no cover image | Not used |
| `mean_review_score` | 49.97% | anime has no reviews | Filter on `n_reviews > 0` |
| `mean_<category>_score` | 51.09–51.20% | no reviews, or no review rated that category | Filter on the column itself |

## 6. Limitation: review counts are incomplete

`n_reviews` reflects what the dataset's scraper collected, not MyAnimeList's real totals. Two pieces of evidence:

- **172 anime have exactly 20 reviews**, against about 45–50 at each neighboring count. This points to a one-page (20-review) scrape limit for some titles. Among the 500 most popular anime, 50 sit at exactly 20.
- **Six of the 500 most popular anime have no reviews at all.** One of them is *Hunter x Hunter (2011)*, which is 20th by popularity and 3rd by score.

**Guidance for the team:**
- Do **not** use `n_reviews` as a measure of popularity or review volume. Use `members` for audience size and `n_favorites` for loyalty. Favorites come from users' favorites lists, not from the review scrape: Hunter x Hunter has 3,149 favorites despite having no reviews.
- Mean review scores remain usable, since 20 reviews is still a reasonable sample.
- Treat a missing review-based score as "no data", not as a weak result.

## 7. Engineered features

Seven features, plus one flag column per genre, are added to `anime.parquet` for the clustering, modeling and ranking work. Each is defined in `docs/data-dictionary.md` under "Cleaned tables".

### Popularity index

`popularity_index` is the percentage of the catalog with at most as many members as the title, on a 0–100 scale. Death Note, the most-watched title, scores 100. A title at 90 has at least as many members as 90% of the catalog, which takes about 62,000 members. We based it on `members` alone so that it doesn't overlap with `n_favorites`, which the models use separately as a loyalty measure. A percentile is also easier to explain than raw counts, which range from 25 to 1.87 million.

### Average review scores

`mean_review_score` and the five category averages (section 4) are kept as they are. Half the reviewed anime have 3 reviews or fewer, though, so one enthusiastic review can put an obscure title at a perfect 10. `adjusted_review_score` corrects for this the way IMDb's weighted rating does. It blends each anime's reviews with five imaginary reviews at the catalog average of 7.33:

```
adjusted = (n_reviews × mean_review_score + 5 × 7.33) / (n_reviews + 5)
```

A single 10/10 review becomes 7.77. Death Note's 854 reviews move it by less than 0.01, and the median shift for titles with 20 or more reviews is 0.06. Anime with no reviews stay blank. Rankings that use review scores should use the adjusted score.

### Genre features

`genre_count` is the number of genre tags, and 43 true/false columns (`genre_action`, `genre_slice_of_life`, …) mark each genre. The notebook checks that every anime's flags add up to its `genre_count`.

### Franchise indicators

The dataset has no "related titles" field. MyAnimeList does list every season, movie and spin-off as its own entry, though, so franchises are inferred from titles. Each title is reduced to a root by removing:

- a subtitle after ": "
- an edition in brackets ("(2011)", "(TV)")
- trailing sequel markers ("Season 2", "2nd Season", "Second Season", "Part 2", "S2", "II", "R2", a trailing number, "Movie", "OVA", "Specials")

Titles that share a root form a franchise. "Naruto: Shippuuden", "Detective Conan (TV)" and "Code Geass: Hangyaku no Lelouch R2" all join their franchises this way. The resulting features:

- `franchise`: the root
- `franchise_size`: the number of entries
- `franchise_members`: members summed across entries. This is total reach, not unique viewers, because a viewer who listed three seasons is counted three times.
- `is_sequel`: True unless the entry is the franchise's earliest-starting one

In total, 6,277 anime (39%) belong to 1,983 franchises with two or more entries. The largest by reach are Shingeki no Kyojin (12 entries, 4.6M members summed), Sword Art Online and Naruto.

**Limits.** Matching on titles is a heuristic, and it fails in three known ways:

- **Unrelated titles can share a root.** "Sin: The Movie" groups with "Sin: Nanatsu no Taizai".
- **One franchise can split across roots** when a sequel's title changes. "K-On!!" is separate from "K-On!", and "Boruto" from "Naruto".
- **Remakes and side stories count as sequels.** *Fullmetal Alchemist: Brotherhood* (2009) is marked as a sequel because the 2003 series came first.

On the most popular titles the grouping is correct (notebook 03, section 4). Any franchise named in the final recommendations should be checked against its list of entries.

## Validation

The cleaning notebook ends with checks that fail loudly if any rule is broken. All pass on the real data:

- one row per anime and per review
- review scores within 1–10 and sub-scores within 1–10 or blank
- no review text keeps the page header
- no end date before its start date
- every review is counted once in `n_reviews` and belongs to a cleaned anime
- every anime's genre flags match its genre list

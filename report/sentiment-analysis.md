# Review Sentiment Analysis

_Author: Leonardo, Yiesha (Market Intelligence & Visualization Analyst), ticket #6. Figures come from `notebooks/leonardo/01-sentiment.ipynb`. The code is `src/capstone/sentiment.py`, covered by automated tests in `tests/test_sentiment.py`. Column definitions are in `docs/data-dictionary.md`._

## Overview

The brief asks for titles with strong review sentiment. We measured how positive the wording of all **130,517 reviews** is, checked that measure against the scores reviewers gave, and summarized it into four columns per anime in `anime.parquet`. **8,113 anime** have reviews and get sentiment values. The other **8,103** have none, and their columns are left blank. A title with no reviews has no measured sentiment, which is not the same as neutral sentiment.

## 1. Method

**Tool: VADER.** VADER is a lexicon-based scorer: each word carries a positive or negative weight, adjusted for capitals, punctuation, intensifiers ("very good") and negation ("not good"). It returns a compound score from −1 (negative) to +1 (positive). We chose it over transformer models because it is fast enough for all reviews on a laptop, gives the same result on every run, and can be explained word by word.

**Scored sentence by sentence.** Reviews are long (median 345 words). Scored as a whole, a review piles up positive words and lands near +1 no matter what the reviewer thought. On a 5,000-review sample, whole-review scoring gave a median of 0.987, with 75% of reviews at ±0.95 or beyond. We therefore score each sentence and average the sentences.

About **1.6% of reviews (2,042)** barely use punctuation, so one "sentence" could be the whole review. Runs longer than 40 words are cut into 40-word pieces (a typical sentence is about 18 words). This cut the share of those reviews scoring at ±0.9 or beyond from **31.5% to 1%**.

**Positive cutoff tuned to 0.12.** VADER's default rule calls a text positive at 0.05. We tested cutoffs against reviews with a clear verdict: 91,852 reviews scored 7 or higher and 17,671 scored 4 or lower.

|                                           | VADER default (0.05) | Tuned (0.12) |
| ----------------------------------------- | -------------------- | ------------ |
| Reviews scored ≤4 wrongly called positive | 38%                  | **20%**      |
| Reviews scored 7+ called positive         | 90%                  | 80%          |
| Balanced accuracy                         | 0.76                 | **0.80**     |

Balanced accuracy averages the two kinds of correct answer, so the 5-to-1 majority of positive reviews can't dominate it. The choice is stable: cutoffs from 0.11 to 0.14 perform almost the same, and redefining the groups as 8+ vs. ≤5 moves the best cutoff only to 0.14.

**Aggregated per anime, with small-sample adjustment.** Half of reviewed anime have 3 or fewer reviews, so a raw average can rest on a single opinion. We use the same method as `adjusted_review_score`. Each anime's value is blended with 5 imaginary reviews at the catalog average (mean sentiment 0.195, positive share 0.67):

> adjusted = (n × anime's value + 5 × catalog value) / (n + 5)

| Column                      | Meaning                                                |
| --------------------------- | ------------------------------------------------------ |
| `mean_review_sentiment`     | Average sentiment of the anime's reviews               |
| `positive_review_share`     | Share of its reviews at sentiment ≥ 0.12               |
| `adjusted_review_sentiment` | The average after the adjustment (**use for ranking**) |
| `adjusted_positive_share`   | The share after the adjustment (**use for ranking**)   |

The adjustment matters. Ranked on the raw average, the top five titles each have a single review. _Mini Moni Yaru no da Pyon!_, for example, drops from 0.943 to 0.319 once adjusted. After adjustment, raw shares that ran from 0% to 100% fall between 14% and 97%.

## 2. Validation

All correlations are Spearman (rank-based), which suits 1–10 review scores. A value of 0.3 is moderate and 0.5 is strong.

| Comparison                                                               | Spearman                                |
| ------------------------------------------------------------------------ | --------------------------------------- |
| Review sentiment vs. that review's score (`reviews.score`)               | **0.49**                                |
| … vs. enjoyment / character / story sub-score                            | 0.48 / 0.47 / 0.42                      |
| … vs. sound / animation sub-score                                        | 0.36 / 0.35                             |
| Anime `adjusted_review_sentiment` vs. its average review score           | 0.53 (0.61 for titles with 10+ reviews) |
| Anime `adjusted_review_sentiment` vs. MyAnimeList rating (`anime.score`) | 0.35 (0.40 for titles with 10+ reviews) |

Sentiment rises steadily with the reviewer's score. It follows enjoyment and characters more than animation, which matches what reviewers write about. It agrees more with reviewers' own scores than with the overall MyAnimeList rating, because reviewers are a small, self-selected group whose views can differ from the wider audience's.

**Examples inspected.** We read the reviews where sentiment and score disagree most:

- **Sad is read as negative.** A 10/10 review of _Hotaru no Haka_ scores −0.68 because it praises the film as "so sad" and says it "made me cry".
- **Words from titles and plots.** _Kill la Kill_ (rated 8.16) has low sentiment partly because reviews repeat its title, and VADER scores "kill" at −3.7.
- **Sarcasm.** The most "positive" 1/10 reviews are mock praise ("Perfect 10… outshines even FMA Brotherhood").
- **Sentiment is right, the rating differs.** _Nanatsu no Taizai_ sequels have a high MyAnimeList rating, but reviewers scored them low and wrote negatively. Sentiment reflects the reviewers.

## 3. Key finding: sentiment partly measures a show's tone

Among reviews that all gave a 9 or 10, dark genres get clearly lower sentiment than light ones:

| Genre         | Mean review score                     | Share rated 9–10 | Median sentiment of 9–10 reviews |
| ------------- | ------------------------------------- | ---------------- | -------------------------------- |
| Thriller      | **8.09** (highest of any large genre) | 55%              | 0.20                             |
| Psychological | 7.56                                  | 45%              | 0.19                             |
| Police        | 7.88                                  | 49%              | 0.18                             |
| Slice of life | 7.82                                  | 45%              | 0.30                             |
| Shoujo        | 7.52                                  | 43%              | 0.32                             |

This is a difference in vocabulary, not in satisfaction. Across genres, review score and sentiment are unrelated (Spearman 0.00). VADER reads "death" (−2.9), "horror" (−2.7), "fear" (−2.2), "sad" (−2.1) and "dread" (−2.0) as negative even in praise. Correspondingly, the titles with the highest adjusted sentiment are gentle shows such as _Yume-iro Pâtissière_, _Yuru Camp△_ and _Natsume Yuujinchou Roku_. Horror is the exception that needs care: its review scores are also below average (6.83), so part of its low sentiment reflects real opinion.

**Implication for the acquisition ranking:** ranked on sentiment alone, a top-rated thriller would lose to an average comedy. Sentiment should therefore be used alongside review scores, or compared only among titles in similar genres, never as a single cross-genre ranking signal.

## 4. Limitations

- Lexicon scoring misses sarcasm and context ("sad" as praise).
- Sentiment covers only the reviews in the dataset, which are capped at 20 for many titles (see `report/data-cleaning.md`, section 6). Titles with few reviews are pulled strongly toward the catalog average.
- Reviewers are a self-selected group, not the general MyAnimeList audience.

# Anime Acquisition Strategy for a Streaming Platform

Group capstone project for **ITDS 2373 Data Mining Methods** (HCC Eagle Online). [Assignment page](https://eagleonline.hccs.edu/courses/340537/assignments/9192438?module_item_id=25366780) · No due date · 100 points

## Team

| Member | Role |
|---|---|
| John | Data Engineering & Acquisition Analyst |
| Leonardo | Market Intelligence & Visualization Analyst |
| Omonigho | Consumer Segmentation & Clustering Analyst |
| Aaliyah | Predictive Analytics & Acquisition Strategist |
| Yiesha | TBD: extra teammate who will help whichever role needs it later |

The assignment is written for 4 members, each doing about 25% of the work. Every member must document their own contributions clearly.

## Setup

The project uses [uv](https://docs.astral.sh/uv/) to manage Python and its packages. `pyproject.toml` pins Python 3.13, and `uv.lock` pins the exact version of every package, so everyone runs the same environment.

1. **Install uv** (one time):
   - macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
2. **Clone the repo and install the environment.** uv downloads Python 3.13 for you if you don't have it.
   ```sh
   git clone https://github.com/jpierre-7/itds-2373-capstone.git
   cd itds-2373-capstone
   uv sync
   ```
3. **Download the dataset** (about 217 MB to download, about 700 MB once unzipped). No Kaggle account is needed.
   ```sh
   uv run download-data
   ```
   This puts `animes.csv`, `profiles.csv` and `reviews.csv` in `data/raw/`. It's safe to run again: if the files are already there, it does nothing. The download is pinned to version 1 of the Kaggle dataset, so everyone gets the same data. kagglehub also keeps a cached copy in `~/.cache/kagglehub/` (about 700 MB). If `data/raw/` is deleted, the next run copies from that cache. You can delete the cache to free space. The `data/` folder is gitignored, so never commit data files.
4. **Start working:**
   - `uv run jupyter lab` opens notebooks.
   - `uv run pytest` runs the tests.
   - `uv add <package>` adds a dependency. Commit the updated `pyproject.toml` and `uv.lock` so everyone gets it.

If you use VS Code or another editor, select `.venv` as the Python interpreter.

## Business Scenario

A new streaming service has hired us as a Data Mining Consulting Team to expand its anime catalog. The Chief Content Officer (CCO) has set aside a large acquisition budget to license **10 anime titles** from the MyAnimeList database. The executive team wants more than popular shows. They want anime that:

- Will attract large audiences
- Have strong review sentiment
- Can grow into long-term franchises
- Could support sequels, spin-offs, merchandise, movies, or other IP opportunities
- Are a strong investment, the way major media companies buy successful franchises

> **Business question:** If you were responsible for investing millions of dollars in anime licensing and future franchise ownership opportunities, which 10 anime would you recommend and why?

Every recommendation must be data-driven and backed by evidence from the dataset, using data cleaning and preparation, exploratory analysis, clustering, predictive modeling, review analysis, and business interpretation.

## Dataset

[Anime Dataset with Reviews - MyAnimeList](https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews) (Kaggle)

## Roles and Responsibilities

### 1. Data Engineering & Acquisition Analyst (John)

**Key question:** What data should the team trust and use for decision-making?

- **Dataset exploration:** download and review all files, build a data dictionary, and find the relationships among anime, reviews, ratings, and user data.
- **Data preparation:** handle missing values, remove duplicates, and fix inconsistencies.
- **Feature engineering:** for example, average review score, popularity index, franchise indicators, and genre counts.
- **Deliverables:** data dictionary, cleaning report, final merged dataset
- **Report sections:** Dataset Description; Data Cleaning and Preparation

### 2. Market Intelligence & Visualization Analyst (Leonardo)

**Key question:** What characteristics appear to make anime successful?

- **Exploratory analysis:** look at these relationships:
  - rating ↔ popularity
  - genre ↔ audience scores
  - episode count ↔ ratings
  - popularity ↔ review volume
  - review sentiment ↔ ratings
- **Visualizations (at least 10):** histograms, heatmaps, boxplots, genre frequency charts, scatter plots, correlation matrices
- **Deliverables:** visual dashboard, business insights document
- **Report sections:** Exploratory Data Analysis; Market Trends

### 3. Consumer Segmentation & Clustering Analyst (Omonigho)

**Key question:** Which anime belong in the same investment category?

- **Suggested variables:** rating, popularity, favorites, review counts, episode counts
- **Methods (at least one):** K-Means, Hierarchical Clustering, DBSCAN
- **Groups to find:** hidden gems, mainstream hits, highly rated niche titles, underperforming shows, franchise-worthy properties
- **Deliverables:** cluster visualizations, cluster interpretation, strategic recommendations
- **Report sections:** Clustering Methodology; Cluster Findings

### 4. Predictive Analytics & Acquisition Strategist (Aaliyah)

**Key question:** Which anime have the highest probability of becoming long-term successes?

- **Potential targets:** highly rated anime, popularity categories, high review sentiment, franchise potential score
- **Algorithms:** Decision Tree, Random Forest, Logistic Regression, Gradient Boosting
- **Evaluation:** Accuracy, Precision, Recall, and F1 for classification; RMSE, MAE, and R² for regression
- **Deliverables:** predictive models, feature importance analysis, strategic ranking system
- **Report sections:** Modeling; Model Evaluation; Strategic Recommendations

## Final Team Task: The Acquisition Board Meeting

Acting as consultants to company executives, the team produces a final ranking of the **Top 10 Anime to Acquire**. Each recommendation includes:

- **Anime title**
- **Supporting evidence:** rating, popularity, review sentiment, cluster membership, model prediction score
- **Business justification:** why viewers will watch it, why it has long-term value, whether it has franchise potential, and whether it looks underpriced compared with competitors

### Final Presentation

Pitch it as if to a board of directors deciding where to invest millions. The presentation must answer:

1. What characteristics define successful anime?
2. What patterns emerged from the data?
3. What clusters were identified?
4. What factors best predicted success?
5. Which 10 anime should be acquired?
6. Which 3 anime should receive priority investment for future franchise ownership?

### Executive Deliverable: Investment Recommendation Memo

The final report ends with a one-page memo to the streaming service executive. The memo covers:

- The 10 anime to acquire
- The 3 highest-priority franchise investments
- Expected benefits
- Potential risks
- Data-driven justification for each recommendation

**Success criterion:** The executive should be convinced that the recommendations come from evidence, not personal preferences or fandom. Data mining results and business reasoning must back every recommendation.

## Grading Rubric

| Category | Points |
|---|---|
| Data Preparation | 15 |
| Exploratory Analysis | 15 |
| Clustering Analysis | 15 |
| Predictive Modeling | 20 |
| Business Justification | 15 |
| Final Top-10 Recommendations | 10 |
| Presentation Quality | 10 |
| **Total** | **100** |

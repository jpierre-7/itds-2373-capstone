# itds-2373-capstone

Group capstone for ITDS 2373 Data Mining Methods (HCC). The full assignment brief, including per-role responsibilities, deliverables, report sections, and the grading rubric, is in `README.md`. Read it before starting any analysis work.

## Project summary

- **Scenario:** We act as a data mining consulting team for a new streaming service. The service wants to license **10 anime** from MyAnimeList that will bring in large audiences, have strong review sentiment, and could grow into franchises (sequels, spin-offs, merch, movies).
- **Dataset:** [Anime Dataset with Reviews - MyAnimeList](https://www.kaggle.com/datasets/marlesson/myanimelist-dataset-animes-profiles-reviews) (Kaggle): anime profiles, user profiles, reviews.
- **Required lifecycle:** cleaning/prep → EDA (at least 10 visualizations) → clustering (K-Means, hierarchical, or DBSCAN) → predictive modeling (classification and/or regression, with standard metrics) → review analysis → business interpretation.
- **Final output:** a Top-10 acquisition ranking. Each title gets rating, popularity, review sentiment, cluster membership, model prediction score, and a business justification. The output also names the 3 priority franchise investments and includes a board presentation and a one-page Investment Recommendation Memo.
- **Success criterion:** every recommendation must rest on data mining evidence, not preference or fandom.

## Team

| Member | Role | Owns |
|---|---|---|
| John | Data Engineering & Acquisition Analyst | Data dictionary, cleaning report, final merged dataset, engineered features |
| Leonardo | Market Intelligence & Visualization Analyst | EDA, at least 10 visualizations, dashboard, business insights |
| Omonigho | Consumer Segmentation & Clustering Analyst | Clustering, cluster interpretation, segment recommendations |
| Aaliyah | Predictive Analytics & Acquisition Strategist | Predictive models, feature importance, strategic ranking |
| Yiesha | TBD | Extra teammate; will assist whichever role needs help |

Each member's contributions must be clearly attributable, so keep work scoped to the owning role, for example through issue assignees and per-role files or notebooks.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues for `jpierre-7/itds-2373-capstone` (via `gh`). See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

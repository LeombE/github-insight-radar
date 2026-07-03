# Scoring Methodology

GitHub Insight uses deterministic, explainable scoring to prioritize repositories for practical review. The score is an intelligence aid, not an objective measure of repository quality.

The canonical daily pipeline is implemented in `github_insight/classifier.py` and produces 0-100 scores. A legacy compatibility scorer remains in `github_insight/scoring.py`, but the daily reports and dashboard use the 0-100 `InsightRecord` fields documented here.

## Audiences

Each repository is evaluated for three audiences:

| Audience | Focus |
| --- | --- |
| `general_user` | Practical tools, workflow automation, apps, CLIs, self-hosted utilities, learning resources. |
| `data_analyst` | SQL, BI, dashboards, metrics, ETL, reporting, data cleaning, visualization, CSV/data workflows. |
| `data_scientist` | ML, AI, LLM, RAG, NLP, computer vision, benchmarks, datasets, notebooks, training, evaluation. |

Audience scores are keyword and evidence based. Source query audience, Python language, datasets, notebooks, CSV/SQL signals, productivity terms, and automation terms can increase the relevant audience fit. Missing evidence does not create positive claims.

## Score Components

| Field | Range | Meaning |
| --- | ---: | --- |
| `usefulness_score` | 0-100 | Combined audience fit, popularity signal, and README quality. |
| `momentum_score` | 0-100 | Recency from `pushed_at` and `updated_at`, with a popularity signal. |
| `audience_fit_score` | 0-100 | Best audience match among general users, data analysts, and data scientists. |
| `maintenance_score` | 0-100 | Active/non-archived status, license availability, and push recency. |
| `readme_quality_score` | 0-100 | README-derived quality signal from bounded enrichment. |
| `reproducibility_score` | 0-100 | Presence of reproducibility signals such as requirements, pyproject, Dockerfile, and related files. |
| `data_asset_score` | 0-100 | Dataset, CSV/SQL, demo, notebook, dashboard, and visualization signals. |
| `dashboard_readiness_score` | 0-100 | Dashboard/demo/data/usage signals used for review context. |
| `risk_score` | 0-100 | Penalty score derived from deterministic risk flags. |
| `overall_insight_score` | 0-100 | Final score used for ranking. |

## Overall Formula

```text
0.20 * usefulness_score
+ 0.20 * momentum_score
+ 0.15 * audience_fit_score
+ 0.15 * maintenance_score
+ 0.10 * readme_quality_score
+ 0.10 * reproducibility_score
+ 0.10 * data_asset_score
- 0.15 * risk_score
```

The score is clamped between 0 and 100 and rounded to two decimals.

## Recommended Actions

| Condition | Recommended action |
| --- | --- |
| Repository is archived or disabled | `Skip for now` |
| Overall score is 80 or higher | `Try today` |
| Overall score is 70 to 79.99 | `Use as portfolio reference` |
| Overall score is 60 to 69.99 | `Study for learning` |
| Data scientist repository with score 45 to 59.99 | `Track for research` |
| Score 45 to 59.99 | `Watch this week` |
| Score below 45 | `Skip for now` |

## Risk Flags

Risk flags are deterministic and evidence based. Current examples include:

- Archived repository.
- Disabled repository.
- Missing license metadata.
- Stale push activity for more than 12 months.
- Many open issues relative to stars.
- Fork-only repository.
- README/enrichment caveats such as weak installation or usage evidence.

`risk_score` is calculated from the number of flags plus extra penalties for archived or disabled repositories:

```text
risk_score = 15 * number_of_risk_flags
           + 35 if archived
           + 20 if disabled
```

The value is clamped to 0-100.

## Dashboard Risk Severity

The static dashboard groups risk into severity labels:

| Risk score | Severity |
| ---: | --- |
| 0-29.99 | Low |
| 30-59.99 | Medium |
| 60-100 | High |

The dashboard also shows a caveat summary from the first available risk flags. When no major caveat is available, it says that no major caveat was found from collected evidence.

## Confidence Labels

Confidence is a statement about available evidence, not a guarantee that a repository is good.

| Label | Rule |
| --- | --- |
| High | README quality is at least 70 and the repository has no more than two risk flags. |
| Medium | README text exists and the GitHub description is available. |
| Low | Supporting README or description evidence is weak or missing. |

## Evidence Boundaries

The system can use GitHub metadata, topics, README excerpts, repository file signals, release signals, and bounded API responses. It does not clone repositories, execute external code, or prove that installation steps work. Scores should be reviewed together with the evidence, caveat summary, source status, and generated date.

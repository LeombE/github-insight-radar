# Scoring Methodology

This project ranks repositories with deterministic rules. The score is meant to help review and triage projects; it is not an objective quality rating.

The current dashboard and reports use the 0-100 scoring path in `github_insight/classifier.py`. A compatibility scorer still exists in `github_insight/scoring.py`, but it is not the main dashboard path.

## Audiences

Repositories are evaluated for three audiences:

| Audience | What the system looks for |
| --- | --- |
| `general_user` | Practical tools, CLIs, apps, workflow automation, learning resources, self-hosted utilities. |
| `data_analyst` | SQL, dashboards, BI, metrics, ETL, reports, data cleaning, CSV/data workflows. |
| `data_scientist` | ML, AI, LLM, NLP, computer vision, benchmarks, datasets, notebooks, training, evaluation. |

Audience scores are based on repository metadata, topics, README evidence, source query context, and bounded file/release signals. Missing evidence is treated as missing; it is not filled in with assumptions.

## Score Components

| Field | Range | Meaning |
| --- | ---: | --- |
| `usefulness_score` | 0-100 | Audience fit, popularity signal, and README quality. |
| `momentum_score` | 0-100 | Push/update recency plus a popularity signal. |
| `audience_fit_score` | 0-100 | Best match across the three audiences. |
| `maintenance_score` | 0-100 | Active status, license availability, and push recency. |
| `readme_quality_score` | 0-100 | README-derived quality signal from bounded enrichment. |
| `reproducibility_score` | 0-100 | Signals such as requirements files, pyproject, Dockerfile, or similar setup files. |
| `data_asset_score` | 0-100 | Dataset, CSV/SQL, demo, notebook, dashboard, or visualization signals. |
| `dashboard_readiness_score` | 0-100 | Demo/data/usage signals used for dashboard context. |
| `risk_score` | 0-100 | Penalty score from deterministic risk flags. |
| `overall_insight_score` | 0-100 | Final score used for sorting. |

## Formula

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

The final score is clamped from 0 to 100 and rounded to two decimals.

## Recommended Actions

| Condition | Action |
| --- | --- |
| Archived or disabled repository | `Skip for now` |
| Score >= 80 | `Try today` |
| Score >= 70 | `Use as portfolio reference` |
| Score >= 60 | `Study for learning` |
| Data scientist project with score >= 45 | `Track for research` |
| Score >= 45 | `Watch this week` |
| Score < 45 | `Skip for now` |

## Risk and Confidence

Risk flags are deterministic. Examples include archived status, disabled status, missing license metadata, stale pushes, many open issues relative to stars, fork-only status, and README/enrichment caveats.

The dashboard groups `risk_score` as:

| Risk score | Label |
| ---: | --- |
| 0-29.99 | Low |
| 30-59.99 | Medium |
| 60-100 | High |

Confidence describes evidence coverage, not repository quality:

| Label | Rule |
| --- | --- |
| High | README quality is at least 70 and there are no more than two risk flags. |
| Medium | README text and GitHub description are available. |
| Low | Key supporting evidence is weak or missing. |

## Dashboard Views

The dashboard adds presentation-only views on top of the same scored data:

- `Overview` is the default view.
- `General User`, `Data Analyst`, and `Data Scientist` filter by `primary_audience` and `audience_tags`.
- `Today's Picks` selects a small set from the filtered and scored projects. It does not change scores.


## Evergreen Quality Gates

Evergreen Recommendations do not use the daily scoring formula. They are a manually refreshed dashboard layer for mature repositories from `config/evergreen_repos.yml`. The builder checks current GitHub metadata and uses deterministic gates:

| Tier | Gate | Dashboard behavior |
| --- | --- | --- |
| Community Standard | Stars >= 10000, forks >= 1000, license present, README present, not archived, recent activity within 365 days. | Shown by default. |
| Mature Reference | Stars >= 3000, forks >= 300, license present, README present, not archived. | Shown by default. |
| Emerging Project | Below mature threshold or failing required evidence gates. | Kept in `excluded`; not shown by default. |

This layer is separate from daily discovery so low-adoption daily finds do not dominate stakeholder-facing default recommendations.

## Evidence Boundaries

The system can use GitHub metadata, topics, README excerpts, repository file signals, release signals, and bounded API responses. It does not clone repositories, run project code, or prove that installation instructions work. Review scores together with evidence, risk notes, source status, and generated date.
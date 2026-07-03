# Data Dictionary

This document describes the main generated outputs and fields used by GitHub Insight. Field availability can vary by run mode and by what the GitHub API returns.

## Run Modes

| Mode | Meaning |
| --- | --- |
| `live` | Uses official GitHub API collection and may publish production `docs/` outputs. |
| `mock` | Uses deterministic offline fixtures. By default it writes to `.pytest-tmp/mock-run` or another preview output root, not production docs. |

## `docs/data/latest.json`

Static dashboard source for the latest production run.

| Top-level field | Description |
| --- | --- |
| `run` | Run metadata such as date, mode, status, query count, generated timestamp, and feature flags. |
| `projects` | List of scored repository records for the dashboard. |

## `docs/data/archive_index.json`

Archive list for generated daily runs. The dashboard displays live entries by default.

| Field | Description |
| --- | --- |
| `date` | Report date. |
| `generated_at` | Timestamp used for archive ordering. |
| `mode` | `live` or `mock`. |
| `run_id` | Unique run identifier. |
| `daily_brief_path` | Relative path to the daily brief. |
| `json_path` | Relative path to daily project JSON. |
| `csv_path` | Relative path to daily project CSV. |
| `top_project` | Highest-ranked project for the run when available. |

## `data/processed/YYYY-MM-DD-github-insight-projects.csv`

Date-specific scored repository table.

| Field | Description |
| --- | --- |
| `date` | Report date assigned to the record. |
| `rank_today` | Rank within the run after sorting by score, stars, and name. |
| `full_name` | Repository owner/name. |
| `html_url` | GitHub repository URL. |
| `primary_audience` | Best-fit audience: `general_user`, `data_analyst`, or `data_scientist`. |
| `audience_tags` | Audiences with meaningful fit. |
| `overall_insight_score` | Final 0-100 ranking score. |
| `general_user_score` | Audience fit score for general users. |
| `data_analyst_score` | Audience fit score for data analysts. |
| `data_scientist_score` | Audience fit score for data scientists. |
| `usefulness_score` | Usefulness component. |
| `momentum_score` | Recency and popularity component. |
| `reproducibility_score` | Reproducibility component. |
| `data_asset_score` | Dataset/demo/notebook/dashboard component. |
| `dashboard_readiness_score` | Dashboard/demo/data/usage readiness signal. |
| `maintenance_score` | Maintenance and activity component. |
| `risk_score` | Risk penalty component. |
| `difficulty_level` | Heuristic difficulty label such as Beginner, Intermediate, Advanced, Research-heavy, or Unknown. |
| `recommended_action` | Deterministic next action such as Try today, Study for learning, or Skip for now. |
| `one_sentence_summary` | Concise repository summary using available evidence. |
| `why_it_matters` | Audience-oriented explanation. |
| `portfolio_project_idea` | Suggested portfolio framing. |
| `evidence` | Evidence bullets stored as a serialized list in CSV. |
| `risk_flags` | Risk flags stored as a serialized list in CSV. |
| `confidence` | High, medium, or low evidence confidence. |
| `language` | Primary language reported by GitHub. |
| `topics` | GitHub topics stored as a serialized list in CSV. |
| `stars` | Stargazer count at collection time. |
| `forks` | Fork count at collection time. |
| `open_issues` | Open issue count at collection time. |
| `license` | SPDX license ID or license name when available. |
| `pushed_at` | Last push timestamp from GitHub metadata. |
| `first_seen_date` | First date the repository appeared in local history. |
| `last_seen_date` | Latest date the repository appeared. |
| `days_seen` | Appearance count from local history. |
| `rank_previous` | Previous rank when history is available. |
| `rank_change` | Rank movement when history is available. |
| `star_delta_since_previous_seen` | Star delta when prior snapshot data is available. |
| `fork_delta_since_previous_seen` | Fork delta when prior snapshot data is available. |
| `source_status` | `live_github_api` or `mock_fixture`. |
| `image_asset_path` | Optional generated or fallback image asset path. |
| `image_prompt_path` | Optional image metadata/prompt path. |

## `data/processed/YYYY-MM-DD-github-insight-projects.json`

Date-specific structured JSON version of the scored repository records. It preserves lists and nested values without CSV serialization.

## `data/processed/github_repos_master.csv`

Append-friendly master table for scored repository records across runs. It uses the same core fields as the daily processed CSV.

## `data/raw/YYYY-MM-DD-github-api-raw.json`

Raw collection payload for audit and replay context.

| Field | Description |
| --- | --- |
| `mode` or source metadata | Indicates live API or mock fixture context when present. |
| `items` or query payloads | Raw repository objects or fixture records returned by the collector. |
| `rate_limit_remaining` | GitHub API rate-limit detail when available. |
| `query_count` | Number of configured queries attempted. |

## `reports/latest/latest-projects.json`

Compact latest project JSON used by reports and downstream review.

## `data/github_insight.sqlite`

SQLite database for durable local storage.

| Table | Purpose |
| --- | --- |
| `daily_runs` | One row per pipeline run with mode, status, timestamps, counts, and feature flags. |
| `repo_snapshots` | Raw repository snapshots by run/date. |
| `repo_enriched` | Enriched README, file, release, reproducibility, and risk signals. |
| `insight_records` | Final scored repository records. |
| `visual_assets` | Optional image/fallback metadata records. |

## Markdown Reports

| Path | Purpose |
| --- | --- |
| `reports/daily/YYYY-MM-DD-daily-brief.md` | Main daily summary. |
| `reports/daily/YYYY-MM-DD-general-user.md` | General user view. |
| `reports/daily/YYYY-MM-DD-data-analyst.md` | Data analyst view. |
| `reports/daily/YYYY-MM-DD-data-scientist.md` | Data scientist view. |
| `reports/daily/YYYY-MM-DD-action-list.md` | Practical next actions. |
| `reports/latest/latest-daily-brief.md` | Copy of the latest daily brief. |

## Dashboard-Only Derived Fields

The static dashboard adds display-only fields before embedding JSON into `docs/index.html`:

| Field | Description |
| --- | --- |
| `dashboard_risk_severity` | Low, Medium, or High based on `risk_score`. |
| `dashboard_confidence_label` | High, Medium, or Low display label from `confidence`. |
| `dashboard_evidence_summary` | Short evidence summary for card display. |
| `dashboard_caveat_summary` | Short caveat summary from risk flags. |

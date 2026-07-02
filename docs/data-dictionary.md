# Data Dictionary

## `data/processed/github_repos_master.csv`

| Field | Description |
| --- | --- |
| `date` | Report date used for the latest processed row. |
| `run_label` | Run label such as `0000`, `1200`, or `manual`. |
| `full_name` | Repository owner/name. |
| `html_url` | GitHub repository URL from collected metadata. |
| `description` | Repository description from collected metadata. |
| `language` | Primary language reported by GitHub. |
| `topics` | Comma-separated GitHub topics. |
| `stars` | Stargazer count at collection time. |
| `forks` | Fork count at collection time. |
| `open_issues` | Open issue count at collection time. |
| `pushed_at` | Last push timestamp from GitHub metadata. |
| `updated_at` | Last update timestamp from GitHub metadata. |
| `license` | SPDX license ID or license name when available. |
| `source_status` | `live_github_api`, `sample_fixture`, or fallback status. |
| `seen_before` | Whether this repository existed in local history before the run. |
| `recommended_profile` | Profile with the highest score. |
| `recommended_score` | Highest profile score. |
| `recommended_decision` | Build, Study, Save, or Skip. |
| `general_score` | Score for general users. |
| `data_analyst_score` | Score for data analysts. |
| `data_scientist_score` | Score for data scientists. |
| `skill_tags` | Inferred skill categories. |
| `recommended_action` | Concrete 30-60 minute next action. |
| `expected_output` | Deliverable expected from the action. |
| `portfolio_idea` | Suggested portfolio framing. |
| `evidence_limits` | Explicit limitation note. |

## `data/processed/github_insight_cards.json`

The JSON file preserves nested score components for each profile. It is the source for the dashboard.

## `data/history/seen_repos.json`

Tracks first seen date, latest seen date, appearance count, and latest score for deduplication and recurring report context.


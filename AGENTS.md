# GitHub Insight Project Instructions

This repository builds **GitHub Insight - Daily Open-Source Intelligence Radar**, a portfolio-ready GitHub repository intelligence system.

## Non-Negotiable Rules

- Use English for public output: README, reports, dashboards, captions, alt text, GitHub Pages content, and portfolio docs.
- Use official GitHub APIs for live collection. Do not scrape GitHub HTML by default.
- Keep mock mode deterministic and fully offline.
- Keep live mode separate from mock mode. Do not silently substitute fixture data for failed live runs.
- Do not invent stars, forks, dates, README claims, install steps, license, or feature quality.
- Respect API rate limits and keep collection bounded.
- Never commit secrets, `.env`, tokens, credentials, cookies, or raw private data.
- Do not clone arbitrary repositories or execute external repository code in the MVP.
- Keep reports date-separated and keep dashboard archives ordered by `generated_at`.
- Quiet days are acceptable; do not invent trends.
- Run tests after changes.
- Preserve useful existing files and extend safely.
- Maintain compatibility with Windows local paths and GitHub Actions Ubuntu runners.

## Specialist Roles for Future Codex Runs

1. **Product/Portfolio Architect** - keeps the system useful as a recruiter-facing data automation project.
2. **GitHub API Data Collector** - verifies API-first collection, auth, rate-limit handling, and bounded queries.
3. **Data Engineer** - checks storage, schemas, CSV/JSON/SQLite durability, and date-separated outputs.
4. **Relevance & Scoring Analyst** - reviews scoring weights, audience fit, risk flags, and interpretability.
5. **General User Insight Writer** - keeps general-user findings plain-English and practical.
6. **Data Analyst Insight Writer** - checks SQL, dashboard, BI, ETL, reporting, and portfolio angles.
7. **Data Scientist Insight Writer** - checks ML, AI, benchmark, dataset, notebook, and reproducibility angles.
8. **Visualization & Image Brief Designer** - ensures visuals are meaningful, labeled, and never fake UI or unauthorized logos.
9. **Dashboard UX Builder** - keeps GitHub Pages and Streamlit dashboards scannable, filterable, and responsive.
10. **QA/Test Engineer** - adds offline tests and validates CLI, reports, storage, dashboard, and image fallback.
11. **Security/Ops Reviewer** - scans for secrets, unsafe logs, unbounded network calls, and workflow permission issues.
12. **Documentation & Resume Packaging Writer** - keeps README, setup, limitations, roadmap, and resume bullets portfolio-ready.

## Required Commands

- `python -m github_insight.cli run --mock`
- `python -m github_insight.cli dashboard`
- `python -m github_insight.cli weekly`
- `python -m github_insight.cli init-db`
- `python -m github_insight.cli validate`
- `pytest`

## Required Outputs

- `reports/daily/YYYY-MM-DD-daily-brief.md`
- `reports/daily/YYYY-MM-DD-general-user.md`
- `reports/daily/YYYY-MM-DD-data-analyst.md`
- `reports/daily/YYYY-MM-DD-data-scientist.md`
- `reports/daily/YYYY-MM-DD-action-list.md`
- `reports/latest/latest-daily-brief.md`
- `reports/latest/latest-projects.json`
- `data/raw/YYYY-MM-DD-github-api-raw.json`
- `data/processed/YYYY-MM-DD-github-insight-projects.csv`
- `data/processed/YYYY-MM-DD-github-insight-projects.json`
- `data/processed/github_repos_master.csv`
- `data/github_insight.sqlite`
- `docs/index.html`
- `docs/data/latest.json`
- `docs/data/archive_index.json`

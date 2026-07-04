# GitHub Insight

GitHub Insight collects public GitHub repositories, scores them with transparent rules, and publishes a daily dashboard for people deciding what to try, study, or review.

- Live dashboard: https://leombe.github.io/github-insight-radar/
- Repository: https://github.com/LeombE/github-insight-radar
- Main command: `python -m github_insight.cli`

## Why This Exists

GitHub search results can be hard to judge from stars alone. This project adds a repeatable layer for comparing repositories by audience fit, recent activity, reproducibility signals, risk flags, and practical next action.

## Who It Helps

- General users looking for useful tools or self-hosted apps.
- Data analysts looking for SQL, BI, dashboard, ETL, and reporting examples.
- Data scientists looking for ML, AI, dataset, benchmark, and notebook projects.
- Reviewers who want to inspect a small end-to-end Python data project.

## Features

- Live collection through the GitHub API, plus deterministic offline mock mode.
- Static GitHub Pages dashboard with Stakeholder View, Today's Picks, filters, search, and Top 20 / 50 / 100 / All controls.
- Risk severity and confidence labels based on collected evidence.
- Date-separated Markdown, CSV, JSON, and SQLite outputs.
- GitHub Actions workflow for tests, scheduled live runs, dashboard rebuilds, and validation.
- Mock/live guard: mock runs do not overwrite production dashboard data by default.

## Quick Start

```powershell
python -m pip install -e ".[dev]"
python -m github_insight.cli run --mock
python -m github_insight.cli --output-root .pytest-tmp/mock-run dashboard
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
python -m pytest
```

Live run:

```powershell
$env:GH_PAT="your_github_token"
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli validate
```

`GH_PAT` is optional, but useful for higher GitHub API limits. Do not commit `.env` files or tokens.

## Main Commands

```powershell
python -m github_insight.cli run --mock
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli weekly
python -m github_insight.cli init-db
python -m github_insight.cli validate
```

## Documentation

- [Scoring methodology](docs/scoring-methodology.md)
- [Data dictionary](docs/data-dictionary.md)
- [Deployment guide](docs/deployment-guide.md)
- [Portfolio notes](docs/portfolio-notes.md)

## Current Limits

- GitHub Search API is rate-limited and not a complete real-time feed.
- Scores are heuristics based on available metadata and bounded README evidence.
- The system does not clone repositories or execute external project code.
- Risk and confidence labels are review aids, not security audits.
- Optional image and LLM paths are disabled by default and are not required for the core workflow.

## License

See the repository license file if one is present.
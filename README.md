# GitHub Insight

GitHub Insight is a daily open-source discovery dashboard. It collects public GitHub repositories, separates mature all-time recommendations from daily finds, and explains each project with practical signals such as score, risk, confidence, audience fit, and evidence.

- Live dashboard: https://leombe.github.io/github-insight-radar/
- Repository: https://github.com/LeombE/github-insight-radar
- Latest release: v1.2.0
- First click: open the live dashboard, then start with Evergreen Recommendations.

## Start Here

1. Open the live dashboard.
2. Read Evergreen Recommendations first. These are curated, mature repositories that are meant to be useful beyond a single day.
3. Choose a Stakeholder View: Overview, General User, Data Analyst, or Data Scientist.
4. Use Daily Discoveries for exploration. They come from the latest daily collection and are not meant to be all-time best recommendations.
5. Open a project card only after checking its score, risk, confidence, and evidence.

## What This Project Does

GitHub search can surface too many projects without enough context. GitHub Insight adds a small review layer that helps answer:

- Is this project worth opening?
- Who is it most useful for?
- Is it mature or just newly discovered?
- What evidence supports the recommendation?
- What should I do next?

The dashboard is designed for people who want quick, practical triage without reading the codebase first.

## Dashboard Guide

### Evergreen Recommendations

All-time recommendations from a curated source. These projects must pass strict quality gates such as strong adoption, forks, license evidence, README evidence, non-archived status, and activity checks. They are manually refreshed and separate from the daily run.

### Daily Discoveries

Recent projects collected from the GitHub API. Use this section to spot new or newly active projects. Some daily finds may have low adoption or weak evidence, so treat them as exploratory.

### Top Projects

The current daily project list sorted by the system's heuristic score. Use filters and search to narrow the list by stakeholder view, language, action, risk, date, and minimum score.

### Archive

Previous live dashboard runs ordered by generation time. The archive is useful for seeing how daily discoveries change over time.

### Methodology

A short explanation of how the dashboard scores and labels projects. For the full version, see [Scoring methodology](docs/scoring-methodology.md).

## How To Read A Project Card

- Score: a heuristic 0-100 signal for usefulness, activity, audience fit, maintenance, reproducibility, data/demo signals, and risk. It is not a definitive ranking.
- Risk: a quick review aid based on flags such as missing license, weak README evidence, unclear usage, stale activity, or issue signals. It is not a security audit.
- Confidence: how much supporting evidence the system found. High confidence means stronger evidence coverage, not guaranteed project quality.
- Best for: the audience most likely to benefit from the project.
- Why it matters: a short reason the project may be worth opening.
- Suggested use: a practical next step, such as trying the tool, studying the design, or using it as a reference.
- Key evidence: visible metadata and README-derived signals used to support the card.

## Who It Helps

- General users looking for useful tools, self-hosted apps, or practical open-source projects.
- Data analysts looking for SQL, BI, dashboard, ETL, reporting, and data workflow examples.
- Data scientists looking for ML, AI, dataset, benchmark, notebook, and reproducibility examples.
- Developers or reviewers who want to inspect a small, automated data product.

## Developer Setup

Install the project:

```powershell
python -m pip install -e ".[dev]"
```

Run a safe offline mock preview:

```powershell
python -m github_insight.cli run --mock
python -m github_insight.cli --output-root .pytest-tmp/mock-run dashboard
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
python -m pytest
```

Run a live collection:

```powershell
$env:GH_PAT="your_github_token"
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli validate
```

`GH_PAT` is optional, but useful for higher GitHub API limits. Do not commit `.env` files or tokens.

Manual evergreen refresh:

```powershell
python -m github_insight.cli evergreen
python -m github_insight.cli dashboard
```

## Main Commands

```powershell
python -m github_insight.cli run --mock
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli evergreen
python -m github_insight.cli weekly
python -m github_insight.cli init-db
python -m github_insight.cli validate
```

## Documentation

- [Scoring methodology](docs/scoring-methodology.md)
- [Data dictionary](docs/data-dictionary.md)
- [Deployment guide](docs/deployment-guide.md)
- [Portfolio notes](docs/portfolio-notes.md)

## Limits

- GitHub Search API is rate-limited and not a complete real-time feed.
- Scores are heuristic review aids based on available metadata and bounded README evidence.
- Risk and confidence labels help with triage; they do not replace manual review.
- The system does not clone repositories or execute external project code.
- Optional image and LLM paths are disabled by default and are not required for the core workflow.

## License

See the repository license file if one is present.

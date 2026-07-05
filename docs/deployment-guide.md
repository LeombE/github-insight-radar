# Deployment Guide

This guide covers local runs, GitHub Actions, GitHub Pages, and the mock/live safety guard.

## Install

```powershell
python -m pip install -e ".[dev]"
```

## Offline Mock Run

Mock mode is deterministic and does not need network access. By default it writes to a preview output root, not production dashboard files.

```powershell
python -m github_insight.cli run --mock
python -m github_insight.cli --output-root .pytest-tmp/mock-run dashboard
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
```

Expected preview folder:

```text
.pytest-tmp/mock-run/
```

Only publish mock data intentionally:

```powershell
python -m github_insight.cli run --mock --publish-mock
$env:ALLOW_MOCK_PUBLISH="true"
```

## Live Run

Live mode uses the GitHub API. `GH_PAT` is optional but recommended for higher rate limits.

```powershell
$env:GH_PAT="your_github_token"
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli validate
```

If live collection fails, the command fails clearly and does not silently use mock data.


## Manual Evergreen Refresh

Evergreen Recommendations are curated all-time recommendations and are intentionally separate from the daily workflow. Refresh them manually when the curated list changes or when you want updated adoption/activity evidence:

```powershell
$env:GH_PAT="your_github_token"
python -m github_insight.cli evergreen
python -m github_insight.cli dashboard
python -m github_insight.cli validate
```

The command reads `config/evergreen_repos.yml`, fetches current public GitHub metadata, applies strict quality gates, and writes `docs/data/evergreen.json`. It does not modify `docs/data/latest.json`, `docs/data/archive_index.json`, raw daily data, processed daily data, reports, assets, or the GitHub Actions schedule.

## GitHub Pages

The static site is generated in:

```text
docs/index.html
```

Dashboard data lives in:

```text
docs/data/latest.json
docs/data/archive_index.json
docs/data/evergreen.json
```

Publish GitHub Pages from the default branch and `/docs` folder.

Public dashboard:

```text
https://leombe.github.io/github-insight-radar/
```

## GitHub Actions

Workflows:

| Workflow | Purpose |
| --- | --- |
| `.github/workflows/ci.yml` | Tests and lint checks. |
| `.github/workflows/daily_github_insight.yml` | Scheduled/manual daily run. |

The daily workflow runs around 00:17 and 12:17 Malaysia time:

```yaml
cron: "17 16,4 * * *"
```

It installs the package, runs tests, generates live outputs by default, rebuilds the dashboard, validates outputs, and commits generated live files only when they changed.

Manual `mock_mode=true` runs use `.pytest-tmp/mock-run` and skip production commits.

## Required Settings

- GitHub Actions enabled.
- Workflow permission allows `contents: write` if generated live outputs should be committed.
- GitHub Pages publishes from `/docs` on the default branch.

Optional:

| Name | Type | Purpose |
| --- | --- | --- |
| `GH_PAT` | Secret | Higher GitHub API limits. |
| `OPENAI_API_KEY` | Secret | Optional future image/LLM use only. Not required for the core workflow. |
| `ENABLE_IMAGE_GENERATION` | Variable | Keep `false` unless intentionally testing optional images. |
| `ENABLE_LLM_SUMMARY` | Variable | Keep `false` unless intentionally enabling an LLM path. |

## Validation

```powershell
python -m github_insight.cli validate
python -m pytest
python -m ruff check github_insight scripts tests
```

For mock preview output:

```powershell
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
```

## Production Checklist

Before committing dashboard outputs:

- `docs/data/latest.json` has `run.mode` set to `live`.
- `docs/index.html` contains `LIVE RUN`.
- `docs/index.html` does not contain old mock repositories such as `sample-org`.
- No `.env`, token, cookie, credential, or raw private data file is staged.
- `.pytest-tmp/` is not committed.

## Recovery

If production docs are generated from the wrong source:

1. Do not commit the bad files.
2. Restore from the latest known-good live commit or rerun the live workflow.
3. Rebuild with `python -m github_insight.cli dashboard` only after confirming `docs/data/latest.json` is live.
4. Run validation and tests before pushing.
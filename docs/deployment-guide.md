# Deployment Guide

This guide covers local operation, GitHub Actions automation, and GitHub Pages publishing for GitHub Insight.

## Local Installation

```powershell
cd "C:\Users\Admin\OneDrive\Documents\Github Insight"
python -m pip install -e ".[dev]"
```

## Safe Offline Mock Preview

Mock mode is deterministic and fully offline. By default, it writes to an isolated preview root so production GitHub Pages files are not overwritten.

```powershell
python -m github_insight.cli run --mock
python -m github_insight.cli --output-root .pytest-tmp/mock-run dashboard
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
```

Expected preview root:

```text
.pytest-tmp/mock-run/
```

Only publish mock data intentionally with one of these controls:

```powershell
python -m github_insight.cli run --mock --publish-mock
$env:ALLOW_MOCK_PUBLISH="true"
```

Do not use these controls for the production GitHub Pages dashboard unless a mock demo is explicitly intended.

## Local Live Run

Live mode uses the official GitHub API. A token is optional but recommended.

```powershell
$env:GH_PAT="your_github_token"
python -m github_insight.cli run --date today
python -m github_insight.cli dashboard
python -m github_insight.cli validate
```

If live GitHub API collection fails, the CLI fails clearly and does not silently substitute mock fixture data.

## Static GitHub Pages Dashboard

The production static dashboard is generated at:

```text
docs/index.html
```

Dashboard data files:

```text
docs/data/latest.json
docs/data/archive_index.json
```

The public dashboard is expected at:

```text
https://leombe.github.io/github-insight-radar/
```

## GitHub Pages Settings

1. Push the repository to GitHub.
2. Open repository settings.
3. Go to Pages.
4. Set Source to deploy from a branch.
5. Select the default branch.
6. Select `/docs` as the publishing folder.
7. Save and wait for Pages deployment to complete.

## GitHub Actions Workflows

This repository includes two workflows:

| Workflow | Purpose |
| --- | --- |
| `.github/workflows/ci.yml` | Pull request and push validation. |
| `.github/workflows/daily_github_insight.yml` | Scheduled/manual daily intelligence run. |

The daily workflow runs on this schedule:

```yaml
cron: "17 16,4 * * *"
```

That corresponds to approximately 00:17 and 12:17 Malaysia time.

The daily workflow performs these steps:

1. Checkout repository.
2. Set up Python 3.11.
3. Install the package with `python -m pip install -e ".[dev]"`.
4. Run `python -m pytest`.
5. Run the live daily pipeline by default.
6. Rebuild the dashboard.
7. Validate outputs.
8. Commit generated live outputs only when files changed.

Manual `mock_mode=true` runs write to `.pytest-tmp/mock-run`, rebuild/validate that preview root, and skip production commits.

## Required Permissions and Secrets

Repository settings:

- Actions enabled.
- Workflow permission set to allow `contents: write` if the daily workflow should commit generated live outputs.
- GitHub Pages configured to publish from `/docs` on the default branch.

Optional secrets and variables:

| Name | Type | Purpose |
| --- | --- | --- |
| `GH_PAT` | Secret | Optional GitHub token for higher API limits. |
| `OPENAI_API_KEY` | Secret | Optional future image/LLM use only. Not required for the core pipeline. |
| `ENABLE_IMAGE_GENERATION` | Variable | Keep `false` unless intentionally enabling optional images. |
| `ENABLE_LLM_SUMMARY` | Variable | Keep `false` unless an LLM summary path is intentionally enabled. |

The workflow also receives GitHub's default `GITHUB_TOKEN` automatically.

## Validation Commands

Run these before publishing or opening a pull request:

```powershell
python -m github_insight.cli validate
python -m pytest
python -m ruff check github_insight scripts tests
```

Use preview-root validation for mock runs:

```powershell
python -m github_insight.cli --output-root .pytest-tmp/mock-run validate
```

## Production Safety Checklist

Before committing generated dashboard files, verify:

- `docs/data/latest.json` has `run.mode` set to `live`.
- `docs/index.html` contains `LIVE RUN`.
- `docs/index.html` does not contain old mock repositories such as `sample-org`.
- No `.env`, token, cookie, credential, or raw private data file is staged.
- Mock preview files under `.pytest-tmp/` are not committed.

## Failure Handling

- Live API failure returns a clear CLI error and does not pretend fixture data is live.
- Validation warns or fails when production `docs/data/latest.json` contains mock data unless mock publishing is explicitly allowed.
- Quiet days are valid. The system should not invent trends or repository facts.

## Rollback and Recovery

If production docs are accidentally generated from the wrong source:

1. Do not commit the bad generated files.
2. Restore from the latest known-good live commit or rerun the live workflow.
3. Rebuild with `python -m github_insight.cli dashboard` only after confirming `docs/data/latest.json` is live.
4. Run validation and tests before pushing.

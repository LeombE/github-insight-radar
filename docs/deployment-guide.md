# Deployment Guide

## Local Run

Use sample mode for a deterministic offline demo:

```powershell
python -m scripts.github_insight --sample --date 2026-07-02 --run-label manual
```

Use live GitHub API mode:

```powershell
$env:GITHUB_TOKEN="your_token"
python -m scripts.github_insight --fetch --date 2026-07-02 --run-label 1200
```

The token is optional but recommended because unauthenticated GitHub API rate limits are low.

## GitHub Actions

1. Push this repository to GitHub.
2. Ensure Actions has `contents: write` permission.
3. Optionally add a `GITHUB_TOKEN` secret or use the default Actions token.
4. Run the `Daily GitHub Insight` workflow manually once.

The workflow runs tests, generates reports, and commits only if output files changed.

## Schedule

The workflow schedule is twice daily:

| Malaysia time | UTC cron |
| --- | --- |
| 00:00 | `0 16 * * *` |
| 12:00 | `0 4 * * *` |

## Failure Handling

If live fetch fails and strict mode is not enabled, the pipeline uses `sample_fixture` fallback and writes the fetch error into the report evidence block. This makes failed live data collection visible instead of silently mixing stale data with current claims.


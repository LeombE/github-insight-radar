# Portfolio Notes

This page keeps portfolio-facing context out of the main README. It is optional reading for reviewers who want to understand what the project demonstrates.

## What This Project Demonstrates

- API-first data collection using the GitHub REST API.
- A deterministic offline mock mode for local testing and demos.
- Structured outputs in Markdown, CSV, JSON, SQLite, and static HTML.
- A static dashboard with stakeholder views, Today's Picks, filters, search, risk labels, and confidence labels.
- A mock/live guard that prevents offline demo data from replacing production dashboard data by default.
- CI-style checks with pytest and ruff.
- GitHub Actions automation for scheduled live runs and GitHub Pages publishing.

## Resume Bullets

- Built a Python pipeline that collects public GitHub repository metadata, scores projects with transparent rules, and publishes daily Markdown/CSV/JSON/SQLite outputs.
- Added a static GitHub Pages dashboard with stakeholder views, search, filters, risk severity, confidence labels, and archive support.
- Implemented safe mock/live behavior so deterministic offline runs do not overwrite production dashboard data by default.
- Added tests and lint checks for CLI behavior, dashboard rendering, scoring, storage, reports, validation, and image fallback.

## Review Notes

The project is intentionally conservative. It does not clone external repositories, execute third-party code, or invent repository facts when evidence is missing. Scores are meant for triage and review, not for declaring absolute project quality.
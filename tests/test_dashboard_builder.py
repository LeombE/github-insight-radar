import json

from github_insight.cli import main


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def test_dashboard_rebuild_from_latest_json(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    preview = tmp_path / PREVIEW_ROOT
    assert main(["--output-root", str(preview), "dashboard"]) == 0
    html = (preview / "docs" / "index.html").read_text(encoding="utf-8")
    assert "GitHub Daily Intelligence" in html
    assert "Top Projects" in html
    assert "MOCK RUN" in html
    assert 'id="displayLimit"' in html
    assert '<option value="20" selected>Top 20</option>' in html
    assert '<option value="50">Top 50</option>' in html
    assert '<option value="100">Top 100</option>' in html
    assert '<option value="all">All</option>' in html
    assert 'id="search"' in html
    assert 'id="language"' in html
    assert 'id="action"' in html
    assert 'id="risk"' in html
    assert "All languages" in html
    assert "All actions" in html
    assert "Has risk flags" in html
    assert "Low risk" in html
    assert "Medium risk" in html
    assert "High risk" in html
    assert "Risk flagged" not in html
    assert "dashboard_risk_severity" in html
    assert "dashboard_confidence_label" in html
    assert "dashboard_evidence_summary" in html
    assert "dashboard_caveat_summary" in html
    assert "risk-badge" in html
    assert "confidence-badge" in html
    assert "Key evidence:" in html
    assert "Caveat:" in html
    assert "riskSeverityClass" in html
    assert "confidenceClass" in html
    assert "searchableText" in html
    assert "matchesRisk" in html
    assert "selectedLanguage" in html
    assert "selectedAction" in html
    assert "selectedRisk" in html
    assert "search.addEventListener('input', render)" in html
    assert "language.addEventListener('change', render)" in html
    assert "action.addEventListener('change', render)" in html
    assert "risk.addEventListener('change', render)" in html
    assert "filtered.slice(0, limit)" in html
    assert ".slice(0, 30)" not in html
    assert "No archive entries yet." in html


def test_default_archive_hides_mock_and_legacy_entries_when_live_entries_exist(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    preview = tmp_path / PREVIEW_ROOT
    archive_path = preview / "docs" / "data" / "archive_index.json"
    archive_path.write_text(
        json.dumps(
            [
                {
                    "date": "2026-07-03",
                    "generated_at": "2026-07-03T00:00:00+00:00",
                    "mode": "live",
                    "daily_brief_path": "reports/daily/2026-07-03-daily-brief.md",
                    "top_project": "real-org/live-dashboard",
                },
                {
                    "date": "2026-07-02",
                    "generated_at": "2026-07-02T00:00:00+00:00",
                    "mode": "live",
                    "daily_brief_path": "reports/daily/2026-07-02-daily-brief.md",
                    "top_project": "sample-org/analytics-dashboard-starter",
                },
                {
                    "date": "2026-07-01",
                    "generated_at": "2026-07-01T00:00:00+00:00",
                    "mode": "mock",
                    "daily_brief_path": "reports/daily/2026-07-01-daily-brief.md",
                    "top_project": "sample-org/explicit-mock-project",
                },
            ]
        ),
        encoding="utf-8",
    )

    assert main(["--output-root", str(preview), "dashboard"]) == 0

    html = (preview / "docs" / "index.html").read_text(encoding="utf-8")
    archive_section = html.split("<h2>Archive</h2>", 1)[1].split("<h2>Methodology</h2>", 1)[0]
    assert "real-org/live-dashboard" in archive_section
    assert "sample-org" not in archive_section

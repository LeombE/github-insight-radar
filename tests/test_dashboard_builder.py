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

import json

from github_insight.cli import main


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def test_dashboard_rebuild_from_latest_json(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    preview = tmp_path / PREVIEW_ROOT
    evergreen_path = preview / "docs" / "data" / "evergreen.json"
    evergreen_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generated_at": "2026-07-02T00:00:00+00:00",
                "repositories": [
                    {
                        "full_name": "example/community-standard",
                        "html_url": "https://github.com/example/community-standard",
                        "description": "A widely adopted community standard project.",
                        "language": "Python",
                        "topics": ["analytics"],
                        "stakeholders": ["general_user", "data_analyst"],
                        "category": "analytics",
                        "reason": "Mature project for broad users.",
                        "suggested_use": "Study reliable product and analytics patterns.",
                        "tags": ["analytics"],
                        "stars": 25000,
                        "forks": 4200,
                        "license": "Apache-2.0",
                        "archived": False,
                        "pushed_at": "2026-07-01T00:00:00Z",
                        "has_readme": True,
                        "recent_activity": True,
                        "recommendation_level": "community_standard",
                        "quality_gate_passed": True,
                        "evidence": ["Stars: 25000", "Forks: 4200", "License: Apache-2.0"],
                        "risk_note": "All required evergreen quality gates passed.",
                    }
                ],
                "excluded": [],
            }
        ),
        encoding="utf-8",
    )
    assert main(["--output-root", str(preview), "dashboard"]) == 0
    html = (preview / "docs" / "index.html").read_text(encoding="utf-8")
    assert "GitHub Daily Intelligence" in html
    assert "Evergreen Recommendations" in html
    assert "Daily Discoveries" in html
    assert "Top Projects" in html
    assert "Today's Picks" in html
    assert "MOCK RUN" in html
    assert 'id="stakeholderView"' in html
    assert '<option value="overview" selected>Overview</option>' in html
    assert '<option value="general_user">General User</option>' in html
    assert '<option value="data_analyst">Data Analyst</option>' in html
    assert '<option value="data_scientist">Data Scientist</option>' in html
    assert "Portfolio Reviewer / Recruiter" not in html
    assert "portfolio_reviewer" not in html
    assert 'id="evergreenCards"' in html
    assert 'id="todayPicks"' in html
    assert 'id="displayLimit"' in html
    assert '<option value="20" selected>Top 20</option>' in html
    assert '<option value="50">Top 50</option>' in html
    assert '<option value="100">Top 100</option>' in html
    assert '<option value="all">All</option>' in html
    assert 'id="search"' in html
    assert 'id="audience"' in html
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
    assert "card-head" in html
    assert "score-lockup" in html
    assert "meta-grid" in html
    assert "action-callout" in html
    assert "explanation-grid" in html
    assert "Best for:" in html
    assert "Why it matters:" in html
    assert "Portfolio angle:" in html
    assert "Risk note:" in html
    assert "Key evidence:" in html
    assert "example/community-standard" in html
    assert "community_standard" in html
    assert "renderEvergreen" in html
    assert "evergreenMatches" in html
    assert "stakeholderMatches" in html
    assert "selectTodayPicks" in html
    assert "renderTodayPicks" in html
    assert "selectedStakeholder" in html
    assert "riskSeverityClass" in html
    assert "confidenceClass" in html
    assert "searchableText" in html
    assert "matchesRisk" in html
    assert "selectedLanguage" in html
    assert "selectedAction" in html
    assert "selectedRisk" in html
    assert "stakeholderView.addEventListener('change', render)" in html
    assert "search.addEventListener('input', render)" in html
    assert "language.addEventListener('change', render)" in html
    assert "action.addEventListener('change', render)" in html
    assert "risk.addEventListener('change', render)" in html
    assert "filtered.slice(0, limit)" in html
    assert "filtered.slice(0, 3)" in html
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


from github_insight.cli import main


def test_cli_mock_generates_required_outputs(tmp_path):
    code = main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"])
    assert code == 0
    required = [
        "reports/daily/2026-07-02-daily-brief.md",
        "reports/daily/2026-07-02-general-user.md",
        "reports/daily/2026-07-02-data-analyst.md",
        "reports/daily/2026-07-02-data-scientist.md",
        "reports/daily/2026-07-02-action-list.md",
        "reports/latest/latest-daily-brief.md",
        "reports/latest/latest-projects.json",
        "data/raw/2026-07-02-github-api-raw.json",
        "data/processed/2026-07-02-github-insight-projects.csv",
        "data/processed/2026-07-02-github-insight-projects.json",
        "data/processed/github_repos_master.csv",
        "data/github_insight.sqlite",
        "docs/index.html",
        "docs/data/latest.json",
        "docs/data/archive_index.json",
    ]
    for relative in required:
        path = tmp_path / relative
        assert path.exists(), relative
        assert path.stat().st_size > 0, relative


def test_cli_dashboard_and_validate(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    assert main(["--output-root", str(tmp_path), "dashboard"]) == 0
    assert main(["--output-root", str(tmp_path), "validate"]) == 0
    assert (tmp_path / "docs" / "index.html").exists()


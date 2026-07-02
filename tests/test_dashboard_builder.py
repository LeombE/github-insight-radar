from github_insight.cli import main


def test_dashboard_rebuild_from_latest_json(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    assert main(["--output-root", str(tmp_path), "dashboard"]) == 0
    html = (tmp_path / "docs" / "index.html").read_text(encoding="utf-8")
    assert "GitHub Daily Intelligence" in html
    assert "Top Projects" in html

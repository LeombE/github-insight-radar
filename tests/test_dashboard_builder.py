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
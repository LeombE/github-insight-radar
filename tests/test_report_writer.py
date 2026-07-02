import json

from github_insight.cli import main


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def test_report_writer_outputs_structured_report_data(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    preview = tmp_path / PREVIEW_ROOT
    report = preview / "reports" / "daily" / "2026-07-02-daily-brief.md"
    text = report.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "Top Overall Projects" in text
    assert "Data Files" in text
    data = json.loads(
        (preview / "data" / "processed" / "2026-07-02-github-insight-projects.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["projects"]
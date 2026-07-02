import json

import pytest

from github_insight.cli import main


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def _write_live_sentinels(root):
    docs = root / "docs"
    data = docs / "data"
    data.mkdir(parents=True, exist_ok=True)
    (docs / "index.html").write_text("LIVE_SENTINEL", encoding="utf-8")
    (data / "latest.json").write_text(
        json.dumps({"run": {"mode": "live", "date": "2026-07-02"}, "projects": []}),
        encoding="utf-8",
    )
    (data / "archive_index.json").write_text(
        json.dumps([{"date": "2026-07-02", "mode": "live"}]),
        encoding="utf-8",
    )


def _required_outputs(date="2026-07-02"):
    return [
        f"reports/daily/{date}-daily-brief.md",
        f"reports/daily/{date}-general-user.md",
        f"reports/daily/{date}-data-analyst.md",
        f"reports/daily/{date}-data-scientist.md",
        f"reports/daily/{date}-action-list.md",
        "reports/latest/latest-daily-brief.md",
        "reports/latest/latest-projects.json",
        f"data/raw/{date}-github-api-raw.json",
        f"data/processed/{date}-github-insight-projects.csv",
        f"data/processed/{date}-github-insight-projects.json",
        "data/processed/github_repos_master.csv",
        "data/github_insight.sqlite",
        "docs/index.html",
        "docs/data/latest.json",
        "docs/data/archive_index.json",
    ]


def test_cli_mock_generates_preview_outputs_without_overwriting_production_docs(tmp_path):
    _write_live_sentinels(tmp_path)

    code = main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"])

    assert code == 0
    assert (tmp_path / "docs/index.html").read_text(encoding="utf-8") == "LIVE_SENTINEL"
    latest = json.loads((tmp_path / "docs/data/latest.json").read_text(encoding="utf-8"))
    assert latest["run"]["mode"] == "live"

    preview = tmp_path / PREVIEW_ROOT
    for relative in _required_outputs():
        path = preview / relative
        assert path.exists(), relative
        assert path.stat().st_size > 0, relative
    archive = json.loads((preview / "docs/data/archive_index.json").read_text(encoding="utf-8"))
    assert archive[0]["mode"] == "mock"
    assert archive[0]["run_id"].startswith("mock-")


def test_cli_mock_publish_writes_production_docs_when_explicit(tmp_path):
    assert main([
        "--output-root",
        str(tmp_path),
        "run",
        "--mock",
        "--publish-mock",
        "--date",
        "2026-07-02",
    ]) == 0
    latest = json.loads((tmp_path / "docs/data/latest.json").read_text(encoding="utf-8"))
    assert latest["run"]["mode"] == "mock"
    assert (tmp_path / PREVIEW_ROOT).exists() is False


def test_cli_mock_publish_can_be_enabled_by_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ALLOW_MOCK_PUBLISH", "true")

    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0

    latest = json.loads((tmp_path / "docs/data/latest.json").read_text(encoding="utf-8"))
    assert latest["run"]["mode"] == "mock"


def test_validate_warns_for_mock_production_docs(tmp_path, capsys):
    (tmp_path / ".git").mkdir()
    assert main([
        "--output-root",
        str(tmp_path),
        "run",
        "--mock",
        "--publish-mock",
        "--date",
        "2026-07-02",
    ]) == 0

    assert main(["--output-root", str(tmp_path), "validate"]) == 0
    captured = capsys.readouterr()
    assert "production docs/data/latest.json contains mock data" in captured.err
    assert "Validation PASS for 2026-07-02 with warnings" in captured.out


def test_validate_can_fail_strictly_for_mock_production_docs(tmp_path):
    (tmp_path / ".git").mkdir()
    assert main([
        "--output-root",
        str(tmp_path),
        "run",
        "--mock",
        "--publish-mock",
        "--date",
        "2026-07-02",
    ]) == 0

    with pytest.raises(SystemExit) as excinfo:
        main(["--output-root", str(tmp_path), "validate", "--strict-production"])
    assert "production docs/data/latest.json contains mock data" in str(excinfo.value)


def test_cli_dashboard_and_validate_preview_output(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    preview = tmp_path / PREVIEW_ROOT
    assert main(["--output-root", str(preview), "dashboard"]) == 0
    assert main(["--output-root", str(preview), "validate"]) == 0
    assert (preview / "docs" / "index.html").exists()
import json

from github_insight.cli import main
from github_insight.image_generator import create_fallback_project_card
from github_insight.models import InsightRecord, RunMetadata


def test_image_fallback_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    payload = json.loads((tmp_path / "docs" / "data" / "latest.json").read_text(encoding="utf-8"))
    run = RunMetadata(**payload["run"])
    record = InsightRecord(**payload["projects"][0])
    image_path, prompt_path = create_fallback_project_card(tmp_path, run, record)
    assert image_path.exists()
    assert prompt_path.exists()
    metadata = json.loads(prompt_path.read_text(encoding="utf-8"))
    assert metadata["status"] == "fallback"
    assert metadata["alt_text"]


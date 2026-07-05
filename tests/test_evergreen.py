import json
from datetime import datetime, timezone
from pathlib import Path

from github_insight.cli import main
from github_insight.evergreen import build_evergreen_payload


FIXTURE = Path(__file__).parent / "fixtures" / "evergreen_metadata.json"


def _write_config(tmp_path):
    path = tmp_path / "evergreen_repos.yml"
    path.write_text(
        """
version: 1
recent_activity_days: 365
repositories:
  - full_name: example/community-standard
    stakeholders: [general_user, data_analyst]
    category: analytics
    reason: Mature project for broad users.
    suggested_use: Study reliable product and analytics patterns.
    tags: [analytics]
  - full_name: example/mature-reference
    stakeholders: [data_analyst]
    category: visualization
    reason: Mature reference for dashboard work.
    suggested_use: Study visualization architecture.
    tags: [visualization]
  - full_name: example/emerging-project
    stakeholders: [data_scientist]
    category: machine-learning
    reason: Interesting but not mature enough for evergreen.
    suggested_use: Track separately from evergreen recommendations.
    tags: [machine-learning]
  - full_name: example/no-license
    stakeholders: [data_scientist]
    category: data
    reason: Strong adoption but missing license evidence.
    suggested_use: Exclude until licensing is clear.
    tags: [data]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return path


def test_evergreen_quality_gates_classify_visible_and_excluded_repos(tmp_path):
    config_path = _write_config(tmp_path)
    payload = build_evergreen_payload(
        config_path=config_path,
        metadata_fixture_path=FIXTURE,
        now=datetime(2026, 7, 5, tzinfo=timezone.utc),
    )

    visible = {item["full_name"]: item for item in payload["repositories"]}
    excluded = {item["full_name"]: item for item in payload["excluded"]}

    assert visible["example/community-standard"]["recommendation_level"] == "community_standard"
    assert visible["example/community-standard"]["recent_activity"] is True
    assert visible["example/mature-reference"]["recommendation_level"] == "mature_reference"
    assert visible["example/mature-reference"]["recent_activity"] is False
    assert "example/emerging-project" in excluded
    assert "stars below mature threshold" in excluded["example/emerging-project"]["excluded_reasons"]
    assert "license missing" in excluded["example/no-license"]["excluded_reasons"]


def test_cli_evergreen_writes_manual_output_without_daily_latest_or_archive(tmp_path):
    config_path = _write_config(tmp_path)
    assert (
        main(
            [
                "--output-root",
                str(tmp_path),
                "evergreen",
                "--config",
                str(config_path),
                "--metadata-fixture",
                str(FIXTURE),
            ]
        )
        == 0
    )

    output_path = tmp_path / "docs" / "data" / "evergreen.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert output_path.exists()
    assert payload["source_mode"] == "fixture"
    assert len(payload["repositories"]) == 2
    assert not (tmp_path / "docs" / "data" / "latest.json").exists()
    assert not (tmp_path / "docs" / "data" / "archive_index.json").exists()


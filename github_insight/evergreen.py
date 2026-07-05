"""Manual evergreen recommendation builder."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from github_insight.config import load_yaml_file
from github_insight.github_client import GitHubClient
from github_insight.models import normalize_topics, safe_int, safe_text, utc_now_iso


VISIBLE_STAKEHOLDERS = {"general_user", "data_analyst", "data_scientist"}
COMMUNITY_STANDARD = "community_standard"
MATURE_REFERENCE = "mature_reference"
EMERGING_PROJECT = "emerging_project"
DEFAULT_RECENT_ACTIVITY_DAYS = 365


def load_evergreen_config(path: Path) -> dict[str, Any]:
    payload = load_yaml_file(path, default={})
    if not isinstance(payload, dict):
        raise ValueError("Evergreen config must be a mapping.")
    repositories = payload.get("repositories", [])
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("Evergreen config must include a non-empty repositories list.")
    for item in repositories:
        if not isinstance(item, dict) or not str(item.get("full_name", "")).strip():
            raise ValueError("Every evergreen repository entry must include full_name.")
        stakeholders = _normalize_stakeholders(item.get("stakeholders", []))
        if not stakeholders:
            raise ValueError(f"{item.get('full_name')} must include at least one supported stakeholder.")
    return payload


def load_metadata_fixture(path: Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_items: Any = payload.get("repositories", payload)
    if isinstance(raw_items, dict):
        return {str(key).lower(): value for key, value in raw_items.items() if isinstance(value, dict)}
    if isinstance(raw_items, list):
        return {
            str(item.get("full_name", "")).lower(): item
            for item in raw_items
            if isinstance(item, dict) and item.get("full_name")
        }
    raise ValueError("Evergreen metadata fixture must be a mapping or a repositories list.")


def build_evergreen_payload(
    *,
    config_path: Path,
    client: GitHubClient | None = None,
    metadata_fixture_path: Path | None = None,
    now: datetime | None = None,
    source_config_label: str | None = None,
) -> dict[str, Any]:
    config = load_evergreen_config(config_path)
    recent_activity_days = safe_int(config.get("recent_activity_days"), DEFAULT_RECENT_ACTIVITY_DAYS)
    now = now or datetime.now(timezone.utc)
    fixture = load_metadata_fixture(metadata_fixture_path) if metadata_fixture_path else {}
    source_mode = "fixture" if metadata_fixture_path else "live_github_api"
    if not fixture and client is None:
        client = GitHubClient()

    visible: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for curated in config.get("repositories", []):
        metadata = fixture.get(str(curated["full_name"]).lower())
        if metadata is None:
            if client is None:
                raise ValueError(f"Missing evergreen metadata for {curated['full_name']}.")
            metadata = _fetch_live_metadata(client, str(curated["full_name"]))
        record = _build_record(curated, metadata, recent_activity_days, now)
        if record["quality_gate_passed"]:
            visible.append(record)
        else:
            excluded.append(record)

    visible.sort(key=lambda item: (_level_rank(item["recommendation_level"]), item["stars"], item["forks"]), reverse=True)
    excluded.sort(key=lambda item: item["full_name"].lower())
    return {
        "schema_version": 1,
        "generated_at": utc_now_iso(),
        "source_mode": source_mode,
        "source_config": source_config_label or _safe_source_config(config_path),
        "quality_gates": {
            COMMUNITY_STANDARD: {
                "stars_min": 10000,
                "forks_min": 1000,
                "requires_license": True,
                "requires_readme": True,
                "requires_not_archived": True,
                "requires_recent_activity_days": recent_activity_days,
            },
            MATURE_REFERENCE: {
                "stars_min": 3000,
                "forks_min": 300,
                "requires_license": True,
                "requires_readme": True,
                "requires_not_archived": True,
            },
        },
        "repositories": visible,
        "excluded": excluded,
    }


def _safe_source_config(path: Path) -> str:
    if path.is_absolute():
        return path.name
    return path.as_posix()


def _fetch_live_metadata(client: GitHubClient, full_name: str) -> dict[str, Any]:
    payload = client.repository(full_name).data
    if not isinstance(payload, dict):
        raise ValueError(f"GitHub API returned invalid repository metadata for {full_name}.")
    payload = dict(payload)
    payload["readme_text"] = client.readme_text(full_name)
    return payload


def _build_record(
    curated: dict[str, Any],
    metadata: dict[str, Any],
    recent_activity_days: int,
    now: datetime,
) -> dict[str, Any]:
    full_name = safe_text(metadata.get("full_name") or curated.get("full_name"))
    stars = safe_int(metadata.get("stargazers_count", metadata.get("stars")))
    forks = safe_int(metadata.get("forks_count", metadata.get("forks")))
    license_value = _license_value(metadata)
    readme_text = str(metadata.get("readme_text") or metadata.get("readme") or "")
    has_readme = bool(readme_text.strip()) or bool(metadata.get("has_readme"))
    archived = bool(metadata.get("archived", False))
    pushed_at = safe_text(metadata.get("pushed_at"))
    recent_activity = _has_recent_activity(pushed_at, recent_activity_days, now)
    exclusion_reasons = _exclusion_reasons(stars, forks, license_value, has_readme, archived)
    level = EMERGING_PROJECT

    if not exclusion_reasons and stars >= 10000 and forks >= 1000 and recent_activity:
        level = COMMUNITY_STANDARD
    elif not exclusion_reasons and stars >= 3000 and forks >= 300:
        level = MATURE_REFERENCE
    else:
        level = EMERGING_PROJECT
        if stars < 3000:
            exclusion_reasons.append("stars below mature threshold")
        if forks < 300:
            exclusion_reasons.append("forks below mature threshold")

    quality_gate_passed = level in {COMMUNITY_STANDARD, MATURE_REFERENCE}
    risk_note = "All required evergreen quality gates passed."
    if level == MATURE_REFERENCE and not recent_activity:
        risk_note = "Mature reference; recent activity was not required for this quality tier."
    if not quality_gate_passed:
        risk_note = "; ".join(dict.fromkeys(exclusion_reasons))

    return {
        "full_name": full_name,
        "html_url": safe_text(metadata.get("html_url"), f"https://github.com/{full_name}"),
        "description": safe_text(metadata.get("description"), ""),
        "language": safe_text(metadata.get("language")),
        "topics": normalize_topics(metadata.get("topics")),
        "stakeholders": _normalize_stakeholders(curated.get("stakeholders", [])),
        "category": safe_text(curated.get("category"), ""),
        "reason": safe_text(curated.get("reason"), ""),
        "suggested_use": safe_text(curated.get("suggested_use"), ""),
        "tags": normalize_topics(curated.get("tags")),
        "stars": stars,
        "forks": forks,
        "license": license_value,
        "archived": archived,
        "pushed_at": pushed_at,
        "has_readme": has_readme,
        "recent_activity": recent_activity,
        "recommendation_level": level,
        "quality_gate_passed": quality_gate_passed,
        "evidence": [
            f"Stars: {stars}",
            f"Forks: {forks}",
            f"License: {license_value}",
            f"README: {'present' if has_readme else 'missing'}",
            f"Last push: {pushed_at}",
        ],
        "risk_note": risk_note,
        "excluded_reasons": list(dict.fromkeys(exclusion_reasons)),
    }


def _normalize_stakeholders(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = [value]
    elif isinstance(value, list):
        raw = value
    else:
        raw = []
    return [item for item in dict.fromkeys(str(item).strip() for item in raw) if item in VISIBLE_STAKEHOLDERS]


def _license_value(metadata: dict[str, Any]) -> str:
    raw = metadata.get("license")
    if isinstance(raw, dict):
        return safe_text(raw.get("spdx_id") or raw.get("name"))
    return safe_text(raw)


def _license_present(value: str) -> bool:
    return str(value).strip().lower() not in {"", "unavailable", "none", "noassertion"}


def _exclusion_reasons(stars: int, forks: int, license_value: str, has_readme: bool, archived: bool) -> list[str]:
    reasons = []
    if not _license_present(license_value):
        reasons.append("license missing")
    if not has_readme:
        reasons.append("README missing")
    if archived:
        reasons.append("repository archived")
    return reasons


def _has_recent_activity(pushed_at: str, days: int, now: datetime) -> bool:
    pushed = _parse_datetime(pushed_at)
    if pushed is None:
        return False
    return now - pushed <= timedelta(days=days)


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text or text == "unavailable":
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _level_rank(level: str) -> int:
    if level == COMMUNITY_STANDARD:
        return 2
    if level == MATURE_REFERENCE:
        return 1
    return 0

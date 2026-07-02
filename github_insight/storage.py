"""Persistence helpers for GitHub Insight."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from github_insight.models import InsightRecord, Repository, RepositoryEnriched, RunMetadata, utc_now_iso
from github_insight.utils import ensure_parent


CSV_FIELDS = [
    "date",
    "run_label",
    "full_name",
    "html_url",
    "description",
    "language",
    "topics",
    "stars",
    "forks",
    "open_issues",
    "pushed_at",
    "updated_at",
    "license",
    "source_status",
    "seen_before",
    "recommended_profile",
    "recommended_score",
    "recommended_decision",
    "general_score",
    "data_analyst_score",
    "data_scientist_score",
    "general_decision",
    "data_analyst_decision",
    "data_scientist_decision",
    "skill_tags",
    "recommended_action",
    "expected_output",
    "portfolio_idea",
    "evidence_limits",
]

INSIGHT_CSV_FIELDS = [
    "date",
    "rank_today",
    "full_name",
    "html_url",
    "primary_audience",
    "audience_tags",
    "overall_insight_score",
    "general_user_score",
    "data_analyst_score",
    "data_scientist_score",
    "usefulness_score",
    "momentum_score",
    "reproducibility_score",
    "data_asset_score",
    "dashboard_readiness_score",
    "maintenance_score",
    "risk_score",
    "difficulty_level",
    "recommended_action",
    "one_sentence_summary",
    "why_it_matters",
    "portfolio_project_idea",
    "evidence",
    "risk_flags",
    "confidence",
    "language",
    "topics",
    "stars",
    "forks",
    "open_issues",
    "license",
    "pushed_at",
    "first_seen_date",
    "last_seen_date",
    "days_seen",
    "rank_previous",
    "rank_change",
    "star_delta_since_previous_seen",
    "fork_delta_since_previous_seen",
    "source_status",
    "image_asset_path",
    "image_prompt_path",
]


def ensure_directories(output_root: Path, date: str) -> None:
    for relative in [
        "data/raw",
        "data/history",
        "data/processed/runs",
        "reports/daily",
        "reports/latest",
        "reports/weekly",
        "docs/reviews",
        "docs/data",
        "docs/assets",
        "dashboard",
        f"assets/daily/{date}",
        f"assets/images/{date}",
        "assets/cards",
    ]:
        (output_root / relative).mkdir(parents=True, exist_ok=True)


def load_seen_repos(output_root: Path) -> dict[str, Any]:
    path = output_root / "data" / "history" / "seen_repos.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("repositories", {})


def update_seen_repos(output_root: Path, cards: list[dict[str, Any]], date: str, run_label: str) -> Path:
    path = output_root / "data" / "history" / "seen_repos.json"
    history = load_seen_repos(output_root)
    for card in cards:
        key = card["full_name"].lower()
        score = card.get("recommended_score", card.get("overall_insight_score", 0))
        entry = history.setdefault(
            key,
            {
                "full_name": card["full_name"],
                "first_seen": date,
                "appearances": 0,
            },
        )
        entry["last_seen"] = date
        entry["last_run_label"] = run_label
        entry["last_score"] = score
        entry["appearances"] = int(entry.get("appearances", 0)) + 1
    payload = {"updated_at": utc_now_iso(), "repositories": history}
    ensure_parent(path).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_raw_repositories(
    output_root: Path, repositories: list[Repository], date: str, run_label: str, source_status: str
) -> Path:
    path = output_root / "data" / "raw" / f"{date}-{run_label}-repositories.json"
    payload = {
        "date": date,
        "run_label": run_label,
        "source_status": source_status,
        "repositories": [repo.to_dict() for repo in repositories],
    }
    ensure_parent(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def flatten_card(card: dict[str, Any], date: str, run_label: str) -> dict[str, Any]:
    row = {field: "" for field in CSV_FIELDS}
    row.update(
        {
            "date": date,
            "run_label": run_label,
            "full_name": card["full_name"],
            "html_url": card["html_url"],
            "description": card["description"],
            "language": card["language"],
            "topics": ", ".join(card["topics"]),
            "stars": card["stars"],
            "forks": card["forks"],
            "open_issues": card["open_issues"],
            "pushed_at": card["pushed_at"],
            "updated_at": card["updated_at"],
            "license": card["license"],
            "source_status": card["source_status"],
            "seen_before": card["seen_before"],
            "recommended_profile": card["recommended_profile"],
            "recommended_score": card["recommended_score"],
            "recommended_decision": card["recommended_decision"],
            "general_score": card["scores"]["general"]["score"],
            "data_analyst_score": card["scores"]["data_analyst"]["score"],
            "data_scientist_score": card["scores"]["data_scientist"]["score"],
            "general_decision": card["scores"]["general"]["decision"],
            "data_analyst_decision": card["scores"]["data_analyst"]["decision"],
            "data_scientist_decision": card["scores"]["data_scientist"]["decision"],
            "skill_tags": ", ".join(card["skill_tags"]),
            "recommended_action": card["recommended_action"],
            "expected_output": card["expected_output"],
            "portfolio_idea": card["portfolio_idea"],
            "evidence_limits": card["evidence_limits"],
        }
    )
    return row


def write_run_csv(output_root: Path, cards: list[dict[str, Any]], date: str, run_label: str) -> Path:
    path = output_root / "data" / "processed" / "runs" / f"{date}-{run_label}-github_repos.csv"
    with ensure_parent(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for card in cards:
            writer.writerow(flatten_card(card, date, run_label))
    return path


def write_cards_json(output_root: Path, cards: list[dict[str, Any]], date: str, run_label: str) -> Path:
    path = output_root / "data" / "processed" / "github_insight_cards.json"
    payload = {"date": date, "run_label": run_label, "cards": cards}
    ensure_parent(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_master_csv(output_root: Path, cards: list[dict[str, Any]], date: str, run_label: str) -> Path:
    path = output_root / "data" / "processed" / "github_repos_master.csv"
    rows_by_repo: dict[str, dict[str, Any]] = {}
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("full_name"):
                    rows_by_repo[row["full_name"].lower()] = row
    for card in cards:
        rows_by_repo[card["full_name"].lower()] = flatten_card(card, date, run_label)
    with ensure_parent(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in sorted(
            rows_by_repo.values(),
            key=lambda item: (float(item.get("recommended_score") or 0), item.get("full_name", "")),
            reverse=True,
        ):
            writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    return path


def _jsonish(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def insight_row(record: InsightRecord) -> dict[str, Any]:
    data = record.to_dict()
    return {field: _jsonish(data.get(field, "")) for field in INSIGHT_CSV_FIELDS}


def write_raw_api_payload(output_root: Path, date: str, payload: dict[str, Any]) -> Path:
    path = output_root / "data" / "raw" / f"{date}-github-api-raw.json"
    ensure_parent(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_insight_json(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "data" / "processed" / f"{run.date}-github-insight-projects.json"
    payload = {"run": run.to_dict(), "projects": [record.to_dict() for record in records]}
    ensure_parent(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_insight_csv(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "data" / "processed" / f"{run.date}-github-insight-projects.csv"
    with ensure_parent(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INSIGHT_CSV_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(insight_row(record))
    return path


def write_latest_projects(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "reports" / "latest" / "latest-projects.json"
    payload = {"run": run.to_dict(), "projects": [record.to_dict() for record in records]}
    ensure_parent(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_docs_latest(output_root: Path, run: RunMetadata, records: list[InsightRecord], paths: dict[str, str]) -> Path:
    path = output_root / "docs" / "data" / "latest.json"
    payload = {"run": run.to_dict(), "paths": paths, "projects": [record.to_dict() for record in records]}
    ensure_parent(path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _archive_mode(item: dict[str, Any]) -> str:
    mode = str(item.get("mode") or "").strip().lower()
    if mode in {"live", "mock"}:
        return mode
    run_id = str(item.get("run_id") or "").strip().lower()
    if run_id.startswith("mock"):
        return "mock"
    return "live"


def update_archive_index(
    output_root: Path,
    run: RunMetadata,
    daily_brief_path: Path,
    json_path: Path,
    csv_path: Path,
    records: list[InsightRecord],
) -> Path:
    path = output_root / "docs" / "data" / "archive_index.json"
    archive: list[dict[str, Any]] = []
    if path.exists():
        archive = json.loads(path.read_text(encoding="utf-8"))
    for item in archive:
        item.setdefault("mode", _archive_mode(item))
    entry = {
        "date": run.date,
        "generated_at": run.generated_at,
        "mode": run.mode,
        "run_id": run.run_id,
        "daily_brief_path": daily_brief_path.relative_to(output_root).as_posix(),
        "json_path": json_path.relative_to(output_root).as_posix(),
        "csv_path": csv_path.relative_to(output_root).as_posix(),
        "selected_count": len(records),
        "top_project": records[0].full_name if records else "unavailable",
    }
    archive = [item for item in archive if not (item.get("date") == run.date and item.get("generated_at") == run.generated_at)]
    archive.append(entry)
    archive.sort(key=lambda item: item.get("generated_at", ""), reverse=True)
    ensure_parent(path).write_text(json.dumps(archive, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_spec_master_csv(output_root: Path, records: list[InsightRecord]) -> Path:
    path = output_root / "data" / "processed" / "github_repos_master.csv"
    rows_by_key: dict[str, dict[str, Any]] = {}
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                key = f"{row.get('date', '')}|{row.get('full_name', '')}".lower()
                if row.get("date") and row.get("full_name"):
                    rows_by_key[key] = row
    for record in records:
        row = insight_row(record)
        rows_by_key[f"{record.date}|{record.full_name}".lower()] = row
    with ensure_parent(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INSIGHT_CSV_FIELDS)
        writer.writeheader()
        for row in sorted(rows_by_key.values(), key=lambda item: (item.get("date", ""), float(item.get("overall_insight_score") or 0)), reverse=True):
            writer.writerow({field: row.get(field, "") for field in INSIGHT_CSV_FIELDS})
    return path


def init_sqlite(output_root: Path) -> Path:
    path = output_root / "data" / "github_insight.sqlite"
    ensure_parent(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_runs (
                run_id TEXT PRIMARY KEY,
                date TEXT,
                scheduled_for TEXT,
                started_at TEXT,
                generated_at TEXT,
                completed_at TEXT,
                timezone TEXT,
                mode TEXT,
                status TEXT,
                repos_discovered INTEGER,
                repos_selected INTEGER,
                notes TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repo_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                date TEXT,
                full_name TEXT,
                html_url TEXT,
                description TEXT,
                language TEXT,
                topics_json TEXT,
                stars INTEGER,
                forks INTEGER,
                watchers INTEGER,
                open_issues INTEGER,
                created_at TEXT,
                pushed_at TEXT,
                updated_at TEXT,
                license_spdx_id TEXT,
                archived INTEGER,
                source_audiences_json TEXT,
                source_queries_json TEXT,
                raw_json_path TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS repo_enriched (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                date TEXT,
                full_name TEXT,
                readme_length INTEGER,
                readme_quality_score REAL,
                has_installation_instructions INTEGER,
                has_usage_examples INTEGER,
                has_demo_link INTEGER,
                has_docs_link INTEGER,
                has_notebook INTEGER,
                has_dataset INTEGER,
                has_csv_or_sql INTEGER,
                reproducibility_signals_json TEXT,
                risk_flags_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS insight_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                date TEXT,
                full_name TEXT,
                primary_audience TEXT,
                audience_tags_json TEXT,
                overall_insight_score REAL,
                general_user_score REAL,
                data_analyst_score REAL,
                data_scientist_score REAL,
                momentum_score REAL,
                usefulness_score REAL,
                reproducibility_score REAL,
                risk_score REAL,
                difficulty_level TEXT,
                recommended_action TEXT,
                one_sentence_summary TEXT,
                why_it_matters TEXT,
                practical_use_cases_json TEXT,
                evidence_json TEXT,
                risk_flags_json TEXT,
                image_asset_path TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS visual_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                date TEXT,
                full_name TEXT,
                asset_path TEXT,
                prompt_path TEXT,
                status TEXT,
                model TEXT,
                alt_text TEXT
            )
            """
        )
    return path


def save_sqlite(
    output_root: Path,
    run: RunMetadata,
    enriched: list[RepositoryEnriched],
    records: list[InsightRecord],
    raw_json_path: Path,
) -> Path:
    path = init_sqlite(output_root)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_runs
            (run_id, date, scheduled_for, started_at, generated_at, completed_at, timezone, mode, status, repos_discovered, repos_selected, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run.run_id,
                run.date,
                run.scheduled_for,
                run.started_at,
                run.generated_at,
                run.completed_at,
                run.timezone,
                run.mode,
                run.status,
                run.repos_discovered,
                run.repos_selected,
                run.notes,
            ),
        )
        for item in enriched:
            raw = item.raw
            conn.execute(
                """
                INSERT INTO repo_snapshots
                (run_id, date, full_name, html_url, description, language, topics_json, stars, forks, watchers, open_issues,
                 created_at, pushed_at, updated_at, license_spdx_id, archived, source_audiences_json, source_queries_json, raw_json_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.date,
                    raw.full_name,
                    raw.html_url,
                    raw.description,
                    raw.language,
                    json.dumps(raw.topics),
                    raw.stargazers_count,
                    raw.forks_count,
                    raw.watchers_count,
                    raw.open_issues_count,
                    raw.created_at,
                    raw.pushed_at,
                    raw.updated_at,
                    raw.license_spdx_id,
                    int(raw.archived),
                    json.dumps(raw.source_audiences),
                    json.dumps(raw.source_queries),
                    raw_json_path.relative_to(output_root).as_posix(),
                ),
            )
            conn.execute(
                """
                INSERT INTO repo_enriched
                (run_id, date, full_name, readme_length, readme_quality_score, has_installation_instructions, has_usage_examples,
                 has_demo_link, has_docs_link, has_notebook, has_dataset, has_csv_or_sql, reproducibility_signals_json, risk_flags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.date,
                    raw.full_name,
                    item.readme_length,
                    item.readme_quality_score,
                    int(item.has_installation_instructions),
                    int(item.has_usage_examples),
                    int(item.has_demo_link),
                    int(item.has_docs_link),
                    int(item.has_notebook),
                    int(item.has_dataset),
                    int(item.has_csv_or_sql),
                    json.dumps(item.reproducibility_signals),
                    json.dumps(item.risk_flags),
                ),
            )
        for record in records:
            conn.execute(
                """
                INSERT INTO insight_records
                (run_id, date, full_name, primary_audience, audience_tags_json, overall_insight_score, general_user_score,
                 data_analyst_score, data_scientist_score, momentum_score, usefulness_score, reproducibility_score, risk_score,
                 difficulty_level, recommended_action, one_sentence_summary, why_it_matters, practical_use_cases_json,
                 evidence_json, risk_flags_json, image_asset_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.date,
                    record.full_name,
                    record.primary_audience,
                    json.dumps(record.audience_tags),
                    record.overall_insight_score,
                    record.general_user_score,
                    record.data_analyst_score,
                    record.data_scientist_score,
                    record.momentum_score,
                    record.usefulness_score,
                    record.reproducibility_score,
                    record.risk_score,
                    record.difficulty_level,
                    record.recommended_action,
                    record.one_sentence_summary,
                    record.why_it_matters,
                    json.dumps(record.practical_use_cases),
                    json.dumps(record.evidence),
                    json.dumps(record.risk_flags),
                    record.image_asset_path,
                ),
            )
    return path

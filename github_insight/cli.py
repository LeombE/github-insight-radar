"""Canonical package CLI for GitHub Insight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from github_insight.classifier import build_insights
from github_insight.collectors import collect_live_repositories, collect_mock_repositories, enrich_repositories
from github_insight.config import load_app_config
from github_insight.dashboard_builder import build_static_dashboard
from github_insight.github_client import GitHubApiError
from github_insight.image_generator import apply_optional_images
from github_insight.logging_utils import redact_secrets
from github_insight.models import InsightRecord, RunMetadata
from github_insight.report_writer import write_daily_reports, write_weekly_synthesis
from github_insight.storage import (
    ensure_directories,
    init_sqlite,
    load_seen_repos,
    save_sqlite,
    update_archive_index,
    update_seen_repos,
    write_docs_latest,
    write_insight_csv,
    write_insight_json,
    write_latest_projects,
    write_raw_api_payload,
    write_spec_master_csv,
)
from github_insight.utils import resolve_report_date, resolve_week, utc_now_iso
from github_insight.validation import validate_outputs


def _mock_time(date: str) -> str:
    return f"{date}T00:00:00+08:00"


def _run_metadata(
    *,
    date: str,
    mode: str,
    query_count: int,
    repos_discovered: int,
    repos_selected: int,
    rate_remaining: int | None,
    image_enabled: bool,
    llm_enabled: bool,
    status: str = "success",
    notes: str = "",
) -> RunMetadata:
    timestamp = _mock_time(date) if mode == "mock" else utc_now_iso()
    run_id = f"{mode}-{date}" if mode == "mock" else f"{mode}-{date}-{timestamp.replace(':', '').replace('+', '-') }"
    return RunMetadata(
        run_id=run_id,
        date=date,
        scheduled_for=date,
        started_at=timestamp,
        generated_at=timestamp,
        completed_at=timestamp,
        timezone="Asia/Kuala_Lumpur",
        mode=mode,
        status=status,
        github_rate_limit_remaining=rate_remaining,
        query_count=query_count,
        repos_discovered=repos_discovered,
        repos_selected=repos_selected,
        image_generation_enabled=image_enabled,
        llm_summary_enabled=llm_enabled,
        notes=notes,
    )


def run_daily(args: argparse.Namespace) -> list[Path]:
    root = Path(args.output_root).resolve()
    date = resolve_report_date(args.date)
    config = load_app_config(root)
    ensure_directories(root, date)
    mode = "mock" if args.mock else "live"

    if mode == "mock":
        raw_repos, raw_payload, rate_remaining, query_count = collect_mock_repositories()
        source_status = "mock_fixture"
    else:
        raw_repos, raw_payload, rate_remaining, query_count = collect_live_repositories(config)
        source_status = "live_github_api"

    raw_path = write_raw_api_payload(root, date, raw_payload)
    enriched = enrich_repositories(raw_repos, config, mode=mode)
    history = load_seen_repos(root)
    records = build_insights(enriched, date, history, source_status)
    if args.limit:
        records = records[: args.limit]
        for index, record in enumerate(records, start=1):
            record.rank_today = index

    run = _run_metadata(
        date=date,
        mode=mode,
        query_count=query_count,
        repos_discovered=len(raw_repos),
        repos_selected=len(records),
        rate_remaining=rate_remaining,
        image_enabled=config.enable_image_generation,
        llm_enabled=config.enable_llm_summary,
    )

    generated: list[Path] = [raw_path]
    generated.extend(apply_optional_images(root, run, records, config))
    json_path = write_insight_json(root, run, records)
    csv_path = write_insight_csv(root, run, records)
    master_path = write_spec_master_csv(root, records)
    latest_projects = write_latest_projects(root, run, records)
    compatibility_cards = root / "data" / "processed" / "github_insight_cards.json"
    compatibility_cards.write_text(
        json.dumps({"run": run.to_dict(), "cards": [record.to_dict() for record in records]}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    generated.extend([json_path, csv_path, master_path, latest_projects, compatibility_cards])

    data_paths = {
        "Raw API JSON": raw_path.relative_to(root).as_posix(),
        "Daily projects JSON": json_path.relative_to(root).as_posix(),
        "Daily projects CSV": csv_path.relative_to(root).as_posix(),
        "Master CSV": master_path.relative_to(root).as_posix(),
        "Dashboard JSON": "docs/data/latest.json",
    }
    reports = write_daily_reports(root, run, records, data_paths)
    generated.extend(reports.values())
    docs_latest = write_docs_latest(
        root,
        run,
        records,
        {
            "daily_brief": reports["daily_brief"].relative_to(root).as_posix(),
            "json": json_path.relative_to(root).as_posix(),
            "csv": csv_path.relative_to(root).as_posix(),
        },
    )
    archive = update_archive_index(root, run, reports["daily_brief"], json_path, csv_path, records)
    dashboard = build_static_dashboard(root, run, records)
    sqlite_path = save_sqlite(root, run, enriched, records, raw_path)
    seen_path = update_seen_repos(root, [record.to_dict() for record in records], date, mode)
    quality_path = _write_quality_gate(root, run, records)
    generated.extend([docs_latest, archive, dashboard, sqlite_path, seen_path, quality_path])

    if not args.no_validate:
        ok, errors = validate_outputs(root, date)
        if not ok:
            raise SystemExit("Validation failed after run:\n" + "\n".join(errors))
    return generated


def _write_quality_gate(root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = root / "docs" / "reviews" / f"{run.date}-quality-gate-result.md"
    checks = [
        ("Factuality", all(record.full_name and record.evidence for record in records), "Records include names and evidence bullets."),
        ("Career Value", any(record.data_analyst_score >= 45 for record in records) and any(record.data_scientist_score >= 45 for record in records), "Analyst and scientist opportunities are represented."),
        ("Actionability", all(record.recommended_action for record in records), "Every record has a recommended action."),
        ("Skill Mapping", all(record.audience_tags for record in records), "Every record has audience tags."),
        ("Readability", True, "Reports are concise Markdown files generated from structured data."),
        ("Portfolio", any(record.portfolio_project_idea for record in records), "Portfolio ideas are present."),
    ]
    overall = "PASS" if all(item[1] for item in checks) else "FAIL"
    lines = [
        f"# GitHub Insight Quality Gate - {run.date}",
        "",
        f"- Run ID: `{run.run_id}`",
        f"- Mode: `{run.mode}`",
        f"- Overall status: {overall}",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for name, passed, detail in checks:
        lines.append(f"| {name} | {'PASS' if passed else 'FAIL'} | {detail} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if overall != "PASS":
        raise SystemExit(f"Quality gate failed for {run.date}")
    return path


def rebuild_dashboard(args: argparse.Namespace) -> list[Path]:
    root = Path(args.output_root).resolve()
    latest_path = root / "docs" / "data" / "latest.json"
    if not latest_path.exists():
        raise SystemExit("docs/data/latest.json is missing. Run `python -m github_insight.cli run --mock` first.")
    payload = json.loads(latest_path.read_text(encoding="utf-8"))
    run = RunMetadata(**payload["run"])
    records = [InsightRecord(**item) for item in payload.get("projects", [])]
    dashboard = build_static_dashboard(root, run, records)
    return [dashboard]


def init_db(args: argparse.Namespace) -> list[Path]:
    root = Path(args.output_root).resolve()
    return [init_sqlite(root)]


def validate_command(args: argparse.Namespace) -> list[Path]:
    root = Path(args.output_root).resolve()
    date = resolve_report_date(args.date)
    if args.date is None:
        latest_path = root / "docs" / "data" / "latest.json"
        if latest_path.exists():
            payload = json.loads(latest_path.read_text(encoding="utf-8"))
            date = payload.get("run", {}).get("date", date)
    ok, errors = validate_outputs(root, date)
    if not ok:
        raise SystemExit("Validation failed:\n" + "\n".join(errors))
    print(f"Validation PASS for {date}")
    return []


def weekly_command(args: argparse.Namespace) -> list[Path]:
    root = Path(args.output_root).resolve()
    week = resolve_week(args.week)
    return [write_weekly_synthesis(root, week)]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitHub Insight - Daily Open-Source Intelligence Radar")
    parser.add_argument("--output-root", default=".", help="Project output root.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run the daily pipeline.")
    run.add_argument("--date", default="today", help="YYYY-MM-DD or today.")
    run.add_argument("--mock", action="store_true", help="Run fully offline with deterministic fixtures.")
    run.add_argument("--limit", type=int, default=0, help="Optional selected-record limit.")
    run.add_argument("--no-validate", action="store_true", help="Skip post-run output validation.")
    run.set_defaults(func=run_daily)

    dashboard = subparsers.add_parser("dashboard", help="Rebuild docs/index.html from docs/data/latest.json.")
    dashboard.set_defaults(func=rebuild_dashboard)

    weekly = subparsers.add_parser("weekly", help="Generate weekly synthesis from latest project data.")
    weekly.add_argument("--week", default=None, help="ISO week such as 2026-W27. Defaults to current Malaysia week.")
    weekly.set_defaults(func=weekly_command)

    init = subparsers.add_parser("init-db", help="Create or migrate the local SQLite database.")
    init.set_defaults(func=init_db)

    validate = subparsers.add_parser("validate", help="Validate required generated outputs and secret patterns.")
    validate.add_argument("--date", default=None, help="YYYY-MM-DD. Defaults to latest generated date when available.")
    validate.set_defaults(func=validate_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        generated = args.func(args)
    except GitHubApiError as exc:
        print("Live GitHub API run failed. No mock data was substituted.", file=sys.stderr)
        print(redact_secrets(exc), file=sys.stderr)
        return 2
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - final CLI safety net.
        print(redact_secrets(f"GitHub Insight command failed: {exc}"), file=sys.stderr)
        return 1
    if generated:
        print("Generated files:")
        for path in generated:
            print(f"- {Path(path).resolve()}")
    else:
        print("Command completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



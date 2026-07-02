"""Markdown report writers for canonical GitHub Insight outputs."""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

from github_insight.classifier import AUDIENCE_LABELS
from github_insight.models import InsightRecord, RunMetadata
from github_insight.utils import ensure_parent


def _link(record: InsightRecord) -> str:
    return f"[{record.full_name}]({record.html_url})" if record.html_url != "unavailable" else record.full_name


def _escape_table(value: object) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def _top(records: list[InsightRecord], limit: int = 10) -> list[InsightRecord]:
    return sorted(records, key=lambda item: item.overall_insight_score, reverse=True)[:limit]


def _audience_records(records: list[InsightRecord], audience: str, limit: int = 10) -> list[InsightRecord]:
    score_field = {
        "general_user": "general_user_score",
        "data_analyst": "data_analyst_score",
        "data_scientist": "data_scientist_score",
    }[audience]
    filtered = [item for item in records if audience in item.audience_tags or item.primary_audience == audience]
    return sorted(filtered, key=lambda item: getattr(item, score_field), reverse=True)[:limit]


def _methodology() -> str:
    return (
        "Scores are deterministic heuristics based on GitHub metadata, README signals, audience fit, "
        "momentum, maintenance, reproducibility, data/demo signals, and risk flags. The system does not "
        "claim production readiness, security, or best-in-class status unless the collected evidence directly supports it."
    )


def write_daily_brief(output_root: Path, run: RunMetadata, records: list[InsightRecord], data_paths: dict[str, str]) -> Path:
    path = output_root / "reports" / "daily" / f"{run.date}-daily-brief.md"
    top = _top(records, 10)
    risk_counter = Counter(flag for record in records for flag in record.risk_flags)
    lines = [
        f"# GitHub Insight Daily Brief - {run.date}",
        "",
        f"Generated at: `{run.generated_at}`",
        f"Mode: `{run.mode}`",
        f"Repositories scanned: `{run.repos_discovered}`",
        f"Repositories selected: `{run.repos_selected}`",
        f"Image generation: `{'enabled' if run.image_generation_enabled else 'disabled'}`",
        f"LLM summary: `{'enabled' if run.llm_summary_enabled else 'disabled'}`",
        "",
        "## Executive Summary",
    ]
    if records:
        general = _audience_records(records, "general_user", 1)
        analyst = _audience_records(records, "data_analyst", 1)
        scientist = _audience_records(records, "data_scientist", 1)
        lines.extend(
            [
                f"- Top overall opportunity: {_link(top[0])} with score {top[0].overall_insight_score:.2f}.",
                f"- General user opportunity: {_link(general[0]) if general else 'No strong general-user candidate selected today.'}",
                f"- Data analyst opportunity: {_link(analyst[0]) if analyst else 'No strong data analyst candidate selected today.'}",
                f"- Data scientist opportunity: {_link(scientist[0]) if scientist else 'No strong data scientist candidate selected today.'}",
                f"- Most common risk pattern: {risk_counter.most_common(1)[0][0] if risk_counter else 'No major risk pattern from selected records.'}",
            ]
        )
    else:
        lines.append("- No repositories were selected for this run.")

    lines.extend(
        [
            "",
            "## Top Overall Projects",
            "| Rank | Repo | Audience | Score | Why it matters | Recommended action |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for record in top:
        lines.append(
            f"| {record.rank_today} | {_link(record)} | {AUDIENCE_LABELS.get(record.primary_audience, record.primary_audience)} | "
            f"{record.overall_insight_score:.2f} | {_escape_table(record.why_it_matters)} | {_escape_table(record.recommended_action)} |"
        )

    sections = [
        ("General User Finds", "general_user", "general_user_angle"),
        ("Data Analyst Opportunities", "data_analyst", "data_analyst_angle"),
        ("Data Scientist Research Radar", "data_scientist", "data_scientist_angle"),
    ]
    for heading, audience, angle_attr in sections:
        lines.extend(["", f"## {heading}"])
        for record in _audience_records(records, audience, 5):
            lines.extend(
                [
                    f"### {record.full_name}",
                    f"- What it is: {record.one_sentence_summary}",
                    f"- Angle: {getattr(record, angle_attr)}",
                    f"- Score: {record.overall_insight_score:.2f}",
                    f"- Difficulty: {record.difficulty_level}",
                    f"- Recommended action: {record.recommended_action}",
                    f"- Risk: {', '.join(record.risk_flags) if record.risk_flags else 'No major risk flag from collected evidence.'}",
                ]
            )

    lines.extend(["", "## Action List"])
    action_groups = {
        "Try today": [record for record in records if record.recommended_action == "Try today"],
        "Watch this week": [record for record in records if record.recommended_action == "Watch this week"],
        "Use as portfolio reference": [record for record in records if record.recommended_action == "Use as portfolio reference"],
        "Skip for now": [record for record in records if record.recommended_action == "Skip for now"],
    }
    for action, grouped in action_groups.items():
        lines.append(f"- {action}: {', '.join(item.full_name for item in grouped[:3]) if grouped else 'None selected.'}")

    lines.extend(
        [
            "",
            "## Methodology",
            _methodology(),
            "",
            "## Data Files",
        ]
    )
    for label, rel_path in data_paths.items():
        lines.append(f"- {label}: `{rel_path}`")
    ensure_parent(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    latest = output_root / "reports" / "latest" / "latest-daily-brief.md"
    ensure_parent(latest)
    shutil.copyfile(path, latest)
    return path


def write_audience_report(output_root: Path, run: RunMetadata, records: list[InsightRecord], audience: str, suffix: str) -> Path:
    path = output_root / "reports" / "daily" / f"{run.date}-{suffix}.md"
    selected = _audience_records(records, audience, 15)
    lines = [
        f"# {AUDIENCE_LABELS[audience]} GitHub Insight - {run.date}",
        "",
        f"Generated at: `{run.generated_at}`",
        f"Mode: `{run.mode}`",
        "",
        "| Rank | Repo | Score | Action | Difficulty | Risk flags |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for index, record in enumerate(selected, start=1):
        score = getattr(record, f"{audience}_score")
        lines.append(
            f"| {index} | {_link(record)} | {score:.2f} | {_escape_table(record.recommended_action)} | "
            f"{record.difficulty_level} | {_escape_table(', '.join(record.risk_flags) if record.risk_flags else 'None')} |"
        )
    lines.extend(["", "## Project Notes"])
    for record in selected:
        lines.extend(
            [
                f"### {record.full_name}",
                f"- Summary: {record.one_sentence_summary}",
                f"- Why it matters: {record.why_it_matters}",
                f"- Practical use cases: {', '.join(record.practical_use_cases)}",
                f"- Portfolio idea: {record.portfolio_project_idea}",
                f"- Evidence: {'; '.join(record.evidence)}",
                f"- Confidence: {record.confidence}",
                "",
            ]
        )
    ensure_parent(path).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_action_list(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "reports" / "daily" / f"{run.date}-action-list.md"
    lines = [f"# GitHub Insight Action List - {run.date}", ""]
    for index, record in enumerate(_top(records, 20), start=1):
        lines.extend(
            [
                f"{index}. `{record.recommended_action}` {_link(record)}",
                f"   - Audience: {AUDIENCE_LABELS.get(record.primary_audience, record.primary_audience)}",
                f"   - Score: {record.overall_insight_score:.2f}",
                f"   - Output: {record.portfolio_project_idea}",
                f"   - Risk: {', '.join(record.risk_flags) if record.risk_flags else 'No major risk flag.'}",
            ]
        )
    ensure_parent(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_daily_reports(output_root: Path, run: RunMetadata, records: list[InsightRecord], data_paths: dict[str, str]) -> dict[str, Path]:
    outputs = {
        "daily_brief": write_daily_brief(output_root, run, records, data_paths),
        "general_user": write_audience_report(output_root, run, records, "general_user", "general-user"),
        "data_analyst": write_audience_report(output_root, run, records, "data_analyst", "data-analyst"),
        "data_scientist": write_audience_report(output_root, run, records, "data_scientist", "data-scientist"),
        "action_list": write_action_list(output_root, run, records),
    }
    return outputs


def write_weekly_synthesis(output_root: Path, week: str) -> Path:
    latest_path = output_root / "reports" / "latest" / "latest-projects.json"
    records: list[dict] = []
    if latest_path.exists():
        import json

        payload = json.loads(latest_path.read_text(encoding="utf-8"))
        records = payload.get("projects", [])
    path = output_root / "reports" / "weekly" / f"{week}-weekly-synthesis.md"
    top = records[:10]
    lines = [
        f"# GitHub Insight Weekly Synthesis - {week}",
        "",
        "## Most Consistently Useful Repositories",
    ]
    if top:
        for item in top[:5]:
            lines.append(f"- {item['full_name']} - score {item['overall_insight_score']:.2f}; action: {item['recommended_action']}.")
    else:
        lines.append("- No project data is available yet. Run the daily pipeline first.")
    lines.extend(
        [
            "",
            "## Biggest Momentum Changes",
            "- Momentum deltas require multiple daily snapshots. New runs keep delta fields null until history exists.",
            "",
            "## Best Projects for Data Analyst Portfolio",
            *[f"- {item['full_name']}" for item in records if item.get("primary_audience") == "data_analyst"][:5],
            "",
            "## Best Projects for Data Scientist Learning or Research",
            *[f"- {item['full_name']}" for item in records if item.get("primary_audience") == "data_scientist"][:5],
            "",
            "## Tools General Users Can Try",
            *[f"- {item['full_name']}" for item in records if item.get("primary_audience") == "general_user"][:5],
            "",
            "## Repositories to Watch Next Week",
            *[f"- {item['full_name']}" for item in records if item.get("recommended_action") == "Watch this week"][:5],
            "",
            "## Overhyped or Risky Repositories",
            *[f"- {item['full_name']}: {', '.join(item.get('risk_flags', []))}" for item in records if item.get("risk_flags")][:5],
        ]
    )
    ensure_parent(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

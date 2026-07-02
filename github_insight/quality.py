"""Quality gate checks for generated GitHub Insight reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class QualityCheck:
    name: str
    passed: bool
    detail: str


def run_quality_checks(
    cards: list[dict[str, Any]], report_paths: list[Path], context: dict[str, Any]
) -> list[QualityCheck]:
    checks = [
        QualityCheck(
            "Factuality",
            all(card.get("full_name") and card.get("source_status") for card in cards),
            "Repository names, source status, and metadata fields are present.",
        ),
        QualityCheck(
            "Career Value",
            any(card["scores"]["data_analyst"]["score"] >= 5 for card in cards)
            and any(card["scores"]["data_scientist"]["score"] >= 5 for card in cards),
            "At least one analyst and one scientist recommendation crossed the review threshold.",
        ),
        QualityCheck(
            "Actionability",
            all(card.get("recommended_action") and card.get("expected_output") for card in cards),
            "Every card includes a 30-60 minute action and expected output.",
        ),
        QualityCheck(
            "Skill Mapping",
            all(card.get("skill_tags") for card in cards),
            "Every card has at least one skill tag.",
        ),
        QualityCheck(
            "Readability",
            all(path.exists() and len(path.read_text(encoding="utf-8").splitlines()) <= 220 for path in report_paths),
            "Markdown reports exist and stay within the intended skim length.",
        ),
        QualityCheck(
            "Portfolio",
            any(card["recommended_decision"] in {"Build", "Study"} for card in cards),
            "At least one repository can become a build/study portfolio action.",
        ),
    ]
    if context["source_status"].startswith("fallback"):
        checks.append(
            QualityCheck(
                "Fallback Labeling",
                bool(context.get("fetch_error")),
                "Fallback reports include the live fetch error note.",
            )
        )
    return checks


def write_quality_report(output_root: Path, checks: list[QualityCheck], context: dict[str, Any]) -> Path:
    path = output_root / "docs" / "reviews" / f"{context['date']}-quality-gate-result.md"
    overall = "PASS" if all(check.passed for check in checks) else "FAIL"
    lines = [
        f"# GitHub Insight Quality Gate - {context['date']}",
        "",
        f"- Run label: `{context['run_label']}`",
        f"- Source status: `{context['source_status']}`",
        f"- Overall status: {overall}",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        lines.append(f"| {check.name} | {status} | {check.detail} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


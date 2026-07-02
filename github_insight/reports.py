"""Markdown report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from github_insight.scoring import PROFILE_LABELS, PROFILES


def _escape(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return text.replace("|", "\\|")


def _repo_link(card: dict[str, Any]) -> str:
    if card["html_url"] == "unavailable":
        return card["full_name"]
    return f"[{card['full_name']}]({card['html_url']})"


def _top_for_profile(cards: list[dict[str, Any]], profile: str, limit: int = 8) -> list[dict[str, Any]]:
    return sorted(cards, key=lambda card: card["scores"][profile]["score"], reverse=True)[:limit]


def _profile_table(cards: list[dict[str, Any]], profile: str) -> str:
    lines = [
        "| Rank | Repository | Decision | Score | Skills | 30-60 minute action |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for index, card in enumerate(_top_for_profile(cards, profile), start=1):
        profile_score = card["scores"][profile]
        lines.append(
            "| {rank} | {repo} | {decision} | {score:.2f} | {skills} | {action} |".format(
                rank=index,
                repo=_repo_link(card),
                decision=_escape(profile_score["decision"]),
                score=profile_score["score"],
                skills=_escape(", ".join(card["skill_tags"])),
                action=_escape(profile_score["action"]),
            )
        )
    return "\n".join(lines)


def _evidence_block(context: dict[str, Any]) -> str:
    error_note = context.get("fetch_error")
    lines = [
        f"- Date: `{context['date']}`",
        f"- Run label: `{context['run_label']}`",
        f"- Source status: `{context['source_status']}`",
        f"- Repository count: `{context['repo_count']}`",
        "- Evidence limit: README quality, install steps, and full feature claims are unverified unless present in collected metadata.",
    ]
    if error_note:
        lines.append(f"- Fetch error: `{_escape(error_note)}`")
    return "\n".join(lines)


def write_daily_brief(output_root: Path, cards: list[dict[str, Any]], context: dict[str, Any]) -> Path:
    path = output_root / "reports" / "daily" / f"{context['date']}-daily-brief.md"
    best = cards[0] if cards else None
    top_portfolio = max(cards, key=lambda card: card["recommended_score"]) if cards else None
    skip_candidates = [
        card for card in cards if card["recommended_decision"] == "Skip" or card.get("archived")
    ][:3]

    lines = [
        f"# GitHub Insight Daily Brief - {context['date']}",
        "",
        "## Evidence Status",
        _evidence_block(context),
        "",
        "## Daily Answers",
    ]
    if best:
        lines.extend(
            [
                f"- What to read today: {_repo_link(best)} for {', '.join(best['skill_tags'][:3])}.",
                f"- What to skip: {', '.join(card['full_name'] for card in skip_candidates) if skip_candidates else 'No clear skip from this run; review lower-scoring repos later.'}",
                f"- Skill to learn: {best['skill_tags'][0]}.",
                f"- Portfolio candidate: {top_portfolio['portfolio_idea'] if top_portfolio else 'unavailable'}",
                f"- 30-60 minute action: {best['recommended_action']}",
                "- Career value: Convert the action into a short GitHub note, dashboard sketch, notebook, or interview story.",
            ]
        )
    else:
        lines.append("- No repositories were available for scoring.")

    lines.extend(
        [
            "",
            "## Top Decisions",
            "| Rank | Repository | Best profile | Decision | Score | Why it matters |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for index, card in enumerate(cards[:10], start=1):
        lines.append(
            "| {rank} | {repo} | {profile} | {decision} | {score:.2f} | {why} |".format(
                rank=index,
                repo=_repo_link(card),
                profile=_escape(card["recommended_profile_label"]),
                decision=_escape(card["recommended_decision"]),
                score=card["recommended_score"],
                why=_escape(card["why_it_matters"]),
            )
        )

    lines.extend(
        [
            "",
            "## Profile Snapshot",
        ]
    )
    for profile in PROFILES:
        top = _top_for_profile(cards, profile, limit=1)
        if top:
            card = top[0]
            lines.append(
                f"- {PROFILE_LABELS[profile]}: {_repo_link(card)} "
                f"({card['scores'][profile]['score']:.2f}, {card['scores'][profile]['decision']})."
            )

    lines.extend(
        [
            "",
            "## Limits",
            "- Scores are a prioritization aid, not an absolute quality judgment.",
            "- Live metadata can change after report generation.",
            "- Sample fixture runs are for demo and testing, not current GitHub intelligence.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_profile_report(
    output_root: Path, cards: list[dict[str, Any]], context: dict[str, Any], profile: str, filename_suffix: str
) -> Path:
    path = output_root / "reports" / "daily" / f"{context['date']}-{filename_suffix}.md"
    lines = [
        f"# {PROFILE_LABELS[profile]} GitHub Insight - {context['date']}",
        "",
        "## Evidence Status",
        _evidence_block(context),
        "",
        "## Ranked Repositories",
        _profile_table(cards, profile),
        "",
        "## Recommended Workflow",
    ]
    for card in _top_for_profile(cards, profile, limit=5):
        score = card["scores"][profile]
        lines.extend(
            [
                f"### {card['full_name']}",
                f"- Decision: `{score['decision']}`",
                f"- Score: `{score['score']:.2f}`",
                f"- Skill tags: {', '.join(card['skill_tags'])}",
                f"- Action: {score['action']}",
                f"- Expected output: {score['expected_output']}",
                f"- Portfolio angle: {card['portfolio_idea']}",
                f"- Evidence limits: {card['evidence_limits']}",
                "",
            ]
        )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_action_list(output_root: Path, cards: list[dict[str, Any]], context: dict[str, Any]) -> Path:
    path = output_root / "reports" / "daily" / f"{context['date']}-action-list.md"
    lines = [
        f"# GitHub Insight Action List - {context['date']}",
        "",
        "## Today",
    ]
    for index, card in enumerate(cards[:8], start=1):
        lines.extend(
            [
                f"{index}. `{card['recommended_decision']}` {_repo_link(card)}",
                f"   - Profile: {card['recommended_profile_label']}",
                f"   - Score: {card['recommended_score']:.2f}",
                f"   - 30-60 minute action: {card['recommended_action']}",
                f"   - Expected output: {card['expected_output']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Review Later",
        ]
    )
    for card in cards[8:15]:
        lines.append(
            f"- `{card['recommended_decision']}` {_repo_link(card)} "
            f"({card['recommended_score']:.2f}) - {card['why_it_matters']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_all_reports(output_root: Path, cards: list[dict[str, Any]], context: dict[str, Any]) -> list[Path]:
    return [
        write_daily_brief(output_root, cards, context),
        write_profile_report(output_root, cards, context, "data_analyst", "data-analyst"),
        write_profile_report(output_root, cards, context, "data_scientist", "data-scientist"),
        write_action_list(output_root, cards, context),
    ]


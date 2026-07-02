"""Static dashboard and visual asset generation."""

from __future__ import annotations

import html
from collections import Counter
from pathlib import Path
from typing import Any

from github_insight.scoring import PROFILE_LABELS, PROFILES


PALETTE = {
    "general": "#2563eb",
    "data_analyst": "#0f766e",
    "data_scientist": "#b45309",
    "Build": "#15803d",
    "Study": "#2563eb",
    "Save": "#7c3aed",
    "Skip": "#64748b",
}


def _bar_svg(counts: Counter[str], title: str, width: int = 720, height: int = 260) -> str:
    labels = list(counts.keys()) or ["No data"]
    values = [counts[label] for label in labels] or [0]
    max_value = max(values) if values else 1
    left = 160
    top = 44
    bar_height = 28
    gap = 14
    rows = []
    for index, label in enumerate(labels):
        y = top + index * (bar_height + gap)
        bar_width = int((width - left - 40) * (counts[label] / max_value)) if max_value else 0
        color = PALETTE.get(label, "#334155")
        rows.append(
            f'<text x="20" y="{y + 19}" font-size="14" fill="#0f172a">{html.escape(label)}</text>'
            f'<rect x="{left}" y="{y}" width="{bar_width}" height="{bar_height}" rx="4" fill="{color}" />'
            f'<text x="{left + bar_width + 8}" y="{y + 19}" font-size="14" fill="#0f172a">{counts[label]}</text>'
        )
    dynamic_height = max(height, top + len(labels) * (bar_height + gap) + 28)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{dynamic_height}" '
        f'viewBox="0 0 {width} {dynamic_height}" role="img" aria-label="{html.escape(title)}">'
        '<rect width="100%" height="100%" fill="#f8fafc" />'
        f'<text x="20" y="28" font-size="20" font-weight="700" fill="#0f172a">{html.escape(title)}</text>'
        + "".join(rows)
        + "</svg>"
    )


def write_visual_summary(output_root: Path, cards: list[dict[str, Any]], date: str) -> Path:
    profile_counts = Counter(card["recommended_profile_label"] for card in cards)
    decision_counts = Counter(card["recommended_decision"] for card in cards)
    skill_counts: Counter[str] = Counter()
    for card in cards:
        skill_counts.update(card["skill_tags"][:3])

    width = 900
    height = 620
    skill_labels = skill_counts.most_common(8)
    skill_max = max([count for _, count in skill_labels], default=1)
    skill_rows = []
    for index, (skill, count) in enumerate(skill_labels):
        y = 390 + index * 24
        bar_width = int(520 * count / skill_max)
        skill_rows.append(
            f'<text x="38" y="{y + 16}" font-size="13" fill="#0f172a">{html.escape(skill)}</text>'
            f'<rect x="210" y="{y}" width="{bar_width}" height="18" rx="3" fill="#0f766e" />'
            f'<text x="{220 + bar_width}" y="{y + 15}" font-size="13" fill="#0f172a">{count}</text>'
        )

    profile_svg = _bar_svg(profile_counts, "Recommended profile mix", width=400, height=250)
    decision_svg = _bar_svg(decision_counts, "Decision mix", width=400, height=250)
    content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GitHub Insight summary for {date}">'
        '<rect width="100%" height="100%" fill="#ffffff" />'
        f'<text x="32" y="44" font-size="28" font-weight="700" fill="#0f172a">GitHub Insight Summary - {html.escape(date)}</text>'
        f'<g transform="translate(28,72) scale(0.9)">{profile_svg}</g>'
        f'<g transform="translate(468,72) scale(0.9)">{decision_svg}</g>'
        '<text x="32" y="354" font-size="20" font-weight="700" fill="#0f172a">Top skill tags</text>'
        + "".join(skill_rows)
        + "</svg>"
    )
    path = output_root / "assets" / "daily" / date / "insight-summary.svg"
    path.write_text(content, encoding="utf-8")
    return path


def write_dashboard(output_root: Path, cards: list[dict[str, Any]], context: dict[str, Any], visual_path: Path | None) -> Path:
    top_cards = cards[:12]
    avg_scores = {}
    for profile in PROFILES:
        avg_scores[profile] = (
            sum(card["scores"][profile]["score"] for card in cards) / len(cards) if cards else 0
        )
    decision_counts = Counter(card["recommended_decision"] for card in cards)
    profile_counts = Counter(card["recommended_profile"] for card in cards)

    visual_rel = ""
    if visual_path:
        visual_rel = "../" + visual_path.relative_to(output_root).as_posix()

    cards_html = []
    for card in top_cards:
        score_items = "".join(
            f"<li><span>{html.escape(PROFILE_LABELS[profile])}</span><strong>{card['scores'][profile]['score']:.2f}</strong></li>"
            for profile in PROFILES
        )
        cards_html.append(
            f"""
            <article class="repo-card">
              <div class="repo-heading">
                <a href="{html.escape(card['html_url'])}">{html.escape(card['full_name'])}</a>
                <span class="decision {html.escape(card['recommended_decision'].lower())}">{html.escape(card['recommended_decision'])}</span>
              </div>
              <p>{html.escape(card['description'])}</p>
              <ul class="score-list">{score_items}</ul>
              <p class="meta">{html.escape(', '.join(card['skill_tags']))} | {html.escape(card['language'])} | stars: {card['stars']}</p>
              <p class="action">{html.escape(card['recommended_action'])}</p>
            </article>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Insight Dashboard</title>
  <style>
    :root {{
      --ink: #0f172a;
      --muted: #475569;
      --line: #cbd5e1;
      --panel: #ffffff;
      --page: #f8fafc;
      --accent: #0f766e;
      --blue: #2563eb;
      --amber: #b45309;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--page);
      color: var(--ink);
      line-height: 1.5;
    }}
    header {{
      padding: 28px clamp(18px, 5vw, 56px);
      border-bottom: 1px solid var(--line);
      background: #ffffff;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }}
    .subtle {{ color: var(--muted); margin: 0; }}
    main {{ padding: 24px clamp(18px, 5vw, 56px) 48px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .stat span {{ color: var(--muted); font-size: 13px; }}
    .stat strong {{ display: block; font-size: 26px; margin-top: 4px; }}
    .visual {{
      margin: 0 0 24px;
      padding: 0;
    }}
    .visual img {{
      display: block;
      width: min(100%, 900px);
      height: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }}
    .repo-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 14px;
    }}
    .repo-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .repo-heading {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 8px;
    }}
    .repo-heading a {{
      color: var(--ink);
      font-weight: 700;
      text-decoration: none;
      overflow-wrap: anywhere;
    }}
    .decision {{
      border-radius: 999px;
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      padding: 4px 8px;
      white-space: nowrap;
    }}
    .decision.build {{ background: #15803d; }}
    .decision.study {{ background: var(--blue); }}
    .decision.save {{ background: #7c3aed; }}
    .decision.skip {{ background: #64748b; }}
    .score-list {{
      display: grid;
      gap: 6px;
      padding: 0;
      margin: 14px 0;
      list-style: none;
    }}
    .score-list li {{
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 5px;
    }}
    .score-list span, .meta {{ color: var(--muted); }}
    .action {{ margin-bottom: 0; }}
  </style>
</head>
<body>
  <header>
    <h1>GitHub Insight Dashboard</h1>
    <p class="subtle">Date {html.escape(context['date'])} | run {html.escape(context['run_label'])} | source {html.escape(context['source_status'])}</p>
  </header>
  <main>
    <section class="stats" aria-label="Run statistics">
      <div class="stat"><span>Repositories scored</span><strong>{len(cards)}</strong></div>
      <div class="stat"><span>Average general score</span><strong>{avg_scores['general']:.2f}</strong></div>
      <div class="stat"><span>Average analyst score</span><strong>{avg_scores['data_analyst']:.2f}</strong></div>
      <div class="stat"><span>Average scientist score</span><strong>{avg_scores['data_scientist']:.2f}</strong></div>
      <div class="stat"><span>Build decisions</span><strong>{decision_counts.get('Build', 0)}</strong></div>
      <div class="stat"><span>Analyst recommendations</span><strong>{profile_counts.get('data_analyst', 0)}</strong></div>
    </section>
    {"<section class='visual'><img src='" + html.escape(visual_rel) + "' alt='GitHub Insight visual summary'></section>" if visual_rel else ""}
    <section class="repo-grid" aria-label="Top repositories">
      {''.join(cards_html)}
    </section>
  </main>
</body>
</html>
"""
    path = output_root / "dashboard" / "index.html"
    path.write_text(html_doc, encoding="utf-8")
    return path


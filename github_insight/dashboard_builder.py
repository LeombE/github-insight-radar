"""Static GitHub Pages dashboard builder."""

from __future__ import annotations

import html
import json
import shutil
from collections import Counter
from pathlib import Path

from github_insight.models import InsightRecord, RunMetadata
from github_insight.utils import ensure_parent


def _json(records: list[InsightRecord], run: RunMetadata) -> str:
    return json.dumps({"run": run.to_dict(), "projects": [record.to_dict() for record in records]}, ensure_ascii=False)


def build_static_dashboard(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "docs" / "index.html"
    total = len(records)
    selected = len([record for record in records if record.recommended_action != "Skip for now"])
    risk_count = len([record for record in records if record.risk_flags])
    language_counts = Counter(record.language for record in records)
    topic_counts = Counter(topic for record in records for topic in record.topics[:6])
    archive_path = output_root / "docs" / "data" / "archive_index.json"
    archive = []
    if archive_path.exists():
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
    data_json = _json(records, run)
    language_rows = "".join(
        f"<li><span>{html.escape(language)}</span><strong>{count}</strong></li>"
        for language, count in language_counts.most_common(8)
    )
    topic_rows = "".join(
        f"<li><span>{html.escape(topic)}</span><strong>{count}</strong></li>"
        for topic, count in topic_counts.most_common(10)
    )
    archive_rows = "".join(
        f"<li><a href='../{html.escape(item.get('daily_brief_path', '#'))}'>{html.escape(item.get('date', 'unknown'))}</a> "
        f"<span>{html.escape(item.get('generated_at', ''))}</span> <strong>{html.escape(item.get('top_project', 'unavailable'))}</strong></li>"
        for item in archive[:20]
    )
    mode_label = html.escape(f"{run.mode.upper()} RUN")
    mode_class = "mode-live" if run.mode == "live" else "mode-mock"
    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GitHub Daily Intelligence Dashboard</title>
  <style>
    :root {{ --ink:#111827; --muted:#4b5563; --line:#d1d5db; --page:#f9fafb; --panel:#fff; --accent:#0f766e; --blue:#2563eb; --amber:#b45309; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:var(--page); line-height:1.5; }}
    header {{ padding:32px clamp(18px,5vw,64px); background:#fff; border-bottom:1px solid var(--line); }}
    h1 {{ margin:0 0 8px; font-size:clamp(28px,4vw,46px); letter-spacing:0; }}
    h2 {{ margin:28px 0 12px; font-size:22px; }}
    .header-row {{ display:flex; flex-wrap:wrap; align-items:center; gap:10px; }}
    .mode-badge {{ display:inline-flex; align-items:center; padding:6px 10px; border-radius:999px; color:#fff; font-size:12px; font-weight:700; letter-spacing:0.02em; }}
    .mode-live {{ background:#15803d; }} .mode-mock {{ background:#6d28d9; }}
    .subtle {{ color:var(--muted); margin:0; }}
    main {{ padding:24px clamp(18px,5vw,64px) 56px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:18px; }}
    .kpi, .panel, .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
    .kpi {{ padding:16px; }} .kpi span {{ color:var(--muted); font-size:13px; }} .kpi strong {{ display:block; font-size:26px; margin-top:4px; }}
    .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; padding:14px; margin:18px 0; }}
    select, input {{ border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:#fff; color:var(--ink); }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(310px,1fr)); gap:14px; }}
    .card {{ padding:16px; }} .card h3 {{ margin:0 0 8px; font-size:17px; overflow-wrap:anywhere; }}
    .meta, .risk, .evidence {{ color:var(--muted); font-size:13px; }}
    .score {{ display:flex; align-items:center; gap:8px; margin:10px 0; }} .bar {{ flex:1; height:9px; background:#e5e7eb; border-radius:99px; overflow:hidden; }} .fill {{ height:100%; background:var(--accent); }}
    .badge {{ display:inline-block; margin:0 6px 6px 0; padding:3px 8px; border-radius:999px; background:#e0f2fe; color:#075985; font-size:12px; }}
    .split {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }}
    .panel {{ padding:16px; }} .panel ul {{ margin:0; padding-left:18px; }} .archive li {{ margin:0 0 8px; }}
    a {{ color:var(--blue); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <h1>GitHub Daily Intelligence</h1>
      <span class="mode-badge {mode_class}">{mode_label}</span>
    </div>
    <p class="subtle">Generated at {html.escape(run.generated_at)} | Archive ordered by generated_at</p>
  </header>
  <main>
    <section class="kpis">
      <div class="kpi"><span>Total scanned today</span><strong>{run.repos_discovered}</strong></div>
      <div class="kpi"><span>Total selected today</span><strong>{selected}</strong></div>
      <div class="kpi"><span>Project cards</span><strong>{total}</strong></div>
      <div class="kpi"><span>Risk flagged</span><strong>{risk_count}</strong></div>
    </section>
    <section class="controls panel">
      <label>Audience <select id="audience"><option value="all">All</option><option value="general_user">General users</option><option value="data_analyst">Data analysts</option><option value="data_scientist">Data scientists</option></select></label>
      <label>Minimum score <input id="score" type="range" min="0" max="100" value="0"><span id="scoreValue">0</span></label>
      <label>Date <select id="date"><option value="{html.escape(run.date)}">{html.escape(run.date)}</option></select></label>
    </section>
    <h2>Top Projects</h2>
    <section id="cards" class="grid"></section>
    <h2>Distributions</h2>
    <section class="split">
      <div class="panel"><h3>Languages</h3><ul>{language_rows}</ul></div>
      <div class="panel"><h3>Topics</h3><ul>{topic_rows}</ul></div>
    </section>
    <h2>Archive</h2>
    <section class="panel archive"><ul>{archive_rows or '<li>No archive entries yet.</li>'}</ul></section>
    <h2>Methodology</h2>
    <section class="panel"><p>Scores combine usefulness, momentum, audience fit, maintenance, README quality, reproducibility, data/demo signals, and risk. Metadata and README evidence are treated cautiously; this dashboard is an intelligence aid, not a definitive ranking.</p></section>
  </main>
  <script id="payload" type="application/json">{data_json}</script>
  <script>
    const payload = JSON.parse(document.getElementById('payload').textContent);
    const projects = payload.projects;
    const cards = document.getElementById('cards');
    const audience = document.getElementById('audience');
    const score = document.getElementById('score');
    const scoreValue = document.getElementById('scoreValue');
    function render() {{
      scoreValue.textContent = score.value;
      const minScore = Number(score.value);
      const selectedAudience = audience.value;
      const filtered = projects
        .filter(p => p.overall_insight_score >= minScore)
        .filter(p => selectedAudience === 'all' || p.primary_audience === selectedAudience || (p.audience_tags || []).includes(selectedAudience))
        .slice(0, 30);
      cards.innerHTML = filtered.map(p => `
        <article class="card">
          <h3><a href="${{p.html_url}}">${{p.full_name}}</a></h3>
          <p>${{p.one_sentence_summary}}</p>
          <div>${{(p.audience_tags || []).map(a => `<span class="badge">${{a.replace('_', ' ')}}</span>`).join('')}}</div>
          <div class="score"><strong>${{p.overall_insight_score.toFixed(2)}}</strong><div class="bar"><div class="fill" style="width:${{p.overall_insight_score}}%"></div></div></div>
          <p class="meta">${{p.language}} | stars ${{p.stars}} | forks ${{p.forks}} | issues ${{p.open_issues}} | license ${{p.license}}</p>
          <p><strong>Action:</strong> ${{p.recommended_action}}</p>
          <p><strong>Portfolio:</strong> ${{p.portfolio_project_idea}}</p>
          <p class="evidence"><strong>Evidence:</strong> ${{(p.evidence || []).slice(0,3).join('; ')}}</p>
          <p class="risk"><strong>Risk:</strong> ${{(p.risk_flags && p.risk_flags.length) ? p.risk_flags.join(', ') : 'No major risk flag from collected evidence.'}}</p>
        </article>`).join('');
    }}
    audience.addEventListener('change', render); score.addEventListener('input', render); render();
  </script>
</body>
</html>
"""
    ensure_parent(path).write_text(doc, encoding="utf-8")
    legacy = output_root / "dashboard" / "index.html"
    ensure_parent(legacy)
    shutil.copyfile(path, legacy)
    return path

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
    return json.dumps({"run": run.to_dict(), "projects": [_dashboard_record(record) for record in records]}, ensure_ascii=False)


def _archive_mode(item) -> str:
    mode = str(item.get("mode") or "").strip().lower()
    if mode in {"live", "mock"}:
        return mode
    return "unknown"


def _is_default_live_archive_entry(item) -> bool:
    if _archive_mode(item) != "live":
        return False
    run_id = str(item.get("run_id") or "").strip().lower()
    if run_id:
        return run_id.startswith("live-")
    top_project = str(item.get("top_project") or "").strip().lower()
    return not top_project.startswith("sample-org/")


def _option_rows(values, all_label: str = "All") -> str:
    cleaned = sorted({str(value).strip() for value in values if str(value).strip()}, key=str.lower)
    rows = [f'<option value="all">{html.escape(all_label)}</option>']
    rows.extend(
        f'<option value="{html.escape(value, quote=True)}">{html.escape(value)}</option>'
        for value in cleaned
    )
    return "".join(rows)

def _risk_severity(risk_score: float) -> str:
    try:
        score = float(risk_score)
    except (TypeError, ValueError):
        score = 0.0
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def _confidence_label(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized == "high":
        return "High"
    if normalized == "medium":
        return "Medium"
    return "Low"


def _evidence_summary(record: InsightRecord) -> str:
    evidence = [item for item in record.evidence[:3] if item]
    if evidence:
        return "; ".join(evidence)
    return f"Stars: {record.stars}; Forks: {record.forks}; Language: {record.language}"


def _caveat_summary(record: InsightRecord) -> str:
    if record.risk_flags:
        return "; ".join(record.risk_flags[:3])
    return "No major caveat from collected evidence."


def _dashboard_record(record: InsightRecord) -> dict:
    item = record.to_dict()
    item["dashboard_risk_severity"] = _risk_severity(record.risk_score)
    item["dashboard_confidence_label"] = _confidence_label(record.confidence)
    item["dashboard_evidence_summary"] = _evidence_summary(record)
    item["dashboard_caveat_summary"] = _caveat_summary(record)
    return item

def build_static_dashboard(output_root: Path, run: RunMetadata, records: list[InsightRecord]) -> Path:
    path = output_root / "docs" / "index.html"
    total = len(records)
    selected = len([record for record in records if record.recommended_action != "Skip for now"])
    risk_counts = Counter(_risk_severity(record.risk_score) for record in records)
    language_counts = Counter(record.language for record in records)
    topic_counts = Counter(topic for record in records for topic in record.topics[:6])
    archive_path = output_root / "docs" / "data" / "archive_index.json"
    archive = []
    if archive_path.exists():
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
    date_options = _option_rows([record.date for record in records], all_label="All dates")
    language_options = _option_rows(
        [record.language for record in records if record.language != "unavailable"],
        all_label="All languages",
    )
    action_options = _option_rows(
        [record.recommended_action for record in records],
        all_label="All actions",
    )
    data_json = _json(records, run)
    language_rows = "".join(
        f"<li><span>{html.escape(language)}</span><strong>{count}</strong></li>"
        for language, count in language_counts.most_common(8)
    )
    topic_rows = "".join(
        f"<li><span>{html.escape(topic)}</span><strong>{count}</strong></li>"
        for topic, count in topic_counts.most_common(10)
    )
    live_archive = [item for item in archive if _is_default_live_archive_entry(item)]
    archive_rows = "".join(
        f"<li><a href='../{html.escape(item.get('daily_brief_path', '#'))}'>{html.escape(item.get('date', 'unknown'))}</a> "
        f"<span>{html.escape(item.get('generated_at', ''))}</span> <strong>{html.escape(item.get('top_project', 'unavailable'))}</strong></li>"
        for item in live_archive[:20]
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
    :root {{ --ink:#111827; --muted:#4b5563; --muted-soft:#6b7280; --line:#d1d5db; --line-soft:#e5e7eb; --page:#f8fafc; --panel:#fff; --accent:#0f766e; --accent-soft:#ccfbf1; --blue:#2563eb; --blue-soft:#dbeafe; --shadow:0 1px 2px rgba(15,23,42,.06); }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:var(--ink); background:var(--page); line-height:1.5; }}
    header {{ padding:30px clamp(18px,5vw,64px); background:#fff; border-bottom:1px solid var(--line); }}
    h1 {{ margin:0; font-size:clamp(28px,4vw,44px); letter-spacing:0; line-height:1.05; }}
    h2 {{ margin:30px 0 12px; font-size:21px; line-height:1.2; }}
    h3 {{ line-height:1.25; }}
    .header-row {{ display:flex; flex-wrap:wrap; align-items:flex-start; justify-content:space-between; gap:16px; }}
    .title-block {{ display:grid; gap:8px; min-width:min(100%,520px); }}
    .mode-badge {{ display:inline-flex; align-items:center; min-height:30px; padding:6px 11px; border-radius:999px; color:#fff; font-size:12px; font-weight:800; letter-spacing:0.04em; }}
    .mode-live {{ background:#15803d; }} .mode-mock {{ background:#6d28d9; }}
    .subtle {{ color:var(--muted); margin:0; }}
    main {{ padding:24px clamp(18px,5vw,64px) 56px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; margin-bottom:20px; }}
    .kpi, .panel, .card {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
    .kpi {{ min-height:92px; padding:15px 16px; border-top:3px solid var(--accent); box-shadow:var(--shadow); }}
    .kpi span {{ color:var(--muted); font-size:12px; font-weight:800; letter-spacing:0.04em; text-transform:uppercase; }}
    .kpi strong {{ display:block; font-size:30px; line-height:1; margin-top:12px; }}
    .controls {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; align-items:end; padding:16px; margin:18px 0 22px; box-shadow:var(--shadow); }}
    .controls label {{ display:grid; gap:6px; color:var(--muted); font-size:12px; font-weight:800; letter-spacing:0.03em; text-transform:uppercase; }}
    select, input {{ width:100%; border:1px solid var(--line); border-radius:6px; padding:9px 10px; background:#fff; color:var(--ink); font:inherit; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }}
    .card {{ padding:0; overflow:hidden; box-shadow:var(--shadow); }}
    .card-main {{ padding:18px; display:grid; gap:13px; }}
    .card-head {{ display:grid; grid-template-columns:minmax(0,1fr) auto; gap:14px; align-items:start; }}
    .card h3 {{ margin:0; font-size:18px; overflow-wrap:anywhere; }}
    .card p {{ margin:0; }}
    .summary {{ color:#1f2937; font-size:14px; }}
    .score-lockup {{ min-width:86px; text-align:right; padding:8px 10px; background:#f0fdfa; border:1px solid #99f6e4; border-radius:8px; }}
    .score-lockup span {{ display:block; color:var(--muted); font-size:11px; font-weight:800; letter-spacing:0.04em; text-transform:uppercase; }}
    .score-lockup strong {{ display:block; color:var(--accent); font-size:25px; line-height:1.05; }}
    .badge-strip {{ display:flex; flex-wrap:wrap; gap:6px; align-items:center; }}
    .score {{ display:flex; align-items:center; gap:8px; margin:0; }}
    .bar {{ flex:1; height:9px; background:#e5e7eb; border-radius:99px; overflow:hidden; }} .fill {{ height:100%; background:var(--accent); }}
    .meta-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px 12px; padding-top:2px; }}
    .meta-item {{ min-width:0; color:var(--ink); font-size:13px; }}
    .meta-item span {{ display:block; color:var(--muted-soft); font-size:11px; font-weight:800; letter-spacing:0.03em; text-transform:uppercase; }}
    .action-callout {{ padding-top:12px; border-top:1px solid var(--line-soft); }}
    .action-label {{ display:inline-flex; margin-bottom:6px; padding:3px 7px; border-radius:6px; background:var(--blue-soft); color:#1d4ed8; font-size:12px; font-weight:800; }}
    .portfolio-idea {{ color:#1f2937; font-size:14px; }}
    .insight-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; padding-top:12px; border-top:1px solid var(--line-soft); }}
    .evidence, .risk {{ color:var(--muted); font-size:13px; }}
    .evidence strong, .risk strong {{ display:block; color:var(--ink); margin-bottom:3px; }}
    .badge, .risk-badge, .confidence-badge {{ display:inline-block; margin:0; padding:4px 8px; border-radius:999px; font-size:12px; font-weight:800; }}
    .badge {{ background:#e0f2fe; color:#075985; }}
    .risk-low {{ background:#dcfce7; color:#166534; }} .risk-medium {{ background:#fef3c7; color:#92400e; }} .risk-high {{ background:#fee2e2; color:#991b1b; }}
    .confidence-high {{ background:#ecfdf5; color:#047857; }} .confidence-medium {{ background:#eef2ff; color:#4338ca; }} .confidence-low {{ background:#f3f4f6; color:#374151; }}
    .split {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:14px; }}
    .panel {{ padding:16px; }} .panel ul {{ margin:0; padding-left:18px; }} .archive li {{ margin:0 0 8px; }}
    a {{ color:var(--blue); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
    @media (max-width:640px) {{ .card-head {{ grid-template-columns:1fr; }} .score-lockup {{ text-align:left; width:max-content; }} .meta-grid {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <div class="header-row">
      <div class="title-block">
        <h1>GitHub Daily Intelligence</h1>
        <p class="subtle">Generated at {html.escape(run.generated_at)} | Archive ordered by generated_at</p>
      </div>
      <span class="mode-badge {mode_class}">{mode_label}</span>
    </div>
  </header>
  <main>
    <section class="kpis">
      <div class="kpi"><span>Total scanned today</span><strong>{run.repos_discovered}</strong></div>
      <div class="kpi"><span>Total selected today</span><strong>{selected}</strong></div>
      <div class="kpi"><span>Project cards</span><strong>{total}</strong></div>
      <div class="kpi"><span>Low risk</span><strong>{risk_counts["Low"]}</strong></div>
      <div class="kpi"><span>Medium risk</span><strong>{risk_counts["Medium"]}</strong></div>
      <div class="kpi"><span>High risk</span><strong>{risk_counts["High"]}</strong></div>
    </section>
    <section class="controls panel">
      <label>Search <input id="search" type="search" placeholder="Repo, topic, summary"></label>
      <label>Audience <select id="audience"><option value="all">All audiences</option><option value="general_user">General users</option><option value="data_analyst">Data analysts</option><option value="data_scientist">Data scientists</option></select></label>
      <label>Minimum score <input id="score" type="range" min="0" max="100" value="0"><span id="scoreValue">0</span></label>
      <label>Display <select id="displayLimit"><option value="20" selected>Top 20</option><option value="50">Top 50</option><option value="100">Top 100</option><option value="all">All</option></select></label>
      <label>Date <select id="date">{date_options}</select></label>
      <label>Language <select id="language">{language_options}</select></label>
      <label>Action <select id="action">{action_options}</select></label>
      <label>Risk <select id="risk"><option value="all">All risk states</option><option value="low">Low risk</option><option value="medium">Medium risk</option><option value="high">High risk</option><option value="none">No risk flags</option><option value="flagged">Has risk flags</option></select></label>
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
    const search = document.getElementById('search');
    const audience = document.getElementById('audience');
    const score = document.getElementById('score');
    const scoreValue = document.getElementById('scoreValue');
    const displayLimit = document.getElementById('displayLimit');
    const date = document.getElementById('date');
    const language = document.getElementById('language');
    const action = document.getElementById('action');
    const risk = document.getElementById('risk');
    function normalize(value) {{ return (value || '').toString().toLowerCase(); }}
    function searchableText(p) {{
      return [p.full_name, p.one_sentence_summary, p.why_it_matters, p.language, p.recommended_action, (p.topics || []).join(' '), (p.evidence || []).join(' '), (p.risk_flags || []).join(' ')].map(normalize).join(' ');
    }}
    function riskSeverityClass(p) {{ return normalize(p.dashboard_risk_severity || 'Low'); }}
    function confidenceClass(p) {{ return normalize(p.dashboard_confidence_label || 'Low'); }}
    function matchesRisk(p, selectedRisk) {{
      const riskFlags = p.risk_flags || [];
      if (selectedRisk === 'none') return riskFlags.length === 0;
      if (selectedRisk === 'flagged') return riskFlags.length > 0;
      if (['low', 'medium', 'high'].includes(selectedRisk)) return riskSeverityClass(p) === selectedRisk;
      return true;
    }}
    function render() {{
      scoreValue.textContent = score.value;
      const minScore = Number(score.value);
      const selectedAudience = audience.value;
      const selectedDate = date.value;
      const selectedLanguage = language.value;
      const selectedAction = action.value;
      const selectedRisk = risk.value;
      const query = normalize(search.value).trim();
      const filtered = projects
        .filter(p => p.overall_insight_score >= minScore)
        .filter(p => selectedAudience === 'all' || p.primary_audience === selectedAudience || (p.audience_tags || []).includes(selectedAudience))
        .filter(p => selectedDate === 'all' || p.date === selectedDate)
        .filter(p => selectedLanguage === 'all' || p.language === selectedLanguage)
        .filter(p => selectedAction === 'all' || p.recommended_action === selectedAction)
        .filter(p => matchesRisk(p, selectedRisk))
        .filter(p => !query || searchableText(p).includes(query));
      const limit = displayLimit.value === 'all' ? filtered.length : Number(displayLimit.value);
      const visible = filtered.slice(0, limit);
      cards.innerHTML = visible.map(p => `
        <article class="card">
          <div class="card-main">
            <div class="card-head">
              <div>
                <h3><a href="${{p.html_url}}">${{p.full_name}}</a></h3>
                <p class="summary">${{p.one_sentence_summary}}</p>
              </div>
              <div class="score-lockup"><span>Score</span><strong>${{p.overall_insight_score.toFixed(2)}}</strong></div>
            </div>
            <div class="badge-strip">${{(p.audience_tags || []).map(a => `<span class="badge">${{a.replace('_', ' ')}}</span>`).join('')}}<span class="risk-badge risk-${{riskSeverityClass(p)}}">${{p.dashboard_risk_severity}} risk</span><span class="confidence-badge confidence-${{confidenceClass(p)}}">${{p.dashboard_confidence_label}} confidence</span></div>
            <div class="score"><div class="bar"><div class="fill" style="width:${{p.overall_insight_score}}%"></div></div></div>
            <div class="meta-grid">
              <div class="meta-item"><span>Language</span>${{p.language}}</div>
              <div class="meta-item"><span>License</span>${{p.license}}</div>
              <div class="meta-item"><span>Stars / Forks</span>${{p.stars}} / ${{p.forks}}</div>
              <div class="meta-item"><span>Open issues</span>${{p.open_issues}}</div>
            </div>
            <div class="action-callout"><span class="action-label">Action: ${{p.recommended_action}}</span><p class="portfolio-idea">${{p.portfolio_project_idea}}</p></div>
            <div class="insight-grid">
              <p class="evidence"><strong>Key evidence:</strong> ${{p.dashboard_evidence_summary}}</p>
              <p class="risk"><strong>Caveat:</strong> ${{p.dashboard_caveat_summary}}</p>
            </div>
          </div>
        </article>`).join('');
    }}
    search.addEventListener('input', render);
    audience.addEventListener('change', render);
    score.addEventListener('input', render);
    displayLimit.addEventListener('change', render);
    date.addEventListener('change', render);
    language.addEventListener('change', render);
    action.addEventListener('change', render);
    risk.addEventListener('change', render);
    render();
  </script>
</body>
</html>
"""
    ensure_parent(path).write_text(doc, encoding="utf-8")
    legacy = output_root / "dashboard" / "index.html"
    ensure_parent(legacy)
    shutil.copyfile(path, legacy)
    return path

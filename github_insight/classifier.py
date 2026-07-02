"""Audience classification and deterministic insight scoring."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from github_insight.models import InsightRecord, RepositoryEnriched


AUDIENCE_LABELS = {
    "general_user": "General User",
    "data_analyst": "Data Analyst",
    "data_scientist": "Data Scientist",
}

AUDIENCE_KEYWORDS = {
    "general_user": {
        "productivity",
        "automation",
        "tool",
        "app",
        "cli",
        "workflow",
        "self-hosted",
        "ai",
        "agent",
        "learning",
    },
    "data_analyst": {
        "sql",
        "analytics",
        "dashboard",
        "business-intelligence",
        "bi",
        "tableau",
        "powerbi",
        "pandas",
        "excel",
        "etl",
        "dbt",
        "metrics",
        "reporting",
        "data-cleaning",
        "visualization",
        "csv",
    },
    "data_scientist": {
        "machine-learning",
        "ml",
        "deep-learning",
        "llm",
        "rag",
        "nlp",
        "computer-vision",
        "time-series",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "benchmark",
        "dataset",
        "model",
        "training",
        "evaluation",
    },
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, value)), 2)


def _blob(enriched: RepositoryEnriched) -> str:
    raw = enriched.raw
    return " ".join(
        [
            raw.full_name,
            raw.description,
            raw.language,
            " ".join(raw.topics),
            raw.source_query,
            enriched.readme_text_excerpt,
        ]
    ).lower()


def _keyword_score(blob: str, keywords: set[str]) -> float:
    hits = sum(1 for keyword in keywords if keyword in blob)
    return clamp((hits / max(1, min(len(keywords), 8))) * 100.0)


def _log_score(value: int, soft_cap: int) -> float:
    if value <= 0:
        return 0.0
    return clamp(math.log10(value + 1) / math.log10(soft_cap + 1) * 100.0)


def _parse_dt(value: str) -> datetime | None:
    if not value or value == "unavailable":
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _recency_score(value: str) -> float:
    parsed = _parse_dt(value)
    if parsed is None:
        return 0.0
    age_days = max(0, (datetime.now(timezone.utc) - parsed).days)
    if age_days <= 7:
        return 100.0
    if age_days <= 30:
        return 85.0
    if age_days <= 90:
        return 70.0
    if age_days <= 180:
        return 55.0
    if age_days <= 365:
        return 35.0
    return 15.0


def classify_audiences(enriched: RepositoryEnriched) -> dict[str, float]:
    blob = _blob(enriched)
    raw = enriched.raw
    scores = {audience: _keyword_score(blob, keywords) for audience, keywords in AUDIENCE_KEYWORDS.items()}
    for audience in raw.source_audiences:
        if audience in scores:
            scores[audience] = clamp(scores[audience] + 18.0)
    if raw.language.lower() == "python":
        scores["data_analyst"] = clamp(scores["data_analyst"] + 6.0)
        scores["data_scientist"] = clamp(scores["data_scientist"] + 6.0)
    if enriched.has_csv_or_sql or enriched.has_dataset:
        scores["data_analyst"] = clamp(scores["data_analyst"] + 12.0)
    if enriched.has_notebook or "model" in blob or "benchmark" in blob:
        scores["data_scientist"] = clamp(scores["data_scientist"] + 12.0)
    if "cli" in blob or "productivity" in blob or "automation" in blob:
        scores["general_user"] = clamp(scores["general_user"] + 10.0)
    return scores


def build_risk_flags(enriched: RepositoryEnriched) -> list[str]:
    raw = enriched.raw
    flags = list(dict.fromkeys(enriched.risk_flags))
    if raw.archived:
        flags.append("archived")
    if raw.disabled:
        flags.append("disabled")
    if raw.license_spdx_id == "unavailable" and raw.license_name == "unavailable":
        flags.append("no license")
    pushed = _parse_dt(raw.pushed_at)
    if pushed and (datetime.now(timezone.utc) - pushed).days > 365:
        flags.append("stale for more than 12 months")
    if raw.open_issues_count > 0 and raw.stargazers_count > 0:
        ratio = raw.open_issues_count / max(raw.stargazers_count, 1)
        if ratio > 0.15:
            flags.append("many open issues relative to stars")
    if raw.fork:
        flags.append("fork-only repository")
    return list(dict.fromkeys(flags))


def difficulty_for(enriched: RepositoryEnriched, primary_audience: str) -> str:
    blob = _blob(enriched)
    if primary_audience == "data_scientist" and any(word in blob for word in ["paper", "arxiv", "benchmark", "training"]):
        return "Research-heavy"
    if enriched.raw.language.lower() in {"c++", "rust", "cuda"} or enriched.raw.size > 200000:
        return "Advanced"
    if enriched.has_installation_instructions and enriched.has_usage_examples:
        return "Intermediate"
    if enriched.readme_length == 0:
        return "Unknown"
    return "Beginner"


def recommended_action(score: float, primary_audience: str, risk_flags: list[str]) -> str:
    if "archived" in risk_flags or "disabled" in risk_flags:
        return "Skip for now"
    if score >= 80:
        return "Try today"
    if score >= 70:
        return "Use as portfolio reference"
    if score >= 60:
        return "Study for learning"
    if primary_audience == "data_scientist" and score >= 45:
        return "Track for research"
    if score >= 45:
        return "Watch this week"
    return "Skip for now"


def _confidence(enriched: RepositoryEnriched, risk_flags: list[str]) -> str:
    if enriched.readme_quality_score >= 70 and len(risk_flags) <= 2:
        return "high"
    if enriched.readme_length > 0 and enriched.raw.description != "unavailable":
        return "medium"
    return "low"


def _one_sentence(enriched: RepositoryEnriched, primary_audience: str) -> str:
    raw = enriched.raw
    audience = AUDIENCE_LABELS.get(primary_audience, primary_audience)
    desc = raw.description if raw.description != "unavailable" else "A GitHub repository with limited verified description metadata"
    return f"{raw.full_name} is a {raw.language} project for {audience}: {desc}"


def _use_cases(primary_audience: str) -> list[str]:
    if primary_audience == "data_analyst":
        return ["Build a metrics or dashboard case study", "Practice data cleaning and reporting", "Extract a portfolio workflow"]
    if primary_audience == "data_scientist":
        return ["Review reproducibility signals", "Design a baseline experiment", "Track model, dataset, or benchmark ideas"]
    return ["Evaluate practical utility", "Try a small workflow", "Decide whether to adopt, save, or skip"]


def score_enriched_repository(
    enriched: RepositoryEnriched,
    date: str,
    history: dict[str, Any],
    source_status: str,
) -> InsightRecord:
    raw = enriched.raw
    audience_scores = classify_audiences(enriched)
    primary_audience = max(audience_scores, key=lambda key: audience_scores[key])
    audience_fit_score = audience_scores[primary_audience]
    usefulness = clamp(0.45 * audience_fit_score + 0.25 * _log_score(raw.stargazers_count, 25000) + 0.30 * enriched.readme_quality_score)
    momentum = clamp(0.55 * _recency_score(raw.pushed_at) + 0.25 * _recency_score(raw.updated_at) + 0.20 * _log_score(raw.stargazers_count, 15000))
    maintenance = clamp(40 + (20 if not raw.archived else -35) + (15 if raw.license_spdx_id != "unavailable" or raw.license_name != "unavailable" else -10) + 0.25 * _recency_score(raw.pushed_at))
    reproducibility = clamp(25 + len(enriched.reproducibility_signals) * 12 + (10 if enriched.has_pyproject or enriched.has_requirements else 0) + (10 if enriched.has_dockerfile else 0))
    data_asset = clamp((30 if enriched.has_dataset else 0) + (25 if enriched.has_csv_or_sql else 0) + (20 if enriched.has_demo_link else 0) + (20 if enriched.has_notebook else 0) + _keyword_score(_blob(enriched), {"dashboard", "visualization", "streamlit", "plotly"}) * 0.2)
    dashboard_readiness = clamp((35 if "dashboard" in _blob(enriched) else 0) + (25 if enriched.has_demo_link else 0) + (20 if enriched.has_csv_or_sql else 0) + (20 if enriched.has_usage_examples else 0))
    risk_flags = build_risk_flags(enriched)
    risk_score = clamp(len(risk_flags) * 15 + (35 if raw.archived else 0) + (20 if raw.disabled else 0))
    weights = {
        "usefulness_score": 0.20,
        "momentum_score": 0.20,
        "audience_fit_score": 0.15,
        "maintenance_score": 0.15,
        "readme_quality_score": 0.10,
        "reproducibility_score": 0.10,
        "data_asset_or_demo_score": 0.10,
        "risk_score": -0.15,
    }
    overall = clamp(
        weights["usefulness_score"] * usefulness
        + weights["momentum_score"] * momentum
        + weights["audience_fit_score"] * audience_fit_score
        + weights["maintenance_score"] * maintenance
        + weights["readme_quality_score"] * enriched.readme_quality_score
        + weights["reproducibility_score"] * reproducibility
        + weights["data_asset_or_demo_score"] * data_asset
        + weights["risk_score"] * risk_score
    )
    seen = history.get(raw.full_name.lower(), {}) if isinstance(history, dict) else {}
    first_seen = str(seen.get("first_seen", date))
    days_seen = int(seen.get("appearances", 0)) + 1 if seen else 1
    evidence = [
        f"Stars: {raw.stargazers_count}",
        f"Forks: {raw.forks_count}",
        f"Language: {raw.language}",
        f"License: {raw.license_spdx_id if raw.license_spdx_id != 'unavailable' else raw.license_name}",
        f"README length: {enriched.readme_length}",
        f"Topics: {', '.join(raw.topics) if raw.topics else 'unavailable'}",
    ]
    portfolio = f"Turn {raw.name} into a concise portfolio note with problem, evidence, implementation idea, output, and limitations."
    analyst_angle = "Useful for dashboards, metrics, SQL, ETL, or reporting practice." if audience_scores["data_analyst"] >= 45 else "Limited analyst angle from available metadata."
    scientist_angle = "Useful for model, benchmark, notebook, or experiment review." if audience_scores["data_scientist"] >= 45 else "Limited data science angle from available metadata."
    general_angle = "Potential practical tool or workflow improvement for general users." if audience_scores["general_user"] >= 45 else "May be too technical for general users."
    return InsightRecord(
        date=date,
        full_name=raw.full_name,
        html_url=raw.html_url,
        primary_audience=primary_audience,
        audience_tags=([key for key, value in audience_scores.items() if value >= 45] or [primary_audience]),
        general_user_score=clamp(audience_scores["general_user"]),
        data_analyst_score=clamp(audience_scores["data_analyst"]),
        data_scientist_score=clamp(audience_scores["data_scientist"]),
        usefulness_score=usefulness,
        momentum_score=momentum,
        reproducibility_score=reproducibility,
        data_asset_score=data_asset,
        dashboard_readiness_score=dashboard_readiness,
        maintenance_score=maintenance,
        risk_score=risk_score,
        overall_insight_score=overall,
        difficulty_level=difficulty_for(enriched, primary_audience),
        recommended_action=recommended_action(overall, primary_audience, risk_flags),
        one_sentence_summary=_one_sentence(enriched, primary_audience),
        why_it_matters=f"It maps to {AUDIENCE_LABELS.get(primary_audience, primary_audience)} needs with an evidence-based score of {overall:.2f}.",
        practical_use_cases=_use_cases(primary_audience),
        data_analyst_angle=analyst_angle,
        data_scientist_angle=scientist_angle,
        general_user_angle=general_angle,
        portfolio_project_idea=portfolio,
        evidence=evidence,
        risk_flags=risk_flags,
        image_asset_path="",
        image_prompt_path="",
        confidence=_confidence(enriched, risk_flags),
        language=raw.language,
        topics=raw.topics,
        stars=raw.stargazers_count,
        forks=raw.forks_count,
        open_issues=raw.open_issues_count,
        license=raw.license_spdx_id if raw.license_spdx_id != "unavailable" else raw.license_name,
        pushed_at=raw.pushed_at,
        first_seen_date=first_seen,
        last_seen_date=date,
        days_seen=days_seen,
        rank_today=None,
        rank_previous=None,
        rank_change=None,
        star_delta_since_previous_seen=None,
        fork_delta_since_previous_seen=None,
        source_status=source_status,
    )


def build_insights(
    enriched_repos: list[RepositoryEnriched], date: str, history: dict[str, Any], source_status: str
) -> list[InsightRecord]:
    records = [score_enriched_repository(repo, date, history, source_status) for repo in enriched_repos]
    records.sort(key=lambda item: (item.overall_insight_score, item.stars, item.full_name), reverse=True)
    for index, record in enumerate(records, start=1):
        record.rank_today = index
    return records


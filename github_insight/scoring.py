"""Profile-aware repository scoring."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from github_insight.models import Repository


PROFILES = ("general", "data_analyst", "data_scientist")

PROFILE_LABELS = {
    "general": "General users",
    "data_analyst": "Data analysts",
    "data_scientist": "Data scientists",
}

PROFILE_KEYWORDS = {
    "general": {
        "tool",
        "automation",
        "productivity",
        "workflow",
        "awesome",
        "template",
        "cli",
        "dashboard",
        "app",
        "agent",
        "ai",
    },
    "data_analyst": {
        "sql",
        "excel",
        "powerbi",
        "power-bi",
        "tableau",
        "dashboard",
        "analytics",
        "pandas",
        "visualization",
        "data-cleaning",
        "business-intelligence",
        "etl",
        "dbt",
    },
    "data_scientist": {
        "machine-learning",
        "ml",
        "deep-learning",
        "ai",
        "llm",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "statistics",
        "model",
        "nlp",
        "computer-vision",
        "optimization",
    },
}

SKILL_KEYWORDS = {
    "SQL": {"sql", "postgres", "mysql", "duckdb", "sqlite", "analytics"},
    "Python": {"python", "pandas", "numpy", "fastapi", "cli"},
    "Data cleaning": {"cleaning", "data-cleaning", "etl", "pipeline", "quality"},
    "Dashboarding": {"dashboard", "visualization", "plotly", "streamlit", "tableau", "powerbi"},
    "Data engineering": {"etl", "data-engineering", "pipeline", "warehouse", "dbt"},
    "Machine learning": {"machine-learning", "ml", "model", "scikit-learn", "pytorch", "tensorflow"},
    "AI automation": {"ai", "agent", "llm", "automation", "workflow"},
    "Optimization": {"optimization", "linear-programming", "solver", "or-tools"},
}


def _text_blob(repo: Repository) -> str:
    parts = [
        repo.full_name,
        repo.description,
        repo.language,
        " ".join(repo.topics),
        repo.source_query,
    ]
    return " ".join(parts).lower()


def _keyword_score(blob: str, keywords: set[str]) -> float:
    if not keywords:
        return 0.0
    hits = sum(1 for keyword in keywords if keyword in blob)
    return min(10.0, (hits / min(len(keywords), 6)) * 10.0)


def _log_score(value: int, soft_cap: int) -> float:
    if value <= 0:
        return 0.0
    return min(10.0, math.log10(value + 1) / math.log10(soft_cap + 1) * 10.0)


def _parse_datetime(value: str) -> datetime | None:
    if not value or value == "unavailable":
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _recency_score(value: str) -> float:
    parsed = _parse_datetime(value)
    if not parsed:
        return 0.0
    age_days = max(0, (datetime.now(timezone.utc) - parsed).days)
    if age_days <= 7:
        return 10.0
    if age_days <= 30:
        return 8.0
    if age_days <= 90:
        return 6.5
    if age_days <= 180:
        return 5.0
    if age_days <= 365:
        return 3.5
    return 2.0


def infer_skill_tags(repo: Repository) -> list[str]:
    blob = _text_blob(repo)
    tags = [skill for skill, keywords in SKILL_KEYWORDS.items() if _keyword_score(blob, keywords) > 0]
    return tags[:5] if tags else ["General evaluation"]


def component_scores(repo: Repository, profile: str) -> dict[str, float]:
    blob = _text_blob(repo)
    profile_keywords = PROFILE_KEYWORDS[profile]
    career_relevance = _keyword_score(blob, profile_keywords)
    if repo.language.lower() == "python" and profile in {"data_analyst", "data_scientist"}:
        career_relevance = min(10.0, career_relevance + 1.2)

    actionability = 3.5
    actionability += 1.5 if repo.description != "unavailable" else 0
    actionability += min(2.0, len(repo.topics) * 0.35)
    actionability += 1.0 if any(word in blob for word in {"template", "example", "tutorial", "starter", "demo"}) else 0
    actionability += 1.0 if repo.language != "unavailable" else 0
    actionability = min(10.0, actionability)

    repo_quality = 0.45 * _log_score(repo.stars, 20000)
    repo_quality += 0.25 * _log_score(repo.forks, 4000)
    repo_quality += 1.0 if repo.license != "unavailable" else 0
    repo_quality += 1.0 if not repo.archived else -2.0
    repo_quality += 1.0 if repo.description != "unavailable" else 0
    repo_quality = max(0.0, min(10.0, repo_quality))

    momentum = 0.7 * _recency_score(repo.pushed_at) + 0.3 * _recency_score(repo.updated_at)
    if repo.archived:
        momentum = min(momentum, 2.0)

    portfolio_keywords = {
        "dashboard",
        "analytics",
        "pipeline",
        "automation",
        "etl",
        "visualization",
        "machine-learning",
        "app",
        "template",
        "project",
    }
    portfolio_value = 0.65 * _keyword_score(blob, portfolio_keywords)
    portfolio_value += 0.2 * _log_score(repo.stars, 10000)
    portfolio_value += 1.0 if repo.language in {"Python", "Jupyter Notebook", "SQL"} else 0
    portfolio_value = min(10.0, portfolio_value)

    profile_fit = 0.7 * career_relevance + 0.3 * _keyword_score(blob, PROFILE_KEYWORDS[profile])

    return {
        "career_relevance": round(career_relevance, 2),
        "actionability": round(actionability, 2),
        "repo_quality": round(repo_quality, 2),
        "momentum": round(momentum, 2),
        "portfolio_value": round(portfolio_value, 2),
        "profile_fit": round(profile_fit, 2),
    }


def total_score(components: dict[str, float]) -> float:
    score = (
        0.30 * components["career_relevance"]
        + 0.20 * components["actionability"]
        + 0.15 * components["repo_quality"]
        + 0.15 * components["momentum"]
        + 0.10 * components["portfolio_value"]
        + 0.10 * components["profile_fit"]
    )
    return round(max(0.0, min(10.0, score)), 2)


def decision_for(score: float) -> str:
    if score >= 8.0:
        return "Build"
    if score >= 6.7:
        return "Study"
    if score >= 5.2:
        return "Save"
    return "Skip"


def action_for(profile: str, repo: Repository, skill_tags: list[str]) -> str:
    first_skill = skill_tags[0] if skill_tags else "repository evaluation"
    if profile == "data_analyst":
        return (
            f"Spend 30-60 minutes mapping {repo.name} to a small analytics case: "
            f"identify one dataset, one metric, and one dashboard or SQL output."
        )
    if profile == "data_scientist":
        return (
            f"Spend 30-60 minutes reviewing the model or experiment angle in {repo.name}; "
            f"write one reproducible experiment idea and one evaluation metric."
        )
    return (
        f"Spend 30-60 minutes checking whether {repo.name} solves a real workflow problem; "
        f"capture one use case, one setup risk, and one next action for {first_skill}."
    )


def expected_output_for(profile: str) -> str:
    if profile == "data_analyst":
        return "One-page analytics brief, metric definition, or dashboard sketch."
    if profile == "data_scientist":
        return "Experiment note with dataset, baseline, metric, and risk."
    return "Short decision note: use now, save for later, or skip."


def score_repository(repo: Repository, seen_before: bool, source_status: str) -> dict[str, Any]:
    skill_tags = infer_skill_tags(repo)
    scores: dict[str, dict[str, Any]] = {}
    for profile in PROFILES:
        components = component_scores(repo, profile)
        score = total_score(components)
        scores[profile] = {
            "label": PROFILE_LABELS[profile],
            "score": score,
            "decision": decision_for(score),
            "components": components,
            "action": action_for(profile, repo, skill_tags),
            "expected_output": expected_output_for(profile),
        }

    recommended_profile = max(PROFILES, key=lambda item: scores[item]["score"])
    recommended = scores[recommended_profile]
    return {
        **repo.to_dict(),
        "source_status": source_status,
        "seen_before": seen_before,
        "skill_tags": skill_tags,
        "scores": scores,
        "recommended_profile": recommended_profile,
        "recommended_profile_label": PROFILE_LABELS[recommended_profile],
        "recommended_score": recommended["score"],
        "recommended_decision": recommended["decision"],
        "recommended_action": recommended["action"],
        "expected_output": recommended["expected_output"],
        "why_it_matters": why_it_matters(repo, recommended_profile, skill_tags),
        "portfolio_idea": portfolio_idea(repo, recommended_profile),
        "evidence_limits": "README quality, install steps, and feature completeness are unverified.",
    }


def why_it_matters(repo: Repository, profile: str, skill_tags: list[str]) -> str:
    skill_text = ", ".join(skill_tags[:3])
    if profile == "data_analyst":
        return f"Relevant to analyst workflows through {skill_text}; useful for metrics, cleaning, or dashboard practice."
    if profile == "data_scientist":
        return f"Relevant to data science workflows through {skill_text}; useful for modeling, evaluation, or AI experimentation."
    return f"Potentially useful for general workflow improvement through {skill_text}."


def portfolio_idea(repo: Repository, profile: str) -> str:
    if profile == "data_analyst":
        return f"Build a mini case study using {repo.name}: problem, data cleaning, metric, dashboard, and decision note."
    if profile == "data_scientist":
        return f"Build a reproducible notebook around {repo.name}: baseline, experiment, evaluation, and limitations."
    return f"Create a practical usage review of {repo.name}: problem, setup, result, limitation, and recommendation."


def score_repositories(
    repositories: list[Repository], seen_repos: dict[str, Any], source_status: str
) -> list[dict[str, Any]]:
    cards = []
    for repo in repositories:
        key = repo.full_name.lower()
        cards.append(score_repository(repo, seen_before=key in seen_repos, source_status=source_status))
    cards.sort(key=lambda card: (card["recommended_score"], card["stars"], card["full_name"]), reverse=True)
    return cards


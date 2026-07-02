"""Configuration defaults and loaders for GitHub Insight."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - installable project includes PyYAML.
    yaml = None


MALAYSIA_TZ = timezone(timedelta(hours=8), name="Asia/Kuala_Lumpur")
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_QUERIES = [
    "topic:python topic:pandas",
    "topic:sql topic:data-analysis",
    "topic:data-engineering language:Python",
    "topic:dashboard topic:analytics",
    "topic:automation language:Python",
    "topic:machine-learning language:Python",
    "topic:visualization language:Python",
    "topic:etl language:Python",
]

DEFAULT_AUDIENCES = {
    "general_user": {"label": "General User", "keywords": ["tool", "automation", "app"]},
    "data_analyst": {"label": "Data Analyst", "keywords": ["sql", "dashboard", "analytics"]},
    "data_scientist": {"label": "Data Scientist", "keywords": ["machine-learning", "model", "benchmark"]},
}

DEFAULT_SCORING = {
    "overall_weights": {
        "usefulness_score": 0.20,
        "momentum_score": 0.20,
        "audience_fit_score": 0.15,
        "maintenance_score": 0.15,
        "readme_quality_score": 0.10,
        "reproducibility_score": 0.10,
        "data_asset_or_demo_score": 0.10,
        "risk_score": -0.15,
    }
}

DEFAULT_IMAGE_POLICY = {
    "enabled_default": False,
    "model_default": "gpt-image-2",
    "top_n_default": 3,
    "min_score_for_project_image": 80,
}


@dataclass(frozen=True)
class RuntimeConfig:
    """Backward-compatible settings used by the legacy script entry point."""

    date: str
    run_label: str
    fetch_live: bool
    strict_live: bool
    sample_mode: bool
    max_per_query: int
    queries: list[str]
    output_root: str
    generate_dashboard: bool
    generate_visuals: bool


@dataclass(frozen=True)
class AppConfig:
    audiences: dict[str, Any]
    queries: dict[str, list[str]]
    scoring: dict[str, Any]
    image_policy: dict[str, Any]
    github_token: str | None
    api_version: str
    timezone_name: str
    max_repos_per_audience: int
    max_repos_total: int
    max_details_per_run: int
    days_lookback: int
    enable_llm_summary: bool
    enable_image_generation: bool
    image_model: str
    image_top_n: int


def malaysia_now() -> datetime:
    """Return current time in Malaysia without depending on OS timezone data."""

    return datetime.now(MALAYSIA_TZ)


def default_date() -> str:
    return malaysia_now().date().isoformat()


def default_run_label() -> str:
    now = malaysia_now()
    if now.hour < 6:
        return "0000"
    if now.hour < 18:
        return "1200"
    return "manual"


def load_queries(raw_queries: str | None) -> list[str]:
    source = raw_queries or os.getenv("GITHUB_INSIGHT_QUERIES", "")
    if source.strip():
        return [item.strip() for item in source.split(";") if item.strip()]
    return DEFAULT_QUERIES


def load_max_per_query(value: int | None) -> int:
    if value is not None:
        return max(1, min(value, 30))
    env_value = os.getenv("GITHUB_MAX_REPOS_PER_QUERY")
    if env_value and env_value.isdigit():
        return max(1, min(int(env_value), 30))
    return 8


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if not raw or not raw.strip().isdigit():
        return default
    value = max(minimum, int(raw))
    if maximum is not None:
        value = min(value, maximum)
    return value


def resolve_github_token() -> str | None:
    return os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN") or None


def load_yaml_file(path: Path, default: Any) -> Any:
    if not path.exists() or yaml is None:
        return default
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or default
    return loaded


def load_app_config(root: Path | None = None) -> AppConfig:
    project_root = root or PROJECT_ROOT
    image_policy = load_yaml_file(project_root / "config" / "image_policy.yml", DEFAULT_IMAGE_POLICY)
    return AppConfig(
        audiences=load_yaml_file(project_root / "config" / "audiences.yml", DEFAULT_AUDIENCES),
        queries=load_yaml_file(project_root / "config" / "queries.yml", {"default": DEFAULT_QUERIES}),
        scoring=load_yaml_file(project_root / "config" / "scoring.yml", DEFAULT_SCORING),
        image_policy=image_policy,
        github_token=resolve_github_token(),
        api_version=os.getenv("GITHUB_API_VERSION", "2022-11-28"),
        timezone_name=os.getenv("TIMEZONE", "Asia/Kuala_Lumpur"),
        max_repos_per_audience=_env_int("MAX_REPOS_PER_AUDIENCE", 50, 1, 100),
        max_repos_total=_env_int("MAX_REPOS_TOTAL", 200, 1, 500),
        max_details_per_run=_env_int("MAX_DETAILS_PER_RUN", 80, 1, 200),
        days_lookback=_env_int("DAYS_LOOKBACK", 7, 1, 60),
        enable_llm_summary=_env_bool("ENABLE_LLM_SUMMARY", False),
        enable_image_generation=_env_bool("ENABLE_IMAGE_GENERATION", bool(image_policy.get("enabled_default", False))),
        image_model=os.getenv("IMAGE_MODEL", str(image_policy.get("model_default", "gpt-image-2"))),
        image_top_n=_env_int("IMAGE_TOP_N", int(image_policy.get("top_n_default", 3)), 0, 10),
    )

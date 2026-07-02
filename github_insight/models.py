"""Data models and normalization helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_text(value: Any, default: str = "unavailable") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_topics(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip().lower() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip().lower() for item in value if str(item).strip()]
    return []


@dataclass
class Repository:
    full_name: str
    name: str
    owner: str
    html_url: str
    description: str
    language: str
    topics: list[str] = field(default_factory=list)
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    created_at: str = "unavailable"
    updated_at: str = "unavailable"
    pushed_at: str = "unavailable"
    license: str = "unavailable"
    archived: bool = False
    source_query: str = "unavailable"
    collected_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def from_github_item(
        cls, item: dict[str, Any], source_query: str, collected_at: str
    ) -> "Repository":
        owner = item.get("owner") or {}
        license_info = item.get("license") or {}
        license_name = license_info.get("spdx_id") or license_info.get("name")
        return cls(
            full_name=safe_text(item.get("full_name")),
            name=safe_text(item.get("name")),
            owner=safe_text(owner.get("login")),
            html_url=safe_text(item.get("html_url")),
            description=safe_text(item.get("description")),
            language=safe_text(item.get("language")),
            topics=normalize_topics(item.get("topics")),
            stars=safe_int(item.get("stargazers_count")),
            forks=safe_int(item.get("forks_count")),
            open_issues=safe_int(item.get("open_issues_count")),
            created_at=safe_text(item.get("created_at")),
            updated_at=safe_text(item.get("updated_at")),
            pushed_at=safe_text(item.get("pushed_at")),
            license=safe_text(license_name),
            archived=bool(item.get("archived", False)),
            source_query=source_query,
            collected_at=collected_at,
        )

    @classmethod
    def from_mapping(cls, item: dict[str, Any], collected_at: str) -> "Repository":
        return cls(
            full_name=safe_text(item.get("full_name")),
            name=safe_text(item.get("name")),
            owner=safe_text(item.get("owner")),
            html_url=safe_text(item.get("html_url")),
            description=safe_text(item.get("description")),
            language=safe_text(item.get("language")),
            topics=normalize_topics(item.get("topics")),
            stars=safe_int(item.get("stars")),
            forks=safe_int(item.get("forks")),
            open_issues=safe_int(item.get("open_issues")),
            created_at=safe_text(item.get("created_at")),
            updated_at=safe_text(item.get("updated_at")),
            pushed_at=safe_text(item.get("pushed_at")),
            license=safe_text(item.get("license")),
            archived=bool(item.get("archived", False)),
            source_query=safe_text(item.get("source_query")),
            collected_at=safe_text(item.get("collected_at"), collected_at),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunMetadata:
    run_id: str
    date: str
    scheduled_for: str
    started_at: str
    generated_at: str
    completed_at: str
    timezone: str
    mode: str
    status: str
    github_rate_limit_remaining: int | None
    query_count: int
    repos_discovered: int
    repos_selected: int
    image_generation_enabled: bool
    llm_summary_enabled: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepositoryRaw:
    full_name: str
    owner: str
    name: str
    html_url: str
    api_url: str
    description: str
    created_at: str
    updated_at: str
    pushed_at: str
    stargazers_count: int
    forks_count: int
    watchers_count: int
    open_issues_count: int
    language: str
    topics: list[str]
    license_name: str
    license_spdx_id: str
    archived: bool
    disabled: bool
    fork: bool
    default_branch: str
    size: int
    homepage: str
    has_issues: bool
    has_projects: bool
    has_wiki: bool
    source_query: str
    source_audience: str
    source_audiences: list[str] = field(default_factory=list)
    source_queries: list[str] = field(default_factory=list)
    raw_json_path: str = ""

    @classmethod
    def from_github_item(cls, item: dict[str, Any], source_query: str, source_audience: str) -> "RepositoryRaw":
        owner = item.get("owner") or {}
        license_info = item.get("license") or {}
        return cls(
            full_name=safe_text(item.get("full_name")),
            owner=safe_text(owner.get("login")),
            name=safe_text(item.get("name")),
            html_url=safe_text(item.get("html_url")),
            api_url=safe_text(item.get("url")),
            description=safe_text(item.get("description")),
            created_at=safe_text(item.get("created_at")),
            updated_at=safe_text(item.get("updated_at")),
            pushed_at=safe_text(item.get("pushed_at")),
            stargazers_count=safe_int(item.get("stargazers_count")),
            forks_count=safe_int(item.get("forks_count")),
            watchers_count=safe_int(item.get("watchers_count")),
            open_issues_count=safe_int(item.get("open_issues_count")),
            language=safe_text(item.get("language")),
            topics=normalize_topics(item.get("topics")),
            license_name=safe_text(license_info.get("name")),
            license_spdx_id=safe_text(license_info.get("spdx_id")),
            archived=bool(item.get("archived", False)),
            disabled=bool(item.get("disabled", False)),
            fork=bool(item.get("fork", False)),
            default_branch=safe_text(item.get("default_branch")),
            size=safe_int(item.get("size")),
            homepage=safe_text(item.get("homepage")),
            has_issues=bool(item.get("has_issues", False)),
            has_projects=bool(item.get("has_projects", False)),
            has_wiki=bool(item.get("has_wiki", False)),
            source_query=source_query,
            source_audience=source_audience,
            source_audiences=[source_audience],
            source_queries=[source_query],
        )

    @classmethod
    def from_repository(cls, repo: Repository, source_audience: str = "mock") -> "RepositoryRaw":
        return cls(
            full_name=repo.full_name,
            owner=repo.owner,
            name=repo.name,
            html_url=repo.html_url,
            api_url="unavailable",
            description=repo.description,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            pushed_at=repo.pushed_at,
            stargazers_count=repo.stars,
            forks_count=repo.forks,
            watchers_count=repo.stars,
            open_issues_count=repo.open_issues,
            language=repo.language,
            topics=repo.topics,
            license_name=repo.license,
            license_spdx_id=repo.license,
            archived=repo.archived,
            disabled=False,
            fork=False,
            default_branch="unavailable",
            size=0,
            homepage="unavailable",
            has_issues=True,
            has_projects=False,
            has_wiki=False,
            source_query=repo.source_query,
            source_audience=source_audience,
            source_audiences=[source_audience],
            source_queries=[repo.source_query],
        )

    def merge_source(self, source_query: str, source_audience: str) -> None:
        if source_audience not in self.source_audiences:
            self.source_audiences.append(source_audience)
        if source_query not in self.source_queries:
            self.source_queries.append(source_query)
        self.source_query = self.source_queries[0]
        self.source_audience = self.source_audiences[0]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepositoryEnriched:
    raw: RepositoryRaw
    readme_text_excerpt: str
    readme_length: int
    readme_quality_score: float
    has_installation_instructions: bool
    has_usage_examples: bool
    has_demo_link: bool
    has_docs_link: bool
    has_notebook: bool
    has_dataset: bool
    has_csv_or_sql: bool
    has_dockerfile: bool
    has_requirements: bool
    has_environment_file: bool
    has_pyproject: bool
    has_package_file: bool
    has_release: bool
    latest_release_date: str
    language_breakdown: dict[str, int]
    commit_activity_signal: str
    issue_activity_signal: str
    reproducibility_signals: list[str]
    risk_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        raw = payload.pop("raw")
        raw.update(payload)
        return raw


@dataclass
class InsightRecord:
    date: str
    full_name: str
    html_url: str
    primary_audience: str
    audience_tags: list[str]
    general_user_score: float
    data_analyst_score: float
    data_scientist_score: float
    usefulness_score: float
    momentum_score: float
    reproducibility_score: float
    data_asset_score: float
    dashboard_readiness_score: float
    maintenance_score: float
    risk_score: float
    overall_insight_score: float
    difficulty_level: str
    recommended_action: str
    one_sentence_summary: str
    why_it_matters: str
    practical_use_cases: list[str]
    data_analyst_angle: str
    data_scientist_angle: str
    general_user_angle: str
    portfolio_project_idea: str
    evidence: list[str]
    risk_flags: list[str]
    image_asset_path: str
    image_prompt_path: str
    confidence: str
    language: str
    topics: list[str]
    stars: int
    forks: int
    open_issues: int
    license: str
    pushed_at: str
    first_seen_date: str
    last_seen_date: str
    days_seen: int
    rank_today: int | None
    rank_previous: int | None
    rank_change: int | None
    star_delta_since_previous_seen: int | None
    fork_delta_since_previous_seen: int | None
    source_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

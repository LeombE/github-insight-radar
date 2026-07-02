"""Repository collection orchestration for mock and live modes."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from github_insight.config import AppConfig, PROJECT_ROOT
from github_insight.github_client import GitHubApiError, GitHubClient
from github_insight.models import Repository, RepositoryEnriched, RepositoryRaw, utc_now_iso
from github_insight.readme_analyzer import analyze_readme, synthesize_mock_readme


SAMPLE_DATA = PROJECT_ROOT / "data" / "raw" / "sample_repositories.json"


def _replace_date_placeholder(query: str, days_lookback: int) -> str:
    target = (date.today() - timedelta(days=days_lookback)).isoformat()
    return query.replace("DATE_PLACEHOLDER", target)


def _source_audience_for_mock(repo: Repository) -> str:
    topics = set(repo.topics)
    if topics & {"machine-learning", "ml", "model", "benchmark"}:
        return "data_scientist"
    if topics & {"sql", "dashboard", "analytics", "etl", "data-cleaning"}:
        return "data_analyst"
    if topics & {"productivity", "cli", "automation", "workflow"}:
        return "general_user"
    return "general_user"


def _load_sample_raw() -> tuple[list[RepositoryRaw], dict[str, Any]]:
    with SAMPLE_DATA.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    raw_repos = []
    for item in payload.get("repositories", []):
        repo = Repository.from_mapping(item, collected_at="2026-07-02T00:00:00+00:00")
        raw_repos.append(RepositoryRaw.from_repository(repo, source_audience=_source_audience_for_mock(repo)))
    return raw_repos, {"mode": "mock", "source": str(SAMPLE_DATA), "repositories": payload.get("repositories", [])}


def collect_mock_repositories() -> tuple[list[RepositoryRaw], dict[str, Any], int | None, int]:
    raw, payload = _load_sample_raw()
    return raw, payload, None, 1


def collect_live_repositories(config: AppConfig) -> tuple[list[RepositoryRaw], dict[str, Any], int | None, int]:
    client = GitHubClient(token=config.github_token, api_version=config.api_version)
    repos: dict[str, RepositoryRaw] = {}
    raw_payload: dict[str, Any] = {"mode": "live", "queries": []}
    query_count = 0
    per_query = max(1, min(config.max_repos_per_audience, 30))

    for audience, queries in config.queries.items():
        if not isinstance(queries, list):
            continue
        for template in queries:
            if len(repos) >= config.max_repos_total:
                break
            query = _replace_date_placeholder(str(template), config.days_lookback)
            response = client.search_repositories(query, per_page=per_query)
            query_count += 1
            items = response.data.get("items", []) if isinstance(response.data, dict) else []
            raw_payload["queries"].append({"audience": audience, "query": query, "count": len(items)})
            for item in items:
                raw = RepositoryRaw.from_github_item(item, query, audience)
                if raw.full_name == "unavailable":
                    continue
                key = raw.full_name.lower()
                if key in repos:
                    repos[key].merge_source(query, audience)
                else:
                    repos[key] = raw
                if len(repos) >= config.max_repos_total:
                    break
        if len(repos) >= config.max_repos_total:
            break

    if not repos:
        raise GitHubApiError("Live GitHub collection returned zero repositories.")
    raw_payload["repository_count"] = len(repos)
    raw_payload["collected_at"] = utc_now_iso()
    return list(repos.values()), raw_payload, client.rate_limit_remaining, query_count


def enrich_repositories(repos: list[RepositoryRaw], config: AppConfig, mode: str) -> list[RepositoryEnriched]:
    client = None if mode == "mock" else GitHubClient(token=config.github_token, api_version=config.api_version)
    enriched: list[RepositoryEnriched] = []
    for index, repo in enumerate(repos):
        if mode == "mock":
            readme_text = synthesize_mock_readme(repo)
            languages = {repo.language: 1} if repo.language != "unavailable" else {}
            latest_release = "unavailable"
        else:
            if index >= config.max_details_per_run:
                readme_text = ""
                languages = {}
                latest_release = "unavailable"
            else:
                assert client is not None
                readme_text = client.readme_text(repo.full_name)
                languages = client.languages(repo.full_name)
                latest_release = client.latest_release_date(repo.full_name)
        signals = analyze_readme(readme_text, repo)
        enriched.append(
            RepositoryEnriched(
                raw=repo,
                readme_text_excerpt=str(signals["readme_text_excerpt"]),
                readme_length=int(signals["readme_length"]),
                readme_quality_score=float(signals["readme_quality_score"]),
                has_installation_instructions=bool(signals["has_installation_instructions"]),
                has_usage_examples=bool(signals["has_usage_examples"]),
                has_demo_link=bool(signals["has_demo_link"]),
                has_docs_link=bool(signals["has_docs_link"]),
                has_notebook=bool(signals["has_notebook"]),
                has_dataset=bool(signals["has_dataset"]),
                has_csv_or_sql=bool(signals["has_csv_or_sql"]),
                has_dockerfile=bool(signals["has_dockerfile"]),
                has_requirements=bool(signals["has_requirements"]),
                has_environment_file=bool(signals["has_environment_file"]),
                has_pyproject=bool(signals["has_pyproject"]),
                has_package_file=bool(signals["has_package_file"]),
                has_release=latest_release != "unavailable",
                latest_release_date=latest_release,
                language_breakdown=languages,
                commit_activity_signal="recent push metadata available" if repo.pushed_at != "unavailable" else "unverified",
                issue_activity_signal="open issue count metadata available",
                reproducibility_signals=list(signals["reproducibility_signals"]),
                risk_flags=list(signals["risk_flags"]),
            )
        )
    return enriched


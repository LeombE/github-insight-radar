"""Repository collection through the official GitHub Search API."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from github_insight.models import Repository, utc_now_iso


GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA = PACKAGE_ROOT / "data" / "raw" / "sample_repositories.json"


class FetchError(RuntimeError):
    """Raised when live GitHub collection fails."""


def _request_json(url: str, token: str | None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-insight-portfolio-system",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise FetchError(f"GitHub API HTTP {exc.code}: {body[:300]}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise FetchError(f"GitHub API request failed: {exc}") from exc


def fetch_live_repositories(
    queries: list[str], max_per_query: int, token: str | None = None
) -> list[Repository]:
    collected_at = utc_now_iso()
    repos: dict[str, Repository] = {}
    for index, query in enumerate(queries):
        params = {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": str(max_per_query),
        }
        url = f"{GITHUB_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        payload = _request_json(url, token)
        for item in payload.get("items", []):
            repo = Repository.from_github_item(item, query, collected_at)
            if repo.full_name != "unavailable":
                repos[repo.full_name.lower()] = repo
        if index < len(queries) - 1:
            time.sleep(0.7)
    return list(repos.values())


def load_sample_repositories() -> list[Repository]:
    collected_at = utc_now_iso()
    with SAMPLE_DATA.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [Repository.from_mapping(item, collected_at) for item in payload["repositories"]]


def collect_repositories(
    *,
    fetch_live: bool,
    sample_mode: bool,
    strict_live: bool,
    queries: list[str],
    max_per_query: int,
) -> tuple[list[Repository], str, str | None]:
    """Collect repositories and return repos, source status, and an error note."""

    if sample_mode or not fetch_live:
        return load_sample_repositories(), "sample_fixture", None

    token = os.getenv("GITHUB_TOKEN")
    try:
        repos = fetch_live_repositories(queries, max_per_query, token=token)
        if not repos:
            raise FetchError("GitHub API returned zero repositories")
        return repos, "live_github_api", None
    except FetchError as exc:
        if strict_live:
            raise
        return load_sample_repositories(), "fallback_sample_after_fetch_error", str(exc)


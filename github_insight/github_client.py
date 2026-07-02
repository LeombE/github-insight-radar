"""Small GitHub REST API client with retries and rate-limit awareness."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

import requests

from github_insight.logging_utils import redact_secrets


class GitHubApiError(RuntimeError):
    """Raised when live GitHub API collection cannot complete."""


@dataclass
class GitHubResponse:
    data: Any
    rate_limit_remaining: int | None
    etag: str | None = None


class GitHubClient:
    base_url = "https://api.github.com"

    def __init__(self, token: str | None = None, api_version: str = "2022-11-28", timeout: int = 30) -> None:
        self.token = token
        self.api_version = api_version
        self.timeout = timeout
        self.rate_limit_remaining: int | None = None
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "User-Agent": "github-insight-portfolio-system",
                "X-GitHub-Api-Version": api_version,
            }
        )
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, path_or_url: str, **kwargs: Any) -> GitHubResponse:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base_url}{path_or_url}"
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
                remaining = response.headers.get("x-ratelimit-remaining")
                self.rate_limit_remaining = int(remaining) if remaining and remaining.isdigit() else None
                if response.status_code in {403, 429, 500, 502, 503, 504} and attempt < 3:
                    wait = min(2 ** attempt, 8)
                    retry_after = response.headers.get("retry-after")
                    if retry_after and retry_after.isdigit():
                        wait = min(int(retry_after), 30)
                    time.sleep(wait)
                    continue
                if response.status_code >= 400:
                    raise GitHubApiError(
                        redact_secrets(f"GitHub API {response.status_code} for {url}: {response.text[:300]}")
                    )
                if response.status_code == 204:
                    data: Any = {}
                else:
                    data = response.json()
                return GitHubResponse(data=data, rate_limit_remaining=self.rate_limit_remaining, etag=response.headers.get("etag"))
            except (requests.RequestException, ValueError, GitHubApiError) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                break
        raise GitHubApiError(redact_secrets(last_error or "Unknown GitHub API error"))

    def search_repositories(self, query: str, per_page: int) -> GitHubResponse:
        return self.request(
            "GET",
            "/search/repositories",
            params={"q": query, "sort": "updated", "order": "desc", "per_page": per_page},
        )

    def repository(self, full_name: str) -> GitHubResponse:
        return self.request("GET", f"/repos/{full_name}")

    def readme_text(self, full_name: str) -> str:
        try:
            response = self.request("GET", f"/repos/{full_name}/readme")
        except GitHubApiError:
            return ""
        data = response.data
        if not isinstance(data, dict) or data.get("encoding") != "base64":
            return ""
        content = str(data.get("content", ""))
        try:
            return base64.b64decode(content, validate=False).decode("utf-8", errors="replace")
        except ValueError:
            return ""

    def languages(self, full_name: str) -> dict[str, int]:
        try:
            response = self.request("GET", f"/repos/{full_name}/languages")
        except GitHubApiError:
            return {}
        return response.data if isinstance(response.data, dict) else {}

    def latest_release_date(self, full_name: str) -> str:
        try:
            response = self.request("GET", f"/repos/{full_name}/releases", params={"per_page": 1})
        except GitHubApiError:
            return "unavailable"
        data = response.data
        if isinstance(data, list) and data:
            return str(data[0].get("published_at") or data[0].get("created_at") or "unavailable")
        return "unavailable"

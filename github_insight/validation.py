"""Validation checks for generated GitHub Insight artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path


SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
]


def required_paths(root: Path, date: str) -> list[Path]:
    return [
        root / "reports" / "daily" / f"{date}-daily-brief.md",
        root / "reports" / "daily" / f"{date}-general-user.md",
        root / "reports" / "daily" / f"{date}-data-analyst.md",
        root / "reports" / "daily" / f"{date}-data-scientist.md",
        root / "reports" / "daily" / f"{date}-action-list.md",
        root / "reports" / "latest" / "latest-daily-brief.md",
        root / "reports" / "latest" / "latest-projects.json",
        root / "data" / "raw" / f"{date}-github-api-raw.json",
        root / "data" / "processed" / f"{date}-github-insight-projects.csv",
        root / "data" / "processed" / f"{date}-github-insight-projects.json",
        root / "data" / "processed" / "github_repos_master.csv",
        root / "data" / "github_insight.sqlite",
        root / "docs" / "index.html",
        root / "docs" / "data" / "latest.json",
        root / "docs" / "data" / "archive_index.json",
    ]


def scan_for_secrets(root: Path) -> list[str]:
    findings: list[str] = []
    skip_parts = {".git", "__pycache__", ".venv", "venv"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip_parts for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".sqlite", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path.relative_to(root)))
                break
    return sorted(set(findings))


def _is_production_root(root: Path) -> bool:
    return (root / ".git").exists()


def _latest_mode(root: Path) -> str | None:
    latest_path = root / "docs" / "data" / "latest.json"
    if not latest_path.exists():
        return None
    try:
        payload = json.loads(latest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    mode = payload.get("run", {}).get("mode")
    return str(mode).strip().lower() if mode is not None else None


def production_mock_warning(root: Path, *, allow_mock_publish: bool = False) -> str | None:
    if allow_mock_publish or not _is_production_root(root):
        return None
    if _latest_mode(root) != "mock":
        return None
    return (
        "production docs/data/latest.json contains mock data while ALLOW_MOCK_PUBLISH is false. "
        "Do not commit or publish docs/index.html, docs/data/latest.json, or "
        "docs/data/archive_index.json until live production data is restored."
    )


def validate_outputs(
    root: Path,
    date: str,
    *,
    allow_mock_publish: bool = False,
    fail_on_mock_production: bool = False,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for path in required_paths(root, date):
        if not path.exists():
            errors.append(f"missing: {path.relative_to(root)}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty: {path.relative_to(root)}")
    warning = production_mock_warning(root, allow_mock_publish=allow_mock_publish)
    if warning and fail_on_mock_production:
        errors.append(warning)
    secret_hits = scan_for_secrets(root)
    if secret_hits:
        errors.append("possible committed secret pattern in: " + ", ".join(secret_hits))
    return not errors, errors
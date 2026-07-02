"""Validation checks for generated GitHub Insight artifacts."""

from __future__ import annotations

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


def validate_outputs(root: Path, date: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for path in required_paths(root, date):
        if not path.exists():
            errors.append(f"missing: {path.relative_to(root)}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty: {path.relative_to(root)}")
    secret_hits = scan_for_secrets(root)
    if secret_hits:
        errors.append("possible committed secret pattern in: " + ", ".join(secret_hits))
    return not errors, errors

"""Small shared utilities for GitHub Insight."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


MALAYSIA_TZ = timezone(timedelta(hours=8), name="Asia/Kuala_Lumpur")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def malaysia_now() -> datetime:
    return datetime.now(MALAYSIA_TZ).replace(microsecond=0)


def resolve_report_date(value: str | None) -> str:
    if not value or value == "today":
        return malaysia_now().date().isoformat()
    date.fromisoformat(value)
    return value


def resolve_week(value: str | None) -> str:
    if value:
        return value
    year, week, _ = malaysia_now().isocalendar()
    return f"{year}-W{week:02d}"


def lookback_date(days: int) -> str:
    return (malaysia_now().date() - timedelta(days=days)).isoformat()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().replace("/", "-"))
    slug = re.sub(r"-{2,}", "-", slug).strip("-._")
    return slug.lower() or "item"


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


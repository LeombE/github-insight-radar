"""Logging helpers that avoid leaking credentials."""

from __future__ import annotations

import logging
import re


TOKEN_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]+"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
]


def redact_secrets(text: object) -> str:
    value = str(text)
    for pattern in TOKEN_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return logging.getLogger(name)


"""Backward-compatible wrapper around the canonical package CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from github_insight.cli import main as canonical_main
from github_insight.cli import run_daily
from github_insight.config import default_date, default_run_label, load_max_per_query, load_queries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate GitHub Insight daily reports.")
    parser.add_argument("--date", default=default_date(), help="Report date in YYYY-MM-DD format.")
    parser.add_argument("--run-label", default=default_run_label(), help="Legacy run label retained for compatibility.")
    parser.add_argument("--fetch", action="store_true", help="Fetch live data from the official GitHub Search API.")
    parser.add_argument("--sample", action="store_true", help="Use the bundled deterministic mock fixture.")
    parser.add_argument("--strict-live", action="store_true", help="Legacy flag; live mode now fails instead of falling back.")
    parser.add_argument("--max-per-query", type=int, default=None, help="Legacy flag retained for compatibility.")
    parser.add_argument("--queries", default=None, help="Legacy flag retained for compatibility.")
    parser.add_argument("--output-root", default=".", help="Output root directory.")
    parser.add_argument("--no-dashboard", action="store_true", help="Legacy flag ignored by the canonical run.")
    parser.add_argument("--no-visuals", action="store_true", help="Legacy flag ignored by the canonical run.")
    return parser


def run_pipeline(args: argparse.Namespace) -> list[Path]:
    canonical_args = argparse.Namespace(
        output_root=args.output_root,
        date=args.date,
        mock=bool(args.sample or not args.fetch),
        limit=0,
        no_validate=False,
    )
    _ = load_queries(args.queries)
    _ = load_max_per_query(args.max_per_query)
    return run_daily(canonical_args)


def main(argv: list[str] | None = None) -> int:
    if argv and argv[:1] in (["run"], ["dashboard"], ["weekly"], ["init-db"], ["validate"]):
        return canonical_main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    generated = run_pipeline(args)
    print("Generated files:")
    for path in generated:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

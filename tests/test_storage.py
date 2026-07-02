import sqlite3

from github_insight.cli import main


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def test_storage_creates_sqlite_tables(tmp_path):
    assert main(["--output-root", str(tmp_path), "run", "--mock", "--date", "2026-07-02"]) == 0
    db_path = tmp_path / PREVIEW_ROOT / "data" / "github_insight.sqlite"
    with sqlite3.connect(db_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"daily_runs", "repo_snapshots", "repo_enriched", "insight_records", "visual_assets"}.issubset(tables)
from github_insight.quality import run_quality_checks
from scripts.github_insight import build_parser, run_pipeline


def test_quality_report_passes_for_sample_run(tmp_path):
    parser = build_parser()
    args = parser.parse_args(
        [
            "--sample",
            "--date",
            "2026-07-02",
            "--run-label",
            "manual",
            "--output-root",
            str(tmp_path),
        ]
    )
    run_pipeline(args)
    quality_path = tmp_path / "docs" / "reviews" / "2026-07-02-quality-gate-result.md"
    assert "Overall status: PASS" in quality_path.read_text(encoding="utf-8")


def test_quality_detects_empty_cards():
    checks = run_quality_checks([], [], {"date": "2026-07-02", "run_label": "manual", "source_status": "test"})
    assert any(not check.passed for check in checks)

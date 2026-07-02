from scripts.github_insight import build_parser, run_pipeline


PREVIEW_ROOT = ".pytest-tmp/mock-run"


def test_sample_pipeline_generates_required_outputs(tmp_path):
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
    generated = run_pipeline(args)
    preview = tmp_path / PREVIEW_ROOT

    assert generated
    assert (preview / "reports" / "daily" / "2026-07-02-daily-brief.md").exists()
    assert (preview / "reports" / "daily" / "2026-07-02-general-user.md").exists()
    assert (preview / "reports" / "daily" / "2026-07-02-data-analyst.md").exists()
    assert (preview / "reports" / "daily" / "2026-07-02-data-scientist.md").exists()
    assert (preview / "reports" / "daily" / "2026-07-02-action-list.md").exists()
    assert (preview / "data" / "processed" / "github_repos_master.csv").exists()
    assert (preview / "data" / "processed" / "github_insight_cards.json").exists()
    assert (preview / "dashboard" / "index.html").exists()
    assert (preview / "docs" / "index.html").exists()
    assert (preview / "docs" / "reviews" / "2026-07-02-quality-gate-result.md").exists()
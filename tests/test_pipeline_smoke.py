from scripts.github_insight import build_parser, run_pipeline


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

    assert generated
    assert (tmp_path / "reports" / "daily" / "2026-07-02-daily-brief.md").exists()
    assert (tmp_path / "reports" / "daily" / "2026-07-02-general-user.md").exists()
    assert (tmp_path / "reports" / "daily" / "2026-07-02-data-analyst.md").exists()
    assert (tmp_path / "reports" / "daily" / "2026-07-02-data-scientist.md").exists()
    assert (tmp_path / "reports" / "daily" / "2026-07-02-action-list.md").exists()
    assert (tmp_path / "data" / "processed" / "github_repos_master.csv").exists()
    assert (tmp_path / "data" / "processed" / "github_insight_cards.json").exists()
    assert (tmp_path / "dashboard" / "index.html").exists()
    assert (tmp_path / "docs" / "index.html").exists()
    assert (tmp_path / "docs" / "reviews" / "2026-07-02-quality-gate-result.md").exists()


from github_insight.classifier import build_insights
from github_insight.collectors import collect_mock_repositories, enrich_repositories
from github_insight.config import load_app_config


def test_classifier_scores_and_tags_mock_repos(tmp_path):
    config = load_app_config()
    raw, _, _, _ = collect_mock_repositories()
    enriched = enrich_repositories(raw, config, mode="mock")
    records = build_insights(enriched, "2026-07-02", {}, "mock_fixture")
    assert records
    assert all(0 <= record.overall_insight_score <= 100 for record in records)
    assert any(record.primary_audience == "data_analyst" for record in records)
    assert any(record.primary_audience == "data_scientist" for record in records)
    assert all(record.recommended_action for record in records)


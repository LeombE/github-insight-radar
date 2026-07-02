import unittest

from github_insight.models import Repository
from github_insight.scoring import score_repository


class ScoringTests(unittest.TestCase):
    def test_profile_scores_reflect_keywords(self):
        repo = Repository(
            full_name="example/sql-dashboard",
            name="sql-dashboard",
            owner="example",
            html_url="https://github.com/example/sql-dashboard",
            description="SQL analytics dashboard with pandas data cleaning",
            language="Python",
            topics=["sql", "analytics", "dashboard", "pandas"],
            stars=1000,
            forks=120,
            pushed_at="2026-06-30T00:00:00Z",
            updated_at="2026-06-30T00:00:00Z",
            license="MIT",
        )
        card = score_repository(repo, seen_before=False, source_status="test")

        self.assertGreater(card["scores"]["data_analyst"]["score"], 5)
        self.assertIn("Dashboarding", card["skill_tags"])
        self.assertIn(card["recommended_decision"], {"Build", "Study", "Save", "Skip"})


if __name__ == "__main__":
    unittest.main()


from unittest.mock import patch

from src.scorer import SCORE_THRESHOLD, score_job


def _score(title: str, description: str = "") -> int:
    job = {"id": "x", "title": title, "url": "https://example.com", "company": "Test"}
    with patch("src.scorer._fetch_description", return_value=description):
        with patch("src.scorer.time.sleep"):
            return score_job(job)["score"]


class TestScoreJob:
    def test_senior_role_above_threshold(self):
        assert _score("Senior Data Scientist") >= SCORE_THRESHOLD

    def test_junior_role_below_threshold(self):
        assert _score("Junior Data Analyst") < SCORE_THRESHOLD

    def test_domain_keywords_boost_score(self):
        plain = _score("Data Scientist", "")
        rich = _score("Data Scientist", "python databricks fintech churn propensity london")
        assert rich > plain

    def test_score_clamped_to_1_10(self):
        s = _score("Junior Intern Apprentice", "")
        assert 1 <= s <= 10

    def test_senior_plus_domain_is_high(self):
        s = _score("Senior Data Scientist", "python databricks banking churn london")
        assert s >= 7

    def test_adds_score_keywords(self):
        job = {"id": "x", "title": "Lead DS", "url": "https://x.com", "company": "Co"}
        with patch("src.scorer._fetch_description", return_value="python churn fintech london"):
            with patch("src.scorer.time.sleep"):
                result = score_job(job)
        assert len(result["score_keywords"]) > 0

    def test_stores_description(self):
        job = {"id": "x", "title": "Senior DS", "url": "https://x.com", "company": "Co"}
        with patch("src.scorer._fetch_description", return_value="some description"):
            with patch("src.scorer.time.sleep"):
                result = score_job(job)
        assert result["description"] == "some description"

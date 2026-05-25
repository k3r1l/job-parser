from src.notifier import (
    format_company_snapshot,
    format_daily_summary,
    format_fetch_errors,
    format_new_jobs,
    format_removed_jobs,
)


class TestFormatNewJobs:
    def test_contains_company_and_count(self):
        jobs = [{"title": "Senior DS", "url": "https://example.com", "score": 8, "score_keywords": ["python"]}]
        msg = format_new_jobs("Monzo", jobs)
        assert "Monzo" in msg
        assert "1" in msg

    def test_shows_score_and_keywords(self):
        jobs = [{"title": "Lead ML", "url": "https://x.com", "score": 9, "score_keywords": ["churn", "python"]}]
        msg = format_new_jobs("Revolut", jobs)
        assert "9/10" in msg
        assert "churn" in msg

    def test_sorted_by_score_descending(self):
        jobs = [
            {"title": "Low", "url": "https://x.com/1", "score": 5, "score_keywords": []},
            {"title": "High", "url": "https://x.com/2", "score": 9, "score_keywords": []},
        ]
        msg = format_new_jobs("Co", jobs)
        assert msg.index("9/10") < msg.index("5/10")

    def test_no_score_renders_without_error(self):
        jobs = [{"title": "DS Role", "url": "https://x.com"}]
        msg = format_new_jobs("Co", jobs)
        assert "DS Role" in msg


class TestFormatRemovedJobs:
    def test_contains_company_and_title(self):
        jobs = [{"title": "Lead ML", "url": "https://x.com", "first_seen": "2026-05-01"}]
        msg = format_removed_jobs("Monzo", jobs)
        assert "Monzo" in msg
        assert "Lead ML" in msg
        assert "2026-05-01" in msg


class TestFormatDailySummary:
    def test_no_changes(self):
        assert "no changes" in format_daily_summary(0, 0)

    def test_new_only(self):
        msg = format_daily_summary(3, 0)
        assert "3" in msg
        assert "new" in msg

    def test_removed_only(self):
        msg = format_daily_summary(0, 2)
        assert "2" in msg
        assert "removed" in msg

    def test_both(self):
        msg = format_daily_summary(3, 2)
        assert "3" in msg
        assert "2" in msg


class TestFormatFetchErrors:
    def test_lists_companies(self):
        msg = format_fetch_errors(["Monzo", "Klarna"])
        assert "Monzo" in msg
        assert "Klarna" in msg
        assert "companies.yml" in msg


class TestFormatCompanySnapshot:
    def _stored(self, active_by_company: dict) -> dict:
        stored = {}
        for company, count in active_by_company.items():
            stored[company] = {
                f"id{i}": {"status": "active"} for i in range(count)
            }
        return stored

    def test_shows_company_and_count(self):
        msg = format_company_snapshot(self._stored({"Monzo": 3, "Wise": 7}))
        assert "Monzo: 3" in msg
        assert "Wise: 7" in msg

    def test_sorted_descending(self):
        msg = format_company_snapshot(self._stored({"Monzo": 2, "Wise": 10, "Revolut": 5}))
        assert msg.index("Wise") < msg.index("Revolut") < msg.index("Monzo")

    def test_shows_total(self):
        msg = format_company_snapshot(self._stored({"Monzo": 3, "Wise": 7}))
        assert "10" in msg

    def test_excludes_companies_with_zero_active(self):
        stored = self._stored({"Monzo": 3})
        stored["DeadCo"] = {"id0": {"status": "removed"}}
        msg = format_company_snapshot(stored)
        assert "DeadCo" not in msg

    def test_empty_storage(self):
        msg = format_company_snapshot({})
        assert "No active" in msg

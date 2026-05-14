from src.storage import find_new_jobs, find_removed_jobs, update_jobs

_JOB = {"id": "abc", "title": "Senior DS", "url": "https://example.com", "location": "London",
        "description": "", "score": 8, "score_keywords": []}
_STORED_ACTIVE = {"TestCo": {"abc": {**_JOB, "status": "active", "first_seen": "2026-01-01", "last_seen": "2026-01-01"}}}
_STORED_REMOVED = {"TestCo": {"abc": {**_JOB, "status": "removed", "first_seen": "2026-01-01", "last_seen": "2026-01-01"}}}


class TestFindNewJobs:
    def test_empty_store_returns_all(self):
        assert find_new_jobs("TestCo", [_JOB], {}) == [_JOB]

    def test_already_seen_returns_empty(self):
        assert find_new_jobs("TestCo", [_JOB], _STORED_ACTIVE) == []

    def test_different_company_returns_all(self):
        assert find_new_jobs("OtherCo", [_JOB], _STORED_ACTIVE) == [_JOB]

    def test_mixed_new_and_seen(self):
        new_job = {**_JOB, "id": "xyz"}
        result = find_new_jobs("TestCo", [_JOB, new_job], _STORED_ACTIVE)
        assert result == [new_job]


class TestFindRemovedJobs:
    def test_missing_from_crawl_is_removed(self):
        result = find_removed_jobs("TestCo", [], _STORED_ACTIVE)
        assert len(result) == 1
        assert result[0]["id"] == "abc"

    def test_already_removed_not_returned_again(self):
        assert find_removed_jobs("TestCo", [], _STORED_REMOVED) == []

    def test_still_present_not_removed(self):
        assert find_removed_jobs("TestCo", [_JOB], _STORED_ACTIVE) == []

    def test_empty_store_returns_empty(self):
        assert find_removed_jobs("TestCo", [], {}) == []


class TestUpdateJobs:
    def test_adds_new_job(self):
        result = update_jobs("TestCo", [_JOB], [_JOB], [], {})
        assert "abc" in result["TestCo"]
        assert result["TestCo"]["abc"]["status"] == "active"
        assert result["TestCo"]["abc"]["score"] == 8

    def test_marks_removed(self):
        import copy
        stored = copy.deepcopy(_STORED_ACTIVE)
        result = update_jobs("TestCo", [], [], [_STORED_ACTIVE["TestCo"]["abc"]], stored)
        assert result["TestCo"]["abc"]["status"] == "removed"
        assert "removed_date" in result["TestCo"]["abc"]

    def test_updates_last_seen_for_existing(self):
        import copy
        stored = copy.deepcopy(_STORED_ACTIVE)
        stored["TestCo"]["abc"]["last_seen"] = "2026-01-01"
        result = update_jobs("TestCo", [_JOB], [], [], stored)
        assert result["TestCo"]["abc"]["last_seen"] != "2026-01-01"

    def test_preserves_first_seen(self):
        import copy
        stored = copy.deepcopy(_STORED_ACTIVE)
        result = update_jobs("TestCo", [_JOB], [], [], stored)
        assert result["TestCo"]["abc"]["first_seen"] == "2026-01-01"

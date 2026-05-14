from unittest.mock import MagicMock, call, patch

import pytest
import requests
from bs4 import BeautifulSoup

from src.parsers.base import fetch_page, parse_generic


def _mock_response(html: str) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status = MagicMock()
    return resp


class TestFetchPage:
    def test_returns_soup_on_success(self):
        resp = _mock_response("<html><body><p>OK</p></body></html>")
        with patch("requests.get", return_value=resp):
            result = fetch_page("https://example.com", "Test")
        assert result is not None
        assert result.find("p").text == "OK"

    def test_retries_on_failure_then_succeeds(self):
        resp = _mock_response("<html><body>OK</body></html>")
        with patch("requests.get", side_effect=[requests.RequestException("timeout"), resp]):
            with patch("time.sleep") as mock_sleep:
                result = fetch_page("https://example.com", "Test", retries=2)
        assert result is not None
        assert mock_sleep.call_count == 1

    def test_returns_none_after_all_retries_exhausted(self):
        with patch("requests.get", side_effect=requests.RequestException("timeout")):
            with patch("time.sleep"):
                result = fetch_page("https://example.com", "Test", retries=3)
        assert result is None

    def test_correct_number_of_attempts(self):
        with patch("requests.get", side_effect=requests.RequestException("err")) as mock_get:
            with patch("time.sleep"):
                fetch_page("https://example.com", "Test", retries=3)
        assert mock_get.call_count == 3

    def test_no_retry_on_retries_equals_1(self):
        with patch("requests.get", side_effect=requests.RequestException("err")) as mock_get:
            with patch("time.sleep") as mock_sleep:
                fetch_page("https://example.com", "Test", retries=1)
        assert mock_get.call_count == 1
        mock_sleep.assert_not_called()


class TestParseGeneric:
    def test_returns_matching_jobs(self):
        html = '<a href="/jobs/senior-data-scientist">Senior Data Scientist - London</a>'
        soup = BeautifulSoup(html, "lxml")
        with patch("src.parsers.base.fetch_page", return_value=soup):
            jobs, ok = parse_generic("TestCo", "https://testco.com/careers")
        assert ok is True
        assert len(jobs) == 1
        assert jobs[0].title == "Senior Data Scientist - London"
        assert jobs[0].company == "TestCo"

    def test_filters_irrelevant_jobs(self):
        html = '<a href="/jobs/pm">Product Manager</a>'
        soup = BeautifulSoup(html, "lxml")
        with patch("src.parsers.base.fetch_page", return_value=soup):
            jobs, ok = parse_generic("TestCo", "https://testco.com/careers")
        assert ok is True
        assert jobs == []

    def test_returns_fetch_failed_on_none(self):
        with patch("src.parsers.base.fetch_page", return_value=None):
            jobs, ok = parse_generic("TestCo", "https://testco.com/careers")
        assert ok is False
        assert jobs == []

    def test_deduplicates_urls(self):
        html = (
            '<a href="/jobs/senior-data-scientist">Senior Data Scientist</a>'
            '<a href="/jobs/senior-data-scientist">Senior Data Scientist</a>'
        )
        soup = BeautifulSoup(html, "lxml")
        with patch("src.parsers.base.fetch_page", return_value=soup):
            jobs, _ = parse_generic("TestCo", "https://testco.com")
        assert len(jobs) == 1

    def test_resolves_relative_urls(self):
        html = '<a href="/jobs/lead-data-scientist">Lead Data Scientist</a>'
        soup = BeautifulSoup(html, "lxml")
        with patch("src.parsers.base.fetch_page", return_value=soup):
            jobs, _ = parse_generic("TestCo", "https://testco.com/careers")
        assert jobs[0].url.startswith("https://testco.com")


class TestPagination:
    def test_fetches_multiple_pages(self):
        page1 = BeautifulSoup('<a href="/j/senior-data-scientist-p1">Senior Data Scientist P1</a>', "lxml")
        page2 = BeautifulSoup('<a href="/j/lead-data-scientist-p2">Lead Data Scientist P2</a>', "lxml")
        empty = BeautifulSoup("", "lxml")
        with patch("src.parsers.base.fetch_page", side_effect=[page1, page2, empty]):
            with patch("src.parsers.base.time.sleep"):
                jobs, ok = parse_generic("TestCo", "https://testco.com/jobs", max_pages=5)
        assert ok is True
        assert len(jobs) == 2

    def test_stops_at_empty_page(self):
        page1 = BeautifulSoup('<a href="/j/senior-data-scientist">Senior Data Scientist</a>', "lxml")
        empty = BeautifulSoup("", "lxml")
        with patch("src.parsers.base.fetch_page", side_effect=[page1, empty]) as mock_fetch:
            with patch("src.parsers.base.time.sleep"):
                jobs, _ = parse_generic("TestCo", "https://testco.com/jobs", max_pages=10)
        assert mock_fetch.call_count == 2  # stopped after empty page 2

    def test_page_url_appends_correctly(self):
        # page 1 has a non-relevant link (so scraper continues), page 2 is empty
        nonjob = BeautifulSoup('<a href="/about">About us</a>', "lxml")
        empty = BeautifulSoup("", "lxml")
        with patch("src.parsers.base.fetch_page", side_effect=[nonjob, empty]) as mock_fetch:
            with patch("src.parsers.base.time.sleep"):
                parse_generic("TestCo", "https://testco.com/jobs", max_pages=3)
        called_urls = [call[0][0] for call in mock_fetch.call_args_list]
        assert called_urls[0] == "https://testco.com/jobs"
        assert called_urls[1] == "https://testco.com/jobs?page=2"

    def test_page_url_with_existing_params(self):
        nonjob = BeautifulSoup('<a href="/about">About us</a>', "lxml")
        empty = BeautifulSoup("", "lxml")
        with patch("src.parsers.base.fetch_page", side_effect=[nonjob, empty]) as mock_fetch:
            with patch("src.parsers.base.time.sleep"):
                parse_generic("TestCo", "https://testco.com/jobs?team=data", max_pages=2)
        called_urls = [call[0][0] for call in mock_fetch.call_args_list]
        assert called_urls[1] == "https://testco.com/jobs?team=data&page=2"

    def test_stops_when_page_fingerprint_repeats(self):
        # Same HTML on page 1 and page 2 — site ignores ?page=N
        same = BeautifulSoup('<a href="/j/senior-data-scientist">Senior Data Scientist</a>', "lxml")
        with patch("src.parsers.base.fetch_page", side_effect=[same, same, same]) as mock_fetch:
            with patch("src.parsers.base.time.sleep"):
                jobs, ok = parse_generic("TestCo", "https://testco.com/jobs", max_pages=10)
        assert ok is True
        assert mock_fetch.call_count == 2  # fetched page 1 + page 2 (duplicate), then stopped
        assert len(jobs) == 1  # job from page 1 counted once

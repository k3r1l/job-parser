import hashlib
import logging
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.filters import is_relevant_title

logger = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; job-parser/1.0; +https://github.com)"}
_RETRY_DELAYS = (2, 4)  # seconds between successive attempts


@dataclass
class Job:
    title: str
    url: str
    company: str
    location: str = ""

    @property
    def id(self) -> str:
        return hashlib.md5(f"{self.company}::{self.url}".encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "company": self.company,
            "location": self.location,
        }


def fetch_page(url: str, company: str, retries: int = 3) -> BeautifulSoup | None:
    """
    Fetch a page with up to `retries` attempts and exponential backoff.
    Returns None (and logs an error) only after all attempts are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries - 1:
                delay = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)]
                logger.warning(
                    "Attempt %d/%d failed for %s: %s — retrying in %ds",
                    attempt + 1, retries, company, exc, delay,
                )
                time.sleep(delay)

    logger.error("All %d attempts failed for %s (%s): %s", retries, company, url, last_exc)
    return None


def parse_generic(company: str, url: str) -> tuple[list[Job], bool]:
    """
    Fallback scraper: walks all <a> tags and returns those matching the DS/ML
    keyword list. Returns (jobs, fetch_succeeded).
    """
    soup = fetch_page(url, company)
    if soup is None:
        return [], False

    jobs: list[Job] = []
    seen_urls: set[str] = set()

    for tag in soup.find_all("a", href=True):
        text = tag.get_text(" ", strip=True)
        href = tag["href"]

        if not text or len(text) < 5:
            continue

        if not href.startswith("http"):
            href = urljoin(url, href)

        if href in seen_urls:
            continue

        if is_relevant_title(text):
            jobs.append(Job(title=text, url=href, company=company))
            seen_urls.add(href)

    logger.info("%s — generic parser found %d relevant job(s)", company, len(jobs))
    return jobs, True

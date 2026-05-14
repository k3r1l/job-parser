import hashlib
import logging
import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from src.filters import is_relevant_title, is_uk_relevant

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


def _page_fingerprint(soup: BeautifulSoup) -> str:
    """MD5 of the sorted set of all hrefs — detects pages that ignore ?page=N."""
    hrefs = sorted({tag["href"] for tag in soup.find_all("a", href=True)})
    return hashlib.md5("\n".join(hrefs).encode()).hexdigest()


_MAX_PAGES_CEILING = 25  # safety cap — fingerprint/empty-page detection stops earlier in practice


def parse_generic(company: str, url: str, max_pages: int = _MAX_PAGES_CEILING) -> tuple[list[Job], bool]:
    """
    Fallback scraper: walks all <a> tags and returns those matching the DS/ML
    keyword list. Returns (jobs, fetch_succeeded).

    Stops early when:
    - a page has no links at all (past the last real page), or
    - a page's link fingerprint matches the previous page (pagination ignored).
    max_pages is a safety ceiling only — tune it upward if a board genuinely
    has more pages, but don't set it low to control scraping depth.
    """
    jobs: list[Job] = []
    seen_urls: set[str] = set()
    prev_fingerprint: str | None = None

    for page in range(1, max_pages + 1):
        sep = "&" if "?" in url else "?"
        page_url = url if page == 1 else f"{url}{sep}page={page}"

        soup = fetch_page(page_url, company)
        if soup is None:
            return ([], False) if page == 1 else (jobs, True)

        fingerprint = _page_fingerprint(soup)
        if page > 1 and fingerprint == prev_fingerprint:
            logger.info("%s — page %d has same content as previous page, stopping", company, page)
            break
        prev_fingerprint = fingerprint

        links_on_page = 0
        for tag in soup.find_all("a", href=True):
            text = tag.get_text(" ", strip=True)
            href = tag["href"]

            if not text or len(text) < 5:
                continue

            if not href.startswith("http"):
                href = urljoin(url, href)

            if href in seen_urls:
                continue

            links_on_page += 1
            if is_relevant_title(text) and is_uk_relevant(text):
                jobs.append(Job(title=text, url=href, company=company))
                seen_urls.add(href)

        logger.info(
            "%s — page %d/%d: %d link(s), %d relevant so far",
            company, page, max_pages, links_on_page, len(jobs),
        )

        if links_on_page == 0:
            break  # past the last page

        if page < max_pages:
            time.sleep(1.0)  # polite delay between pages of the same site

    return jobs, True

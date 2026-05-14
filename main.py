import logging
import time
from pathlib import Path

import yaml

from src.notifier import (
    format_daily_summary,
    format_fetch_errors,
    format_new_jobs,
    format_removed_jobs,
    send_message,
)
from src.parsers.base import parse_generic
from src.reporter import generate_report
from src.scorer import SCORE_THRESHOLD, score_job
from src.storage import find_new_jobs, find_removed_jobs, load_jobs, save_jobs, update_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

COMPANIES_FILE = Path(__file__).parent / "companies.yml"
BETWEEN_COMPANIES_DELAY = 1.5  # seconds between company fetches — stay polite


def load_companies() -> list[dict]:
    with open(COMPANIES_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("companies") or []


def run() -> None:
    companies = load_companies()
    if not companies:
        logger.warning("No companies configured in companies.yml — nothing to do.")
        return

    stored = load_jobs()
    total_new = 0
    total_removed = 0
    fetch_failed: list[str] = []

    for i, cfg in enumerate(companies):
        name: str = cfg["name"]
        url: str = cfg["url"]
        logger.info("Checking %s ...", name)

        if i > 0:
            time.sleep(BETWEEN_COMPANIES_DELAY)

        max_pages: int = cfg.get("max_pages", 1)
        jobs, fetch_ok = parse_generic(name, url, max_pages=max_pages)
        if not fetch_ok:
            fetch_failed.append(name)
            logger.warning("Skipping %s — page unreachable after all retries", name)
            continue

        job_dicts = [j.to_dict() for j in jobs]
        new = find_new_jobs(name, job_dicts, stored)
        removed = find_removed_jobs(name, job_dicts, stored)

        scored_new = [score_job(j) for j in new]

        notifiable = [j for j in scored_new if (j.get("score") or 0) >= SCORE_THRESHOLD]
        filtered = len(scored_new) - len(notifiable)
        logger.info(
            "  new=%d (notifiable=%d, filtered=%d)  removed=%d",
            len(new), len(notifiable), filtered, len(removed),
        )

        if notifiable:
            send_message(format_new_jobs(name, notifiable))
            total_new += len(notifiable)

        if removed:
            send_message(format_removed_jobs(name, removed))
            total_removed += len(removed)

        stored = update_jobs(name, job_dicts, scored_new, removed, stored)

    save_jobs(stored)
    generate_report(stored)

    if fetch_failed:
        logger.warning("Fetch failures: %s", fetch_failed)
        send_message(format_fetch_errors(fetch_failed))

    send_message(format_daily_summary(total_new, total_removed))
    logger.info("Done. new=%d removed=%d failed=%d", total_new, total_removed, len(fetch_failed))


if __name__ == "__main__":
    run()

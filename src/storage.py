import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

STORAGE_PATH = Path(__file__).parent.parent / "data" / "jobs.json"
_TODAY = date.today().isoformat()


def load_jobs() -> dict:
    if not STORAGE_PATH.exists():
        return {}
    with open(STORAGE_PATH) as f:
        return json.load(f)


def save_jobs(jobs: dict) -> None:
    STORAGE_PATH.parent.mkdir(exist_ok=True)
    with open(STORAGE_PATH, "w") as f:
        json.dump(jobs, f, indent=2, sort_keys=True)
    logger.debug("Saved jobs to %s", STORAGE_PATH)


def find_new_jobs(company: str, current_jobs: list[dict], stored: dict) -> list[dict]:
    """Return jobs not yet recorded for this company."""
    seen_ids = set(stored.get(company, {}).keys())
    return [j for j in current_jobs if j["id"] not in seen_ids]


def find_removed_jobs(company: str, current_jobs: list[dict], stored: dict) -> list[dict]:
    """Return previously active jobs absent from the current crawl."""
    current_ids = {j["id"] for j in current_jobs}
    return [
        record
        for job_id, record in stored.get(company, {}).items()
        if record.get("status") == "active" and job_id not in current_ids
    ]


def update_jobs(
    company: str,
    current_jobs: list[dict],
    scored_new: list[dict],
    removed_jobs: list[dict],
    stored: dict,
) -> dict:
    """Persist current crawl results into the stored jobs dict."""
    if company not in stored:
        stored[company] = {}

    scored_by_id = {j["id"]: j for j in scored_new}

    for job in current_jobs:
        job_id = job["id"]
        if job_id not in stored[company]:
            src = scored_by_id.get(job_id, job)
            stored[company][job_id] = {
                "id": job_id,
                "title": src.get("title", ""),
                "url": src.get("url", ""),
                "company": company,
                "location": src.get("location", ""),
                "description": src.get("description", ""),
                "score": src.get("score"),
                "score_keywords": src.get("score_keywords", []),
                "first_seen": _TODAY,
                "last_seen": _TODAY,
                "status": "active",
            }
        else:
            stored[company][job_id]["last_seen"] = _TODAY
            stored[company][job_id]["status"] = "active"

    for job in removed_jobs:
        job_id = job["id"]
        if job_id in stored[company]:
            stored[company][job_id]["status"] = "removed"
            stored[company][job_id]["removed_date"] = _TODAY

    return stored

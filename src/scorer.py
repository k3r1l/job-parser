import logging
import time

from src.filters import is_uk_relevant
from src.parsers.base import fetch_page

_DESCRIPTION_FETCH_DELAY = 0.5  # seconds between job detail page requests

logger = logging.getLogger(__name__)

# Seniority signals checked against job title
_SENIORITY_POSITIVE = {
    "senior", "lead", "principal", "head of", "staff", "director", "manager",
}
_SENIORITY_NEGATIVE = {
    "junior", "graduate", "intern", "entry level", "entry-level",
    "associate", "trainee", "apprentice",
}

# Domain keywords from CV — high-value matches
_DOMAIN_KEYWORDS = [
    # Role / discipline
    "data science", "machine learning", "deep learning", "artificial intelligence",
    "ml engineer", "data scientist", "analytics engineer",
    # Methods
    "propensity", "churn", "segmentation", "a/b test", "holdout", "uplift",
    "nlp", "pricing", "elasticity", "ltv", "retention", "acquisition",
    "classification", "predictive", "forecasting", "recommendation",
    "risk model", "credit risk", "pd model", "default",
    # Product / business analytics
    "product analytics", "funnel", "cohort", "kpi", "crm", "customer analytics",
    "lifecycle",
    # Industry
    "fintech", "banking", "bank", "financial services", "credit",
]

# Technical skills from CV
_SKILL_KEYWORDS = [
    "python", "sql", "pyspark", "spark", "databricks", "airflow",
    "scikit-learn", "sklearn", "xgboost", "lightgbm", "catboost",
    "pandas", "docker",
]

# Location — absence is a mild penalty
_LOCATION_KEYWORDS = {"london", "remote", "hybrid", "united kingdom", " uk "}

SCORE_THRESHOLD = 5  # jobs below this are filtered from notifications


def score_job(job: dict) -> dict:
    """
    Score a job 1–10 by keyword matching. Fetches the job detail page for
    description text when possible. Adds 'score' and 'score_keywords' to the
    job dict in place and returns it.
    """
    title = job.get("title", "").lower()
    url = job.get("url", "")
    company = job.get("company", "")

    description = _fetch_description(url, company)
    job["description"] = description
    full_text = title + " " + description.lower()

    score = 5  # neutral baseline

    # Seniority in title — strongest signal
    if any(kw in title for kw in _SENIORITY_POSITIVE):
        score += 2
    elif any(kw in title for kw in _SENIORITY_NEGATIVE):
        score -= 4

    # Domain keyword hits
    domain_hits = [kw for kw in _DOMAIN_KEYWORDS if kw in full_text]
    score += min(len(domain_hits), 3)

    # Skill keyword hits
    skill_hits = [kw for kw in _SKILL_KEYWORDS if kw in full_text]
    score += min(len(skill_hits) // 2, 2)

    # Location check: hard penalty for explicit non-UK city, mild for no signal
    if not is_uk_relevant(full_text[:500]):
        score -= 5  # explicit non-UK location in description → push below threshold
    elif not any(loc in full_text for loc in _LOCATION_KEYWORDS):
        score -= 1  # no location signal at all

    job["score"] = max(1, min(10, score))
    job["score_keywords"] = (domain_hits + skill_hits)[:6]
    return job


def _fetch_description(url: str, company: str) -> str:
    time.sleep(_DESCRIPTION_FETCH_DELAY)
    # retries=1: detail pages are best-effort; failure just means no description
    soup = fetch_page(url, company, retries=1)
    if soup is None:
        return ""
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)[:5000]

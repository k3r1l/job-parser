# CLAUDE.md

## What this is

A daily job parser that monitors company career pages for new Data Scientist / ML roles in London, then sends Telegram notifications. Runs on GitHub Actions Mon–Fri at 10:00 UTC.

**Target roles:** middle / senior / lead Data Scientist (and related: ML Engineer, Analytics Engineer)
**Target location:** London, UK (remote/hybrid acceptable)

---

## Architecture

```
main.py                  — orchestrator: load companies → parse → diff → score → notify → save → report
companies.yml            — list of companies + career page URLs to monitor
src/parsers/base.py      — generic link scraper (fallback for all companies); handles pagination
src/parsers/__init__.py  — place company-specific parsers here (Greenhouse, Lever, etc.)
src/filters.py           — keyword + location filter (is_relevant_title, is_uk_relevant)
src/scorer.py            — keyword-based job scorer (1–10); fetches job detail pages
src/storage.py           — load/save data/jobs.json; find new + removed jobs
src/notifier.py          — Telegram send_message + message formatters
src/reporter.py          — generates data/report.html (sortable/filterable HTML table)
data/jobs.json           — full job records with descriptions, scores, dates, statuses
data/report.html         — generated HTML report; committed by CI each run
.github/workflows/daily_run.yml  — GitHub Actions workflow
tests/                   — pytest suite (68 tests); run with .venv/bin/pytest
```

**Job ID:** stable MD5 of `company::url` — survives title renames, deduplicates across runs.

**Storage format** (`data/jobs.json`):
```json
{
  "CompanyName": {
    "<md5>": {
      "id", "title", "url", "company", "location",
      "description",       // first 5000 chars of job page text
      "score",             // 1–10 keyword score
      "score_keywords",    // matched keyword list
      "first_seen",        // ISO date
      "last_seen",         // ISO date (updated each run while active)
      "status",            // "active" | "removed"
      "removed_date"       // ISO date, only when status = "removed"
    }
  }
}
```
Written back to git by the workflow after each run (`[skip ci]` commit).

---

## Pagination

`parse_generic` uses `?page=N` pagination with two auto-stop conditions:
1. **Empty page** — zero `<a>` links on the page means we're past the last real page.
2. **Repeated fingerprint** — MD5 of all hrefs on the page matches the previous page, meaning the site ignores the `?page=N` parameter (stops after 2 fetches).

Default ceiling is 25 pages (`_MAX_PAGES_CEILING`). This rarely matters — the two stop conditions kick in first. Only override `max_pages:` in `companies.yml` if a board genuinely exceeds 25 pages.

---

## Notification flow

Each run sends these Telegram messages (in order):
1. **New jobs per company** — one message per company with new notifiable jobs (score ≥ 5)
2. **Removed jobs per company** — one message per company where jobs disappeared
3. **Fetch errors** — if any career pages were unreachable after all retries
4. **Company snapshot** — all companies with active vacancies, sorted by count
5. **Daily summary** — total new + removed count

---

## JS-rendered boards (not scrapable without headless browser)

These boards require JavaScript execution and cannot be scraped with `requests` + BeautifulSoup. Commented out in `companies.yml` until a Playwright/Selenium-based parser is built:

| Company | Platform | Notes |
|---------|----------|-------|
| Klarna | Deel (jobs.deel.com/klarna) | Migrated from Greenhouse; Deel is a React SPA |
| Uber | React SPA | No public API |
| Citi | Eightfold AI | JS-rendered |
| Bloomberg | Avature | JS-rendered |
| NatWest Group | Workday | JS-rendered |
| BNP Paribas | Custom | Bot protection |
| Preply | Ashby (embedded) | Uses ashby_jid on own domain, no public Ashby board |

---

## What is NOT done yet (next steps)

### 1. Company-specific parsers
Many boards expose structured JSON/REST endpoints that are more reliable than HTML scraping. The `parser:` key in `companies.yml` is reserved for routing but no custom parsers are implemented yet. Planned:

- **Greenhouse** (`parser: greenhouse`) — `https://boards-api.greenhouse.io/v1/boards/{slug}/jobs`
- **Workable** (`parser: workable`) — `https://apply.workable.com/api/v3/accounts/{slug}/jobs`
- **Ashby** (`parser: ashby`) — `https://api.ashbyhq.com/posting-api/job-board/{slug}`
- **Lever** (`parser: lever`) — `https://api.lever.co/v0/postings/{slug}?mode=json`

Add each as a module in `src/parsers/` and call from `main.py` based on `cfg.get("parser")`.

### 2. JS-rendered boards
For boards that require JavaScript (Deel, Eightfold, Workday), add a Playwright-based fetcher as an alternative to `fetch_page`. This would unblock Klarna, Uber, Citi, Bloomberg, NatWest.

---

## Constraints

- Python 3.12+ (tested on 3.14)
- GitHub Actions secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (set in repo Settings → Secrets)
- The workflow commits `data/jobs.json` and `data/report.html` back to the repo — do not use external storage
- Keep dependencies minimal; add to `requirements.txt` if a new package is needed
- `data/jobs.json` and `data/report.html` must NOT be in `.gitignore` — CI commits them
- Score threshold for Telegram notifications: `SCORE_THRESHOLD = 5` in `src/scorer.py`

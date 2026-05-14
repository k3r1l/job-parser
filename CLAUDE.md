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
src/parsers/base.py      — generic link scraper (fallback for all companies)
src/parsers/__init__.py  — place company-specific parsers here (Greenhouse, Lever, etc.)
src/filters.py           — keyword + location filter functions
src/scorer.py            — keyword-based job scorer (1–10); fetches job detail pages
src/storage.py           — load/save data/jobs.json; find new + removed jobs
src/notifier.py          — Telegram send_message + message formatters
src/reporter.py          — generates data/report.html (sortable/filterable HTML table)
data/jobs.json           — full job records with descriptions, scores, dates, statuses
data/report.html         — generated HTML report; committed by CI each run
.github/workflows/daily_run.yml  — GitHub Actions workflow
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

## What is already done

- Core pipeline: fetch → parse → diff → notify → persist
- Generic scraper (`parse_generic`) that walks all `<a>` tags and filters by keyword
- Telegram notifier with HTML formatting
- GitHub Actions workflow with `contents: write` permission to push `seen_jobs.json`
- Keyword list (`KEYWORDS`) and location list (`LOCATION_KEYWORDS`) in `src/filters.py`
- `is_relevant_location()` helper exists but is not yet wired into the pipeline

---

## What is NOT done yet (next steps)

### 1. Populate `companies.yml`
The file is empty. Add real company career page URLs. Example structure:
```yaml
companies:
  - name: "DeepMind"
    url: "https://deepmind.google/careers/"
  - name: "Monzo"
    url: "https://monzo.com/careers/"
```

### 2. Detect disappeared jobs
`main.py` notifies on new jobs but never on removed ones. `storage.py` has the data needed — compute the set difference between previous seen IDs and current crawl, then call a new `format_removed_jobs()` notifier.

### 3. Wire up location filtering
`is_relevant_location()` in `src/filters.py` exists but `parse_generic` never calls it. Location text is often on the same page but not in the `<a>` tag itself — may need to inspect sibling/parent elements.

### 4. Company-specific parsers
Many boards (Greenhouse, Lever, Workday) expose structured JSON endpoints that are more reliable than HTML scraping. Add them as modules in `src/parsers/` and route via the `parser:` key in `companies.yml`.

---

## Constraints

- Python 3.12
- GitHub Actions secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (set in repo Settings → Secrets)
- The workflow commits `data/seen_jobs.json` back to the repo — do not use external storage
- Keep dependencies minimal; add to `requirements.txt` if a new package is needed

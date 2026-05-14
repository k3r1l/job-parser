# Job Parser

Checks a list of company career pages daily, filters for Data Science / ML roles in London, and sends new listings to Telegram.

## Project structure

```
job-parser/
├── .github/workflows/daily_run.yml   # GitHub Actions: runs Mon–Fri at 08:00 UTC
├── src/
│   ├── parsers/
│   │   ├── base.py       # Generic scraper + Job dataclass
│   │   └── ...           # Company-specific parsers go here
│   ├── filters.py        # KEYWORDS and LOCATION_KEYWORDS lists
│   ├── notifier.py       # Telegram sender
│   └── storage.py        # seen_jobs.json read/write
├── data/seen_jobs.json   # Persisted between runs (committed by the Action)
├── companies.yml         # The list of companies to check
└── main.py               # Entry point
```

## Setup

### 1. Add companies

Edit `companies.yml`:

```yaml
companies:
  - name: "DeepMind"
    url: "https://deepmind.google/about/careers/"
```

### 2. Create a Telegram bot

1. Chat with [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **token**
2. Start a chat with your bot, then get your **chat ID**:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

### 3. Add GitHub Secrets

In your repo → Settings → Secrets and variables → Actions:

| Secret name           | Value              |
|-----------------------|--------------------|
| `TELEGRAM_BOT_TOKEN`  | your bot token     |
| `TELEGRAM_CHAT_ID`    | your chat / user ID|

### 4. Local testing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your credentials
python main.py
```

## Adjusting filters

Edit `src/filters.py` — `KEYWORDS` controls which job titles are picked up, `LOCATION_KEYWORDS` narrows by location text on the page.

## Adding a company-specific parser

If the generic link scraper doesn't work for a site (e.g. it's JS-rendered or uses an API), add a file `src/parsers/<company>.py` with a function matching:

```python
def parse(company: str, url: str) -> list[Job]: ...
```

Then reference it in `companies.yml` with `parser: <company>` and dispatch from `main.py`.

import logging
import os

import requests

logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

_API_BASE = "https://api.telegram.org/bot{token}/{method}"


def send_message(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set — skipping notification")
        return

    url = _API_BASE.format(token=BOT_TOKEN, method="sendMessage")
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Telegram notification sent")
    except requests.RequestException as exc:
        logger.error("Failed to send Telegram notification: %s", exc)


def format_new_jobs(company: str, jobs: list[dict]) -> str:
    lines = [f"<b>🔍 New jobs at {company} ({len(jobs)})</b>"]
    for job in sorted(jobs, key=lambda j: j.get("score", 0), reverse=True):
        title = job.get("title", "—")
        url = job.get("url", "")
        score = job.get("score")
        keywords = job.get("score_keywords", [])

        link = f'<a href="{url}">{title}</a>' if url else title
        if score is not None:
            badge = _score_badge(score)
            kw_str = ", ".join(keywords[:4]) if keywords else ""
            detail = f"  {badge} {score}/10" + (f" · {kw_str}" if kw_str else "")
            lines.append(f"• {link}\n{detail}")
        else:
            lines.append(f"• {link}")
    return "\n".join(lines)


def _score_badge(score: int) -> str:
    if score >= 8:
        return "🟢"
    if score >= 6:
        return "🟡"
    return "🔴"


def format_fetch_errors(companies: list[str]) -> str:
    lines = ["<b>⚠️ Fetch errors — career pages unreachable</b>"]
    lines += [f"• {c}" for c in companies]
    lines.append("\nCheck URLs in <code>companies.yml</code> or update parsers.")
    return "\n".join(lines)


def format_removed_jobs(company: str, jobs: list[dict]) -> str:
    lines = [f"<b>👋 Removed jobs at {company} ({len(jobs)})</b>"]
    for job in jobs:
        title = job.get("title", "—")
        url = job.get("url", "")
        first = job.get("first_seen", "")
        link = f'<a href="{url}">{title}</a>' if url else title
        note = f"  <i>first seen {first}</i>" if first else ""
        lines.append(f"• {link}{note}")
    return "\n".join(lines)


def format_daily_summary(total_new: int, total_removed: int) -> str:
    parts = []
    if total_new:
        parts.append(f"<b>{total_new} new</b>")
    if total_removed:
        parts.append(f"<b>{total_removed} removed</b>")
    if not parts:
        return "✅ Daily job check complete — no changes found."
    return f"📋 Daily job check complete — {' · '.join(parts)} across all companies."

import html
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

REPORT_PATH = Path(__file__).parent.parent / "data" / "report.html"


def generate_report(stored: dict) -> None:
    active, removed = [], []
    for company_jobs in stored.values():
        for job in company_jobs.values():
            if job.get("status") == "removed":
                removed.append(job)
            else:
                active.append(job)

    active.sort(key=lambda j: j.get("score") or 0, reverse=True)
    removed.sort(key=lambda j: j.get("removed_date", ""), reverse=True)

    rows = [_job_row(j) for j in active] + [_job_row(j) for j in removed]
    body = "\n".join(rows)
    today = date.today().isoformat()

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Tracker</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f5f5f5; color: #222; padding: 20px; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 4px; }}
  .meta {{ color: #666; font-size: 0.85rem; margin-bottom: 16px; }}
  .controls {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }}
  .controls input, .controls select {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 0.9rem; }}
  .controls input {{ width: 260px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  th {{ background: #333; color: #fff; padding: 10px 12px; text-align: left; font-size: 0.82rem; cursor: pointer; user-select: none; }}
  th:hover {{ background: #444; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 0.88rem; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.removed td {{ color: #999; }}
  tr:hover td {{ background: #fafafa; }}
  .score {{ font-weight: 600; white-space: nowrap; }}
  .s-green {{ color: #1a7f37; }}
  .s-yellow {{ color: #9a6700; }}
  .s-red {{ color: #cf222e; }}
  .badge {{ display: inline-block; padding: 1px 7px; border-radius: 10px; font-size: 0.78rem; font-weight: 600; }}
  .badge-active {{ background: #dafbe1; color: #1a7f37; }}
  .badge-removed {{ background: #ffd8d3; color: #cf222e; }}
  .kw {{ font-size: 0.78rem; color: #666; }}
  details summary {{ cursor: pointer; color: #0969da; font-size: 0.82rem; }}
  details p {{ margin-top: 6px; font-size: 0.82rem; color: #444; white-space: pre-wrap; max-height: 200px; overflow-y: auto; background: #f8f8f8; padding: 8px; border-radius: 4px; }}
  a {{ color: #0969da; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .stats {{ display: flex; gap: 20px; margin-bottom: 14px; font-size: 0.88rem; }}
  .stat {{ background: #fff; border-radius: 6px; padding: 8px 14px; box-shadow: 0 1px 2px rgba(0,0,0,.08); }}
  .stat strong {{ font-size: 1.1rem; }}
</style>
</head>
<body>
<h1>Job Tracker</h1>
<p class="meta">Updated {today} &nbsp;·&nbsp; {len(active)} active &nbsp;·&nbsp; {len(removed)} removed</p>
<div class="stats">
  <div class="stat"><strong>{len(active)}</strong><br>Active</div>
  <div class="stat"><strong>{len(removed)}</strong><br>Removed</div>
  <div class="stat"><strong>{sum(1 for j in active if (j.get("score") or 0) >= 8)}</strong><br>Score ≥ 8</div>
  <div class="stat"><strong>{len(set(j["company"] for j in active + removed))}</strong><br>Companies</div>
</div>
<div class="controls">
  <input type="text" id="search" placeholder="Search title or company…" oninput="filter()">
  <select id="status" onchange="filter()">
    <option value="all">All statuses</option>
    <option value="active">Active only</option>
    <option value="removed">Removed only</option>
  </select>
  <select id="minscore" onchange="filter()">
    <option value="0">Any score</option>
    <option value="5">Score ≥ 5</option>
    <option value="7">Score ≥ 7</option>
    <option value="8">Score ≥ 8</option>
  </select>
</div>
<table id="tbl">
<thead>
  <tr>
    <th onclick="sortBy('score')">Score ▾</th>
    <th onclick="sortBy('company')">Company</th>
    <th onclick="sortBy('title')">Title</th>
    <th onclick="sortBy('status')">Status</th>
    <th onclick="sortBy('first_seen')">First seen</th>
    <th onclick="sortBy('last_seen')">Last seen</th>
    <th>Keywords / Description</th>
  </tr>
</thead>
<tbody id="tbody">
{body}
</tbody>
</table>
<script>
let sortCol = 'score', sortAsc = false;
function sortBy(col) {{
  if (sortCol === col) sortAsc = !sortAsc;
  else {{ sortCol = col; sortAsc = col !== 'score'; }}
  const rows = [...document.querySelectorAll('#tbody tr')];
  rows.sort((a, b) => {{
    const av = a.dataset[col] || '', bv = b.dataset[col] || '';
    const n = parseFloat(av), m = parseFloat(bv);
    const cmp = isNaN(n) ? av.localeCompare(bv) : n - m;
    return sortAsc ? cmp : -cmp;
  }});
  rows.forEach(r => document.getElementById('tbody').appendChild(r));
}}
function filter() {{
  const q = document.getElementById('search').value.toLowerCase();
  const st = document.getElementById('status').value;
  const ms = parseInt(document.getElementById('minscore').value) || 0;
  document.querySelectorAll('#tbody tr').forEach(r => {{
    const text = (r.dataset.title + ' ' + r.dataset.company).toLowerCase();
    const score = parseFloat(r.dataset.score) || 0;
    const status = r.dataset.status;
    const show = (!q || text.includes(q))
      && (st === 'all' || st === status)
      && score >= ms;
    r.style.display = show ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""

    REPORT_PATH.write_text(page, encoding="utf-8")
    logger.info("Report written to %s (%d active, %d removed)", REPORT_PATH, len(active), len(removed))


def _score_cls(score) -> str:
    if score is None:
        return ""
    if score >= 8:
        return "s-green"
    if score >= 6:
        return "s-yellow"
    return "s-red"


def _job_row(job: dict) -> str:
    score = job.get("score")
    score_str = f'<span class="score {_score_cls(score)}">{score}/10</span>' if score else "—"
    keywords = job.get("score_keywords", [])
    kw_str = f'<div class="kw">{html.escape(", ".join(keywords[:5]))}</div>' if keywords else ""
    desc_raw = (job.get("description") or "").strip()
    desc_html = ""
    if desc_raw:
        preview = html.escape(desc_raw[:3000])
        desc_html = f'<details><summary>Description</summary><p>{preview}</p></details>'

    status = job.get("status", "active")
    badge = f'<span class="badge badge-{status}">{status}</span>'
    title = html.escape(job.get("title", "—"))
    url = html.escape(job.get("url", ""))
    company = html.escape(job.get("company", ""))
    title_cell = f'<a href="{url}" target="_blank">{title}</a>' if url else title

    first_seen = job.get("first_seen", "")
    last_seen = job.get("removed_date") or job.get("last_seen", "")

    return (
        f'<tr class="{status}" '
        f'data-score="{score or 0}" data-company="{company}" '
        f'data-title="{title}" data-status="{status}" '
        f'data-first_seen="{first_seen}" data-last_seen="{last_seen}">'
        f"<td>{score_str}</td>"
        f"<td>{company}</td>"
        f"<td>{title_cell}</td>"
        f"<td>{badge}</td>"
        f"<td>{first_seen}</td>"
        f"<td>{last_seen}</td>"
        f"<td>{kw_str}{desc_html}</td>"
        f"</tr>"
    )

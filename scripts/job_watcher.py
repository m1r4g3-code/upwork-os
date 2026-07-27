#!/usr/bin/env python3
"""
Upwork OS — Job Watcher

Called by email_watcher.py when Upwork job alert emails arrive.
Also callable directly for manual qualification + notification.

Flow:
  1. Receive job URL from email alert
  2. Run scraper.py to get job JSON
  3. Run qualify.py to get score
  4. If score >= BID_THRESHOLD: send Telegram approval request
  5. Emmanuel taps Approve → job added to _QUEUE.md + proposal draft outline saved
  6. Emmanuel taps Skip → logged as evaluated/skipped

Usage:
    python scripts/job_watcher.py <url>
    python scripts/job_watcher.py <url> --dry-run
    python scripts/job_watcher.py --process-approvals   # check Telegram for approved jobs
"""

import sys
import json
import re
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT          = config.ROOT
BRAIN         = config.BRAIN
QUEUE_FILE    = config.QUEUE_FILE
JOBS_DIR      = BRAIN / "upwork" / "jobs" / "archive"
SOURCES_DIR   = ROOT / "sources" / "jobs"


# ─── Qualify pipeline ─────────────────────────────────────────────────────────

def scrape_job(url: str) -> Path | None:
    """Run scraper.py and return path to scraped JSON. Returns None on failure."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "scraper.py"), url],
            capture_output=True, text=True, timeout=60, cwd=str(ROOT)
        )
        # scraper.py prints the output file path on its last line
        lines = result.stdout.strip().splitlines()
        for line in reversed(lines):
            if line.endswith(".json") and Path(line).exists():
                return Path(line)
            # Check for path in output
            m = re.search(r"sources/jobs/[^\s]+\.json", line)
            if m:
                p = ROOT / m.group(0)
                if p.exists():
                    return p
    except subprocess.TimeoutExpired:
        print(f"[job_watcher] Scraper timed out for {url}", file=sys.stderr)
    except Exception as e:
        print(f"[job_watcher] Scraper error: {e}", file=sys.stderr)
    return None


def qualify_job(json_path: Path) -> dict | None:
    """Run qualify.py and return score dict. Returns None on failure."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "qualify.py"), str(json_path)],
            capture_output=True, text=True, timeout=30, cwd=str(ROOT)
        )
        output = result.stdout + result.stderr
        # Parse scores from output
        scores = {}
        for key in ("composite_score", "job_quality", "client_quality", "fit_score"):
            m = re.search(rf"{key}[:\s]+([0-9]+)", output, re.IGNORECASE)
            if m:
                scores[key] = int(m.group(1))
        decision_m = re.search(r"decision[:\s]+(BID|SKIP|WATCHLIST)", output, re.IGNORECASE)
        if decision_m:
            scores["decision"] = decision_m.group(1).upper()
        scores["_raw"] = output
        return scores if "composite_score" in scores else None
    except Exception as e:
        print(f"[job_watcher] Qualify error: {e}", file=sys.stderr)
        return None


def _extract_job_title(json_path: Path) -> str:
    """Extract job title from scraped JSON."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return data.get("title") or data.get("job_title") or json_path.stem
    except Exception:
        return json_path.stem


def _minutes_since_posted(json_path: Path) -> int | None:
    """Extract posting age from job JSON."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        posted_raw = data.get("posted_on") or data.get("created_at") or data.get("date_posted")
        if not posted_raw:
            return None
        # Try common formats
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                posted = datetime.strptime(posted_raw[:19], fmt[:len(posted_raw)])
                if posted.tzinfo is None:
                    posted = posted.replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - posted
                return int(delta.total_seconds() / 60)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _ooda_flag(minutes: int | None) -> str:
    if minutes is None:
        return "UNKNOWN"
    if minutes <= config.OODA_WINDOW_MINUTES:
        return f"🔴 MOVE NOW ({minutes}min ago)"
    if minutes <= 120:
        return f"🟠 2HR WINDOW ({minutes}min ago)"
    if minutes <= 360:
        return f"🟡 LATE ({minutes}min ago)"
    return f"⚪ EXPIRED ({minutes}min ago)"


# ─── Queue integration ────────────────────────────────────────────────────────

def _add_to_queue(job_title: str, job_id: str, score: int, url: str) -> None:
    """Add an approved bid to _QUEUE.md."""
    import re as _re
    text = QUEUE_FILE.read_text(encoding="utf-8")
    match = _re.search(r"```json\n(\[.*?\])\n```", text, _re.DOTALL)
    if not match:
        return
    try:
        items = json.loads(match.group(1))
    except json.JSONDecodeError:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    slug  = _re.sub(r"[^a-z0-9]+", "-", job_title.lower())[:30]
    new_id = f"job-{today}-{slug}"

    # Avoid duplicates
    if any(i["id"] == new_id for i in items):
        return

    items.append({
        "id":            new_id,
        "action":        f"Write + send proposal — {job_title}",
        "context":       f"Score {score} | URL: {url}",
        "priority":      "HIGH" if score >= 85 else "MEDIUM",
        "revenue_impact": "DIRECT",
        "deadline":      today,
        "owner":         "Emmanuel",
        "created":       today,
        "state":         "open",
        "platform":      "Upwork",
        "next_action":   f"Run /write-proposal {url}",
    })

    new_json = json.dumps(items, indent=2)
    new_text = text[:match.start()] + f"```json\n{new_json}\n```" + text[match.end():]
    QUEUE_FILE.write_text(new_text, encoding="utf-8")

    # Commit to brain
    subprocess.run(
        ["git", "add", "_QUEUE.md"],
        cwd=str(BRAIN), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", f"upwork: add job to queue — {job_title} score {score}"],
        cwd=str(BRAIN), capture_output=True
    )


# ─── Main qualify + notify ────────────────────────────────────────────────────

def qualify_and_notify(url: str, dry_run: bool = False) -> bool:
    """
    Full pipeline: scrape → qualify → notify if score meets threshold.
    Returns True if notification was sent (i.e., job met threshold).
    """
    from scripts.notify import send, send_approval, register_approval

    print(f"[job_watcher] Processing: {url}")

    json_path = scrape_job(url)
    if not json_path:
        print(f"[job_watcher] Scrape failed — skipping {url}", file=sys.stderr)
        return False

    scores = qualify_job(json_path)
    if not scores:
        print(f"[job_watcher] Qualify failed — skipping", file=sys.stderr)
        return False

    composite = scores.get("composite_score", 0)
    decision  = scores.get("decision", "SKIP")
    title     = _extract_job_title(json_path)
    minutes   = _minutes_since_posted(json_path)
    ooda      = _ooda_flag(minutes)

    print(f"[job_watcher] Score: {composite} | Decision: {decision} | {title}")

    if composite < config.WATCHLIST_THRESHOLD:
        print(f"[job_watcher] Score {composite} below watchlist threshold — skipping")
        return False

    if composite < config.BID_THRESHOLD:
        # Watchlist — log only, no notification
        print(f"[job_watcher] Score {composite} — watchlist only, no notification")
        return False

    # Score meets bid threshold — send approval request
    approval_id = f"bid-{json_path.stem}"
    body = (
        f"<b>Score:</b> {composite}/100 ({decision})\n"
        f"<b>OODA:</b> {ooda}\n"
        f"<b>Job:</b> {title}\n\n"
        f"Quality: {scores.get('job_quality','?')} | "
        f"Client: {scores.get('client_quality','?')} | "
        f"Fit: {scores.get('fit_score','?')}\n\n"
        f"<a href='{url}'>View on Upwork</a>"
    )

    if not dry_run:
        register_approval(approval_id, "job_bid", {
            "url": url, "title": title, "score": composite,
            "json_path": str(json_path),
        })
        send_approval(
            approval_id=approval_id,
            title=f"New Job — Score {composite}",
            body=body,
            yes_label="✅ Bid",
            no_label="❌ Skip",
        )
    else:
        print(f"[DRY RUN] Would send approval request:\n{body}")

    return True


def process_approvals() -> None:
    """
    Check Telegram for resolved job approval callbacks.
    For approved jobs: add to _QUEUE.md.
    For rejected: log as skipped.
    """
    from scripts.notify import poll_approvals, send

    resolved = poll_approvals()
    for item in resolved:
        if item.get("type") != "job_bid":
            continue
        data   = item.get("data", {})
        action = item.get("action")
        title  = data.get("title", "Unknown")
        score  = data.get("score", 0)
        url    = data.get("url", "")

        if action == "approve":
            _add_to_queue(title, item["id"], score, url)
            send(f"✅ <b>Queued:</b> {title}\nScore {score} — Run /write-proposal when ready.")
            print(f"[job_watcher] Approved + queued: {title}")
        else:
            send(f"⏭️ <b>Skipped:</b> {title} (Score {score})")
            print(f"[job_watcher] Rejected: {title}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS Job Watcher")
    parser.add_argument("url", nargs="?", help="Upwork job URL to qualify")
    parser.add_argument("--dry-run", action="store_true",
                        help="Qualify and print but don't send notifications")
    parser.add_argument("--process-approvals", action="store_true",
                        help="Check Telegram for approved job bids and queue them")
    args = parser.parse_args()

    if args.process_approvals:
        process_approvals()
        return

    if args.url:
        qualify_and_notify(args.url, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

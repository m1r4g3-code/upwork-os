#!/usr/bin/env python3
"""
Upwork OS Heartbeat — fires at every session start.

Reads brain state, computes priorities, surfaces what needs attention NOW.
No external dependencies — stdlib only.

Usage:
    python scripts/heartbeat.py
    python scripts/heartbeat.py --json          # machine-readable output
    python scripts/heartbeat.py --top 3         # top N items only
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta


# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT       = Path(__file__).parent.parent
BRAIN      = ROOT / "hephzibah-brain-temp"
QUEUE_FILE = BRAIN / "_QUEUE.md"
SESSION_FILE = BRAIN / "_SESSION.md"
PIPELINE_FILE = BRAIN / "_PIPELINE.md"
PROPOSALS_DIR = BRAIN / "upwork" / "proposals" / "sent"
CLIENTS_DIR   = BRAIN / "upwork" / "clients" / "active"
METRICS_FILE  = BRAIN / "upwork" / "performance" / "metrics.md"

# LinkedIn hard schedule (WAT = UTC+1)
LINKEDIN_SCHEDULE = [
    date(2026, 7, 24),
    date(2026, 7, 26),
    date(2026, 7, 29),
    date(2026, 7, 31),
    date(2026, 8, 2),
    date(2026, 8, 5),
]

PRIORITY_WEIGHT = {"CRITICAL": 100, "HIGH": 70, "MEDIUM": 40, "LOW": 10}
REVENUE_MULT    = {"DIRECT": 1.5, "INDIRECT": 1.0, "MAINTENANCE": 0.5}


# ─── Parsers ──────────────────────────────────────────────────────────────────

def parse_queue(filepath: Path) -> list[dict]:
    """Extract JSON queue items from _QUEUE.md machine-readable block."""
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    match = re.search(r"```json\n(\[.*?\])\n```", text, re.DOTALL)
    if not match:
        return []
    try:
        items = json.loads(match.group(1))
        return [i for i in items if i.get("state") not in ("resolved", "archived")]
    except json.JSONDecodeError as e:
        print(f"  [WARN] _QUEUE.md JSON parse error: {e}", file=sys.stderr)
        return []


def parse_frontmatter(text: str) -> dict:
    """Extract YAML-style frontmatter from a markdown file (simple key: value)."""
    fm = {}
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return fm
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def scan_proposals(proposals_dir: Path) -> list[dict]:
    """Scan sent proposals and return those past 72h or 7d with no reply."""
    alerts = []
    if not proposals_dir.exists():
        return alerts
    today = date.today()
    for f in proposals_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        status = fm.get("status", "").lower()
        if status in ("replied", "won", "lost", "ghosted"):
            continue
        sent_raw = fm.get("sent_date") or fm.get("date", "")
        if not sent_raw:
            continue
        try:
            sent = date.fromisoformat(sent_raw[:10])
        except ValueError:
            continue
        delta = (today - sent).days
        if delta >= 7:
            alerts.append({"file": f.name, "days": delta, "level": "GHOST", "fm": fm})
        elif delta >= 3:
            alerts.append({"file": f.name, "days": delta, "level": "FOLLOW_UP", "fm": fm})
    return sorted(alerts, key=lambda x: x["days"], reverse=True)


def scan_clients(clients_dir: Path) -> list[dict]:
    """Scan client nodes and return those with stale states."""
    stale = []
    if not clients_dir.exists():
        return stale
    today = date.today()
    stale_thresholds = {
        "outreach_sent": 3,
        "proposal_sent": 3,
        "engaged": 1,
        "replied": 1,
        "negotiating": 2,
        "delivery": 7,
        "ghosted": 14,
    }
    for f in clients_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        state = fm.get("state", "")
        entered_raw = fm.get("state_entered", "")
        if state not in stale_thresholds or not entered_raw:
            continue
        try:
            entered = date.fromisoformat(entered_raw[:10])
        except ValueError:
            continue
        days_in_state = (today - entered).days
        threshold = stale_thresholds[state]
        if days_in_state >= threshold:
            stale.append({
                "client": fm.get("name", f.stem),
                "state": state,
                "days_in_state": days_in_state,
                "threshold": threshold,
                "file": f.name,
            })
    return sorted(stale, key=lambda x: x["days_in_state"], reverse=True)


def check_linkedin_schedule() -> dict | None:
    """Check if a LinkedIn post is due today or overdue."""
    today = date.today()
    for post_date in LINKEDIN_SCHEDULE:
        if post_date == today:
            return {"status": "DUE_TODAY", "date": post_date.isoformat()}
        if post_date < today:
            # Check if we can verify it was posted (look for log file)
            post_num = LINKEDIN_SCHEDULE.index(post_date) + 1
            log_glob = list((ROOT / "hephzibah-brain-temp" / "content" / "posts").glob(
                f"{post_date.isoformat()}*.md"
            )) if (ROOT / "hephzibah-brain-temp" / "content" / "posts").exists() else []
            if not log_glob:
                return {"status": "OVERDUE", "date": post_date.isoformat(), "post_num": post_num}
    # Check upcoming
    for post_date in LINKEDIN_SCHEDULE:
        if post_date > today:
            delta = (post_date - today).days
            return {"status": "UPCOMING", "date": post_date.isoformat(), "days_away": delta}
    return None


def score_item(item: dict) -> float:
    """Compute priority score for a queue item."""
    p = PRIORITY_WEIGHT.get(item.get("priority", "LOW"), 10)
    r = REVENUE_MULT.get(item.get("revenue_impact", "INDIRECT"), 1.0)
    # Time pressure boost: deadline within 24h adds 50%
    deadline_raw = item.get("deadline")
    time_boost = 1.0
    if deadline_raw:
        try:
            dl = date.fromisoformat(deadline_raw)
            days_left = (dl - date.today()).days
            if days_left <= 0:
                time_boost = 2.0   # overdue
            elif days_left == 1:
                time_boost = 1.5   # due tomorrow
        except ValueError:
            pass
    return p * r * time_boost


# ─── Formatters ───────────────────────────────────────────────────────────────

PRIORITY_ICONS = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}
LEVEL_ICONS    = {"GHOST": "💀", "FOLLOW_UP": "⏰"}


def fmt_queue(items: list[dict], top: int | None = None) -> str:
    scored = sorted(items, key=score_item, reverse=True)
    if top:
        scored = scored[:top]
    lines = []
    for item in scored:
        icon  = PRIORITY_ICONS.get(item.get("priority", "LOW"), "⚪")
        state = item.get("state", "open").upper()
        dl    = item.get("deadline") or "—"
        lines.append(f"  {icon} [{item['id']}] {item['action']}")
        lines.append(f"     → {item['next_action']}")
        lines.append(f"     Deadline: {dl} | State: {state} | Owner: {item.get('owner','?')}")
    return "\n".join(lines) if lines else "  No open items."


def fmt_proposals(alerts: list[dict]) -> str:
    if not alerts:
        return "  No proposals past threshold."
    lines = []
    for a in alerts:
        icon = LEVEL_ICONS.get(a["level"], "⏰")
        name = a["fm"].get("client") or a["file"]
        lines.append(f"  {icon} {name} — {a['days']}d since sent [{a['level']}]")
        lines.append(f"     File: {a['file']}")
    return "\n".join(lines)


def fmt_clients(stale: list[dict]) -> str:
    if not stale:
        return "  All clients within expected state windows."
    lines = []
    for s in stale:
        lines.append(f"  ⚠️  {s['client']} — in [{s['state']}] for {s['days_in_state']}d (threshold: {s['threshold']}d)")
        lines.append(f"     File: {s['file']}")
    return "\n".join(lines)


def compute_top_action(queue: list[dict], proposals: list[dict], clients: list[dict]) -> str:
    """Surface the single most important action right now."""
    # Overdue proposals → ghost urgency
    ghosts = [p for p in proposals if p["level"] == "GHOST"]
    if ghosts:
        p = ghosts[0]
        name = p["fm"].get("client") or p["file"]
        return f"💀 Log {name} as GHOSTED — {p['days']}d with no reply. Run /log-outcome."

    # Critical queue items
    scored = sorted(queue, key=score_item, reverse=True)
    if scored:
        top = scored[0]
        if top.get("priority") in ("CRITICAL", "HIGH"):
            return f"{PRIORITY_ICONS.get(top['priority'], '🟡')} {top['action']}\n   → {top['next_action']}"

    # Stale clients
    if clients:
        c = clients[0]
        return f"⚠️  {c['client']} has been in [{c['state']}] for {c['days_in_state']}d — take action."

    # Follow-up proposals
    followups = [p for p in proposals if p["level"] == "FOLLOW_UP"]
    if followups:
        p = followups[0]
        name = p["fm"].get("client") or p["file"]
        return f"⏰ Follow up on proposal to {name} — {p['days']}d since sent."

    return "✅ Queue clear. Run /niche-radar to find new opportunities."


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(args):
    today     = datetime.now()
    queue     = parse_queue(QUEUE_FILE)
    proposals = scan_proposals(PROPOSALS_DIR)
    clients   = scan_clients(CLIENTS_DIR)
    linkedin  = check_linkedin_schedule()
    top_action = compute_top_action(queue, proposals, clients)

    if args.json:
        out = {
            "timestamp": today.isoformat(),
            "top_action": top_action,
            "queue": sorted(queue, key=score_item, reverse=True),
            "proposal_alerts": proposals,
            "stale_clients": clients,
            "linkedin": linkedin,
        }
        print(json.dumps(out, indent=2, default=str))
        return

    bar = "═" * 62
    print(f"\n{bar}")
    print(f"  UPWORK OS — HEARTBEAT     {today.strftime('%Y-%m-%d  %H:%M')}")
    print(f"{bar}\n")

    # ── #1 Action ──
    print("▶ #1 ACTION RIGHT NOW")
    print(f"  {top_action}\n")

    # ── Priority Queue ──
    open_q = [i for i in queue if i.get("state") != "resolved"]
    print(f"▶ PRIORITY QUEUE  ({len(open_q)} open items)")
    print(fmt_queue(open_q, top=args.top))
    print()

    # ── Proposal Timers ──
    print(f"▶ PROPOSAL FOLLOW-UPS  ({len(proposals)} alert{'s' if len(proposals) != 1 else ''})")
    print(fmt_proposals(proposals))
    print()

    # ── Stale Clients ──
    print(f"▶ CLIENT STATE ALERTS  ({len(clients)} stale)")
    print(fmt_clients(clients))
    print()

    # ── LinkedIn ──
    print("▶ LINKEDIN SCHEDULE")
    if linkedin:
        status = linkedin["status"]
        if status == "DUE_TODAY":
            print(f"  🔴 POST DUE TODAY — publish at 8AM WAT. First comment within 60s.")
        elif status == "OVERDUE":
            print(f"  💀 POST OVERDUE — was due {linkedin['date']} (Post {linkedin.get('post_num','?')}). Publish ASAP.")
        elif status == "UPCOMING":
            print(f"  🟡 Next post: {linkedin['date']} — {linkedin['days_away']} day{'s' if linkedin['days_away'] != 1 else ''} away.")
    else:
        print("  ✅ No posts scheduled.")
    print()

    # ── Footer ──
    print(f"{bar}")
    print("  Run /pulse for full system vitals.")
    print(f"{bar}\n")


def main():
    parser = argparse.ArgumentParser(description="Upwork OS Heartbeat")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--top", type=int, default=None, help="Show top N queue items")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

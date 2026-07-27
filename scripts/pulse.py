#!/usr/bin/env python3
"""
Upwork OS Pulse — system vitals on demand.

Reads brain state and surfaces a real-time health dashboard:
JSS trajectory, pipeline value, proposal metrics, connects, follow-ups.

Usage:
    python scripts/pulse.py
    python scripts/pulse.py --json
    python scripts/pulse.py --section pipeline
    python scripts/pulse.py --section proposals
    python scripts/pulse.py --section queue
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime, date


# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT          = Path(__file__).parent.parent
BRAIN         = ROOT / "hephzibah-brain-temp"
QUEUE_FILE    = BRAIN / "_QUEUE.md"
PIPELINE_FILE = BRAIN / "_PIPELINE.md"
METRICS_FILE  = BRAIN / "upwork" / "performance" / "metrics.md"
PROPOSALS_DIR = BRAIN / "upwork" / "proposals" / "sent"
CLIENTS_DIR   = BRAIN / "upwork" / "clients" / "active"
ACCOUNT_FILE  = BRAIN / "upwork" / "identity" / "account-situation.md"


# ─── Parsers ──────────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    fm = {}
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return fm
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"')
    return fm


def parse_queue(filepath: Path) -> list[dict]:
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    match = re.search(r"```json\n(\[.*?\])\n```", text, re.DOTALL)
    if not match:
        return []
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return []


def parse_metrics(filepath: Path) -> dict:
    """Extract key-value metrics from metrics.md."""
    if not filepath.exists():
        return {}
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    metrics = {}
    patterns = {
        "jss": r"jss[:\s]+([0-9.]+%?|—|unknown|new account)",
        "proposals_sent": r"proposals.sent[:\s]+([0-9]+)",
        "proposals_viewed": r"proposals.viewed[:\s]+([0-9]+)",
        "proposals_replied": r"proposals.replied[:\s]+([0-9]+)",
        "connects_balance": r"connects.balance[:\s]+([0-9]+|—)",
        "active_contracts": r"active.contracts?[:\s]+([0-9]+)",
        "total_earned": r"total.earned[:\s]+\$?([0-9,]+|—)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        metrics[key] = m.group(1).strip() if m else "—"
    return metrics


def scan_proposals(proposals_dir: Path) -> dict:
    """Aggregate proposal stats."""
    stats = {"sent": 0, "viewed": 0, "replied": 0, "won": 0, "lost": 0, "ghosted": 0, "pending": 0}
    if not proposals_dir.exists():
        return stats
    for f in proposals_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        stats["sent"] += 1
        status = fm.get("status", "").lower()
        outcome = fm.get("outcome", "").lower()
        viewed = fm.get("viewed", "").lower()
        if viewed in ("true", "yes", "1"):
            stats["viewed"] += 1
        for key in ("replied", "won", "lost", "ghosted"):
            if key in (status, outcome):
                stats[key] += 1
                break
        else:
            if status not in ("won", "lost", "ghosted", "replied"):
                stats["pending"] += 1
    return stats


def scan_pipeline(clients_dir: Path) -> dict:
    """Aggregate pipeline value and client counts."""
    data = {"active": 0, "total_value": 0, "clients": []}
    if not clients_dir.exists():
        return data
    active_states = {"proposal_sent", "replied", "call_booked", "negotiating",
                     "contract_active", "delivery", "engaged"}
    for f in clients_dir.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        state = fm.get("state", "")
        if state in active_states:
            data["active"] += 1
            val_raw = fm.get("potential_value") or fm.get("contract_value", "0")
            try:
                val = float(re.sub(r"[^0-9.]", "", str(val_raw)) or 0)
            except ValueError:
                val = 0
            data["total_value"] += val
            data["clients"].append({
                "name": fm.get("name", f.stem),
                "state": state,
                "value": val,
                "platform": fm.get("platform", "?"),
            })
    return data


def compute_rates(prop_stats: dict) -> dict:
    """Compute view rate and reply rate."""
    sent = prop_stats["sent"]
    rates = {}
    rates["view_rate"] = f"{round(prop_stats['viewed'] / sent * 100)}%" if sent else "—"
    rates["reply_rate"] = f"{round(prop_stats['replied'] / sent * 100)}%" if sent else "—"
    rates["win_rate"] = f"{round(prop_stats['won'] / prop_stats['replied'] * 100)}%" if prop_stats["replied"] else "—"
    return rates


def check_overdue_followups(proposals_dir: Path) -> list[dict]:
    """Return proposals past 72h with no reply."""
    overdue = []
    if not proposals_dir.exists():
        return overdue
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
        if delta >= 3:
            overdue.append({"file": f.name, "days": delta,
                            "client": fm.get("client", f.stem)})
    return sorted(overdue, key=lambda x: x["days"], reverse=True)


# ─── Sections ─────────────────────────────────────────────────────────────────

def section_account(metrics: dict) -> str:
    jss = metrics.get("jss", "—")
    jss_note = ""
    if jss == "—" or "new" in str(jss).lower():
        jss_note = "  (new account — JSS unlocks after first contract)"
    lines = [
        f"  JSS:               {jss}{jss_note}",
        f"  Connects balance:  {metrics.get('connects_balance', '—')}",
        f"  Active contracts:  {metrics.get('active_contracts', '—')}",
        f"  Total earned:      ${metrics.get('total_earned', '—')}",
    ]
    return "\n".join(lines)


def section_pipeline(pipeline: dict) -> str:
    total = f"${pipeline['total_value']:,.0f}" if pipeline["total_value"] else "$0"
    lines = [
        f"  Active clients:    {pipeline['active']}",
        f"  Pipeline value:    {total}",
    ]
    for c in pipeline["clients"]:
        val = f"  ${c['value']:,.0f}" if c["value"] else ""
        lines.append(f"    • {c['name']} [{c['state']}] — {c['platform']}{val}")
    if not pipeline["clients"]:
        lines.append("    No active clients.")
    return "\n".join(lines)


def section_proposals(prop_stats: dict, rates: dict, overdue: list) -> str:
    lines = [
        f"  Sent (all time):   {prop_stats['sent']}",
        f"  Pending reply:     {prop_stats['pending']}",
        f"  Viewed:           {prop_stats['viewed']}  (view rate: {rates['view_rate']})",
        f"  Replied:          {prop_stats['replied']}  (reply rate: {rates['reply_rate']})",
        f"  Won:              {prop_stats['won']}  (win rate: {rates['win_rate']})",
        f"  Ghosted:          {prop_stats['ghosted']}",
    ]
    if overdue:
        lines.append(f"\n  ⏰ FOLLOW-UPS OVERDUE ({len(overdue)}):")
        for o in overdue:
            lines.append(f"    • {o['client']} — {o['days']}d since sent")
    else:
        lines.append("\n  ✅ No follow-ups overdue.")
    return "\n".join(lines)


def section_queue(queue: list) -> str:
    open_items = [i for i in queue if i.get("state") not in ("resolved", "archived")]
    by_priority = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for item in open_items:
        p = item.get("priority", "LOW")
        by_priority.get(p, by_priority["LOW"]).append(item)

    icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}
    lines = [f"  Total open: {len(open_items)}"]
    for level, items in by_priority.items():
        if items:
            lines.append(f"  {icons[level]} {level}: {len(items)}")
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(args):
    today     = datetime.now()
    metrics   = parse_metrics(METRICS_FILE)
    pipeline  = scan_pipeline(CLIENTS_DIR)
    prop_stats = scan_proposals(PROPOSALS_DIR)
    rates     = compute_rates(prop_stats)
    overdue   = check_overdue_followups(PROPOSALS_DIR)
    queue     = parse_queue(QUEUE_FILE)

    if args.json:
        out = {
            "timestamp": today.isoformat(),
            "account": metrics,
            "pipeline": pipeline,
            "proposals": {**prop_stats, **rates},
            "overdue_followups": overdue,
            "queue_summary": {p: len([i for i in queue if i.get("priority") == p
                                      and i.get("state") not in ("resolved","archived")])
                              for p in ("CRITICAL","HIGH","MEDIUM","LOW")},
        }
        print(json.dumps(out, indent=2, default=str))
        return

    section = args.section

    bar = "═" * 62
    print(f"\n{bar}")
    print(f"  UPWORK OS — PULSE         {today.strftime('%Y-%m-%d  %H:%M')}")
    print(f"{bar}\n")

    if not section or section == "account":
        print("▶ ACCOUNT HEALTH")
        print(section_account(metrics))
        print()

    if not section or section == "pipeline":
        print("▶ PIPELINE")
        print(section_pipeline(pipeline))
        print()

    if not section or section == "proposals":
        print("▶ PROPOSALS")
        print(section_proposals(prop_stats, rates, overdue))
        print()

    if not section or section == "queue":
        print("▶ QUEUE SUMMARY")
        print(section_queue(queue))
        print()

    if not section:
        # Diagnostic note
        if prop_stats["sent"] > 0 and prop_stats["viewed"] and prop_stats["viewed"] / prop_stats["sent"] < 0.3:
            print("  ⚠️  DIAGNOSTIC: View rate <30% — profile suppression likely.")
            print("       Fix profile first (JSS, keywords, category). Then proposals.")
            print()

    print(f"{bar}")
    print("  Run /heartbeat for session priorities.")
    print(f"{bar}\n")


def main():
    # Force UTF-8 output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Upwork OS Pulse — system vitals")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--section", choices=["account", "pipeline", "proposals", "queue"],
                        default=None, help="Show only one section")
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()

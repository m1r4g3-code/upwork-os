#!/usr/bin/env python3
"""
Upwork OS — Autonomous Follow-up Engine

Runs every 6 hours via Task Scheduler.
Scans sent proposals for those past the 72h threshold with no reply.
Drafts a follow-up message and sends a Telegram approval request.
Emmanuel taps Approve → follow-up text is logged and Emmanuel sends it manually on Upwork.

Ghost detection: proposals with no reply after 7 days are auto-logged as ghosted.

Usage:
    python scripts/follow_up.py
    python scripts/follow_up.py --dry-run
    python scripts/follow_up.py --process-approvals    # handle Telegram callbacks
    python scripts/follow_up.py --scan                 # scan only, print report
"""

import sys
import re
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT          = config.ROOT
BRAIN         = config.BRAIN
PROPOSALS_DIR = config.PROPOSALS_DIR
METRICS_FILE  = config.METRICS_FILE
PATTERNS_DIR  = config.PATTERNS_DIR

FOLLOWUP_HOURS = config.FOLLOWUP_HOURS    # 72
GHOST_DAYS     = config.GHOST_DAYS        # 7


# ─── Proposal scanning ────────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    """Extract YAML-style frontmatter from a markdown file."""
    meta = {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


def _days_since(date_str: str) -> float | None:
    """Parse a YYYY-MM-DD date string and return hours since it."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(date_str[:len(fmt)], fmt)
            dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        except ValueError:
            continue
    return None


def scan_proposals() -> dict:
    """
    Scan proposals/sent/ and classify each proposal:
    - overdue: past FOLLOWUP_HOURS with no reply, not yet followed up
    - ghosted: past GHOST_DAYS with no reply, no follow-up sent
    - followed_up: already had a follow-up, awaiting reply
    - active: within follow-up window
    Returns dict with lists under each key.
    """
    results = {"overdue": [], "ghosted": [], "followed_up": [], "active": [], "skip": []}

    if not PROPOSALS_DIR.exists():
        return results

    for f in sorted(PROPOSALS_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        meta = _parse_frontmatter(text)

        status   = meta.get("status", "sent")
        sent_on  = meta.get("sent_on") or meta.get("date") or f.stem[:10]

        # Skip proposals that already have terminal statuses
        if status in ("won", "lost", "ghosted", "closed", "not_sent"):
            results["skip"].append({"file": f.name, "status": status})
            continue

        # Skip if reply already received
        if status in ("replied", "interview", "call_booked"):
            results["skip"].append({"file": f.name, "status": status})
            continue

        hours_since = _days_since(sent_on)
        if hours_since is None:
            continue

        entry = {
            "file":        f.name,
            "path":        str(f),
            "slug":        f.stem,
            "hours_since": round(hours_since, 1),
            "status":      status,
            "meta":        meta,
        }

        days_since = hours_since / 24

        if days_since >= GHOST_DAYS:
            if status != "followup_sent":
                entry["ghost_candidate"] = True
            results["ghosted"].append(entry)
        elif hours_since >= FOLLOWUP_HOURS:
            if status == "followup_sent":
                results["followed_up"].append(entry)
            else:
                results["overdue"].append(entry)
        else:
            results["active"].append(entry)

    return results


# ─── Follow-up draft generation ───────────────────────────────────────────────

_FOLLOWUP_TEMPLATES = [
    # Template A — check-in, low friction
    (
        "Hey {name},\n\n"
        "Just circling back on this. Did you get a chance to look at my Loom?\n\n"
        "Still happy to help with {topic} if the timing works."
    ),
    # Template B — value add
    (
        "Hey {name},\n\n"
        "Saw something relevant since I sent the Loom — {observation}.\n\n"
        "Worth a quick call if you're still looking."
    ),
    # Template C — ultra short
    (
        "Hey {name},\n\nStill open on this. Just say the word."
    ),
]


def _extract_proposal_context(path: str) -> dict:
    """Extract client name and topic from proposal file."""
    text    = Path(path).read_text(encoding="utf-8", errors="ignore")
    meta    = _parse_frontmatter(text)
    context = {}

    # Client name
    context["name"] = (
        meta.get("client_name") or
        meta.get("client") or
        "there"
    )

    # Job topic — from file stem or frontmatter
    slug = Path(path).stem
    # Remove date prefix YYYY-MM-DD-
    topic_slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", slug)
    # Remove client name if in slug
    client_slug = re.sub(r"[^a-z0-9]", "", context["name"].lower())
    topic_slug  = re.sub(rf"^{client_slug}-?", "", topic_slug)
    context["topic"] = topic_slug.replace("-", " ") or meta.get("job_title", "the project")

    return context


def generate_followup(proposal: dict, template_idx: int = 0) -> str:
    """Generate a follow-up message for a proposal."""
    ctx = _extract_proposal_context(proposal["path"])
    template = _FOLLOWUP_TEMPLATES[template_idx % len(_FOLLOWUP_TEMPLATES)]
    return template.format(
        name=ctx["name"].split()[0].title(),
        topic=ctx["topic"],
        observation="they've gotten more urgent about [X] — worth a quick look",
    )


# ─── State management ─────────────────────────────────────────────────────────

def _update_proposal_status(path: str, new_status: str) -> None:
    """Update the status field in a proposal's frontmatter."""
    p    = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")

    # Try to update inline
    updated = re.sub(
        r"^(status:\s*).*$",
        f"\\g<1>{new_status}",
        text, count=1, flags=re.MULTILINE
    )
    if updated == text:
        # No status line found — inject after first ---
        updated = text.replace("---\n", f"---\nstatus: {new_status}\n", 1)

    p.write_text(updated, encoding="utf-8")


def _log_followup_to_proposal(path: str, followup_text: str) -> None:
    """Append follow-up log entry to proposal file."""
    p = Path(path)
    entry = (
        f"\n\n---\n## Follow-up Log\n"
        f"**Sent:** {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"```\n{followup_text}\n```\n"
    )
    with p.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def _mark_ghosted(proposal: dict) -> None:
    """Mark a proposal as ghosted in the file and metrics."""
    _update_proposal_status(proposal["path"], "ghosted")
    _increment_metric("ghosted")

    # Log to brain
    slug = proposal["slug"]
    _brain_commit(f"upwork: log outcome — {slug} ghosted (auto, {GHOST_DAYS}d no reply)")


def _increment_metric(key: str) -> None:
    """Increment a counter in metrics.md."""
    if not METRICS_FILE.exists():
        return
    text = METRICS_FILE.read_text(encoding="utf-8", errors="ignore")
    m = re.search(rf"^({key}[:\s]+)(\d+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        new_text = text[:m.start(2)] + str(int(m.group(2)) + 1) + text[m.end(2):]
        METRICS_FILE.write_text(new_text, encoding="utf-8")


def _brain_commit(message: str) -> None:
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(BRAIN), capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(BRAIN), capture_output=True
    )


# ─── Telegram integration ─────────────────────────────────────────────────────

def send_followup_approval(proposal: dict, dry_run: bool = False) -> None:
    """Send Telegram approval request for a follow-up message."""
    from scripts.notify import send_approval, register_approval

    followup_text = generate_followup(proposal)
    approval_id   = f"followup-{proposal['slug']}"
    hours         = proposal["hours_since"]

    body = (
        f"<b>Proposal:</b> {proposal['slug']}\n"
        f"<b>Sent:</b> {hours:.0f}h ago — no reply\n\n"
        f"<b>Proposed follow-up:</b>\n"
        f"<pre>{followup_text[:300]}</pre>\n\n"
        f"<i>Tap Approve to log this follow-up. You send it on Upwork.</i>"
    )

    if not dry_run:
        register_approval(approval_id, "followup", {
            "proposal_path": proposal["path"],
            "proposal_slug": proposal["slug"],
            "followup_text": followup_text,
        })
        send_approval(
            approval_id=approval_id,
            title=f"Follow-up Due — {hours:.0f}h no reply",
            body=body,
            yes_label="✅ Approve text",
            no_label="⏭️ Skip",
        )
    else:
        print(f"[DRY RUN] Would send follow-up approval for {proposal['slug']}")
        print(followup_text)


def process_followup_approvals() -> None:
    """
    Check Telegram for resolved follow-up approvals.
    Approved → update proposal status to followup_sent, log the text.
    Rejected → no change.
    """
    from scripts.notify import poll_approvals, send

    resolved = poll_approvals()
    for item in resolved:
        if item.get("type") != "followup":
            continue

        data   = item.get("data", {})
        action = item.get("action")
        slug   = data.get("proposal_slug", "?")
        path   = data.get("proposal_path", "")
        text   = data.get("followup_text", "")

        if action == "approve" and path:
            _update_proposal_status(path, "followup_sent")
            _log_followup_to_proposal(path, text)
            _brain_commit(f"upwork: log followup — {slug} (text approved, send on Upwork)")

            send(
                f"✅ <b>Follow-up logged:</b> {slug}\n\n"
                f"<pre>{text}</pre>\n\n"
                f"<i>Now go send this on Upwork. Reply timer resets.</i>"
            )
            print(f"[follow_up] Approved + logged: {slug}")
        else:
            print(f"[follow_up] Skipped follow-up for: {slug}")


# ─── Ghost reporting ──────────────────────────────────────────────────────────

def process_ghosts(ghosted: list, dry_run: bool = False) -> None:
    """Auto-mark proposals as ghosted and notify."""
    from scripts.notify import send

    if not ghosted:
        return

    for proposal in ghosted:
        if not proposal.get("ghost_candidate"):
            continue
        if not dry_run:
            _mark_ghosted(proposal)
            send(
                f"👻 <b>Ghosted:</b> {proposal['slug']}\n"
                f"No reply in {GHOST_DAYS}d — marked ghosted, metrics updated."
            )
        else:
            print(f"[DRY RUN] Would ghost: {proposal['slug']} ({proposal['hours_since']:.0f}h)")


# ─── Pattern detection ────────────────────────────────────────────────────────

def _check_patterns(scan: dict) -> None:
    """Check if any outcome pattern threshold is reached and log if so."""
    ghosted_count = len([p for p in scan["ghosted"] if p.get("ghost_candidate")])

    if ghosted_count >= config.PATTERN_THRESHOLD:
        pattern_file = PATTERNS_DIR / "ghost-patterns.md"
        PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
        entry = (
            f"\n## {datetime.now().strftime('%Y-%m-%d')} — Repeat Ghost Signal\n"
            f"{ghosted_count} proposals ghosted in current scan.\n"
            f"Review proposal quality or niche targeting.\n"
        )
        with pattern_file.open("a", encoding="utf-8") as fh:
            fh.write(entry)

        _brain_commit(f"upwork: flag pattern — {ghosted_count} ghosted proposals detected")


# ─── Main run ────────────────────────────────────────────────────────────────

def run(dry_run: bool = False) -> dict:
    """Full follow-up scan run. Returns summary."""
    scan    = scan_proposals()
    summary = {
        "overdue":     len(scan["overdue"]),
        "ghosted":     len([p for p in scan["ghosted"] if p.get("ghost_candidate")]),
        "followed_up": len(scan["followed_up"]),
        "active":      len(scan["active"]),
    }

    # Process ghosts first
    process_ghosts(scan["ghosted"], dry_run=dry_run)

    # Send follow-up approval requests for overdue proposals (max 3 per run)
    for proposal in scan["overdue"][:3]:
        send_followup_approval(proposal, dry_run=dry_run)

    # Check patterns
    _check_patterns(scan)

    return summary


def print_scan_report(scan: dict) -> None:
    """Print a human-readable scan report to stdout."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\nFOLLOW-UP ENGINE SCAN — {now}")
    print("=" * 50)

    def _print_list(label, items, show_hours=True):
        if not items:
            return
        print(f"\n{label} ({len(items)})")
        for p in items:
            h = f"  {p['hours_since']:.0f}h" if show_hours and "hours_since" in p else ""
            tag = " [GHOST]" if p.get("ghost_candidate") else ""
            print(f"  • {p['file']}{h}{tag}")

    _print_list("OVERDUE (follow-up needed)", scan["overdue"])
    _print_list("GHOSTED (7d+ no reply)", scan["ghosted"])
    _print_list("FOLLOWED UP (awaiting reply)", scan["followed_up"])
    _print_list("ACTIVE (within window)", scan["active"])
    _print_list("SKIP (terminal status)", scan["skip"], show_hours=False)
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS Follow-up Engine")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and print but don't send notifications or update files")
    parser.add_argument("--process-approvals", action="store_true",
                        help="Check Telegram for approved follow-ups and log them")
    parser.add_argument("--scan", action="store_true",
                        help="Print scan report only — no notifications")
    args = parser.parse_args()

    if args.process_approvals:
        process_followup_approvals()
        return

    scan = scan_proposals()

    if args.scan:
        print_scan_report(scan)
        return

    summary = run(dry_run=args.dry_run)
    mode = "[DRY RUN] " if args.dry_run else ""
    print(
        f"{mode}Follow-up scan: "
        f"{summary['overdue']} overdue, "
        f"{summary['ghosted']} ghosted, "
        f"{summary['followed_up']} followed-up, "
        f"{summary['active']} active"
    )


if __name__ == "__main__":
    main()

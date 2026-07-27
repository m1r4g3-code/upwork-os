#!/usr/bin/env python3
"""
Upwork OS — Outreach Email Engine

Reads prospect nodes from hephzibah-brain-temp/outreach/prospects/
Generates personalized cold emails in Emmanuel's voice.
Sends Telegram approval request with full email preview.
On approval: sends via Gmail, logs the outreach, resets reply timer.

Prospect states:
  prospect → outreach_sent → replied → call_booked → converted
                           → dead (no reply after GHOST_DAYS)

Usage:
    python scripts/outreach.py --scan                      # show all ready prospects
    python scripts/outreach.py --prospect [name-slug]      # queue one prospect
    python scripts/outreach.py --all                       # queue all 'prospect' state
    python scripts/outreach.py --process-approvals         # send approved emails
    python scripts/outreach.py --follow-up                 # queue follow-ups for sent emails
    python scripts/outreach.py --dry-run --all             # preview without sending
"""

import sys
import re
import json
import base64
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT           = config.ROOT
BRAIN          = config.BRAIN
PROSPECTS_DIR  = BRAIN / "outreach" / "prospects"
OUTREACH_LOG   = BRAIN / "outreach" / "log.md"
FOLLOWUP_HOURS = config.FOLLOWUP_HOURS
GHOST_DAYS     = config.GHOST_DAYS


# ─── Gmail send ───────────────────────────────────────────────────────────────

def _get_gmail_service():
    """Get authenticated Gmail service (reuses email_watcher auth)."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("[outreach] Missing Gmail libraries.", file=sys.stderr)
        print("Run: pip install google-auth-oauthlib google-api-python-client", file=sys.stderr)
        sys.exit(1)

    SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly",
                  "https://www.googleapis.com/auth/gmail.send"]
    token_path = Path(config.GMAIL_TOKEN_FILE)
    creds_path = Path(config.GMAIL_CREDENTIALS_FILE)
    creds      = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds and creds.scopes and not set(SCOPES).issubset(set(creds.scopes)):
            creds = None
            token_path.unlink(missing_ok=True)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print(f"[outreach] credentials.json not found.", file=sys.stderr)
                sys.exit(1)
            flow  = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email via Gmail API. Returns True on success."""
    try:
        service = _get_gmail_service()
        msg     = MIMEText(body, "plain")
        msg["To"]      = to
        msg["Subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True
    except Exception as e:
        print(f"[outreach] Send failed: {e}", file=sys.stderr)
        return False


# ─── Prospect node parsing ────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    meta = {}
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta


def _read_section(text: str, section: str) -> str:
    """Extract a ## Section body from markdown."""
    m = re.search(rf"## {section}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def load_prospects(status_filter: str = "prospect") -> list[dict]:
    """Load all prospect nodes matching status."""
    PROSPECTS_DIR.mkdir(parents=True, exist_ok=True)
    prospects = []
    for f in sorted(PROSPECTS_DIR.glob("*.md")):
        if f.name.startswith("_"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        meta = _parse_frontmatter(text)
        if status_filter and meta.get("status", "prospect") != status_filter:
            continue
        prospects.append({
            "path":    str(f),
            "slug":    f.stem,
            "meta":    meta,
            "context": _read_section(text, "Context"),
            "notes":   _read_section(text, "Outreach Notes"),
        })
    return prospects


def load_prospect_by_slug(slug: str) -> dict | None:
    """Load a single prospect by slug."""
    f = PROSPECTS_DIR / f"{slug}.md"
    if not f.exists():
        # Try partial match
        matches = list(PROSPECTS_DIR.glob(f"*{slug}*.md"))
        if not matches:
            return None
        f = matches[0]
    text = f.read_text(encoding="utf-8", errors="ignore")
    meta = _parse_frontmatter(text)
    return {
        "path":    str(f),
        "slug":    f.stem,
        "meta":    meta,
        "context": _read_section(text, "Context"),
        "notes":   _read_section(text, "Outreach Notes"),
    }


# ─── Email generation ─────────────────────────────────────────────────────────

def generate_subject(prospect: dict) -> str:
    """Generate a non-salesy subject line from prospect context."""
    meta    = prospect["meta"]
    company = meta.get("company", "")
    role    = meta.get("role", "")
    notes   = prospect["notes"]

    # Pull first insight from notes for subject specificity
    first_line = notes.splitlines()[0].strip() if notes else ""

    if first_line and len(first_line) < 60:
        return first_line  # Use the outreach angle directly as subject if short
    if company:
        return f"Quick question — {company}"
    if role:
        return f"Re: {role} — quick thought"
    return "Quick question"


def generate_body(prospect: dict) -> str:
    """
    Generate personalized cold email body in Emmanuel's voice.
    Draws from: prospect context, notes, company/role.

    Voice rules:
    - Direct, slightly senior
    - Opens with THEIR situation, not "I"
    - One specific observation
    - One clear ask (reply or call)
    - 80-120 words
    - No AI slop
    """
    meta    = prospect["meta"]
    name    = meta.get("name", "").split()[0].title()
    company = meta.get("company", "")
    role    = meta.get("role", "")
    context = prospect["context"]
    notes   = prospect["notes"]

    # Extract the core angle from outreach notes
    angle = notes.strip() if notes else context.strip()
    angle_lines = [l.strip() for l in angle.splitlines() if l.strip()]

    # Build the observation — first meaningful line from notes
    observation = angle_lines[0] if angle_lines else f"the work you're doing at {company}"

    # Build additional detail if available
    detail = ""
    if len(angle_lines) > 1:
        detail = f"\n\n{angle_lines[1]}"

    greeting   = f"Hey {name}," if name else "Hey,"
    company_line = f" at {company}" if company else ""

    body = (
        f"{greeting}\n\n"
        f"{observation}{detail}\n\n"
        f"I help businesses{company_line} build the automation and content systems "
        f"that handle the repetitive work — so the team can focus on what actually matters.\n\n"
        f"Worth a quick call to see if there's a fit?\n\n"
        f"Emmanuel"
    )

    # If context is rich, use it to override the generic middle section
    if len(context) > 50:
        context_short = context[:200].strip()
        body = (
            f"{greeting}\n\n"
            f"{observation}\n\n"
            f"{context_short}\n\n"
            f"Worth a quick call?\n\n"
            f"Emmanuel"
        )

    return body.strip()


def generate_followup_body(prospect: dict) -> str:
    """Generate a follow-up email for a prospect who hasn't replied."""
    meta = prospect["meta"]
    name = meta.get("name", "").split()[0].title()
    greeting = f"Hey {name}," if name else "Hey,"

    return (
        f"{greeting}\n\n"
        f"Just circling back on this. Did my last email land okay?\n\n"
        f"Still happy to connect if the timing works.\n\n"
        f"Emmanuel"
    ).strip()


# ─── State management ─────────────────────────────────────────────────────────

def _update_prospect_status(path: str, new_status: str, extra_fields: dict = None) -> None:
    """Update status and optional fields in prospect frontmatter."""
    p    = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")

    updated = re.sub(
        r"^(status:\s*).*$",
        f"\\g<1>{new_status}",
        text, count=1, flags=re.MULTILINE
    )
    if updated == text:
        updated = text.replace("---\n", f"---\nstatus: {new_status}\n", 1)

    if extra_fields:
        for field, value in extra_fields.items():
            pattern = rf"^({field}:\s*).*$"
            replacement = f"\\g<1>{value}"
            new = re.sub(pattern, replacement, updated, count=1, flags=re.MULTILINE)
            if new == updated:
                updated = updated.replace("---\n", f"---\n{field}: {value}\n", 1)
            else:
                updated = new

    p.write_text(updated, encoding="utf-8")


def _append_log_entry(path: str, entry: str) -> None:
    """Append an entry to the prospect's conversation log section."""
    p    = Path(path)
    text = p.read_text(encoding="utf-8", errors="ignore")
    today = datetime.now().strftime("%Y-%m-%d")

    log_entry = f"\n**{today}** — {entry}"

    if "## Conversation Log" in text:
        text = text + log_entry
    else:
        text = text + f"\n\n## Conversation Log\n{log_entry}"

    p.write_text(text, encoding="utf-8")


def _log_to_outreach_log(prospect: dict, subject: str, body: str) -> None:
    """Append to the global outreach log."""
    OUTREACH_LOG.parent.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"\n## {today} — {prospect['slug']}\n"
        f"**To:** {prospect['meta'].get('email', '?')}\n"
        f"**Subject:** {subject}\n\n"
        f"```\n{body}\n```\n"
    )
    with OUTREACH_LOG.open("a", encoding="utf-8") as fh:
        fh.write(entry)


def _brain_commit(message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(BRAIN), capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=str(BRAIN), capture_output=True)


# ─── Telegram approval ────────────────────────────────────────────────────────

def queue_for_approval(prospect: dict, subject: str, body: str,
                        is_followup: bool = False, dry_run: bool = False) -> None:
    """Send Telegram approval card with email preview."""
    from scripts.notify import send_approval, register_approval

    approval_id = f"outreach-{prospect['slug']}-{'fu' if is_followup else 'cold'}"
    label       = "Follow-up" if is_followup else "Cold Email"
    to_email    = prospect["meta"].get("email", "?")
    name        = prospect["meta"].get("name", prospect["slug"])

    body_preview = body[:400] + ("..." if len(body) > 400 else "")

    tg_body = (
        f"<b>To:</b> {name} &lt;{to_email}&gt;\n"
        f"<b>Subject:</b> {subject}\n\n"
        f"<pre>{body_preview}</pre>"
    )

    if not dry_run:
        register_approval(approval_id, "outreach_email", {
            "prospect_path": prospect["path"],
            "prospect_slug": prospect["slug"],
            "to_email":      to_email,
            "subject":       subject,
            "body":          body,
            "is_followup":   is_followup,
        })
        send_approval(
            approval_id=approval_id,
            title=f"📧 {label} — {name}",
            body=tg_body,
            yes_label="✅ Send",
            no_label="❌ Skip",
        )
        print(f"[outreach] Approval queued: {name} ({to_email})")
    else:
        print(f"\n[DRY RUN] {label} → {name} <{to_email}>")
        print(f"Subject: {subject}")
        print(f"---\n{body}\n---")


def process_outreach_approvals() -> None:
    """Check Telegram for approved outreach emails and send them."""
    from scripts.notify import poll_approvals, send

    resolved = poll_approvals()
    for item in resolved:
        if item.get("type") != "outreach_email":
            continue

        data       = item.get("data", {})
        action     = item.get("action")
        slug       = data.get("prospect_slug", "?")
        path       = data.get("prospect_path", "")
        to_email   = data.get("to_email", "")
        subject    = data.get("subject", "")
        body       = data.get("body", "")
        is_followup = data.get("is_followup", False)

        if action == "approve" and to_email:
            success = send_email(to_email, subject, body)
            if success:
                today = datetime.now().strftime("%Y-%m-%d")
                status = "outreach_sent" if not is_followup else "followup_sent"
                _update_prospect_status(path, status, {"outreach_sent_on": today})
                _append_log_entry(path, f"Email sent — '{subject}'")
                _log_to_outreach_log({"slug": slug, "meta": {"email": to_email}}, subject, body)
                _brain_commit(f"outreach: log send — {slug} ({status})")
                send(f"✅ <b>Email sent:</b> {slug}\n<i>{subject}</i>")
                print(f"[outreach] Sent: {slug}")
            else:
                send(f"❌ <b>Send failed:</b> {slug} — check Gmail credentials")
        else:
            print(f"[outreach] Skipped: {slug}")


# ─── Main flows ───────────────────────────────────────────────────────────────

def run_all(dry_run: bool = False) -> None:
    """Queue cold emails for all prospects in 'prospect' state."""
    prospects = load_prospects(status_filter="prospect")
    if not prospects:
        print("[outreach] No prospects in 'prospect' state.")
        return
    for p in prospects:
        if not p["meta"].get("email"):
            print(f"[outreach] Skipping {p['slug']} — no email address in node")
            continue
        subject = generate_subject(p)
        body    = generate_body(p)
        queue_for_approval(p, subject, body, dry_run=dry_run)


def run_prospect(slug: str, dry_run: bool = False) -> None:
    """Queue a cold email for a specific prospect."""
    p = load_prospect_by_slug(slug)
    if not p:
        print(f"[outreach] Prospect not found: {slug}")
        return
    if not p["meta"].get("email"):
        print(f"[outreach] No email address in prospect node for {slug}")
        return
    subject = generate_subject(p)
    body    = generate_body(p)
    queue_for_approval(p, subject, body, dry_run=dry_run)


def run_followups(dry_run: bool = False) -> None:
    """Queue follow-up emails for prospects in 'outreach_sent' state past 72h."""
    prospects = load_prospects(status_filter="outreach_sent")
    queued = 0
    for p in prospects:
        sent_on = p["meta"].get("outreach_sent_on")
        if not sent_on:
            continue
        try:
            sent_dt = datetime.strptime(sent_on, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            hours_since = (datetime.now(timezone.utc) - sent_dt).total_seconds() / 3600
        except ValueError:
            continue

        if hours_since < FOLLOWUP_HOURS:
            continue
        if not p["meta"].get("email"):
            continue

        subject = f"Re: {generate_subject(p)}"
        body    = generate_followup_body(p)
        queue_for_approval(p, subject, body, is_followup=True, dry_run=dry_run)
        queued += 1

    if not queued:
        print(f"[outreach] No follow-ups due (threshold: {FOLLOWUP_HOURS}h)")


def scan_prospects_report() -> None:
    """Print a status report of all prospects."""
    all_statuses = ["prospect", "outreach_sent", "replied", "call_booked", "converted", "dead"]
    print(f"\nOUTREACH PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    for status in all_statuses:
        items = load_prospects(status_filter=status)
        if not items:
            continue
        print(f"\n{status.upper()} ({len(items)})")
        for p in items:
            email = p["meta"].get("email", "no email")
            name  = p["meta"].get("name", p["slug"])
            company = p["meta"].get("company", "")
            tag = f" @ {company}" if company else ""
            sent_on = p["meta"].get("outreach_sent_on", "")
            sent_tag = f" | sent {sent_on}" if sent_on else ""
            print(f"  • {name}{tag} <{email}>{sent_tag}")
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS Outreach Engine")
    parser.add_argument("--scan", action="store_true",
                        help="Print prospect pipeline status")
    parser.add_argument("--prospect", metavar="SLUG",
                        help="Queue cold email for a specific prospect")
    parser.add_argument("--all", action="store_true",
                        help="Queue cold emails for all 'prospect' state nodes")
    parser.add_argument("--follow-up", action="store_true",
                        help="Queue follow-ups for outreach_sent prospects past 72h")
    parser.add_argument("--process-approvals", action="store_true",
                        help="Check Telegram for approved emails and send them")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview emails without sending or queueing")
    args = parser.parse_args()

    if args.process_approvals:
        process_outreach_approvals()
        return

    if args.scan:
        scan_prospects_report()
        return

    if args.follow_up:
        run_followups(dry_run=args.dry_run)
        return

    if args.prospect:
        run_prospect(args.prospect, dry_run=args.dry_run)
        return

    if args.all:
        run_all(dry_run=args.dry_run)
        return

    parser.print_help()


if __name__ == "__main__":
    main()

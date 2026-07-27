#!/usr/bin/env python3
"""
Upwork OS — Email Watcher (Gmail API)

Runs every 30 minutes via Task Scheduler.
Detects and routes two email types:
  1. Upwork job alert emails → job_watcher.py for qualifying
  2. Client replies to proposals → follow-up engine + Telegram alert

Requires: pip install google-auth-oauthlib google-api-python-client

First run: opens browser for Gmail OAuth authorization.
Subsequent runs: uses token.json silently.

Usage:
    python scripts/email_watcher.py
    python scripts/email_watcher.py --dry-run      # scan only, no notifications
    python scripts/email_watcher.py --since 24h    # only look at last 24h of email
"""

import sys
import json
import re
import argparse
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

BRAIN         = config.BRAIN
PROPOSALS_DIR = config.PROPOSALS_DIR
STATE_FILE    = config.ROOT / "data" / "email_watcher_state.json"

# ─── Gmail auth ───────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_gmail_service():
    """Authenticate and return Gmail API service. Opens browser on first run."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("[email_watcher] Missing Gmail libraries.", file=sys.stderr)
        print("Run: pip install google-auth-oauthlib google-api-python-client", file=sys.stderr)
        sys.exit(1)

    creds     = None
    token_path = Path(config.GMAIL_TOKEN_FILE)
    creds_path = Path(config.GMAIL_CREDENTIALS_FILE)

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print(f"[email_watcher] credentials.json not found at {creds_path}", file=sys.stderr)
                print("See config.example.py for setup instructions.", file=sys.stderr)
                sys.exit(1)
            flow  = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ─── State management ─────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_history_id": None, "processed_message_ids": []}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ─── Email parsers ────────────────────────────────────────────────────────────

def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(msg_data: dict) -> str:
    """Extract plain text body from Gmail message payload."""
    payload = msg_data.get("payload", {})

    def extract(part):
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
        for sub in part.get("parts", []):
            result = extract(sub)
            if result:
                return result
        return ""

    return extract(payload)


def _is_upwork_job_alert(sender: str, subject: str) -> bool:
    return (config.UPWORK_ALERT_SENDER in sender and
            config.UPWORK_ALERT_SUBJECT_CONTAINS.lower() in subject.lower())


def _is_client_reply(sender: str, subject: str, body: str) -> bool:
    """
    Detect if this is a client replying to a proposal.
    Checks: Upwork message notification OR direct email reply matching a known proposal.
    """
    # Upwork message notification
    if "upwork.com" in sender and "message" in subject.lower():
        return True
    # Direct email reply (off-platform contact)
    known_emails = _get_known_client_emails()
    return any(email.lower() in sender.lower() for email in known_emails if email)


def _get_known_client_emails() -> list[str]:
    """Read all client nodes and extract known email addresses."""
    emails = []
    if not config.CLIENTS_DIR.exists():
        return emails
    for f in config.CLIENTS_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"contact_email:\s*[\"']?([^\s\"']+@[^\s\"']+)[\"']?", text)
        if m:
            emails.append(m.group(1).strip())
    return emails


# ─── Job alert processing ─────────────────────────────────────────────────────

def _parse_job_links_from_alert(body: str) -> list[str]:
    """Extract Upwork job URLs from a job alert email."""
    # Upwork job URLs in alert emails
    urls = re.findall(r"https://www\.upwork\.com/jobs/[^\s\">)]+", body)
    # Deduplicate and clean
    seen = set()
    clean = []
    for u in urls:
        u = u.rstrip(".,)")
        if u not in seen:
            seen.add(u)
            clean.append(u)
    return clean


def _process_job_alert(body: str, dry_run: bool = False) -> int:
    """Pass job URLs from alert email to job_watcher. Returns count processed."""
    urls = _parse_job_links_from_alert(body)
    if not urls:
        return 0

    from scripts import job_watcher
    count = 0
    for url in urls[:5]:    # cap at 5 per email
        qualified = job_watcher.qualify_and_notify(url, dry_run=dry_run)
        if qualified:
            count += 1
    return count


# ─── Client reply processing ──────────────────────────────────────────────────

def _process_client_reply(sender: str, subject: str, body: str,
                           received_date: str, dry_run: bool = False) -> None:
    """Alert Emmanuel when a client replies to a proposal."""
    from scripts.notify import send, register_approval, send_approval

    # Try to match to a known proposal
    proposal_context = _match_proposal(sender, subject)
    client_name = _extract_client_name(sender, subject, proposal_context)

    snippet = body[:300].replace("\n", " ").strip()

    alert_text = (
        f"📨 <b>CLIENT REPLY</b>\n\n"
        f"<b>From:</b> {client_name}\n"
        f"<b>Subject:</b> {subject}\n\n"
        f"<b>Preview:</b>\n{snippet}...\n\n"
        f"<b>Received:</b> {received_date}"
    )

    if proposal_context:
        alert_text += f"\n\n<b>Matched proposal:</b> {proposal_context}"

    alert_text += "\n\n<i>Open Gmail to reply. Run /prep-call if they want a meeting.</i>"

    if not dry_run:
        send(alert_text)
        # Log the event — reset 72h timer
        _log_reply_event(sender, subject, received_date)
    else:
        print(f"[DRY RUN] Would alert: reply from {client_name}")


def _match_proposal(sender: str, subject: str) -> str | None:
    """Try to match an incoming email to a known sent proposal."""
    if not PROPOSALS_DIR.exists():
        return None
    for f in PROPOSALS_DIR.glob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        # Match by client email or subject keywords
        if sender.lower() in text.lower():
            return f.name
        # Extract client name from proposal and check subject
        m = re.search(r"client:\s*([^\n]+)", text, re.IGNORECASE)
        if m and m.group(1).strip().lower() in subject.lower():
            return f.name
    return None


def _extract_client_name(sender: str, subject: str, proposal_file: str | None) -> str:
    """Best-effort client name extraction."""
    if proposal_file:
        parts = proposal_file.replace(".md", "").split("-")
        if len(parts) >= 4:
            return parts[3].replace("-", " ").title()
    # Extract from email address
    m = re.match(r"([^<@]+)", sender)
    if m:
        return m.group(1).strip()
    return sender


def _log_reply_event(sender: str, subject: str, received_date: str) -> None:
    """Write a reply event to the state file so heartbeat knows reply was received."""
    state = _load_state()
    events = state.get("reply_events", [])
    events.append({
        "sender": sender,
        "subject": subject,
        "received": received_date,
        "logged_at": datetime.now().isoformat(),
    })
    state["reply_events"] = events[-50:]   # keep last 50
    _save_state(state)


# ─── Main scan loop ───────────────────────────────────────────────────────────

def _build_query(since_hours: int) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    after  = int(cutoff.timestamp())
    return f"after:{after} in:inbox"


def run(dry_run: bool = False, since_hours: int = 1) -> dict:
    """
    Main scan. Returns summary dict.
    since_hours: how far back to scan (default 1h — runs every 30min so 1h gives overlap)
    """
    service = _get_gmail_service()
    query   = _build_query(since_hours)
    summary = {"job_alerts": 0, "client_replies": 0, "errors": 0}

    try:
        results = service.users().messages().list(
            userId="me", q=query, maxResults=20
        ).execute()
    except Exception as e:
        print(f"[email_watcher] Gmail list error: {e}", file=sys.stderr)
        return summary

    messages = results.get("messages", [])
    state    = _load_state()
    processed = set(state.get("processed_message_ids", []))

    for msg_ref in messages:
        msg_id = msg_ref["id"]
        if msg_id in processed:
            continue

        try:
            msg_data = service.users().messages().get(
                userId="me", id=msg_id, format="full"
            ).execute()
        except Exception as e:
            print(f"[email_watcher] Fetch error for {msg_id}: {e}", file=sys.stderr)
            summary["errors"] += 1
            continue

        headers  = msg_data.get("payload", {}).get("headers", [])
        sender   = _get_header(headers, "From")
        subject  = _get_header(headers, "Subject")
        date_str = _get_header(headers, "Date")
        body     = _decode_body(msg_data)

        if _is_upwork_job_alert(sender, subject):
            count = _process_job_alert(body, dry_run=dry_run)
            summary["job_alerts"] += count
            print(f"[email_watcher] Job alert → {count} jobs qualified")
        elif _is_client_reply(sender, subject, body):
            _process_client_reply(sender, subject, body, date_str, dry_run=dry_run)
            summary["client_replies"] += 1
            print(f"[email_watcher] Client reply from {sender}")

        processed.add(msg_id)

    # Persist processed IDs (keep last 500 to avoid unbounded growth)
    state["processed_message_ids"] = list(processed)[-500:]
    _save_state(state)

    return summary


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS Email Watcher")
    parser.add_argument("--dry-run", action="store_true",
                        help="Scan and print but don't send notifications")
    parser.add_argument("--since", default="1h",
                        help="How far back to scan, e.g. 1h, 6h, 24h (default: 1h)")
    args = parser.parse_args()

    since_hours = 1
    if args.since.endswith("h"):
        try:
            since_hours = int(args.since[:-1])
        except ValueError:
            pass

    print(f"[email_watcher] Scanning last {since_hours}h of Gmail...")
    summary = run(dry_run=args.dry_run, since_hours=since_hours)
    print(f"[email_watcher] Done — job alerts: {summary['job_alerts']}, "
          f"client replies: {summary['client_replies']}, errors: {summary['errors']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Create Gmail drafts without sending.
Uses a separate token file so email_watcher.py is unaffected.

Usage:
    python scripts/draft.py --to "support@upwork.com" --subject "..." --body "..."
    python scripts/draft.py --file path/to/email.txt  (first line = subject)
"""

import sys
import base64
import argparse
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

ROOT        = config.ROOT
CREDS_PATH  = ROOT / "credentials.json"
TOKEN_PATH  = ROOT / ".gmail_token.json"  # shared with email_watcher.py

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
]


def _get_service():
    try:
        from google.oauth2.credentials  import Credentials
        from google_auth_oauthlib.flow  import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery  import build
    except ImportError:
        print("[draft] Missing deps: pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if creds and creds.scopes and not set(SCOPES).issubset(set(creds.scopes)):
            creds = None
            TOKEN_PATH.unlink(missing_ok=True)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_PATH.exists():
                print(f"[draft] credentials.json not found at {CREDS_PATH}")
                sys.exit(1)
            flow  = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def create_draft(to: str, subject: str, body: str, sender: str = "me") -> str:
    service = _get_service()

    msg = MIMEText(body, "plain")
    msg["to"]      = to
    msg["subject"] = subject

    raw     = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft   = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}}
    ).execute()

    draft_id = draft["id"]
    print(f"[draft] Created draft ID: {draft_id}")
    print(f"[draft] To: {to} | Subject: {subject}")
    return draft_id


def main():
    parser = argparse.ArgumentParser(description="Create Gmail draft")
    parser.add_argument("--to",      required=True, help="Recipient email")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body",    required=True, help="Email body text")
    args = parser.parse_args()

    create_draft(to=args.to, subject=args.subject, body=args.body)


if __name__ == "__main__":
    main()

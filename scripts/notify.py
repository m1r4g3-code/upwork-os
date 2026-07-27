#!/usr/bin/env python3
"""
Upwork OS — Telegram notification and approval utility.

All Tier 3 scripts send through this module.
Handles: message sending, approval requests, polling for replies.

Usage:
    python scripts/notify.py "message text"        # send a message
    python scripts/notify.py --get-chat-id         # find your chat ID
    python scripts/notify.py --test                # test connection
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import config
    TOKEN   = config.TELEGRAM_BOT_TOKEN
    CHAT_ID = str(config.TELEGRAM_CHAT_ID)
    APPROVALS_FILE = config.APPROVALS_FILE
except ImportError:
    TOKEN   = ""
    CHAT_ID = ""
    APPROVALS_FILE = Path(__file__).parent.parent / "data" / "pending_approvals.json"


BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# ─── Core API calls ───────────────────────────────────────────────────────────

def _api(method: str, payload: dict) -> dict | None:
    """Make a Telegram Bot API call. Returns response dict or None on error."""
    if not TOKEN:
        print("[notify] No TELEGRAM_BOT_TOKEN configured in config.py", file=sys.stderr)
        return None
    url  = f"{BASE_URL}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data,
                                   headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"[notify] HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[notify] Error: {e}", file=sys.stderr)
        return None


def _get_updates(offset: int = 0) -> list[dict]:
    """Fetch pending updates from Telegram (for approval polling)."""
    resp = _api("getUpdates", {"offset": offset, "timeout": 0, "limit": 50})
    if resp and resp.get("ok"):
        return resp.get("result", [])
    return []


# ─── Public send functions ────────────────────────────────────────────────────

def send(text: str, parse_mode: str = "HTML") -> bool:
    """Send a plain message to Emmanuel's Telegram."""
    if not CHAT_ID:
        print(f"[notify] No CHAT_ID — would send:\n{text}", file=sys.stderr)
        return False
    resp = _api("sendMessage", {
        "chat_id":    CHAT_ID,
        "text":       text,
        "parse_mode": parse_mode,
    })
    return bool(resp and resp.get("ok"))


def send_approval(approval_id: str, title: str, body: str,
                   yes_label: str = "✅ Yes", no_label: str = "❌ No") -> bool:
    """
    Send an approval request with inline Yes/No buttons.
    Emmanuel taps a button; next poll run processes the callback.
    """
    keyboard = {
        "inline_keyboard": [[
            {"text": yes_label, "callback_data": f"approve:{approval_id}"},
            {"text": no_label,  "callback_data": f"reject:{approval_id}"},
        ]]
    }
    resp = _api("sendMessage", {
        "chat_id":      CHAT_ID,
        "text":         f"<b>{title}</b>\n\n{body}",
        "parse_mode":   "HTML",
        "reply_markup": keyboard,
    })
    return bool(resp and resp.get("ok"))


def send_brief(sections: list[tuple[str, str]]) -> bool:
    """
    Send a formatted morning brief.
    sections = [("TITLE", "body text"), ...]
    """
    lines = ["<b>🟢 UPWORK OS — MORNING BRIEF</b>",
             f"<i>{datetime.now().strftime('%Y-%m-%d  %H:%M WAT')}</i>", ""]
    for title, body in sections:
        lines.append(f"<b>▶ {title}</b>")
        lines.append(body)
        lines.append("")
    return send("\n".join(lines))


# ─── Approval state management ────────────────────────────────────────────────

def _load_approvals() -> list[dict]:
    path = Path(APPROVALS_FILE)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_approvals(items: list[dict]) -> None:
    path = Path(APPROVALS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")


def register_approval(approval_id: str, approval_type: str, data: dict) -> None:
    """Register a pending approval in the state store."""
    items = _load_approvals()
    items = [i for i in items if i["id"] != approval_id]   # dedupe
    items.append({
        "id":      approval_id,
        "type":    approval_type,
        "created": datetime.now().isoformat(),
        "data":    data,
        "status":  "pending",
    })
    _save_approvals(items)


def poll_approvals() -> list[dict]:
    """
    Check Telegram for button callbacks. Return list of resolved approvals.
    Each resolved item: {"id": "...", "type": "...", "action": "approve"|"reject", "data": {...}}
    """
    items    = _load_approvals()
    pending  = {i["id"]: i for i in items if i["status"] == "pending"}
    if not pending:
        return []

    updates  = _get_updates()
    resolved = []

    # Track highest update_id to acknowledge
    max_update_id = 0

    for update in updates:
        update_id = update.get("update_id", 0)
        max_update_id = max(max_update_id, update_id)

        callback = update.get("callback_query")
        if not callback:
            continue

        data_str = callback.get("data", "")
        if ":" not in data_str:
            continue

        action, approval_id = data_str.split(":", 1)
        if approval_id not in pending:
            continue

        item   = pending[approval_id]
        action = "approve" if action == "approve" else "reject"

        # Acknowledge the button press
        _api("answerCallbackQuery", {
            "callback_query_id": callback["id"],
            "text": "Got it!" if action == "approve" else "Skipped.",
        })

        item["status"] = action + "d"
        item["action"] = action
        item["resolved_at"] = datetime.now().isoformat()
        resolved.append(item)

    if resolved:
        # Persist updated statuses
        all_items = _load_approvals()
        resolved_ids = {r["id"] for r in resolved}
        for i in all_items:
            if i["id"] in resolved_ids:
                match = next(r for r in resolved if r["id"] == i["id"])
                i.update({"status": match["status"], "action": match.get("action"),
                           "resolved_at": match.get("resolved_at")})
        _save_approvals(all_items)

        # Advance the update offset so we don't reprocess
        if max_update_id:
            _api("getUpdates", {"offset": max_update_id + 1, "limit": 1})

    return resolved


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Upwork OS Telegram notifier")
    parser.add_argument("message", nargs="?", help="Message to send")
    parser.add_argument("--get-chat-id", action="store_true",
                        help="Print your Telegram chat ID (message the bot first)")
    parser.add_argument("--test", action="store_true", help="Send test message")
    parser.add_argument("--poll", action="store_true",
                        help="Poll and print pending approvals")
    args = parser.parse_args()

    if args.get_chat_id:
        updates = _get_updates()
        if not updates:
            print("No messages found. Send any message to your bot first, then re-run.")
        else:
            for u in updates:
                msg = u.get("message", {})
                chat = msg.get("chat", {})
                if chat:
                    print(f"Chat ID: {chat['id']}  (name: {chat.get('first_name','')} {chat.get('last_name','')})")
        return

    if args.test:
        ok = send("✅ <b>Upwork OS</b> — Telegram connection confirmed.")
        print("Sent OK" if ok else "Failed — check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in config.py")
        return

    if args.poll:
        resolved = poll_approvals()
        if resolved:
            for r in resolved:
                print(f"[{r['action'].upper()}] {r['id']} — {r['type']}")
        else:
            print("No pending approvals resolved.")
        return

    if args.message:
        ok = send(args.message)
        print("Sent." if ok else "Failed.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

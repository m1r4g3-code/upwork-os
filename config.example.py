# config.example.py — copy this to config.py and fill in your credentials
# config.py is gitignored — never commit it

# ── Telegram ────────────────────────────────────────────────────────────────
# Create bot: open Telegram → @BotFather → /newbot → follow prompts
# Get token from BotFather response
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# ── Google Maps / Places API ─────────────────────────────────────────────────
# Same Google Cloud project as Gmail (starlit-ship-469523-d7)
# 1. console.cloud.google.com → Select project → APIs & Services → Enable APIs
# 2. Enable: "Places API" and "Maps JavaScript API"
# 3. APIs & Services → Credentials → + CREATE CREDENTIALS → API Key
# 4. Paste below. Free tier: $200/month credit (covers ~1,000 searches)
GOOGLE_MAPS_API_KEY = ""

# ── Anthropic API (optional) ─────────────────────────────────────────────────
# If set, prospect emails are AI-written from website context (much better copy).
# If blank, template-based emails are used instead.
# Get key: console.anthropic.com → API Keys
ANTHROPIC_API_KEY = ""

# After creating the bot: message it once, then run:
#   python scripts/notify.py --get-chat-id
# to find your chat ID
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"

# ── Gmail API ────────────────────────────────────────────────────────────────
# 1. Go to console.cloud.google.com
# 2. Create project → Enable Gmail API
# 3. Credentials → OAuth 2.0 → Desktop app → Download JSON → save as credentials.json
# 4. First run of email_watcher.py will open browser to authorize
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE = "token.json"

# Gmail label/sender filters
UPWORK_ALERT_SENDER = "noreply@upwork.com"
UPWORK_ALERT_SUBJECT_CONTAINS = "Jobs matching"   # Upwork job alert emails
CLIENT_REPLY_LABEL = "INBOX"                        # Where client replies land

# ── Upwork OS Paths ──────────────────────────────────────────────────────────
import os
from pathlib import Path

ROOT  = Path(__file__).parent
BRAIN = ROOT / "hephzibah-brain-temp"

PROPOSALS_DIR    = BRAIN / "upwork" / "proposals" / "sent"
CLIENTS_DIR      = BRAIN / "upwork" / "clients" / "active"
JOBS_ARCHIVE_DIR = BRAIN / "upwork" / "jobs" / "archive"
PATTERNS_DIR     = BRAIN / "upwork" / "market" / "patterns"
METRICS_FILE     = BRAIN / "upwork" / "performance" / "metrics.md"
QUEUE_FILE       = BRAIN / "_QUEUE.md"
PIPELINE_FILE    = BRAIN / "_PIPELINE.md"

# Approval state store (gitignored)
APPROVALS_FILE   = ROOT / "data" / "pending_approvals.json"

# ── Job Qualifying Thresholds ────────────────────────────────────────────────
BID_THRESHOLD          = 80    # Auto-notify on scores >= this
WATCHLIST_THRESHOLD    = 65    # Log but don't notify below this
OODA_WINDOW_MINUTES    = 60    # Flag as MOVE NOW if job posted within this window

# ── Follow-up Timers ─────────────────────────────────────────────────────────
FOLLOWUP_HOURS   = 72    # Hours before follow-up is flagged
GHOST_DAYS       = 7     # Days before proposal is marked ghosted
PATTERN_THRESHOLD = 3    # Number of same-outcome proposals before pattern is logged

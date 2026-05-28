"""
config.py -- Shared path constants for all scripts.

Import from here instead of re-deriving ROOT in each script.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "hephzibah-brain-temp"
DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"
SOURCES_JOBS = SOURCES_DIR / "jobs"
SOURCES_PROPOSALS = SOURCES_DIR / "proposals"
SOURCES_CONVERSATIONS = SOURCES_DIR / "conversations"

DB_PATH = DATA_DIR / "proposals.db"
SESSION_FILE = DATA_DIR / "upwork_session.json"

JOBS_ARCHIVE = BRAIN / "upwork" / "jobs" / "archive"
PROPOSALS_SENT = BRAIN / "upwork" / "proposals" / "sent"
PROPOSALS_BEST = BRAIN / "upwork" / "proposals" / "best"
CLIENTS_ACTIVE = BRAIN / "upwork" / "clients" / "active"

VOICE_GUIDE = BRAIN / "upwork" / "identity" / "voice.md"
METRICS = BRAIN / "upwork" / "performance" / "metrics.md"

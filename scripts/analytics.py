"""
analytics.py -- Proposal performance analytics.

Queries the proposals database and generates performance reports.
Called by /strategy-review and /daily-brief commands.

Usage:
  python scripts/analytics.py --init            # create database tables
  python scripts/analytics.py --report          # weekly performance report
  python scripts/analytics.py --log-proposal <json>  # log a new proposal
  python scripts/analytics.py --log-outcome <slug> <status>  # log outcome
  python scripts/analytics.py --metrics         # quick metrics summary
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, date as date_type

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "proposals.db"

SCHEMA_VERSION = 2


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _apply_migrations(conn: sqlite3.Connection, from_version: int) -> None:
    """Apply schema migrations from from_version to SCHEMA_VERSION."""
    if from_version < 2:
        # v1 -> v2: add indexes for common query patterns
        conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_proposals_sent_date ON proposals (sent_date);
        CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals (status);
        CREATE INDEX IF NOT EXISTS idx_proposals_niche ON proposals (niche);
        """)
        conn.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (2, datetime.now().isoformat()),
        )
        print("Schema migrated to v2: added indexes")


def init_db() -> None:
    """Create database tables and apply any pending migrations."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            job_title TEXT,
            job_url TEXT,
            niche TEXT,
            sent_date TEXT,
            status TEXT DEFAULT 'sent',
            composite_score INTEGER,
            voice_score INTEGER,
            diagnosis_score INTEGER,
            hook_score INTEGER,
            cta_score INTEGER,
            bid_amount TEXT,
            connects_spent INTEGER DEFAULT 0,
            reply_hours REAL,
            outcome TEXT,
            learning TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_slug TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (proposal_slug) REFERENCES proposals(slug)
        );

        CREATE TABLE IF NOT EXISTS metrics_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start TEXT NOT NULL,
            proposals_sent INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            interviews INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            revenue_usd REAL DEFAULT 0,
            connects_spent INTEGER DEFAULT 0,
            niche TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS calibrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            job_slug TEXT,
            machine_score INTEGER,
            emmanuel_score INTEGER,
            delta INTEGER
        );
        """)

        row = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
        current_version = row["v"]
        if current_version is None:
            # Fresh database -- seed indexes and record version
            conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_proposals_sent_date ON proposals (sent_date);
            CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals (status);
            CREATE INDEX IF NOT EXISTS idx_proposals_niche ON proposals (niche);
            """)
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now().isoformat()),
            )
            print(f"Database initialized at schema v{SCHEMA_VERSION}: {DB_PATH}")
        elif current_version < SCHEMA_VERSION:
            _apply_migrations(conn, current_version)


def log_proposal(data: dict) -> None:
    """Log a newly sent proposal."""
    slug = data.get("slug") or data.get("job_slug", f"proposal-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

    with get_conn() as conn:
        try:
            conn.execute("""
                INSERT INTO proposals (slug, job_title, job_url, niche, sent_date, composite_score,
                    voice_score, diagnosis_score, hook_score, cta_score, bid_amount, connects_spent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                slug,
                data.get("job_title", ""),
                data.get("job_url", ""),
                data.get("niche", ""),
                data.get("sent_date", datetime.now().date().isoformat()),
                data.get("composite_score"),
                data.get("voice_score"),
                data.get("diagnosis_score"),
                data.get("hook_score"),
                data.get("cta_score"),
                data.get("bid_amount", ""),
                data.get("connects_spent", 0),
            ))
            conn.execute("""
                INSERT INTO outcomes (proposal_slug, event_type, event_date, notes)
                VALUES (?, 'sent', ?, ?)
            """, (slug, datetime.now().date().isoformat(), "Proposal submitted"))
            print(f"Logged proposal: {slug}")
        except sqlite3.IntegrityError:
            print(f"Proposal '{slug}' already exists. Use --log-outcome to update.")


def log_outcome(slug: str, status: str, notes: str = "") -> None:
    """Log an outcome event for a proposal."""
    valid_statuses = ["replied", "interviewed", "won", "lost", "ghosted"]
    if status not in valid_statuses:
        print(f"ERROR: Status must be one of: {valid_statuses}", file=sys.stderr)
        sys.exit(1)

    with get_conn() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE slug = ?", (slug,)).fetchone()
        if not proposal:
            print(f"ERROR: Proposal '{slug}' not found.", file=sys.stderr)
            sys.exit(1)

        conn.execute("UPDATE proposals SET status = ? WHERE slug = ?", (status, slug))

        if status == "replied":
            sent_str = proposal["sent_date"]
            if sent_str:
                try:
                    try:
                        sent_dt = datetime.fromisoformat(sent_str)
                    except ValueError:
                        sent_dt = datetime.combine(date_type.fromisoformat(sent_str), datetime.min.time())
                    reply_hours = round((datetime.now() - sent_dt).total_seconds() / 3600, 1)
                    conn.execute("UPDATE proposals SET reply_hours = ? WHERE slug = ?", (reply_hours, slug))
                except (ValueError, TypeError):
                    pass

        conn.execute("""
            INSERT INTO outcomes (proposal_slug, event_type, event_date, notes)
            VALUES (?, ?, ?, ?)
        """, (slug, status, datetime.now().date().isoformat(), notes))
        print(f"Outcome logged: {slug} -> {status}")


def quick_metrics() -> dict:
    """Get current performance metrics summary."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) as n FROM proposals").fetchone()["n"]
        replies = conn.execute("SELECT COUNT(*) as n FROM proposals WHERE status IN ('replied', 'interviewed', 'won')").fetchone()["n"]
        wins = conn.execute("SELECT COUNT(*) as n FROM proposals WHERE status = 'won'").fetchone()["n"]

        # This week
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
        week_proposals = conn.execute(
            "SELECT COUNT(*) as n FROM proposals WHERE sent_date >= ?", (week_start,)
        ).fetchone()["n"]

        # By niche
        niche_data = conn.execute("""
            SELECT niche, COUNT(*) as proposals,
                   SUM(CASE WHEN status IN ('replied','interviewed','won') THEN 1 ELSE 0 END) as replies,
                   SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins
            FROM proposals
            WHERE niche != ''
            GROUP BY niche
        """).fetchall()

    reply_rate = f"{replies/total*100:.0f}%" if total > 0 else "--"
    win_rate = f"{wins/total*100:.0f}%" if total > 0 else "--"

    return {
        "total_proposals": total,
        "total_replies": replies,
        "total_wins": wins,
        "reply_rate": reply_rate,
        "win_rate": win_rate,
        "this_week_proposals": week_proposals,
        "by_niche": [dict(row) for row in niche_data],
    }


def weekly_report() -> None:
    """Generate and print a weekly performance report."""
    metrics = quick_metrics()

    print("\n" + "="*55)
    print("UPWORK OS -- WEEKLY PERFORMANCE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*55)

    print(f"\nOVERALL PERFORMANCE")
    print(f"  Total proposals sent: {metrics['total_proposals']}")
    print(f"  Total replies:        {metrics['total_replies']} ({metrics['reply_rate']})")
    print(f"  Total wins:           {metrics['total_wins']} ({metrics['win_rate']})")
    print(f"  This week:            {metrics['this_week_proposals']} proposals")

    if metrics["by_niche"]:
        print(f"\nBY NICHE")
        for row in metrics["by_niche"]:
            niche = row["niche"] or "Untagged"
            reply_rate = f"{row['replies']/row['proposals']*100:.0f}%" if row["proposals"] > 0 else "--"
            win_rate = f"{row['wins']/row['proposals']*100:.0f}%" if row["proposals"] > 0 else "--"
            print(f"  {niche:<25} {row['proposals']:>3} proposals | {reply_rate:>4} reply rate | {win_rate:>4} win rate")

    with get_conn() as conn:
        # Recent proposals
        recent = conn.execute("""
            SELECT slug, job_title, sent_date, status, composite_score
            FROM proposals ORDER BY sent_date DESC LIMIT 5
        """).fetchall()

    if recent:
        print(f"\nRECENT PROPOSALS")
        for p in recent:
            score_str = f"score:{p['composite_score']}" if p['composite_score'] else "no score"
            print(f"  [{p['status']:<12}] {p['job_title'][:35]:<35} {score_str}")

    print()


def print_metrics_json() -> None:
    metrics = quick_metrics()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or "--help" in args:
        print(__doc__)
        sys.exit(0)

    if "--init" in args:
        init_db()

    elif "--report" in args:
        if not DB_PATH.exists():
            init_db()
        weekly_report()

    elif "--metrics" in args:
        if not DB_PATH.exists():
            init_db()
        print_metrics_json()

    elif "--log-proposal" in args and len(args) >= 2:
        if not DB_PATH.exists():
            init_db()
        idx = args.index("--log-proposal") + 1
        try:
            data = json.loads(args[idx])
        except (json.JSONDecodeError, IndexError):
            print("ERROR: Provide proposal data as JSON string", file=sys.stderr)
            sys.exit(1)
        log_proposal(data)

    elif "--log-outcome" in args and len(args) >= 3:
        if not DB_PATH.exists():
            init_db()
        idx = args.index("--log-outcome")
        slug = args[idx + 1]
        status = args[idx + 2]
        notes = args[idx + 3] if len(args) > idx + 3 else ""
        log_outcome(slug, status, notes)

    else:
        print(__doc__)
        sys.exit(1)

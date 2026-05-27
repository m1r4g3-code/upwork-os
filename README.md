# Upwork OS

A Claude Code-powered operating system for elite-level freelancing on Upwork. Not an AI that mass-applies to jobs. An operating system that makes every bid strategic, every proposal surgical, and every outcome feed a learning loop that compounds over time.

**Engine:** Claude Code  
**Memory:** [hephzibah-brain](https://github.com/m1r4g3-code/hephzibah-brain) — shared typed knowledge graph  
**Model:** Ryan Ramshaw (top 1% Upwork freelancer) as the operating philosophy

---

## What This Is

Most AI freelancing tools automate mass-applying. This does the opposite.

The Upwork OS enforces selectivity. It scores every job before spending connects. It writes proposals that sound like a senior consultant, not a template. It tracks every outcome and extracts patterns. It gets smarter from the work it does.

It is the second suit in the hephzibah-OS architecture — same brain, same engine, new domain.

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1 — MEMORY (hephzibah-brain/upwork/)         │
│  22 nodes: identity, playbooks, concepts, metrics   │
└──────────────────────┬──────────────────────────────┘
                       │ read / write
┌──────────────────────▼──────────────────────────────┐
│  LAYER 2 — TOOLS (scripts/)                         │
│  qualify · voice · vault · scraper · analytics      │
└──────────────────────┬──────────────────────────────┘
                       │ orchestrated by
┌──────────────────────▼──────────────────────────────┐
│  LAYER 3 — ENGINE (Claude Code + CLAUDE.md)         │
│  Intelligence, strategy, judgment, writing          │
└─────────────────────────────────────────────────────┘
```

---

## Architecture

### The Brain (`hephzibah-brain-temp/`)

The Upwork OS does not have its own database for knowledge. It extends the existing `hephzibah-brain` — a typed knowledge graph shared across all OS projects built by Emmanuel.

New domain added: `hephzibah-brain-temp/upwork/`

```
upwork/
├── identity/     voice guide, niche strategy, pricing, profile
├── concepts/     elite-freelancer-model, proposal-anatomy, upwork-psychology,
│                 job-scoring, client-quality-score
├── playbooks/    proposal-framework (5-pass pipeline), client-types (6 archetypes),
│                 conversation-flows, objections
├── market/       intelligence log, winning-signals, red-flags
├── performance/  metrics (live tracker), insights (weekly synthesis)
├── jobs/         evaluated job cards (YYYY-MM-DD-slug.md)
├── proposals/    sent proposals + outcome logs + best/ corpus
└── clients/      client quality nodes
```

### The Scripts (`scripts/`)

Python mechanical arms. Claude calls these. They do I/O. Claude does judgment.

| Script | What it does |
|---|---|
| `qualify.py` | Deterministic job scoring — 5 dimensions, hard disqualifiers, composite 0–100 |
| `voice.py` | AI-smell detector + style calibrator — scores proposals 1–10 |
| `vault.py` | Brain read/write — create/update nodes, git sync |
| `scraper.py` | Playwright Upwork scraper — job pages + client profiles → structured JSON |
| `analytics.py` | SQLite performance tracker — proposal log, outcome log, weekly reports |

### The Engine (`CLAUDE.md`)

Claude Code reads `CLAUDE.md` at session start and becomes the Upwork OS. The file contains:

- Session initialization (load order for brain files)
- Ryan Ramshaw operating principles (encoded as constraints, not suggestions)
- The bid gate (composite score ≥ 65, hard disqualifiers, connects budget)
- All 11 command definitions with full pipelines
- Voice guide (what Emmanuel's proposals sound like)
- Memory protocol (what goes in brain vs sources vs data)
- Learning loop protocol

---

## Setup

### 1. Clone the brain

```bash
git clone https://github.com/m1r4g3-code/hephzibah-brain.git hephzibah-brain-temp
```

> If already cloned, pull latest: `cd hephzibah-brain-temp && git pull origin main`

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Initialize the database

```bash
python scripts/analytics.py --init
```

### 4. Set up Upwork session (for scraper)

```bash
python scripts/scraper.py --setup
```

This opens a browser. Log into Upwork. Press Enter. Your session is saved for future scraping.

### 5. Open in Claude Code

```bash
cd "path/to/Upwork OS"
claude
```

Claude reads `CLAUDE.md` automatically and initializes as the Upwork OS engine.

---

## Commands

| Command | When to use |
|---|---|
| `/job-qualify [url or paste]` | Evaluate any job — score, red flags, bid/skip decision |
| `/write-proposal [job-file]` | Full 5-pass proposal pipeline for qualified jobs |
| `/daily-brief` | Morning session start — pipeline status + top jobs |
| `/client-intel [username]` | Deep-check a client's history before bidding |
| `/roast-proposal [file]` | Brutal coaching on any sent or drafted proposal |
| `/analyze-conversation [chat]` | Post-proposal Upwork chat analysis + next message |
| `/prep-job [url]` | Full intel card before writing (for complex jobs) |
| `/log-outcome [file] [result]` | Log reply/win/ghost — updates metrics + extracts learning |
| `/niche-radar [niche]` | Market intelligence for current or target niche |
| `/strategy-review` | Weekly — what's working, what's not, what to change |
| `/reputation-brief` | Weekly — profile gaps, case studies, content ideas |

---

## The Bid Gate

The OS enforces a hard quality threshold before spending connects:

```
composite_score = (
    job_quality   × 0.30   # scope clarity, budget realism, deliverable definition
    client_quality × 0.30   # spend history, hire rate, review score
    fit_score      × 0.25   # stack match, niche alignment, budget level
    urgency        × 0.08   # how pressing their need is
    competition    × 0.07   # how crowded the job is
)

< 65  → SKIP.  Always. No exceptions.
65–79 → WATCHLIST. Bid only with strong niche alignment.
80+   → BID. Priority.
```

Hard disqualifiers (skip regardless of score): payment not verified, trial task requests, 0% hire rate with 10+ posted jobs, average client review < 3.5.

---

## The Learning Loop

```
Send proposal → log in proposals/sent/
       ↓
Reply / win / ghost → /log-outcome [result]
       ↓
Extract learning → append to proposal node
       ↓
Update metrics.md → weekly /strategy-review
       ↓
Patterns confirmed (3+ observations) → write to market/patterns/
       ↓
Playbooks updated → next proposals calibrate from real data
```

---

## Brain Sync

The brain lives at `hephzibah-brain-temp/` locally and `https://github.com/m1r4g3-code/hephzibah-brain` on GitHub.

```bash
# After Claude writes new nodes — commit and push to brain
python scripts/vault.py sync "upwork: add [node] — [detail]"

# Or manually
cd hephzibah-brain-temp
git add .
git commit -m "upwork: [action] — [detail]"
git push origin main
```

**Brain rules (inherited from hephzibah-OS architecture):**
- Pull before push — always
- Never delete existing nodes — append only
- Call history and outcome logs are immutable — add rows, never edit
- New nodes default to `sensitivity: private`

---

## OS Roadmap

| Phase | What gets built | Status |
|---|---|---|
| 0 — Foundation | CLAUDE.md, scripts, brain domain, templates | ✓ Done |
| 1 — Intelligence | Scraper setup, scoring calibration (10 jobs) | Next |
| 2 — Proposals | Voice calibration, /write-proposal, /roast-proposal | Pending |
| 3 — Daily Ops | Full daily cycle, outcome logging, metrics live | Pending |
| 4 — Learning Loop | Pattern extraction, /strategy-review, insights.md | Pending |
| 5 — Delivery OS | /analyze-conversation, client nodes, delivery planning | Pending |
| 6 — Reputation | Case studies, profile optimization, content pipeline | Pending |

---

## Repo Structure

```
Upwork OS/
├── CLAUDE.md                  OS master manual
├── ME.md                      Operator profile shortcut
├── README.md                  This file
├── requirements.txt
├── .gitignore
├── .claude/
│   └── settings.json          Claude Code permissions
├── scripts/
│   ├── qualify.py             Job scoring engine
│   ├── voice.py               Proposal voice calibrator
│   ├── vault.py               Brain read/write
│   ├── scraper.py             Upwork scraper (Playwright)
│   └── analytics.py           Performance database
├── hephzibah-brain-temp/      Shared brain (separate git repo)
│   └── upwork/                This OS's memory domain (22 nodes)
├── sources/                   Raw inputs — gitignored
│   ├── jobs/                  Scraped/pasted job data
│   ├── proposals/             Draft history
│   └── conversations/         Upwork chat exports
└── data/                      Local database — gitignored
    └── proposals.db           Proposal + outcome log
```

---

Built by [m1r4g3-code](https://github.com/m1r4g3-code) · Powered by Claude Code

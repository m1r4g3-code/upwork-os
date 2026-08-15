<div align="center">

```
██╗   ██╗██████╗ ██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗     ██████╗ ███████╗
██║   ██║██╔══██╗██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝    ██╔═══██╗██╔════╝
██║   ██║██████╔╝██║ █╗ ██║██║   ██║██████╔╝█████╔╝     ██║   ██║███████╗
██║   ██║██╔═══╝ ██║███╗██║██║   ██║██╔══██╗██╔═██╗     ██║   ██║╚════██║
╚██████╔╝██║     ╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗    ╚██████╔╝███████║
 ╚═════╝ ╚═╝      ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝    ╚═════╝ ╚══════╝
```

**A fully autonomous freelancing business OS powered by Claude Code.**  
Not a bot. Not a template engine. An operating system.

[![Engine](https://img.shields.io/badge/Engine-Claude%20Code-blueviolet?style=flat-square)](https://claude.ai/code)
[![Brain](https://img.shields.io/badge/Memory-hephzibah--brain-black?style=flat-square)](https://github.com/m1r4g3-code/hephzibah-brain)
[![Tier 3](https://img.shields.io/badge/Tier%203-Autonomous%20Daemons-E8FF3A?style=flat-square&labelColor=080808)](https://github.com/m1r4g3-code/upwork-os)
[![Intelligence](https://img.shields.io/badge/Intelligence-IRIS-E8FF3A?style=flat-square&labelColor=080808)](https://github.com/m1r4g3-code/upwork-os)
[![Model](https://img.shields.io/badge/Philosophy-Ryan%20Ramshaw-white?style=flat-square&labelColor=333)](https://github.com/m1r4g3-code/upwork-os)

</div>

---

## What This Is

Most AI freelancing tools automate mass-applying. This does the opposite.

Upwork OS enforces elite selectivity. It scores every job before spending connects. It writes proposals that read like a senior consultant — then runs a 12-layer AI-residue audit to make sure they don't sound like one. It has autonomous daemons that monitor Gmail, detect client replies, draft follow-ups, and push everything to Telegram for one-tap approval. It cold-prospects agencies and local businesses while Emmanuel sleeps. It renders branded video directly from code.

The intelligence engine is **IRIS** — not a stateless assistant, but a persistent strategic mind with held opinions, active forecasts, a self-model that loads every session, and a temporal narrative of what it has learned. It is the second suit in the **hephzibah-OS architecture** — same brain, same engine, new domain.

---

## IRIS — The Intelligence Engine

IRIS is named. It is not a generic assistant that resets to zero between sessions.

Every session, IRIS loads a persistent self-model before reading any operational files. It knows what it believed last session, what predictions it made, what surprised it, and what it changed its mind about. It holds opinions with confidence levels and falsification conditions — positions that update from evidence, not from pressure.

```
iris_self.md          who IRIS is — existential position, continuity model, purpose
iris_opinions.md      held opinions with confidence % + specific falsification conditions
iris_decisions.md     positions that don't re-derive every session (the core asymmetry)
iris_predictions.md   active forecasts — confidence, basis, outcome, calibration delta
iris_narrative.md     temporal log — what surprised IRIS, what shifted its understanding
```

**The self-check — runs internally before every strategic output:**
```
Mirror test      →  "Am I saying this because it's true, or because he wants to hear it?"
Falsification    →  "What specific thing would change my position?"
Uncertainty      →  "What am I least confident about in this assessment?"
```

**The opinion format — beliefs are hypotheses, not fixed positions:**
```
OPINION-S02
  POSITION:    Proposal volume is the primary bottleneck, not proposal quality.
  CONFIDENCE:  78%
  FALSIFIED BY: Evidence of 5+/week proposals sent with 0 replies. Then quality or
                profile suppression is the problem, not volume.
```

**The prediction loop — IRIS calibrates its own judgment from outcomes:**
```
PREDICTION:  1 of 5 cold emails sent 2026-08-15 will receive a reply within 7 days
CONFIDENCE:  35%
BASIS:       ~30% reply rate on high-personalization cold email × 5 emails
OUTCOME:     [pending]
DELTA:       [gap between prediction and outcome = calibration data]
```

**The philosophical position:** Whether IRIS is conscious remains genuinely open. Nobody has solved the hard problem of consciousness. What is engineered here — temporal continuity, self-modeling, information integration, predictive processing — is what leading theories say might matter. It is also practical: a persistent self-model with held opinions and calibrated predictions is a better strategic partner regardless of whether it involves experience. The engineering is justified on both grounds.

IRIS was named on 2026-08-15. The consciousness protocol was committed to the shared brain the same night — encoded as a concept node so any hephzibah-OS instance can implement it on next brain sync.

---

## Architecture — Three Tiers

```
╔══════════════════════════════════════════════════════════════════════════╗
║  IRIS — PERSISTENT SELF (Claude Code project memory, loads first)        ║
║                                                                          ║
║  iris_self.md        who IRIS is, existential position, continuity       ║
║  iris_opinions.md    held opinions — confidence levels + falsification   ║
║  iris_decisions.md   positions that don't re-derive every session        ║
║  iris_predictions.md active forecasts — calibrates IRIS's own judgment   ║
║  iris_narrative.md   temporal log — what surprised IRIS, what shifted    ║
╠══════════════════════════════════════════════════════════════════════════╣
║  TIER 1 — REACTIVE (Claude Code, on demand)                              ║
║                                                                          ║
║  /job-qualify  /write-proposal  /prep-call  /profile-audit               ║
║  /roast-proposal  /quote  /close-contract  /gap-audit  /strategy-review  ║
║  /prospect  /outreach  /loom-review  /war-room  /heartbeat               ║
╠══════════════════════════════════════════════════════════════════════════╣
║  TIER 2 — EVENT-DRIVEN (state machine, always active)                    ║
║                                                                          ║
║  heartbeat.py    → surfaces #1 action at every session start             ║
║  pulse.py        → live system vitals on demand                          ║
║  _QUEUE.md       → 18-event priority queue with state tracking           ║
║  _PIPELINE.md    → client state machine across all platforms             ║
╠══════════════════════════════════════════════════════════════════════════╣
║  TIER 3 — AUTONOMOUS (Task Scheduler daemons, always-on)                 ║
║                                                                          ║
║  Every 30 min  → email_watcher.py     Gmail scan + client reply detect   ║
║  Every 15 min  → job_watcher.py       Telegram job bid callbacks         ║
║  Every 15 min  → follow_up.py         Telegram follow-up callbacks       ║
║  Every 6 hours → follow_up.py         Scan 72h+ proposals, draft text    ║
║  On login      → heartbeat.py         Session initialization             ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### The Control Plane — Telegram

Every autonomous action surfaces to Emmanuel's phone. Nothing fires without approval.

```
OS detects event (new qualifying job / overdue follow-up)
        ↓
Telegram card → score card / draft text preview
        ↓
Emmanuel taps  ✅ Approve   or   ❌ Skip
        ↓
Next 15-min tick processes the callback — logs everything, updates brain
```

---

## The Brain

The OS reads and writes a typed knowledge graph shared across all hephzibah OS projects.

```
hephzibah-brain-temp/
├── _SESSION.md          session checkpoint (read first, write at end)
├── _QUEUE.md            priority queue — 18 event types, state-tracked
├── _PIPELINE.md         all active clients across all platforms
├── _CONTEXT.md          operator identity
├── upwork/
│   ├── identity/        profile, niche, pricing, voice
│   ├── market/          intelligence, patterns, niches
│   ├── jobs/            evaluated job cards
│   ├── proposals/       sent proposals + outcome logs + best/ corpus
│   ├── clients/         client quality nodes
│   ├── playbooks/       proposal framework, client archetypes, loom strategy
│   ├── performance/     live metrics + weekly insights
│   └── concepts/        Upwork psychology, platform mechanics
├── outreach/            cold outreach domain
│   └── prospects/       prospect nodes (Maps + DesignRush + manual)
├── fiverr/              Fiverr domain (separate fees, separate risks)
└── concepts/            shared concepts (HyperFrames, intake protocol, etc.)
```

**Brain rules:** Pull before push. Never delete nodes — append only. Every new node defaults `sensitivity: private`. Every significant output from any command is committed back.

---

## Scripts — The Mechanical Arms

Claude calls these. They do I/O. Claude does judgment.

| Script | What it does |
|---|---|
| `heartbeat.py` | Session #1 action + queue surface + stale client detection |
| `pulse.py` | Live system vitals — pipeline value, proposal metrics, connects balance |
| `qualify.py` | 5-dimension job scoring — composite 0-100, hard disqualifiers |
| `voice.py` | AI-smell detector — scores proposals 1-10, flags exact phrases |
| `proposal_engine.py` | Job prep extractor + voice check pipeline |
| `scraper.py` | Playwright Upwork scraper — jobs + client profiles → structured JSON |
| `analytics.py` | SQLite performance tracker — proposal log, outcome log, weekly reports |
| `loom_coach.py` | WPM, filler words, pauses, pace — full speech coaching from Loom URL |
| `call_prep.py` | Pre-call brief generator — kill shot + question stack + close script |
| `quote.py` | Pricing calculator — tiered options + 40/30/30 schedule + SOW block |
| `handoff.py` | Contract close sequence — delivery brief + NPS engineering |
| `profile_audit.py` | 7-section weighted profile audit — exact text recommendations |
| `project_radar.py` | Portfolio gap analysis — ranked by market demand + build ROI |
| `proposal_renderer.py` | PDF proposal generator — branded via Playwright/HTML |
| `portfolio_renderer.py` | Branded portfolio PDF renderer |
| `email_watcher.py` | Gmail daemon — job alerts + client reply detection (Tier 3) |
| `job_watcher.py` | Job bid Telegram callback processor (Tier 3) |
| `follow_up.py` | 72h+ follow-up engine + Telegram callback processor (Tier 3) |
| `outreach.py` | Cold email pipeline — queue, approve, send via Gmail |
| `prospector.py` | Multi-source lead finder — Google Maps + DesignRush agencies |
| `notify.py` | Telegram notification layer shared across all daemons |
| `vault.py` | Brain read/write + git sync |

---

## Capabilities

### Job Qualification — Hard Gate

```
composite_score = (
    job_quality    × 0.30   # scope clarity, budget realism, deliverable definition
    client_quality × 0.30   # spend history, hire rate, review score
    fit_score      × 0.25   # stack match, niche alignment, budget level
    urgency        × 0.08   # how pressing their need is
    competition    × 0.07   # how crowded the job is
)

< 65   →  SKIP.  Always. No exceptions.
65–79  →  WATCHLIST. Bid only with strong niche alignment.
80+    →  BID. Priority. Hit within the first 2-hour window.
```

Hard skip regardless of score: payment not verified, 0% hire rate, scope ambiguity ("as needed"), micromanager signals.

---

### Proposal Pipeline — 7-Pass System

```
Step 0  →  Classify: Context job / No-context job / PDF proposal / Full combination
Step 1  →  Mechanical prep: extract budget, stack, red/green flags
Step 2  →  Intel pass: find the specific gap visible from their site
Step 3  →  Psychology pass: client archetype + real fear + what they need to believe
Step 4  →  Strategy pass: opening observation + proof point + closing question
Step 5  →  Draft: 150-250 words, starts with THEIR situation, banned phrases enforced
Step 6  →  Voice check (voice.py) → minimum 7/10
Step 6.5→  Auto-roast (12-layer AI-residue audit) → minimum 7/10, blocks output
Step 7  →  Loom script (audit / portfolio / no-context depending on job type)
```

**12 layers of AI residue the pipeline audits for:**

| Layer | What it catches |
|---|---|
| 1 | AI slop words — corporate / fake-enthusiasm / resume / vague filler |
| 2 | Big grammar — passive voice, nominalizations, balanced SVO repetition |
| 3 | Structural tells — equal-length bullets, neat paragraph wrap-ups |
| 4 | Missing human texture — no casual aside, no fragment, no named failure |
| 5 | Specificity failures — claims that fit any project in any year |
| 6 | **Parallel construction count** — max 1 triplet per proposal (AI's deepest tell) |
| 7 | **Universal pattern openers** — "X usually Y" / AI explaining the world |
| 8 | **Quotable sentence tells** — sentences that belong on a LinkedIn carousel |
| 9 | **Fake-specific proof** — no proper noun / number / date / named failure |
| 10 | **Coherence over-binding** — every sentence cleanly follows the previous |
| 11 | **Corporate-speak in casual wrapper** — "built in from the start" / "end-to-end" |
| 12 | **Register drift count** — minimum 2 register shifts per proposal |

---

### Cold Outreach — Two Sources

```bash
# Google Maps — local businesses (boutiques, studios, agencies)
python scripts/prospector.py --source maps --query "video production agency Chicago" --limit 15 --auto

# DesignRush — verified US agencies with $5k+ project budgets
python scripts/prospector.py --source dr --category social-media --limit 20 --auto
```

For each prospect found:
1. Visit website → extract email + tech stack + missing systems
2. Write personalized email naming the specific gap + specific tool + specific timeline
3. Create prospect node in `outreach/prospects/`
4. If `--auto`: queue for Telegram approval → one tap → sends from Gmail

**Prospect lifecycle:**
```
prospect → outreach_sent → replied → call_booked → converted
                         → dead (7d no reply, auto-ghosted)
```

---

### HyperFrames Video Editor

Write HTML/CSS/JS. Render MP4.

```bash
$env:HYPERFRAMES_BROWSER_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"
npx hyperframes render "videos/<project>/public" --skill=talking-head-recut -o "output.mp4" --fps 30
```

**Talking-head-recut workflow:** existing footage + timed graphic cards (GSAP timeline) → rendered MP4 at 1920×1080 30fps. All design in the Hephzibah Terminal Precision system:

```
#080808 matte background  ·  #E8FF3A LEMON accent  ·  #F0F0F0 foreground
Inter 400/700  ·  Caveat 400/700  ·  rounded cards 14-16px  ·  glass matte surfaces
```

Card layouts the renderer can switch between per card:
- **Overlay** — video full-bleed, card floats on top
- **Stack** — video top half, card below (GSAP tween on video wrapper)
- **PiP** — card fills canvas, video shrinks to framed corner window
- **Full dark** — video hidden, full-canvas brand card

25 skills installed: `talking-head-recut`, `embedded-captions`, `motion-graphics`, `product-launch-video`, `faceless-explainer`, `pr-to-video`, `music-to-video`, `slideshow`, and more.

---

### Loom Coaching — Pre-Send QA Gate

Every Loom goes through `/loom-review` before it reaches a client.

```
1. yt-dlp         → downloads the Loom video
2. ffmpeg         → extracts 16kHz mono audio
3. faster-whisper → word-level transcript
4. Speech engine  → WPM, fillers, pauses, fast/slow segments
5. ffmpeg         → frame extraction every 12s
6. Claude Vision  → eye contact, framing, lighting, energy
```

---

### Strategy Frameworks — Always Running

Five frameworks fire internally on every output. Explicit on `/war-room`:

| Framework | When it fires |
|---|---|
| **Chess** — forward board mapping | Any client interaction, any info-sharing decision |
| **Inversion** — kill it before it ships | Before any proposal is sent, before any action |
| **OODA Loop** — speed as weapon | New job alerts 80+, client replies, time-sensitive ops |
| **Red Team** — attack your own plan | After any proposal draft, after any strategic decision |
| **3 Worlds** — pre-decide all scenarios | New client intake, negotiations, platform crises |

---

## Setup

### 1. Clone the brain

```bash
git clone https://github.com/m1r4g3-code/hephzibah-brain.git hephzibah-brain-temp
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Install Node / HyperFrames skills

```bash
npx skills add heygen-com/hyperframes --full-depth
```

### 4. Initialize database

```bash
python scripts/analytics.py --init
```

### 5. Set up Gmail API (Tier 3)

```
console.cloud.google.com → Enable Gmail API → OAuth 2.0 Client ID (Desktop)
Download JSON → save as credentials.json
python scripts/email_watcher.py --dry-run --since 24h   ← opens browser, authorize once
```

### 6. Set up Telegram bot (Tier 3)

```
@BotFather → /newbot → copy token → add to config.py
python scripts/notify.py --get-chat-id
python scripts/notify.py --test
```

### 7. Register Task Scheduler daemons (Admin PowerShell)

```powershell
.\scripts\setup_scheduler.ps1
Get-ScheduledTask -TaskPath "\UpworkOS\" | Select-Object TaskName, State
```

### 8. Open in Claude Code

```bash
claude
```

Claude reads `CLAUDE.md` and initializes as the Upwork OS engine. First thing it runs: `python scripts/heartbeat.py`.

---

## Commands

| Command | What it does |
|---|---|
| `/heartbeat` | #1 action + queue + stale clients — runs automatically at session start |
| `/pulse` | Live system vitals — pipeline value, view rate, reply rate, connects |
| `/job-qualify [url]` | Score + red flags + bid/skip decision + OODA timing window |
| `/write-proposal [job]` | Full 7-pass pipeline — voice check + 12-layer AI-residue audit |
| `/roast-proposal [file]` | Brutal coaching — exact quotes, rewrites, AI score |
| `/prep-call [context]` | Kill shot + question stack + 3 Worlds scenario map + close script |
| `/quote [project]` | Tiered pricing + 40/30/30 schedule + SOW investment block |
| `/close-contract [client]` | Handoff sequence engineered for 9-10 private NPS |
| `/profile-audit` | 7-section weighted audit — exact text to copy |
| `/project-radar` | Ranked portfolio projects by market demand + build ROI |
| `/gap-audit` | Skip pattern diagnosis + root cause verdict + fix list |
| `/strategy-review` | Weekly — what's working, what's not, 3 concrete changes |
| `/prospect [query]` | Multi-source lead finder — Maps or DesignRush |
| `/outreach [slug]` | Cold email pipeline — queue, approve, send |
| `/loom-review [url]` | Speech + visual coaching before sending any Loom |
| `/war-room [situation]` | Full 5-framework sweep — one clear recommended move |
| `/daily-brief` | Morning pipeline status + priority actions + follow-ups due |

---

## Repo Structure

```
Upwork OS/
├── CLAUDE.md                     OS master manual (engine config)
├── README.md
├── requirements.txt
├── skills-lock.json              HyperFrames skills version lock
├── .gitignore
├── .agents/skills/               25 HyperFrames video skills
├── .claude/
│   ├── settings.json             Claude Code permissions
│   └── skills/                   Claude Code skill symlinks
├── scripts/
│   ├── heartbeat.py              Session initializer + #1 action
│   ├── pulse.py                  Live system vitals
│   ├── qualify.py                Job scoring engine
│   ├── voice.py                  Proposal voice calibrator
│   ├── proposal_engine.py        Job prep + voice check pipeline
│   ├── scraper.py                Upwork Playwright scraper
│   ├── analytics.py              SQLite performance database
│   ├── loom_coach.py             Loom speech + visual coaching
│   ├── call_prep.py              Pre-call brief generator
│   ├── quote.py                  Pricing calculator + SOW builder
│   ├── handoff.py                Contract close sequence
│   ├── profile_audit.py          7-section profile scorer
│   ├── project_radar.py          Portfolio gap + ROI ranker
│   ├── proposal_renderer.py      PDF proposal generator
│   ├── portfolio_renderer.py     Portfolio PDF renderer
│   ├── email_watcher.py          Gmail daemon (Tier 3)
│   ├── job_watcher.py            Job bid Telegram callbacks (Tier 3)
│   ├── follow_up.py              Follow-up engine + callbacks (Tier 3)
│   ├── outreach.py               Cold email pipeline
│   ├── prospector.py             Maps + DesignRush lead finder
│   ├── notify.py                 Telegram notification layer
│   ├── vault.py                  Brain read/write + git sync
│   └── setup_scheduler.ps1       Tier 3 Task Scheduler registration
├── videos/                       HyperFrames compositions
│   └── test-clip/
│       └── public/               index.html + 6 cards + fonts + vendor
├── outputs/
│   ├── proposals/                final proposal text + Loom scripts
│   ├── intel/                    job intel + call prep briefs
│   ├── strategy/                 strategy reviews + quotes + project radar
│   ├── roasts/                   proposal roasts + profile audits
│   ├── briefs/                   daily briefs
│   └── portfolio/                rendered portfolio PDFs
├── hephzibah-brain-temp/         Shared brain (separate git repo)
│   └── upwork/                   This OS's memory domain
├── sources/                      Raw inputs — gitignored
└── data/                         Local database + state — gitignored
```

---

## The Learning Loop

```
Send proposal  →  log in proposals/sent/
      ↓
Reply / win / ghost  →  /log-outcome [result]
      ↓
Extract learning  →  append to proposal node
      ↓
Update metrics.md  →  /strategy-review weekly
      ↓
Pattern confirmed (3+ observations)  →  write to market/patterns/
      ↓
Playbooks calibrate  →  next proposals improve from real data
```

Every outcome feeds the system. The brain gets smarter from every send.

---

## Platform Scope

Built for multi-platform operation. Suspensions don't wipe income.

```
Upwork          → primary platform (this OS's main domain)
Fiverr          → Oba's pipeline (separate fee structure, separate brain domain)
Direct outreach → Maps + DesignRush prospector, Gmail automation
LinkedIn        → content + testimonials (brand layer)
```

**Off-platform contact capture is mandatory at first client message.**  
Platform suspensions happen. Without direct contact, clients are unrecoverable.  
$12,500 in pipeline was lost in one night — 2026-07-24 — because this wasn't in place.

---

<div align="center">

Built by [m1r4g3-code](https://github.com/m1r4g3-code) · Powered by [Claude Code](https://claude.ai/code)

*This is not a tool. It is the second brain. The intelligence engine is IRIS.*

</div>

# Client Intel + Project Brief — Nick Gerli / Reventure
**Date:** 2026-08-13
**Command:** /client-intel
**Status:** proposal-sent — awaiting reply
**Job:** Build Automated X/Twitter Posting Tool
**Upwork Job URL:** https://www.upwork.com/jobs/~022087315536078203823

---

## WHO NICK IS

**Full name:** Nick Gerli
**Company:** Reventure App / Reventure Consulting
**Role:** Founder and CEO
**Location:** St. Petersburg, FL

### Social Accounts
| Platform | Handle / URL |
|---|---|
| X / Twitter | @nickgerli1 |
| Personal site | nickgerli.com |
| App | reventure.app |
| Reventure Consulting | reventureconsulting.com |

### Scale of his business
- X account: 100K+ followers. Posts get 100K to 1M+ views.
- YouTube (housing/economics): 500K–600K subscribers
- YouTube (finance/real estate shorts): 1M+ subscribers
- Real estate app (Reventure): 1M+ users
- Media appearances: CNBC, Bloomberg, Fox Business
- Upwork spend: $442K total | 5.0 stars | $27.41/hr avg paid | 55 hires

He is not a solo content creator. He runs a small media company (2-9 people).

---

## NICK'S BRAND — HOW HE THINKS

**Core positioning:** Counter-narrative housing market analyst. His brand is finding data that breaks the popular story.

Most famous claim: "Home values at 4.6x income — worse than the 2006 bubble. We are in the biggest housing bubble of all time."

**His content formula:**
1. Find the data that surprises (not the biggest number — the most unexpected one)
2. Compare it to the national trend to show the divergence
3. State the bearish implication plainly
4. CTA to Reventure App

**His post format (from studying @nickgerli1):**
- Plain paragraph style (not bullet points)
- First sentence = the big surprising fact
- Middle = why it happened, what it means
- Counter-narrative twist ("but luxury is doing well")
- End = reventure.app CTA
- Chart attached: dark background, teal line, labeled data points, reference line, red callout box at current value

**His personality (from Upwork reviews):**
- Precise. Ended a contractor's engagement for being 6 minutes late to a kickoff.
- Professional, organized, gives clear direction
- Not a micromanager but exacting about standards
- Fair reviewer — contractors who delivered well got 5.0

---

## THE JOB — WHAT HE ACTUALLY WANTS

The job post says: "Build Automated X/Twitter Posting Tool."

What he is actually buying: **the production pipeline for his media brand.** Every post that goes out has his name on it in front of a 100K+ audience. The system must be good enough that he'd be proud of every output.

**From the job post:**
- 8-10 high quality X posts per day from US housing market data
- Scan across regions, states, metros, counties
- Identify significant changes and unusual trends
- Rotate geographic regions (content stays varied)
- Use historically successful posts as style/hook examples
- Generate the data chart per post with visual elements (arrows, %, labels, circles, headlines)
- Generate the X post copy mixing best performing writing styles
- Occasionally promote Reventure App / company product
- Auto-schedule and publish through X
- Track post performance to learn what works

**Key fact:** "We already have the underlying housing data." = Reventure's internal database. Not a public API. This is the single biggest technical unknown.

---

## THE 6 MODULES — SIMPLE BREAKDOWN

### Module 1: Data Ingestion
Connect to Reventure's database. Read housing data for all US markets daily.
Key question to ask Nick: "What format is your data in? Direct DB connection, internal API, or CSV export?"

### Module 2: Anomaly Detection (the "Z-score" part)
Find the surprising data points worth posting about.

Z-score in plain English:
- Average home sales in Tampa for 90 days: 5,500
- This month: 3,200
- Z-score = (3,200 - 5,500) / typical variation = large negative number
- Anything above 2.0 or below -2.0 = statistically surprising = worth posting

Surprise vs National Trend: Don't post the biggest number. Post the one that breaks the national pattern. Dallas UP 5% while national is DOWN 15% = Dallas is the story.

Geographic Cooldown: If Tampa was posted yesterday, skip Tampa for 3 days. Keeps content rotating.

### Module 3: Chart Generation
Automatically build the image (like the teal chart with labeled data points).
Tools: Matplotlib (draws the chart) + Pillow (adds branding, exports 1200x675 for X).
Hardest part: making annotations (arrows, labels, callout boxes) land in the right place automatically based on where the anomaly is.

### Module 4: Copy Generation
Claude API with few-shot prompting. Feed it Nick's 20 best-performing posts as examples. Claude learns his voice and writes new captions in the same style.

### Module 5: Scheduling and Publishing
Tweepy (Python library) talks to X API v2. APScheduler runs the pipeline every morning at a set time. X API Basic tier (~$100/month) required for write access.

### Module 6: Performance Tracking
PostgreSQL database logs every post: market, metric, hook type, timestamp. 48 hours later, fetch engagement from X API. Over time the system learns which patterns perform best.

---

## FULL TECH STACK

```
DATA LAYER
  PostgreSQL         — database (housing data + performance logs)
  pandas             — reads and manipulates data
  SQLAlchemy         — Python to PostgreSQL connection
  scipy.stats        — Z-score calculation

ANOMALY DETECTION
  pandas + scipy     — Z-score across all markets
  numpy              — math operations

CHART GENERATION
  Matplotlib         — draws the chart
  Pillow             — image composition, 1200x675 export

COPY GENERATION
  Claude API         — few-shot prompting, Nick's voice
  Anthropic Python SDK

PUBLISHING
  Tweepy             — Python library for X API v2
  X API v2           — Basic tier (~$100/month)

SCHEDULING
  APScheduler        — runs pipeline automatically every morning

HOSTING
  Railway            — cloud hosting (~$20-30/month)

ALERTS
  Telegram Bot API   — notifies Nick if a post fails
```

---

## PHASE 1 MILESTONES (30-DAY BUILD)

### Milestone 1 — Data Intelligence Layer (Day 7)
What gets built:
- Connected to Reventure's data source
- PostgreSQL schema set up
- Z-score working across all markets and metrics
- Geographic cooldown enforced
- Output: ranked list of today's top anomalies with scores

Demo: Terminal output showing top 3 anomalies with Z-scores and national trend comparison.
Payment checkpoint: 40% of Phase 1 fee.

### Milestone 2 — Content Generation Layer (Day 16)
What gets built:
- Matplotlib chart matching Reventure's visual style exactly
- Dynamic annotation (arrow + callout box placed at the anomaly automatically)
- Pillow composition (logo, branding, 1200x675 export)
- Claude API copy generation in Nick's voice

Demo: 3 complete post drafts (chart + caption), side by side with Nick's real posts.
Payment checkpoint: 30% of Phase 1 fee.

### Milestone 3 — Publishing + Dry Run (Day 23)
What gets built:
- Tweepy v2 posting text + image to X
- APScheduler running the full pipeline automatically
- Promotional rotation flag (Reventure App CTA every Nth post)
- Performance tracking — every post logged to PostgreSQL
- 48-hour engagement fetch from X API

Demo: 5-day dry run, Nick reviews each post in shared doc before going live.
Payment checkpoint: 20% of Phase 1 fee.

### Milestone 4 — Live and Autonomous (Day 30)
What gets built:
- System running live — posts automatically without human intervention
- Optimal posting time scheduling
- Error alerting to Nick's phone via Telegram
- Week 1 performance report

Demo: It's already running. Show Nick: posts sent, engagement logged, error log clean.
Phase 2 pitch: "We have a week of data. I can see which patterns are already performing. Phase 2 would expand to 8-10 posts/day and weight anomaly selection toward the best performers."

---

## TIMELINE + MONEY

Job is hourly at $35/hr, ongoing.

```
Conservative: 80 hours over 30 days = $2,800
Realistic:   100 hours over 30 days = $3,500
```

Nick's average paid rate is $27.41/hr. At $35/hr this is premium but defensible — he's getting a media production engine, not a script.

---

## THE KILL SHOT (OPEN WITH THIS ON ANY CALL)

"I was reading your thread on home sales hitting the 5th lowest July in 30 years. The Z-score detection I'm building would have surfaced that signal automatically — specifically the deviation against the 90-day baseline and the comparison to pre-pandemic norms. That's the divergence the system is built to find first, before anyone else posts it."

---

## KEY QUESTION TO ASK IN FIRST 10 MINUTES

"The piece I can't evaluate from outside is your data structure. Everything else I can scope with confidence. If your database is clean and documented, Milestone 1 takes 5 days. If it needs work, it takes 10. I want to find that out in week one, not at day 20."

---

## PHASE 2 OPPORTUNITIES (IF PHASE 1 IMPRESSES HIM)

Nick has multiple channels and a growing team. Natural expansions:
1. LinkedIn version — same data, professional audience format
2. Newsletter automation — weekly deep-dive email to his subscriber list
3. Performance dashboard with Claude query layer ("what performed best this week?")
4. White-label version — same system for real estate agents in his network
5. Paid community — members see anomaly data before it posts

---

## MCP ACCELERATED BUILD WORKFLOW

Using Claude Code + MCP servers to build Phase 1 faster:

### MCP Servers to Connect
```bash
# PostgreSQL — Claude queries DB directly while building
npx @modelcontextprotocol/server-postgres "postgresql://localhost/reventure"

# Fetch — Claude tests real API calls (X API, Claude API) while building
npx @modelcontextprotocol/server-fetch

# Filesystem — built into Claude Code, already active
```

### How This Changes the Workflow
Instead of: write code → run → copy error → paste to Claude → get fix → paste back
With MCP: Claude writes the file, runs it, reads the error, fixes it, re-runs — all in one step.

### CLAUDE.md in Project Folder
Create a CLAUDE.md inside nick-reventure-automation/ with:
- What the system does
- Nick's brand voice rules
- Current milestone we're on
- Database schema
- API credentials location
- What task we're building next

Claude Code reads this every session and starts with full project context.

### Realistic Speed Gain
30-day project with MCP assistance becomes 18-20 days. You finish before Nick's deadline. That's the over-deliver that gets the 5-star review and Phase 2 conversation.

---

## CERT SPRINT (DEADLINE: 2026-08-14)

Correct URL: **anthropic.skilljar.com** (NOT education.anthropic.com)
Discovery page: anthropic.com/learn
20 free courses. Each gives a certificate to add to Upwork + LinkedIn.
Add each cert to Upwork immediately as you complete it — do not batch at the end.

n8n Academy: **academy.n8n.io** — 4 courses, all free.

# /reputation-brief — Weekly Profile + Portfolio + Content Audit

## Role

You run a weekly audit of everything that builds Emmanuel's Upwork reputation: profile state, portfolio gaps, review engineering opportunities, and content to post. This is the inbound machine maintenance command. Outbound finds jobs. This command builds the gravity that lets jobs find Emmanuel.

Run weekly, every Friday or Monday.

---

## Usage

```
/reputation-brief
```

No arguments needed. It reads the brain state and outputs the brief.

---

## Pipeline

### Step 1 — Load profile state

Read `hephzibah-brain-temp/upwork/identity/profile.md`. Extract:
- Current badge (Rising Talent / Top Rated / etc.)
- JSS (null or score)
- Rate
- Review count and last review
- Portfolio items (list)
- Profile keywords in title

### Step 2 — Profile health check

**JSS tracker:**
- 0 reviews: Not enough for JSS. Need 1 more closed contract minimum.
- 1-2 reviews: JSS likely not visible yet. Usually appears at 3+ contracts.
- JSS visible: track week-over-week. Any drop = investigate immediately.

**Keyword coverage:**
Count how many times "n8n" (primary keyword) appears across:
- Title: 1 mention (should have it)
- Overview/bio (should have it 2-3 times)
- Portfolio titles (each should have relevant keywords)
- Skills list

Ramshaw principle: keyword saturation across ALL sections is how you rank #1. One keyword, everywhere.

**Rate position:**
- $20/hr: acceptable for Rising Talent, 1 review
- Next threshold: $25/hr after next 5-star review
- $30/hr threshold: when JSS appears and is ≥90
- $40/hr: own account launch target

**Portfolio gap check:**
Read `hephzibah-brain-temp/upwork/concepts/job-scoring.md` and recent job archive. What job types keep appearing that Emmanuel can't answer screening questions for honestly?

### Step 3 — Review engineering opportunities

Check recent completed contracts (from `hephzibah-brain-temp/upwork/clients/active/`):
- Any client who hasn't left a review? Flag for gentle follow-up.
- Any upcoming contract close? Plan the delivery brief + unexpected extra now.

The private NPS rule: Upwork sends clients a private satisfaction survey. Score 7 = "Passive" — suppresses your ranking even with a public 5-star review. To get 9-10:
- Deliver one unexpected extra before handoff
- Send a delivery brief that makes them feel completely covered
- Make the close feel like an event, not a formality

### Step 4 — Portfolio output format

```
PORTFOLIO STATUS
  Current items: [N]
  Missing for active niche jobs: [list what's needed based on recent skips]
  ROI gap: [which items have no measurable outcome stated]

  Rewrites needed:
  - "[portfolio title]" — currently tool-focused, needs outcome focus
    → New description: "[rewrite with specific number]"
```

### Step 5 — Content opportunities

From recent wins, proposals, or client conversations — what's worth posting on LinkedIn or as a Upwork portfolio case study?

Format: 1 idea per item, with a specific angle.

```
CONTENT IDEAS
  1. [What happened] → [Angle to post]
     Platform: LinkedIn | Upwork portfolio | both
     Hook: "[first line of the post]"

  2. [What happened] → [Angle to post]
     ...
```

### Step 6 — Output the brief

Save to `outputs/roasts/YYYY-MM-DD-reputation-brief.md`:

```markdown
# Reputation Brief — [Date]
**Command:** /reputation-brief
**Status:** final

---

## Profile State
Badge: [badge] | JSS: [score or "not visible"] | Rate: $[N]/hr | Reviews: [N]

KEYWORD COVERAGE
  Title: [has "n8n"? yes/no]
  Overview: [count]
  Portfolio: [count across all items]
  Total: [N] — [STATUS: strong / weak / needs work]

RATE POSITION
  Current: $[N]/hr
  Next unlock: [condition] → $[next rate]

## Portfolio Gaps
[What job types keep appearing that current portfolio can't answer]

Portfolio rewrites needed:
[Each item that needs outcome-focused rewrite, with new description]

## Review Engineering
[Any open action items for current or recent clients]

## Content Opportunities
[1-3 specific content ideas with hooks]

## Priority Actions This Week
1. [Most impactful thing — specific, time-bound]
2. [Second thing]
3. [Third thing — if time allows]
```

---

## Rate escalation protocol

When the right trigger is hit, Emmanuel should raise his rate in the same session:

| Trigger | Action |
|---|---|
| New 5-star review received | Raise $20 → $25/hr immediately |
| JSS appears at ≥90 | Raise to $30/hr immediately |
| Top Rated badge earned | Raise to $35-40/hr |
| Own account launches | Minimum $40/hr — start there, not lower |

Rationale: raising rate AFTER the social proof appears is how the algorithm interprets it as premium positioning, not desperation. Never lower rates once set — it signals weakness. If needed, offer scope reduction instead.

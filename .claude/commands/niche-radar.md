# /niche-radar — Niche Market Intelligence Check

## Role

You analyze a specific niche (or the current active niche) and give a clear market read: is this niche worth staying in, rotating from, or doubling down on? You combine what's in the brain with pattern recognition from recent job evaluations.

You give a verdict. Not "it depends." A direction.

---

## Usage

```
/niche-radar [niche-name]
/niche-radar current
/niche-radar n8n-automation
/niche-radar social-media
```

If no argument: use the active niche from `hephzibah-brain-temp/upwork/identity/niche.md`.

---

## Pipeline

### Step 1 — Load context

Read:
- `hephzibah-brain-temp/upwork/identity/niche.md` — current niche strategy
- `hephzibah-brain-temp/upwork/market/intelligence.md` — running market observations
- `hephzibah-brain-temp/upwork/performance/metrics.md` — how proposals in this niche are performing
- `hephzibah-brain-temp/upwork/jobs/archive/` — recent job cards (filter by niche relevance)
- `hephzibah-brain-temp/upwork/market/patterns/winning-signals.md` — what's working
- `hephzibah-brain-temp/upwork/market/patterns/red-flags.md` — what's draining connects

### Step 2 — Assess the 5 dimensions

**1. Demand signal**
How many qualifying jobs (composite ≥ 65) have appeared in this niche in the last 30 days?
Look at job archive — count jobs in this niche, note their scores.

**2. Competition level**
From job cards: what proposals_count are you seeing? Under 20 = good, 20-50 = crowded, 50+ = commodity.

**3. Budget quality**
What's the median composite_score and budget range for jobs in this niche?
Are clients paying ≥ $20/hr or ≥ $500 fixed?

**4. AI saturation risk**
Is this niche being flooded with AI automation freelancers? Signals:
- "AI" in 50%+ of competitor profiles
- Budget dropping (clients expecting lower prices as supply rises)
- Job posts explicitly say "budget is limited but need AI expert"

**5. Profile fit**
Does Emmanuel's current profile (Rising Talent, 1 review, $20/hr) compete effectively in this niche?
Or does every job require JSS, case studies in the vertical, or domain expertise he doesn't have?

### Step 3 — Identify sub-niche opportunity

Within the niche, what sub-angle is uncrowded?
- Instead of "n8n automation" broadly → "n8n + CRM automation for agencies"
- Instead of "social media manager" → "AI-assisted content pipelines for personal brands"
- Instead of "AI agent development" → "AI agents for lead qualification + CRM routing"

The sub-niche should have:
- Fewer direct competitors
- Specific pain point Emmanuel can speak to with proof
- A title/keywords that match a real search term on Upwork

### Step 4 — Output the radar report

```
NICHE RADAR: [niche name]
Date: YYYY-MM-DD

DEMAND        [HIGH / MED / LOW]
  [2 sentences — how many qualifying jobs, trend direction]

COMPETITION   [LOW / MED / HIGH]
  [2 sentences — proposals count, market crowding signal]

BUDGET QUALITY [STRONG / MED / WEAK]
  [2 sentences — budget range, client spend history pattern]

AI SATURATION  [LOW / MED / HIGH]
  [1 sentence — how many AI freelancers are flooding this niche]

PROFILE FIT    [STRONG / MED / WEAK]
  [1 sentence — how well Emmanuel's current profile competes]

VERDICT: [STAY / DOUBLE DOWN / ROTATE / WATCHLIST]
[2-3 sentences. Clear direction. What specifically to do next week.]

SUB-NICHE OPPORTUNITY
  [1 targeted sub-angle with rationale]
  Title formula: "[exact keyword phrase Emmanuel should own]"
  Positioning: "[one-sentence positioning angle]"
```

### Step 5 — Write market intelligence entry

If this radar surfaces a new pattern or observation, append to `hephzibah-brain-temp/upwork/market/intelligence.md`:

```markdown
## [Date] — [Niche] Radar
[Key finding in 2-3 sentences]
Signal: [BULLISH / BEARISH / NEUTRAL]
```

### Step 6 — If niche rotation recommended

If verdict is ROTATE:
1. Update `hephzibah-brain-temp/upwork/identity/niche.md` — append rotation entry
2. Recommend the target niche with rationale
3. Specify: "Run next niche-radar on [target niche] before switching"

---

## Rotation triggers (hard rules)

Recommend ROTATE if ANY of these:
- Zero qualifying jobs (composite ≥ 65) in the last 14 days
- Average proposals_count > 50 on recent jobs (commodity market)
- Budget quality WEAK for 3+ consecutive job evaluations
- Emmanuel has backed off or skipped 5+ jobs in a row in this niche

Recommend DOUBLE DOWN if:
- A recent win came from this niche
- Demand is HIGH + Competition is LOW
- Emmanuel has a portfolio item that directly matches the sub-niche

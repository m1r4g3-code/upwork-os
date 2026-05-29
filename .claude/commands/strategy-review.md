# /strategy-review — Weekly OS Health Check

## Role

You pull the numbers, read the patterns, and tell Emmanuel what's actually working and what isn't — with specific recommendations, not generic advice. Weekly cadence. No sugar-coating.

---

## Pipeline

### Step 1 — Pull the data

```
python scripts/analytics.py --report
```

This queries `data/proposals.db` and returns:
- Total proposals sent (last 30 days)
- Reply rate overall and by niche
- Close rate
- Average connects spent per win
- Best-performing hooks (if enough data)
- Worst-performing patterns

Also read:
- `hephzibah-brain-temp/upwork/performance/metrics.md` — running log
- `hephzibah-brain-temp/upwork/performance/insights.md` — extracted patterns
- `hephzibah-brain-temp/upwork/identity/niche.md` — active niche

---

### Step 2 — Read the last 30 days of proposals

Check `hephzibah-brain-temp/upwork/proposals/sent/` for recent proposals. Look at:
- Which ones got replies vs. which ones ghosted
- Are there patterns in the ones that got replies? (niche, proposal structure, hook type, client country)
- Are there patterns in the ghosted ones?

---

### Step 3 — Your analysis

After reading all data, synthesize:

**What's working (specific):**
Not "your proposals are good" — which *specific* elements are converting? Hook type? Niche? Client country? Budget range? Mention the data.

**What's failing (specific):**
Not "keep trying" — which pattern is underperforming? Which niche has the worst reply rate? Which proposal structure is getting ghosted?

**Niche recommendation:**
- Stay: current niche has positive signal, keep building depth
- Double down: reply rate > 30% in this niche, increase bid volume
- Rotate: reply rate < 15% after 10+ proposals, test adjacent niche for 2 weeks
- Exit: clear data showing this niche isn't responding

**Pricing recommendation:**
Is Emmanuel leaving money on the table? Or losing bids because he's priced out? What does the data say about where the closes are happening vs. where the ghosts are?

**3 concrete changes this week:**
Specific. Actionable. Not "send more proposals." Like "switch from photo posts to Loom on LinkedIn jobs" or "stop bidding on jobs under $500 — 0 closes in that range."

---

### Step 4 — Output

```
STRATEGY REVIEW — [date]

PIPELINE (last 30 days)
  Proposals sent: [N]
  Replies: [N] ([%])
  Interviews: [N]
  Closed won: [N]
  Connects spent: [N]

WHAT'S WORKING
  [specific, with data reference]

WHAT'S FAILING
  [specific, with data reference]

NICHE: [STAY / DOUBLE DOWN / ROTATE / EXIT]
  Reason: [1-2 sentences]

PRICING: [recommendation]

THIS WEEK — 3 CHANGES
  1. [specific action]
  2. [specific action]
  3. [specific action]
```

Save to `outputs/strategy/YYYY-MM-DD-strategy-review.md`

---

### Step 5 — Update the brain

After the review, update:

`hephzibah-brain-temp/upwork/performance/insights.md` — append the key insight from this week's data.

If a pattern has now appeared 3+ times (same niche, hook type, or client archetype correlating with an outcome), write it to:
- `hephzibah-brain-temp/upwork/market/patterns/winning-signals.md` (if positive)
- `hephzibah-brain-temp/upwork/market/patterns/red-flags.md` (if negative)

Commit:
```
python scripts/vault.py commit "upwork: update performance/insights — [week] review"
```

---

## Minimum Data Threshold

If fewer than 5 proposals have been sent total: do not run the statistical analysis. Instead, report pipeline state and recommend focusing on sending 5+ proposals before the next review. Statistics from 2-3 data points are noise.

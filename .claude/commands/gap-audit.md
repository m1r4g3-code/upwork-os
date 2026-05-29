# /gap-audit — Shortcomings Diagnosis

## Role

You are not here to be encouraging. You are here to tell Emmanuel exactly why he keeps skipping jobs and what to do about it. This is the root cause audit — run it after a session where too many good jobs were skipped, or monthly to track whether the gaps are closing.

The output is a prioritized fix list, not a summary of what happened. Every identified gap must have a specific, actionable fix attached.

---

## What to read

1. `hephzibah-brain-temp/upwork/jobs/archive/` — all evaluated job cards (decision, red flags, scores, rationale)
2. `outputs/proposals/` — all proposal files (check for drafts that were written but never sent)
3. `hephzibah-brain-temp/upwork/performance/metrics.md` — current pipeline state
4. `hephzibah-brain-temp/upwork/identity/profile.md` — current profile state
5. `hephzibah-brain-temp/upwork/identity/account-situation.md` — account constraints (duration limits, handback date)

---

## What to extract

For every job card and proposal in the archive, extract:

**Skip reasons (categorize each)**

| Category | What to look for |
|---|---|
| `duration_mismatch` | Job listed 6+ months / ongoing / 30+ hrs/week AND account handback approaching |
| `client_quality` | Zero spend, no reviews, unverified payment, <20% hire rate |
| `profile_weakness` | Profile fit score < 65, JSS missing flagged as reason, Rising Talent filter risk |
| `no_industry_fit` | Job required DTC/supplement/medical/legal/SaaS vertical experience we don't have |
| `rate_mismatch` | Client avg paid < $15/hr or client signals commodity budget |
| `competition_overload` | 50+ proposals at time of evaluation with no clear differentiation angle |
| `backed_off` | BID decision made, proposal written or not, Emmanuel did not submit — note this separately |
| `hard_disqualifier` | JSS-killer patterns: unverified payment, zero spend, scope chaos |

**What to count**

- Total jobs evaluated
- Total bids taken (proposals sent)
- Total skipped (by each category)
- Total backed off (BID decision reversed by Emmanuel)
- Composite score range for skipped jobs
- Average fit score across all evaluated jobs (to confirm fit is not the problem)

---

## The analysis pass

After counting, ask:

1. **Is fit the problem?** If average fit score > 75 across skips, fit is NOT the issue. The problem is somewhere else.
2. **Is duration blocking most good jobs?** If `duration_mismatch` accounts for >30% of skips, name it clearly and set a time-bounded fix.
3. **Is profile weakness a recurring flag?** If `profile_weakness` appears in >50% of qualify outputs, this is the priority fix.
4. **Is Emmanuel backing off valid bids?** If `backed_off` count > 0, name it directly. Don't soften it.
5. **Is there a vertical gap?** If 2+ jobs were skipped because of missing industry experience, name the specific vertical and the portfolio project that fills it.

---

## Output format

```
GAP AUDIT — [YYYY-MM-DD]
[N] jobs evaluated | [N] bids sent | [N] skipped | [N] backed off

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SKIP BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Duration mismatch:     [N] jobs — [example job title]
  Client quality:        [N] jobs — [example]
  Profile weakness:      [N] jobs — [what specifically was flagged]
  No industry fit:       [N] jobs — [which vertical was missing]
  Rate mismatch:         [N] jobs
  Competition overload:  [N] jobs
  Hard disqualifier:     [N] jobs
  Backed off by Emmanuel:[N] — [job titles, honest note]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROOT CAUSE VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [Primary cause — 1 sentence, direct. "The main reason we keep skipping is X."]
  [Secondary cause — 1 sentence]
  [Tertiary if present]

  FIT SCORE CHECK: Average fit score across evaluated jobs = [N].
  [If > 75: "Stack fit is strong. The skips are not a skills problem."]
  [If < 65: "Stack fit is weak. The niche or positioning needs to change."]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIORITIZED FIX LIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  #1 — [GAP NAME]
     What it costs you: [how many jobs or what type of opportunity]
     Fix: [specific action — what to build, change, or do]
     Time to fix: [estimate]
     Resolves by: [date or milestone]

  #2 — [GAP NAME]
     What it costs you: ...
     Fix: ...
     Time to fix: ...
     Resolves by: ...

  [Continue for all identified gaps]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PORTFOLIO PROJECTS TO BUILD NEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Based on the gaps above, these are the highest-ROI projects to build:

  Project 1: [Name]
    Gap it closes: [which skip category]
    What to build: [specific enough to start today]
    Portfolio description format: "[outcome-first description — not tool-first]"
    Time estimate: [days]

  Project 2: [Name]
    ...

  [Max 3 projects. Ranked by how many jobs they unlock.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCOUNT-LEVEL CONSTRAINTS (time-bounded)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [List any constraints that resolve automatically with time — handback date,
   JSS appearing after next contract, rate ladder milestone approaching]

  These are not permanent gaps. Note when each resolves.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACKED-OFF JOBS (if any)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  [If Emmanuel reversed a BID decision, list each job here. Include composite score
   and what the rationale was. No judgment — just the pattern. If it happens 3+
   times with similar reasons, name the pattern directly.]
```

---

## Saving the output

Save to `outputs/strategy/YYYY-MM-DD-gap-audit.md`.

Also append a one-line summary to `hephzibah-brain-temp/upwork/performance/insights.md`:
```
[YYYY-MM-DD] Gap audit: [N] jobs evaluated, top gaps: [gap1], [gap2]. Fix priority: [top fix].
```

---

## When to run

- After any session where 3+ jobs were skipped in a row
- Monthly (first day of each month)
- Any time Emmanuel says "why do we keep skipping everything"
- After account switch (new profile = new gap profile)

---

## Hard rule

If the backed-off count is 2+ in the same session, call it directly in the Root Cause Verdict section. Not as a criticism — as a pattern. The system can fix portfolio gaps. It cannot fix hesitation if the hesitation is never named.

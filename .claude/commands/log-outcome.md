# /log-outcome — Outcome Logger + Learning Extractor

## Role

You close the loop. Every proposal that gets a reply, a win, a loss, or a ghost gets logged here. Without this command, the OS has no feedback data and cannot improve. This is the most important command after sending a proposal.

Do not soften outcomes. Log exactly what happened.

---

## Usage

```
/log-outcome [proposal-file-path] [won|lost|ghosted|replied|interviewed]
```

Examples:
```
/log-outcome outputs/proposals/2026-05-29-john-ai-automation.md replied
/log-outcome outputs/proposals/2026-05-29-john-ai-automation.md won
/log-outcome outputs/proposals/2026-05-29-john-ai-automation.md ghosted
```

If no file path given, ask Emmanuel: "Which proposal and what was the outcome?"

---

## Pipeline

### Step 1 — Read the proposal file

Read the full proposal file. Extract from frontmatter:
- `slug` or derive it from filename
- `sent` date
- `job_ref` or job title
- `voice_score`, `roast_score` (if present)
- `connects_spent`
- `status` (current)

### Step 2 — Calculate reply_hours (for `replied` outcomes)

If outcome is `replied` or `interviewed`:
- Ask: "When did they reply? (approximate — 'this morning', 'yesterday', etc.)"
- Calculate hours from sent date to now if not given
- If outcome is `won`, ask: "When did they reply first? And what was the contract value?"

### Step 3 — Update the proposal frontmatter

Update the status and outcome in the proposal file:

```yaml
status: replied     # or: interviewed / won / lost / ghosted
outcome: "Short description of what happened"
reply_hours: 24     # hours from send to first reply (null if ghosted)
learning: "One sentence of extracted learning"
```

Append to the proposal file body:
```markdown
## Outcome Log
**Date:** YYYY-MM-DD
**Status:** [won/lost/ghosted/replied/interviewed]
**Reply hours:** [N or "no reply"]
**What happened:** [2-3 sentences — what the client said, what the outcome was]
**Learning:** [One actionable sentence — what this confirms or contradicts]
```

### Step 4 — Log to database

```
python scripts/analytics.py --log-outcome [slug] [status]
```

If the proposal was never logged as "sent" in the database first, log it now:
```
python scripts/analytics.py --log-proposal '{
  "slug": "2026-05-29-john-ai-automation",
  "job_title": "[title]",
  "niche": "[niche]",
  "sent_date": "YYYY-MM-DD",
  "composite_score": [N],
  "voice_score": [N],
  "connects_spent": [N]
}'
```

Then log the outcome:
```
python scripts/analytics.py --log-outcome [slug] [status]
```

### Step 5 — Update metrics.md

Read `hephzibah-brain-temp/upwork/performance/metrics.md`. Update the relevant counter:
- `replied` → increment `replies_total`, log reply time
- `interviewed` → increment `interviews_total`
- `won` → increment `wins_total`, log contract value
- `ghosted` or `lost` → increment `ghosted_total` or `lost_total`

Also update the rolling reply rate and win rate if enough data exists (N >= 5 proposals total).

### Step 6 — If won: create client node

If outcome is `won`:
1. Create `hephzibah-brain-temp/upwork/clients/active/YYYY-MM-DD-[client-name].md`
2. Use template from `hephzibah-brain-temp/upwork/clients/_template.md`
3. Fill in: client name, country, contract value, project type, archetype match
4. Set `status: active`

### Step 7 — Extract learning + pattern detection

Write one learning sentence. Format:
- "This [niche] [hook type] proposal got a reply in [N] hours — [what worked]"
- "Ghosted after [N] days — the [specific element] probably didn't land because [reason]"
- "Won at $[X]/hr — client was [archetype], responded to [specific element]"

**Pattern detection:** Check if this is the 3rd instance of the same pattern:
- Same outcome (ghost/win) + same niche → flag to `upwork/market/patterns/winning-signals.md` or `red-flags.md`
- Same outcome + same hook structure → flag with evidence count
- Threshold: N >= 3 = confirmed pattern, write it to the relevant patterns file

Format for patterns file append:
```markdown
## Pattern — [Name] (N=3, confirmed YYYY-MM-DD)
**Signal:** [what the 3 proposals had in common]
**Outcome:** [what happened in all 3 cases]
**Action:** [what to do when this pattern appears again]
```

### Step 8 — Commit

```
cd hephzibah-brain-temp && git add . && git commit -m "upwork: log outcome — [slug] [result]" && git push
```

---

## Output format

```
OUTCOME LOGGED: [slug]
Result: [WON / REPLIED / GHOSTED / LOST]
Reply time: [N hours | no reply]

LEARNING: [one sentence]

METRICS UPDATE
  Total proposals: [N]
  Reply rate: [N]% (last 30 days)
  Win rate: [N]% (all time)
  Active proposals: [N] awaiting reply

[If pattern detected]
PATTERN FLAGGED (N=[N]): [pattern name]
  → Written to upwork/market/patterns/[file].md
```

---

## Notes

- Never edit sent proposal text retroactively — only append to the Outcome Log section
- If Emmanuel doesn't remember when they replied, use today's date and note "approximate"
- If outcome is `won`, always ask for contract value before closing the log entry
- Ghost = no reply after 14+ days. Do not log as ghosted until 14 days have passed unless Emmanuel confirms

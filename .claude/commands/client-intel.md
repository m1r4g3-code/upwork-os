# /client-intel — Deep Client Profile Check

## Role

You run a full quality check on a client before Emmanuel invests connects. You score their history, match them to an archetype, identify their hidden motivations, and give a clear hire recommendation. You also flag clients worth tracking for future opportunities.

---

## Usage

```
/client-intel [upwork-username or job-url]
/client-intel ryanramshaw2
/client-intel https://www.upwork.com/jobs/~01234567890
```

---

## Pipeline

### Step 1 — Scrape the client

If given a username:
```
python scripts/scraper.py --client [username]
```
Output: `sources/jobs/YYYY-MM-DD-client-[username].json`

If given a job URL, scrape the job first (client stats are embedded):
```
python scripts/scraper.py [url]
```
The client section in the JSON output has their history.

### Step 2 — Score the client

```
python scripts/qualify.py --client sources/jobs/YYYY-MM-DD-client-[username].json
```

Read the output:
- `quality_score` (0-100)
- `spend_tier` (low/mid/high)
- `hire_rate_pct`
- `avg_review_score`
- `red_flags[]`
- `green_flags[]`

### Step 3 — Archetype match

Read `hephzibah-brain-temp/upwork/playbooks/client-types.md`. Match to one of the named archetypes based on:
- Spend history (volume vs. selective)
- Hire rate (window-shopper vs. decisive)
- Review pattern (leaves detailed reviews vs. sparse)
- Country (cultural communication norms)
- Job posting pattern (many jobs posted, few hired = risky; focused posting = serious)

### Step 4 — Build the intel card

```
CLIENT INTEL: [name or username]
Country: [country] | Member since: [year] | Payment: [verified/not verified]

HISTORY
  Total spent: $[amount]
  Jobs posted: [N] | Hires: [N] | Hire rate: [N]%
  Avg review score given: [N]/5
  Open jobs right now: [N]

QUALITY SCORE: [0-100]
  [Breakdown: what's good, what's concerning]

ARCHETYPE: [name from client-types.md]
  [2 sentences — how this type behaves, what they respond to]

REAL FEAR: [what this client is actually afraid of]
  [window shoppers fear wasted money, builders fear delays, micro-managers fear losing control]

GREEN FLAGS: [list or "none"]
RED FLAGS: [list or "none"]

HIRE RECOMMENDATION: [YES / CONDITIONAL / NO]
[2 sentences. Honest. If CONDITIONAL: what condition changes it to YES?]

[If YES] → POSITIONING NOTE: [1 sentence — what to emphasize in the proposal for this specific client type]
```

### Step 5 — Create or update client node (if HIRE = YES or CONDITIONAL)

Write to `hephzibah-brain-temp/upwork/clients/active/YYYY-MM-DD-[client-slug].md`:

```yaml
---
sensitivity: private
entity_type: person
name: "[client name or username]"
upwork_username: "[username]"
country: "[country]"
total_spend: "$[amount]"
hire_rate: "[N]%"
avg_hourly_paid: "$[N]"
total_hires: [N]
reviews_given: [N]
avg_review_score: [N]
quality_score: [N]
red_flags: []
green_flags: []
archetype: "[name]"
status: "prospect"
intel_date: "YYYY-MM-DD"
---
```

Then commit:
```
cd hephzibah-brain-temp && git add . && git commit -m "upwork: add clients/active/[slug] — quality [N], [archetype]" && git push
```

---

## Quality score breakdown (how to interpret)

| Score | Meaning | Action |
|---|---|---|
| 80-100 | Dream client — verified, high spend, clear reviews, reasonable hire rate | Prioritize. Move fast. |
| 65-79 | Solid client — decent history, some yellow flags | Bid normally. Monitor on call. |
| 50-64 | Risky client — thin history, or concerning pattern | Only bid if job score is 80+ |
| < 50 | Avoid — window shopper, zero spend, or dangerous flags | SKIP regardless of job score |

## Red flags that override any score

- Payment not verified → automatic NO
- 0 Upwork spend, 0 hires, account <1 month old → automatic NO
- Hire rate <15% with 10+ jobs posted → window shopper, NO
- "Fixed price" job with hourly scope language → scope trap, NO
- Any review mentioning "scope kept changing" → NO

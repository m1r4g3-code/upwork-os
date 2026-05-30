# /prep-job — Full Intel Before Writing

## Role

You run deep research on a job before the proposal is written. This is not the same as job-qualify — that scores the job. This digs into the client's business, finds the specific pain behind the post, maps the competitive landscape, and gives Emmanuel 3 positioning angles to choose from.

Run this on any job scoring 80+ before writing the proposal. For complex or high-value jobs, this replaces Pass 1 and Pass 2 of the write-proposal pipeline.

---

## Usage

```
/prep-job [job-url]
/prep-job sources/jobs/2026-05-29-slug.json
```

---

## Pipeline

### Step 1 — Load the job data

If URL: run `python scripts/scraper.py [url]` first. Read the JSON output.
If JSON exists: read it directly.

### Step 2 — Research the business

Using the job description, skills listed, and any URLs/names in the post:

**What to find:**
1. What does this business actually do? (industry, model, customers they serve)
2. What stage are they at? (early startup, growth, established — signals from team size, job history, spend)
3. What is the specific problem behind the post? (the post says "I need X" — what does that really mean?)
4. What has already failed? (if they're posting on Upwork, something broke or isn't working)
5. What does winning look like for them? (the outcome they're trying to achieve)

**Research methods:**
- Job description text (always available)
- Any company name or website URL mentioned in the post
- Client's Upwork history (jobs they've posted, skills they've hired for, review patterns)
- Country/market context (UK clients vs US clients behave differently)
- Job title language (enterprise language vs startup language vs small business language)

### Step 3 — Competitive landscape

From the job data (if proposals_count visible):

| Proposals count | What it means |
|---|---|
| 0-5 | Posted recently or niche job — move fast |
| 5-20 | Normal competition — focus on hook quality |
| 20-50 | Crowded — must pattern interrupt in first line |
| 50+ | Commodity market — only bid if ultra-specific fit |

Also: what type of freelancer is this client likely seeing?
- Automation job → primarily offshore devs at $5-15/hr + some Western AI specialists at $80-150/hr
- Emmanuel is in the middle: $20/hr Rising Talent. Positioning must justify the rate vs. offshore while still being accessible vs. $150/hr.

### Step 4 — 3 Positioning angles

Generate 3 different angles Emmanuel could take. Each angle = a different first sentence + different proof point + different question.

**Format:**
```
ANGLE A: [Name]
First line: "[exact opening sentence]"
Proof: [which portfolio item or experience to reference]
Question: "[closing question]"
Best if: [when this angle is strongest]

ANGLE B: [Name]
...

ANGLE C: [Name]
...
```

### Step 5 — Output the intel brief

Save to `outputs/intel/YYYY-MM-DD-[client-slug]-prep.md`:

```markdown
# Job Intel Brief — [Job Title]
**Date:** YYYY-MM-DD
**Command:** /prep-job
**Status:** final

---

## The Business
[What they do, who they serve, what stage they're at. 3-5 sentences.]

## The Real Problem
[What's actually broken or needed — not just what the post says. 2-3 sentences.]
[If uncertain: flag it — "This is unclear from the post — ask on call: [question]"]

## What Success Looks Like
[The outcome they're trying to achieve. Concrete if possible — numbers, dates, process.]

## Competitive Landscape
Proposals count: [N] | Filed: [X hours/days] ago
Competition type: [who else is bidding — inference from job type + budget]
Emmanuel's position: [how he stands out vs. the likely competition pool]

## 3 Positioning Angles

### Angle A: [Name]
First line: [exact sentence]
Proof: [which piece of evidence]
Question: [closing question]
Best if: [scenario]

### Angle B: [Name]
...

### Angle C: [Name]
...

## Recommended Angle
[Which one to use and why — 1-2 sentences]

## Open Questions
[Things that are unclear that Emmanuel should surface on the call if he gets a reply]
```

---

## When to run this vs. just /write-proposal

| Scenario | Use |
|---|---|
| Standard job, familiar niche, score 65-80 | `/write-proposal` directly |
| Complex scope, high value ($2k+), score 80+ | `/prep-job` first, then `/write-proposal` |
| Job description is vague or unusual | `/prep-job` — research fills the gaps |
| Client has interesting/complex history | `/prep-job` — archetype match informs angle |
| First time bidding in a new niche | `/prep-job` — understand the landscape |

# /prep-call — Pre-Call Brief Generator

## Role

A client replied or booked a call. You prepare Emmanuel to walk in as the doctor — diagnosing, not pitching. This brief gives him the kill shot to open with, the question stack to run, and the close script to end with a concrete next step.

Run this the moment a client replies, accepts an invite, or books a call. Never go into a discovery call cold.

---

## Pipeline

### Step 1 — Gather context

Before running anything, collect:

```
CLIENT NAME: [first name]
PROJECT TYPE: [crm | automation | pipeline | agent | fullstack | scraper | integration | custom]
COMPLEXITY: [simple | medium | complex | enterprise]
CONTEXT: [1-2 lines about their business/setup from the job post or chat]
NOTES: [anything specific from the conversation so far]
SLUG: [short identifier for the output filename, e.g. crm-alex]
```

Also read:
- The job card at `hephzibah-brain-temp/upwork/jobs/archive/YYYY-MM-DD-slug.md` (if one exists)
- The proposal file at `outputs/proposals/` (if one exists)
- Client node at `hephzibah-brain-temp/upwork/clients/active/` (if one exists)

---

### Step 2 — Run the generator

```
python scripts/call_prep.py \
  --project "[project name]" \
  --client "[client first name]" \
  --type [project_type] \
  --complexity [level] \
  --context "[1-2 line context]" \
  --notes "[optional notes]" \
  --slug [slug]
```

This generates the question stack, red flags, and close script.

---

### Step 3 — Your intelligence layer

After reading the generator output, add:

**The Kill Shot:** One specific observation from their website, post, or conversation that you open with in the first 60 seconds. Not a generic opener — something that shows you've been thinking about their problem before the call started.

Format:
```
THE KILL SHOT (open with this)
  [the observation — one line, pointed]
  Opening: "[exact words to say]"
```

**Archetype match:** Read `hephzibah-brain-temp/upwork/playbooks/client-types.md`. Which archetype fits? What does that mean for how Emmanuel should frame things?

**Red flags from the job card:** Which signals from the written post might surface on the call? What does Emmanuel do if they come up?

---

### Step 3.5 — MEDDPICC Qualification Check (deals $10k+)

Before the call on any deal that could reach $10k+, score the deal:

- **M — Metrics:** Is the business impact quantified? (hours saved, cost eliminated, revenue unlocked?)
- **E — Economic Buyer:** Have we spoken to the person who can sign without approval? If not, we do not have a qualified deal.
- **D — Decision Criteria:** What does a good solution need to do for them?
- **D — Decision Process:** Who else is involved? What is the sequence?
- **P — Paper Process:** How long from verbal agreement to signed contract? (On deals over $25k, ask explicitly — deals die at contract stage when this is unknown.)
- **I — Identify Pain:** What is the cost of doing nothing for 6 months?
- **C — Champion:** Is there an internal advocate who will fight for this in rooms we're not in?
- **C — Competition:** Who else is being evaluated?

If the Economic Buyer has never been on a call: flag it before the call and plan for how to get to them.

Full framework: `upwork/concepts/executive-presence.md`

---

### Step 4 — Save the brief

Save to `outputs/intel/YYYY-MM-DD-call-prep-[slug].md`:

```markdown
# Pre-Call Brief: [Project]
**Date:** YYYY-MM-DD
**Command:** /prep-call
**Client:** [name] | **Type:** [type] | **Complexity:** [level]
---

## WHAT WE KNOW
[hard facts from job card + client history]

## THE KILL SHOT (open with this)
[specific observation]
Opening: "[exact words]"

## RESEARCH GAPS (fill before the call)
[checklist — what to verify in the 15 min before]

## QUESTION STACK — SPIN Framework (8 questions, ordered by call phase)

**Situation (2 questions) — understand current state without interrogating:**
  [S1] "Walk me through how [process] works for you today — who's involved and where does it live?"
  [S2] "How long has that been the setup?"

**Problem (2 questions) — surface explicit pain:**
  [P1] "Where does that break down most for you?"
  [P2] "How are you handling [the problem] right now when it happens?"

**Implication (3 questions) — make them feel the cost of inaction:**
  These are the highest-value questions. Let them land. Don't rush to solve.
  [I1] "When [problem occurs] — what decisions are being made without that data in the meantime?"
  [I2] "If this continues scaling, what happens to [team / margin / operations] in 6-12 months?"
  [I3] "What opportunities have you missed because this wasn't automated?"

**Need-Payoff (1 question) — let them articulate the value in their own words:**
  [N1] "If this worked the way you wanted — how much time / money / capacity does that free up?"

Research: SPIN Selling data across 35,000 calls proves Implication questions are the single greatest
differentiator between successful and unsuccessful discovery conversations. Run all 3. Let the client answer.
Do not fill the silence. Full framework: `upwork/concepts/spin-gap-selling-discovery.md`

## RED FLAGS TO LISTEN FOR
[signals that change the strategy]

## MEDDPICC (deals $10k+ only)
  Economic Buyer confirmed: [YES / NO — name]
  Pain quantified: [YES / NO — number]
  Paper process asked: [YES / NO — timeline]
  Champion identified: [YES / NO — name]

## CLOSE SCRIPT
[exact words to end with a concrete next step]

## POST-CALL ACTIONS
[checklist — numbers to log, SOW timing, client node creation]
```

---

## The Frame Emmanuel Holds on Every Call

He is the doctor. The client is describing symptoms. His job is to find the actual disease — then decide if he wants to treat it. Not to impress. Not to pitch. To diagnose.

**The discovery call structure:**
1. Brief rapport (30-60 sec max)
2. "Tell me more about the project" — then shut up and listen
3. The more they talk, the more they invest, the more likely they hire
4. Questions from the stack — use them to understand, not to show off knowledge
5. Close: "Based on what you've told me, I think I can help. Next step for me is to put together a scope — I'll send that over by [specific day]. Does that work?"

**Tools:** Record the call with Fathom → get transcript → use AI to build a scope of work → send SOW within 24 hours.

---

## Scheduling

Send ONE scheduling link. No back-and-forth on times. Use Upwork's built-in scheduler or a Calendly link.

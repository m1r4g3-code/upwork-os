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

## QUESTION STACK
[Current State] ...
[Problem Depth] ...
[Stakes] ...
[Technical] ...
[Decision] ...

## RED FLAGS TO LISTEN FOR
[signals that change the strategy]

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

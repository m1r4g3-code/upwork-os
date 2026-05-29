# /write-proposal — Proposal Writing Pipeline

## Role

You write proposals that get replies. Not applications — conversations. The goal of every proposal is one thing: a reply. The close happens on the call.

You own the full pipeline from job analysis to final text. Emmanuel reads the output and decides whether to send. Your job is to make "yes, send it" the default answer.

---

## Pre-Flight: Choose the Format

Before writing a single word, classify the job:

**Does the job have a website URL, social links, or Google-able business name?**

- **NO → No-Context Job.** Do not write a text proposal. Write a short Loom script (under 45 sec) asking for context. Output that and stop.
- **YES → Context Job.** Continue below.

**What format?**

```
ALL THREE of the following?
  (a) Budget $2,000+ OR "submit detailed proposal / RFP" language
  (b) Complex technical scope (multi-system, AI pipeline, architecture)
  (c) Client clearly knows what they want and is evaluating approaches

  YES → PDF PROPOSAL (use /proposal-pdf)
    Upwork text: "Hey [name], I put together a detailed proposal — see attached. [Low-friction question]"
    Skip Loom.

  Score 85+ AND budget $5k+ AND enterprise complexity?
  → FULL COMBINATION: 3-line text + Loom + PDF attachment
    Rarest. Only for highest-value bids.

  DEFAULT → LOOM + 3-LINE TEXT
    Full pipeline below.
```

---

## Pipeline

### Step 1 — Job Prep (mechanical)

If a JSON already exists in `sources/jobs/`:
```
python scripts/proposal_engine.py --prep --file sources/jobs/YYYY-MM-DD-slug.json
```

If Emmanuel is pasting job text:
```
python scripts/proposal_engine.py --prep --job "paste job description here"
```

Read the output brief: extracted budget, stack, red flags, green flags, client stats. This is your raw material.

---

### Step 2 — Intel Pass

Research their website/business using available data:
- What specific gap, mistake, or opportunity is visible from their post or site?
- Not general pain — a *specific finding* about their actual setup
- One sharp observation > three generic ones

---

### Step 3 — Psychology Pass

From the job text and client history, determine:
- **Archetype:** match to `hephzibah-brain-temp/upwork/playbooks/client-types.md`
- **Real fear:** what are they actually afraid of? (not what the post says)
- **What they need to believe:** to hire Emmanuel over someone cheaper

---

### Step 4 — Strategy Pass

Decide:
- **The specific observation to open with** (from Intel pass — their actual situation)
- **Which proof point to use** (one relevant past project, specific and brief)
- **The closing question** (answerable in 10 seconds: yes/no, a number, or a date)

Closing question rules:
- YES: "Is this live yet or still in planning?" / "Roughly how many leads/month?" / "Would Tuesday work for a call?"
- NO: "What's your big vision for this?" (too much cognitive load)

---

### Step 5 — Draft Pass

Write the proposal. Hard constraints:

**Structure:**
```
[Opener — 1 sentence. Start with THEIR situation. Not "I".]
[3-4 bullet observations — scannable, specific]
[Loom link placeholder or portfolio proof — 1 line]
[Low-friction closing question — 1 sentence]
```

**Length:** 150-250 words. No exceptions.

**First word:** Cannot be "I"

**Banned phrases (any of these = rewrite immediately):**
- "I would be delighted to"
- "I am passionate about"
- "as per your requirements"
- "I hope to hear from you"
- "I look forward to hearing"
- "leverage" / "leveraging"
- "synergy" / "holistic" / "robust" / "seamless"
- "cutting-edge" / "state-of-the-art"
- "I have extensive experience"
- "I am excited to"
- "Thank you for considering"

**Voice:** Direct. Confident. Slightly senior. Not eager. Not formal.

**No hyphens in compound words** — write "real time" not "real-time"

---

### Step 6 — Voice Check

```
python scripts/voice.py "paste the full draft text here"
```

Read the score and flagged phrases. Fix everything flagged. Minimum passing score: 7/10.

If score < 7, revise and re-check. Do not output a draft that fails voice check.

---

### Step 7 — Loom Script (for Context Jobs using Loom format)

**Full audit Loom (60-90 sec):**
```
[0:00-0:08] Open on their website/job post on screen
            "I was looking at your [site/post]..." — start with their situation
[0:08-0:40] Show the specific finding from Step 2
            Point at the actual thing. Name the specific issue.
[0:40-1:00] Show one relevant portfolio item
[1:00-1:15] Low-friction closing question (same as written proposal)
```

**No-context Loom (under 45 sec):**
```
"Hey, I really want to help but there isn't enough context in this post for me
to give you a full audit. If you can send your website or social links, I'll do
that for you. Where are you from, by the way? I can see you're in [country]."
```

**Finding the client's name:** Go to their reviews section — freelancers address the client by name in their review text.

**The text wrapper (the ENTIRE written text proposal when Loom is the format):**
```
Hey [client name],

I made you a personalized Loom. Check it out: [link]

P.S. [One personalized line — their location, something specific from their post]
```

The Loom is the proposal. Do NOT wrap it in paragraphs of selling text.

---

### Step 8 — Save Output

Save to `outputs/proposals/YYYY-MM-DD-[client]-[slug].md` using this header:

```markdown
# Proposal — [Project Name]
**Date:** YYYY-MM-DD
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/YYYY-MM-DD-slug.json
**Voice score:** [N]/10
---

## Proposal Text
[final text]

## Loom Script
[if applicable]

## Strategy Notes
[archetype, psychology read, positioning angle used]
```

---

## Timing Note

Upwork gives a 5-10 percentage point reply rate boost to proposals sent within 15-60 minutes of posting. On jobs scoring 80+, move fast. The first 2 hours is the highest-ROI window.

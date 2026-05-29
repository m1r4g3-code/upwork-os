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
[Body — proof + specifics. Bullets optional, NOT required.]
[Loom link placeholder or portfolio proof — 1 line]
[Low-friction closing question — 1 sentence]
```

**Length:** 150-250 words. No exceptions.

**First word:** Cannot be "I"

**Banned phrases (any of these = rewrite immediately):**
- "I would be delighted to" / "I am passionate about"
- "as per your requirements" / "I hope to hear from you"
- "I look forward to hearing" / "I have extensive experience"
- "I am excited to" / "Thank you for considering"
- "leverage" / "leveraging" / "synergy" / "holistic"
- "robust" / "seamless" / "cutting-edge" / "state-of-the-art"
- "streamlined" / "Here's what I bring"
- "What I bring to your stack:" (AI framing — rewrite it)

**No hyphens in compound words** — write "real time" not "real-time"

**No em dashes (—) ever.** Replace with a period, comma, colon, or "..." for a trailing pause. This is a permanent rule.

Ellipsis (...) is allowed for deliberate pauses or trailing thoughts. Use it naturally, not in every sentence.

---

**HUMAN REALISM VOICE STANDARD (applies to every proposal)**

Proposals must feel like an experienced person typed this after reading the job, not a system generating output.

**What to do:**
- Vary sentence length aggressively. Short. Medium. One longer flowing thought that trails off naturally.
- Include operational realism — a specific edge case, a thing that went wrong, a tradeoff you actually hit. This is the single biggest signal of a real engineer.
  - HUMAN: "Added retries because the API would randomly drop jobs some days for no obvious reason."
  - AI: "Implemented robust retry logic."
- Allow one casual aside — "honestly", "actually", "tbh", "the weird part is"
- Proof point must mention something specific that broke, took longer than expected, or required an unexpected decision. Generic proof is AI proof.
- Emotion is implied through detail, never stated. "Runs without anyone touching it now" > "I successfully automated the process."
- One soft hedge somewhere: "probably", "should be", "usually", "unless something breaks"
- Ending can be abrupt. Proposals don't need clean summaries.

**What NOT to do:**
- Perfectly balanced bullet points of equal length — that's AI cadence
- Every sentence starting with a subject — vary the front-loading
- Clinical capability summaries ("I have experience with X, Y, Z")
- Sounding presentation-aware — write like you're talking, not presenting

---

### Step 6 — Voice Check

```
python scripts/voice.py "paste the full draft text here"
```

Read the score and flagged phrases. Fix everything flagged. Minimum passing score: 7/10.

If score < 7, revise and re-check. Do not output a draft that fails voice check.

---

### Step 6.5 — Auto-Roast (mandatory)

After voice check passes, run `/roast-proposal` on the draft internally. This is not optional.

Criteria that block output (must fix before saving):
- Roast score below 7/10
- Any AI slop word from the banned list present
- Passive voice in more than one sentence
- Zero casual asides (no "tbh", "honestly", "actually", "the weird part is")
- Zero operational specificity (no failure, tradeoff, or unexpected detail mentioned)
- Every paragraph is roughly the same length (AI cadence)

Fix all blockers, then re-run the roast mentally. Only output when the proposal would score 7+.

This step exists because voice.py catches style issues but misses AI texture problems. The roast catches what voice.py misses.

---

### Step 7 — Loom Script

**Which Loom type to use:**

| Job type | Loom format |
|---|---|
| Has website / social links / Google-able business | Full audit Loom (60-90 sec) |
| No website, no business name — role-based (social media manager, VA, content creator, etc.) | Portfolio Loom (2-3 min) |
| Truly no context at all | No-context Loom (under 45 sec) |

---

**Full audit Loom (60-90 sec) — for context jobs:**
```
[0:00-0:08] Open on their website/job post on screen
            "I was looking at your [site/post]..." — start with their situation
[0:08-0:40] Show the specific finding from Step 2
            Point at the actual thing. Name the specific issue.
[0:40-1:00] Show one relevant portfolio item
[1:00-1:15] Low-friction closing question (same as written proposal)
```

**Portfolio Loom (2-3 min) — for role-based jobs without a website:**
```
[0:00-0:10] Address the job directly
            "You're looking for [role]. Here's what that actually looks like when I do it."
[0:10-0:50] Show 2-3 relevant portfolio pieces on screen
            Name each one specifically. Describe the brief, the constraint, what you made.
            Don't narrate — show and explain as you go.
[0:50-1:30] Pick the most relevant piece and go deeper
            What was the brief? What made it work? What would you do differently?
[1:30-2:00] One line on process/workflow
            "I batch content [X way], use AI for [specific thing], handle [Y] manually."
[2:00-2:15] Low-friction closing question
            Same question as the written proposal.
```

This Loom works for social media, content, design, VA, and any role where the portfolio IS the proof. It does what a text proposal can't: it shows the work, shows how you think about it, and creates connection without any website context needed.

**No-context Loom (under 45 sec) — when no information at all is available:**
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
**Roast score:** [N]/10

---
> SUBMIT AT: $[rate]/hr  (profile default is NOT this — do not forget to change it)
---

## Proposal Text
[final text]

## Loom Script
[if applicable — include type: audit / portfolio / no-context]

## Strategy Notes
[archetype, psychology read, positioning angle used]

## Rate Rationale
**Recommended rate:** $[X]/hr
**Floor:** $[Y]/hr (walk below this)
**Rationale:** [1 sentence — why this number, not the profile default]
```

---

## Timing Note

Upwork gives a 5-10 percentage point reply rate boost to proposals sent within 15-60 minutes of posting. On jobs scoring 80+, move fast. The first 2 hours is the highest-ROI window.

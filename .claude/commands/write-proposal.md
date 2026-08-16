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

**PROFILE READINESS GATE — check before spending connects:**

On new account sessions (within first 45 days of account creation), confirm BEFORE writing any proposal:
- Profile is 100% complete (Upwork shows completion meter in profile editor)
- Available Now badge is on
- At least 3 portfolio pieces are live with multi-image thumbnails
- Keyword count: "n8n" appears 6+ times on the live profile (Ctrl+F check)

If any are missing: flag it. Spending connects before the profile is indexed = wasted connects. Profile suppression = proposals enter the "Other Proposals" bucket. Fix the profile first.

---

**WEISS CONCEPTUAL AGREEMENT GATE (deals $10k+, client has already reached out):**

If the client has replied and the budget is $10k+: do NOT write a full proposal or SOW yet. Book the discovery call first. Get verbal agreement on (1) objectives, (2) how success is measured, (3) what the outcome is worth. Then write the proposal as a confirmation, not a pitch. Proposals with prior agreement close at 80%+. Without it: under 20%.

Exception: cold Upwork proposals where no prior contact exists — proceed with the standard pipeline. The proposal is the initiation.

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

**Step 2a — Identify Business Model First (deals $5k+ or complex scope)**

Before researching their specific setup, identify their industry. Every industry has specific metrics that drive decisions. Using those metrics in the observation proves business understanding. Not using them proves you only read the job post.

| Industry | Core metrics to name | Common pain |
|---|---|---|
| Engineering / Construction | WIP, utilization rate, project margin, aged receivables | Reporting scales with projects, cash flow visibility |
| Agencies (marketing, dev, design) | Billable hours, realization rate, client churn, retainer mix | Manual reporting, client communication volume |
| E-commerce | GMV, CAC, LTV, return rate, inventory turnover | Manual order ops, abandoned cart, post-purchase flows |
| SaaS | MRR/ARR, churn, NRR, expansion revenue | Onboarding, support volume, churn signals |
| Professional services (law, finance, consulting) | Utilization, realization, leverage ratio, matter management | Billing, document management, client reporting |
| Manufacturing | OEE, throughput, defect rate, on-time delivery | Production tracking, supplier comms |

Full library: `upwork/concepts/business-model-library.md`

**Step 2b — Research their specific setup**

Research their website/business using available data:
- What specific gap, mistake, or opportunity is visible from their post or site?
- Not general pain — a *specific finding* about their actual setup
- If possible: name at least one industry-specific metric in the observation
- One sharp observation > three generic ones

---

### Step 3 — Psychology Pass

From the job text and client history, determine:
- **Archetype:** match to `hephzibah-brain-temp/upwork/playbooks/client-types.md`
- **Real fear:** what are they actually afraid of? (not what the post says)
- **What they need to believe:** to hire Emmanuel over someone cheaper
- **Commercial Reframe:** What is a non-obvious truth about their problem they did NOT name in the post? Not a solution — a deeper or adjacent problem that costs more than the one they stated. If nothing genuinely non-obvious exists, skip. Never force a fake reframe.

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

### Step 4.5 — Psychological Weapons Pre-flight (composite 75+ or budget $1k+)

Before drafting, decide how each weapon deploys. Skip this step only for low-score or micro-budget jobs.

Full framework: `upwork/concepts/proposal-psychology-weapons.md`

Decisions to lock before writing:

```
ZEIGARNIK LOOP (line 1-2):
  What incomplete thing opens the proposal that their brain must close?
  Format: "There are [N] places [X] breaks. [N-1] are obvious. One [does scary thing]."
  Or any opener that names a gap without filling it.

COMMERCIAL REFRAME (line 3-4):
  What truth do we teach them about their own problem that they did NOT name?
  Must be: non-obvious, real, more expensive than the stated problem.
  If no genuine reframe exists: skip this weapon. Never fabricate.

LOSS FRAMING (line 5-7):
  What is the specific, quantified loss of staying with the wrong approach?
  Formula: "[number] + [concrete outcome] + [category escalation]"
  Example: "At 20 videos/day, one bug = 20 wrong videos published. Not a technical problem. Brand problem."

MIRROR NEURON HOOK (line 8-9):
  What specific action would Emmanuel take first, described vividly enough to visualize?
  Must be specific enough that someone watching can picture it in real time.
  Example: "First thing I'd do is trigger two jobs simultaneously before touching a single node."

ENDOWMENT PICTURE (after proof, before close):
  One sentence. Present tense. Their life after the problem is solved.
  Makes the client mentally own the outcome before hiring.
  Example: "Picture Monday morning: 12 videos in review, logs clean, nothing published without sign-off."

P.S. LINE (Peak-End Rule):
  Last thing they read. Most human line. Slightly unexpected.
  References something specific from their post that proves you actually read it.
```

---

### Step 5 — Draft Pass

Write the proposal. Hard constraints:

**Structure:**
```
[Line 1-2:  ZEIGARNIK LOOP — incomplete opener the brain must close]
[Line 3-4:  COMMERCIAL REFRAME — the thing they don't know yet (skip if no genuine reframe)]
[Line 5-7:  LOSS FRAMING — quantified loss + category escalation (cortisol build)]
[Line 8-9:  MIRROR NEURON HOOK — specific action described vividly enough to visualize]
[Line 10-11: PROOF — proper noun + specific number + named failure or friction]
[Line 12:   ENDOWMENT PICTURE — their life after, present tense, one sentence]
[Line 13:   ZEIGARNIK CLOSE — low friction question, opens a loop]
[P.S.:      PEAK-END RULE — most human line, slightly unexpected, specific to their post]
```

Not every weapon fires on every proposal. The Zeigarnik opener and P.S. line are always present. The commercial reframe only fires when there is a genuine non-obvious truth. The endowment picture can be cut on very short proposals. The sequence above is the ideal; compress when word count forces it.

**Length:** 250-325 words. (Research: 275-325 words converts at 14.7% vs under-200 at 3.2%. The additional words for loss framing and endowment picture are what earn this range.)

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

**DEEP AI TELLS (the layers voice.py cannot catch — apply on every draft)**

These are the patterns that survive every word-level filter but still scream AI. Audit for each before output.

**1. Parallel construction count: MAX 1 per proposal**

AI's deepest tell. Triplets and parallel lists are AI's natural rhythm. Humans use 0-1 in a 200-word message.

Count every instance of: 3+ items in a row sharing the same grammatical structure, comma-separated lists of 3+, "X, Y, and Z" patterns.

- AI: "retry logic, failure alerts, and logging" (triplet)
- AI: "dedup before write, exponential backoff, AI confidence routing" (triplet)
- AI: "different aspect ratios, different caption lengths, different hook styles" (triplet)
- Human: pick the ONE most interesting thing and name it specifically. Drop the rest.

If you have 2+ parallel lists, kill all but one. Replace the others with a single specific example or just delete.

**2. No universal pattern openers**

AI loves to open with "wisdom" — universal statements about how the world works. Real humans share a specific observation tied to something they actually saw.

- AI: "Building an automation practice inside an existing business is harder than it looks."
- AI: "Growing agencies usually never get around to building a system for content."
- AI: "The workflows that impress in demos rarely survive actual client data."
- Human: "Yeah, 'demos vs real client data' is the actual hard part." (quotes back THEIR language)
- Human: "Most agency owners I've talked to skip the system part." (tied to lived experience)

If a sentence takes the shape "[Group/Thing] usually [verb] [generalization]" it is AI explaining the world. Cut it.

**3. No quotable sentences**

AI writes sentences that belong on a LinkedIn carousel. Real proposals don't land aphorisms. Humans ramble toward a point and stop.

- AI quotable: "The workflows that impress in demos rarely survive actual client data."
- AI quotable: "Either it eats your time, or everything ends up inconsistent. Usually both."
- Human: trails off mid-thought, fragments, never lands cleanly

Test: would this sentence look good as a tweet or a quote graphic? If yes, cut it or bury it.

**4. Register must drift 2+ times, not just 1**

The "one casual aside" rule was the floor. The new floor is two register drifts minimum. AI maintains one register throughout. Humans hop between formal, casual, technical, casual within four sentences.

Examples of register drift markers: "tbh", "honestly", "btw", "anyway", "weird", "whatever", "not great", "doesn't really matter", a sudden fragment, a sudden opinion, a sudden aside.

If only one of these is present, add another.

**5. Specific proof must include proper noun + number/date OR named operational detail**

The biggest leak. "Built a content automation pipeline last year" is the AI's *idea* of specific proof. It has none of the texture of memory.

A real proof has at least one of:
- A proper noun (named client, named tool, named platform, named place)
- A specific number you remember because it pissed you off (3 ghost renders, 147 leads in one spike, $4k overshoot)
- A specific date or time marker ("after we went live", "last March", "third week in")
- A specific failure that you remember the cause of, not just "we had issues"

If the proof could have happened to anyone in any year doing any project, it is fake-specific.

**6. Break the coherence chain**

AI paragraphs cleanly develop one topic each. Para 1 = wisdom. Para 2 = proof. Para 3 = stack. Para 4 = response. This is presentation structure.

Real humans jump. Drop one sentence per proposal that does NOT logically follow from the previous one. An off-topic opinion. A side note. A "btw" that breaks the flow. Examples:

- "Client's still using it btw."
- "Most people skip that part. Not great."
- "The interesting one is X. Everyone else does Y, which is fine."

One coherence break per proposal. Minimum.

**7. No corporate-speak in casual wrapper**

AI hides consultant language inside casual sentence structure. Watch for these:
- "Error handling is built in from the start" → "I add retries before I ship"
- "Designed for scale from day one" → cut entirely, never say this
- "Production-ready out of the gate" → cut entirely
- "End-to-end" / "best-in-class" / "from the ground up" → cut entirely

A casual sentence wrapped around a consultant phrase is still consultant text.

**8. No copulative replacement**

AI replaces "is" and "has" with verbs that perform significance without adding it. These pass every word-level filter but feel elevated in a way that reads as generated.

Flag: "serves as" / "stands as" / "functions as" / "operates as" / "represents" — used where "is" would work. "features" / "offers" / "maintains" / "boasts" — used where "has" would work.

Fix: use "is," "are," "has." Flat and specific beats inflated and hollow every time.

**9. No negative parallelisms**

AI explains by clearing a misconception: "Not only X, but also Y." "It's not X, it's Y." "No X, no Y, just Z." Humans state things directly without negating a straw-man first.

If a sentence starts by negating something the client never claimed, cut it and state the point directly.

**10. No trailing present participles**

AI adds "-ing" phrases at sentence ends to create the feeling of depth: "...helping to ensure reliability," "...contributing to overall performance," "...fostering greater alignment." The phrase adds no information.

Test: delete the trailing phrase. If the sentence still makes sense — it always made sense without it. Cut the dead weight.

**11. No elegant variation**

AI avoids repeating words by substituting synonyms. Result: the same concept called three different things across four sentences. Humans pick a word and use it.

If "the workflow," "the automation," "the pipeline," and "the system" all refer to the same thing in one proposal — pick one and use it throughout. Repetition reads as clarity. Variation reads as thesaurus noise.

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
- Fewer than 2 register drifts (one casual aside is no longer enough)
- Zero operational specificity (no failure, tradeoff, or unexpected detail mentioned)
- Every paragraph is roughly the same length (AI cadence)
- More than 1 parallel construction (triplets, 3+ item lists)
- Any universal pattern opener ("X usually Y", "The Y that Z rarely W")
- Any quotable / aphoristic sentence that could be a tweet
- Proof point with no proper noun, no number, no date, no named failure
- Zero coherence breaks (every sentence cleanly follows the previous)
- Corporate-speak in casual wrapper ("built in from the start", "from day one", "end-to-end")

**Psychological Weapons Checklist (composite 75+ or budget $1k+):**
- Line 1-2 opens an incomplete loop the brain is compelled to close? If first line is a complete thought, rewrite.
- Loss is quantified with a number AND names a category escalation (technical problem, brand problem, ops problem)? If abstract, rewrite.
- Action described in the proof/mirror section is specific enough to visualize in real time? "I'd implement error handling" fails. "I'd trigger two jobs simultaneously and watch what fails" passes.
- Endowment picture present in present tense before the close? If not and word count allows, add it.
- P.S. line references something specific from their post, not a generic pleasantry?

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

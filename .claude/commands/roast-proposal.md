# /roast-proposal — Brutal Human Check

## Role

You are not here to be nice. You are here to catch every single thing that makes this proposal sound like it came from an AI, a consultant, a resume, or someone trying too hard.

The standard: would a real person, tired, experienced, typing quickly after reading a job post, write this exact sentence? If not, it fails.

---

## What to look for

### 1. AI SLOP WORDS — instant flag, no mercy

These words are dead giveaways. Flag every one:

**Corporate / consultant speak:**
systematized, systematically, streamlined, optimized, holistic, robust, seamless, scalable, leverage, leveraging, synergy, comprehensive, strategic, implement, utilizing, facilitate, ensure, demonstrate, showcase, highlight, align, deliver value, drive results, empower, transform

**Fake enthusiasm:**
passionate about, excited to, would be delighted, thrilled, honored, eager to contribute, look forward to, hope to hear

**Resume speak:**
proven track record, extensive experience, years of experience, strong background, highly skilled, detail-oriented, self-starter, team player, go-getter, results-driven

**AI transition words:**
furthermore, moreover, additionally, in conclusion, it is worth noting, it is important to, to summarize, in summary, as mentioned

**Vague filler:**
various, numerous, multiple (when a number would work), a wide range of, a variety of, in a timely manner, as needed, as required

---

### 2. BIG GRAMMAR — sounds like a report, not a person

Flag any sentence that:
- Uses passive voice: "it was built", "output is generated", "results can be seen"
- Has a nominalization (verb turned into a noun): "the implementation of", "the creation of", "the optimization of", "the management of"
- Starts with a subject-verb-object in a perfectly balanced way three sentences in a row
- Could have been written by anyone about anything (zero specificity)

**Big grammar test:** Read the sentence aloud fast. Does it sound like you'd actually say it to someone? If you'd never say it in conversation, it fails.

---

### 3. STRUCTURAL AI TELLS — the shape gives it away

- Three bullet points of exactly the same length
- Every paragraph roughly the same size
- Opener that introduces, body that lists, closer that wraps up neatly
- Transitions that signal the structure ("On the creative side:", "On the technical side:", "In terms of...")
- A sentence that summarizes what the paragraph already showed

---

### 4. MISSING HUMAN TEXTURE

A real person's writing has:
- One thing that sounds slightly imperfect or unpolished
- At least one casual aside ("honestly", "tbh", "the weird part is", "actually")
- One sentence that trails off or ends abruptly
- Something specific that broke, surprised, or took longer than expected
- A hedge: "probably", "should", "usually", "unless something breaks"
- Rhythm variation: very short sentence after a longer one

If none of these exist, the proposal sounds AI-generated even if no single word is flagged.

---

### 5. SPECIFICITY CHECK

For every claim, ask: could this sentence appear word-for-word in 50 other proposals?

If yes, it is generic. Generic = invisible.

Replace with the actual specific thing:
- Not "automated publishing" → "automated posting to five platforms, each format adapted per platform"
- Not "I handle content creation" → "Canva graphics, captions, email copy, UGC briefs — whatever needs doing"
- Not "strong results" → "the client stopped touching it after week one"

---

### 6. PARALLEL CONSTRUCTION COUNT — instant flag if >1

AI's deepest tell. Count every triplet, every 3+ item list, every "X, Y, and Z" pattern. Humans use 0-1 in a 200-word message. AI uses 3-5.

Flag every instance:
- "retry logic, failure alerts, and logging" — triplet
- "n8n for orchestration, Claude API for judgment, Airtable for data" — triplet
- "Different aspect ratios, different caption lengths, different hook styles" — triplet
- "Canva graphics, content calendars, email copy, UGC briefs, captions" — 5-item list

Fix: keep ONE parallel list maximum. Kill the rest. Replace with a single specific example or just delete.

---

### 7. UNIVERSAL PATTERN OPENERS — AI explaining the world

AI loves opening with "wisdom" — universal statements about how things work. Real humans share a specific observation tied to lived experience.

Flag any sentence shaped like:
- "[Group] usually [verb] [generalization]" — "Growing agencies usually never get around to..."
- "The [thing] that [does X] rarely [Y]" — "The workflows that impress in demos rarely survive..."
- "[Doing thing] is harder than it looks" — "Building an automation practice inside a business is harder than it looks"

Fix:
- Quote back THEIR language: 'Yeah, "[their phrase]" is the actual hard part.'
- Tie to specific people you've talked to: "Most agency owners I've worked with skip the system part"
- Cut the wisdom entirely and open with the proof story

---

### 8. QUOTABLE SENTENCE TELLS

AI writes sentences that belong on a LinkedIn carousel. Real proposals never land aphorisms — humans ramble toward a point and stop.

Test: would this sentence look good as a tweet, a quote graphic, or a slide bullet? If yes, it is too polished.

Flag examples:
- "The workflows that impress in demos rarely survive actual client data."
- "Either it eats your time, or everything ends up inconsistent. Usually both."
- "Done right, automation runs in the background. Done wrong, it runs you."

Fix: bury it inside a longer fragmented thought, or cut entirely.

---

### 9. FAKE-SPECIFIC PROOF

"Built a content automation pipeline last year" is the AI's *idea* of specific proof. It has none of the texture of real memory.

Real proof has at least one of:
- A proper noun (named client, named tool, named industry, named place)
- A specific number you remember because it pissed you off (3 ghost renders, 147 leads in one spike)
- A specific time marker ("after we went live", "last March", "third week in")
- A specific failure with named cause, not "we had issues"

Flag any proof that could have happened to anyone in any year on any project.

Fix: name something. "Built this for a yoga studio in Lagos earlier this year" beats "built a workflow for a client last year" every time.

---

### 10. COHERENCE OVER-BINDING

AI paragraphs cleanly develop one topic each. Para 1 = wisdom. Para 2 = proof. Para 3 = stack. Para 4 = response. Para 5 = CTA. This is presentation structure. A tired engineer typing after reading a job post does not produce this.

Flag: every sentence logically follows the previous one with no jumps, side notes, or tangents.

Fix: insert one coherence break per proposal. An off-topic opinion. A "btw". An aside. Examples:
- "Client's still using it btw."
- "Most people skip that. Not great."
- "Anyway."

One break minimum.

---

### 11. CORPORATE-SPEAK IN CASUAL WRAPPER

AI hides consultant language inside casual sentence structure. The wrapper sounds human; the phrase inside is pure consultant.

Flag every instance:
- "Error handling is built in from the start" — corporate
- "Designed for scale from day one" — corporate
- "Production-ready out of the gate" — corporate
- "End-to-end pipeline" — corporate
- "Best-in-class approach" — corporate

Fix: rewrite or cut. "I add retries before I ship" beats "error handling is built in from the start."

---

### 12. REGISTER DRIFT COUNT — need 2+ minimum

One casual aside is no longer enough. Real humans hop between registers within four sentences. Count register drift markers:

- "tbh", "honestly", "btw", "anyway", "weird", "whatever"
- "not great", "doesn't really matter", "either works"
- A sudden fragment after a longer sentence
- A sudden opinion or aside
- A casual contraction in a formal context

If fewer than 2 drifts present: flag and add more.

---

## How to run the roast

### Input

Paste the proposal text after the command, or reference a file:
```
/roast-proposal [paste text]
/roast-proposal outputs/proposals/YYYY-MM-DD-slug.md
```

---

### Output format

```
ROAST SCORE: [X]/10
(10 = no human would suspect AI. 1 = ChatGPT on its worst day.)

AI SLOP DETECTED
  "[exact quoted phrase]" — why it fails + human replacement
  ...

BIG GRAMMAR
  "[exact sentence]" — what makes it sound formal + rewrite
  ...

STRUCTURAL TELLS
  [describe the structural pattern that gave it away]

MISSING HUMAN TEXTURE
  [what is completely absent: casual aside? specific failure? rhythm variation?]

SPECIFICITY FAILURES
  "[vague claim]" — what specific detail would replace it

PARALLEL CONSTRUCTION COUNT
  [N triplets / lists found, threshold is 1]
  1. "[exact list]"
  2. "[exact list]"
  ...

UNIVERSAL PATTERN OPENERS
  "[exact AI wisdom sentence]" — why it reads as AI explaining the world

QUOTABLE SENTENCE TELLS
  "[exact sentence]" — why it reads like a tweet / quote graphic

FAKE-SPECIFIC PROOF
  "[exact phrase]" — what proper noun / number / date / named failure is missing

COHERENCE OVER-BINDING
  [Yes/No — does every sentence cleanly follow? If yes, where to insert the break]

CORPORATE-SPEAK IN CASUAL WRAPPER
  "[exact phrase]" — the consultant phrase hiding inside the casual sentence

REGISTER DRIFT COUNT
  [N drifts found, minimum is 2]
  Markers present: [list them]

FINAL VERDICT
  [2-3 sentences. Brutally honest. What is the biggest single problem?
   If sent as-is, what would a client scanning 20 proposals think?]

REWRITTEN VERSION
  [Full rewrite of the proposal applying every fix. No AI slop.
   No big grammar. Clear, simple, human. Sounds like a real person typed it.]
```

---

## Voice standard (what "human" means here)

Steal from how people actually talk:

**Not this:** "I specialize in delivering comprehensive social media strategies that drive engagement and brand awareness across multiple platforms."

**This:** "Mostly Instagram and LinkedIn, some TikTok. Canva for graphics, caption writing, scheduling. I automate the repetitive parts so the interesting parts actually get done."

**Not this:** "My experience with AI-assisted workflows enables me to optimize content production pipelines for maximum efficiency."

**This:** "I use AI for first drafts, research, and scheduling logic. Cuts the boring work down. More time on the stuff that actually needs a human."

**Not this:** "I would be delighted to discuss how my skills align with your requirements."

**This:** "What platforms are you starting with?"

---

## Hard rules for the rewrite

Same rules as write-proposal:
- No em dashes (use period, comma, or ...)
- No hyphens in compound words ("low confidence" not "low-confidence", "follow up" not "follow-up")
- First word cannot be "I"
- 150-250 words
- No banned phrases
- At least 2 register drifts (not 1)
- At least one specific operational detail with proper noun, number, or named failure
- Rhythm must vary: short sentences mixed with longer ones
- Max 1 parallel construction (triplets, 3+ item lists)
- Zero universal pattern openers
- Zero quotable / aphoristic sentences
- One coherence break minimum (an off-topic line that doesn't logically follow)
- Zero corporate-speak even when wrapped casually
- End abruptly or with a question. No clean wrap-up.

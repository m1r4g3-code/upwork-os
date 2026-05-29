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
- No hyphens in compound words
- First word cannot be "I"
- 150-250 words
- No banned phrases
- At least one casual aside
- At least one specific operational detail
- Rhythm must vary: short sentences mixed with longer ones
- End abruptly or with a question. No clean wrap-up.

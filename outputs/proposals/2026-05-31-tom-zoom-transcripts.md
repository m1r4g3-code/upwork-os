# Proposal — Automated System for Zoom Transcripts
**Date:** 2026-05-31
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/2026-05-31-022060770510.json
**Voice score:** 7/10
**Roast score:** 8/10

---
> SUBMIT AT: $25/hr  (profile default is $20 — change it before submitting)
---

## Proposal Text (Loom Wrapper)

```
Hey Tom,

I made you a quick Loom on this: [link]

P.S. Houston law firm — I'm guessing these are client meeting recordings?
That shapes exactly what fields we'd pull.
```

---

## Loom Script (Context Loom, 60-90 sec)

**Screen setup:** Upwork job post open, simple workflow diagram ready (Zoom → n8n → Claude → MySQL)

---

**[0:00 - 0:08]** Open on the job post
> "Tom, you want to automatically pull specific information from your Zoom transcripts or AI summaries. Here's exactly how I'd build this."

**[0:08 - 0:40]** Show workflow diagram: Zoom → n8n → OpenAI/Claude → MySQL

> "The flow works like this. Zoom finishes a meeting and generates a summary or transcript. n8n — think of it as Power Automate but built for AI pipelines — catches that automatically. It sends the text to Claude or OpenAI with a custom extraction prompt I build based on whatever fields you actually care about. Action items, client names, key dates, follow-up tasks, billing relevant details — whatever matters for your workflow. That structured data goes straight into your MySQL database."

> "I use n8n instead of Power Automate for this because it handles the AI step more cleanly and there are no per-run fees. Same end result: data in your database, no manual work."

**[0:40 - 1:00]** Show error handling note or n8n error branch

> "I also build in failure handling — if Zoom doesn't generate a summary, or the API call fails, the system logs it and alerts you. No silent failures where you don't know something was missed."

**[1:00 - 1:15]** Closing

> "The one thing I'd lock down with you first is the exact fields — what specifically are you pulling from each transcript? Once I know that, I can have a working prototype in a week or less. How many Zoom calls per week are we processing roughly?"

---

## Strategy Notes

**Archetype:** Solo professional / small firm owner. Overwhelmed by post-call admin. Real fear: building something that breaks or never quite matches what they need.

**Psychology:** "Mix of experience and value" = he knows what he wants, doesn't want to overpay, wants proof. He paid $80/hr when the work was genuinely technical. This is genuinely technical.

**Key moves:**
- Named the likely extraction fields (legal context) without asking "what do you want?" — shows domain understanding
- Addressed PHP/Power Automate proactively: reframed n8n as better, not a gap
- Error handling detail = operational realism signal (not a generic "I build robust systems")
- Closing question is answerable in 5 seconds

**What NOT to do in the Loom:**
- Don't say "I have experience with automation" — show the diagram
- Don't ask "can you tell me more about the project" — you already know enough to show the architecture

---

## Rate Rationale

**Recommended rate:** $25/hr
**Floor:** $22/hr (walk below this)
**Rationale:** Client avg rate paid is $50.83/hr on technical work. $25 positions us as experienced and affordable without racing to the bottom. Profile default is $20 — don't submit at $20, it signals junior.

# Proposal — Build a 5 Socials FullAutomation
**Date:** 2026-05-28
**Command:** /write-proposal
**Status:** draft (test run)
**Job:** https://www.upwork.com/jobs/~022056055168274538464
**Format:** Loom + 3-line text (context job, standard scope)

---

## Pass 1 — Intel

**What we know:**
- Client has 2 existing workflows but no central brain connecting them
- HeyGen workflow generates videos → outputs to Drive or nowhere structured
- Blotato workflow posts from its own input, not Sheets
- The missing piece: Google Sheets CMS as the single source of truth that orchestrates both
- Client's name is likely Eugen (from "Insert Avatar ID & Voice ID (from Eugen)")
- German client = precise, wants things that actually work, dislikes vague promises
- HeyGen question = explicit buying signal for expert advice

**Specific finding from brief:**
The client says "two workflows already exist" but the actual problem is they're disconnected silos. The Sheets CMS layer doesn't exist. Without it, someone still has to manually trigger each workflow — which defeats the entire point. The central build is the orchestration layer, not the individual channels.

---

## Pass 2 — Psychology

**Archetype:** Precision Builder. Has done the research (knows n8n, HeyGen, Blotato, Kling AI, Higgsfield, GPT-4). Wrote a detailed brief because he doesn't want to explain himself twice. Slightly frustrated that automation keeps requiring human babysitting.

**Real fear:** "I hire someone, pay $650, and three weeks later I'm still manually triggering things every morning."

**What he needs to believe:** This person already understands my system architecture without me explaining it, and they'll deliver something I genuinely don't have to touch.

**Motivators:**
- Time reclaimed (5 min/day is the stated dream)
- Content consistency (AI clone keeps personal brand active without his direct input)
- Scalability (YouTube "additionally" = more channels coming)

**Risk tolerance:** Low — new to Upwork, detailed brief = control orientation. He'll want to see competence fast, not reassurance.

---

## Pass 3 — Strategy

**The specific observation to open with:**
The HeyGen vs Kling question reveals they're still in decision mode. Most freelancers will ignore this or say "both work." Answering it directly and correctly (HeyGen = right call for their use case, here's why) signals expertise before anything else.

**Diagnosis frame:**
"You have two workflows that don't talk to each other. The Google Sheets layer that orchestrates everything doesn't exist yet — that's the actual build."

**Proof to use:**
n8n social media pipeline with Google Sheets trigger, multi-channel posting, status tracking.

**Closing question:**
"Have you defined the Google Sheets column schema yet, or do we start from scratch on the CMS structure?"

This is answerable in 5 seconds (yes/no + detail) and shows we're already thinking about implementation.

---

## Pass 4 — Draft Proposal (Written)

**Format: Loom + 3-line text wrapper**

```
Hey Eugen,

I recorded a quick walkthrough for you: [Loom link]

P.S. On HeyGen vs Kling vs Higgsfield — already covered in the video.
```

---

## Pass 5 — Voice Check

- First word is not "I" ✓
- Length: 3 lines ✓ (Loom carries the content)
- Specific to their situation ✓ (addresses HeyGen question directly)
- One personalised P.S. ✓
- No "I would be delighted" / "passionate about" / "leverage" ✓
- No wall of text ✓
- Opens conversation ✓

Voice score: 9/10

---

## Pass 6 — Loom Script (60-90 seconds)

**Setup:** Screen showing the Upwork job post open in one window

---

**[0:00–0:10] Open on their job post**
> "Hey Eugen — I saw your social media automation brief. Quick answer on HeyGen vs Kling AI vs Higgsfield, because that matters for how we build this."

**[0:10–0:30] Answer the HeyGen question directly**
> "HeyGen is the right call for your use case — talking-head avatar cloning with voice replication for reels. Kling AI generates cinematic motion video — it's not for avatar cloning, different product entirely. Higgsfield is the same category as Kling — generative video, not your digital twin.
> 
> If you want to explore alternatives to HeyGen specifically, Creatify.ai does avatar replication at $33/month versus HeyGen's $29-168 range — worth comparing. But HeyGen's quality on custom avatars is still the benchmark."

**[0:30–0:55] Name the real problem in their system**
> "Looking at your brief — you have two workflows, but they're running as separate silos right now. The HeyGen workflow generates videos, the Blotato posting workflow handles distribution. What's missing is the Google Sheets orchestration layer in the middle.
>
> One Google Sheet, one trigger: new row added → workflow fires → content generated → saved to Drive → status updated → published. That's what makes it genuinely 5-minutes-a-day. Right now without that layer, someone still has to manually kick each workflow off."

**[0:55–1:15] Proof + close**
> "I've built this exact pattern in n8n — Sheets as the CMS trigger, multi-channel posting with status tracking, carousel counter logic. It's what I do.
>
> One question before we talk scope: have you already defined your Google Sheets column schema, or do we start from scratch on the CMS structure? That answer changes the build order."

---

## Notes for Emmanuel

- **Budget:** $650 is below rate for this scope. Real price = $2,500-3,500. Proceed for test only. If client replies, counter-propose a Phase 1 scope for $650 (Sheets CMS + one channel working) + Phase 2 for the rest.
- **Contract-to-hire flag:** If this goes well, long-term retainer opportunity. Don't mention it in the proposal.
- **YouTube scope:** Don't include in $650 scope. Address separately if they ask.
- **Forced bid:** `forced_bid: true` — logged for learning data, outcome should be tracked regardless of result.

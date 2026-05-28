# Proposal Reply 4 — Phase 1A Scope Negotiation
**Date:** 2026-05-28
**Status:** draft
**Context:** Eugen acknowledged the architecture gap, proposed a leaner v1 (keep existing workflows, orchestration layer only, defer retry/approval, limit channels). Asking if there's a Phase 1A below $2,500.

---

## Analysis

Eugen's instinct is correct. The actual minimum viable version is:

**What already exists:**
- HeyGen workflow (generates avatar videos)
- Blotato posting workflow (has 4 channel nodes already: TikTok, LinkedIn, Facebook, Instagram)

**What's genuinely missing (the actual gap):**
- Google Sheets CMS as the central orchestration layer
- HeyGen reading from Sheets (currently reads from somewhere else)
- Blotato replaced by Sheets as input source — but keep the existing channel posting nodes

**One honest unknown:** We haven't seen the existing workflows. "Adapting" could be 2 hours or 10+ hours depending on how they're built.

**Phase 1A scope (honest):**
- Sheets schema (Content Queue + Settings)
- HeyGen workflow: swap input to Sheets
- Blotato channel nodes: swap input to Sheets
- Basic queue (ready → posting → done, no advanced retry)
- 4 channels (TikTok, LinkedIn, Facebook, Instagram — defer YouTube)

**What this defers:**
- Content generator (News API + GPT-4 + image gen) — manual Sheets input for v1
- Advanced retry / exponential backoff
- Telegram monitoring
- Carousel automation
- YouTube

**Estimated hours:** 20-28 hours (depending on existing workflow condition)
**Price: $1,200 – $1,500**

**Trade-off to name:** Without the content generator, Eugen manually writes topics into Sheets daily. That breaks the "5 minutes/day" goal temporarily. He needs to know this before agreeing to Phase 1A.

---

## Upwork Message Draft

Hey Eugen,

That framing is right — it's the smarter way to de-risk before committing fully.

Here's what Phase 1A actually looks like working with what you have:

**What we build:**
- Google Sheets CMS schema (Content Queue + Settings tab) — the orchestration layer
- HeyGen workflow adapted: swap input from current source to Sheets row trigger
- Blotato channel nodes kept, Blotato as input replaced with Sheets source
- Basic queue: ready → posting → done
- 4 channels to start (TikTok, LinkedIn, Facebook, Instagram) — YouTube deferred

**What we defer:**
- Content generator (News API → GPT-4 → image gen) — you manually write topics into Sheets for v1
- Advanced retry / exponential backoff
- Telegram monitoring
- Carousel automation

**One honest variable:**
I haven't seen your existing workflows. Adapting HeyGen and the Blotato nodes could be 2 hours or 10 hours depending on how they're currently structured. Before I give you a fixed number, I'd want to see them — export as JSON from n8n, or a quick Loom of the workflow canvas. That protects you from a disagreement mid-build.

**Phase 1A investment: $1,200 – $1,500**
Fixed number once I see the existing workflows.

Payment: 50% upfront, 50% on completion — simpler for a smaller engagement.

**One trade-off to name clearly:**
Without the content generator in Phase 1A, you're manually filling Sheets with topics daily. That's fine for proving the publishing layer works — but it's not 5 minutes/day yet. Phase 1B (content gen + retry logic + monitoring) would get you there, at roughly $800-$1,000 more. Natural add-on once v1 proves out.

If you want to move fast: share the existing workflows and I'll give you a fixed number today.

Emmanuel

---

## Notes for Emmanuel

- **Don't drop below $1,200.** Phase 1A is still 20-28 hours. Below $1,200 is below $50/hr on a complex project.
- **The "share your workflows" close is important.** Seeing the existing n8n workflows is a prerequisite for fixing the price. If they're messy, the adaptation work could be much higher than the simple case.
- **If he shares workflows and they're basically functional:** fixed at $1,200, fast build.
- **If he shares workflows and they're a mess:** price at $1,500, scope the adaptation work explicitly.
- **The content-generator omission must be named.** If he thinks Phase 1A = fully automated content, he'll be disappointed. Name the trade-off now.
- **Next step if he agrees:** `/prep-call` then kick off with workflow review.

# Proposal Reply — Build a 5 Socials FullAutomation
**Date:** 2026-05-28
**Command:** /write-proposal (follow-up reply)
**Status:** draft
**Context:** Eugen replied to the Loom proposal with 5 technical questions. Strong engagement signal — he watched the video, confirmed the Sheets orchestration insight, and is now evaluating technical depth before committing.

---

## Context — What Eugen Said

> "You're one of the few people so far who actually understood the architecture issue instead of just talking about AI automation."
> "The main thing I'm trying to avoid is building another fragile workflow stack."

5 questions asked:
1. Rate limits / failed publish retries — especially TikTok + Instagram
2. Queue logic — no duplicates, no collision when multiple rows trigger simultaneously
3. AI image gen — DALL-E vs Flux/Midjourney for consistent realism
4. Content approval vs full autonomy toggle
5. YouTube — Shorts only or long-form architecture too

---

## Reply Draft

Hey Eugen,

All five are solvable. Here's how I'd handle each:

**1. Rate limits + retries (TikTok + Instagram)**
Every post attempt logs a timestamp and attempt count back to the Sheet before firing. On rate limit errors, the workflow sets that row's status to `retry_scheduled` and uses n8n's Wait node with exponential backoff — 2 minutes, then 8, then 30. After 3 failures it flips to `failed_alert` and sends a Telegram notification. TikTok's daily limit gets tracked against a running counter in a Settings tab — the queue checks it before dispatching anything.

**2. Queue logic / collision prevention**
Each row has a status column: `ready → locked → posting → done/failed`. The first action any workflow takes when it picks up a row is set status to `locked`. Even if two workflow instances wake simultaneously, the second one sees `locked` and skips. No collisions. Sequential processing per channel. The Sheet is the single source of truth — nothing posts unless the Sheet says it's ready.

**3. DALL-E vs Flux**
For LinkedIn photorealism specifically: Flux Pro via Replicate API. DALL-E 3 is fine for abstract graphics and fast iteration, but for professional photo quality Flux consistently outperforms it. In n8n it's a one-node swap — same API call pattern, better output. Midjourney has no stable API so I'd leave it out entirely.

**4. Content approval toggle**
Settings tab in Google Sheets — one cell: `AUTO_POST = TRUE/FALSE`. When FALSE, the workflow generates content, writes it to the row, sets status to `pending_review`, and fires a Telegram notification with a direct link to that row. You review it in the Sheet and change status to `ready` when approved — the workflow picks it up on the next poll cycle. Can be set per channel (auto-post TikTok, review mode LinkedIn) without touching the workflow code.

**5. YouTube**
Shorts first, reusing the same HeyGen avatar reels you're already generating for TikTok. Same video file, different upload parameters, zero extra generation cost. I'll build the YouTube node so long-form can be added later without rebuilding the queue — different content type, same orchestration logic.

I can put together a scope document with build order and timeline this week. Or if a 20-minute call is faster, we can cover it there.

Emmanuel

---

## Notes

- **Signal quality:** Eugen is technically sharp. These questions test whether the freelancer can reason about system design, not just whether they've used the tools. Good answers here likely close the deal.
- **Red flags still active:** Budget $650 for this scope is still $16/hr implied. New Upwork account. If he engages seriously, the /quote command should be run before any SOW to calibrate the real price.
- **Next step:** If he replies positively, run `/quote eugen-5socials` and generate a SOW before any discovery call.

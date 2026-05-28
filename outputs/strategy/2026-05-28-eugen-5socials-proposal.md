# 5-Channel Social Media Automation
## Project Proposal — Phase 1A

**Prepared for:** Eugen  
**Prepared by:** Emmanuel Adekoya  
**Date:** 28 May 2026  
**Version:** 1.0

---

## The Situation

You have two n8n workflows that work in isolation:

- **HeyGen workflow** — generates avatar videos
- **Blotato posting workflow** — pushes content to TikTok, LinkedIn, Facebook, and Instagram

The problem is they don't talk to each other. There's no central orchestration layer. Every post still requires someone to manually trigger the right workflow at the right time — which defeats the entire point of automation.

The goal of Phase 1A is to wire these together through a single Google Sheets CMS so the system runs on its own without daily intervention.

---

## What We're Building

### The Orchestration Layer (Google Sheets CMS)

Google Sheets becomes the single source of truth. Every piece of content — topic, status, scheduled time, generated file reference — lives in one place. Workflows read from it. Workflows write back to it. Nothing posts unless Sheets says it's ready.

**Content Queue tab** — one row per piece of content:

| Field | Purpose |
|---|---|
| topic | what the post is about |
| content_type | reel, photo, or carousel |
| platform | TikTok, LinkedIn, Facebook, Instagram |
| status | ready → locked → posting → done / failed |
| scheduled_time | when to post |
| drive_file_id | generated media location in Google Drive |
| post_id | platform's returned confirmation ID |
| attempt_count | retry counter |
| error_log | last error message if failed |

**Settings tab** — controls without touching workflows:

| Setting | Default |
|---|---|
| AUTO_POST | TRUE |
| TIKTOK_DAILY_COUNT | rolling 24h counter |
| LINKEDIN_POST_COUNTER | 0 (carousel triggers at 6) |
| FB_IG_POST_COUNTER | 0 (carousel triggers at 3) |

---

### Workflow Adaptations

**HeyGen Workflow (update)**  
Currently: reads from a hardcoded source or manual input  
After: reads the next ready reel row from Sheets → generates video → saves to Google Drive → writes Drive file ID back to the row → sets status to `ready_to_post`

**Blotato Channel Nodes (update)**  
Currently: receives content from Blotato's own input  
After: reads from the Sheets Content Queue instead. The existing posting nodes for TikTok, LinkedIn, Facebook, and Instagram are kept — only the input source changes.

Queue collision is prevented by a lock pattern: the moment a workflow picks up a row, it sets status to `locked` before doing anything else. A second workflow instance checking simultaneously sees `locked` and skips — no duplicate posts.

---

### Channels in Phase 1A

| Channel | Content Type | Status |
|---|---|---|
| TikTok | Avatar reels | Included |
| LinkedIn | Photos + carousels | Included |
| Facebook | Reels + photos + carousels | Included |
| Instagram | Reels + photos + carousels | Included |
| YouTube | Shorts | Deferred to Phase 1B |

---

## Milestone Breakdown

### Week 1 — Sheets Schema + HeyGen

- Google Sheets CMS built out (Content Queue, Settings tabs)
- HeyGen workflow updated to read from Sheets
- Generated videos save to Google Drive
- Row status updates correctly after generation

**Checkpoint:** HeyGen generates an avatar video from a Sheets row without manual input

---

### Week 2 — Publisher Workflows Live

- Blotato channel nodes updated to read from Sheets queue
- Queue lock pattern implemented (no duplicate posts)
- Rate limit counters active (daily TikTok cap, LinkedIn + FB/IG carousel counters)
- All 4 channels posting successfully from queue (manual trigger to test)

**Checkpoint:** One complete content cycle runs — row enters queue, video generates, posts to all 4 channels, row updates to `done`

---

### Week 3 — Stability + Handoff

- End-to-end automated run (no manual trigger)
- Basic error logging (failed rows clearly marked in Sheets)
- Cross-platform testing across all content types (reel, photo, carousel)
- Handoff: documentation of Sheets schema, workflow logic, how to add new content rows

**Checkpoint:** System runs one full automated cycle with no manual input and posts correctly to all 4 channels

---

## What's Deferred

Phase 1A proves the publishing layer works. The following are deliberately excluded to keep the build lean:

| Feature | Reason for deferral |
|---|---|
| Content generator (News API + GPT-4 + image gen) | Phase 1A uses manual Sheets input — you write topics directly |
| Advanced retry (exponential backoff) | Basic failure logging only; manual fix on failed rows |
| Telegram monitoring | Deferred to Phase 1B |
| YouTube Shorts | Same architecture, added in Phase 1B |
| Carousel automation | Counter logic deferred; carousels added manually for v1 |
| Approval/review toggle | Phase 2 feature |

**Important trade-off to name:** Without the content generator, you are writing topics into Sheets manually for Phase 1A. That means the "5 minutes/day" goal is not fully achieved yet — you're at more like 15-20 minutes. Phase 1B eliminates that. The trade-off is intentional: prove the publishing layer first, then automate the input.

---

## Infrastructure Recommendation

**n8n hosting:** Start on n8n cloud ($20/month). Avoids Docker/SSL/backup overhead while the workflows are being proven. Migration to a self-hosted VPS (Hetzner CX21, €5/month) is a JSON export/import — 30 minutes — once Phase 1A is stable.

**Ongoing API costs at Phase 1A volume:**

| Service | Monthly estimate |
|---|---|
| HeyGen (60 videos/month) | $80–120 |
| DALL-E 3 (photos) | $7 |
| GPT-4 (content, Phase 1B) | $5 |
| n8n cloud | $20 |
| **Total** | **~$112–152/month** |

These are your operational costs — separate from the build fee.

---

## Investment

| Scope | Investment |
|---|---|
| Phase 1A (4 channels, orchestration layer, 3 weeks) | **$1,200 – $1,500** |
| Phase 1B add-on (content gen, retry, Telegram, YouTube) | $800 – $1,000 |
| Full Phase 1A + 1B | **$2,000 – $2,500** |

The range on Phase 1A depends on the condition of your existing workflows. Once I review them (JSON export from n8n or a quick Loom walkthrough), I'll give you a single fixed number — no range.

**Payment terms (Phase 1A):**  
50% upfront · 50% on completion (stable automated run across all 4 channels)

No milestone payments on a 3-week engagement — simpler for both sides.

---

## Next Step

Share your existing workflows — export as JSON from n8n, or record a 2-minute Loom of the workflow canvas. That's all I need to lock in the fixed price and confirm the start date.

If a 20-minute call is faster, I can work around your schedule this week.

---

*Prepared by Emmanuel Adekoya · Upwork · May 2026*

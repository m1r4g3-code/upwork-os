# Proposal Reply 3 — Architecture + Milestones
**Date:** 2026-05-28
**Status:** draft
**Context:** Eugen asked for architecture, milestone breakdown, timeline. Also asked 3 quick questions (monitoring, VPS vs cloud, Replicate scaling).

---

## Upwork Message Draft

Hey Eugen,

Quick answers first, then the full breakdown.

**Monitoring/logging**
Three layers — nothing fancy:
- n8n execution history (built-in, searchable by workflow + date)
- Logs tab in Google Sheets: every run appends a row — timestamp, platform, post_id, status, error. Fully auditable, no extra tooling.
- Telegram bot: daily summary ("7 posts sent, 0 failed") + immediate alert when something breaks.

That covers you long-term without overbuilding.

**VPS vs cloud**
Start on n8n cloud. VPS introduces Docker/SSL/backup overhead before the workflows are even proven stable — that's the wrong order. Cloud handles all of that. Once Phase 1 is running reliably for 2-3 weeks, migration is a JSON export/import (30 minutes). If you already have a VPS you want to use: Hetzner CX21 (€5/month) works fine for this volume.

**Replicate / Flux scaling**
At your volume (3 LinkedIn photos/day), Flux Pro costs ~$5/month via Replicate. Rate limits are a non-issue below 500 images/day. If you ever scale to that: switch to Black Forest Labs API directly for batch pricing. Not relevant for Phase 1.

---

**Phase 1 — Reliable Core**
Goal: runs daily, posts reliably, alerts you when something breaks. No approval flows, no analytics, no overengineering.

*What gets built:*
- Google Sheets CMS (3 tabs: Content Queue, Settings, Logs)
- HeyGen workflow updated to read from Sheets, save to Drive, update status
- Content generator: News API → GPT-4 topics → Flux Pro (LinkedIn photos) + DALL-E (Facebook/Instagram graphics)
- Publisher workflows for all 5 channels — queue logic, rate limit counters, retry on failure
- Error handling: exponential backoff (2min → 8min → 30min), Telegram alerts after 3 failures
- Carousel counter (every 3 posts Facebook/Instagram, every 6 posts LinkedIn)
- Daily monitoring summary to Telegram

*Timeline: 3 weeks*

| Week | Milestone |
|---|---|
| 1 | Sheets schema live, HeyGen reads from Sheets, video saves to Drive |
| 2 | Content generator running, all 5 channels posting from queue (manual trigger) |
| 3 | Full automation, error handling, cross-platform testing, handoff |

*Out of scope for Phase 1:* approval toggle, analytics, long-form YouTube, multi-avatar.

---

**Phase 2 — Control Layer**
Only after Phase 1 has run stably for 2+ weeks:
- Approval/review toggle (per-channel, Sheets-controlled, Telegram notification to approve)
- Content performance analytics (platform API read-back)
- Long-form YouTube (separate architecture conversation)
- Multi-avatar support

---

**On investment:**
Phase 1 is 40-55 hours of build time. I want to be straight with you on that before we go further — the posted budget covers roughly the first week. Full Phase 1 would be $2,500. Phase 1 + Phase 2 complete would be $4,000.

Standard schedule: 40% upfront, 30% at midpoint (all channels posting), 30% on handoff after a stable 7-day run.

Worth having a direct conversation about this — happy to jump on a 20-minute call this week if that's easier.

Emmanuel

---

## Notes for Emmanuel

- **The budget gap is named directly.** $650 vs $2,500 is too wide to paper over. Better to surface it now than after he reads a detailed SOW expecting the $650 number.
- **The close is a call invite.** If he says yes to the budget, move straight to `/prep-call`.
- **If he pushes back on price:** don't drop below $2,000 for Phase 1. That's already lean. Below that means you're working at a loss on a high-complexity project.
- **If he counters with $1,000-1,500:** offer Phase 1 minus YouTube and carousel automation. Core 4-channel posting only. That's a negotiable scope cut, not a rate cut.
- Full architecture doc: `outputs/strategy/2026-05-28-eugen-5socials-architecture.md`

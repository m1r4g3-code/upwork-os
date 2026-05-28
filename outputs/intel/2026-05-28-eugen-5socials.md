# Job Intel — Build a 5 Socials FullAutomation
**Date:** 2026-05-28
**Command:** /job-qualify
**Status:** forced_bid (test — below threshold, proceeding for OS test run)
**Source:** https://www.upwork.com/jobs/~022056055168274538464

---

## Score Card

| Dimension | Score | Reason |
|---|---|---|
| Job quality | 42/100 | Detailed scope but $650 for expert-level 5-channel AI automation = severe budget mismatch |
| Client quality | 15/100 | 12-day-old Upwork account, $200 total spend, 0 reviews, payment unverified |
| Fit score | 82/100 | n8n + Google Sheets + HeyGen + social automation = exact niche |
| Urgency | 5/10 | Posted last week, 5-10 proposals already |
| Competition | 5/10 | Low-moderate — 5-10 proposals, 1 unanswered invite |
| **Composite** | **42/100** | **Below 65 threshold** |

**Decision: SKIP** (overridden to BID for OS test — `forced_bid: true`)

---

## Red Flags
- Budget $650 for "Expert + Complex": implied $16/hr at 40hrs minimum. Real scope is 60-80hrs → $3,000-5,000 at any professional rate
- Account 12 days old: zero Upwork track record, no reviews, higher dispute/ghosting risk
- Payment verification: not confirmed in post
- "Contract-to-hire opportunity" on a new account = unclear intent
- 1 unanswered invite out of 1 sent — other freelancers already passed on it
- YouTube added as "additionally" = scope creep signal from day one

## Green Flags
- Stack is exact: n8n, Google Sheets, HeyGen, DALL-E 3 — no ramp-up time
- 2 workflows already exist (HeyGen avatar gen + Blotato posting nodes) — not starting from zero
- Brief is detailed and precise — client has thought this through
- German client: precise, direct, results-focused
- Contract-to-hire could mean long-term relationship if it goes well

---

## Job Description (Full)

**Client:** Eugen (Germany, Rinteln) — `DEU`
**Budget:** $650 fixed-price
**Level:** Expert | Complex project | Remote | Contract-to-hire eligible

Build a fully automated social media machine for:
- **TikTok**: Reels using AI clone avatar (HeyGen) with subtitles
- **LinkedIn**: AI-generated photos + captions/hooks. 3x daily photo posts. Carousel after every 6 posts (1x weekly)
- **Facebook + Instagram**: Reels (AI clone) + AI photos. Carousel after every 3 posts (carousels built by separate custom GPT)
- **YouTube**: Added as "additionally" — scope TBD

**Tools specified:**
- n8n (self-hosted) — automation engine
- HeyGen (?) — avatar video creation (client asking if Kling AI / Higgsfield better)
- Google Sheets — content management / trigger system
- Google Drive — output storage
- GPT-4 / DALL-E 3 — hooks, captions, images

**Current status (existing work):**
1. HeyGen Avatar Workflow — generates avatar videos
2. Blotato Posting Workflow — 4 channel nodes (TikTok, LinkedIn, Facebook, Instagram)

**Tasks to build:**
- Adjust HeyGen workflow: Insert Avatar ID + Voice ID (from Eugen), read from Sheets, save to Drive, update status
- Modify Blotato workflow: Remove Blotato upload step, keep 5 channel nodes, use Sheets as input
- New: Carousel Counter (weekly trigger), Google Sheets Monitor (auto-trigger), Error Handling
- Setup: Sheets column schema, API credentials in n8n

**Target output:**
> "News API → generate topics → convert to videos/images/texts → publish daily. My role: 5 min/day max."

---

## Client Profile

| Field | Value |
|---|---|
| Name | Eugen (mentioned in avatar ID task) |
| Country | Germany — Rinteln, Lower Saxony |
| Upwork since | May 16, 2026 (12 days ago) |
| Total spent | $200 |
| Hires | 1 active |
| Reviews | 0 |
| Payment verified | Not confirmed |

---

## Positioning Angle

Lead with the HeyGen question — everyone else will ignore it or say "all work fine." Give a direct answer: HeyGen is correct for talking-head avatar cloning; Kling is generative motion video (wrong use case); Higgsfield is cinematic generation (wrong use case). If budget is a concern, Creatify.ai is $33/month and does avatar replication.

Then name the missing piece: the Google Sheets orchestration layer is the actual system — not the individual channel workflows. Two workflows exist but they don't talk to each other. The CMS schema + trigger logic + status tracking is what makes it truly hands-off.

---

## Connects: 6 (standard bid)
## Bid amount: $650 (matching posted — test only; real bid would be $2,500+)

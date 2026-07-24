# Proposal — AI Automation & Growth Systems Engineer
**Date:** 2026-05-31
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/2026-05-31-022061184978.json
**Voice score:** 8/10
**Roast score:** 8/10

---
> SUBMIT AT: $35/hr  (profile default is $20 — change it before submitting)
---

## Proposal Text (Text Only)

For the Slack analyst: n8n triggers at 6am, pulls Meta Ads data at campaign and ad set level, structures the response, passes it to Claude with a prompt that knows your KPIs and fatigue thresholds. Claude outputs a ranked action list. n8n posts it to Slack before the team's day starts. The interesting part is the prompt layer. Getting Claude to reason reliably about ad data without inventing numbers requires careful schema design. That usually takes a day of iteration, not an hour.

Stack I'd use: n8n for orchestration and scheduling, Python for any preprocessing that needs heavier logic, Claude or GPT-4o for the analysis step. n8n handles retry and scheduling logic without custom code, which saves a few days of plumbing.

On the API side: Claude and OpenAI in production agent workflows. For Meta's Ads API specifically, I'd be starting fresh. The hard part is auth and pagination setup. The endpoints are straightforward once that's sorted.

Built something structurally similar recently. n8n plus OpenAI plus CRM, scoring 147 leads a day automatically. Client's still running it. Took about a week to make the classification prompt reliable enough to trust.

How many client ad accounts are you running daily diagnostics across?

---

## Screening Question Answer

**"Describe your recent experience with similar projects"**

Built an automated lead scoring and routing pipeline using n8n and OpenAI. 147 leads per day processed automatically, structured output routed to CRM with zero manual input. Still running unattended. Also built a Zoom transcript extraction workflow in n8n — Claude pulls structured fields from meeting summaries, routes output to a database automatically. Stack: n8n for orchestration, Python for heavier logic, Claude or GPT-4o for the analysis layer.

---

## Strategy Notes

**Archetype:** Technical Operator who's been burned by generalists. The "NOT a generic AI agency team" language is a direct signal — they've already tried these people.

**Real fear:** Hiring someone who demos well but can't ship a reliable system. The screening question is a filter for this.

**What they need to believe:** Emmanuel understands systems architecture and knows where the hard parts actually are. Not just which tools to use, but why they work and what breaks.

**Key moves:**
- Opened with the Slack analyst answer directly — no buildup. This is what they asked for.
- Named the real difficulty (schema design for the prompt layer, not the API integration)
- Honest admission on Meta Ads API gap, immediately followed by showing domain knowledge (auth/pagination is the hard part)
- Proof point has a number (147/day), a time marker (one week), and a specific named challenge (classification prompt reliability)
- Closing question is scoping intelligence — knowing how many accounts shapes the architecture
- "Client's still running it" — coherence break, present tense, signals durability

**What to avoid on the call:**
- Don't commit to the 6-month retainer framing — position as starting with the Slack analyst project
- Don't overpromise on Meta Ads API depth. You can learn it fast, but don't pretend you've shipped it.

---

## Rate Rationale

**Recommended rate:** $35/hr
**Floor:** $30/hr (walk below this)
**Rationale:** Client avg is $31.54/hr but has paid $47-$115/hr for strong technical specialists. $35 positions above their average without hitting the ceiling. Profile default of $20 signals junior — do not submit at $20.

---

## Timing

Job was 28 minutes old at evaluation. Submit now. First-mover window is open.

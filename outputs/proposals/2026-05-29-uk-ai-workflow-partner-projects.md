# Proposal — AI Workflow Automation / Claude Code / n8n Specialist (UK Partner Projects)
**Date:** 2026-05-29
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/2026-05-29-022060403729.json
**Voice score:** 8.5/10
**Roast score:** 8.5/10

---
> SUBMIT AT: $28/hr  (profile default is $20/hr — change it before submitting)
---

## Proposal Text

Building an automation practice inside an existing business is harder than it looks from the outside. The workflows that impress in demos rarely survive actual client data.

Built a content automation pipeline last year. Google Trends pulled topics, AI generated scripts, HeyGen rendered the videos, everything published to Facebook and Instagram on schedule. The part that took the most work, honestly, was handling failed renders. HeyGen would timeout on longer scripts with no error returned, just silence. Added monitoring and retry logic after the third ghost render, plus a fallback notification so the client could step in manually when needed. Runs clean now.

That's roughly how I work across the stack: n8n for orchestration, Claude API for anything needing judgment or text processing, Airtable or HubSpot depending on what the client already uses. Error handling is built in from the start. Every workflow gets retry logic, failure alerts, and logging so you can see exactly what ran and when.

For the edge cases you mentioned specifically: deduplication nodes before any write, exponential backoff on API failures, AI outputs below a confidence threshold route to human review before any action fires.

Portfolio and Loom walkthroughs ready. What type of workflow would you want to start the trial on, document collection and onboarding, or lead follow up?

---

## Loom Script (portfolio format — no website to audit)

```
[0:00-0:08] Screen open on n8n workflow canvas or portfolio item
            "You're building an automation service for other businesses.
             Let me show you the kind of system I build."

[0:08-0:40] Show the content automation pipeline
            "This one pulls topics from Google Trends, AI writes the script,
             HeyGen renders the video, posts to Facebook and Instagram.
             The problem we hit was HeyGen timing out silently on longer scripts.
             Added retry logic and a human fallback notification.
             Runs without anyone touching it now."

[0:40-1:10] Show CRM or lead pipeline portfolio item
            "This is a lead pipeline: capture, score, route to rep,
             follow up sequences trigger automatically based on status.
             n8n, Airtable, webhook triggers."

[1:10-1:30] Error handling callout
            "Everything I build has retry logic, failure alerts,
             and logging so you can see exactly what ran. AI outputs
             that are uncertain route to a human queue before anything fires."

[1:30-1:45] Close
            "What type of workflow would you want to start the trial on,
             document collection, or lead follow up?"
```

---

## Upwork Screening Questions (answer these in the form fields)

**Q1: Describe one real AI automation project you built.**
"Built a content automation pipeline: Google Trends pulled topics, AI generated scripts, HeyGen rendered videos, everything auto-published to Facebook and Instagram. The tricky part was HeyGen timing out silently on longer scripts. Added monitoring, retry logic, and a human fallback notification after the third silent failure. Runs without intervention now."

**Q2: Which tools are you strongest in?**
"n8n (primary orchestration), Claude API and OpenAI API (AI processing and agents), Airtable, HubSpot, GoHighLevel (CRM), Google Workspace integrations, REST APIs and webhooks, Zapier and Make for simpler flows. I use n8n for anything complex — better error handling and more control than Zapier."

**Q3: Have you built document collection, onboarding, CRM, dashboards, email classification, support or lead follow-up workflows?**
"Yes: CRM automation with HubSpot and Airtable (lead capture, routing, follow-up sequences), social media autopublishing pipelines, AI agent workflows with OpenAI and Claude APIs. Happy to walk through specifics on a call."

**Q4: How do you handle errors, failed runs, duplicates, API issues, human review?**
"Deduplication nodes before every write. Exponential backoff on API failures with a max retry limit. AI outputs below a confidence threshold route to a human review queue before any action fires. All workflows have logging so you can see exactly what ran, when, and what failed. Error notifications go to the client so nothing fails silently."

**Q5: Can you share screenshots, Loom videos, diagrams or examples?**
"Yes — portfolio on the profile and Loom walkthroughs available. Happy to record a specific walkthrough relevant to your first trial workflow if that helps."

---

## Strategy Notes

**Archetype:** Builder who's been burned — 116 jobs, 2016 member, 67 reviews. Knows what a bad freelancer looks like. Wants a partner, not a vendor.

**Real fear:** Hiring someone who builds working demos that break in production — silent API failures, duplicate records, AI making wrong calls with no human in the loop.

**What they need to believe:** This person has shipped systems that run in the real world, handles edge cases by design (not as an afterthought), and can be trusted to represent them to their own clients.

**Proof used:** Content automation pipeline with the HeyGen silent failure. Shows: production experience, real problem encountered, specific fix applied, outcome confirmed.

**Positioning angle:** Lead with the reality of building inside an existing business. Then prove it with a specific failure story. Close with a scoping question that signals you've read the job and know their domain.

**6+ month timeline note:** Do not commit to 6 months on this account. Position for trial + initial project. Let it grow naturally.

---

## Rate Rationale
**Recommended rate:** $28/hr
**Floor:** $22/hr (below this, walk — the client has $23K spend and can pay more)
**Rationale:** Their avg paid is $16.99 but the GDPR consultant got $120/hr. Bid $28 to signal you're above commodity rate without shocking them. Change from profile default of $20 before submitting.

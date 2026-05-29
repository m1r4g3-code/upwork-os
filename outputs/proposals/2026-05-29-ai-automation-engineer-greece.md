# Proposal — AI Automation Engineer (n8n, Make, AI Agents)
**Date:** 2026-05-29
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/2026-05-29-022060326127.json
**Voice score:** 8/10 (voice authenticity: 10/10)
---

## Proposal Text

*(Paste this into the Upwork text box)*

---

"design and build, not just connect tools." That line is doing a lot of work in this post. Most people who apply to automation roles can wire up a Zap. Some can handle n8n. Far fewer know what to do when a third party API starts silently dropping jobs at volume, or when two workflows race each other and corrupt state.

Built a content pipeline recently for a media client. Topic in, AI generated video scripts to HeyGen for avatar rendering, automated publishing across 5 platforms. n8n for orchestration, Make for the media routing (honestly cleaner there for those API types).

The part that actually took work was queue management. Without it overlapping render jobs would fail silently. No error, just nothing published. Added retries because the HeyGen API drops jobs randomly some days for no obvious reason.

The whole thing runs without anyone touching it now. That is what your clients need from you: systems that do not require babysitting.

Here is a Loom walking through it: [paste Loom link here]

Available 20+ hrs/week. What is the first project on your roadmap, already scoped with a client, or still building the foundational stack?

---

## Loom Script (2:00–2:30)

*Record with the n8n canvas or the most impressive workflow visible on screen.*

---

**[0:00-0:10] Open on n8n canvas (or Make scenario)**
"This is a content automation system I built for a media client. A topic comes in, and the system outputs AI generated videos scheduled across 5 social platforms with no manual steps in between. Let me walk you through how it works."

**[0:10-0:45] Show the n8n workflow**
"The entry is a webhook trigger. From there n8n handles orchestration, routes to Claude for video script generation, then hits the HeyGen API for avatar rendering. You can see this queue lock node here. This prevents overlapping jobs when multiple pieces are generating at the same time. That is the kind of edge case that kills most automation systems at volume."

**[0:45-1:15] Show error handling and the Make handoff**
"There is a parallel branch for static image posts. Separate generation flow, same queue management. If the video branch fails, the image branch keeps going. Errors route to a Slack notification and queue a retry automatically. The final stage hands off to Make for platform publishing across Instagram, TikTok, YouTube, LinkedIn, Facebook, because those API integrations are cleaner to manage there."

**[1:15-1:45] Zoom out on the full canvas**
"The whole thing runs unattended. The client does not touch it. Documentation covers every node, every decision point, every failure mode. That is what building for an agency means. The system has to work for whoever picks it up next, not just the person who built it."

**[1:45-2:10] Close**
"If this is the kind of architecture you are building for your clients, I would like to be that engineer. Happy to jump on a 15 minute call to understand what is on your roadmap first. What is the first project, already scoped, or still building the foundational stack?"

---

## Rate
Post at **$50/hr**. Above their range ($25–$47), but they stated "willing to pay higher rates for the most experienced." If they push back: hold at $45. Below $40 = wrong fit, walk.

---

## Strategy Notes

**Archetype:** Builder/Operator — running an agency, needs a reliable technical co executor  
**Real fear:** Hiring someone who handles basic workflows but fails on complex client work, making the agency look bad in front of paying clients  
**Secondary fear:** Engineer disappears when something breaks mid project  
**What they need to believe:** Emmanuel owns technical quality end to end and operates independently

**Positioning angle used:** Quoted their own post back to them ("design and build, not just connect tools") — signals close reading, differentiates from generic applicants

**Key unknown answered by closing question:** Whether they have active client projects or are pre-revenue. Determines if hours will actually materialize.

**Note on client:** Their prior $181 spend is all non-technical contracts. First developer hire. Manage expectations on project scope per engagement — don't agree to open ended "troubleshoot whatever comes up" language. Each project should have a defined scope before work starts.

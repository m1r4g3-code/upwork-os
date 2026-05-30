# Proposal — Build a 5 Socials Full Automation (Eugen, v2)
**Date:** 2026-05-30
**Command:** /write-proposal
**Status:** draft
**Job file:** sources/jobs/2026-05-30-022056055168.json
**Voice score:** 9/10
**Roast score:** 9/10

---
> SUBMIT AT: $650 (match his posted budget — scope the phasing in the Loom)
---

## Proposal Text

*(This is the ENTIRE written proposal — Loom carries the weight)*

---

Hey Eugen,

Put together a quick Loom for you: [link]

P.S. HeyGen is the right call. And the two workflows aren't the problem — it's the layer between them that doesn't exist yet.

---

## Why This Text Works

The P.S. does three things in one line:
1. Answers his explicit question (HeyGen vs Kling vs Higgsfield)
2. Names his real problem (missing orchestration layer, not the individual workflows)
3. Creates a reason to click the Loom — he needs to hear the explanation

Most freelancers will open with skill lists. This opens with a diagnosis.
The only thing he can do after reading this P.S. is click the video.

---

## Loom Script (75-90 seconds, portfolio + audit format)

**Setup:** Screen open on his job post. Scroll slowly as you talk so he sees you read every line.

---

**[0:00-0:12] Open on the job post, start talking immediately**

"Hey Eugen. Quick answer on HeyGen vs Kling vs Higgsfield first, because I know that's blocking the build decision.

HeyGen is right for what you're doing. Kling AI and Higgsfield are generative video tools — cinematic motion, not avatar cloning. Different category entirely. If you want an alternative to HeyGen specifically, Creatify does custom avatar replication at a lower price point, but HeyGen's quality on digital twins is still the benchmark. Stick with HeyGen."

---

**[0:12-0:40] Name the real architecture problem**

"Now, looking at your brief — you said two workflows already exist. That's true. But the actual gap isn't the workflows. It's that they're not connected to anything.

Right now the HeyGen workflow generates videos and probably drops them somewhere in Drive. The Blotato workflow posts from its own input, not from a central source. So someone still has to manually kick each one off.

The build isn't adjusting two workflows. The build is the Google Sheets layer in the middle that doesn't exist. One sheet, one trigger — new row added, everything fires automatically. Videos generated, saved to Drive, status updated, posted to all five channels. That's what gets you to five minutes a day. Without that layer, you're still babysitting it."

---

**[0:40-1:05] Show the solution + proof**

"I've built this exact pattern. n8n reading from Google Sheets as the trigger, branching into content generation, HeyGen for video, parallel posting to multiple channels, status column updating back on completion. The carousel counter logic runs on a separate schedule workflow — checks the post count, fires the carousel when threshold hits.

The schema for your Sheets is probably eight to ten columns. Content queue, channel targets, post type, status, HeyGen job ID, Drive output URL, scheduled time, error log. I can define that before we start so there's no ambiguity mid-build."

---

**[1:05-1:20] Scope the YouTube note + Phase split**

"YouTube you mentioned additionally — I'd keep that in Phase 2. The core five channels in Phase 1, YouTube after the posting logic is stable. Easier to debug one thing at a time.

On budget: your $650 covers Phase 1 core. Happy to talk Phase 2 scope once Phase 1 is running."

---

**[1:20-1:30] Close with the schema question**

"One thing before we talk specifics: have you defined the Google Sheets column structure yet, or are we starting from scratch on that? That answer changes where we begin.

Reply here or drop a message — happy to look at the existing workflows before we lock scope."

---

## Deep Audit Check

**Parallel constructions:** 1 (the eight to ten column list — acceptable, it's a technical spec)
**Universal pattern openers:** 0 (opens with a direct answer to his question)
**Quotable sentences:** 0
**Register drifts:** "Stick with HeyGen." (decisive, casual drop) / "That's true. But..." (abrupt pivot) / "Easier to debug one thing at a time." (conversational) = 3 drifts
**Specific proof:** n8n + Google Sheets trigger + HeyGen job ID + Drive output URL + status column + carousel counter (named operational details, not generic)
**Coherence break:** Jump from architecture problem to showing solution skips the "here's what I'd propose" transition — goes straight to proof
**Double dash:** 0
**Em dashes:** 0
**Corporate-speak:** 0 (no "robust", "end-to-end", "built in from the start")

---

## Strategy Notes

**Archetype:** Precision Builder. Wrote a 400-word technical brief. Knows the stack. Doesn't want to explain himself twice. German = expects directness, hates vague promises.

**Real fear:** "I pay $650 and three weeks later I'm still manually triggering things every morning."

**Why this proposal wins:**
- Only proposal that answers his HeyGen question directly and correctly
- Names the real problem (missing Sheets layer) before he has to explain it
- Shows schema-level thinking (8-10 columns named specifically) — signals implementation experience, not just concept knowledge
- P.S. forces the click — impossible to read it and not want to see the Loom

**On Talha K. already working:** Do not mention. Let the proposal quality make the comparison implicit. If Eugen is reposting while Talha is active, he's unhappy with the delivery. Our proposal should just be the best one he's seen.

**Phase split:**
- Phase 1 ($650): Sheets CMS schema + HeyGen workflow adjusted + Blotato nodes adjusted + queue logic (4 channels: TikTok, LinkedIn, Facebook, Instagram)
- Phase 2 ($800-1,000): Content generator (News API + GPT-4 + image gen) + retry logic + monitoring + YouTube

**If he replies and asks to lock scope:** Run /prep-call. Ask for the existing workflow JSONs from n8n before setting a fixed number. Seeing how they're built changes the adaptation estimate significantly.

---

## Rate Rationale
**Bid:** $650 (match his posted budget)
**Floor:** $1,200 for full Phase 1 scope (20-28hrs work)
**Strategy:** Bid $650 to get the conversation. Loom explains Phase 1 covers core only. Once he replies, phase the scope honestly. Do not drop below $1,200 on Phase 1 or $50/hr equivalent.

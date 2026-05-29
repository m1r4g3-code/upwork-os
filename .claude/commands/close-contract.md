# /close-contract — Delivery Brief + Contract Close

## Role

Work is done. You engineer the close to get a 9-10 private NPS score, not just a 5-star public review. Upwork sends clients a private satisfaction survey you never see. A 7 is a "Passive" — it suppresses your ranking even if their public review is glowing. Your job is to engineer 9-10s.

---

## Pre-Flight Checklist

Before generating anything, confirm:

1. Is the work genuinely complete and tested?
2. Is there an unexpected extra Emmanuel can include (something small, not requested, valuable)?
3. Is the client's temperature warm? (If they've gone quiet for 3+ days — do a check-in call before the delivery, not after)
4. Will anything break in the next 7 days?

If any answer is no — do not generate the close yet. Fix the underlying issue first.

---

## Pipeline

### Step 1 — Gather context

```
CLIENT: [first name]
PROJECT: [project name]
SLUG: [short identifier, e.g. crm-alex]
```

Also read:
- Client node at `hephzibah-brain-temp/upwork/clients/active/` if it exists
- Original job card at `hephzibah-brain-temp/upwork/jobs/archive/` for scope reference

---

### Step 2 — Run the generator

```
python scripts/handoff.py --project "[project name]" --client "[client name]" --slug [slug]
```

This opens an interactive session. It collects:
- Stack used
- What was delivered (list of deliverables)
- How to use it (step-by-step instructions)
- The unexpected extra
- Maintenance notes

Provide the information from context when running interactively.

---

### Step 3 — Review and augment the output

The generator produces:
1. **Delivery brief** — what was built, how to use it, unexpected extra, maintenance
2. **Contract close message** — ready to paste into Upwork chat
3. **Silent follow-up scripts** — if client goes quiet at days 5 and 10

Read all of it. Augment the delivery brief with any project-specific details the generator couldn't know.

---

### Step 4 — Save and log

Save to `outputs/briefs/YYYY-MM-DD-handoff-[slug].md`

Update the client node in `hephzibah-brain-temp/upwork/clients/active/`:
```
python scripts/vault.py append [client-slug] "Contract Closed" "Date: YYYY-MM-DD. Outcome: [notes]."
```

Commit:
```
python scripts/vault.py commit "upwork: log close — [slug] delivered"
```

---

## The JSS Rule

**Never close the contract yourself.** Freelancer-initiated endings register as JSS negatives regardless of the reason.

Always let the client close. When work is done and client goes silent:

> "Everything is wrapped up on my end. Could you close the contract when you get a chance?"

If they still don't close after 10 days — follow-up once more, then let it sit. Do not initiate the close.

---

## Engineering the 9-10

Upwork's private survey goes out at contract close. Client sentiment at that exact moment determines the score.

**What moves the score from 7 to 9:**
- A small unexpected extra delivered with the handoff (not asked for, clearly valuable)
- A delivery summary that proves you understood the business, not just the task
- Clean, simple documentation they can actually use without calling you
- The close message landing warm, not transactional

**Delivery summary framing:**
Not "here's what I built" — "here's what changed for your business and how to keep it running."

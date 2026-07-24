# Build Spec — Revamp Consulting Social Media Automation
**Date:** 2026-07-18
**Project:** Automated Social Media Content System — Phase 1
**Client:** Revamp Consulting LLC (via Bayonet)
**Prepared by:** Emmanuel Adekoya

---

## What This Builds

One n8n workflow. Every morning at 9AM it generates a strategy post using Groq (free), sends it to Telegram for approval, waits for the approver to respond, then publishes to LinkedIn and Instagram via Upload-Post. No databases, no second workflow, no paid AI.

---

## How It Works — End to End

```
9AM Cron Trigger
      |
      v
Code Node — pick today's topic, build Groq prompt
      |
      v
HTTP Request — Groq API (free, Llama 3.3 70B)
      |
      v
Telegram sendAndWait — sends post + 3 buttons
  [Approve] [Edit] [Regenerate]
      |
      v
Switch — what did the approver choose?
      |
   Approve ————————————————————————> HTTP Request (Upload-Post) → Done
      |
   Edit ——> Telegram sendAndWait (freeText, "send edited version")
              |
              v
            HTTP Request (Upload-Post) → Done
      |
   Regenerate ——> back to Groq → back to Telegram sendAndWait
```

The `sendAndWait` node is native n8n — it pauses the execution, holds it open until the approver responds, then resumes automatically. No webhook setup, no polling, no second workflow.

---

## Stack

| Layer | Tool | Cost |
|---|---|---|
| Workflow engine | n8n (already on SERAMAN instance or Bayonet's VPS) | $0 or VPS only |
| AI content | Groq API — Llama 3.3 70B | Free tier, 14,400 req/day |
| Approval flow | Telegram Bot (sendAndWait) | Free |
| Publishing | Upload-Post API | Client's existing subscription |

No Google Sheets. No extra database. No Docker setup needed if using SERAMAN's n8n already.

---

## Credentials Needed (Before Starting)

| What | Where to get it |
|---|---|
| Groq API key | console.groq.com — free account |
| Telegram bot token | BotFather on Telegram (@BotFather → /newbot) |
| Telegram chat ID of approver | Message the bot, then call `api.telegram.org/bot{TOKEN}/getUpdates` |
| Upload-Post API key | Bayonet's existing Upload-Post account |

In n8n → Settings → Credentials, add:
- **Groq**: HTTP Header Auth — Name: `Authorization`, Value: `Bearer YOUR_KEY`
- **Telegram Bot**: Telegram API — paste bot token
- **Upload-Post**: HTTP Header Auth — Name: `Authorization`, Value: `Bearer YOUR_KEY`

---

## The Content System

The Code node contains a `topics` array. Each topic has a name and 3-5 talking points that the client actually wants used. The AI generates within those talking points only — it cannot drift or go generic.

**Emmanuel fills in the talking points** with Bayonet before the first live run. The developer wires it into the prompt — the client fills in the words.

Template (goes inside the Code node's `jsCode`):

```javascript
const topics = [
  {
    name: "Business Case Studies",
    points: [
      // FILL IN: a real case study or business lesson Revamp references
      // FILL IN: an industry example their clients relate to
      // FILL IN: the strategic lesson from it
    ]
  },
  {
    name: "What Strategy Actually Is",
    points: [
      // FILL IN: a misconception clients bring to Revamp
      // FILL IN: how Revamp defines strategy differently
      // FILL IN: strategy vs tactics confusion they see often
    ]
  },
  {
    name: "Strategy Development Process",
    points: [
      // FILL IN: a step in Revamp's advisory process
      // FILL IN: what most businesses skip
      // FILL IN: a specific tool or framework Revamp uses
    ]
  },
  {
    name: "Business Nuggets",
    points: [
      // FILL IN: team performance observation
      // FILL IN: finance or org design insight
      // FILL IN: culture or people management point
    ]
  },
  {
    name: "Disruption and Innovation",
    points: [
      // FILL IN: disruption pattern in their clients' industries
      // FILL IN: how successful businesses handled it
      // FILL IN: what most businesses get wrong
    ]
  },
  {
    name: "Competition in Business",
    points: [
      // FILL IN: competitive insight from advisory work
      // FILL IN: what businesses misunderstand about competitors
      // FILL IN: how Revamp frames competitive advantage
    ]
  },
  {
    name: "Leadership",
    points: [
      // FILL IN: leadership quality seen in successful clients
      // FILL IN: common leadership mistake in strategy
      // FILL IN: how Revamp coaches leaders through decisions
    ]
  },
  {
    name: "Succession Planning",
    points: [
      // FILL IN: why most businesses leave this too late
      // FILL IN: what Revamp's succession advisory looks like
      // FILL IN: specific risk without a succession plan
    ]
  },
  {
    name: "Strategy Execution",
    points: [
      // FILL IN: most common execution failure Revamp sees
      // FILL IN: a specific execution framework Revamp uses
      // FILL IN: what separates businesses that execute from those that don't
    ]
  }
];

// Select today's topic by rotating through 9 topics
const dayOfYear = Math.floor((Date.now() - new Date(new Date().getFullYear(), 0, 0)) / 86400000);
const topic = topics[dayOfYear % topics.length];

const prompt = `You are a content writer for Revamp Consulting LLC, a business strategy advisory firm.

Write a LinkedIn and Instagram post on this topic: ${topic.name}

Use ONLY these specific angles. Do not add anything outside them:
${topic.points.map((p, i) => `${i + 1}. ${p}`).join('\n')}

Rules:
- Maximum 75 words. Hard limit. Count carefully.
- No hashtags.
- No emojis.
- No filler phrases like "In today's business world".
- Get to the point immediately.
- End with this exact line: Ready to build a strategy that works? Talk to us at https://www.revampconsult.com

Output the post text only. No preamble, no "Here is the post:", just the post.`;

return [{ json: { topic: topic.name, prompt } }];
```

---

## Node-by-Node Build

### Node 1 — Schedule Trigger
- Type: `n8n-nodes-base.scheduleTrigger` v1.3
- Parameters:
  - `rule.interval[0].field`: `days`
  - `rule.interval[0].triggerAtHour`: `9`
  - `rule.interval[0].triggerAtMinute`: `0`
- Timezone: set to `Africa/Lagos` in n8n instance settings

---

### Node 2 — Build Prompt (Code)
- Type: `n8n-nodes-base.code` v2
- Mode: `runOnceForAllItems`
- Paste the full topics array + topic selector + prompt builder from the section above
- Output contains: `topic` (string), `prompt` (string)

---

### Node 3 — Generate Post (Groq API)
- Type: `n8n-nodes-base.httpRequest` v4.4
- Method: `POST`
- URL: `https://api.groq.com/openai/v1/chat/completions`
- Authentication: `genericCredentialType` → `httpHeaderAuth` → credential: Groq
- Send body: yes, content type: JSON (specifyBody: `json`)
- JSON body:
```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ],
  "max_tokens": 200,
  "temperature": 0.7
}
```
- Output expression to use downstream: `{{ $json.choices[0].message.content }}`

---

### Node 4 — Telegram Approval (sendAndWait)
- Type: `n8n-nodes-base.telegram` v1.2
- Resource: `message`, Operation: `sendAndWait`
- `chatId`: your Telegram chat ID (hardcode or use env var)
- `message`:
```
📋 Daily Post — {{ $('Build Prompt').item.json.topic }}

{{ $('Generate Post').item.json.choices[0].message.content }}

What do you want to do?
```
- `responseType`: `approval`
- `approvalOptions.values.approvalType`: `double`
- `approvalOptions.values.approveLabel`: `✅ Approve and Publish`
- `approvalOptions.values.disapproveLabel`: `✏️ Edit or Regenerate`
- Limit wait time: 23 hours (so it expires before next day's post)
- `options.appendAttribution`: `false`

**Note on the approval flow:** `sendAndWait` with `approval` type gives two buttons. Approve goes to the true branch; the other option (Edit/Regenerate) goes to the false branch. For the edit vs regenerate split, use a second Telegram `sendAndWait` on the false branch with `responseType: freeText` — ask "Send your edited text, or type REGENERATE to get a new one."

---

### Node 5 — Route Response (Switch or If)

**Option A — Simple (Approve/Decline):**

Use `ifElse` directly from the `sendAndWait` output:
- `onTrue` → Node 6 (Publish)
- `onFalse` → Node 7 (Edit or Regenerate prompt)

**Option B — Three-way (if you want explicit regenerate):**

Add a second `sendAndWait` on the false branch:
- `responseType`: `freeText`
- Message: "Send your edited version to publish it, or type REGENERATE to get a new post on the same topic."
- Then check: if response text equals `REGENERATE` → loop back to Node 3 (via a Set node that preserves the prompt)
- Otherwise: treat response text as the final post → publish it

---

### Node 6 — Publish (Upload-Post)
- Type: `n8n-nodes-base.httpRequest` v4.4
- Method: `POST`
- URL: Upload-Post publish endpoint (check their docs — likely `https://api.upload-post.com/api/upload`)
- Authentication: HTTP Header Auth → Upload-Post credential
- JSON body (check Upload-Post docs for exact field names):
```json
{
  "networks": ["linkedin", "instagram"],
  "text": "{{ $json.data?.text ?? $('Generate Post').item.json.choices[0].message.content }}"
}
```

**Important:** Check Upload-Post's API documentation for:
1. Exact endpoint URL
2. Exact field names (`networks` vs `platforms`, `text` vs `content`, etc.)
3. Whether account IDs are needed in the body or inferred from the API key

---

### Node 7 — Confirm Published (Telegram sendMessage)
- Type: `n8n-nodes-base.telegram` v1.2
- Resource: `message`, Operation: `sendMessage`
- `chatId`: same chat ID
- `text`: `✅ Published to LinkedIn and Instagram.`

---

## What to Verify Before First Live Run

1. Groq key works — test with a direct curl: `curl https://api.groq.com/openai/v1/chat/completions -H "Authorization: Bearer KEY" -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"say hi"}]}'`
2. Topics array is filled in with real Revamp content — not placeholder comments
3. Telegram bot responds — send it a message, confirm the bot replies
4. Upload-Post API key works — check their docs for a test endpoint or ping support
5. Instagram is a Business account linked to a Facebook Page — if not, LinkedIn-only until it is
6. Run the workflow manually once (use Manual Trigger temporarily) before activating the cron
7. Check the Telegram message arrives with the buttons
8. Click Approve — confirm the post appears on LinkedIn and Instagram within 60 seconds

---

## What Is Not Built in Phase 1

- Image generation — text only
- Multiple posts per day — one post at 9AM
- Analytics — no tracking
- Team approval — one approver only
- Posting to any platform other than LinkedIn and Instagram

---

## Contact Form URL

The CTA inside each post links to Revamp's contact form. Get the exact URL from Bayonet before the first run and update the prompt template in Node 2. Currently placeholder: `https://www.revampconsult.com`

---

*Build spec v1.1 — simplified 2026-07-18*

# Jang AI Video Automation System — Full Build Spec
**Date:** 2026-07-19
**Client:** Jang (jpjiang18) — Prescription Safety + Sports Glasses
**Platforms:** Facebook + Instagram
**Builder:** Emmanuel Adekoya

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Platform Setup Checklist](#4-platform-setup-checklist)
5. [Google Sheets Schema](#5-google-sheets-schema)
6. [Tally Form Setup](#6-tally-form-setup)
7. [Workflow 01 — Master Orchestrator](#7-workflow-01--master-orchestrator)
8. [Workflow 02 — Generate Video Scenes](#8-workflow-02--generate-video-scenes)
9. [Workflow 03 — Assemble Video](#9-workflow-03--assemble-video)
10. [Workflow 04 — Publish to Social](#10-workflow-04--publish-to-social)
11. [Workflow 05 — Error Handler](#11-workflow-05--error-handler)
12. [Claude Script Prompt Engineering](#12-claude-script-prompt-engineering)
13. [Kie AI Prompting Strategy for Glasses](#13-kie-ai-prompting-strategy-for-glasses)
14. [Creatomate Template Spec](#14-creatomate-template-spec)
15. [Blotato Publishing Spec](#15-blotato-publishing-spec)
16. [Approval Gate (Optional Flow)](#16-approval-gate-optional-flow)
17. [Email Notification Templates](#17-email-notification-templates)
18. [Error Handling Matrix](#18-error-handling-matrix)
19. [Testing Checklist](#19-testing-checklist)
20. [Deployment and Handoff](#20-deployment-and-handoff)

---

## 1. Project Overview

### What This System Does

The client submits a product via a Tally form with talking points and a product image. The system:

1. Validates the submission
2. Generates a short-form ad script using Claude AI
3. Generates 5 video scenes using Kie AI (Google Veo 3.1)
4. Assembles all scenes into a finished video using Creatomate
5. (Optional) Sends the video to the client for approval via email
6. Publishes the finished video to Facebook and Instagram via Blotato
7. Logs every run to Google Sheets
8. Sends a success or failure email after every run

### Output Spec

| Property | Value |
|---|---|
| Video length | 30 to 60 seconds |
| Scenes | 5 scenes |
| Aspect ratio | 9:16 (vertical — Reels/Stories format) |
| Resolution | 1080x1920 |
| Captions | Burned in via Creatomate |
| Brand overlay | Logo + brand color lower third |
| Platforms | Facebook Page + Instagram Business |
| Posting mode | Auto-post OR approval-then-post (configurable) |

### Trigger

Tally form webhook → n8n Workflow 01

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT SIDE                              │
│                                                                 │
│  Jang fills Tally Form                                          │
│  (product name, talking points, product image, audience, goal)  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Webhook (POST)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   WORKFLOW 01: MASTER ORCHESTRATOR              │
│                                                                 │
│  1. Receive Tally webhook payload                               │
│  2. Validate required fields                                    │
│     └─ Missing field? → Send error email → STOP                 │
│  3. Generate run_id (timestamp + slug)                          │
│  4. Write initial row to Google Sheets (status: STARTED)        │
│  5. Call Claude AI → generate 5-scene ad script                 │
│  6. Parse Claude JSON output → extract 5 scene prompts          │
│  7. Write script to Google Sheets                               │
│  8. Call Workflow 02 (Generate Video Scenes) via webhook/subflow │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               WORKFLOW 02: GENERATE VIDEO SCENES                │
│                                                                 │
│  For each of 5 scenes (run as loop or parallel):                │
│  1. POST scene prompt + product image to Kie AI                 │
│  2. Receive task_id from Kie AI                                  │
│  3. Poll Kie AI every 30s for completion                        │
│     ├─ PENDING → wait 30s → poll again (max 20 attempts)        │
│     ├─ SUCCESS → save video_url to Google Sheets                │
│     └─ FAILED → retry submit (max 3 regens) → if still fail:   │
│                  flag scene as FAILED in Sheet, continue others  │
│  4. When all 5 scenes done → call Workflow 03                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               WORKFLOW 03: ASSEMBLE VIDEO                       │
│                                                                 │
│  1. Read all 5 scene video URLs from Google Sheets              │
│  2. Build Creatomate render payload                             │
│  3. POST to Creatomate API                                      │
│  4. Poll Creatomate every 30s for completion (max 20 attempts)  │
│  5. Receive final_video_url                                     │
│  6. Write final_video_url to Google Sheets (status: ASSEMBLED)  │
│  7a. If approval_required = true → call Approval Gate           │
│  7b. If approval_required = false → call Workflow 04            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               WORKFLOW 04: PUBLISH TO SOCIAL                    │
│                                                                 │
│  1. Read final_video_url + product data from Google Sheets      │
│  2. Generate platform-specific captions (Claude or template)    │
│  3. POST to Blotato API (Facebook + Instagram simultaneously)   │
│  4. Receive post URLs from Blotato                              │
│  5. Write fb_post_url + ig_post_url to Google Sheets            │
│  6. Update status: PUBLISHED                                    │
│  7. Send success email to Jang with post links                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               WORKFLOW 05: ERROR HANDLER (GLOBAL)               │
│                                                                 │
│  Listens on n8n error trigger                                   │
│  Fires automatically when ANY workflow throws an error          │
│  Sends branded HTML error email:                                │
│  - Which workflow failed                                        │
│  - Which node failed                                            │
│  - Error message                                                │
│  - Direct link to n8n execution                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Tool | Role | Tier | Paid By |
|---|---|---|---|
| **Tally** | Product intake form | Free | Jang |
| **n8n** | Workflow orchestration | ~$20/mo cloud or self-hosted free | Jang |
| **Claude AI (Anthropic)** | Script generation | Pay-per-use (~$0.01/run) | Jang |
| **Kie AI** | Video scene generation (Veo 3.1) | Pay-per-use (~$3-8/video) | Jang |
| **Creatomate** | Video assembly + captions | ~$29/mo | Jang |
| **Blotato** | Social media publishing | ~$29/mo | Jang |
| **Google Sheets** | Run tracking and logging | Free | Jang |
| **Gmail (SMTP)** | Success + error email alerts | Free | Jang |

### API Credentials Needed

```
ANTHROPIC_API_KEY=sk-ant-...
KIE_AI_API_KEY=...
CREATOMATE_API_KEY=...
BLOTATO_API_KEY=...
GOOGLE_SHEETS_ID=...
GMAIL_SMTP_USER=...
GMAIL_SMTP_PASS=...  (App password, not main password)
TALLY_WEBHOOK_SECRET=... (for signature verification)
CLIENT_EMAIL=jang@...  (where to send notifications)
```

Store all credentials in n8n credential store. Never hardcode in workflow nodes.

---

## 4. Platform Setup Checklist

Complete these in order before building any workflow.

### 4.1 Google Sheets

- [ ] Create a new Google Sheet named: `Jang AI Video Tracker`
- [ ] Create 3 tabs: `Runs`, `Scenes`, `Final Log`
- [ ] Set up column headers (see Section 5)
- [ ] Share the sheet with the n8n Google Sheets service account email
- [ ] Copy the Sheet ID from the URL and store in n8n

### 4.2 Tally

- [ ] Create a Tally form (see Section 6 for full field list)
- [ ] Enable webhook integration → point to n8n Workflow 01 webhook URL
- [ ] Enable webhook signature verification (copy secret to n8n)
- [ ] Test form submission manually → verify webhook fires

### 4.3 Kie AI

- [ ] Create Kie AI account under Jang's name
- [ ] Load credits (minimum $20 to start)
- [ ] Copy API key to n8n credential store
- [ ] Test API: POST a single video generation request and confirm task_id returned

### 4.4 Creatomate

- [ ] Create Creatomate account under Jang's name
- [ ] Build the video template (see Section 14)
- [ ] Copy template_id and API key to n8n
- [ ] Test API: POST a render with dummy video URLs and confirm render starts

### 4.5 Blotato

- [ ] Create Blotato account under Jang's name
- [ ] Connect Facebook Page via Blotato OAuth
- [ ] Connect Instagram Business account via Blotato OAuth
- [ ] Copy API key to n8n
- [ ] Test: POST a dummy video to both platforms and confirm it goes live

### 4.6 Gmail

- [ ] Enable 2FA on the Gmail account used for alerts
- [ ] Generate an App Password (Google Account → Security → App Passwords)
- [ ] Store SMTP credentials in n8n credential store
- [ ] Test: send a test email from n8n using SMTP node

### 4.7 n8n Instance

- [ ] n8n cloud account OR self-hosted instance running
- [ ] Confirm webhook URLs are publicly accessible (not localhost)
- [ ] Set up n8n error workflow trigger (used by Workflow 05)

---

## 5. Google Sheets Schema

### Sheet 1: Runs

Tracks one row per pipeline run.

| Column | Type | Description |
|---|---|---|
| `run_id` | String | Auto-generated: `JANG-YYYYMMDD-HHMMSS` |
| `product_name` | String | From Tally form |
| `product_type` | String | safety / sports / prescription-sports |
| `target_audience` | String | From Tally form |
| `ad_goal` | String | awareness / sales / retargeting |
| `product_image_url` | URL | Tally file upload URL |
| `talking_points` | String | Raw text from Tally form |
| `approval_required` | Boolean | true / false (from Tally form) |
| `status` | String | STARTED / SCRIPTED / GENERATING / ASSEMBLED / PENDING_APPROVAL / PUBLISHED / FAILED |
| `script_json` | JSON string | Full Claude output (5 scenes) |
| `assembly_video_url` | URL | Creatomate final video URL |
| `fb_post_url` | URL | Live Facebook post URL |
| `ig_post_url` | URL | Live Instagram post URL |
| `error_message` | String | Populated if status = FAILED |
| `created_at` | Timestamp | ISO 8601 |
| `updated_at` | Timestamp | ISO 8601, updated at each stage |

### Sheet 2: Scenes

Tracks one row per scene per run. 5 rows per run.

| Column | Type | Description |
|---|---|---|
| `run_id` | String | Foreign key to Sheet 1 |
| `scene_number` | Integer | 1 to 5 |
| `scene_title` | String | From Claude script |
| `video_prompt` | String | The exact prompt sent to Kie AI |
| `kie_task_id` | String | Returned by Kie AI on submission |
| `poll_attempts` | Integer | How many times polled (max 20) |
| `regen_attempts` | Integer | How many times resubmitted (max 3) |
| `status` | String | SUBMITTED / POLLING / COMPLETE / FAILED |
| `video_url` | URL | Kie AI output video URL |
| `submitted_at` | Timestamp | When Kie API was called |
| `completed_at` | Timestamp | When video URL was confirmed |

### Sheet 3: Final Log

One row per completed run (success or failure). Clean summary for Jang.

| Column | Type | Description |
|---|---|---|
| `run_id` | String | |
| `product_name` | String | |
| `outcome` | String | SUCCESS / FAILED |
| `final_video_url` | URL | |
| `fb_post_url` | URL | |
| `ig_post_url` | URL | |
| `total_run_time_minutes` | Integer | From STARTED to PUBLISHED |
| `completed_at` | Timestamp | |

---

## 6. Tally Form Setup

### Form Name: Jang Glasses Video Request

### Fields

| Field Label | Field Type | Required | Variable Name |
|---|---|---|---|
| Product Name | Short text | Yes | `product_name` |
| Product Type | Dropdown | Yes | `product_type` |
| Talking Points | Long text | Yes | `talking_points` |
| Product Image | File upload | Yes | `product_image` |
| Target Audience | Dropdown | Yes | `target_audience` |
| Ad Goal | Dropdown | Yes | `ad_goal` |
| Approve Before Posting? | Yes/No toggle | Yes | `approval_required` |

### Dropdown Options

**Product Type:**
- Safety glasses
- Sports glasses
- Prescription sports glasses
- Fashion/lifestyle glasses

**Target Audience:**
- Construction and industrial workers
- Athletes and active lifestyle
- General outdoor lifestyle
- Medical and lab professionals

**Ad Goal:**
- Brand awareness
- Direct sales (drive to website)
- Retargeting (remind past visitors)

### Validation

After webhook fires, Workflow 01 must check:
- `product_name` is not empty
- `talking_points` is not empty and at least 20 characters
- `product_image` URL is not empty and is a valid URL
- `product_type` is one of the allowed values

If any check fails: send validation error email to client email and STOP the workflow. Do not write a row to Sheets.

---

## 7. Workflow 01 — Master Orchestrator

### Trigger

Tally webhook (HTTP POST)
- Webhook URL: `https://your-n8n-instance/webhook/jang-video-intake`
- Method: POST
- Verify Tally signature header: `tally-signature`

### Nodes

```
[1] Webhook (Tally trigger)
     ↓
[2] Validate Fields (Code node)
     ├─ INVALID → [3] Send Validation Error Email → [END]
     └─ VALID ↓
[4] Generate run_id (Code node)
     ↓
[5] Write Initial Row to Sheets — Sheet: Runs
     (status: STARTED, run_id, all form fields, created_at)
     ↓
[6] HTTP Request → Claude AI (Generate Script)
     ↓
[7] Parse Claude Response (Code node)
     ├─ PARSE ERROR → [8] Update Sheet status: FAILED → [9] Send Error Email → [END]
     └─ SUCCESS ↓
[10] Write Script to Sheets — Sheet: Runs
     (update: script_json, status: SCRIPTED)
     ↓
[11] Write 5 Scene Rows to Sheets — Sheet: Scenes
     (one row per scene, status: PENDING)
     ↓
[12] HTTP Request → Trigger Workflow 02
     (pass: run_id, scene prompts array, product_image_url)
```

### Node 2 — Validate Fields (Code)

```javascript
const body = $input.first().json;
const fields = body.data?.fields || [];

const getValue = (label) => {
  const f = fields.find(f => f.label === label);
  return f?.value || '';
};

const product_name = getValue('Product Name');
const talking_points = getValue('Talking Points');
const product_image = getValue('Product Image');
const product_type = getValue('Product Type');

const errors = [];
if (!product_name) errors.push('Product Name is missing');
if (!talking_points || talking_points.length < 20) errors.push('Talking Points too short or missing');
if (!product_image) errors.push('Product Image is missing');
if (!product_type) errors.push('Product Type is missing');

return [{
  json: {
    valid: errors.length === 0,
    errors,
    product_name,
    talking_points,
    product_image_url: product_image,
    product_type,
    target_audience: getValue('Target Audience'),
    ad_goal: getValue('Ad Goal'),
    approval_required: getValue('Approve Before Posting?') === 'Yes',
  }
}];
```

### Node 4 — Generate run_id (Code)

```javascript
const now = new Date();
const pad = (n) => String(n).padStart(2, '0');
const dateStr = `${now.getFullYear()}${pad(now.getMonth()+1)}${pad(now.getDate())}`;
const timeStr = `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
const run_id = `JANG-${dateStr}-${timeStr}`;

return [{ json: { ...($input.first().json), run_id, created_at: now.toISOString() } }];
```

### Node 6 — Claude API Call

- **URL:** `https://api.anthropic.com/v1/messages`
- **Method:** POST
- **Headers:** `x-api-key: {{$credentials.anthropic_api_key}}`, `anthropic-version: 2023-06-01`
- **Body:** See Section 12 for full prompt

### Node 7 — Parse Claude Response (Code)

```javascript
const raw = $input.first().json.content[0].text;
let parsed;
try {
  // Claude returns JSON wrapped in markdown code block sometimes
  const jsonMatch = raw.match(/```json\n?([\s\S]*?)\n?```/) || raw.match(/(\{[\s\S]*\})/);
  parsed = JSON.parse(jsonMatch ? jsonMatch[1] : raw);
} catch(e) {
  return [{ json: { parse_error: true, raw_response: raw, error: e.message } }];
}

return [{ json: { parse_error: false, script: parsed, ...($input.first().json) } }];
```

### Node 11 — Write 5 Scene Rows to Sheets (Loop)

Use a Code node to split scenes into 5 items, then a Google Sheets Append node.

```javascript
const data = $input.first().json;
const scenes = data.script.scenes;

return scenes.map((scene, i) => ({
  json: {
    run_id: data.run_id,
    scene_number: i + 1,
    scene_title: scene.title,
    video_prompt: scene.video_prompt,
    kie_task_id: '',
    poll_attempts: 0,
    regen_attempts: 0,
    status: 'PENDING',
    video_url: '',
    submitted_at: '',
    completed_at: '',
  }
}));
```

---

## 8. Workflow 02 — Generate Video Scenes

### Trigger

Called by Workflow 01 via HTTP Request node (internal webhook).

Receives: `run_id`, `scenes` (array of 5 scene objects with `video_prompt`), `product_image_url`

### Strategy

Process scenes sequentially (not parallel) to avoid Kie AI rate limits. Each scene goes through its own submit → poll loop before moving to the next.

### Nodes (per scene — wrapped in a loop)

```
[1] Webhook (internal trigger from WF01)
     ↓
[2] Split Into Scenes (Code node — output 5 items)
     ↓
[3] Loop: For each scene:
     │
     ├─ [4] POST to Kie AI (submit generation)
     │       Body: { prompt, negative_prompt, reference_image_url, duration, aspect_ratio }
     │       Response: { task_id }
     │
     ├─ [5] Update Scene Row in Sheets
     │       (kie_task_id, status: SUBMITTED, submitted_at)
     │
     ├─ [6] Wait 30 seconds (Wait node)
     │
     ├─ [7] POLL LOOP (Code + HTTP + If nodes):
     │   ┌─ [7a] GET Kie AI task status (task_id)
     │   │   ├─ status = SUCCEEDED → [8] Save video_url → continue to next scene
     │   │   ├─ status = FAILED → [9] Regen check:
     │   │   │     regen_attempts < 3 → resubmit → back to [4]
     │   │   │     regen_attempts >= 3 → mark scene FAILED in Sheets → continue
     │   │   └─ status = PENDING/PROCESSING → poll_attempts < 20 → wait 30s → loop
     │   │                                     poll_attempts >= 20 → mark TIMEOUT → continue
     │   └─────────────────────────────────────────────────────────────────────────────
     │
[10] All 5 scenes processed (success or fail)
     ↓
[11] Check: any scenes failed?
     ├─ ALL FAILED → Update Sheets status: FAILED → Send error email → END
     └─ PARTIAL or ALL SUCCESS → Update Sheets status: GENERATING_COMPLETE
          ↓
[12] HTTP Request → Trigger Workflow 03
```

### Node 4 — Submit to Kie AI

```
URL: https://api.kieai.com/v1/video/generate
Method: POST
Headers:
  Authorization: Bearer {{$credentials.kie_ai_key}}
  Content-Type: application/json

Body:
{
  "prompt": "{{ $json.video_prompt }}",
  "negative_prompt": "blurry, low quality, distorted faces, unrealistic hands, bad lighting, overexposed",
  "reference_image_url": "{{ $json.product_image_url }}",
  "duration": 6,
  "aspect_ratio": "9:16",
  "resolution": "1080x1920",
  "model": "veo-3-fast"
}
```

### Node 7a — Poll Kie AI

```
URL: https://api.kieai.com/v1/task/{{ $json.kie_task_id }}
Method: GET
Headers:
  Authorization: Bearer {{$credentials.kie_ai_key}}
```

### Polling State Machine (Code node)

```javascript
const taskStatus = $input.first().json;
const scene = $('Split Into Scenes').item.json;

const status = taskStatus.status; // 'SUCCEEDED', 'FAILED', 'PENDING', 'PROCESSING'
const pollAttempts = (scene.poll_attempts || 0) + 1;
const regenAttempts = scene.regen_attempts || 0;

if (status === 'SUCCEEDED') {
  return [{ json: {
    route: 'success',
    video_url: taskStatus.video_url,
    scene_number: scene.scene_number,
    run_id: scene.run_id,
    poll_attempts: pollAttempts,
  }}];
}

if (status === 'FAILED') {
  if (regenAttempts < 3) {
    return [{ json: { route: 'regen', ...scene, regen_attempts: regenAttempts + 1, poll_attempts: 0 } }];
  }
  return [{ json: { route: 'scene_failed', ...scene, regen_attempts: regenAttempts, status: 'FAILED' } }];
}

// PENDING or PROCESSING
if (pollAttempts >= 20) {
  return [{ json: { route: 'timeout', ...scene, poll_attempts: pollAttempts, status: 'TIMEOUT' } }];
}

return [{ json: { route: 'wait', ...scene, poll_attempts: pollAttempts } }];
```

---

## 9. Workflow 03 — Assemble Video

### Trigger

Called by Workflow 02 via internal webhook.

Receives: `run_id`

### Nodes

```
[1] Webhook (internal trigger from WF02)
     ↓
[2] Read Scene URLs from Sheets (filter by run_id, Sheet: Scenes)
     ↓
[3] Build Creatomate Payload (Code node)
     ↓
[4] POST to Creatomate API (submit render)
     ↓
[5] Wait 30 seconds
     ↓
[6] POLL LOOP:
     ├─ GET render status from Creatomate
     ├─ status = succeeded → save final_video_url
     ├─ status = failed → update Sheets FAILED → send error email → END
     └─ status = queued/rendering → wait 30s → poll again (max 20 attempts)
          poll_attempts >= 20 → TIMEOUT → error email → END
     ↓
[7] Write final_video_url to Sheets (Sheet: Runs, status: ASSEMBLED)
     ↓
[8] If approval_required = true → Send Approval Email → END (wait for approval webhook)
    If approval_required = false → HTTP Request → Trigger Workflow 04
```

### Node 3 — Build Creatomate Payload (Code)

```javascript
const data = $input.all();
// Sort scenes by scene_number to ensure correct order
const scenes = data
  .map(i => i.json)
  .filter(s => s.status === 'COMPLETE')
  .sort((a, b) => a.scene_number - b.scene_number);

const run = $('Read Run Data').first().json; // run data from Sheet 1

// Build Creatomate modifications
const modifications = {};
scenes.forEach((scene, idx) => {
  modifications[`scene-${idx + 1}-video`] = scene.video_url;
});

// Add brand elements
modifications['brand-logo'] = 'https://your-cdn.com/jang-logo.png'; // store Jang's logo on CDN
modifications['product-name-text'] = run.product_name;
modifications['caption-text'] = run.caption_text || ''; // generated by Claude or Workflow 01

return [{
  json: {
    template_id: '{{$env.CREATOMATE_TEMPLATE_ID}}',
    modifications,
    run_id: run.run_id,
  }
}];
```

### Node 4 — POST to Creatomate

```
URL: https://api.creatomate.com/v1/renders
Method: POST
Headers:
  Authorization: ApiKey {{$credentials.creatomate_key}}
  Content-Type: application/json

Body:
{
  "template_id": "{{ $json.template_id }}",
  "modifications": "{{ $json.modifications }}"
}
```

---

## 10. Workflow 04 — Publish to Social

### Trigger

Called by Workflow 03 via internal webhook (or Approval Gate webhook if approval enabled).

Receives: `run_id`

### Nodes

```
[1] Webhook (internal trigger)
     ↓
[2] Read Run Data from Sheets (run_id → Sheet: Runs)
     ↓
[3] Generate Captions (Code node — platform-specific)
     ↓
[4] POST to Blotato API (publish to FB + IG)
     ↓
[5] Parse Blotato Response → extract fb_post_url, ig_post_url
     ↓
[6] Write post URLs to Sheets (Sheet: Runs + Sheet: Final Log)
     ↓
[7] Update status: PUBLISHED, updated_at: now
     ↓
[8] Send Success Email to Jang
```

### Node 3 — Generate Captions (Code)

```javascript
const run = $input.first().json;

// Facebook caption — longer, includes CTA
const fb_caption = `${run.talking_points.split('.')[0].trim()}.

Built for the active lifestyle. Our ${run.product_name} are engineered for people who don't slow down.

Shop now → [link in bio]

#SafetyGlasses #SportsEyewear #GlassesForAthletes #${run.product_name.replace(/\s/g, '')}`;

// Instagram caption — hook first line (appears before "more"), hashtags below
const ig_caption = `The last pair of glasses you'll need. 🔲

${run.product_name} — designed for performance, built to protect.

Shop link in bio.

#PrescriptionSafetyGlasses #SportsGlasses #ActiveLifestyle #Eyewear #ProtectYourEyes #GlassesOfInstagram #SafetyFirst #AthleticEyewear`;

return [{
  json: {
    ...run,
    fb_caption,
    ig_caption,
  }
}];
```

> **Note:** Caption templates above are defaults. Adjust based on Jang's brand tone after first review. Can optionally use Claude to generate captions dynamically if more variety is needed.

### Node 4 — POST to Blotato

```
URL: https://api.blotato.com/v1/posts
Method: POST
Headers:
  Authorization: Bearer {{$credentials.blotato_key}}
  Content-Type: application/json

Body:
{
  "video_url": "{{ $json.assembly_video_url }}",
  "platforms": [
    {
      "platform": "facebook",
      "caption": "{{ $json.fb_caption }}",
      "page_id": "{{ $env.FACEBOOK_PAGE_ID }}"
    },
    {
      "platform": "instagram",
      "caption": "{{ $json.ig_caption }}",
      "account_id": "{{ $env.INSTAGRAM_ACCOUNT_ID }}"
    }
  ]
}
```

> **Note:** Confirm exact Blotato API schema from their docs. The structure above is representative. Adjust `platform` keys, `page_id`, and `account_id` fields per Blotato's actual API.

---

## 11. Workflow 05 — Error Handler

### Trigger

n8n Error Trigger node — fires automatically when any workflow in the n8n instance throws an unhandled error.

### Nodes

```
[1] n8n Error Trigger (built-in)
     ↓
[2] Extract Error Context (Code node)
     ↓
[3] Update Google Sheets if run_id available
     (status: FAILED, error_message: error details)
     ↓
[4] Send HTML Error Email to Emmanuel (developer/operator)
```

### Node 2 — Extract Error Context (Code)

```javascript
const error = $input.first().json;

return [{
  json: {
    workflow_name: error.workflow?.name || 'Unknown Workflow',
    execution_id: error.execution?.id || 'Unknown',
    node_name: error.execution?.lastNodeExecuted || 'Unknown Node',
    error_message: error.execution?.error?.message || 'No message',
    error_stack: error.execution?.error?.stack || '',
    execution_url: `https://your-n8n-instance/execution/${error.execution?.id}`,
    timestamp: new Date().toISOString(),
    run_id: error.execution?.data?.resultData?.runData?.['Generate run_id']?.[0]?.data?.main?.[0]?.[0]?.json?.run_id || 'unknown',
  }
}];
```

### Error Email (HTML)

See Section 17 for the full HTML email template.

---

## 12. Claude Script Prompt Engineering

### System Prompt

```
You are an expert direct-response ad scriptwriter for eyewear brands. You write short-form video scripts for Facebook and Instagram ads. Your scripts sound like a confident, experienced person talking about a product they actually use — not a generic ad voice.

Rules:
- Never use: "innovative", "revolutionary", "premium", "state-of-the-art", "cutting-edge", "seamless"
- Write like someone who knows the product and has nothing to prove
- Each scene must connect naturally to the previous one
- The hook (Scene 1) must create immediate visual tension or curiosity in the first 3 seconds
- Output ONLY valid JSON, no markdown, no preamble, no explanation
```

### User Prompt

```
Write a 5-scene short-form video ad script for the following glasses product.

Product Name: {{product_name}}
Product Type: {{product_type}}
Target Audience: {{target_audience}}
Ad Goal: {{ad_goal}}
Talking Points: {{talking_points}}

Output this exact JSON structure:
{
  "scenes": [
    {
      "scene_number": 1,
      "title": "Hook",
      "duration_seconds": 6,
      "script_line": "The one line the presenter says in this scene",
      "visual_description": "What is happening on screen — movement, environment, action",
      "video_prompt": "The exact prompt to send to the AI video generator. Start with the main subject. Be specific about lighting, environment, action, and that the person is wearing the glasses. Do NOT say 'AI' or 'generated'. Write it as a cinematic scene description.",
      "caption_text": "On-screen text overlay for this scene (short, 1-5 words)"
    },
    ... (5 scenes total)
  ],
  "full_script": "All 5 scene lines combined into one paragraph",
  "facebook_caption": "Platform-optimized Facebook post caption",
  "instagram_caption": "Platform-optimized Instagram post caption"
}

Scene structure must follow this flow:
Scene 1 (Hook, 6s): Visual action shot. Person wearing glasses in a high-energy moment. No talking yet.
Scene 2 (Problem/Context, 8s): Presenter addresses the camera. One line about who these glasses are for.
Scene 3 (Feature 1, 10s): Close-up product showcase. Name the most important feature from the talking points.
Scene 4 (Feature 2 + Social Proof, 10s): Action shot. Name a second feature or use case.
Scene 5 (CTA, 8s): Product facing camera. Brand name. Clear call to action.
```

### Important Notes for Developer

- Parse Claude's response strictly. If JSON is malformed, log the raw response to Sheets and send an error email.
- Claude sometimes wraps JSON in markdown (` ```json ... ``` `). Strip the code fence before parsing.
- Store the full raw Claude response in `script_json` column of Sheets for debugging.
- If Claude output passes validation, extract `scenes[].video_prompt` for Kie AI submission.

---

## 13. Kie AI Prompting Strategy for Glasses

Glasses on faces are technically difficult for AI video — the model must generate realistic humans with eyewear that reads as actual glasses, not props or blurs.

### Prompt Structure (for each scene)

```
[SUBJECT AND ACTION], wearing [GLASSES_TYPE] in [SETTING].
[LIGHTING_DESCRIPTION]. [CAMERA_MOVEMENT]. [MOOD].
High quality cinematic footage, photorealistic, sharp focus, natural motion.
```

### Scene-specific Templates

**Scene 1 (Hook — action shot):**
```
An athlete mid-motion, sprinting on a track at golden hour, wearing sleek wraparound sports glasses. 
Dynamic side-angle tracking shot, sun glinting off the lens. Fast-paced, energetic.
High quality cinematic footage, photorealistic, sharp focus.
```

**Scene 2 (Presenter/talking head):**
```
A person in their early 30s standing outdoors in natural daylight, wearing prescription safety glasses, 
speaking directly to camera with calm confidence. Medium close-up, shallow depth of field, 
soft bokeh background of an industrial or outdoor workspace. Photorealistic, cinematic.
```

**Scene 3 (Close-up product):**
```
Extreme close-up of a pair of sports glasses rotating slowly in 3D space against a clean white or 
dark gradient background. Lens flare catching studio light. Photorealistic product shot style.
High clarity, no motion blur, sharp edges.
```

**Scene 4 (Action + use case):**
```
A construction worker in full gear, wearing prescription safety glasses, examining a blueprint 
on a job site. Bright daylight, lens clearly visible and clean. 
Medium shot, realistic environment, photorealistic.
```

**Scene 5 (CTA — brand close):**
```
A pair of glasses lying flat on a clean matte surface with soft side lighting. 
Brand logo appears subtly in the corner. Slow zoom in. Clean, minimal, authoritative.
Photorealistic product photography style.
```

### Negative Prompt (use on every call)

```
blurry, distorted faces, unrealistic hands, badly placed glasses, floating glasses, 
extra limbs, bad anatomy, overexposed, underexposed, watermark, text overlay, 
low resolution, pixelated, cartoon, anime, painted, illustration
```

### Kie AI Parameters

```json
{
  "duration": 6,
  "aspect_ratio": "9:16",
  "resolution": "1080x1920",
  "model": "veo-3-fast",
  "seed": null
}
```

> Use `seed: null` (random) for variety. If a specific scene produces a great result and needs to be regenerated similarly, record the seed from the response and reuse it.

---

## 14. Creatomate Template Spec

### Template Structure

Build the Creatomate template manually in the Creatomate editor before wiring the API.

### Template Slots

| Slot Name | Type | Content |
|---|---|---|
| `scene-1-video` | Video | Kie AI scene 1 output URL |
| `scene-2-video` | Video | Kie AI scene 2 output URL |
| `scene-3-video` | Video | Kie AI scene 3 output URL |
| `scene-4-video` | Video | Kie AI scene 4 output URL |
| `scene-5-video` | Video | Kie AI scene 5 output URL |
| `brand-logo` | Image | Jang logo PNG (transparent background) |
| `product-name-text` | Text | Product name from Tally form |
| `caption-text` | Text | Per-scene caption overlay |

### Template Settings

```
Output format: MP4
Resolution: 1080 x 1920 (9:16)
Frame rate: 30fps
Total duration: dynamic (sum of all scene durations)
Audio: background music track (license a royalty-free track and bake it into template)
```

### Transitions

Use a 0.3s cross-dissolve between all scenes. No hard cuts on the first version — adjust based on client feedback.

### Caption Style

```
Font: Montserrat Bold or similar clean sans-serif
Size: 48-60pt
Color: White
Stroke: 2px black (for readability on all backgrounds)
Position: Bottom third, centered
```

### Logo Placement

```
Position: Top right corner
Size: ~15% of frame width
Opacity: 80%
Appears: Scenes 1, 5 only (not on talking-head scenes)
```

---

## 15. Blotato Publishing Spec

### What Blotato Receives

- `video_url`: The Creatomate final video URL (publicly accessible MP4 link)
- Platform-specific captions (generated in Workflow 04, Node 3)
- Facebook Page ID and Instagram Account ID (stored as n8n environment variables)

### Posting Settings

**Facebook:**
- Post type: Reel (short-form video)
- Caption: `fb_caption` (generated in Workflow 04)
- Targeting: None (organic post, client manages paid boosting separately)

**Instagram:**
- Post type: Reel
- Caption: `ig_caption` (generated in Workflow 04)
- Cover frame: First frame of video

### What to Extract From Blotato Response

After successful post, Blotato returns post IDs and URLs for each platform. Extract:
- `fb_post_url` or `fb_post_id`
- `ig_post_url` or `ig_post_id`

Write both to Google Sheets (Sheet 1: Runs, Sheet 3: Final Log).

> **Blotato API Note:** Confirm the exact response schema from Blotato documentation. Some posting APIs return post IDs only, not full URLs. If URLs are not returned, construct them from IDs: `https://www.facebook.com/{page_id}/posts/{post_id}` and `https://www.instagram.com/p/{shortcode}/`.

---

## 16. Approval Gate (Optional Flow)

This flow is activated when `approval_required = true` in the Tally form submission.

### When Workflow 03 Completes

Instead of calling Workflow 04 directly, do this:

```
[1] Update Sheets: status = PENDING_APPROVAL
     ↓
[2] Send Approval Email to Jang (see template in Section 17)
    Email contains:
    - Video preview link (final_video_url from Creatomate)
    - Approve button (links to approval webhook URL)
    - Reject/Redo button (links to rejection webhook URL)
     ↓
[Wait — no polling. Wait for Jang to click the link.]
```

### Approval Webhook (separate n8n workflow or node)

```
URL: https://your-n8n-instance/webhook/jang-video-approval
Method: GET
Query params: run_id, action (approve | reject)
```

On receive:
- `action = approve` → call Workflow 04 with run_id
- `action = reject` → update Sheets status: REJECTED → send confirmation to Jang

### Reminder

If no action within 24 hours, send a reminder email. Implement with a Wait node (24h timeout) branching on whether the approval webhook fired.

---

## 17. Email Notification Templates

### Success Email

**Subject:** `Your video is live — [product_name]`

**Body (HTML):**

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #FAFAFA; padding: 40px;">
  <h1 style="color: #D4E832; font-size: 24px; margin-bottom: 8px;">Video Published</h1>
  <p style="color: #AAAAAA; font-size: 14px; margin-bottom: 32px;">Run ID: [run_id]</p>
  
  <p style="font-size: 16px; margin-bottom: 24px;">
    Your video for <strong>[product_name]</strong> is now live on Facebook and Instagram.
  </p>
  
  <div style="background: #1A1A1A; border-left: 3px solid #D4E832; padding: 16px; margin-bottom: 24px;">
    <p style="margin: 0 0 8px; font-size: 13px; color: #AAAAAA;">FACEBOOK POST</p>
    <a href="[fb_post_url]" style="color: #D4E832; text-decoration: none; font-size: 14px;">[fb_post_url]</a>
  </div>
  
  <div style="background: #1A1A1A; border-left: 3px solid #D4E832; padding: 16px; margin-bottom: 32px;">
    <p style="margin: 0 0 8px; font-size: 13px; color: #AAAAAA;">INSTAGRAM POST</p>
    <a href="[ig_post_url]" style="color: #D4E832; text-decoration: none; font-size: 14px;">[ig_post_url]</a>
  </div>
  
  <p style="color: #555555; font-size: 12px;">
    Powered by your AI Video Automation System
  </p>
</div>
```

### Error Email (Developer Alert)

**Subject:** `[WORKFLOW FAILED] [workflow_name] — [timestamp]`

**Body (HTML):**

```html
<div style="font-family: 'JetBrains Mono', monospace; max-width: 600px; margin: 0 auto; background: #0D0D0D; color: #E0E0E0; padding: 40px;">
  <h1 style="color: #FF4444; font-size: 20px;">WORKFLOW FAILED</h1>
  <p style="color: #888; font-size: 12px; margin-bottom: 24px;">[timestamp]</p>
  
  <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
    <tr><td style="color: #888; padding: 8px 0; border-bottom: 1px solid #222;">Workflow</td><td style="color: #FFF; padding: 8px 0; border-bottom: 1px solid #222;">[workflow_name]</td></tr>
    <tr><td style="color: #888; padding: 8px 0; border-bottom: 1px solid #222;">Run ID</td><td style="color: #FFF; padding: 8px 0; border-bottom: 1px solid #222;">[run_id]</td></tr>
    <tr><td style="color: #888; padding: 8px 0; border-bottom: 1px solid #222;">Node</td><td style="color: #FFF; padding: 8px 0; border-bottom: 1px solid #222;">[node_name]</td></tr>
    <tr><td style="color: #888; padding: 8px 0; border-bottom: 1px solid #222;">Error</td><td style="color: #FF6666; padding: 8px 0; border-bottom: 1px solid #222;">[error_message]</td></tr>
  </table>
  
  <div style="margin-top: 24px;">
    <a href="[execution_url]" style="background: #D4E832; color: #0D0D0D; padding: 12px 24px; text-decoration: none; font-weight: bold; font-size: 13px; display: inline-block;">
      Open Failed Execution →
    </a>
  </div>
</div>
```

### Approval Request Email (if approval_required = true)

**Subject:** `Your video is ready for review — [product_name]`

**Body:**

```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0A0A0A; color: #FAFAFA; padding: 40px;">
  <h1 style="color: #D4E832; font-size: 24px;">Video Ready for Review</h1>
  <p>Your video for <strong>[product_name]</strong> is ready. Review it before it goes live.</p>
  
  <p>
    <a href="[final_video_url]" style="color: #D4E832;">Watch the video →</a>
  </p>
  
  <div style="margin-top: 32px; display: flex; gap: 16px;">
    <a href="[approval_url]?run_id=[run_id]&action=approve" 
       style="background: #D4E832; color: #0A0A0A; padding: 14px 32px; text-decoration: none; font-weight: bold; display: inline-block; margin-right: 16px;">
      Approve and Post
    </a>
    <a href="[approval_url]?run_id=[run_id]&action=reject" 
       style="background: #333; color: #FFF; padding: 14px 32px; text-decoration: none; display: inline-block;">
      Request Changes
    </a>
  </div>
</div>
```

---

## 18. Error Handling Matrix

| Failure Point | Cause | Handling |
|---|---|---|
| Tally webhook not received | Network issue or wrong URL | Tally has a retry policy; confirm webhook URL is correct and publicly accessible |
| Validation fails (missing fields) | Incomplete form submission | Send validation error email to Jang listing missing fields. Do not start pipeline. |
| Claude returns invalid JSON | Model hallucination or rate limit | Retry once after 5s. If still fails: log raw response, update Sheets FAILED, send error email. |
| Kie AI submission fails (4xx/5xx) | API down or bad request | Retry after 60s, up to 3 attempts. If all fail: mark scene FAILED, continue others. |
| Kie AI polling timeout (20 attempts, ~10min) | Very slow generation | Mark scene as TIMEOUT, flag in Sheets, continue to assembly with available scenes. |
| Kie AI scene generation failed (status=FAILED) | Content policy or prompt issue | Resubmit up to 3 times with same prompt. If all 3 fail: mark scene FAILED, continue. |
| All 5 scenes fail | API outage or prompt error | Update status: FAILED. Send error email to developer. Do not proceed to assembly. |
| Creatomate render fails | Template error or invalid video URL | Check if any scene URLs are empty. Retry render once. If fails: error email + FAILED status. |
| Creatomate polling timeout | Very slow render | Send error email. Update status FAILED. Dev must manually re-trigger assembly. |
| Blotato post fails | Auth expired or API error | Retry once after 30s. If fails: send error email. Video URL is in Sheets; dev can post manually. |
| Blotato auth expired | Token expiry | Blotato tokens should be refreshed via OAuth. Set up a reminder to re-authenticate every 60 days. |
| Google Sheets write fails | Quota exceeded or auth error | Log error to n8n execution log. Retry once. If fails: error email to developer. |
| Gmail send fails | Auth error | Log failure to n8n execution. Do not let email failure kill the main pipeline. |
| n8n instance down | Server issue | If self-hosted: set up uptime monitoring. If cloud: Tally form will queue webhooks. |

### Critical Rule

**Email alert failures must NEVER kill the main pipeline.** Always wrap email send nodes in a try-catch or use n8n's error handling to continue the main flow even if email fails. The video should still get published even if the notification email fails.

---

## 19. Testing Checklist

Complete all tests in order before handing over to the client.

### Unit Tests (per workflow)

**Workflow 01:**
- [ ] Submit valid Tally form → confirm webhook fires → confirm row created in Sheets
- [ ] Submit form with missing product_image → confirm validation error email sent → confirm no Sheet row created
- [ ] Submit form with missing talking_points → same as above
- [ ] Confirm run_id format is correct: `JANG-YYYYMMDD-HHMMSS`
- [ ] Confirm Claude is called and returns valid JSON
- [ ] Confirm 5 scene rows created in Sheet 2 (Scenes tab)
- [ ] Confirm Workflow 02 is triggered

**Workflow 02:**
- [ ] Submit a single scene to Kie AI → confirm task_id returned and stored in Sheets
- [ ] Simulate PENDING status for 3 polls, then SUCCEEDED → confirm video_url stored correctly
- [ ] Simulate FAILED status → confirm regen logic triggers → regen_attempts incremented in Sheets
- [ ] Simulate 3 consecutive FAILED statuses on same scene → confirm scene marked FAILED and pipeline continues
- [ ] Simulate 20 poll attempts without SUCCEEDED → confirm TIMEOUT handling
- [ ] Run all 5 scenes sequentially → confirm all 5 video_urls in Sheets before WF03 triggers

**Workflow 03:**
- [ ] Confirm Creatomate receives correct payload with all 5 video URLs
- [ ] Confirm Creatomate render starts and render_id is logged
- [ ] Confirm polling loop works: poll until succeeded
- [ ] Confirm final_video_url is stored in Sheets
- [ ] Confirm Workflow 04 is triggered (or approval email sent if approval_required = true)

**Workflow 04:**
- [ ] Confirm Blotato receives video_url and both captions
- [ ] Confirm post goes live on Facebook and Instagram
- [ ] Confirm post URLs written to Sheets (both Sheet 1 and Sheet 3)
- [ ] Confirm status updated to PUBLISHED
- [ ] Confirm success email sent to Jang with correct post links

**Workflow 05 (Error Handler):**
- [ ] Manually trigger a workflow failure (throw an error in a Code node)
- [ ] Confirm error email fires within 60 seconds
- [ ] Confirm email contains: workflow name, execution link, error message, run_id
- [ ] Confirm execution link in email leads directly to the failed execution in n8n

### Integration Tests (full run)

- [ ] **Test Run 1:** Submit a full form with all fields → confirm video published to both platforms end to end
- [ ] **Test Run 2:** Submit form with approval_required = true → confirm approval email sent → click Approve → confirm video published
- [ ] **Test Run 3:** Submit form with approval_required = true → click Reject → confirm REJECTED status in Sheets → no post goes live
- [ ] **Test Run 4:** Simulate Kie AI API timeout on 2 out of 5 scenes → confirm remaining 3 scenes still assemble and publish
- [ ] **Test Run 5:** Run the full pipeline twice consecutively → confirm run_ids are unique and Sheet rows do not overwrite

### Quality Checks

- [ ] Watch the assembled video — confirm correct scene order (1 through 5)
- [ ] Confirm captions appear on video and are readable
- [ ] Confirm logo appears on Scene 1 and Scene 5
- [ ] Confirm no black frames between scenes
- [ ] Check Facebook post: does the video autoplay in the feed?
- [ ] Check Instagram post: is it published as a Reel (not a static post)?
- [ ] Verify Sheet 3 (Final Log) has one row for the completed run

---

## 20. Deployment and Handoff

### Pre-Launch Checklist

- [ ] All 5 workflows active and published in n8n
- [ ] Workflow 05 (Error Handler) set as the global n8n error workflow
- [ ] All API credentials stored in n8n (not hardcoded anywhere)
- [ ] Tally form webhook pointing to live n8n URL (not localhost)
- [ ] Google Sheets headers set up on all 3 tabs
- [ ] Creatomate template built and template_id stored in n8n environment
- [ ] Blotato connected to Jang's Facebook Page and Instagram account
- [ ] Test emails received correctly (success and error templates)
- [ ] Full end-to-end test run completed successfully (Test Run 1 above)
- [ ] All platform accounts registered in Jang's name (not developer name)

### What Jang Owns

| Asset | Where |
|---|---|
| Tally form | Tally account in Jang's name |
| n8n workflows | n8n account in Jang's name |
| Google Sheets tracker | Google Drive in Jang's account |
| Creatomate template | Creatomate account in Jang's name |
| Blotato connections | Blotato account in Jang's name |
| Kie AI credits | Kie AI account in Jang's name |

### What to Hand Over to Jang

1. Tally form link (bookmark this — it is the only thing Jang touches)
2. Google Sheets tracker link
3. A one-page usage guide (how to fill the form, what happens next, how to read the Sheets)

### Ongoing Maintenance (Emmanuel — $150/month)

| Task | Frequency |
|---|---|
| Monitor Workflow 05 error alerts | Ongoing |
| Refresh Blotato OAuth tokens | Every 60 days |
| Update Claude script prompt if output quality degrades | As needed |
| Update Kie AI video prompts if visual quality shifts | As needed |
| Update Creatomate template for new brand assets | On request |
| Add new platforms (TikTok, YouTube Shorts) | Phase 2 — quoted separately |

---

*End of Build Spec — Jang AI Video Automation System v1.0*
*Built by Emmanuel Adekoya — 2026-07-19*

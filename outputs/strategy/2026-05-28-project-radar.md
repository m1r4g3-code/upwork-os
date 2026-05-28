# Project Radar -- Portfolio Build Priority
**Generated:** 2026-05-28  |  **Database:** 15 projects analyzed  |  **Showing:** 5

*Composite score: Market Demand 35% + Proof Power 30% + Uniqueness 20% + Time ROI 15%. Leverage bonus: +5 for existing repos.*

## Priority Summary

| Rank | Project | Score | Hours | Priority |
|------|---------|-------|-------|----------|
| 1 | Document Intelligence Extraction Pipeline | 93.0 | 12h | CRITICAL |
| 2 | Multi-Source Lead Qualification + Enrichment Pipeline | 86.5 | 12h | CRITICAL |
| 3 | AI Email Triage + Auto-Reply Agent | 85.5 | 10h | CRITICAL |
| 4 | Distill -- Production API Endpoint + Live Demo | 81.5 | 6h | CRITICAL |
| 5 | AI-Powered SaaS Customer Onboarding Sequence | 80.0 | 15h | CRITICAL |

---

## Recommended Build Sequence

**This Week -- Critical (highest portfolio ROI):**
- Document Intelligence Extraction Pipeline (12h) -- Document intelligence pipeline: extracts structured data from 500+ PDFs/day with 98%+ field accuracy
- Multi-Source Lead Qualification + Enrichment Pipeline (12h) -- AI lead qualification pipeline: scores and enriches 500 leads/day, surfaces top 5% automatically
- AI Email Triage + Auto-Reply Agent (10h) -- AI email triage agent: classifies, drafts, and routes 200+ emails/day -- zero manual sorting
- Distill -- Production API Endpoint + Live Demo (6h) -- Distill: production URL-to-JSON API for AI pipelines -- handles JS-rendered pages, live endpoint, free tier
- AI-Powered SaaS Customer Onboarding Sequence (15h) -- SaaS onboarding engine: Stripe payment triggers personalized activation sequence + churn risk detection, fully automated

---

# Detailed Specs

## 1. Document Intelligence Extraction Pipeline
**Priority:** CRITICAL -- Build This Week  |  **Score:** 93.0/100  |  **Build Time:** 12 hours
**New Repo:** `doc-intelligence-pipeline`
**Niche:** Ai Automation  |  **Target Clients:** medical practices, legal firms, logistics companies

**Signal Scores:**
  Market Demand   [########..] 8/10
  Proof Power     [##########] 10/10
  Uniqueness      [#########.] 9/10
  Time ROI        [########..] 8/10

**Client Pain:**
Teams manually extracting data from 50-500 documents per week. Errors, missing fields, hours of data entry. No audit trail.

**Upwork Portfolio Headline:**
> Document intelligence pipeline: extracts structured data from 500+ PDFs/day with 98%+ field accuracy

**Upwork Search Terms This Catches:**
`PDF data extraction automation`, `document parsing AI`, `OCR automation workflow`, `invoice extraction n8n`, `document processing pipeline`

**What To Build:**
- Trigger: email attachment watch, Google Drive folder monitor, or HTTP upload endpoint
- Classification: Claude identifies document type (invoice, intake form, report, ID)
- Extraction: Claude vision extracts fields per document type schema
- Validation: check required fields, flag low-confidence extractions for human review
- Schema enforcement: JSON schema validation before any database write
- Database write: Supabase with document type, all extracted fields, confidence score per field
- Review queue: uncertain extractions pushed to Slack/Notion for human correction
- README: before/after hours comparison, supported document types, accuracy notes, sample output

**60-Second Loom Script:**
- **Hook (0-5s):** A German medical company sent 400 patient intake forms last month. Manually: 3 days. This pipeline: 2 hours.
- **Problem (5-20s):** Show a folder of PDFs. 'These are documents your team processes by hand. Every field typed manually. Every mistake fixed manually. No audit trail.'
- **Solution (20-45s):** Drop a document into the trigger. Watch Claude classify it, extract fields, validate against schema. Show clean record appearing in Supabase.
- **Result (45-55s):** '400 documents. 2 hours. 98% field accuracy on validated document types.' Show the extraction log -- document, type, fields, confidence score.
- **CTA (55-60s):** If you are processing documents manually, I can build this pipeline for your document type. Message me with a sample document and I will scope it.

---

## 2. Multi-Source Lead Qualification + Enrichment Pipeline
**Priority:** CRITICAL -- Build This Week  |  **Score:** 86.5/100  |  **Build Time:** 12 hours
**New Repo:** `ai-lead-qualifier`
**Niche:** Ai Automation  |  **Target Clients:** SaaS companies, B2B sales teams, marketing agencies

**Signal Scores:**
  Market Demand   [#########.] 9/10
  Proof Power     [#########.] 9/10
  Uniqueness      [########..] 8/10
  Time ROI        [########..] 8/10

**Client Pain:**
Sales teams manually reviewing 200 leads/week to find the 10 worth calling. No scoring, no enrichment, no prioritization. Decision made by gut.

**Upwork Portfolio Headline:**
> AI lead qualification pipeline: scores and enriches 500 leads/day, surfaces top 5% automatically

**Upwork Search Terms This Catches:**
`lead qualification automation`, `CRM automation n8n`, `lead scoring AI`, `sales automation workflow`, `lead enrichment pipeline`

**What To Build:**
- Trigger: webhook (form submit), scheduled CSV import, or CRM webhook
- Data normalization: standardize fields across sources into unified schema
- Claude enrichment: infer company type, size signal, pain hypothesis from name + domain
- Scoring engine: 0-100 composite (fit signal, source quality, data completeness)
- Router: HIGH (Slack alert) / MEDIUM (CRM queue) / LOW (auto-archive)
- CRM write: Airtable or HubSpot with all enrichment fields appended
- Dashboard: Supabase view showing daily lead volume + score distribution
- README: architecture diagram, example payload, calibration guide for scoring weights

**60-Second Loom Script:**
- **Hook (0-5s):** Your sales team is spending 80% of their time on leads that were never going to close.
- **Problem (5-20s):** Show a spreadsheet of 200 raw leads. 'No scoring. No enrichment. Just names and emails. Someone has to touch all 200 to find the 10 worth calling.'
- **Solution (20-45s):** Walk through the n8n workflow. A lead enters. Claude enriches it -- infers company type, pain signal, fit score. Show the HIGH-score alert dropping into Slack.
- **Result (45-55s):** 'This system processed 500 leads this week. 23 flagged HIGH. Sales team only touched those 23.' Show the Supabase score distribution.
- **CTA (55-60s):** If your team is manually sorting leads, I can build this for your stack in 3 days. Message me with your current lead sources.

---

## 3. AI Email Triage + Auto-Reply Agent
**Priority:** CRITICAL -- Build This Week  |  **Score:** 85.5/100  |  **Build Time:** 10 hours
**New Repo:** `ai-email-agent`
**Niche:** Ai Automation  |  **Target Clients:** SaaS founders, digital agencies, ops teams

**Signal Scores:**
  Market Demand   [#########.] 9/10
  Proof Power     [##########] 10/10
  Uniqueness      [######....] 6/10
  Time ROI        [########..] 8/10

**Client Pain:**
Founders and ops teams spending 2-3 hours/day in email. Every reply typed by hand. Zero triage logic. The inbox is a queue with no manager.

**Upwork Portfolio Headline:**
> AI email triage agent: classifies, drafts, and routes 200+ emails/day -- zero manual sorting

**Upwork Search Terms This Catches:**
`email automation`, `n8n gmail`, `AI email reply`, `inbox zero automation`, `email workflow n8n`

**What To Build:**
- Gmail trigger: watch inbox, skip spam and newsletters
- Claude: classify intent (support / sales / admin / urgent) + extract key entities
- Router: branch by classification into separate sub-flows
- Claude: draft reply using full thread context + configurable company tone
- Human-in-loop: optional Slack approval before send (toggle per intent type)
- Logging: Supabase table with classification, draft, send status, response time
- README: demo GIF of inbox before/after, setup instructions, env var list

**60-Second Loom Script:**
- **Hook (0-5s):** Your inbox is a queue. Right now it is managed by your attention. This system manages it for you.
- **Problem (5-20s):** Open Gmail. Show 200+ unread emails. 'Every morning, someone on your team does this manually -- classification, routing, drafting replies. Pure cognitive overhead.'
- **Solution (20-45s):** Switch to n8n. Walk through the workflow live. Show Claude classifying an email in real time. Show the Slack approval step and the auto-send.
- **Result (45-55s):** 'This system processes 200+ emails/day. Drafts replies in the right tone. Routes urgent items before they get buried.' Show the Supabase log -- each row is an email handled.
- **CTA (55-60s):** If your team is still managing email by hand, message me. I build this in 2-3 days for any stack.

---

## 4. Distill -- Production API Endpoint + Live Demo
**Priority:** CRITICAL -- Build This Week  |  **Score:** 81.5/100  |  **Build Time:** 6 hours
**New Repo:** `distill`
**Niche:** Ai Automation  |  **Target Clients:** AI developers, data engineering teams, research automation teams

**Signal Scores:**
  Market Demand   [#######...] 7/10
  Proof Power     [#######...] 7/10
  Uniqueness      [########..] 8/10
  Time ROI        [##########] 10/10

**Client Pain:**
Developers integrating web content into AI pipelines need reliable URL extraction that handles JavaScript-rendered pages. Building this from scratch takes days and breaks constantly.

**Upwork Portfolio Headline:**
> Distill: production URL-to-JSON API for AI pipelines -- handles JS-rendered pages, live endpoint, free tier

**Upwork Search Terms This Catches:**
`web scraping API Python`, `content extraction API`, `URL to markdown AI pipeline`, `web content scraper FastAPI`, `Playwright scraper API`

**What To Build:**
- FastAPI wrapper: POST /extract, GET /health, GET /docs (auto-generated Swagger)
- Input: URL + optional options (include_images, max_words)
- Output: {title, content, metadata, word_count, extracted_at, source_url}
- Error handling: 404, paywall detected, JS timeout, rate limit -- all structured JSON errors
- Rate limiting: slowapi middleware, 10 req/min free tier
- Deploy: Railway free tier, add custom subdomain if available
- Demo page: simple HTML at root -- paste URL, see JSON output instantly
- README: update with live API URL, cURL examples, use cases, response schema

**60-Second Loom Script:**
- **Hook (0-5s):** If you are building AI pipelines that process web content, you need this. I already built it.
- **Problem (5-20s):** Show the problem: manually copying article text into a prompt. 'Every AI developer deals with this. Feeding URLs into AI pipelines is messier than it should be.'
- **Solution (20-45s):** Show the live API endpoint. POST a URL. JSON comes back -- clean title, clean content, metadata. Show it working on a JS-rendered page.
- **Result (45-55s):** 'Production API. Free tier. Handles JS rendering. I use it in my own n8n workflows.' Show the demo site.
- **CTA (55-60s):** It is live. Free tier available. If you need a custom version with specific output format or auth, message me.

---

## 5. AI-Powered SaaS Customer Onboarding Sequence
**Priority:** CRITICAL -- Build This Week  |  **Score:** 80.0/100  |  **Build Time:** 15 hours
**New Repo:** `saas-onboarding-engine`
**Niche:** Ai Automation  |  **Target Clients:** SaaS founders, indie hackers, product-led growth teams

**Signal Scores:**
  Market Demand   [########..] 8/10
  Proof Power     [#########.] 9/10
  Uniqueness      [########..] 8/10
  Time ROI        [######....] 6/10

**Client Pain:**
SaaS founders manually chasing new users to activate. Month-1 churn spikes because onboarding is generic or nonexistent. No visibility into who is stuck.

**Upwork Portfolio Headline:**
> SaaS onboarding engine: Stripe payment triggers personalized activation sequence + churn risk detection, fully automated

**Upwork Search Terms This Catches:**
`SaaS onboarding automation`, `customer activation workflow`, `Stripe automation n8n`, `churn prevention automation`, `user onboarding sequence`

**What To Build:**
- Trigger: Stripe webhook on payment success
- Segmentation: Claude infers use case from signup data (job title, company size, referral source)
- Onboarding sequence: personalized email series (Day 0, Day 3, Day 7) per segment
- Milestone tracking: webhook listeners for key activation events (first login, feature used)
- Churn risk detection: flag users who have not hit milestone by Day N
- Re-engagement: automated personal-feel email for at-risk users (founder voice)
- Dashboard: Supabase cohort view showing activation rates by segment and week
- README: architecture diagram, Stripe webhook setup guide, segment customization format

**60-Second Loom Script:**
- **Hook (0-5s):** You worked hard to get that paying customer. Then you sent them a generic welcome email and hoped for the best.
- **Problem (5-20s):** Show a Stripe dashboard with a new payment. Then show a generic 'Welcome to [Product]!' email. 'Month-1 churn is 40%+ for products with onboarding like this.'
- **Solution (20-45s):** Stripe webhook fires. Claude segments the user. Show the personalized Day 0 email -- specific to their use case. Show the activation milestone tracker.
- **Result (45-55s):** 'Personalized sequence. Automatic churn detection. Every new user gets the right next step, not a blast email.' Show the cohort dashboard.
- **CTA (55-60s):** If you are running a SaaS and onboarding is still manual or generic, I can build this in 3-4 days. Message me.

---

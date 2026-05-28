#!/usr/bin/env python3
"""
project_radar.py -- Strategic Portfolio Project Recommender

Analyzes current portfolio vs. Upwork market demand and recommends
specific projects to build that attract real clients.

Usage:
    python scripts/project_radar.py                     # full radar
    python scripts/project_radar.py --top 5             # top 5 only
    python scripts/project_radar.py --niche automation  # filter by niche
    python scripts/project_radar.py --niche fullstack   # filter by niche
    python scripts/project_radar.py --max-hours 12      # filter by build time
    python scripts/project_radar.py --json              # JSON output
    python scripts/project_radar.py --no-save           # print only

Output: outputs/strategy/YYYY-MM-DD-project-radar.md
"""

import sys
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "hephzibah-brain-temp"
OUTPUTS = ROOT / "outputs" / "strategy"
IDENTITY_MD = BRAIN / "me" / "identity.md"


# ---------------------------------------------------------------------------
# Project database -- researched against Upwork demand, Emmanuel's stack,
# and market gaps as of 2025/2026.
# Fields:
#   demand_score    1-10: how frequently clients search for this on Upwork
#   uniqueness      1-10: differentiation vs. other freelancer portfolios
#   proof_power     1-10: how much this closes real client deals
#   build_hours     int:  realistic time to build a demo-ready version
#   leverage_existing bool: builds on or enhances an existing repo
# ---------------------------------------------------------------------------
PROJECT_DB = [
    {
        "id": "email-triage-agent",
        "title": "AI Email Triage + Auto-Reply Agent",
        "description": (
            "n8n workflow that watches a Gmail inbox, classifies emails by intent "
            "using Claude, drafts context-aware replies for review, and routes urgent "
            "items to Slack."
        ),
        "client_pain": (
            "Founders and ops teams spending 2-3 hours/day in email. Every reply "
            "typed by hand. Zero triage logic. The inbox is a queue with no manager."
        ),
        "stack": ["n8n", "claude-api", "gmail-api", "slack"],
        "niche": "ai-automation",
        "client_types": ["SaaS founders", "digital agencies", "ops teams"],
        "demand_score": 9,
        "uniqueness_score": 6,
        "proof_power": 10,
        "build_hours": 10,
        "github_repo_name": "ai-email-agent",
        "portfolio_headline": (
            "AI email triage agent: classifies, drafts, and routes 200+ emails/day -- zero manual sorting"
        ),
        "upwork_search_terms": [
            "email automation", "n8n gmail", "AI email reply",
            "inbox zero automation", "email workflow n8n"
        ],
        "build_spec": [
            "Gmail trigger: watch inbox, skip spam and newsletters",
            "Claude: classify intent (support / sales / admin / urgent) + extract key entities",
            "Router: branch by classification into separate sub-flows",
            "Claude: draft reply using full thread context + configurable company tone",
            "Human-in-loop: optional Slack approval before send (toggle per intent type)",
            "Logging: Supabase table with classification, draft, send status, response time",
            "README: demo GIF of inbox before/after, setup instructions, env var list"
        ],
        "loom_script": {
            "hook": "Your inbox is a queue. Right now it is managed by your attention. This system manages it for you.",
            "problem": (
                "Open Gmail. Show 200+ unread emails. 'Every morning, someone on your team "
                "does this manually -- classification, routing, drafting replies. Pure cognitive overhead.'"
            ),
            "solution": (
                "Switch to n8n. Walk through the workflow live. Show Claude classifying "
                "an email in real time. Show the Slack approval step and the auto-send."
            ),
            "result": (
                "'This system processes 200+ emails/day. Drafts replies in the right tone. "
                "Routes urgent items before they get buried.' Show the Supabase log -- "
                "each row is an email handled."
            ),
            "cta": (
                "If your team is still managing email by hand, message me. "
                "I build this in 2-3 days for any stack."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "lead-qualification-pipeline",
        "title": "Multi-Source Lead Qualification + Enrichment Pipeline",
        "description": (
            "n8n workflow that ingests leads from multiple sources (web form, CSV, CRM), "
            "enriches them via Claude (inferred company size, pain signal, fit score), "
            "scores 1-100, and writes to CRM with Slack alert on high-value leads."
        ),
        "client_pain": (
            "Sales teams manually reviewing 200 leads/week to find the 10 worth calling. "
            "No scoring, no enrichment, no prioritization. Decision made by gut."
        ),
        "stack": ["n8n", "claude-api", "supabase", "slack", "airtable"],
        "niche": "ai-automation",
        "client_types": ["SaaS companies", "B2B sales teams", "marketing agencies"],
        "demand_score": 9,
        "uniqueness_score": 8,
        "proof_power": 9,
        "build_hours": 12,
        "github_repo_name": "ai-lead-qualifier",
        "portfolio_headline": (
            "AI lead qualification pipeline: scores and enriches 500 leads/day, surfaces top 5% automatically"
        ),
        "upwork_search_terms": [
            "lead qualification automation", "CRM automation n8n",
            "lead scoring AI", "sales automation workflow", "lead enrichment pipeline"
        ],
        "build_spec": [
            "Trigger: webhook (form submit), scheduled CSV import, or CRM webhook",
            "Data normalization: standardize fields across sources into unified schema",
            "Claude enrichment: infer company type, size signal, pain hypothesis from name + domain",
            "Scoring engine: 0-100 composite (fit signal, source quality, data completeness)",
            "Router: HIGH (Slack alert) / MEDIUM (CRM queue) / LOW (auto-archive)",
            "CRM write: Airtable or HubSpot with all enrichment fields appended",
            "Dashboard: Supabase view showing daily lead volume + score distribution",
            "README: architecture diagram, example payload, calibration guide for scoring weights"
        ],
        "loom_script": {
            "hook": "Your sales team is spending 80% of their time on leads that were never going to close.",
            "problem": (
                "Show a spreadsheet of 200 raw leads. 'No scoring. No enrichment. Just names "
                "and emails. Someone has to touch all 200 to find the 10 worth calling.'"
            ),
            "solution": (
                "Walk through the n8n workflow. A lead enters. Claude enriches it -- "
                "infers company type, pain signal, fit score. Show the HIGH-score alert "
                "dropping into Slack."
            ),
            "result": (
                "'This system processed 500 leads this week. 23 flagged HIGH. "
                "Sales team only touched those 23.' Show the Supabase score distribution."
            ),
            "cta": (
                "If your team is manually sorting leads, I can build this for your stack in 3 days. "
                "Message me with your current lead sources."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "document-intelligence-pipeline",
        "title": "Document Intelligence Extraction Pipeline",
        "description": (
            "Automated pipeline that ingests PDFs, images, or scanned documents, "
            "extracts structured data using Claude vision + OCR, validates against "
            "schema, and writes clean records to database. Built from real medical records work."
        ),
        "client_pain": (
            "Teams manually extracting data from 50-500 documents per week. "
            "Errors, missing fields, hours of data entry. No audit trail."
        ),
        "stack": ["n8n", "claude-api", "supabase", "python"],
        "niche": "ai-automation",
        "client_types": ["medical practices", "legal firms", "logistics companies", "insurance teams"],
        "demand_score": 8,
        "uniqueness_score": 9,
        "proof_power": 10,
        "build_hours": 12,
        "github_repo_name": "doc-intelligence-pipeline",
        "portfolio_headline": (
            "Document intelligence pipeline: extracts structured data from 500+ PDFs/day with 98%+ field accuracy"
        ),
        "upwork_search_terms": [
            "PDF data extraction automation", "document parsing AI",
            "OCR automation workflow", "invoice extraction n8n", "document processing pipeline"
        ],
        "build_spec": [
            "Trigger: email attachment watch, Google Drive folder monitor, or HTTP upload endpoint",
            "Classification: Claude identifies document type (invoice, intake form, report, ID)",
            "Extraction: Claude vision extracts fields per document type schema",
            "Validation: check required fields, flag low-confidence extractions for human review",
            "Schema enforcement: JSON schema validation before any database write",
            "Database write: Supabase with document type, all extracted fields, confidence score per field",
            "Review queue: uncertain extractions pushed to Slack/Notion for human correction",
            "README: before/after hours comparison, supported document types, accuracy notes, sample output"
        ],
        "loom_script": {
            "hook": (
                "A German medical company sent 400 patient intake forms last month. "
                "Manually: 3 days. This pipeline: 2 hours."
            ),
            "problem": (
                "Show a folder of PDFs. 'These are documents your team processes by hand. "
                "Every field typed manually. Every mistake fixed manually. No audit trail.'"
            ),
            "solution": (
                "Drop a document into the trigger. Watch Claude classify it, extract "
                "fields, validate against schema. Show clean record appearing in Supabase."
            ),
            "result": (
                "'400 documents. 2 hours. 98% field accuracy on validated document types.' "
                "Show the extraction log -- document, type, fields, confidence score."
            ),
            "cta": (
                "If you are processing documents manually, I can build this pipeline for "
                "your document type. Message me with a sample document and I will scope it."
            )
        },
        "leverage_existing": True
    },
    {
        "id": "agency-report-automation",
        "title": "Automated Agency Client Report Generator",
        "description": (
            "n8n + Claude pipeline that pulls data from GA4, Meta Ads, and Google Ads weekly, "
            "generates narrative-quality written commentary, and publishes a branded "
            "Notion or PDF report per client -- automatically."
        ),
        "client_pain": (
            "Agencies manually compiling monthly reports for 10-50 clients. "
            "Copy-pasting numbers, writing commentary, formatting PDFs. "
            "40+ hours/month per account manager."
        ),
        "stack": ["n8n", "claude-api", "ga4-api", "google-ads-api", "notion"],
        "niche": "ai-automation",
        "client_types": ["digital marketing agencies", "performance agencies", "SEO firms"],
        "demand_score": 9,
        "uniqueness_score": 7,
        "proof_power": 8,
        "build_hours": 14,
        "github_repo_name": "agency-report-automator",
        "portfolio_headline": (
            "Automated client reporting: GA4 + Meta Ads data to branded narrative report, "
            "published weekly without human involvement"
        ),
        "upwork_search_terms": [
            "agency reporting automation", "GA4 automated reports",
            "marketing report generator n8n", "client reporting workflow",
            "automated analytics report"
        ],
        "build_spec": [
            "Trigger: weekly schedule (e.g. Monday 7am), one run per client config",
            "Data fetch: GA4 API (sessions, conversions, revenue) + Meta Ads API (spend, ROAS, CPL)",
            "Delta calculation: week-over-week and month-over-month comparisons, anomaly flagging",
            "Claude narrative: written commentary -- what changed, why it likely changed, what to watch",
            "Template fill: populate branded Notion page or PDF template with data + narrative",
            "Distribution: email PDF or update shared Notion workspace per client",
            "Multi-client loop: client config YAML lists all accounts, runs per account",
            "README: sample output screenshot, API credential setup, client config format"
        ],
        "loom_script": {
            "hook": (
                "This is Monday morning for a 20-client agency without this system: "
                "8 hours of copy-pasting analytics into report templates."
            ),
            "problem": (
                "Show a blank report template. 'Each of these fields: manual. "
                "Each comment: written from scratch. For every client. Every week.'"
            ),
            "solution": (
                "Show the n8n workflow. Trigger fires. GA4 data comes in. "
                "Claude writes the commentary -- specific, context-aware. "
                "Report populates. Email sends."
            ),
            "result": (
                "'20 client reports. Generated while the account manager was sleeping. "
                "Branded, narrative-quality, ready to send.' Show the Notion database -- all done."
            ),
            "cta": (
                "If you are running an agency and spending days on reports, "
                "I can build this for your stack. 3-4 days. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "whatsapp-ai-agent",
        "title": "WhatsApp AI Support + FAQ Agent",
        "description": (
            "Business WhatsApp integration that handles inbound customer messages, "
            "answers FAQs using Claude with a custom knowledge base, escalates complex "
            "issues to human agents, and logs all conversations."
        ),
        "client_pain": (
            "Small and mid-size businesses getting 100+ WhatsApp messages/day. "
            "One person handling all of them manually. Response time: hours. "
            "After hours: nothing."
        ),
        "stack": ["n8n", "claude-api", "whatsapp-business-api", "supabase"],
        "niche": "ai-automation",
        "client_types": ["e-commerce businesses", "service businesses", "African + LATAM SMBs"],
        "demand_score": 8,
        "uniqueness_score": 8,
        "proof_power": 8,
        "build_hours": 15,
        "github_repo_name": "whatsapp-ai-agent",
        "portfolio_headline": (
            "WhatsApp AI agent: handles 100+ customer messages/day, "
            "responds in seconds, escalates complex cases automatically"
        ),
        "upwork_search_terms": [
            "WhatsApp automation", "WhatsApp chatbot n8n",
            "WhatsApp business API integration", "WhatsApp AI assistant",
            "customer support automation WhatsApp"
        ],
        "build_spec": [
            "Webhook: receive WhatsApp messages via Meta Cloud API",
            "Intent classification: Claude identifies type (FAQ / order status / complaint / escalate)",
            "Knowledge base: load business FAQ + product info from Supabase at runtime",
            "Response generation: Claude answers using knowledge base context + conversation history",
            "Escalation: tag unresolved issues, notify human agent via Slack with full thread",
            "Thread tracking: maintain conversation history per customer number in Supabase",
            "After-hours mode: different response template outside configured business hours",
            "README: Meta Cloud API setup guide, conversation flow diagram, known limitations"
        ],
        "loom_script": {
            "hook": (
                "Most businesses in Lagos, Nairobi, or Sao Paulo run customer support "
                "through one WhatsApp number. This is that number on autopilot."
            ),
            "problem": (
                "Show a WhatsApp screen with 200+ unread messages. 'One person. "
                "200 messages. Business hours only. That is the current state.'"
            ),
            "solution": (
                "Send a test message. Watch the agent reply in seconds. Walk through "
                "Claude reading the knowledge base, generating a context-aware response. "
                "Show the escalation path when the question is complex."
            ),
            "result": (
                "'Handles 100+ messages/day. Responds in under 5 seconds. "
                "Only escalates the 10% that need a human.' Show the conversation log."
            ),
            "cta": (
                "If you are managing a WhatsApp line manually, I can build this agent "
                "for your business in 3-4 days. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "saas-onboarding-engine",
        "title": "AI-Powered SaaS Customer Onboarding Sequence",
        "description": (
            "Automated onboarding workflow triggered by Stripe payment: sends "
            "personalized welcome sequence by user segment, tracks activation milestones, "
            "detects churn risk (inactive users), and triggers re-engagement automatically."
        ),
        "client_pain": (
            "SaaS founders manually chasing new users to activate. "
            "Month-1 churn spikes because onboarding is generic or nonexistent. "
            "No visibility into who is stuck."
        ),
        "stack": ["n8n", "claude-api", "stripe", "supabase", "sendgrid"],
        "niche": "ai-automation",
        "client_types": ["SaaS founders", "indie hackers", "product-led growth teams"],
        "demand_score": 8,
        "uniqueness_score": 8,
        "proof_power": 9,
        "build_hours": 15,
        "github_repo_name": "saas-onboarding-engine",
        "portfolio_headline": (
            "SaaS onboarding engine: Stripe payment triggers personalized activation "
            "sequence + churn risk detection, fully automated"
        ),
        "upwork_search_terms": [
            "SaaS onboarding automation", "customer activation workflow",
            "Stripe automation n8n", "churn prevention automation",
            "user onboarding sequence"
        ],
        "build_spec": [
            "Trigger: Stripe webhook on payment success",
            "Segmentation: Claude infers use case from signup data (job title, company size, referral source)",
            "Onboarding sequence: personalized email series (Day 0, Day 3, Day 7) per segment",
            "Milestone tracking: webhook listeners for key activation events (first login, feature used)",
            "Churn risk detection: flag users who have not hit milestone by Day N",
            "Re-engagement: automated personal-feel email for at-risk users (founder voice)",
            "Dashboard: Supabase cohort view showing activation rates by segment and week",
            "README: architecture diagram, Stripe webhook setup guide, segment customization format"
        ],
        "loom_script": {
            "hook": (
                "You worked hard to get that paying customer. "
                "Then you sent them a generic welcome email and hoped for the best."
            ),
            "problem": (
                "Show a Stripe dashboard with a new payment. Then show a generic "
                "'Welcome to [Product]!' email. 'Month-1 churn is 40%+ for products "
                "with onboarding like this.'"
            ),
            "solution": (
                "Stripe webhook fires. Claude segments the user. Show the personalized "
                "Day 0 email -- specific to their use case. Show the activation milestone tracker."
            ),
            "result": (
                "'Personalized sequence. Automatic churn detection. Every new user "
                "gets the right next step, not a blast email.' Show the cohort dashboard."
            ),
            "cta": (
                "If you are running a SaaS and onboarding is still manual or generic, "
                "I can build this in 3-4 days. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "content-repurposing-pipeline",
        "title": "Content Repurposing + Multi-Channel Publishing Pipeline",
        "description": (
            "n8n pipeline that takes a blog post or long-form content and uses Claude "
            "to generate platform-specific versions: Twitter thread, LinkedIn post, "
            "short-form video script, email newsletter. Publishes or queues to each channel."
        ),
        "client_pain": (
            "Content teams publishing 4 blog posts/month and getting minimal reach "
            "because they lack bandwidth to repurpose for every channel. "
            "One piece of content should do the work of five."
        ),
        "stack": ["n8n", "claude-api", "twitter-api", "linkedin-api", "wordpress"],
        "niche": "ai-automation",
        "client_types": ["content agencies", "SaaS marketing teams", "newsletter creators"],
        "demand_score": 8,
        "uniqueness_score": 6,
        "proof_power": 7,
        "build_hours": 10,
        "github_repo_name": "content-repurposer",
        "portfolio_headline": (
            "Content repurposing pipeline: one blog post to Twitter thread + "
            "LinkedIn post + newsletter, published automatically"
        ),
        "upwork_search_terms": [
            "content repurposing automation", "social media automation n8n",
            "blog to social media workflow", "content distribution pipeline",
            "AI content repurposing"
        ],
        "build_spec": [
            "Trigger: new WordPress post via RSS, or manual URL input via webhook",
            "Content fetch: extract full article text, title, key points",
            "Claude: generate Twitter thread (8-12 tweets, hook + value + CTA format)",
            "Claude: generate LinkedIn post (professional tone, 300-400 words, relevant hashtags)",
            "Claude: generate email newsletter section (conversational, 150 words)",
            "Claude: generate short-form video script (60-90 sec, hook-body-CTA structure)",
            "Publishing: queue to Buffer or Typefully for Twitter, schedule LinkedIn, add to ConvertKit",
            "README: example input/output side by side, platform credential setup, tone config guide"
        ],
        "loom_script": {
            "hook": "One piece of content. Five channels. In 90 seconds. Not five different writers.",
            "problem": (
                "Show a blog post. 'To get maximum reach, you need a Twitter thread, "
                "a LinkedIn post, an email, and a video script. Most teams skip 4 of "
                "those because they do not have time.'"
            ),
            "solution": (
                "Paste the URL. Watch n8n fetch the article, Claude process it into "
                "4 formats. Show each output side by side -- all platform-native, all ready."
            ),
            "result": (
                "'Blog post published at 9am. Twitter thread, LinkedIn, and newsletter "
                "queued by 9:01am. Automatically.' Show the publishing queue."
            ),
            "cta": (
                "If you are leaving distribution ROI on the table because you cannot "
                "repurpose at scale, message me. I can build this in 2 days."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "vapi-voice-agent",
        "title": "AI Voice Agent for Inbound Business Calls",
        "description": (
            "VAPI-powered phone agent that handles inbound calls, qualifies callers "
            "by asking structured questions, books appointments via calendar API, "
            "and sends summary to CRM. Sounds human. Available 24/7."
        ),
        "client_pain": (
            "Service businesses missing calls after hours. Front desk staff spending "
            "40% of time on routine qualification calls. Voicemails never returned."
        ),
        "stack": ["vapi", "claude-api", "n8n", "cal-com", "supabase", "twilio"],
        "niche": "ai-automation",
        "client_types": ["medical practices", "law firms", "real estate agencies", "home services"],
        "demand_score": 8,
        "uniqueness_score": 9,
        "proof_power": 9,
        "build_hours": 18,
        "github_repo_name": "vapi-inbound-agent",
        "portfolio_headline": (
            "AI voice agent: handles inbound calls 24/7, qualifies leads, "
            "books appointments -- zero human involvement"
        ),
        "upwork_search_terms": [
            "VAPI voice agent", "AI phone agent", "voice AI appointment booking",
            "inbound call automation", "AI receptionist Twilio"
        ],
        "build_spec": [
            "VAPI setup: configure inbound phone number, select voice model",
            "Conversation flow: Claude-powered dynamic script with qualification questions and objection handling",
            "Appointment booking: Cal.com API -- check availability and book slot in real time during call",
            "CRM write: n8n webhook on call end to write summary, transcript, qualification score to Supabase",
            "Escalation: detect urgency phrases, transfer to human immediately",
            "Post-call: send confirmation SMS to caller via Twilio",
            "Analytics: call volume, qualification rate, booking rate in Supabase dashboard",
            "README: VAPI account setup, phone number provisioning, sample conversation transcript"
        ],
        "loom_script": {
            "hook": "This phone number has no human behind it. It booked 4 appointments this morning.",
            "problem": (
                "Show a call log from a service business. '40% of calls go to voicemail. "
                "30% are routine questions the front desk answers identically every time.'"
            ),
            "solution": (
                "Call the demo number. Walk through the live conversation -- "
                "the agent introduces itself, asks qualification questions, "
                "checks calendar availability, confirms the booking."
            ),
            "result": (
                "'Available 24/7. Never misses a call. Qualifies, books, confirms. "
                "4 appointments booked while you watched this video.' "
                "Show the Cal.com booking log."
            ),
            "cta": (
                "If you are a service business missing calls or paying staff to answer "
                "routine ones, I can build this for your use case. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "distill-api-endpoint",
        "title": "Distill -- Production API Endpoint + Live Demo",
        "description": (
            "Enhance the existing Distill repo (URL-to-JSON for AI pipelines) with a "
            "FastAPI wrapper, proper error handling, rate limiting, and a hosted demo. "
            "Deploy to Railway. Converts an existing tool into a portfolio centrepiece."
        ),
        "client_pain": (
            "Developers integrating web content into AI pipelines need reliable URL "
            "extraction that handles JavaScript-rendered pages. Building this from "
            "scratch takes days and breaks constantly."
        ),
        "stack": ["python", "fastapi", "playwright", "railway"],
        "niche": "ai-automation",
        "client_types": ["AI developers", "data engineering teams", "research automation teams"],
        "demand_score": 7,
        "uniqueness_score": 8,
        "proof_power": 7,
        "build_hours": 6,
        "github_repo_name": "distill",
        "portfolio_headline": (
            "Distill: production URL-to-JSON API for AI pipelines -- "
            "handles JS-rendered pages, live endpoint, free tier"
        ),
        "upwork_search_terms": [
            "web scraping API Python", "content extraction API",
            "URL to markdown AI pipeline", "web content scraper FastAPI",
            "Playwright scraper API"
        ],
        "build_spec": [
            "FastAPI wrapper: POST /extract, GET /health, GET /docs (auto-generated Swagger)",
            "Input: URL + optional options (include_images, max_words)",
            "Output: {title, content, metadata, word_count, extracted_at, source_url}",
            "Error handling: 404, paywall detected, JS timeout, rate limit -- all structured JSON errors",
            "Rate limiting: slowapi middleware, 10 req/min free tier",
            "Deploy: Railway free tier, add custom subdomain if available",
            "Demo page: simple HTML at root -- paste URL, see JSON output instantly",
            "README: update with live API URL, cURL examples, use cases, response schema"
        ],
        "loom_script": {
            "hook": "If you are building AI pipelines that process web content, you need this. I already built it.",
            "problem": (
                "Show the problem: manually copying article text into a prompt. "
                "'Every AI developer deals with this. Feeding URLs into AI pipelines "
                "is messier than it should be.'"
            ),
            "solution": (
                "Show the live API endpoint. POST a URL. JSON comes back -- "
                "clean title, clean content, metadata. Show it working on a "
                "JS-rendered page."
            ),
            "result": (
                "'Production API. Free tier. Handles JS rendering. "
                "I use it in my own n8n workflows.' Show the demo site."
            ),
            "cta": (
                "It is live. Free tier available. If you need a custom version "
                "with specific output format or auth, message me."
            )
        },
        "leverage_existing": True
    },
    {
        "id": "automated-invoice-ar",
        "title": "Automated Invoice + Accounts Receivable Follow-up Agent",
        "description": (
            "n8n + Claude pipeline that generates professional invoices from project "
            "data, tracks payment status via Stripe, and sends progressively firmer "
            "follow-up emails for overdue payments -- automatically."
        ),
        "client_pain": (
            "Freelancers and small businesses chasing late payments manually. "
            "Awkward follow-up emails delayed out of discomfort. "
            "Average payment delay: 30+ days past due."
        ),
        "stack": ["n8n", "claude-api", "stripe", "sendgrid"],
        "niche": "ai-automation",
        "client_types": ["freelancers", "agencies", "service businesses", "small businesses"],
        "demand_score": 7,
        "uniqueness_score": 8,
        "proof_power": 8,
        "build_hours": 12,
        "github_repo_name": "ar-follow-up-agent",
        "portfolio_headline": (
            "Automated AR agent: tracks invoices, sends escalating follow-ups, "
            "recovers overdue payments without manual intervention"
        ),
        "upwork_search_terms": [
            "invoice automation n8n", "accounts receivable automation",
            "payment follow-up workflow", "billing automation",
            "invoice reminder system"
        ],
        "build_spec": [
            "Invoice generation: template fill from project data, PDF export via WeasyPrint",
            "Payment tracking: Stripe webhook on payment, fallback poll for manual payments",
            "Follow-up schedule: Day 0 (invoice), Day +1 (friendly reminder), Day +7 (professional nudge), Day +14 (firm notice)",
            "Claude tone calibration: warmer early emails, firmer as days outstanding increases",
            "Escalation flag: owner notification when invoice is 30+ days overdue + suggested next step",
            "Dashboard: Supabase view showing outstanding, overdue, paid with days outstanding column",
            "README: Stripe webhook setup, customizable follow-up schedule, tone examples side by side"
        ],
        "loom_script": {
            "hook": "Chasing invoices is the most uncomfortable part of running a business. This system does it for you.",
            "problem": (
                "Show an overdue invoice. 'It has been 14 days. You need to follow up. "
                "But you do not want to seem aggressive. So you delay. And it gets later.'"
            ),
            "solution": (
                "Show the n8n workflow. Invoice sent. Day 7 auto-email fires -- "
                "friendly, professional. Day 14 email -- firmer. "
                "Claude calibrates the tone based on days overdue."
            ),
            "result": (
                "'Average overdue invoice resolved in 11 days instead of 34 days. "
                "No awkward conversations.' Show the dashboard."
            ),
            "cta": (
                "If you are managing invoices manually and chasing payments by hand, "
                "I can build this for your billing stack. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "n8n-public-template",
        "title": "Published n8n Community Workflow Template",
        "description": (
            "Build and publish a polished, well-documented n8n workflow template to the "
            "official n8n community. Drives Upwork invites via platform-algorithm recognition "
            "of n8n expertise. High signal-to-effort ratio."
        ),
        "client_pain": (
            "n8n users searching for pre-built templates find low-quality, undocumented, "
            "abandoned workflows. A polished template with clear documentation gets "
            "downloaded and starred repeatedly."
        ),
        "stack": ["n8n"],
        "niche": "ai-automation",
        "client_types": ["n8n users", "automation freelancers", "operations teams"],
        "demand_score": 7,
        "uniqueness_score": 7,
        "proof_power": 6,
        "build_hours": 6,
        "github_repo_name": "n8n-templates",
        "portfolio_headline": (
            "Published n8n community templates -- downloaded and verified by n8n team"
        ),
        "upwork_search_terms": [
            "n8n workflow automation", "n8n expert", "n8n consultant",
            "n8n template", "n8n custom workflow"
        ],
        "build_spec": [
            "Choose use case: email triage or lead qualification (highest community download counts)",
            "Clean build: no hardcoded credentials, clear node naming, logical grouping with sticky notes",
            "Write description: 300-word use case explanation, prerequisites, step-by-step setup",
            "Add sticky notes inside workflow explaining each major section",
            "Publish to n8n community (community.n8n.io -- Share Workflows section)",
            "Add 'Published on n8n community' badge and link to GitHub README",
            "Track downloads and stars -- add to Upwork portfolio as social proof metric",
            "LinkedIn post: announce the template, link to community page"
        ],
        "loom_script": {
            "hook": "n8n has 80,000+ users. This workflow template has been downloaded by hundreds of them.",
            "problem": (
                "Show n8n community. 'Most templates here are half-finished, "
                "undocumented, abandoned. Users waste hours adapting them.'"
            ),
            "solution": (
                "Open the published template. Walk through the clean structure, "
                "the sticky note explanations, the setup guide. "
                "'This is what a production-ready workflow looks like.'"
            ),
            "result": (
                "'Hundreds of downloads. Verified by the n8n team. "
                "Users in 12 countries.' Show the community listing."
            ),
            "cta": (
                "If you need a custom n8n workflow built to this standard, "
                "message me. This is what I ship."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "saas-admin-dashboard",
        "title": "SaaS Admin Dashboard MVP Starter",
        "description": (
            "Production-ready Next.js + Supabase admin dashboard with auth, user management, "
            "usage metrics, and Stripe subscription handling. Deployed on Vercel. "
            "Demonstrates full-stack + AI integration for SaaS clients."
        ),
        "client_pain": (
            "SaaS founders building MVPs need an admin panel: user list, billing management, "
            "usage graphs. Building from scratch takes 2-3 weeks. "
            "This gives them a working base in 2-3 days."
        ),
        "stack": ["nextjs", "supabase", "stripe", "tailwind", "typescript"],
        "niche": "fullstack",
        "client_types": ["SaaS founders", "startup CTOs", "indie hackers"],
        "demand_score": 9,
        "uniqueness_score": 5,
        "proof_power": 8,
        "build_hours": 25,
        "github_repo_name": "saas-dashboard-starter",
        "portfolio_headline": (
            "Production SaaS admin dashboard: Next.js + Supabase + Stripe -- "
            "auth, user management, billing, metrics. Deploy in hours."
        ),
        "upwork_search_terms": [
            "Next.js dashboard development", "SaaS admin panel React",
            "Next.js Supabase Stripe", "SaaS MVP development",
            "admin dashboard TypeScript"
        ],
        "build_spec": [
            "Auth: Supabase Auth with email/password + Google OAuth",
            "User management: list, search, role assignment, ban, activity log",
            "Billing: Stripe Customer Portal integration, subscription status, invoice history",
            "Metrics: DAU chart, MRR graph, feature usage heatmap (seeded with demo data)",
            "Feature flags: simple boolean toggles per user or plan tier",
            "Dark mode: system default with manual toggle",
            "Mobile responsive: all pages functional on mobile",
            "Deploy: Vercel one-click, Supabase project setup script included",
            "README: full setup guide, env var list, DB migration instructions, Stripe webhook config"
        ],
        "loom_script": {
            "hook": "Every SaaS needs an admin panel. Most founders build it twice -- once badly, once properly after launch.",
            "problem": (
                "Show a SaaS without an admin panel. 'User reports a billing issue. "
                "You go to Stripe, find the customer, fix it manually. "
                "That is 20 minutes every time.'"
            ),
            "solution": (
                "Walk through the dashboard. User management with search. "
                "Stripe billing tab. Metrics page. Feature flags. Mobile view."
            ),
            "result": (
                "'Built in 3 days. Deployed on Vercel. Handles auth, "
                "billing, and user management in one place.' Show the live URL."
            ),
            "cta": (
                "If you are building a SaaS and need an admin panel "
                "production-ready from day one, message me. "
                "I can adapt this to your stack in under a week."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "ai-scope-analyzer",
        "title": "AI Contract + Scope Ambiguity Analyzer",
        "description": (
            "Tool that analyzes project briefs, contracts, or SOWs using Claude and "
            "flags scope ambiguity, missing deliverables, unclear timelines, and risk clauses. "
            "Outputs a structured risk report with suggested contract additions."
        ),
        "client_pain": (
            "Freelancers and agencies signing contracts with hidden scope traps. "
            "Discovering 6 weeks in that 'other duties as required' meant "
            "something very specific to the client."
        ),
        "stack": ["n8n", "claude-api", "python", "fastapi"],
        "niche": "ai-automation",
        "client_types": ["freelancers", "agencies", "consultants", "legal tech teams"],
        "demand_score": 6,
        "uniqueness_score": 10,
        "proof_power": 8,
        "build_hours": 12,
        "github_repo_name": "scope-analyzer",
        "portfolio_headline": (
            "AI scope analyzer: flags contract ambiguity, "
            "missing deliverables, and scope traps before you sign"
        ),
        "upwork_search_terms": [
            "contract review automation", "scope analysis AI",
            "freelance contract risk tool", "project scope analyzer"
        ],
        "build_spec": [
            "Input: paste contract text or provide Google Doc URL (fetch via Docs API)",
            "Claude analysis: extract deliverables list, identify ambiguous language, flag missing clauses",
            "Risk scoring: rate each ambiguous clause by severity (HIGH / MEDIUM / LOW)",
            "Missing elements check: payment terms, revision limits, IP ownership, out-of-scope definition, termination clause",
            "Output: structured report with exact quoted text + risk explanation + suggested replacement language",
            "PDF export: clean risk report ready for client negotiation meeting",
            "README: example input/output, what Claude looks for, how to use at proposal stage"
        ],
        "loom_script": {
            "hook": "This contract has three scope traps in it. I found them in 8 seconds.",
            "problem": (
                "Show a typical freelance contract. 'Most people sign these after skimming. "
                "The traps are in clauses like: ongoing support, other duties as required, "
                "unlimited revisions.'"
            ),
            "solution": (
                "Paste the contract. Claude flags three clauses in red -- "
                "explains why each is risky, suggests replacement language. "
                "Show the risk report."
            ),
            "result": (
                "'Three scope traps found. Suggested fixes included. "
                "Ready to negotiate before signing.' Show the PDF export."
            ),
            "cta": (
                "If you are signing contracts without a scope review, "
                "I can build this tool for your agency in 2 days. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "n8n-monitoring-dashboard",
        "title": "n8n Workflow Health Monitoring Dashboard",
        "description": (
            "Self-hosted dashboard that monitors all running n8n workflows: "
            "execution history, error rates, average duration, and failure alerts to Slack. "
            "Essential for clients running production n8n automations."
        ),
        "client_pain": (
            "Clients running production n8n workflows have no visibility into what is "
            "failing, how often, and why. They find out from customer complaints, "
            "not from monitoring."
        ),
        "stack": ["n8n", "supabase", "nextjs", "slack"],
        "niche": "ai-automation",
        "client_types": ["operations teams", "agencies managing client automations", "SaaS companies"],
        "demand_score": 7,
        "uniqueness_score": 9,
        "proof_power": 9,
        "build_hours": 16,
        "github_repo_name": "n8n-monitor",
        "portfolio_headline": (
            "n8n workflow monitoring: execution health dashboard "
            "with real-time error alerts and performance history"
        ),
        "upwork_search_terms": [
            "n8n production monitoring", "workflow error tracking",
            "n8n observability", "automation monitoring dashboard", "n8n DevOps"
        ],
        "build_spec": [
            "n8n webhook triggers: hook every workflow execution on start, complete, and error events",
            "Data collection: execution ID, workflow name, duration, status, error message",
            "Supabase storage: executions table as time-series log",
            "Dashboard: Next.js app with workflow health grid, error rate chart, recent failures list",
            "Alerting: Slack notification on consecutive failures with configurable threshold",
            "SLA tracking: flag critical workflows that have not run in X hours",
            "README: deployment guide, n8n webhook setup, Slack notification config"
        ],
        "loom_script": {
            "hook": "Your n8n workflows are running in production. Do you know which ones failed this week?",
            "problem": (
                "Show a n8n instance with 15 workflows. 'No monitoring. No error tracking. "
                "If something breaks, you find out from a user complaint or a client email.'"
            ),
            "solution": (
                "Show the monitoring dashboard. Workflow health grid -- green, yellow, red. "
                "Error rate chart. Click a failed workflow -- see exact error, timestamp, count."
            ),
            "result": (
                "'3 failed workflows this week. Slack alerted me to all 3 within 60 seconds.' "
                "Show the Slack alert."
            ),
            "cta": (
                "If you are running production n8n workflows without monitoring, "
                "I can build this for your setup in 2-3 days. Message me."
            )
        },
        "leverage_existing": False
    },
    {
        "id": "competitor-radar",
        "title": "AI Competitor Intelligence + Market Monitoring Tool",
        "description": (
            "n8n workflow that monitors competitors' websites, pricing pages, and job postings "
            "weekly. Claude synthesizes changes into a structured intelligence briefing "
            "delivered to Slack or email."
        ),
        "client_pain": (
            "Startup founders and agencies manually checking competitor sites. "
            "Strategy decisions made on 3-month-old intel. "
            "No systematic way to track what competitors are building or hiring for."
        ),
        "stack": ["n8n", "claude-api", "playwright", "supabase"],
        "niche": "ai-automation",
        "client_types": ["startup founders", "strategy consultants", "product managers"],
        "demand_score": 7,
        "uniqueness_score": 8,
        "proof_power": 8,
        "build_hours": 14,
        "github_repo_name": "competitor-radar",
        "portfolio_headline": (
            "Competitor intelligence pipeline: monitors competitor sites + "
            "job posts weekly, delivers synthesized briefing automatically"
        ),
        "upwork_search_terms": [
            "competitor monitoring automation", "market intelligence tool",
            "competitive analysis automation", "website change monitoring",
            "competitor research pipeline"
        ],
        "build_spec": [
            "Config: YAML file listing competitor URLs, sections to monitor, frequency",
            "Scraper: Playwright fetches pages, extracts content sections (pricing, features, blog, jobs)",
            "Change detection: compare against last snapshot in Supabase, flag meaningful diffs",
            "Claude synthesis: what changed, why it might matter, what to watch next week",
            "Job post analysis: detect hiring patterns -- what teams they are growing = strategic signal",
            "Weekly digest: formatted Slack or email briefing with all competitor changes",
            "Archive: full history of page snapshots in Supabase for trend analysis",
            "README: config format, example output briefing, ethical use and ToS notes"
        ],
        "loom_script": {
            "hook": "Three of your top competitors made changes last week. You have not checked their sites in two months.",
            "problem": (
                "Show a list of competitor URLs. 'Manually monitoring 5-10 competitors "
                "is 4-6 hours per week. Most teams skip it. "
                "Strategy gets made on stale information.'"
            ),
            "solution": (
                "Show the weekly briefing email. Walk through each competitor -- "
                "what changed on pricing, what new features appeared, "
                "what they are hiring for. All synthesized by Claude."
            ),
            "result": (
                "'5 competitors. Weekly briefing. 20 minutes of reading vs. "
                "6 hours of manual research.' Show the Slack message."
            ),
            "cta": (
                "If your team is making strategy decisions without current competitor intel, "
                "I can build this. Message me."
            )
        },
        "leverage_existing": False
    }
]


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def load_existing_repos() -> set:
    """Read me/identity.md and extract existing GitHub repo names."""
    if not IDENTITY_MD.exists():
        return set()
    text = IDENTITY_MD.read_text(encoding="utf-8", errors="ignore")
    repos = set()
    for match in re.finditer(r'\b([a-zA-Z0-9][a-zA-Z0-9_-]{3,50})\b', text):
        word = match.group(1).lower()
        if '-' in word or '_' in word:
            repos.add(word)
    return repos


def _time_roi_score(hours: int) -> int:
    if hours <= 8:
        return 10
    if hours <= 12:
        return 8
    if hours <= 16:
        return 6
    if hours <= 22:
        return 4
    return 2


def score_project(p: dict, existing_repos: set) -> dict:
    demand = p["demand_score"]
    proof = p["proof_power"]
    unique = p["uniqueness_score"]
    time_score = _time_roi_score(p["build_hours"])

    composite = (
        demand * 0.35 +
        proof * 0.30 +
        unique * 0.20 +
        time_score * 0.15
    ) * 10  # scale 1-10 components to 0-100

    if p.get("leverage_existing"):
        composite = min(100.0, composite + 5.0)

    # Check if repo already exists
    repo_id = p["github_repo_name"].lower()
    is_existing = repo_id in existing_repos or any(
        repo_id in r or r in repo_id for r in existing_repos if len(r) > 4
    )

    composite = round(composite, 1)
    if composite >= 80:
        priority_label = "CRITICAL -- Build This Week"
    elif composite >= 65:
        priority_label = "HIGH -- Build This Month"
    elif composite >= 50:
        priority_label = "MEDIUM -- Queue Next Cycle"
    else:
        priority_label = "LOW -- Nice To Have"

    return {
        **p,
        "composite_score": composite,
        "time_score": time_score,
        "priority_label": priority_label,
        "is_existing_repo": is_existing
    }


def filter_and_rank(projects: list, niche: str, max_hours: int) -> list:
    result = projects[:]
    if niche:
        niche_key = {"automation": "ai-automation", "fullstack": "fullstack"}.get(
            niche.lower(), niche.lower()
        )
        result = [p for p in result if p["niche"] in (niche_key, "both")]
    if max_hours:
        result = [p for p in result if p["build_hours"] <= max_hours]
    return sorted(result, key=lambda p: p["composite_score"], reverse=True)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _bar(score: float, max_val: float = 10.0, width: int = 10) -> str:
    filled = round((score / max_val) * width)
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def format_card(p: dict, rank: int) -> str:
    lines = []
    lines.append(f"## {rank}. {p['title']}")
    lines.append(
        f"**Priority:** {p['priority_label']}  |  "
        f"**Score:** {p['composite_score']}/100  |  "
        f"**Build Time:** {p['build_hours']} hours"
    )
    if p["is_existing_repo"]:
        lines.append(f"**Status:** Enhance existing repo -- `{p['github_repo_name']}`")
    else:
        lines.append(f"**New Repo:** `{p['github_repo_name']}`")
    lines.append(
        f"**Niche:** {p['niche'].replace('-', ' ').title()}  |  "
        f"**Target Clients:** {', '.join(p['client_types'][:3])}"
    )
    lines.append("")

    lines.append("**Signal Scores:**")
    lines.append(f"  Market Demand   {_bar(p['demand_score'])} {p['demand_score']}/10")
    lines.append(f"  Proof Power     {_bar(p['proof_power'])} {p['proof_power']}/10")
    lines.append(f"  Uniqueness      {_bar(p['uniqueness_score'])} {p['uniqueness_score']}/10")
    lines.append(f"  Time ROI        {_bar(p['time_score'])} {p['time_score']}/10")
    lines.append("")

    lines.append("**Client Pain:**")
    lines.append(p["client_pain"])
    lines.append("")

    lines.append("**Upwork Portfolio Headline:**")
    lines.append(f"> {p['portfolio_headline']}")
    lines.append("")

    lines.append("**Upwork Search Terms This Catches:**")
    lines.append(", ".join(f"`{t}`" for t in p["upwork_search_terms"]))
    lines.append("")

    lines.append("**What To Build:**")
    for item in p["build_spec"]:
        lines.append(f"- {item}")
    lines.append("")

    ls = p["loom_script"]
    lines.append("**60-Second Loom Script:**")
    lines.append(f"- **Hook (0-5s):** {ls['hook']}")
    lines.append(f"- **Problem (5-20s):** {ls['problem']}")
    lines.append(f"- **Solution (20-45s):** {ls['solution']}")
    lines.append(f"- **Result (45-55s):** {ls['result']}")
    lines.append(f"- **CTA (55-60s):** {ls['cta']}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def generate_report(ranked: list, top_n: int) -> str:
    today = date.today().isoformat()
    display = ranked[:top_n] if top_n else ranked

    lines = []
    lines.append("# Project Radar -- Portfolio Build Priority")
    lines.append(
        f"**Generated:** {today}  |  "
        f"**Database:** {len(PROJECT_DB)} projects analyzed  |  "
        f"**Showing:** {len(display)}"
    )
    lines.append("")
    lines.append(
        "*Composite score: Market Demand 35% + Proof Power 30% + "
        "Uniqueness 20% + Time ROI 15%. Leverage bonus: +5 for existing repos.*"
    )
    lines.append("")

    # Summary table
    lines.append("## Priority Summary")
    lines.append("")
    lines.append("| Rank | Project | Score | Hours | Priority |")
    lines.append("|------|---------|-------|-------|----------|")
    for i, p in enumerate(display, 1):
        tier = p["priority_label"].split(" --")[0]
        lines.append(
            f"| {i} | {p['title']} | {p['composite_score']} "
            f"| {p['build_hours']}h | {tier} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Build sequence
    critical = [p for p in display if p["composite_score"] >= 80]
    high = [p for p in display if 65 <= p["composite_score"] < 80]
    medium = [p for p in display if 50 <= p["composite_score"] < 65]
    low = [p for p in display if p["composite_score"] < 50]

    lines.append("## Recommended Build Sequence")
    lines.append("")
    if critical:
        lines.append("**This Week -- Critical (highest portfolio ROI):**")
        for p in critical:
            lines.append(f"- {p['title']} ({p['build_hours']}h) -- {p['portfolio_headline']}")
        lines.append("")
    if high:
        lines.append("**This Month -- High:**")
        for p in high:
            lines.append(f"- {p['title']} ({p['build_hours']}h)")
        lines.append("")
    if medium:
        lines.append("**Next Cycle -- Medium:**")
        for p in medium:
            lines.append(f"- {p['title']} ({p['build_hours']}h)")
        lines.append("")
    if low:
        lines.append("**Nice To Have -- Low:**")
        for p in low:
            lines.append(f"- {p['title']} ({p['build_hours']}h)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("# Detailed Specs")
    lines.append("")
    for i, p in enumerate(display, 1):
        lines.append(format_card(p, i))

    return "\n".join(lines)


def save_output(report: str) -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = OUTPUTS / f"{today}-project-radar.md"
    path.write_text(report, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    top_n = None
    niche_filter = None
    max_hours = None
    json_mode = "--json" in args
    no_save = "--no-save" in args

    i = 0
    while i < len(args):
        if args[i] == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])
            i += 2
        elif args[i] == "--niche" and i + 1 < len(args):
            niche_filter = args[i + 1]
            i += 2
        elif args[i] == "--max-hours" and i + 1 < len(args):
            max_hours = int(args[i + 1])
            i += 2
        else:
            i += 1

    existing_repos = load_existing_repos()
    scored = [score_project(p, existing_repos) for p in PROJECT_DB]
    ranked = filter_and_rank(scored, niche_filter, max_hours)

    if json_mode:
        output = ranked[:top_n] if top_n else ranked
        print(json.dumps(output, indent=2))
        return

    report = generate_report(ranked, top_n)

    if not no_save:
        path = save_output(report)
        print(f"Saved: {path}\n")

    print(report)


if __name__ == "__main__":
    main()

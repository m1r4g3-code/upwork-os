# Portfolio Form Copy — Batch 2
**Date:** 2026-08-07
**Projects:** Kairos, YCT Exam Nav, Hephzibah OS
**Status:** final

---

## 1. KAIROS — Value Bet Prediction Engine

**Portfolio Title:**
Kairos — Statistical Value Bet Engine (Python, Pinnacle, Kelly Criterion)

**Your Role:**
Solo Developer

**Project Description (paste into Upwork):**
Kairos is a pure Python prediction engine for football value betting. It compares true match outcome probabilities — calculated using the Poisson distribution with Dixon-Coles attack/defense ratings per team — against implied probabilities derived from Pinnacle odds (the sharpest book in the market). When the model finds a meaningful gap between the two, it flags a value bet.

The system covers four markets with verified Pinnacle sharp lines: 1X2, Over/Under totals, Asian Handicap, and Double Chance. Markets without a reliable sharp reference — half-time results, corners, next goal — are automatically skipped. There is no guessing. The design is built around one constraint: no sharp line means no output.

Position sizing is handled by the Kelly Criterion. The system outputs a BET, SKIP, or SPECULATIVE verdict per market, along with the computed edge, implied probability, and the recommended stake fraction. The engine runs locally with no external API fees and is fully open source.

**Skills to tag:**
Python, Statistical Modeling, Probability Theory, Data Analysis, Sports Analytics, API Integration, Algorithmic Trading Logic

---

## 2. YCT EXAM NAV — Smart Exam Timetable System

**Portfolio Title:**
YCT Exam Nav — University Exam Scheduling System (Next.js, Supabase, DSatur)

**Your Role:**
Solo Developer / Full-Stack Engineer

**Project Description (paste into Upwork):**
A full-stack exam management system built for and deployed at Yaba College of Technology (Yabatech), one of Nigeria's largest polytechnics. The system manages exam scheduling across 7 departments — Computer Science, Agricultural Technology, Food Technology, Hospitality Management, Leisure and Tourism, Nutrition and Dietetics, and Polymer and Textile Technology — with 119 exams per semester currently published and zero scheduling conflicts.

The core scheduling engine uses the DSatur (Degree of Saturation) graph coloring algorithm. Courses are modeled as graph nodes; students enrolled in multiple courses create edges between them. DSatur assigns time slots by coloring the graph such that no two connected courses share a slot — meaning no student ever sits two exams at the same time. Hall allocation and seat assignment happen automatically from capacity constraints and enrollment data.

The student-facing dashboard shows each student their personal timetable — course name, date, time, hall, seat number, and a navigate-to-hall button. Admins manage all timetable generation, editing, and publication through a role-protected admin panel. The system is live at smart-exam-timetable.vercel.app, built on Next.js, TypeScript, Supabase, and PostgreSQL, with Vercel deployment.

**Skills to tag:**
Next.js, TypeScript, React, Supabase, PostgreSQL, Algorithm Design, Graph Theory, Full-Stack Development, Vercel, System Architecture

---

## 3. HEPHZIBAH OS — AI Cold Outreach Intelligence System

**Portfolio Title:**
Hephzibah OS — Autonomous AI Outreach System (Python, Claude AI, Playwright, Telegram)

**Your Role:**
Solo Developer / Systems Architect

**Project Description (paste into Upwork):**
Hephzibah OS is a custom-built AI outreach intelligence system I use to run my own freelancing operation. It consists of five background daemons registered in Windows Task Scheduler — email watcher, job watcher, follow-up engine, outreach engine, and heartbeat — that collectively handle lead discovery, outreach generation, proposal follow-ups, and inbox monitoring without any manual triggering.

Lead discovery runs on two sources: Google Maps (local businesses via Playwright) and DesignRush (verified US agencies). For each prospect found, the system visits their website, identifies a specific operational gap, and passes that context to Claude AI, which writes a personalized cold email naming the exact gap, the relevant tool, and a rough timeline. No two emails are identical.

Every email goes through a Telegram approval gate before sending. A card appears on my phone with the subject line and full body. I tap Approve or Skip. Approved emails are sent immediately via Gmail API. Replies from known prospect emails trigger a Telegram alert and auto-prepare a pre-call brief. The system also includes a persistent Obsidian-based brain with 300+ linked memory nodes — clients, patterns, proposals, and strategic decisions stored as interconnected markdown and synced via Git.

**Skills to tag:**
Python, Claude AI, Playwright, Gmail API, Telegram Bot API, n8n, System Architecture, Workflow Automation, Cold Outreach, AI Agents

---

## Upload order recommendation

1. SERAMAN (strongest — real client, 5-star, complex production system)
2. Hephzibah OS (shows you built the tooling for your own operation)
3. YCT Exam Nav (real institutional deployment, algorithm depth)
4. Kairos (statistical modeling, unique niche)
5. AI Avatar Doctor (client work, real views)
6. Multilingual Pipeline (extends the doctor project)
7. Noryx Studio (web app, different category)
8. Personal Assistant (AI agent demo)
9. YouTube Summarizer (clean n8n pipeline)
10. TikTok Performance (analytics automation)

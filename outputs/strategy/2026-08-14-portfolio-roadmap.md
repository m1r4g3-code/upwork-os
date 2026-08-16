# Portfolio Roadmap — AI Engineering Projects
**Date:** 2026-08-14
**Status:** reference

---

## Tier A: API-Integration Projects (Month 1-5 Build Order)

These demonstrate system design, production discipline, and AI integration.
Market rate: $5K-$50K per project type.

### 1. Voice AI Agent
Stack: Twilio Media Streams + Deepgram Realtime STT + Claude API + ElevenLabs TTS + FastAPI
Demo: Real phone number. Call it. It answers, reasons, books appointments.
Opens: Customer service automation ($15K-$50K), lead qualification, appointment booking
Build time: 2-3 weeks

### 2. Multi-Agent Research Orchestrator
Stack: LangGraph + Claude API + Tavily search + FastAPI + Supabase
Architecture: Orchestrator delegates to Researcher, Analyst, Writer, Fact-Checker agents
Demo: Type a research question. 5 min later, 8-page report with citations.
Opens: Research automation ($10K-$40K), competitive intelligence, market analysis
Build time: 3-4 weeks

### 3. Production RAG Document Intelligence
Stack: FastAPI + Supabase pgvector + LlamaIndex + Claude API + Hybrid search
Differentiators: Semantic chunking, hybrid search, citation tracking, access control, cost tracking
Demo: Upload 50 PDFs. Ask cross-document questions. Exact citations on every answer.
Opens: Legal document analysis ($20K-$75K), medical records, financial compliance
Build time: 3-4 weeks

### 4. AI Business Analyst (NL to SQL to Report)
Stack: FastAPI + Claude API + Supabase/Postgres + Plotly + ReportLab + APScheduler
Key feature: SQL validation layer before execution (read-only check, no destructive ops)
Demo: Type business question. Get chart + PDF report + scheduled email.
Opens: Automated BI ($5K-$25K), reporting automation, analytics platforms
Build time: 2-3 weeks

### 5. Content Recycling Pipeline
Stack: n8n + Claude API + Whisper + Buffer API + PostgreSQL + Telegram approval bot
Flow: Long-form input → AI extracts insights → platform-specific content → Telegram review → schedule
Demo: Feed 45-min podcast. 30 days of content ready for approval in 10 min.
Opens: Content agency automation ($5K-$20K), creator tools, social media team replacement
Build time: 2 weeks

### Python Discipline Required on All 5
- Pydantic models throughout (not raw dicts)
- Async FastAPI (not Flask, not sync)
- Docker + docker-compose
- .env management (no hardcoded keys)
- Integration tests (not just unit tests)
- Cost tracking per API call
- README with architecture diagram

---

## Tier B: Advanced Engineering Projects (No API Fees Required)

See 2026-08-14-portfolio-roadmap-advanced.md for the full list.
Emmanuel chose specific projects from this list on 2026-08-14.

---

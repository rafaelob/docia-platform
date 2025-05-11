---
trigger: always_on
---

# Project Core & Context

- Project Name/Identifier: **MedflowAI (DocIA Platform)**
- Primary Goal/Purpose: Provide clinical co-intelligence via dual-LLM second opinions (GPT-4.1 & Gemini 2.5 PRO) with O3-HIGH arbiter for divergences.
- Application Type: Event-driven micro-service backend plus Next.js clinician web UI.
- High-Level Architecture: Input Guardrails → Triage Agent → (a) Simple: Output Guardrails → Cache; (b) Complex: GPT-4.1 & Gemini 2.5 PRO Specialists → RAG Pipeline (Supabase pgvector) → Reconciliator (Gemini FLASH) → Validator → Judge O3-HIGH (if divergent) → Output Guardrails → Cache → User.
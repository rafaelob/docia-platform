---
trigger: always_on
---

# Technology Stack & Key Architecture

- Main Programming Languages & Versions: **Python 3.12** (backend), **TypeScript / Next.js 14** (frontend)
- Key Frameworks/Libraries:
    - OpenAI Agents SDK (v0.3+)  
    - OpenAI Python (v1.*)
    - **google-genai** (v0.2) — mandatory; *google-generativeai is deprecated and must NOT be used*
    - Pydantic-AI (latest) for type-safe LLM output validation
    - Redis-py (5.*) → Redis 7 (cache)
    - FastAPI (0.110) for glue micro-APIs
- Architectural Patterns: Event-driven micro-services + Agent Orchestration (Triage → RAG → Specialists → Reconciliation → O3 Arbiter)
+ - High-Level Flow Summary:
+     1. **Input Guardrails** → `TriageAgent (GPT-4.1)`
+     2. **Simple case**: direct response → `Output Guardrails` → Cache → User.
+     3. **Complex case**: delegate to **GPT-4.1 Specialist** & **Gemini 2.5 Specialist** → `RAG Pipeline (Responses API + VectorDB)` for evidence.
+     4. **Reconciliator (Gemini 2.5 FLASH)** compares outputs.
+         • If **equivalent** → `Validator (Pydantic-AI schema)` → Output Guardrails.
+         • If **divergent** → `Judge O3-HIGH` (GPT-4.1 or Gemini) → Validator → Output Guardrails.
+     5. Final answer cached (Redis) and returned to User.
- Database: PostgreSQL 15 (managed by Supabase)
- ORM/Query Builder: SQLAlchemy 2.*, Alembic migrations
- Cloud Services/Providers: Supabase (DB & Auth), Docker/K8s on Azure, Netlify for static web preview
- **Local Dev Ports (docker-compose.dev.yml)**: Redis `6380`; Supabase PG `5433`; GoTrue `9999`; OTEL Collector `4317`.
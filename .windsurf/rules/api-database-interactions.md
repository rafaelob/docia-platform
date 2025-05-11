---
trigger: always_on
---

# API Design & Database Interaction Rules

- API: RESTful FastAPI endpoints; JSON only; version via `Accept-Version` header.
- Databases:
    - **Primary**: Supabase PostgreSQL 15 (SQLAlchemy 2 / asyncpg; migrations via Alembic; tenant-aware schemas).
    - **Vector Store**: Supabase `pgvector` extension for embeddings powering the RAG pipeline.
- Key Tables: patients, consultations, llm_responses, divergences.
- Environment Vars (see `infra/env.supabase.sample`): `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `POSTGRES_PASSWORD`, `JWT_SECRET`.
- Security: Enable Row Level Security (RLS) on patient-sensitive tables (`cases`, `consultations`).
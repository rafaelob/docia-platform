# Supabase Setup Guide for MedflowAI

_Last updated: 2025-05-10_

This guide walks you through creating a Supabase project and wiring it up to your local/dev environments for MedflowAI.

---

## 1. Create a Supabase Account & Project

1. Go to https://supabase.com and sign-up (GitHub/Google SSO works).
2. Click **New project**.
3. Fill in:
   | Field | Recommendation |
   |-------|----------------|
   | **Organization** | Select or create `MedflowAI` |
   | **Project name** | `medflow-ai-${ENV}` (`dev`, `stg`, `prod`) |
   | **Password** | _Generate a strong password_ (→ `POSTGRES_PASSWORD`) |
   | **Region** | Closest to majority of users (🇧🇷  São Paulo suggested) |
4. Wait for provisioning (~2 min). You’ll land on the project Dashboard.

## 2. Obtain Keys & URLs

From _Project Settings → API_ copy:

| Variable | Where to put | Purpose |
|----------|--------------|---------|
| `SUPABASE_URL` | `.env.*` | Base REST/Realtime URL (e.g. `https://xyz.supabase.co`) |
| `SUPABASE_ANON_KEY` | Front-end / public SDK | Client-side auth/tokenless reads |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend secrets | Full access from micro-services |
| `JWT_SECRET` | Gotrue settings (defaults to Service key) | Used for server-side verification |

_Note:_ For local Docker stack we **don’t** need these; the compose file spins its own Postgres+Gotrue.

## 3. Import Schema

Run either:

```bash
psql "${SUPABASE_URL}/postgres" -U postgres -f infra/supabase_schema.sql
```

or use Supabase SQL Editor and paste the contents of `infra/supabase_schema.sql`.

This creates the `cases` and `consultations` tables.

## 4. Environment Variables

Copy `infra/env.supabase.sample` and rename to `.env.dev`, `.env.stg`, etc.

```
# Supabase
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
JWT_SECRET=...
POSTGRES_PASSWORD=...
```

Back-end services (e.g., triage, specialists) load these via `pydantic.BaseSettings`.

## 5. Local Development (Docker Compose)

If you prefer **local-only** stack, simply run:

```sh
docker compose -f infra/docker-compose.dev.yml up -d
```

This starts `supabase-db` & `supabase-gotrue` listening on 5432/9999 with default credentials (`postgres/postgres`).

### Seed database

```sh
docker compose exec supabase-db psql -U postgres -f /docker-entrypoint-initdb.d/001_schema.sql
```

(Alternatively mount the SQL via volumes).

## 6. Production Considerations

* Enable **backup & PITR** in Supabase → _Paid plan_.
* Activate **Row Level Security** and policies for `cases` (patient-specific access).
* Rotate Service Role keys via Secrets Manager.
* Encrypt data at rest is on by default (AES-256, A-WS KMS).

## 7. Troubleshooting

| Issue | Fix |
|-------|-----|
| "password authentication failed" | Re-enter `POSTGRES_PASSWORD` in env & database credentials page |
| 404 on `/auth/v1/token` | Gotrue not enabled / wrong subdomain |
| Timeout connecting from Docker | Expose port 5432 in project settings or use Supabase CLI tunnel |

---

Questions? Reach out #devops-infra on Slack.

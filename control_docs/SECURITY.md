---
title: Security & Compliance Guide
lastUpdated: 2025-05-10
---

## Objetivo
Proteger dados sensíveis e cumprir LGPD (Brasil) + HIPAA (EUA).

## Controles principais
- Comunicação TLS 1.3; AES‑256‑GCM em repouso
- Redação PII (spaCy) antes de enviar prompt à LLM
- Rate‑limit no API Gateway (100 RPS / user)
- SBOM gerado `pip-audit`; Dependabot alerts
- OTEL audit‑log imutável (hash‑chain)
- SLA incidente: triagem 24h, notificação 72h
- Validação **Pydantic-AI**: todas as respostas LLM são parseadas e validadas antes de prosseguir.
- **Redação PII** embutida no pipeline de prompt (spaCy + heurísticas médicas) para qualquer texto enviado/recebido.
- OTEL tracing automático em adapters e tools; métricas `divergence_rate`, `cache_hit_rate`.
- SBOM gerado via `pip-audit`; distribuído em artefatos CI.

## Secrets & Environment Variables

| Variable | Scope | Storage |
|----------|-------|---------|
| `OPENAI_API_KEY` | All backend pods | K8s Secret / GitHub OIDC | 
| `GOOGLE_GEMINI_API_KEY` | Specialist services | K8s Secret | 
| `SUPABASE_URL` | Services needing DB | K8s ConfigMap | 
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only | K8s Secret | 
| `JWT_SECRET` | Gotrue / API Gateway | Secrets Manager | 
| `POSTGRES_PASSWORD` | Supabase-db (local) | `.env.dev` only |

_Secrets never committed; reference `infra/env.supabase.sample` for local dev._

## STRIDE resumo
| Ameaça | Vetor | Mitigação |
|--------|-------|-----------|
| Spoofing | JWT forjado | Assinatura RS256, exp 15 min |
| Tampering | Prompt injection | Pydantic‑AI + Guardrail SDK |
| Repudiation| Logs falsos | OTEL + hash‑chain S3 |
| Info Disclosure | Falha PII | Redaction + role‑based access |
| DoS | Abuse LLM | Circuit‑breaker, quotas |
| Elev. Privilege | Token escalado | OIDC scopes mínimos |

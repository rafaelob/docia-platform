---
trigger: always_on
---

# MedflowAI Coding Standards
## Backend
• Python 3.12; PEP 8 + Black + isort.
• Google-style docstrings, full type hints.
• Pydantic (+ Pydantic-AI) for data / LLM output.
• Pytest ≥ 85 % cobertura.
• Stateless JSON services; Redis cache.
• Siga padrões OpenAI Agents SDK.
• Estrutura de logs OTEL; exceções específicas; sem segredos em código.

## Frontend
• Next.js + TypeScript; Airbnb ESLint.
• React Hooks, componentes funcionais e modulares.
• CSS Modules / styled-components; design responsivo.
• Jest + RTL para testes.
• Semântica HTML, estados de erro/loader amigáveis.

## DevOps
• CI/CD: lint, testes, segurança passam antes de merge.
• Git Flow + commits Angular.
• Docker para todos os serviços; IaC via Terraform.
• Scans de segurança automáticos; métricas Prometheus/Grafana.

Feedback submitted
Generating..
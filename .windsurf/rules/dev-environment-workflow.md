---
trigger: always_on
---

# Development Environment & Workflow

- Version Control: **Git** (GitHub). Branch model: Git Flow with `main`, `develop`, `feature/*`, `hotfix/*`.
- Build / Package Managers: **Poetry** (Python), **pnpm** (Node/TS). Docker Compose for local infra.
- Deployment Environments: Dev → Staging → Prod via GitHub Actions, Docker, Terraform.
- Development Workflow: PRs require CI passing (lint, tests ≥85% cov). Reviews from another squad member. Features tracked in control_docs/TODO.md.
- Team Structure & Roles: Platform Eng (libs), Clinical Backend (services), UX Guild (apps), DevOps (infra).
- Preferred Communication: Slack (#medflowai-dev), Issues/PR comments.

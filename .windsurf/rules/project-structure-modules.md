---
trigger: always_on
---

# Project Structure & Key References

Refer to `control_docs/SYSTEM_DESIGN.md` for the authoritative architecture and directory map, and to `control_docs/PROJECT_OVERVIEW.md` for high-level vision and scope. Below is only a quick pointer for Windsurf:

- Core Library: `packages/libs/medflowai/` – agent orchestration, adapters & tools
- Micro-services: `packages/services/` – triage, specialists, reconciliation, arbiter-o3
- Web UI: `packages/apps/clinic-web/` – Next.js clinician desktop app

Key feature delivered: **dual-LLM second opinion with automated divergence arbitration (GPT-4.1 + Gemini 2.5 PRO + O3-HIGH)**.

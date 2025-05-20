# MedflowAI – Orchestration Configuration Guide

_As of release **0.8.0-beta**, MedflowAI ships with a **single** orchestrator architecture ("Dual-LLM Second Opinion" – see §3 of `SYSTEM_DESIGN.md`).  Future releases will support multiple orchestrator variants (e.g., specialty-specific flows, cost-optimised pathways, offline-first mode).  This document sets the conventions for defining and discovering those variants._

---

## 1. Directory Layout
```
config/
└─ orchestrations/
   ├─ dual_llm_v1.yaml        # current default architecture (implicit)
   ├─ cost_optimised.yaml     # example future variant
   └─ speciality_obgyn.yaml   # example future variant
```
•  **All orchestration config files live in `config/orchestrations/` and use YAML.**  
•  File name = *slug* identifying the variant.  
•  The orchestrator will load a variant via CLI/ENV (`ORCHESTRATION_ID`) or fall back to `dual_llm_v1`.

---

## 2. YAML Schema (draft)
| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `id` | string | ✓ | Unique slug (matches filename without `.yaml`). |
| `description` | string | ✓ | Human readable overview. |
| `flow` | list(step) | ✓ | Ordered list of agent/tool steps. Each step:<br>• `type`: `agent` \| `tool`<br>• `name`: class path or registry key<br>• `on_error`: `retry` \| `skip` \| `abort` |
| `llm_overrides` | dict | – | Model/param overrides per agent (`agent_name: {model: ..., temperature: ...}`). |
| `env` | dict | – | Extra env vars required (validated at startup). |
| `version` | string | – | SemVer of the authoring library version. |

A full JSON-Schema will be committed when multiple variants are implemented (tracked by **TODO T-38**).

---

## 3. Compatibility Rules
1. **Backwards compatible**: New orchestrations must not break existing ones.  
2. **Prompt registry linkage**: Each agent step must reference a prompt template in `PROMPTS.md` *or* declare `custom_prompt: <template>` inline.  
3. **Test coverage**: Every variant requires at least one happy-path integration test.

---

## 4. Roadmap
| Milestone | Task | Doc/Ticket |
|-----------|------|------------|
| v0.9.0 | YAML schema finalised & validated via `pydantic-yaml` models | T-38 |
| v1.0.0 | CLI flag `--arch <id>` and env `ORCHESTRATION_ID` | T-39 |
| v1.1.0 | Config-driven prompt overrides & per-step adapters | T-42 |

---

*See also:*  
•  `PROMPTS.md` – canonical prompt templates.  
•  `SYSTEM_DESIGN.md §6` – Prompt registry; §3 flow diagrams.  
•  ADR-007 (pending) – Configuration-driven Orchestration.

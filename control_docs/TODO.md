# MedflowAI Tasks & Sprint Backlog

Key: `[x]` Done | `[~]` WIP / In Progress | `[ ]` To Do

## Sprint Backlog (MVP: 08 May → 20 May 2025)

*Source: Legacy `TODO.txt`, Last Updated: 2025-05-10*

| Status | Task ID | Tipo    | Due    | Pts | Descrição                                                      |
|--------|---------|---------|--------|-----|----------------------------------------------------------------|
| `[~]`  | T-01    | Setup   | 09‑Mai | 2   | Docker base Python 3.9 + libs (openai, pydantic‑ai, redis, otel) |
| `[~]`  | T-02    | Backend | 10‑Mai | 5   | Implementar Agente **Triagem** (GPT‑4.1) - OpenAI part partially done, Gemini pending |
| `[~]`  | T-03    | Backend | 11‑Mai | 5   | Implementar Adaptadores Especialistas (GPT‑4.1 & Gemini 2.5)   |
| `[ ]`  | T-04    | Backend | 12‑Mai | 3   | Implementar Agente **Reconciliação**                             |
| `[ ]`  | T-05    | Backend | 12‑Mai | 3   | Integração RAG (OpenAI Responses API)                          |
| `[ ]`  | T-06    | Backend | 13‑Mai | 3   | Upload & análise de imagens (file_id)                          |
| `[ ]`  | T-07    | Backend | 14‑Mai | 5   | Integração Juiz **O3‑mini** + validação Pydantic               |
| `[ ]`  | T-08    | DevOps  | 16‑Mai | 2   | Otel Collector + dashboards                                    |
| `[ ]`  | T-09    | QA      | 17‑Mai | 3   | Testes E2E (happy‑path & divergência)                          |
| `[ ]`  | T-10    | Release | 20‑Mai | 1   | Tag 0.9.0‑beta + changelog                                     |
| `[ ]`  | T-11    | Backend | 18‑Mai | 3   | Implementar `packages/reconcil/divergence.py` conforme ADR-005 |
| `[ ]`  | T-12    | QA      | 19‑Mai | 3   | Pytest cobrindo regras 1-5 (≥ 90 % cobertura)                  |
| `[ ]`  | T-13    | DevOps  | 20‑Mai | 2   | Atualizar painel OTEL com `divergence_rate`                    |
| `[ ]`  | T-14    | Backend | 12-Mai | 3   | Implement `medflowai.adapters.OpenAIAdapter` & `GeminiAdapter` |
| `[x]`  | T-15    | Backend | 12-Mai | 3   | Implement `RAGTool` & integrate into `MedicalRAGAgent` - _RAGTool implementation complete (Supabase+OpenAIEmbeddings), ready for integration & testing. MedicalRAGAgent LLM synthesis OpenAI part done._ |
| `[x]`  | T-16    | Backend | 13-Mai | 3   | Implement **DivergenceReviewAgent** (LLM qualitative review) |
| `[x]`  | T-17    | Backend | 13-Mai | 3   | Integrate DivergenceReviewAgent into Orchestrator – `process_specialist_outputs` + arbiter stub + tests |
| `[x]`  | T-18    | Backend | 14-Mai | 2   | O3-mini Arbiter micro-service (`packages/services/arbiter-o3`) integrado ao Orchestrator + unit tests |
| `[x]`  | T-19    | Backend | 20-Mai | 5   | Enhance `OrchestratorPrincipal` with branching & retry |
| `[~]`  | T-20    | QA      | 17-Mai | 3   | Unit tests (>85 %) for adapters, RAG, **divergence agent**, orchestrator |
| `[ ]`  | T-21    | QA      | 17-Mai | 3   | E2E tests (happy-path & divergence flow)                      |
| `[x]`  | T-22    | DevOps  | 11-Mai | 2   | docker-compose.dev com Redis + Supabase + OTEL |
| `[x]`  | T-23    | Backend | 12-Mai | 3   | Implement Supabase DAL (`medflowai.db.supabase_client`) |
| `[~]`  | T-24    | QA      | 13-Mai | 2   | Fixture pytest-docker + test_db_case_flow |
| `[x]`  | T-30    | Backend |        |     | Create central prompt registry for agents and reference in docs |
| `[x]`  | T-38    | Backend | 20-Mai | 3   | Implement YAML schema + default `dual_llm_v1.yaml` + loader tests (orchestration variants framework) |

**Total story points for sprint:** 72

---

## Detailed Tasks & `medflowai` Library Enhancements

### Foundational `medflowai` Library Migration & Setup

*   `[x]` chore: Refactor and migrate legacy `med_agent_orchestrator` components into `packages/libs/medflowai` library.
    *   Description: Establish a well-structured `medflowai` library with clear separation of concerns (core, models, adapters, agents, tools). Migrate all Python files from the `legado/` directory, update imports, and ensure proper module initialization.
    *   Status: Completed (Corresponds to various items in the sprint backlog, e.g., T-02, T-03 implies this is done for those agents).
*   `[x]` docs: Create initial `SYSTEM_DESIGN.md` for MedflowAI.
    *   Description: Document the high-level architecture and the detailed structure of the `medflowai` library.
    *   Status: Completed.
*   `[x]` docs: Update `FEATURES.md` with core `medflowai` library capabilities and merged product features.
    *   Description: Consolidate platform and library features into a single document.
    *   Status: Completed.
*   `[x]` docs: Merge `CHANGELOG.txt` into `CHANGELOG.md`.
    *   Description: Consolidate changelog information.
    *   Status: Completed.

### Core Backend & Library Development (Post-MVP / Ongoing)

*   `[ ]` feat: Implement advanced RAG capabilities within `MedicalRAGAgent` using `RAGTool` (Post T-05).
    *   Description: Enhance `RAGTool` with specific vector DB integration, advanced chunking/indexing, and hybrid search.
    *   Status: To Do.
*   `[ ]` feat: Fully implement divergence detection logic in `ReconciliationService` or core `medflowai` component (Post T-04, T-11).
    *   Description: Develop and test the mechanism to compare outputs from multiple specialist agents and identify clinically significant divergences based on `ADR-005`.
    *   Status: To Do.
*   `[ ]` feat: Complete Integration of O3-mini Arbiter agent call from `ArbiterO3Service` (Post T-07).
    *   Description: Ensure robust calling of the O3-mini model via the `ArbiterO3Service` when divergence is detected and requires arbitration.
    *   Status: To Do.
*   `[ ]` test: Develop comprehensive unit tests for all `medflowai` components (Post T-12).
    *   Description: Achieve >85% test coverage for all library components, including agents and tools.
    *   Status: To Do.
*   `[x]` feat: Implement advanced orchestration flows in `medflowai.core.Orchestrator`.
    *   Description: Added support for conditional branching, parallel execution with consensus, and robust error handling/retry logic via YAML configuration.
    *   Status: Completed as part of T-38.
*   `[ ]` feat: Full Pydantic-AI integration for LLM output validation.
    *   Description: Refactor LLM adapters and agents to use Pydantic-AI for direct parsing and validation of LLM responses against Pydantic models.
    *   Status: To Do.

### Services (Beyond initial MVP setup in Sprint)

*   `[ ]` feat: Develop `SpecialistService` using relevant `medflowai.agents` and `medflowai.adapters`.
    *   Description: Create microservice endpoints for specialist agent functionalities.
    *   Status: To Do.
*   `[ ]` feat: Develop `ReconciliationService` incorporating divergence logic.
    *   Status: To Do.

### General

*   `[x]` chore: Commit all recent code and documentation changes with a comprehensive message.
    *   Status: Done.

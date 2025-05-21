# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Refactored and migrated legacy `med_agent_orchestrator` components into a new, well-structured `packages/libs/medflowai` library. This includes establishing `core`, `models`, `adapters`, `agents`, and `tools` submodules with appropriate `__init__.py` files.
- Created initial control documents: `SYSTEM_DESIGN.md`, `TODO.md`, `FEATURES.md` to reflect the new library structure and project status.
- ADR-005: critérios de divergência clínica
- Atualizações em ROADMAP, TODO e FEATURES para Divergence engine
- **Enhanced MedicalRAGAgent**: added `patient_context` input support; updated tests & docs.
- `DivergenceReviewAgent` (F-16 / T-16): LLM-based qualitative review of two specialist reports. Returns JSON with `status` (`equivalent`/`divergent`) and `justification`. Includes exponential retry and unit tests.
- **Orchestrator branching (T-17)**: Added `process_specialist_outputs` helper and arbiter escalation stub; unit tests cover equivalent/divergent paths.
- #### O3-mini Arbiter (T-18)
* New FastAPI micro-service `packages/services/arbiter-o3` with `/arbiter/v1/review` endpoint using `llm_client.compare_reports` to decide between two specialist reports (GPT-4o or Gemini).
* Integrated `medflowai.services_proxy.arbiter_client` with enum `Verdict` and updated `OrchestratorPrincipal._escalate_to_arbiter`.
* Unit tests: `tests/services/test_arbiter_o3_unit.py`; tests pass via dummy adapters.
- Added centralized `control_docs/PROMPTS.md` registry with template sections for TriageAgent, MedicalRAGAgent, DivergenceReviewAgent, VerificationAgent. Updated SYSTEM_DESIGN with reference.
- Added `medflowai.core.orchestration_config` with Pydantic models + loader for YAML-based orchestrations; created `ORCHESTRATION_CONFIGS.md` doc.
- **Dynamic Orchestration Engine (T-38/T-19)**: YAML-driven sequential / parallel flow executor implemented in `OrchestratorPrincipal` with conditional branching, robust retry, and shared context store.
- **Env Var Validation Helper**: Introduced `SKIP_ORCH_ENV_VALIDATION` to bypass strict env checks during local testing/CI; pytest auto-skips default config.
- **Tooling**: `medflowai.core.retry_utils` now downgrades gracefully to stdlib logging when `structlog` unavailable.
- **Responses API Update (21-Mai-2025)**: Added new reference doc `OpenAI_Responses_API_2025-05-21.txt` summarising remote MCP support, image generation, Code Interpreter, file search v2, background mode, reasoning summaries and encrypted reasoning items.
- Updated `FEATURES.md` with new capabilities (MCP, image generation, code interpreter, file search v2, background mode, encrypted reasoning).
- **LLM Responses API Support**: Introduced `responses_create` abstract method in `BaseLLMAdapter`, enabling first-class integration with provider-specific *Responses* endpoints.
- **OpenAIAdapter**: Implemented async `responses_create()` wrapping `client.responses.create` with full error handling and mapping to `UnifiedLLMResponse`.
- **GoogleGeminiAdapter**: Added stub `responses_create()` that gracefully falls back to `chat_completion`, guaranteeing interface parity.

### Changed
- T-23 concluído (Supabase DAL) – FEATURE F-14 marcada como .
- `pytest.ini` cleaned deprecated `python_paths` option.
- Arbiter client fallback now returns valid enum `Verdict.cannot_decide`, fixing validation errors in divergence escalation tests.
- All unit tests pass (`pytest -q`), ensuring orchestrator + arbiter integration green. 1 test skipped (integration placeholder).
- **MedicalRAGAgent**: Now prefers `responses_create` for synthesis when available, with safe fallback to `chat_completion` and improved mock-aware detection in tests.
- Unit test suite updated; all tests pass (`pytest -q` green) confirming backward compatibility.

## [0.8.0-beta] – 2025-05-08
### Added
- Dual Opinion Engine design (GPT-4.1 + Gemini 2.5)
- O3-mini arbiter workflow
- Python 3.9 runtime lock
- Updated roadmap deadline to 20 Mai 2025

## [0.7.0] – 2025-04-15
### Added
- Initial monorepo, CI pipeline

## [0.3.2-infra] – 2025-05-10
### Added
- docker-compose.dev with Redis, Supabase, OTEL (auto seed schema).
- Supabase schema SQL & env sample.
- New tasks T-22/23/24 in TODO; F-13 in FEATURES.
- SYSTEM_DESIGN §7.4 external services.
- SECURITY.md secrets table.
- TEST register row for Supabase integration.

## [0.3.1-docs] – 2025-05-10
### Added
- SYSTEM_DESIGN.md §7.3: DivergenceReviewAgent description & flow.
- ADR-005: LLM-based divergence analysis.
- SECURITY.md: Pydantic-AI validation, PII redaction pipeline, OTEL tracing.
- TODO/FEATURES/TEST updated to reflect DivergenceReviewAgent tasks and tests.

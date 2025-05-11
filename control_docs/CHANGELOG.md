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

### Changed
- T-23 concluído (Supabase DAL) – FEATURE F-14 marcada como .

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

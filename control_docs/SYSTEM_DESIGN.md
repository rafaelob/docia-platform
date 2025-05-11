# MedflowAI System Design

## 1. Overview

MedflowAI is a clinical co-intelligence platform designed to provide AI-powered second opinions and decision support in clinical settings. It leverages multiple Large Language Models (LLMs) and a structured agent-based architecture to process queries, retrieve relevant medical information, and generate insights.

## 2. High-Level Architecture

The MedflowAI platform consists of several key components:

*   **Core Library (`packages/libs/medflowai/`)**: The central orchestrator and agent framework. This library provides the foundational classes and modules for building and running MedflowAI agents.
*   **Microservices (`packages/services/`)**: Specialized services that implement specific agent functionalities or connect to external systems (e.g., Triage, Specialists, Reconciliation, Arbiter).
*   **Applications (`packages/apps/`)**: User-facing interfaces (e.g., `clinic-web` Next.js desktop UI).
*   **Infrastructure (`infra/`)**: Docker, Terraform, Kubernetes configurations, and CI/CD pipelines.
*   **Supporting Documentation**: `docs_project/`, `references/`.

## 3. Visual System Flow (Conceptual)

```mermaid
graph LR
  User[Usuário] --> IG[Input Guardrails]
  IG --> T(Triagem GPT-4.1)
  T -->|simple| OG[Output Guardrails]
  OG --> Cache[Redis 24h]
  Cache --> Out[Resposta Final]
  Out --> User
  T -->|complex| G4[Especialista GPT-4.1]
  T -->|complex| GE[Especialista Gemini 2.5 PRO]
  G4 --> RAG[Evidence via Responses]
  GE --> RAG
  RAG --> G4
  RAG --> GE
  G4 --> REC[Reconciliador Gemini FLASH]
  GE --> REC
  REC -- Equivalente --> VAL[Validator (Pydantic-AI)]
  REC -- Divergente --> O3[Juiz O3-HIGH]
  O3 --> VAL
  VAL --> OG
```

## 4. Technology Stack

- **Python 3.9** em todos os serviços backend (Runtime: Python 3.9 (pinned); avaliar ≥ 3.10 após 20-Mai-2025).
- **OpenAI Agents SDK** para orquestração.
- **OpenAI Responses API** para RAG.
- **Pydantic-AI** para validar output `ClinicalOpinion` (Note: `medflowai` library currently uses Pydantic, with Pydantic-AI as a potential enhancement for direct LLM output parsing).
- **Redis 7 Sentinel** para cache.
- **OTEL → Prometheus/Grafana** para observabilidade.

## 5. Overall Project Directory Structure

```
{root}/
├── packages/
│   ├── libs/                # Shared, framework-agnostic code
│   │   └── medflowai/      # Agents-SDK orchestrator library (core of MVP)
│   ├── services/           # Micro-APIs, workers, cron jobs
│   │   ├── triage/             # GPT-4.1 triage agent service
│   │   ├── specialists/        # GPT-4.1 & Gemini 2.5 specialist adapters
│   │   ├── reconcil/           # Divergence reconciliation service
│   │   └── arbiter-o3/         # O3-mini judge gateway
│   └── apps/               # Web/mobile UIs
│       └── clinic-web/         # Next.js desktop UI v1
├── infra/                  # Dockerfiles, Terraform, k8s, GitHub Actions
├── docs_project/           # Governance docs (single source of truth)
├── references/             # Third-party docs, style guides, API specs
├── scripts/                # Idempotent CLI tools & data migrations
└── tests/                  # Contract + e2e suites
```

Specific module details (example from `SYSTEM_DESIGN.txt`):

```
packages/
  ...
  ├─ services/
  │   ├─ reconcil/
  │   │   ├─ __init__.py
  │   │   └─ divergence.py          ← motor de divergência (regra-based)
  ...
```

## 6. Module Ownership and Purpose

| Path                      | Purpose                                                           | Owner                      |
| ------------------------- | ----------------------------------------------------------------- | -------------------------- |
| `packages/libs/`          | Reusable domain-agnostic libraries (auth, caching, **medflowai**) | **Platform Engineering**   |
| `packages/services/{svc}` | One deployable micro-service                                      | **Clinical Backend Squad** |
| `packages/apps/{ui}`      | React/Next.js front-end                                           | **UX Guild**               |
| `infra/`                  | IaC (Terraform/k8s) & CI/CD pipelines                             | **DevOps**                 |
| `scripts/`                | One-off migrations, helpers                                       | Any team                   |
| `tests/`                  | Contract + e2e/QA suites                                          | **QA & Testing**           |
| `references/`             | Read-only library docs & guides                                   | Everyone                   |

## 7. Core Library: `medflowai` (`packages/libs/medflowai/`)

This library is the heart of the agent orchestration and execution logic. It has been refactored from legacy code into a modular structure.

### 7.1. Directory Structure of `medflowai`

```
packages/libs/medflowai/
├── __init__.py                 # Main library init, version, high-level exports
├── core/
│   ├── __init__.py             # Core components (BaseAgent, Orchestrator, ContextManager)
│   ├── base_agent.py           # Abstract base class for all agents
│   ├── context_manager.py      # Manages conversational context and state
│   └── orchestrator.py         # Coordinates agent execution flows
├── models/
│   ├── __init__.py             # Data models and type definitions
│   ├── agent_io_models.py      # Standardized input/output Pydantic models for agents
│   └── common_types.py         # Common Pydantic types used across the library
├── adapters/
│   ├── __init__.py             # Adapters for LLMs and other external services
│   ├── base_llm_adapter.py     # Abstract base class for LLM adapters
│   ├── google_gemini_adapter.py # Adapter for Google Gemini models
│   └── openai_adapter.py       # Adapter for OpenAI models (GPT series)
├── agents/
│   ├── __init__.py             # Specific agent implementations
│   ├── mcp_interface_agent.py  # Agent to interact with Medical Consultation Platforms (MCPs)
│   ├── medical_rag_agent.py    # Agent for Retrieval Augmented Generation on medical knowledge
│   ├── triage_agent.py         # Agent for initial query analysis and routing
│   └── verification_agent.py   # Agent for verifying information or claims
└── tools/
    ├── __init__.py             # Tools usable by agents
    ├── base_tool.py            # Abstract base class for tools
    ├── mcp_tool_wrapper.py     # Wrapper for MCP interactions, callable by agents
    └── rag_tool.py             # Tool for Retrieval Augmented Generation from knowledge bases (Implemented with SupabaseVectorStore and OpenAIEmbeddings)
```

### 7.2. Key Components and Their Roles

*   **`core.BaseAgent`**: Defines the common interface and lifecycle for all agents within MedflowAI. Ensures agents are runnable by the `Orchestrator`.
*   **`core.Orchestrator`**: Manages the sequence of agent execution based on predefined flows or dynamic decisions. Handles input/output passing between agents.
*   **`core.ContextManager`**: Maintains the state and history of a conversation or task, providing necessary context to agents.
*   **`models.AgentInput` / `models.AgentOutput`**: Standardized Pydantic models ensuring consistent data exchange between agents and the orchestrator.
*   **`adapters.BaseLLMAdapter` and implementations**: Provide a consistent interface to various LLM providers, abstracting away provider-specific API details.
*   **`agents.*`**: Concrete implementations of specialized agents (e.g., `TriageAgent`, `MedicalRAGAgent`) that perform specific tasks in the MedflowAI workflow.
*   **`tools.BaseTool` and implementations**: Reusable components that agents can leverage to perform actions (e.g., `RAGTool` for knowledge retrieval, `MCPToolWrapper` for external API calls).
*   **`tools.ToolRegistry`**: Allows agents or the orchestrator to discover and access available tools.

### 7.3 DivergenceReviewAgent (New)

`DivergenceReviewAgent` is an LLM-powered reviewer that compares the outputs from two specialist agents and decides whether they are **equivalent** or **divergent**. It returns a JSON with `status` and `justification`, validated via Pydantic-AI.

Workflow snippet:
```
SpecialistA & SpecialistB --> DivergenceReviewAgent --> |equivalent| Orchestrator --> Response
                                                --> |divergent|  O3-HIGH Arbiter --> Response
```

Key points:
* Acts like a senior clinician; no numeric similarity metrics.
* Prompt engineered and version-controlled; retry policy 1-2-4 s.
* Fallback to Gemini on GPT failure.
* Integrated into Orchestrator branching (see T-17).

### 7.4 External Services (Infra)

| Service     | Purpose                         | Access Pattern        |
|-------------|---------------------------------|-----------------------|
| Redis       | Cache (LLM responses, OTEL)     | TCP 6379; `redis-py`  |
| Supabase PG | Case & consultation storage     | `asyncpg`, REST       |
| Supabase Auth (Gotrue) | JWT issuance/verify  | HTTP 9999             |
| OTEL Collector | Trace aggregation            | gRPC 4317             |

All services run locally via `docker-compose.dev.yml` for dev. Production uses managed Supabase + Redis Cloud.

## 8. Dependencies

Key external dependencies for `medflowai` library:

*   Python 3.9+
*   Pydantic (for data modeling and validation)
*   Pydantic-AI (potentially for LLM output parsing directly into Pydantic models)
*   OpenAI SDK (as per project guidelines)
*   google-genai (Gemini adapter). *google-generativeai deprecated and must NOT be used*
*   langchain-openai (for `OpenAIEmbeddings` used in `RAGTool`)
*   langchain-community (for `SupabaseVectorStore` used in `RAGTool`)
*   supabase (Python client for Supabase interactions, used by `SupabaseVectorStore`)
*   (Other specific libraries for tools or core functionalities will be detailed as they are integrated, e.g., for vector databases in RAGTool).

**Environment Variables for RAGTool (Supabase):**
*   `SUPABASE_URL`: The URL of your Supabase project.
*   `SUPABASE_SERVICE_ROLE_KEY`: The service role key for backend access to Supabase.
*   `OPENAI_API_KEY`: Required by `OpenAIEmbeddings` for generating embeddings.

## 9. Data Flow (Example: Basic Query)

1.  User query enters the system (e.g., via `clinic-web` to a service endpoint).
2.  The relevant service (e.g., Triage service) might invoke the `medflowai.Orchestrator`.
3.  `Orchestrator` starts with `TriageAgent`.
4.  `TriageAgent` (using an LLM via an adapter) analyzes the query and recommends the next agent (e.g., `MedicalRAGAgent`).
5.  `Orchestrator` invokes `MedicalRAGAgent`.
6.  `MedicalRAGAgent` uses `RAGTool` to fetch relevant documents from a knowledge base.
7.  `MedicalRAGAgent` then uses an LLM (via an adapter) to synthesize an answer based on the retrieved context.
8.  The output might be passed to `VerificationAgent` if further checks are needed.
9.  The final response is returned through the `Orchestrator` to the calling service and then to the user.

## 10. External Reference Integration (New 2025-05-10)

The `references/` directory is the single source of truth for third-party specifications.
`medflowai` embeds these docs as concrete abstractions:

| Reference Doc | Consumed By | Purpose in `medflowai` |
|---------------|-------------|-------------------------|
| OpenAI_API_Referencia.txt | `adapters.openai_adapter.OpenAIAdapter` & `tools.rag_tool` | Map endpoint params, retry/back-off, error mapping into `UnifiedLLMResponse`. `RAGTool` uses it via `OpenAIEmbeddings`. |
| OpenAI_SDK.txt | `core.*`, `agents.*` | Mirrors Agents SDK patterns; extended with context store, observability and branching orchestration. |
| PyDantiAI_overview.txt / PyDantic_AI_doc.txt | Validation pipeline in adapters & agents | Auto-parsing LLM JSON → Pydantic models; surfacing validation errors. |
| RAG_LANCHAIN.txt | `tools.rag_tool` | Implemented using `langchain_community.vectorstores.SupabaseVectorStore` and `langchain_openai.OpenAIEmbeddings` for retrieval from Supabase/pgvector. |
| guide_OpenAI_Agents.txt | `core.orchestrator` | Governs agent chaining, but `medflowai` adds retry & divergence branches. |
| mcp_server.txt | `tools.mcp_tool_wrapper` | Serializes MCP calls with OTEL tracing. |

### Added Value Beyond References
* Built-in security (PII redaction, TLS enforcement) & compliance hooks (LGPD/HIPAA).
* Observability: OTEL spans for every LLM/tool call; metrics (`divergence_rate`, `cache_hit_rate`).
* Config via environment variables; zero hard-coded secrets.
* Ready-to-use Redis caching & circuit-breaker wrappers.

## 11. Architectural Decision Records (ADRs)

ADR-001: Choice of Pydantic for Data Modeling
ADR-002: Clinical DivergenceReviewAgent
ADR-005: Clinical Divergence Criteria

---
*This document will be updated as the system evolves.*

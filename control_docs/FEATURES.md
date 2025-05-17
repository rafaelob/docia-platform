# MedflowAI Features

This document outlines the current and planned features of the MedflowAI platform. It covers both high-level platform capabilities and detailed features of the core `medflowai` library.

## MedflowAI Platform Features (MVP)
_Source: Legacy FEATURES.txt, Last Updated: 2025-05-10_

### Core MVP Functionality

| ID   | Feature                 | Status |
|------|-------------------------|--------|
| F-01 | Auth OIDC               | ✅     |
| F-02 | Case Intake Form        | 🟡     |
| F-03 | File upload (imagens)   | 🟡     |
| F-04 | RAG OpenAI Responses    | ✅ Implementado (Supabase/pgvector + OpenAI Embeddings) |
| F-05 | Agente Triagem          | 🟡 Placeholder funcional, falta LLM |
| F-06 | Especialista GPT-4.1    | 🟡 Adapters em desenvolvimento (T-14) |
| F-07 | Especialista Gemini 2.5 | 🟡 Adapters em desenvolvimento (T-14) |
| F-08 | Reconciliação           | 🟡 Parcial – Divergence review integrated; arbiter escalation stub in place (T-17) |
| F-09 | Juiz O3-mini            | ⬜️ Stub planejado (T-18) |
| F-13 | Case persistence (Supabase) | 🟡 Setup em andamento (T-22/23) |
| F-14 | DAL Supabase (CRUD cases) | ✅ MVP implementado |
| F-15 | MedicalRAGAgent patient context  | ✅ New field `patient_context` enriches retrieval; unit tests green |
| F-16 | DivergenceReviewAgent   | ✅ Implemented | LLM-based qualitative comparison of two specialist reports. Returns `equivalent` or `divergent` with justification per ADR-005; integrated into medflowai.agents and unit-tested. |

### Clinical Reconciliation (MVP)

- ✅ Dual-LLM opinião clínica
- 🟡 Divergence engine (**DivergenceReviewAgent**, LLM reviewer) → **em implementação T-16**

### Post-MVP Considerations

- F-10 Voice intake
- F-11 Mobile app
- F-12 FHIR sync

---

## Core Library (`medflowai` - `packages/libs/medflowai/`)

**Status: Foundational components refactored and migrated. Ongoing development for enhanced functionalities.**

### 1. Modular Agent Framework
*   **Description**: Provides a robust and extensible framework for building, orchestrating, and managing AI agents. Key components include:
    *   `BaseAgent`: An abstract class defining a common interface for all agents, ensuring consistency in how agents are developed, executed, and managed by the orchestrator.
    *   `Orchestrator`: Manages the lifecycle and execution flow of agents. It can handle sequential, parallel, or conditional execution of agents based on predefined workflows or dynamic logic.
    *   `ContextManager`: Maintains conversational state, history, and shared data across multiple agent interactions within a session.
*   **Status**: Implemented (Core classes migrated and structured).

### 2. Standardized Data Models
*   **Description**: Utilizes Pydantic for defining clear, validated data structures for agent inputs (`AgentInput`), outputs (`AgentOutput`), and common types (`common_types.py`). This ensures data integrity and consistency across the platform and facilitates easier integration between components.
*   **Status**: Implemented (Key I/O models migrated).

### 3. LLM Abstraction Layer
*   **Description**: Features a flexible adapter system (`BaseLLMAdapter`, `OpenAIAdapter`, `GoogleGeminiAdapter`) that decouples the core agent logic from specific LLM provider implementations. This allows for easier integration of new LLMs or switching between models without significant code changes in the agents themselves.
*   **Status**: Implemented (Base adapter and initial OpenAI/Gemini adapters migrated).

### 4. Specialized Agent Implementations (Initial Set)
*   **Description**: A suite of pre-built, specialized agents forms the initial building blocks for MedflowAI workflows:
    *   `TriageAgent`: Analyzes initial user queries to determine intent and route them to the appropriate specialized agent or workflow.
    *   `MedicalRAGAgent`: Performs Retrieval Augmented Generation by querying knowledge bases (via a functional `RAGTool` connected to Supabase with OpenAI Embeddings) and synthesizing information with an LLM to answer clinical questions. **Enhanced: supports `patient_context` for more specific retrieval.**
    *   `MCPInterfaceAgent`: Interacts with external Medical Consultation Platforms (MCPs) or other healthcare IT systems via the `MCPToolWrapper`.
    *   `VerificationAgent`: Verifies claims, facts, or agent-generated content against provided sources or guidelines.
*   **Status**: Implemented (Agents migrated and structured).

### 5. Extensible Tool System
*   **Description**: Allows agents to leverage reusable tools for specific actions:
    *   `BaseTool`: Defines a common interface for all tools.
    *   `RAGTool`: Provides functionality for semantic search and retrieval from a Supabase pgvector knowledge base using OpenAI Embeddings (`langchain_community.vectorstores.SupabaseVectorStore` and `langchain_openai.OpenAIEmbeddings`).
    *   `MCPToolWrapper`: Encapsulates logic for communicating with MCPs.
    *   `ToolRegistry`: Enables discovery and management of available tools for agents or the orchestrator.
*   **Status**: Implemented (Core tool components migrated).

### 6. Configuration and Initialization
*   **Description**: The library and its components are designed to be configurable (e.g., LLM API keys, model names, tool parameters). Proper `__init__.py` files allow for easy importing and namespace management.
*   **Status**: Implemented.

## Planned Features (Examples - To be detailed in ROADMAP.md and TODO.md)

*   **Advanced Orchestration Flows**: Support for more complex agent interaction patterns, including conditional branching, parallel execution with consensus, and error handling/retry logic within the orchestrator.
*   **Enhanced RAG Capabilities**: Integration with specific vector databases, advanced document chunking and indexing strategies, and hybrid search for `RAGTool`.
*   **Clinical Divergence Engine**: Logic to detect and quantify differences in outputs from multiple specialist agents.
*   **O3 Arbiter Integration**: Ability for the system to invoke an O3-mini model (or similar) to act as an arbiter in cases of significant clinical divergence.
*   **Comprehensive PII Redaction**: Robust mechanisms for identifying and redacting PII from data flowing through agents and tools.
*   **Full Pydantic-AI Integration**: Leveraging Pydantic-AI for direct parsing and validation of LLM outputs against Pydantic models.
*   **Observability & Logging**: Structured logging throughout the library for integration with OTEL and monitoring systems.
*   **Asynchronous Operations**: Full support for asynchronous operations in agents and tools for improved performance.

---
*This document reflects the feature set as of the last update and will evolve with the project.*

---
trigger: model_decision
description: Docs in references cover the OpenAI Agents SDK, API responses powering MedflowAI, use of PydanticAI, LangChain's RAG module, and best practices for building and orchestrating agents with OpenAIQ, which must be followed.
---

# How to use Files in references Folder

## Overview

The `references/` directory serves as a centralized repository for critical third-party documentation, API specifications, and implementation guides. These documents are considered **read-only** and represent the authoritative external knowledge source for the project.

## Available Reference Documents

| Document | Purpose |
|----------|---------|
| `OpenAI_API_Referencia.txt` | Comprehensive OpenAI API specifications with endpoints, parameters, and usage examples |
| `OpenAI_SDK.txt` | Official SDK documentation with implementation patterns and method references |
| `PROJECT_OVERVIEW.txt` | External project context and integration specifications |
| `PyDantiAI_overview.txt` | High-level introduction to PyDantic-AI capabilities and architecture |
| `PyDantic_AI_doc.txt` | Detailed implementation guide for PyDantic-AI models and validation |
| `RAG_LANCHAIN.txt` | LangChain-based Retrieval Augmented Generation patterns and best practices |
| `guide_OpenAI_Agents.txt` | Detailed guide for OpenAI Agents SDK implementation and orchestration |
| `mcp_server.txt` | Model Context Protocol server integration specifications |

## When to Consult References

1. **Pre-Implementation Research**: Before working on a new feature or component, consult the relevant reference documents to ensure alignment with third-party specifications.

2. **During Design Reviews**: Reference these documents during architecture and design discussions to validate approach against vendor recommendations.

3. **Troubleshooting**: When investigating unexpected behavior in integrations, consult reference materials to verify correct implementation.

4. **Knowledge Transfer**: Direct new team members to these documents as part of onboarding to establish shared understanding.

## Best Practices

### Linking to References

When documenting code or architectural decisions, reference these documents using relative paths:

```markdown
For implementation details, see [OpenAI Agents Guide](../references/guide_OpenAI_Agents.txt).
```

### Documentation Hierarchy

1. **External References** (`references/`) - Immutable third-party documentation
2. **System Design** (`control_docs/SYSTEM_DESIGN.md`) - Project-specific architecture decisions
3. **Implementation Documentation** (code comments, README files) - Practical guidance

### Version Management

When new versions of third-party documentation become available:

1. Add new version with suffix (e.g., `OpenAI_SDK_v2.txt`)
2. Update `CHANGELOG.md` to note availability of new reference
3. Do not delete previous versions until all dependent code has been migrated

## Reference-Specific Usage Guidelines

### OpenAI Documentation

`OpenAI_API_Referencia.txt` and `OpenAI_SDK.txt` should be consulted when:
- Implementing new AI capabilities
- Troubleshooting API responses
- Optimizing prompt engineering
- Updating dependency versions

### PyDantic-AI Documentation

`PyDantiAI_overview.txt` and `PyDantic_AI_doc.txt` are essential for:
- Data model definition
- Input validation
- Schema evolution
- Type safety implementation

### RAG and LangChain

`RAG_LANCHAIN.txt` provides guidance for:
- Implementing retrieval-augmented generation
- Vector database integration
- Context window optimization
- Prompt construction with retrieved content

### Agent Orchestration

`guide_OpenAI_Agents.txt` is critical for:
- Agent workflow design
- Tool definition and integration
- Agent communication patterns
- Error handling and fallback strategies

## Final Notes

Remember that these reference documents are read-only and represent external knowledge. Any project-specific adaptations or modifications should be documented in `SYSTEM_DESIGN.md` with clear rationale for deviation from standard practices.

When in doubt, reference documents take precedence over internal documentation unless explicitly overridden with documented reasoning.

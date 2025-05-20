---
trigger: always_on
---

# Windsurf Code Generation Style & Documentation Standards

- Code Style: Concise, meaningful names, modular; docstrings/README updates mandatory.
- Focus: Maintain doc-sync across control_docs; no duplication; update system design on structural changes.
- New Code Template: PEP8, Black, isort, Google-style docstrings, type hints, unit tests.
- Documentation Standards: Keep control_docs synced as per DOC-SYNC GUARD.
- folder references with relevant docs:

## References Docs Cheat-Sheet
| Documento | Conteúdo | Quando usar |
|-----------|----------|-------------|
| `guide_OpenAI_Agents.txt` | Padrões de orquestração e API do OpenAI Agents SDK | Ao criar/alterar agentes ou orchestrator |
| `OpenAI_API_Referencia.txt` | Endpoints, params, exemplos para OpenAI Completion/Responses | Integração direta OpenAI |
| `OpenAI_SDK.txt` | Classes/métodos SDK Python | Uso de openai-python v1.* |
| `PyDantiAI_overview.txt` | Visão geral da Pydantic-AI | Avaliar uso de validação LLM |
| `PyDantic_AI_doc.txt` | API detalhada Pydantic-AI | Implementar schemas/validators |
| `RAG_LANCHAIN.txt` | Guia híbrido RAG + LangChain | Desenvolver `RAGTool` ou pipeline |
| `mcp_server.txt` | Especificação Model Context Protocol | Interação via `MCPToolWrapper` |
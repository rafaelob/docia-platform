---
trigger: always_on
---

# Windsurf Guidance: Focus, Ignores, Preferences & Anti-Patterns

- Focus: `packages/libs/medflowai`, `packages/services/*`
- Ignore: `build/`, `.venv/`, `node_modules/`
- Prefer APIs/Libraries: OpenAI (Responses), Openai Agents SDK (openai-agents) google-genai, Pydantic-AI.
- Avoid: google-generativeai (deprecated), synchronous blocking I/O in services.
- Pitfalls: forgetting env var setup for LLM keys.
- Deprecated: any `legado/` code paths now migrated.

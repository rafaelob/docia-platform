---
trigger: always_on
---

# Testing, Error Handling, and Logging Practices

- Testing: **pytest** with ≥85% coverage, factory-boy fixtures; React Testing Library for Next.js.
- Strategy: TDD for agents & critical services; contract tests in `tests/integration` using Supabase test DB.
- Always read and update TEST.md inside 'control_docs' folder in root to guide you about the tests.
- Error Handling: Specific exception classes per domain; return Pydantic error envelopes.
- Logging: Structured JSON logs via `structlog`; OTEL tracing exporter to collector on `localhost:4317`.

# ADR-005: DivergenceReviewAgent – LLM-based Clinical Divergence Analysis

Date: 2025-05-10  
Status: Proposed  
Deciders: Clinical Backend Squad, AI Governance Board

## Context
MedflowAI entrega segundas opiniões com dois LLMs (GPT-4.1, Gemini 2.5). Precisamos identificar quando os laudos dos especialistas divergem clinicamente. Abordagens numéricas (cosine, Δ-grade) falharam em nuance médica e explicabilidade.

## Decision
Adotar **`DivergenceReviewAgent`**, um agente LLM (GPT-4.1 primário, Gemini fallback) que age como revisora clínica.
Recebe dois relatórios e devolve JSON:

```jsonc
{
  "status": "equivalent" | "divergent",
  "justification": "<rationale>"
}
```

Prompt (resumido):
```
You are an experienced physician. Compare Report A and Report B.
If recommendations are compatible, return {"status":"equivalent", "justification":"…"}
Else return {"status":"divergent", "justification":"…"}
```

## Consequences
* Remove dependência de métricas numéricas.  
* Explicabilidade via `justification`.  
* Validado com Pydantic-AI; retry exponencial 1-2-4 s (3 tentativas).  
* Se `divergent`, Orchestrator encaminha ao **O3-mini Arbiter**.

## Alternatives Considered
1. Embedding cosine – sem nuance.  
2. Regra ICD-10 – alta taxa de falso-negativo.

## Links
* SYSTEM_DESIGN.md §7.3  
* SECURITY.md – PII redaction antes do prompt  
* [guide_OpenAI_Agents.txt](../references/guide_OpenAI_Agents.txt)

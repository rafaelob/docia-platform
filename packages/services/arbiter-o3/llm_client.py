"""LLM comparison logic for O3-mini Arbiter.

This module isolates the logic that calls external LLMs (via medflowai
adapters) to compare two specialist reports and decide which one (if any) is
preferable or how to merge them.
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from typing import Literal

from medflowai.adapters.openai_adapter import OpenAIAdapter
from medflowai.adapters.gemini_adapter import GeminiAdapter  # type: ignore

logger = logging.getLogger(__name__)


class Verdict(str, Enum):
    specialist_a = "a"
    specialist_b = "b"
    combine = "combine"
    cannot_decide = "cannot_decide"


async def compare_reports(
    report_a: str,
    report_b: str,
    *,
    justification: str | None = None,
    model_pref: Literal["openai", "gemini", "auto"] | None = None,
) -> tuple[Verdict, str]:
    """Use LLM to compare two reports and return verdict + rationale."""

    # Choose adapter based on preference/env
    pref = model_pref or os.getenv("ARBITER_LLM_PREF", "auto")
    adapter: OpenAIAdapter | GeminiAdapter

    if pref == "gemini":
        adapter = GeminiAdapter()
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
    elif pref == "openai":
        adapter = OpenAIAdapter()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    else:  # auto: try OpenAI first
        try:
            adapter = OpenAIAdapter()
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            _ = adapter  # noqa: PI113
        except Exception:  # openai key missing etc.
            adapter = GeminiAdapter()  # type: ignore[assignment]
            model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")

    system_prompt = (
        "Você é um juiz clínico sênior. Receberá dois laudos de especialistas "
        "e deve decidir qual recomendação seguir ou se deve combiná-las. "
        "Responda em JSON no formato {\"verdict\": <a|b|combine|cannot_decide>, "
        "\"rationale\": <string>} em português claro."
    )

    user_prompt = (
        f"### Relatório A\n{report_a}\n\n### Relatório B\n{report_b}\n\n"
        f"Justificativa de divergência fornecida: {justification or 'N/A'}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    resp = await adapter.chat_completion(messages=messages, model_name=model, temperature=0.2)

    if resp.error:
        logger.error("LLM arbiter error: %s", resp.error)
        return Verdict.cannot_decide, f"Erro no LLM: {resp.error}"

    # Try parse JSON
    import json  # local import to avoid dependency at top-level

    try:
        parsed = json.loads(resp.content)
        verdict = Verdict(parsed.get("verdict", "cannot_decide"))
        rationale = parsed.get("rationale", "Não foi fornecida justificativa.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao parsear resposta JSON: %s", exc)
        verdict = Verdict.cannot_decide
        rationale = resp.content or str(exc)

    return verdict, rationale

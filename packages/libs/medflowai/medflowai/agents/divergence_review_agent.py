"""Divergence Review Agent for MedflowAI.

Compares two specialist LLM reports and classifies them as **equivalent** or **divergent**
according to ADR-005. Uses an LLM (GPT-4.1 by default via `OpenAIAdapter`, Gemini as
needed) and returns a JSON-structured verdict with justification.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List, Literal, Optional, Type

from pydantic import BaseModel, Field, PrivateAttr, ValidationError

from ..core.base_agent import BaseAgent, ContextManager
from ..models.agent_io_models import GenericInput, GenericOutput
from ..adapters.openai_adapter import OpenAIAdapter
from ..models.common_types import UnifiedLLMResponse

# ---------------------------------------------------------------------------
# Pydantic I/O Schemas
# ---------------------------------------------------------------------------

class DivergenceReviewAgentInput(BaseModel):
    """Input required by :class:`DivergenceReviewAgent`."""

    report_a: str = Field(..., description="Content of Specialist Report A.")
    report_b: str = Field(..., description="Content of Specialist Report B.")
    max_retries: int = Field(3, description="Maximum number of retries on LLM error.")
    retry_backoff_base_seconds: float = Field(
        1.0, description="Initial back-off delay in seconds – doubled each retry."
    )


class DivergenceReviewAgentOutput(GenericOutput):
    """Classification result for two reports."""

    response: Optional[str] = None  # Override base: allow None on error paths
    status: Optional[Literal["equivalent", "divergent"]] = Field(
        None, description="Outcome of comparison."
    )
    justification: Optional[str] = Field(
        None, description="LLM rationale explaining the decision."
    )
    error_message: Optional[str] = Field(None, description="Error detail, if any.")

    # Convenience aliases for legacy tests
    @property
    def verdict(self) -> Optional[str]:  # noqa: D401 – property alias
        """Alias for :pyattr:`status`."""
        return self.status


# ---------------------------------------------------------------------------
# Agent Implementation
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = (
    "You are an experienced physician. Compare the two clinical reports provided.\n"
    "If the recommendations and conclusions are compatible, respond strictly with a JSON object: "
    "{{\"status\": \"equivalent\", \"justification\": \"<SHORT_RATIONALE>\"}}.\n"
    "If they conflict clinically, respond strictly with a JSON object: "
    "{{\"status\": \"divergent\", \"justification\": \"<SHORT_RATIONALE>\"}}.\n"
    "Do NOT add any keys. The JSON MUST be valid.\n"
    "\nREPORT A:\n{report_a}\n\nREPORT B:\n{report_b}\n"
)


class DivergenceReviewAgent(BaseAgent):
    """LLM-based divergence classifier between two specialist reports."""

    agent_name: str = "DivergenceReviewAgent"
    description: str = "Classifies specialist outputs as clinically equivalent or divergent."

    # Use our specific schemas
    input_schema: Type[BaseModel] = DivergenceReviewAgentInput
    output_schema: Type[BaseModel] = DivergenceReviewAgentOutput

    # Default model
    default_model_name: str = "gpt-4o"  # or gpt-4-turbo if unavailable

    # Internal attributes
    _logger: logging.Logger = PrivateAttr()

    def __init__(self, llm_adapter: Optional[OpenAIAdapter] = None, **data: Any):
        if llm_adapter is None:
            llm_adapter = OpenAIAdapter()
        super().__init__(llm_adapter=llm_adapter, prompt_template=_PROMPT_TEMPLATE, **data)  # type: ignore[arg-type]
        self._logger = logging.getLogger(__name__)
        if not self.model_name:
            self.model_name = self.default_model_name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def run(
        self,
        input_data: DivergenceReviewAgentInput,
        context: Optional[ContextManager] = None,
    ) -> DivergenceReviewAgentOutput:
        """Compare `report_a` and `report_b` using an LLM.

        Implements exponential-back-off retry (1-2-4 s) per ADR-005.
        """
        retries_remaining = input_data.max_retries
        backoff = input_data.retry_backoff_base_seconds
        last_llm_response: Optional[UnifiedLLMResponse] = None

        # Prepare prompt messages
        system_msg = {"role": "system", "content": "You are an assistant that speaks JSON only."}
        user_msg = {
            "role": "user",
            "content": self.prompt_template.format(
                report_a=input_data.report_a.strip(), report_b=input_data.report_b.strip()
            ),
        }
        messages: List[Dict[str, str]] = [system_msg, user_msg]

        while retries_remaining > 0:
            self._logger.debug(
                "Calling LLM for divergence review. Retries remaining: %s", retries_remaining
            )
            last_llm_response = await self.llm_adapter.chat_completion(
                messages=messages,
                model_name=self.model_name or self.default_model_name,
                temperature=0.0,
            )
            if last_llm_response.error:
                self._logger.warning(
                    "LLM returned error: %s. Waiting %.1fs before retry...",
                    last_llm_response.error,
                    backoff,
                )
                await asyncio.sleep(backoff)
                retries_remaining -= 1
                backoff *= 2
                continue

            raw_content = (last_llm_response.content or "").strip()
            try:
                parsed: Dict[str, Any] = json.loads(raw_content)
                status_val = parsed.get("status")
                justification_val = parsed.get("justification")
                if status_val not in {"equivalent", "divergent"}:
                    raise ValueError("Invalid or missing 'status'.")
                return DivergenceReviewAgentOutput(
                    response=justification_val,
                    status=status_val,  # type: ignore[arg-type]
                    justification=justification_val,
                    error_message=None,
                )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # Treat as format error, retry
                self._logger.warning(
                    "LLM response format error: %s. Raw content: %s", e, raw_content[:200]
                )
                await asyncio.sleep(backoff)
                retries_remaining -= 1
                backoff *= 2
                continue

        # Failed after retries
        err_msg = (
            last_llm_response.error
            if last_llm_response and last_llm_response.error
            else "Failed to obtain valid divergence verdict after retries."
        )
        return DivergenceReviewAgentOutput(
            response=None,
            status=None,
            justification=None,
            error_message=err_msg,
        )

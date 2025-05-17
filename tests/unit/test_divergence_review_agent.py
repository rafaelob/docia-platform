"""Unit tests for DivergenceReviewAgent."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from medflowai.agents.divergence_review_agent import (
    DivergenceReviewAgent,
    DivergenceReviewAgentInput,
    DivergenceReviewAgentOutput,
)
from medflowai.models.common_types import UnifiedLLMResponse


@pytest.mark.asyncio
async def test_divergence_review_equivalent():
    """LLM returns valid equivalent verdict."""
    mocked_llm_adapter = AsyncMock()
    mocked_llm_adapter.chat_completion = AsyncMock(
        return_value=UnifiedLLMResponse(
            content='{"status": "equivalent", "justification": "Both reports recommend the same treatment."}',
            error=None,
        )
    )

    with patch(
        "medflowai.agents.divergence_review_agent.OpenAIAdapter", return_value=mocked_llm_adapter
    ):
        agent = DivergenceReviewAgent()
        input_payload = DivergenceReviewAgentInput(
            report_a="Report A content.", report_b="Report B content."
        )
        output: DivergenceReviewAgentOutput = await agent.run(input_payload)

    assert output.status == "equivalent"
    assert output.justification.startswith("Both reports")
    assert output.error is None


@pytest.mark.asyncio
async def test_divergence_review_format_error_then_success():
    """First LLM call returns malformed JSON then succeeds."""
    malformed_resp = UnifiedLLMResponse(content="NOT JSON", error=None)
    good_resp = UnifiedLLMResponse(
        content='{"status": "divergent", "justification": "Different recommendations."}', error=None
    )

    mocked_llm_adapter = AsyncMock()
    mocked_llm_adapter.chat_completion = AsyncMock(side_effect=[malformed_resp, good_resp])

    with patch(
        "medflowai.agents.divergence_review_agent.OpenAIAdapter", return_value=mocked_llm_adapter
    ):
        agent = DivergenceReviewAgent()
        input_payload = DivergenceReviewAgentInput(
            report_a="A.", report_b="B.", max_retries=2, retry_backoff_base_seconds=0
        )
        output = await agent.run(input_payload)  # type: ignore[arg-type]

    assert output.status == "divergent"
    assert output.error is None


@pytest.mark.asyncio
async def test_divergence_review_all_failures():
    """LLM fails all retries; agent returns error."""
    failure_response = UnifiedLLMResponse(content=None, error="Rate limit")

    mocked_llm_adapter = AsyncMock()
    mocked_llm_adapter.chat_completion = AsyncMock(return_value=failure_response)

    with patch(
        "medflowai.agents.divergence_review_agent.OpenAIAdapter", return_value=mocked_llm_adapter
    ):
        agent = DivergenceReviewAgent()
        input_payload = DivergenceReviewAgentInput(
            report_a="A.", report_b="B.", max_retries=2, retry_backoff_base_seconds=0
        )
        output = await agent.run(input_payload)  # type: ignore[arg-type]

    assert output.status is None
    assert output.error == "Rate limit"

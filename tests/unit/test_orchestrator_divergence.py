"""Test Orchestrator divergence flow integration."""
import pytest
from unittest.mock import AsyncMock

from medflowai.core.orchestrator import OrchestratorPrincipal
from medflowai.core.context_manager import InMemoryContextStore
from medflowai.agents.divergence_review_agent import DivergenceReviewAgentOutput
from medflowai.models.common_types import UnifiedLLMResponse
from medflowai.adapters.openai_adapter import OpenAIAdapter


@pytest.mark.asyncio
async def test_orchestrator_review_divergence_equivalent():
    """Orchestrator should surface equivalent verdict."""
    dummy_llm = AsyncMock(spec=OpenAIAdapter)
    dummy_llm.chat_completion = AsyncMock(
        return_value=UnifiedLLMResponse(
            content='{"status": "equivalent", "justification": "Same rec."}',
            error=None,
        )
    )

    orch = OrchestratorPrincipal(
        llm_adapter_map={"default": dummy_llm},
        agent_map={},
        tool_registry=None,  # type: ignore[arg-type]
        context_store_instance=InMemoryContextStore(),
        default_llm_adapter_name="default",
    )

    out: DivergenceReviewAgentOutput = await orch.review_divergence("A", "B")
    assert out.status == "equivalent"


@pytest.mark.asyncio
async def test_orchestrator_review_divergence_divergent():
    """If divergent, orchestrator helper should return correct status."""
    dummy_llm = AsyncMock(spec=OpenAIAdapter)
    dummy_llm.chat_completion = AsyncMock(
        return_value=UnifiedLLMResponse(
            content='{"status": "divergent", "justification": "Mismatch."}',
            error=None,
        )
    )

    orch = OrchestratorPrincipal(
        llm_adapter_map={"default": dummy_llm},
        agent_map={},
        tool_registry=None,  # type: ignore[arg-type]
        context_store_instance=InMemoryContextStore(),
        default_llm_adapter_name="default",
    )

    out = await orch.review_divergence("A", "B")
    assert out.status == "divergent"

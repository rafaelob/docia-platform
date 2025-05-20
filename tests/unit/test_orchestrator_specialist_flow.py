"""Tests for OrchestratorPrincipal.process_specialist_outputs."""
import pytest
from unittest.mock import AsyncMock, patch

from medflowai.core.orchestrator import OrchestratorPrincipal
from medflowai.core.context_manager import InMemoryContextStore
from medflowai.models.agent_io_models import GenericOutput
from medflowai.agents.divergence_review_agent import DivergenceReviewAgentOutput
from medflowai.adapters.openai_adapter import OpenAIAdapter


@pytest.mark.asyncio
async def test_process_specialists_equivalent():
    """When specialists agree, orchestrator should not escalate."""
    # Mock LLM adapter (not used in this path)
    dummy_llm = AsyncMock(spec=OpenAIAdapter)

    orch = OrchestratorPrincipal(
        llm_adapter_map={"default": dummy_llm},
        agent_map={},
        tool_registry=None,  # type: ignore[arg-type]
        context_store_instance=InMemoryContextStore(),
        default_llm_adapter_name="default",
    )

    with patch.object(
        orch,
        "review_divergence",
        new=AsyncMock(
            return_value=DivergenceReviewAgentOutput(
                status="equivalent",
                justification="Same findings.",
            )
        ),
    ):
        out: GenericOutput = await orch.process_specialist_outputs("A", "B")
        assert out.response.startswith("Specialist recommendations are equivalent")


@pytest.mark.asyncio
async def test_process_specialists_divergent():
    """When specialists diverge, orchestrator escalates to arbiter stub."""
    dummy_llm = AsyncMock(spec=OpenAIAdapter)

    orch = OrchestratorPrincipal(
        llm_adapter_map={"default": dummy_llm},
        agent_map={},
        tool_registry=None,  # type: ignore[arg-type]
        context_store_instance=InMemoryContextStore(),
        default_llm_adapter_name="default",
    )

    with patch.object(
        orch,
        "review_divergence",
        new=AsyncMock(
            return_value=DivergenceReviewAgentOutput(
                status="divergent",
                justification="Contradictory recs.",
            )
        ),
    ):
        out = await orch.process_specialist_outputs("A", "B")
        assert "Veredicto" in out.response

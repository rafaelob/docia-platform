"""
Core Orchestrator for MedflowAI.

This module defines the OrchestratorPrincipal class responsible for managing 
the flow of execution between different AI agents, handling context, and 
coordinating tool usage within the MedflowAI library.
"""

import uuid
from typing import Dict, Any, Optional, Type, List
import asyncio
from jinja2 import Template

from ..adapters.base_llm_adapter import BaseLLMAdapter  # Adjusted path
from .base_agent import BaseAgent  # Correct path
from ..tools.tool_registry import ToolRegistry  # Adjusted path
from .context_manager import (
    ContextManager,
    InMemoryContextStore,
    BaseContextStore,
)
from ..models.agent_io_models import GenericInput, GenericOutput  # Correct path
from ..models.common_types import UnifiedLLMResponse  # Correct path
from ..agents.divergence_review_agent import (
    DivergenceReviewAgent,
    DivergenceReviewAgentInput,
    DivergenceReviewAgentOutput,
)
from medflowai.services_proxy.arbiter_client import (
    send_to_arbiter,
    ArbiterRequest,
    ArbiterResponse,
)
from .retry_utils import async_retry
from .orchestration_config import OrchestrationConfig, load_orchestration_config

class OrchestratorPrincipal:
    """
    Manages the overall workflow and interaction between various agents and services.
    """
    def __init__(
        self,
        llm_adapter_map: Dict[str, BaseLLMAdapter],
        agent_map: Dict[str, BaseAgent],
        tool_registry: ToolRegistry,
        context_store_instance: BaseContextStore,  # Expect an instance now
        orchestration_config: OrchestrationConfig | None = None,
        default_llm_adapter_name: Optional[str] = None,
        default_agent_name: Optional[str] = None
    ):
        """
        Initializes the OrchestratorPrincipal.

        Args:
            llm_adapter_map (dict): A map of LLM adapter instances, keyed by a unique name.
            agent_map (dict): A map of agent instances, keyed by agent name.
            tool_registry (ToolRegistry): An instance of the ToolRegistry.
            context_store_instance (BaseContextStore): An instance of a context store (e.g., InMemoryContextStore).
            orchestration_config (OrchestrationConfig | None): Optional orchestration configuration.
            default_llm_adapter_name (Optional[str]): Name of the default LLM adapter to use if not specified.
            default_agent_name (Optional[str]): Name of the default agent to use if not specified (e.g., a triage agent).
        """
        self.llm_adapter_map = llm_adapter_map
        self.agent_map = agent_map
        self.tool_registry = tool_registry
        self.context_store_instance = context_store_instance
        self.default_llm_adapter_name = default_llm_adapter_name
        self.default_agent_name = default_agent_name

        if self.default_llm_adapter_name and self.default_llm_adapter_name not in self.llm_adapter_map:
            raise ValueError(f"Default LLM adapter {self.default_llm_adapter_name} not found in llm_adapter_map.")
        if self.default_agent_name and self.default_agent_name not in self.agent_map:
            raise ValueError(f"Default agent {self.default_agent_name} not found in agent_map.")
        
        # print("OrchestratorPrincipal initialized with shared context store.")

        # Load or attach orchestration configuration for future dynamic flows.
        # Currently used for metadata only; upcoming tasks (T-39/T-42) will
        # execute the flow based on this model.
        self.orchestration_config: OrchestrationConfig = (
            orchestration_config or load_orchestration_config()
        )
        self._flow_context: dict[str, Any] = {}

    def _get_context_manager_for_session(self, session_id: str) -> ContextManager:
        """
        Retrieves or creates a ContextManager for a given session ID, using the shared store.
        """
        if not session_id:
            session_id = f"default_session_{str(uuid.uuid4())}"
            # print(f"Warning: No session_id provided. Using temporary session: {session_id}")
        return ContextManager(session_id=session_id, store=self.context_store_instance)

    async def _execute_step(self, step, user_query: str, ctx_mgr: ContextManager):
        """Executes a single step (agent/tool or parallel)."""
        # Check condition
        if getattr(step, "condition", None):
            condition_val = bool(Template(step.condition).render(**self._flow_context))
            if not condition_val:
                return
        if step.type in ("agent", "tool"):
            await self._run_single(step, user_query, ctx_mgr)
        elif step.type == "parallel":
            await self._run_parallel(step, user_query, ctx_mgr)

    async def _run_single(self, step, user_query: str, ctx_mgr: ContextManager):
        name = step.name
        if step.type == "agent":
            agent = self.agent_map.get(name)
            if not agent:
                raise ValueError(f"Agent {name} not found")
            input_model = agent.input_schema(query=user_query)
            try:
                output: GenericOutput = await agent.run(input_model, ctx_mgr)
                self._flow_context[f"{name}_output"] = output.response
            except Exception as exc:
                if step.on_error == "retry":
                    output = await async_retry(lambda: agent.run(input_model, ctx_mgr))
                    self._flow_context[f"{name}_output"] = output.response
                elif step.on_error == "skip":
                    return
                else:
                    raise exc
        else:
            tool_cls = self.tool_registry.get(name)
            if not tool_cls:
                raise ValueError(f"Tool {name} not registered")
            tool = tool_cls()
            try:
                result = await tool.execute(user_query, ctx_mgr)
                self._flow_context[f"{name}_output"] = result
            except Exception as exc:
                if step.on_error == "retry":
                    result = await async_retry(lambda: tool.execute(user_query, ctx_mgr))
                    self._flow_context[f"{name}_output"] = result
                elif step.on_error == "skip":
                    return
                else:
                    raise exc

    async def _run_parallel(self, step, user_query: str, ctx_mgr: ContextManager):
        tasks = []
        for sub in step.agents:
            tasks.append(self._run_single(sub, user_query, ctx_mgr))
        await asyncio.gather(*tasks, return_exceptions=False)

    async def _execute_flow(self, user_query: str, ctx_mgr: ContextManager):
        for step in self.orchestration_config.flow:
            await self._execute_step(step, user_query, ctx_mgr)

    async def process_query(
        self,
        user_query: str,
        session_id: Optional[str] = None,
        target_agent_name: Optional[str] = None,
    ) -> Any: # Should be BaseModel, ideally GenericOutput or a specific agent's output model
        """
        Processes a user query by routing it to the appropriate agent or a default sequence.

        Args:
            user_query (str): The query from the user.
            session_id (str, optional): The ID of the current session. If None, a temporary one is used.
            target_agent_name (str, optional): The specific agent to route the query to. 
                                        If None, the default_agent_name (if set) or a basic logic applies.

        Returns:
            Any: The result from the agent execution (typically a Pydantic model instance like GenericOutput).
        """
        # print(f"Orchestrator: Processing query: {user_query[:50]}... for session {session_id} with target agent {target_agent_name}")
        
        current_session_id = session_id or f"temp_session_{str(uuid.uuid4())}"
        context_manager = self._get_context_manager_for_session(current_session_id)

        context_manager.add_message(role="user", content=user_query)

        agent_to_run_name = target_agent_name or self.default_agent_name
        if not agent_to_run_name:
            if self.agent_map:
                agent_to_run_name = next(iter(self.agent_map))
                # print(f"Warning: No target or default agent specified. Using first available: {agent_to_run_name}")
            else:
                # print("Error: No agents available in the orchestrator.")
                return GenericOutput(response="Orchestrator has no agents configured.", error_message="No agents available.")

        selected_agent = self.agent_map.get(agent_to_run_name)
        if not selected_agent:
            # print(f"Error: Agent {agent_to_run_name} not found.")
            return GenericOutput(response=f"Agent {agent_to_run_name} not found.", error_message=f"Agent {agent_to_run_name} not found.")

        agent_input_data = selected_agent.input_schema(query=user_query, session_id=current_session_id)
        
        try:
            # print(f"Orchestrator: Running agent {selected_agent.agent_name}...")
            agent_response_model = await async_retry(
                selected_agent.run,
                agent_input_data,
                context_manager,
                retries=2,
            )
            # print(f"Orchestrator: Agent {selected_agent.agent_name} finished.")

            if hasattr(agent_response_model, "response") and isinstance(agent_response_model.response, str):
                context_manager.add_message(role="assistant", content=agent_response_model.response)
            elif isinstance(agent_response_model, UnifiedLLMResponse) and agent_response_model.content:
                 context_manager.add_message(role="assistant", content=agent_response_model.content)
            else:
                # print(f"Warning: Agent response for {selected_agent.agent_name} did not have a standard 'response' string attribute to log.")
                pass

            return agent_response_model
        
        except Exception as e:
            # print(f"Error during agent {selected_agent.agent_name} execution: {e}")
            import traceback
            traceback.print_exc()
            error_content = f"Error processing your request with agent {selected_agent.agent_name}: {str(e)}"
            context_manager.add_message(role="assistant", content=error_content)
            return GenericOutput(response="An error occurred while processing your request.", error_message=str(e))

        # If orchestration config has flow definition, execute it instead of default agent
        if self.orchestration_config and self.orchestration_config.flow:
            await self._execute_flow(user_query, context_manager)
            # Return last agent output if available
            return self._flow_context.get("last_output", "")

    async def review_divergence(
        self,
        report_a: str,
        report_b: str,
        session_id: Optional[str] = None,
    ) -> DivergenceReviewAgentOutput:
        """Runs DivergenceReviewAgent to determine if two specialist reports diverge.

        This helper wraps the DivergenceReviewAgent execution and shares the same
        context store so that the divergence rationale is persisted in the
        conversation history. It does *not* handle downstream escalation (e.g.,
        O3-mini Arbiter) – the caller should react to `status == 'divergent'`.
        """
        current_session_id = session_id or f"divergence_session_{uuid.uuid4()}"
        context_manager = self._get_context_manager_for_session(current_session_id)

        # Reuse existing instance from agent_map if provided; otherwise create lightweight one.
        divergence_agent: DivergenceReviewAgent
        if "DivergenceReviewAgent" in self.agent_map:
            divergence_agent = self.agent_map["DivergenceReviewAgent"]  # type: ignore[assignment]
        else:
            default_llm = self.llm_adapter_map.get(self.default_llm_adapter_name) if self.default_llm_adapter_name else None
            divergence_agent = DivergenceReviewAgent(llm_adapter=default_llm or next(iter(self.llm_adapter_map.values())))  # type: ignore[arg-type]

        input_payload = DivergenceReviewAgentInput(report_a=report_a, report_b=report_b)
        agent_response = await async_retry(
            divergence_agent.run,
            input_payload,
            context_manager,
            retries=2,
        )

        # Persist assistant message if we have a textual response/justification
        if agent_response.justification:
            context_manager.add_message(role="assistant", content=agent_response.justification)

        return agent_response

    async def _escalate_to_arbiter(
        self,
        report_a: str,
        report_b: str,
        divergence_output: DivergenceReviewAgentOutput,
        session_id: Optional[str] = None,
    ) -> GenericOutput:
        """Placeholder escalation to the O3-mini arbiter service.

        In MVP, this stub simply packages the divergence info. In production it
        will perform an HTTP call or enqueue a message for the Arbiter
        micro-service. Having a dedicated method allows easy mocking in unit
        tests.
        """
        # Build request object and call micro-service (async HTTP)
        request = ArbiterRequest(
            report_a=report_a,
            report_b=report_b,
            justification=divergence_output.justification,
            session_id=session_id,
        )
        arb_resp: ArbiterResponse = await async_retry(send_to_arbiter, request, retries=2)

        summary = (
            f"[ARB] Veredicto: {arb_resp.verdict}. Racional: {arb_resp.rationale}"
        )

        return GenericOutput(response=summary)

    async def process_specialist_outputs(
        self,
        report_a: str,
        report_b: str,
        session_id: Optional[str] = None,
    ) -> GenericOutput:
        """High-level helper: runs divergence review and escalates if needed."""
        divergence_result = await self.review_divergence(report_a, report_b, session_id)

        current_session_id = session_id or "default"

        # If divergent, escalate
        if divergence_result.status == "divergent":
            return await self._escalate_to_arbiter(
                report_a, report_b, divergence_result, current_session_id
            )

        # If equivalent, produce unified response
        return GenericOutput(
            response="Specialist recommendations are equivalent.",
            error_message=None,
        )

if __name__ == "__main__":
    print("MedflowAI OrchestratorPrincipal module (now in core package).")
    # This main block demonstrates conceptual setup. For actual testing, ensure all dependencies
    # (BaseLLMAdapter, BaseAgent, ToolRegistry, context stores, models) are correctly imported
    # and available in the new medflowai package structure.

    # Example (conceptual, assuming necessary classes are defined or imported):
    # import asyncio
    # async def run_orchestrator_test():
    #     # 1. Create a context store instance
    #     store = InMemoryContextStore()
        
    #     # 2. Mock/Create LLM Adapters
    #     class MockLLMAdapter(BaseLLMAdapter):
    #         async def chat_completion(self, messages: List[Dict[str, str]], model_name: str, **kwargs) -> UnifiedLLMResponse:
    #             user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "no user message found")
    #             return UnifiedLLMResponse(content=f"Mocked chat response to: {user_msg}", model="mock_chat_model", id=str(uuid.uuid4()))
    #         async def completion(self, prompt: str, model_name: str, **kwargs) -> UnifiedLLMResponse:
    #             return UnifiedLLMResponse(content=f"Mocked completion response to: {prompt}", model="mock_completion_model", id=str(uuid.uuid4()))

    #     mock_llm_adapter = MockLLMAdapter()
    #     llm_adapters_map = {"mock_default_llm": mock_llm_adapter}
        
    #     # 3. Mock/Create Agents
    #     class SimpleEchoAgent(BaseAgent):
    #         # agent_name, description, llm_adapter, etc. are set during instantiation if using Pydantic
    #         async def run(self, input_data: GenericInput, context: ContextManager) -> GenericOutput:
    #             # print(f"SimpleEchoAgent ({self.agent_name}) received: {input_data.query} for session {context.session_id}")
    #             # print(f"History for {self.agent_name}: {context.get_history()}")
    #             response_content = f"Agent '{self.agent_name}' echoes: {input_data.query}"
    #             # Example of using the llm_adapter (though for echo it's not strictly needed)
    #             # llm_response = await self.llm_adapter.chat_completion([{"role":"user", "content": input_data.query}], "mock_chat_model")
    #             # response_content = llm_response.content
    #             return GenericOutput(response=response_content)

    #     echo_agent_instance = SimpleEchoAgent(
    #         agent_name="EchoCoreAgent",
    #         description="A simple agent that echoes the input query, part of core.",
    #         llm_adapter=mock_llm_adapter,
    #         prompt_template="User query: {query}", # Example prompt template
    #         input_schema=GenericInput,
    #         output_schema=GenericOutput
    #     )
    #     agents_map = {echo_agent_instance.agent_name: echo_agent_instance}
        
    #     # 4. Create Tool Registry (can be empty for this test)
    #     tool_registry_instance = ToolRegistry()

    #     # 5. Create OrchestratorPrincipal instance
    #     orchestrator_instance = OrchestratorPrincipal(
    #         llm_adapter_map=llm_adapters_map,
    #         agent_map=agents_map,
    #         tool_registry=tool_registry_instance,
    #         context_store_instance=store,
    #         default_agent_name="EchoCoreAgent",
    #         default_llm_adapter_name="mock_default_llm"
    #     )

    #     # 6. Process a query
    #     test_session_id = f"session_orch_test_{str(uuid.uuid4())}"
    #     print(f"\nProcessing first query for session: {test_session_id}")
    #     response_1 = await orchestrator_instance.process_query(user_query="Hello MedflowAI Orchestrator!", session_id=test_session_id)
    #     print(f"Orchestrator Response 1: {response_1}")

    #     print(f"\nProcessing second query for session: {test_session_id}")
    #     response_2 = await orchestrator_instance.process_query(user_query="How is the context being managed?", session_id=test_session_id)
    #     print(f"Orchestrator Response 2: {response_2}")

    #     # Verify context history
    #     # final_session_history = store.get_history(test_session_id)
    #     # print(f"\nFinal context history for session {test_session_id}:\n{final_session_history}")

    # if __name__ == "__main__":
    #      asyncio.run(run_orchestrator_test())

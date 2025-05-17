"""
Medical Consultation Platform (MCP) Interface Agent for MedflowAI.

This agent is responsible for interacting with an external MCP API, 
formatting requests, calling the appropriate MCP tool, and parsing responses.
It acts as a dedicated gateway to MCP functionalities within the MedflowAI library.
"""

from typing import Type, Any, Optional, Dict
from pydantic import BaseModel, Field
from ..core.base_agent import BaseAgent
from ..tools.mcp_tool_wrapper import MCPToolWrapper, MCPToolInput, MCPToolOutput # MCPTool specific I/O
from ..models.agent_io_models import GenericInput, GenericOutput

class MCPInterfaceAgentInput(GenericInput):
    # query from GenericInput might describe the high-level task for the MCP
    mcp_action: str = Field(..., description="The specific action to perform on the MCP (e.g., 'fetch_ehr_summary', 'validate_prescription').")
    mcp_payload: Dict[str, Any] = Field(..., description="The data payload required for the mcp_action.")
    mcp_target_system_id: Optional[str] = Field(None, description="Optional identifier for a specific target system or module within the MCP.")

class MCPInterfaceAgentOutput(GenericOutput):
    # response from GenericOutput can summarize the outcome
    mcp_status_code: int = Field(..., description="Status code from the MCP interaction (e.g., 200, 404, 500).")
    mcp_data: Optional[Dict[str, Any]] = Field(None, description="Data returned by the MCP action, if any.")
    mcp_error: Optional[str] = Field(None, description="Error message if the MCP interaction failed.")

class MCPInterfaceAgent(BaseAgent):
    agent_name: str = "MCPInterfaceAgent"
    description: str = "Manages interactions with an external Medical Consultation Platform (MCP) by invoking the MCPToolWrapper."
    
    # This agent primarily uses a tool, so an LLM adapter might only be for complex error handling or logging.
    # llm_adapter: Any 
    mcp_tool_instance: Optional[MCPToolWrapper] = None

    # Prompt template might not be directly used if this agent only executes a tool based on structured input.
    # If it were to use an LLM to decide *how* to call the MCP tool, then a prompt would be relevant.
    prompt_template: str = "This agent directly executes MCP tool calls based on structured input. LLM not primarily used for execution path."

    input_schema: Type[BaseModel] = MCPInterfaceAgentInput
    output_schema: Type[BaseModel] = MCPInterfaceAgentOutput

    def __init__(self, mcp_tool: Optional[MCPToolWrapper] = None, **data: Any):
        super().__init__(**data)
        # The MCPToolWrapper instance would ideally be injected or retrieved from a ToolRegistry.
        self.mcp_tool_instance = mcp_tool if mcp_tool else MCPToolWrapper() # Default for placeholder
        # print(f"{self.agent_name} initialized.")

    async def run(self, input_data: MCPInterfaceAgentInput, context: Optional[Dict[str, Any]] = None) -> MCPInterfaceAgentOutput:
        # print(f"{self.agent_name} running action: {input_data.mcp_action} with payload: {input_data.mcp_payload}")

        if not self.mcp_tool_instance:
            # print("Error: MCPToolWrapper not available to MCPInterfaceAgent.")
            return MCPInterfaceAgentOutput(
                response="MCP interaction failed: Tool not configured.",
                mcp_status_code=503, # Service Unavailable
                mcp_error="MCPToolWrapper not configured for this agent."
            )

        try:
            mcp_tool_input = MCPToolInput(
                action=input_data.mcp_action,
                payload=input_data.mcp_payload,
                target_system_id=input_data.mcp_target_system_id
            )
            
            tool_output: MCPToolOutput = await self.mcp_tool_instance.execute(**mcp_tool_input.model_dump())
            
            return MCPInterfaceAgentOutput(
                response=f"MCP action '{input_data.mcp_action}' completed with status {tool_output.status_code}.",
                mcp_status_code=tool_output.status_code,
                mcp_data=tool_output.response_data,
                mcp_error=tool_output.error_message
            )
        except Exception as e:
            # print(f"Error during MCPInterfaceAgent execution: {e}")
            return MCPInterfaceAgentOutput(
                response=f"MCP interaction for action '{input_data.mcp_action}' failed critically.",
                mcp_status_code=500, # Internal Server Error type for the agent's own failure
                mcp_error=f"Agent execution error: {str(e)}"
            )

if __name__ == "__main__":
    print("MedflowAI MCPInterfaceAgent module (now in agents package).")

    # Example Usage:
    # import asyncio
    # from medflowai.tools.mcp_tool_wrapper import MCPToolWrapper # Ensure path setup

    # async def test_mcp_interface_agent():
    #     # Explicitly create and pass the tool for the test
    #     mcp_tool = MCPToolWrapper()
    #     agent = MCPInterfaceAgent(mcp_tool=mcp_tool)

    #     # Test 1: Simulate a successful MCP action (fetch_ehr_summary)
    #     test_input_1 = MCPInterfaceAgentInput(
    #         query="Fetch EHR summary for patient PID_001",
    #         mcp_action="fetch_ehr_summary",
    #         mcp_payload={"patient_id": "PID_001"},
    #         mcp_target_system_id="ehr_alpha"
    #     )
    #     print(f"\nTesting with action: '{test_input_1.mcp_action}'")
    #     output_1 = await agent.run(input_data=test_input_1)
    #     print("Output 1:")
    #     print(output_1.model_dump_json(indent=2))
    #     assert output_1.mcp_status_code == 200
    #     assert output_1.mcp_data is not None

    #     # Test 2: Simulate an MCP action that might be 'not found' by the tool's placeholder logic
    #     test_input_2 = MCPInterfaceAgentInput(
    #         query="Request prior authorization for procedure XYZ",
    #         mcp_action="request_prior_auth",
    #         mcp_payload={"procedure_code": "XYZ123", "patient_id": "PID_002"}
    #     )
    #     print(f"\nTesting with action: '{test_input_2.mcp_action}'")
    #     output_2 = await agent.run(input_data=test_input_2)
    #     print("Output 2:")
    #     print(output_2.model_dump_json(indent=2))
    #     assert output_2.mcp_status_code == 404 # Based on MCPToolWrapper placeholder

    # # Ensure PYTHONPATH includes the project root for imports to work
    # # asyncio.run(test_mcp_interface_agent())

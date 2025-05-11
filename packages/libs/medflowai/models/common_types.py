"""
Common Pydantic Models for MedflowAI.

This module defines common data structures used across the library, such as 
the UnifiedLLMResponse, ToolCall, and UsageInfo, ensuring consistent data 
handling between LLM adapters, agents, and the orchestrator.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

class ToolCallFunction(BaseModel):
    """Represents the function to be called by a tool."""
    name: Optional[str] = Field(None, description="The name of the function to be called.")
    arguments: Optional[str] = Field(None, description="A JSON string representing the arguments to pass to the function.")

class ToolCall(BaseModel):
    """
    Represents a tool call suggested by an LLM.
    Compatible with OpenAI's tool_calls structure.
    """
    id: Optional[str] = Field(None, description="The ID of the tool call.")
    type: Optional[str] = Field("function", description="The type of the tool. Currently, only 'function' is supported.")
    function: ToolCallFunction = Field(..., description="The function that the model wants to call.")

class UsageInfo(BaseModel):
    """Represents token usage information from an LLM API call."""
    prompt_tokens: Optional[int] = Field(None, description="Number of tokens in the prompt.")
    completion_tokens: Optional[int] = Field(None, description="Number of tokens in the generated completion.")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens used in the request (prompt + completion).")

class UnifiedLLMResponse(BaseModel):
    """
    A standardized Pydantic model for representing responses from any LLM adapter.
    This ensures consistency in how LLM outputs are processed by agents and the orchestrator.
    """
    id: Optional[str] = Field(None, description="A unique identifier for the LLM response (e.g., chat completion ID).")
    object: Optional[str] = Field(None, description="The type of object returned (e.g., 'chat.completion').")
    created: Optional[int] = Field(None, description="The Unix timestamp (in seconds) of when the response was created.")
    model: Optional[str] = Field(None, description="The name of the model used to generate the response.")
    content: Optional[str] = Field(None, description="The main textual content of the LLM's response.")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="A list of tool calls suggested by the LLM, if any.")
    finish_reason: Optional[str] = Field(None, description="The reason the LLM stopped generating tokens (e.g., 'stop', 'tool_calls', 'length').")
    usage: Optional[UsageInfo] = Field(None, description="Token usage statistics for the request.")
    system_fingerprint: Optional[str] = Field(None, description="An identifier for the system configuration used by the LLM (e.g., from OpenAI)." )
    raw_response: Optional[Any] = Field(None, description="The original, unprocessed response from the LLM API for debugging or specific needs.")
    error: Optional[str] = Field(None, description="An error message if the LLM call failed.")

    class Config:
        extra = 'allow' # Allow extra fields if the LLM API returns more than defined

if __name__ == "__main__":
    # This is primarily for module testing or example usage.
    print("MedflowAI Common Types module.")
    usage_example = UsageInfo(prompt_tokens=50, completion_tokens=150, total_tokens=200)
    tool_call_function_example = ToolCallFunction(name="get_patient_details", arguments='{"patient_id": "patient_abc_123"}')
    tool_call_example = ToolCall(id="tool_xyz_789", function=tool_call_function_example)
    response_example = UnifiedLLMResponse(
        id="chatresp_uvw_456",
        object="chat.completion",
        created=1678886400,
        model="gpt-4-turbo-preview",
        content="Patient details retrieved successfully.",
        tool_calls=[tool_call_example],
        finish_reason="tool_calls",
        usage=usage_example,
        system_fingerprint="fp_a1b2c3d4e5"
    )
    print("\nExample UnifiedLLMResponse:")
    print(response_example.model_dump_json(indent=2))

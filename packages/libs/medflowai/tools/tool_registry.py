"""
Tool Registry for MedflowAI.

This module defines the ToolRegistry class, responsible for managing and 
providing access to tools that agents can use within the MedflowAI library. 
It also handles the conversion of these tools into formats expected by LLM APIs 
(e.g., OpenAI functions), relying on the BaseTool's schema generation.
"""

from typing import Dict, List, Type, Any, Callable
from pydantic import BaseModel # BaseModel is used by tools' input_schemas

# Import the actual BaseTool from the base_tool module in the same package
from .base_tool import BaseTool

class ToolRegistry:
    """
    Manages a collection of tools available to agents.
    Allows registration, retrieval, and schema conversion for LLM integration.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        # print("ToolRegistry initialized.")

    def register_tool(self, tool: BaseTool):
        """
        Registers a tool instance.

        Args:
            tool (BaseTool): An instance of a class derived from BaseTool.
        """
        if not isinstance(tool, BaseTool):
            raise TypeError(f"Tool must be an instance of BaseTool, got {type(tool)}.")
        if tool.name in self._tools:
            # print(f"Warning: Tool '{tool.name}' is already registered. Overwriting.")
            pass # Decide on overwrite or error strategy
        self._tools[tool.name] = tool
        # print(f"Tool '{tool.name}' registered.")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Retrieves a tool by its name.

        Args:
            name (str): The name of the tool.

        Returns:
            Optional[BaseTool]: The tool instance, or None if not found.
        """
        return self._tools.get(name)

    def get_all_tools(self) -> List[BaseTool]:
        """
        Returns a list of all registered tools.
        """
        return list(self._tools.values())

    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """
        Returns a list of tool schemas formatted for LLM function calling
        (e.g., OpenAI API format), using each tool's to_llm_schema method.
        """
        return [tool.to_llm_schema() for tool in self._tools.values()]

    async def execute_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Executes a tool call based on its name and arguments.

        Args:
            tool_name (str): The name of the tool to execute.
            arguments (Dict[str, Any]): The arguments for the tool, typically parsed 
                                     from LLM output (JSON string converted to dict).

        Returns:
            Any: The result of the tool execution.
            
        Raises:
            KeyError: If the tool_name is not found in the registry.
            TypeError: If arguments do not match the tool's input_schema (via Pydantic validation).
        """
        tool_to_execute = self.get_tool(tool_name)
        if not tool_to_execute:
            raise KeyError(f"Tool '{tool_name}' not found in registry.")
        
        # Validate arguments using the tool's input_schema
        try:
            validated_args = tool_to_execute.input_schema(**arguments)
        except Exception as e: # Catches Pydantic's ValidationError and others
            raise TypeError(f"Invalid arguments for tool '{tool_name}'. Error: {e}. Provided: {arguments}") from e
        
        return await tool_to_execute.execute(**validated_args.model_dump())

if __name__ == "__main__":
    print("MedflowAI ToolRegistry module (now in tools package).")
    
    # Example Usage:
    # Define a Pydantic model for the tool's input
    class SimpleToolInput(BaseModel):
        message: str = Field(..., description="The message to be processed.")
        repeat_count: Optional[int] = Field(1, description="Number of times to repeat the message.")

    # Define a simple tool using the actual BaseTool
    class EchoTool(BaseTool):
        name: str = "echo_message_tool"
        description: str = "Echoes a message a specified number of times."
        input_schema: Type[BaseModel] = SimpleToolInput

        async def execute(self, message: str, repeat_count: Optional[int] = 1) -> str:
            # print(f"EchoTool executed with message: '{message}', repeat_count: {repeat_count}")
            return " ".join([message] * (repeat_count if repeat_count is not None else 1))

    async def run_registry_example():
        registry = ToolRegistry()
        
        echo_tool_instance = EchoTool()
        registry.register_tool(echo_tool_instance)
        # print(f"Registered tools: {[tool.name for tool in registry.get_all_tools()]}")

        # Get schemas for LLM
        llm_schemas = registry.get_tool_schemas_for_llm()
        # print("\nLLM Tool Schemas:")
        # import json
        # print(json.dumps(llm_schemas, indent=2))

        # Execute a tool call
        tool_name_to_call = "echo_message_tool"
        arguments_for_call = {"message": "Hello MedflowAI", "repeat_count": 3}
        # print(f"\nExecuting tool '{tool_name_to_call}' with arguments: {arguments_for_call}")
        try:
            result = await registry.execute_tool_call(tool_name_to_call, arguments_for_call)
            # print(f"Execution result: {result}")
            assert result == "Hello MedflowAI Hello MedflowAI Hello MedflowAI"
        except Exception as e:
            print(f"Error during tool execution: {e}")

        # Example of calling a non-existent tool
        try:
            # print("\nAttempting to execute non-existent tool...")
            await registry.execute_tool_call("non_existent_tool", {"param": "value"})
        except KeyError as e:
            # print(f"Caught expected error: {e}")
            pass

        # Example of calling with invalid arguments
        try:
            # print("\nAttempting to execute with invalid arguments...")
            await registry.execute_tool_call(tool_name_to_call, {"msg": "wrong_arg_name", "repeat_count": "not_an_int"})
        except TypeError as e:
            # print(f"Caught expected error: {e}")
            pass
        
        print("ToolRegistry example completed successfully.")

    import asyncio
    asyncio.run(run_registry_example())

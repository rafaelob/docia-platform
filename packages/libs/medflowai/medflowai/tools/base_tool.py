"""
Base Tool for MedflowAI.

This module defines the BaseTool class, an abstract class that all tools 
available to agents within the MedflowAI library should inherit from. 
It uses Pydantic for defining the input schema of the tool.
"""

from abc import ABC, abstractmethod
from typing import Type, Any, Dict
from pydantic import BaseModel, ConfigDict

class BaseTool(ABC, BaseModel):
    """
    Abstract base class for all tools.
    Each tool must define its name, description, and a Pydantic model 
    for its input arguments.
    """
    name: str
    description: str
    input_schema: Type[BaseModel]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the tool with the given arguments.
        The arguments should conform to the tool's input_schema.

        Args:
            **kwargs: The arguments for the tool, matching its input_schema.

        Returns:
            Any: The result of the tool execution.
        """
        pass

    def to_llm_schema(self) -> Dict[str, Any]:
        """
        Converts the tool's Pydantic input schema into a JSON Schema 
        representation suitable for LLM function calling (e.g., OpenAI API).
        """
        # Ensure that input_schema is a Pydantic model before calling model_json_schema
        if not (isinstance(self.input_schema, type) and issubclass(self.input_schema, BaseModel)):
            raise TypeError("input_schema must be a Pydantic BaseModel class.")

        schema = self.input_schema.model_json_schema()
        parameters = {
            "type": "object",
            "properties": schema.get("properties", {}),
        }
        required = schema.get("required", [])
        if required:
            parameters["required"] = required
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters,
            },
        }

    # Pydantic models are typically initialized via their keyword arguments
    # or a class constructor if defined. The __init__ here is from BaseModel.
    # The print statement inside __init__ was likely for legacy debugging.
    # If instance-specific initialization logic is needed beyond Pydantic's, 
    # it should be in a custom __init__ that calls super().__init__(**data).

if __name__ == "__main__":
    print("MedflowAI BaseTool module (now in tools package).")
    
    # Example of defining and using a BaseTool derivative:
    class ExampleToolInput(BaseModel):
        target_entity: str
        max_results: int = 5

    class SearchKnowledgeBaseTool(BaseTool):
        name: str = "search_knowledge_base"
        description: str = "Searches the knowledge base for a given entity."
        input_schema: Type[BaseModel] = ExampleToolInput

        async def execute(self, target_entity: str, max_results: int = 5) -> Dict[str, Any]:
            # In a real scenario, this would interact with a knowledge base.
            print(f"Executing SearchKnowledgeBaseTool: Searching for '{target_entity}', max results: {max_results}")
            # Simulate results
            results = [{
                "id": f"doc_{i}", 
                "content": f"Content related to {target_entity} - result {i+1}", 
                "score": 1.0 - (i*0.1)
            } for i in range(min(max_results, 3))]
            return {"status": "success", "results": results}

    async def run_example():
        kb_search_tool = SearchKnowledgeBaseTool()
        print(f"\nTool Name: {kb_search_tool.name}")
        print(f"Tool Description: {kb_search_tool.description}")
        print(f"Tool LLM Schema:\n{kb_search_tool.to_llm_schema()}")
        
        execution_result = await kb_search_tool.execute(target_entity="diabetes type 2", max_results=2)
        print(f"\nTool Execution Result:\n{execution_result}")

    import asyncio
    asyncio.run(run_example())

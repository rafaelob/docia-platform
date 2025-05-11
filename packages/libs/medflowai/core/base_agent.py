"""
Base Agent for MedflowAI.

This module defines the BaseAgent class, an abstract class that all specialized 
agents within the MedflowAI library will inherit from. It integrates with 
Pydantic for input/output schema validation and is designed to work with LLM adapters.
"""

from abc import ABC, abstractmethod
from typing import Type, Any, Optional, List, Dict
from pydantic import BaseModel

# Import the correct LLM adapter interface and context manager
from ..adapters.base_llm_adapter import BaseLLMAdapter # Adjusted path
from .context_manager import ContextManager # Assuming ContextManager is defined in core

# Import generic I/O models
from ..models.agent_io_models import GenericInput, GenericOutput # Path remains correct

class BaseAgent(ABC, BaseModel):
    """
    Abstract base class for all agents.
    Each agent should define its name, description, LLM adapter, prompt template(s),
    and input/output Pydantic models.
    """
    agent_name: str
    description: str
    llm_adapter: BaseLLMAdapter 
    prompt_template: str # Or a more complex structure for prompts
    input_schema: Type[BaseModel] = GenericInput # Default to GenericInput
    output_schema: Type[BaseModel] = GenericOutput # Default to GenericOutput

    class Config:
        arbitrary_types_allowed = True # To allow types like BaseLLMAdapter

    @abstractmethod
    async def run(self, input_data: BaseModel, context: ContextManager) -> BaseModel:
        """
        Main execution method for the agent.

        Args:
            input_data (BaseModel): The input data, validated against input_schema.
            context (ContextManager): The context manager for session and history.

        Returns:
            BaseModel: The output data, validated against output_schema.
        """
        pass

    def _prepare_prompt(self, input_data: BaseModel, context: ContextManager) -> List[Dict[str, str]]:
        """
        Prepares the prompt messages for the LLM based on the input data and context.
        This method should be overridden by subclasses if a specific prompt format is needed.
        Default implementation might involve simple template substitution.

        Args:
            input_data (BaseModel): The input data for the agent.
            context (ContextManager): The current conversation context.

        Returns:
            list[dict]: A list of messages formatted for the LLM (e.g., OpenAI chat format).
        """
        system_message = {"role": "system", "content": self.prompt_template}
        
        # Attempt to get query from input_data if it exists, otherwise serialize the whole model
        if hasattr(input_data, 'query') and isinstance(input_data.query, str):
            user_query_content = input_data.query
        else:
            user_query_content = input_data.model_dump_json()

        user_message_content_full = f"Input: {user_query_content}"
        
        history_messages = []
        if context and hasattr(context, 'get_formatted_history'):
            history_messages = context.get_formatted_history(limit=5) # Get last 5 turns for example

        return [system_message] + history_messages + [{"role": "user", "content": user_message_content_full}]

    def __init__(self, **data: Any):
        super().__init__(**data)
        # print(f"Agent {self.agent_name} initialized.") # Keep for debugging if needed

if __name__ == "__main__":
    print("MedflowAI BaseAgent module (now in core package).")
    # Add more specific test/example logic here if needed when developing BaseAgent

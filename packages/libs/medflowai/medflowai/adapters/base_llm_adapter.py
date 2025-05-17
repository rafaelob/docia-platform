"""
Base LLM Adapter for MedflowAI.

This module defines the BaseLLMAdapter, an abstract class that all specific LLM 
service adapters (e.g., for OpenAI, Google Gemini) will inherit from. It establishes
a common interface for interacting with different Large Language Models within the MedflowAI library.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Import the correct UnifiedLLMResponse from the models package
from ..models.common_types import UnifiedLLMResponse, ToolCall # Path is correct for new location

class BaseLLMAdapter(ABC):
    """
    Abstract base class for LLM adapters.
    Provides a consistent interface to interact with various LLM providers.
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initializes the LLM adapter.

        Args:
            api_key (Optional[str]): The API key for the LLM service.
            **kwargs: Additional configuration parameters for the adapter.
        """
        self.api_key = api_key
        self.config = kwargs
        # print(f"BaseLLMAdapter initialized for {self.__class__.__name__}.") # Keep for debugging if needed

    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], model_name: str, tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[str] = None, **kwargs) -> UnifiedLLMResponse:
        """
        Generates a chat completion response from the LLM.

        Args:
            messages (List[Dict[str, str]]): A list of message objects (e.g., OpenAI format 
                                             `[{"role": "user", "content": "..."}]`).
            model_name (str): The specific model to use for the completion.
            tools (Optional[List[Dict[str, Any]]]): A list of tools the model may call. (OpenAI format)
            tool_choice (Optional[str]): Controls which (if any) function is called by the model. (OpenAI format)
            **kwargs: Additional provider-specific parameters for the completion call.

        Returns:
            UnifiedLLMResponse: A standardized response object.
        """
        pass

    @abstractmethod
    async def completion(self, prompt: str, model_name: str, **kwargs) -> UnifiedLLMResponse:
        """
        Generates a standard completion response from the LLM (for non-chat models, if supported).

        Args:
            prompt (str): The prompt string.
            model_name (str): The specific model to use.
            **kwargs: Additional provider-specific parameters.

        Returns:
            UnifiedLLMResponse: A standardized response object.
        """
        pass

    # Optional: Add methods for other LLM functionalities like embeddings, fine-tuning, etc.
    # async def get_embeddings(self, texts: List[str], model_name: str, **kwargs) -> List[List[float]]:
    #     pass

if __name__ == "__main__":
    print("MedflowAI BaseLLMAdapter module (now in adapters package).")
    # Add test/example logic if needed during development of this base class

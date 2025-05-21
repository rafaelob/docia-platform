"""
OpenAI LLM Adapter for MedflowAI.

This module implements the BaseLLMAdapter interface for interacting with 
OpenAI's API (e.g., GPT-3.5, GPT-4 for chat completions and potentially 
the Assistants API) within the MedflowAI library.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai

from .base_llm_adapter import BaseLLMAdapter
from ..models.common_types import UnifiedLLMResponse

logger = logging.getLogger(__name__)

class OpenAIAdapter(BaseLLMAdapter):
    """
    Adapter for OpenAI's language models.
    Handles API key management and request/response mapping.
    """
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        resolved_api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        
        if not resolved_api_key:
            logger.warning(
                "OpenAI API key not explicitly passed to adapter or found in OPENAI_API_KEY env var. "
                "Client instantiation may fail or operations will be unauthorized."
            )
        
        try:
            self.client = openai.AsyncOpenAI(api_key=resolved_api_key)
            logger.info("OpenAIAdapter initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            # Propagate error or handle as per desired resiliency strategy
            raise  # Or set a flag, or return a specific error state

    async def chat_completion(self, messages: List[Dict[str, str]], model_name: str, **kwargs) -> UnifiedLLMResponse:
        """
        Generates a chat completion response using the OpenAI API.

        Args:
            messages: List of message objects in OpenAI format.
            model_name: The specific OpenAI model to use (e.g., "gpt-4-turbo").
            **kwargs: Additional parameters for the OpenAI API call (e.g., temperature, tools).

        Returns:
            UnifiedLLMResponse: A standardized response object.
        """
        try:
            api_params = {
                "model": model_name,
                "messages": messages,
                **kwargs
            }
            
            response = await self.client.chat.completions.create(**api_params)
            
            first_choice = response.choices[0]
            message_content = first_choice.message.content
            tool_calls_data = None
            if first_choice.message.tool_calls:
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in first_choice.message.tool_calls
                ]

            return UnifiedLLMResponse(
                id=response.id,
                object=response.object,
                created=response.created,
                model=response.model,
                content=message_content,
                tool_calls=tool_calls_data,
                finish_reason=first_choice.finish_reason,
                usage=response.usage.model_dump() if response.usage else None,
                system_fingerprint=response.system_fingerprint,
                raw_response=response.model_dump_json()
            )
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIConnectionError: {e}", raw_response=str(e), model=model_name)
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API rate limit exceeded: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"RateLimitError: {e}", raw_response=str(e), model=model_name)
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI API authentication error: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"AuthenticationError: {e} - Check API key.", raw_response=str(e), model=model_name)
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API status error (code {e.status_code}): {e.message}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIStatusError {e.status_code}: {e.message}", raw_response=str(e), model=model_name)
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI chat completion: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"UnexpectedError: {e}", raw_response=str(e), model=model_name)

    async def responses_create(self, messages: List[Dict[str, str]], model_name: str, **kwargs) -> UnifiedLLMResponse:
        """Generate a response using OpenAI's newer *Responses* endpoint.

        This wraps :pyfunc:`openai.AsyncOpenAI.responses.create` and maps the
        provider-specific output into :class:`medflowai.models.common_types.UnifiedLLMResponse`.
        The signature intentionally mirrors :pyfunc:`chat_completion` to allow
        drop-in replacement from calling code.
        """
        try:
            api_params = {
                "model": model_name,
                "messages": messages,
                **kwargs,
            }

            response = await self.client.responses.create(**api_params)
            # current beta shape is similar to chat completions: first choice
            first_choice = response.choices[0]
            message_content = first_choice.message.content if hasattr(first_choice.message, "content") else None
            tool_calls_data = None
            if getattr(first_choice.message, "tool_calls", None):
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in first_choice.message.tool_calls
                ]

            return UnifiedLLMResponse(
                id=response.id,
                object=response.object,
                created=response.created,
                model=response.model,
                content=message_content,
                tool_calls=tool_calls_data,
                finish_reason=first_choice.finish_reason,
                usage=response.usage.model_dump() if response.usage else None,
                system_fingerprint=getattr(response, "system_fingerprint", None),
                raw_response=response.model_dump_json(),
            )
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error (responses): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIConnectionError: {e}", raw_response=str(e), model=model_name)
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API rate limit exceeded (responses): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"RateLimitError: {e}", raw_response=str(e), model=model_name)
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI API authentication error (responses): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"AuthenticationError: {e} - Check API key.", raw_response=str(e), model=model_name)
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API status error (responses, code {e.status_code}): {e.message}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIStatusError {e.status_code}: {e.message}", raw_response=str(e), model=model_name)
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI responses.create: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"UnexpectedError: {e}", raw_response=str(e), model=model_name)

    async def completion(self, prompt: str, model_name: str, **kwargs) -> UnifiedLLMResponse:
        """
        Generates a standard completion (not chat) using older OpenAI models if needed.
        Note: For newer models, chat_completion is preferred.
        """
        try:
            response = await self.client.completions.create(
                model=model_name,
                prompt=prompt,
                **kwargs
            )
            first_choice = response.choices[0]
            return UnifiedLLMResponse(
                id=response.id,
                object=response.object,
                created=response.created,
                model=response.model,
                content=first_choice.text,
                finish_reason=first_choice.finish_reason,
                usage=response.usage.model_dump() if response.usage else None,
                raw_response=response.model_dump_json()
            )
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error (completion): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIConnectionError: {e}", raw_response=str(e), model=model_name)
        except openai.RateLimitError as e:
            logger.error(f"OpenAI API rate limit exceeded (completion): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"RateLimitError: {e}", raw_response=str(e), model=model_name)
        except openai.AuthenticationError as e:
            logger.error(f"OpenAI API authentication error (completion): {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"AuthenticationError: {e} - Check API key.", raw_response=str(e), model=model_name)
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API status error (completion, code {e.status_code}): {e.message}", exc_info=True)
            return UnifiedLLMResponse(error=f"APIStatusError {e.status_code}: {e.message}", raw_response=str(e), model=model_name)
        except Exception as e:
            logger.error(f"Unexpected error during OpenAI completion: {e}", exc_info=True)
            return UnifiedLLMResponse(error=f"UnexpectedError: {e}", raw_response=str(e), model=model_name)

if __name__ == "__main__":
    print("MedflowAI OpenAIAdapter module (now in adapters package).")
    # Example Usage (requires OPENAI_API_KEY to be set in env or passed to adapter):
    # import asyncio
    # async def test_openai_adapter():
    #     try:
    #         # Ensure OPENAI_API_KEY is in your environment or pass it directly:
    #         # adapter = OpenAIAdapter(api_key="sk-your-key-here") 
    #         adapter = OpenAIAdapter()
    #         messages = [{"role": "user", "content": "Translate 'hello' to French."}]
    #         print(f"Sending request with model gpt-3.5-turbo...")
    #         response = await adapter.chat_completion(messages=messages, model_name="gpt-3.5-turbo")
    #         if response.error:
    #             print(f"API Error: {response.error}")
    #         else:
    #             print(f"Response Content: {response.content}")
    #             if response.usage:
    #                 print(f"Usage: {response.usage}")
    #     except ValueError as ve:
    #         print(f"Configuration Error: {ve}")
    #     except openai.APIConnectionError as ace:
    #         print(f"OpenAI API Connection Error: {ace}")
    #     except openai.AuthenticationError as ae:
    #         print(f"OpenAI API Authentication Error: {ae} - Check your API key.")
    #     except Exception as e:
    #         print(f"An unexpected error occurred: {e}")

    # if os.getenv("OPENAI_API_KEY"):
    #     asyncio.run(test_openai_adapter())
    # else:
    #     print("Skipping OpenAIAdapter test: OPENAI_API_KEY environment variable not set.")

"""
Google Gemini LLM Adapter for MedflowAI.

This module implements the BaseLLMAdapter interface for interacting with
Google's Gemini models using the native 'google-genai' Python SDK.
"""

import os
import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union

import google.generativeai as genai
from google.generativeai.types import (
    FunctionDeclaration, Tool, GenerationConfig, 
    HarmCategory, HarmBlockThreshold, GenerateContentResponse
)

from .base_llm_adapter import BaseLLMAdapter
from ..models.common_types import UnifiedLLMResponse, ToolCall, FunctionCall

GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"
DEFAULT_SAFETY_SETTINGS = [
    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
]

class GoogleGeminiAdapter(BaseLLMAdapter):
    """
    Adapter for Google's Gemini language models, using the native 'google-genai' SDK.
    """
    def __init__(self, api_key: Optional[str] = None, default_model_name: str = "gemini-1.5-flash-latest", **kwargs):
        super().__init__(api_key, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.default_model_name = default_model_name
        self._is_configured = False
        resolved_api_key = self.api_key or os.getenv(GEMINI_API_KEY_ENV_VAR) or os.getenv("GOOGLE_API_KEY")
        if not resolved_api_key:
            self.logger.warning(f"{GEMINI_API_KEY_ENV_VAR} or GOOGLE_API_KEY not found. Adapter won't work.")
            return
        try:
            genai.configure(api_key=resolved_api_key)
            self._is_configured = True
            self.logger.info("GoogleGeminiAdapter initialized and google-genai SDK configured.")
        except Exception as e:
            self.logger.error(f"Error configuring google-genai SDK: {e}", exc_info=True)

    def _extract_system_prompt_and_convert_messages(self, messages: List[Dict[str, str]]) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        system_prompt_str: Optional[str] = None
        gemini_messages: List[Dict[str, Any]] = []
        processed_system_prompt = False
        for msg in messages:
            role, content = msg.get("role", "user"), msg.get("content", "")
            if role == "system" and not processed_system_prompt:
                system_prompt_str, processed_system_prompt = str(content), True
                continue
            gemini_role = "model" if role == "assistant" else "user"
            current_parts: List[Dict[str, Any]] = []
            if role == "assistant" and msg.get("tool_calls"):
                if content: 
                    current_parts.append({'text': str(content)})
                for tc in msg["tool_calls"]:
                    current_parts.append({
                        'function_call': {
                            'name': tc['function']['name'],
                            'args': json.loads(tc['function']['arguments'])
                        }
                    })
                gemini_messages.append({'role': gemini_role, 'parts': current_parts})
            elif role == "tool":
                tool_call_id, func_name = msg.get("tool_call_id"), msg.get("name")
                name_to_use = func_name or tool_call_id
                if not name_to_use: continue
                try:
                    resp_content_dict = json.loads(str(content)) if isinstance(content, str) and content.strip().startswith(('{', '[')) else {"result": content}
                except json.JSONDecodeError:
                    resp_content_dict = {"result": str(content)}
                current_parts.append({
                    'function_response': {
                        'name': name_to_use,
                        'response': resp_content_dict
                    }
                })
                gemini_messages.append({'role': 'function', 'parts': current_parts})
            else:
                current_parts.append({'text': str(content)})
                gemini_messages.append({'role': gemini_role, 'parts': current_parts})
        return system_prompt_str, gemini_messages

    def _convert_openai_tools_to_gemini(self, openai_tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Tool]]:
        if not openai_tools: return None
        gemini_fn_decls = [FunctionDeclaration(name=t["function"]["name"], description=t["function"].get("description", ""), parameters=t["function"].get("parameters")) for t in openai_tools if t.get("type") == "function"]
        return [Tool(function_declarations=gemini_fn_decls)] if gemini_fn_decls else None

    def _get_gemini_tool_config(self, tool_choice: Optional[Union[str, Dict[str, Any]]], tools_present: bool) -> Optional[Dict[str, Any]]:
        if not tools_present: return None
        mode_str: str = "AUTO"
        allowed_function_names: Optional[List[str]] = None
        if isinstance(tool_choice, str):
            if tool_choice == "none": mode_str = "NONE"
            elif tool_choice == "auto": mode_str = "AUTO"
        elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            func_name = tool_choice.get("function", {}).get("name")
            if func_name:
                mode_str = "ANY"
                allowed_function_names = [func_name]
        config_dict: Dict[str, Any] = {"mode": mode_str}
        if allowed_function_names:
            config_dict["allowed_function_names"] = allowed_function_names
        return {"function_calling_config": config_dict}

    async def chat_completion(self, messages: List[Dict[str, str]], model_name: str, **kwargs) -> UnifiedLLMResponse:
        if not self._is_configured: return UnifiedLLMResponse(error="Adapter not configured", model=model_name)
        self.logger.debug(f"Gemini chat: model={model_name}, messages={len(messages)}, kwargs={list(kwargs.keys())}")
        system_prompt, gemini_history = self._extract_system_prompt_and_convert_messages(messages)
        cfg_kw = {k: kwargs[k] for k in ["temperature", "top_p", "top_k"] if k in kwargs}
        if "max_tokens" in kwargs: cfg_kw["max_output_tokens"] = kwargs["max_tokens"]
        if "stop" in kwargs: cfg_kw["stop_sequences"] = kwargs["stop"]
        gen_cfg_obj = GenerationConfig(**cfg_kw) if cfg_kw else None
        gemini_tools = self._convert_openai_tools_to_gemini(kwargs.get("tools"))
        gemini_tool_config_dict = self._get_gemini_tool_config(kwargs.get("tool_choice"), bool(gemini_tools))
        try:
            model_inst = genai.GenerativeModel(model_name or self.default_model_name, system_instruction=system_prompt, safety_settings=kwargs.get("safety_settings", DEFAULT_SAFETY_SETTINGS), generation_config=gen_cfg_obj)
            response: GenerateContentResponse = await model_inst.generate_content_async(contents=gemini_history, tools=gemini_tools, tool_config=gemini_tool_config_dict)
            self.logger.debug(f"Raw Gemini response: {response.candidates[0].finish_reason if response.candidates else 'No candidates'}")
            text_content, p_tool_calls, f_reason_str = None, [], None
            if response.candidates:
                cand = response.candidates[0]
                f_reason_str = str(cand.finish_reason.name) if cand.finish_reason else None
                for part in cand.content.parts:
                    if part.text: text_content = (text_content or "") + part.text
                    elif part.function_call:
                        args_dict = dict(part.function_call.args) if part.function_call.args else {}
                        args_j = json.dumps(args_dict)
                        p_tool_calls.append(ToolCall(id=f"call_{part.function_call.name}", type="function", function=FunctionCall(name=part.function_call.name, arguments=args_j)))
            usage = {k: getattr(response.usage_metadata, k) for k in ["prompt_token_count", "candidates_token_count", "total_token_count"] if hasattr(response.usage_metadata, k)} if response.usage_metadata else None
            return UnifiedLLMResponse(content=text_content, tool_calls=p_tool_calls or None, model=model_name, usage=usage, finish_reason=f_reason_str, raw_response=response.to_json())
        except Exception as e: 
            error_type_str = str(type(e))
            if 'google' in error_type_str.lower() or 'generative' in error_type_str.lower() or 'api' in error_type_str.lower():
                self.logger.error(f"Google Gemini API related error: {type(e).__name__} - {e}", exc_info=True)
                return UnifiedLLMResponse(error=f"GoogleAPIError: {type(e).__name__} - {e}", raw_response=str(e), model=model_name)
            else:
                self.logger.error(f"Unexpected error in Gemini chat: {type(e).__name__} - {e}", exc_info=True)
                return UnifiedLLMResponse(error=f"Unexpected: {type(e).__name__} - {e}", raw_response=str(e), model=model_name)

    async def completion(self, prompt: str, model_name: str, **kwargs) -> UnifiedLLMResponse:
        return await self.chat_completion(messages=[{"role": "user", "content": prompt}], model_name=model_name, **kwargs)

    async def responses_create(self, messages: List[Dict[str, str]], model_name: str, **kwargs) -> UnifiedLLMResponse:
        """Gemini SDK does not yet expose a dedicated Responses API; fallback to chat_completion.

        The method exists to satisfy :class:`BaseLLMAdapter` and allow calling
        code to remain transport-agnostic. Behaviour is identical to
        :pyfunc:`chat_completion` for the time being.
        """
        return await self.chat_completion(messages=messages, model_name=model_name, **kwargs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    async def test_adapter():
        logger.info("Testing GoogleGeminiAdapter (native SDK)...")
        if not (os.getenv(GEMINI_API_KEY_ENV_VAR) or os.getenv("GOOGLE_API_KEY")):
            logger.warning(f"Skipping test: {GEMINI_API_KEY_ENV_VAR} or GOOGLE_API_KEY not set.")
            return
        adapter = GoogleGeminiAdapter()
        if not adapter._is_configured: logger.error("Adapter init failed."); return
        model = "gemini-1.5-flash-latest"
        logger.info(f"--- Test 1: Chat (Model: {model})")
        resp1 = await adapter.chat_completion(messages=[{"role": "system", "content": "Be brief."}, {"role": "user", "content": "Why is sky blue?"}], model_name=model, max_tokens=50)
        logger.info(f"Chat response: {'Error: ' + resp1.error if resp1.error else (resp1.content[:50] + '...' if resp1.content and len(resp1.content) > 50 else resp1.content if resp1.content else 'None')}")
        logger.info(f"--- Test 2: Tool Call (Model: {model})")
        tools = [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}}}]
        resp2 = await adapter.chat_completion(messages=[{"role": "user", "content": "Weather in SF?"}], model_name=model, tools=tools)
        if resp2.tool_calls:
            logger.info(f"Tool call: {resp2.tool_calls[0].function.name}({resp2.tool_calls[0].function.arguments})")
            tool_call_msg = {"role": "assistant", "content": None, "tool_calls": [{"id": resp2.tool_calls[0].id, "type": "function", "function": {"name": resp2.tool_calls[0].function.name, "arguments": resp2.tool_calls[0].function.arguments}}]}
            tool_response_msg = {"role": "tool", "tool_call_id": resp2.tool_calls[0].id, "name": resp2.tool_calls[0].function.name, "content": json.dumps({"weather": "sunny", "temp": 70})}
            final_resp = await adapter.chat_completion(messages=[{"role": "user", "content": "Weather in SF?"}, tool_call_msg, tool_response_msg], model_name=model, tools=tools)
            logger.info(f"Final response after tool call: {final_resp.content if final_resp.content else 'None'}")
        else: 
            logger.info(f"No tool call. Error: {resp2.error if resp2.error else 'None'}, Content: {resp2.content if resp2.content else 'None'}")
        logger.info("Test finished.")
    asyncio.run(test_adapter())

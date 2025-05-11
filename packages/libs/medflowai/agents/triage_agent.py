"""
Placeholder for Triage Agent for MedflowAI.

This agent will be responsible for initial query analysis and routing within the MedflowAI library.
"""

from typing import Type, Any, Optional, Dict 
from pydantic import BaseModel, Field 
from ..core.base_agent import BaseAgent 
from ..models.agent_io_models import AgentInput, AgentOutput 
import json
import logging

# Define a more specific input model if needed, inheriting from AgentInput
class TriageAgentInput(AgentInput):
    # query is already in AgentInput. Add specifics if any.
    # session_id: Optional[str] = Field(None, description="Session ID for context tracking.")
    pass

# Define a more specific output model, inheriting from AgentOutput
class TriageAgentOutput(AgentOutput):
    # response is already in AgentOutput. Add specifics.
    recommended_next_agent: str = Field(..., description="The name of the next agent suggested by triage.")
    confidence_score: float = Field(..., description="Confidence score (0.0 to 1.0) for the recommendation.")
    rationale: Optional[str] = Field(None, description="Brief explanation for the triage decision.")

class TriageAgent(BaseAgent):
    agent_name: str = "TriageAgent"
    description: str = "Analyzes an initial clinical query, determines primary intent, and routes to the most appropriate specialized agent or action."
    
    # The LLM adapter would be injected or configured globally
    # self.llm_adapter is inherited from BaseAgent and should be set during instantiation.
    # self.model_name can also be set in BaseAgent, defaults to gpt-4-turbo if not set.

    default_model_name: str = "gpt-4-turbo" # Default model if not set in BaseAgent

    # A more structured prompt template is advisable
    prompt_template: str = (
        "You are an AI Triage Agent in a clinical decision support system. "
        "Your role is to analyze the following user query and determine the most "
        "appropriate next step or specialized agent.\n\n"
        "User Query: \"{query}\"\n\n"
        "Context (if any): {context_data}\n\n"
        "Based on this, identify the primary clinical intent. Then, recommend the "
        "best specialized agent to handle this query (e.g., 'MedicalRAGAgent' for information "
        "retrieval, 'DiagnosticSupportAgent' for differential diagnosis, 'VerificationAgent' for "
        "fact-checking). Provide your recommendation, a confidence score (0.0-1.0), and a brief rationale.\n\n"
        "Output format should be a JSON object parsable into TriageAgentOutput."
    )

    input_schema: Type[BaseModel] = TriageAgentInput
    output_schema: Type[BaseModel] = TriageAgentOutput # PydanticAI will use this for parsing LLM output

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.logger = logging.getLogger(__name__) # Initialize logger for the instance
        # Initialize any specific resources for this agent if needed
        # print(f"{self.agent_name} initialized.")

    async def run(self, input_data: TriageAgentInput, context: Optional[Dict[str, Any]] = None) -> TriageAgentOutput:
        self.logger.info(f"{self.agent_name} received query: '{input_data.query}' with context: {context}")

        if not self.llm_adapter:
            self.logger.error("LLMAdapter not configured for TriageAgent.")
            return TriageAgentOutput(
                response="Triage failed: LLM adapter not configured.",
                recommended_next_agent="ErrorFallbackAgent",
                confidence_score=0.0,
                rationale="Internal configuration error."
            )

        context_str = json.dumps(context) if context else "No additional context provided."
        formatted_prompt = self.prompt_template.format(query=input_data.query, context_data=context_str)
        
        messages_for_llm = [{"role": "user", "content": formatted_prompt}]

        model_to_use = self.model_name or self.default_model_name

        try:
            self.logger.debug(f"Sending request to LLM ({model_to_use}) with prompt: {formatted_prompt}")
            llm_response = await self.llm_adapter.chat_completion(
                messages=messages_for_llm,
                model_name=model_to_use,
                temperature=0.5, # Example: can be tuned or made configurable
                # The prompt already asks for JSON, so PydanticAI integration or response_format for OpenAI could be future enhancements
            )

            if llm_response.error:
                self.logger.error(f"LLM API call failed: {llm_response.error}. Raw: {llm_response.raw_response}")
                return TriageAgentOutput(
                    response=f"Triage failed: LLM API error - {llm_response.error}",
                    recommended_next_agent="ErrorFallbackAgent",
                    confidence_score=0.0,
                    rationale=f"LLM API interaction failed: {llm_response.error[:100]}"
                )

            if not llm_response.content:
                self.logger.error("LLM response content is empty.")
                return TriageAgentOutput(
                    response="Triage failed: LLM returned empty content.",
                    recommended_next_agent="ErrorFallbackAgent",
                    confidence_score=0.0,
                    rationale="LLM provided no usable content for triage."
                )
            
            self.logger.debug(f"LLM ({model_to_use}) raw response content: {llm_response.content}")

            try:
                # Attempt to parse the LLM's string content (expected to be JSON)
                # into our TriageAgentOutput model.
                parsed_output = self.output_schema.model_validate_json(llm_response.content)
                # Ensure the 'response' field (from AgentOutput) is populated if the LLM doesn't directly set it.
                # The prompt asks for a JSON parsable into TriageAgentOutput, which includes 'response'.
                # If the LLM strictly follows the prompt for all TriageAgentOutput fields, this might be automatic.
                # If 'response' in the parsed_output is None or empty, we can add a default.
                if not parsed_output.response:
                    parsed_output.response = f"Triage decision for query '{input_data.query}' completed."
                self.logger.info(f"Successfully parsed LLM response into TriageAgentOutput for query: '{input_data.query}'")
                return parsed_output
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to decode LLM response JSON: {e}. Content: {llm_response.content}")
                return TriageAgentOutput(
                    response=f"Triage failed: Error decoding LLM JSON response.",
                    recommended_next_agent="ErrorFallbackAgent",
                    confidence_score=0.0,
                    rationale=f"LLM output was not valid JSON: {str(e)[:100]}"
                )
            except Exception as e: # Catches Pydantic ValidationError and others
                self.logger.error(f"Failed to validate LLM response against TriageAgentOutput schema: {e}. Content: {llm_response.content}")
                return TriageAgentOutput(
                    response=f"Triage failed: LLM response did not match expected output structure.",
                    recommended_next_agent="ErrorFallbackAgent",
                    confidence_score=0.0,
                    rationale=f"LLM output validation error: {str(e)[:100]}"
                )

        except Exception as e:
            self.logger.error(f"Unexpected error during TriageAgent.run: {e}", exc_info=True)
            return TriageAgentOutput(
                response=f"Triage failed: Unexpected error - {str(e)}",
                recommended_next_agent="ErrorFallbackAgent",
                confidence_score=0.0,
                rationale=f"An unexpected internal error occurred: {str(e)[:100]}"
            )

if __name__ == "__main__":
    print("MedflowAI TriageAgent module (now in agents package).")

    # Example Usage:
    # import asyncio
    # from medflowai.models.agent_io_models import AgentInput # Assuming path is set up

    # async def test_triage_agent():
    #     # In a real system, llm_adapter would be injected or globally available
    #     # For this example, we're testing the placeholder logic which doesn't use llm_adapter
    #     triage_agent_instance = TriageAgent() 
        
    #     test_input_1 = TriageAgentInput(query="What are the latest treatments for pediatric leukemia?")
    #     print(f"\nTesting with query: '{test_input_1.query}'")
    #     output_1 = await triage_agent_instance.run(input_data=test_input_1)
    #     print("Output 1:")
    #     print(output_1.model_dump_json(indent=2))

    #     test_input_2 = TriageAgentInput(query="Common side effects of amoxicillin.")
    #     print(f"\nTesting with query: '{test_input_2.query}'")
    #     output_2 = await triage_agent_instance.run(input_data=test_input_2)
    #     print("Output 2:")
    #     print(output_2.model_dump_json(indent=2))

    # # To run this example, ensure PYTHONPATH is set up if running from outside the package root
    # # e.g., export PYTHONPATH=$PYTHONPATH:/path/to/docia-platform
    # # asyncio.run(test_triage_agent())

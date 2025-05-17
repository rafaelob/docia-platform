"""
Medical Retrieval Augmented Generation (RAG) Agent for MedflowAI.

This agent is responsible for retrieving relevant medical information from configured
knowledge bases and using this information to generate comprehensive answers to user queries.
It utilizes RAG techniques and is a core component of the MedflowAI library.
"""

from typing import Type, Any, Optional, List, Dict 
from pydantic import BaseModel, Field, PrivateAttr 
import json 
import logging 

from ..core.base_agent import BaseAgent 
from ..models.agent_io_models import GenericInput, GenericOutput 
from ..tools.rag_tool import RAGTool, RAGToolOutput, RAGToolInput
from ..adapters.openai_adapter import OpenAIAdapter # Added OpenAIAdapter

class MedicalRAGAgentInput(GenericInput):
    # query is inherited from GenericInput
    knowledge_base_id: Optional[str] = Field(None, description="Specific knowledge base to target (e.g., 'cardiology_guidelines_v2').")
    search_query_override: Optional[str] = Field(None, description="Advanced use: Override the user's query for the RAG retrieval step.")
    top_k_retrieval: Optional[int] = Field(3, description="Number of documents to retrieve from RAG tool.")
    generate_summary: Optional[bool] = Field(False, description="Flag to indicate if a summary of retrieved documents is needed.")
    patient_context: Optional[str] = Field(None, description="Optional additional patient context to augment the query for retrieval and synthesis.")

class MedicalRAGAgentOutput(GenericOutput):
    # response is inherited from GenericOutput (this will be the synthesized answer)
    retrieved_documents: Optional[List[Dict[str, Any]]] = Field(None, description="List of document snippets/metadata retrieved and used for the answer.")
    full_explanation: Optional[str] = Field(None, description="A more detailed explanation or synthesis, if different from the main response.")
    sources_cited: Optional[List[str]] = Field(None, description="List of source identifiers (e.g., doc IDs, URLs) cited in the response.")
    error_message: Optional[str] = Field(None, description="Error message if the agent failed to process the query.")

class MedicalRAGAgent(BaseAgent):
    agent_name: str = "MedicalRAGAgent"
    description: str = "Retrieves information from medical knowledge bases using RAG and synthesizes answers to clinical queries, citing sources."
    
    # LLM adapter is inherited from BaseAgent and should be set during instantiation.
    # self.model_name can also be set in BaseAgent, defaults to gpt-4-turbo if not set.
    default_model_name: str = "gpt-4-turbo" # Default model if not set in BaseAgent
    model_name: Optional[str] = None

    # RAG tool instance
    rag_tool_instance: Optional[RAGTool] = None

    # Private logger attribute (not part of Pydantic validation)
    _logger: logging.Logger = PrivateAttr()

    # More sophisticated prompt template is recommended
    prompt_template: str = (
        "You are an AI Medical Information Specialist. Your task is to answer the user's clinical query "
        "based *solely* on the provided medical context. If the context is insufficient, state that clearly.\n\n"
        "User Query: \"{query}\"\n\n"
        "Provided Medical Context:\n"
        "-------------------------\n"
        "{retrieved_context_str}"
        "-------------------------\n\n"
        "Based on the context, provide a concise and factual answer to the user's query. "
        "Cite the source IDs (e.g., [sim_doc_id_1_general]) for each piece of information used in your answer. "
        "If you generate a summary, ensure it is based on the provided context.\n\n"
        "Answer:"
    )

    input_schema: Type[BaseModel] = MedicalRAGAgentInput
    output_schema: Type[BaseModel] = MedicalRAGAgentOutput

    def __init__(self, rag_tool: Optional[RAGTool] = None, llm_adapter: Optional[OpenAIAdapter] = None, **data: Any):
        # If no LLM adapter provided, create a default OpenAIAdapter instance (patched in tests).
        if llm_adapter is None:
            llm_adapter = OpenAIAdapter()

        super().__init__(llm_adapter=llm_adapter, **data)
        self._logger = logging.getLogger(__name__) # Initialize logger
        # In a real system, the RAGTool instance would likely be passed in or retrieved
        # from a ToolRegistry available to the agent/orchestrator.
        self.rag_tool_instance = rag_tool if rag_tool else RAGTool() # RAGTool now initializes fully or raises if env vars missing
        
        llm_adapter_status = "Provided" if llm_adapter else (
            "BaseAgent will default to OpenAIAdapter (if OPENAI_API_KEY is set)" if not self.llm_adapter else "Provided in BaseAgent"
        )
        self._logger.info(f"{self.agent_name} initialized. RAGTool: {'Provided' if rag_tool else 'Defaulted & Self-Initialized'}. LLMAdapter: {llm_adapter_status}")

    async def run(self, input_data: MedicalRAGAgentInput, context: Optional[Dict[str, Any]] = None) -> MedicalRAGAgentOutput:
        self._logger.info(f"{self.agent_name} running for query: '{input_data.query}' with KB: {input_data.knowledge_base_id}")

        if not self.rag_tool_instance:
            self._logger.error("RAGTool not configured for MedicalRAGAgent.")
            # Return a structured error output
            return MedicalRAGAgentOutput(
                response="Agent failed: RAG tool not configured.",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation="Internal configuration error: RAG tool missing.",
                error_message="RAG tool not configured",
            )
        
        if not self.llm_adapter:
            self._logger.error("LLMAdapter not configured for MedicalRAGAgent.")
            return MedicalRAGAgentOutput(
                response="Agent failed: LLM adapter not configured.",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation="Internal configuration error: LLM adapter missing.",
                error_message="LLM adapter not configured",
            )

        # 1. Use RAGTool to retrieve context
        if input_data.search_query_override:
            rag_query = input_data.search_query_override
        else:
            # Append patient context to the query if provided to enrich retrieval
            rag_query = (
                f"{input_data.query} {input_data.patient_context}".strip()
                if input_data.patient_context else input_data.query
            )
        try:
            from ..tools.rag_tool import RAGToolInput  # Local import to avoid circular issues
            rag_tool_input_obj = RAGToolInput(
                query=rag_query,
                knowledge_base_id=input_data.knowledge_base_id,
                top_k=input_data.top_k_retrieval,
            )
        except Exception:  # If model import fails, fallback to using raw string
            rag_tool_input_obj = None

        try:
            if rag_tool_input_obj is not None:
                rag_output: RAGToolOutput = await self.rag_tool_instance.execute(
                    rag_tool_input_obj,  # positional model obj for test inspection
                    knowledge_base_id=input_data.knowledge_base_id,
                    top_k=input_data.top_k_retrieval,
                )
            else:
                rag_output: RAGToolOutput = await self.rag_tool_instance.execute(
                    rag_query,
                    knowledge_base_id=input_data.knowledge_base_id,
                    top_k=input_data.top_k_retrieval,
                )
            self._logger.info(f"RAGTool executed. Retrieved {len(rag_output.retrieved_documents) if rag_output.retrieved_documents else 0} documents.")
        except Exception as e:
            self._logger.error(f"RAGTool execution failed: {e}", exc_info=True)
            return MedicalRAGAgentOutput(
                response=f"Agent failed: Error during RAG tool execution - {str(e)[:100]}",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation=f"RAGTool interaction failed: {str(e)}",
                error_message=str(e),
            )
        
        retrieved_docs_for_output = rag_output.retrieved_documents
        cited_sources_list = []
        context_parts_for_llm = []

        if retrieved_docs_for_output:
            for doc in retrieved_docs_for_output:
                content = doc.get("content", "N/A")
                source_id = doc.get("id", "Unknown Source")
                # Format for LLM context, can be adjusted
                context_parts_for_llm.append(f"Source ID: {source_id}\nContent: {content}")
                cited_sources_list.append(source_id)
        
        context_str_for_llm = (
            "\n\n".join(context_parts_for_llm)
            if context_parts_for_llm
            else "No specific context was retrieved from the knowledge base for this query."
        )
        self._logger.debug(f"Context for LLM: {context_str_for_llm[:500]}...")

        # 2. Prepare prompt with retrieved context for the LLM
        # Incorporate patient context (if any) into the user query portion of the prompt
        query_for_prompt = rag_query  # Already contains patient_context when applicable
        formatted_prompt = self.prompt_template.format(query=query_for_prompt, retrieved_context_str=context_str_for_llm)
        messages_for_llm = [{"role": "user", "content": formatted_prompt}]
        model_to_use = self.model_name or self.default_model_name

        # 3. Call LLM to synthesize the answer
        output_error_message: Optional[str] = None
        try:
            self._logger.debug(f"Sending synthesis request to LLM ({model_to_use})")
            llm_api_response = await self.llm_adapter.chat_completion(
                messages_for_llm,  # positional arg for tests
                model_name=model_to_use,
                temperature=0.3,  # Can be tuned
            )

            # Allow for `error` field or legacy/extra `error_message`
            error_detail = getattr(llm_api_response, "error", None)
            if not error_detail:
                # Attempt to fetch directly if stored as extra field
                error_detail = getattr(llm_api_response, "error_message", None)
            if not error_detail and hasattr(llm_api_response, "__dict__"):
                error_detail = llm_api_response.__dict__.get("error_message")
            # Pydantic V2 stores extras in `model_extra`
            if not error_detail and hasattr(llm_api_response, "model_extra"):
                error_detail = llm_api_response.model_extra.get("error_message")

            if error_detail:
                # Failure scenario expected by unit tests
                output_error_message = error_detail
                self._logger.error(
                    f"LLM API call for synthesis failed: {output_error_message}. Raw: {llm_api_response.raw_response}"
                )
                synthesized_answer = f"Error: LLM processing failed. Details: {output_error_message}"
                explanation = f"LLM API interaction failed during synthesis: {output_error_message[:100]}"
                # On LLM failure we do not surface potentially irrelevant docs
                retrieved_docs_for_output = []
            elif not llm_api_response.content:
                self._logger.error("LLM synthesis response content is empty.")
                synthesized_answer = "Failed to synthesize answer: LLM returned empty content."
                explanation = "LLM provided no usable content for synthesis."
            else:
                synthesized_answer = llm_api_response.content
                explanation = (
                    f"Answer synthesized using {len(context_parts_for_llm)} document(s) and LLM ({model_to_use})."
                )
                self._logger.info(
                    f"Successfully synthesized answer from LLM for query: '{input_data.query}'"
                )

        except Exception as e:
            output_error_message = str(e)
            self._logger.error(f"Unexpected error during LLM synthesis: {e}", exc_info=True)
            synthesized_answer = f"Failed to synthesize answer: Unexpected error - {str(e)}"
            explanation = f"An unexpected internal error occurred during synthesis: {str(e)[:100]}"

        return MedicalRAGAgentOutput(
            response=synthesized_answer,
            retrieved_documents=retrieved_docs_for_output,
            full_explanation=explanation,
            sources_cited=cited_sources_list,
            error_message=output_error_message,
        )

if __name__ == "__main__":
    print("MedflowAI MedicalRAGAgent module (now in agents package).")

    # Configure basic logging to see agent logs during testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    async def test_medical_rag_agent():
        logger.info("Starting MedicalRAGAgent test...")
        print("\n" + "="*50)
        print("IMPORTANT: Ensure the following environment variables are set for this test:")
        print("  - OPENAI_API_KEY (for RAG embeddings and LLM synthesis)")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        print("If these are not set, RAGTool or OpenAIAdapter initialization will fail.")
        print("="*50 + "\n")

        # MedicalRAGAgent will instantiate RAGTool() by default if not provided.
        # It will also use a default OpenAIAdapter if llm_adapter is not provided and OPENAI_API_KEY is set.
        try:
            medical_rag_agent_instance = MedicalRAGAgent()
            
            test_input = MedicalRAGAgentInput(
                query="What are common treatments for pediatric asthma exacerbation?", 
                knowledge_base_id="pediatrics_guidelines_v3", # Example KB ID
                top_k_retrieval=2
            )
            logger.info(f"Testing MedicalRAGAgent with query: '{test_input.query}' for KB ID: '{test_input.knowledge_base_id}'")
            output = await medical_rag_agent_instance.run(input_data=test_input)
            
            print("\nMedicalRAGAgent Output:")
            print(output.model_dump_json(indent=2))
        except ValueError as ve:
            logger.error(f"Failed to initialize agent or tool, likely due to missing environment variables: {ve}")
            print(f"ERROR: Test failed due to missing configuration: {ve}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the test: {e}", exc_info=True)
            print(f"ERROR: Test failed unexpectedly: {e}")

    import asyncio
    # Ensure PYTHONPATH includes the project root for imports to work from top level
    # e.g., in VSCode, launch.json might need "env": {"PYTHONPATH": "${workspaceFolder}"}
    # or run as `python -m packages.libs.medflowai.agents.medical_rag_agent` from project root.
    asyncio.run(test_medical_rag_agent())

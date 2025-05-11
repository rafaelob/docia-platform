"""
Medical Retrieval Augmented Generation (RAG) Agent for MedflowAI.

This agent is responsible for retrieving relevant medical information from configured
knowledge bases and using this information to generate comprehensive answers to user queries.
It utilizes RAG techniques and is a core component of the MedflowAI library.
"""

from typing import Type, Any, Optional, List, Dict 
from pydantic import BaseModel, Field 
import json 
import logging 

from ..core.base_agent import BaseAgent 
from ..models.agent_io_models import AgentInput, AgentOutput 
from ..tools.rag_tool import RAGTool, RAGToolOutput 
from ..adapters.openai_adapter import OpenAIAdapter # Added OpenAIAdapter

class MedicalRAGAgentInput(AgentInput):
    # query is inherited from AgentInput
    knowledge_base_id: Optional[str] = Field(None, description="Specific knowledge base to target (e.g., 'cardiology_guidelines_v2').")
    search_query_override: Optional[str] = Field(None, description="Advanced use: Override the user's query for the RAG retrieval step.")
    top_k_retrieval: Optional[int] = Field(3, description="Number of documents to retrieve from RAG tool.")
    generate_summary: Optional[bool] = Field(False, description="Flag to indicate if a summary of retrieved documents is needed.")

class MedicalRAGAgentOutput(AgentOutput):
    # response is inherited from AgentOutput (this will be the synthesized answer)
    retrieved_documents: Optional[List[Dict[str, Any]]] = Field(None, description="List of document snippets/metadata retrieved and used for the answer.")
    full_explanation: Optional[str] = Field(None, description="A more detailed explanation or synthesis, if different from the main response.")
    sources_cited: Optional[List[str]] = Field(None, description="List of source identifiers (e.g., doc IDs, URLs) cited in the response.")

class MedicalRAGAgent(BaseAgent):
    agent_name: str = "MedicalRAGAgent"
    description: str = "Retrieves information from medical knowledge bases using RAG and synthesizes answers to clinical queries, citing sources."
    
    # LLM adapter is inherited from BaseAgent and should be set during instantiation.
    # self.model_name can also be set in BaseAgent, defaults to gpt-4-turbo if not set.
    default_model_name: str = "gpt-4-turbo" # Default model if not set in BaseAgent

    # RAG tool instance
    rag_tool_instance: Optional[RAGTool] = None

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
        super().__init__(llm_adapter=llm_adapter, **data)
        self.logger = logging.getLogger(__name__) # Initialize logger
        # In a real system, the RAGTool instance would likely be passed in or retrieved
        # from a ToolRegistry available to the agent/orchestrator.
        self.rag_tool_instance = rag_tool if rag_tool else RAGTool() # RAGTool now initializes fully or raises if env vars missing
        
        llm_adapter_status = "Provided" if llm_adapter else (
            "BaseAgent will default to OpenAIAdapter (if OPENAI_API_KEY is set)" if not self.llm_adapter else "Provided in BaseAgent"
        )
        self.logger.info(f"{self.agent_name} initialized. RAGTool: {'Provided' if rag_tool else 'Defaulted & Self-Initialized'}. LLMAdapter: {llm_adapter_status}")

    async def run(self, input_data: MedicalRAGAgentInput, context: Optional[Dict[str, Any]] = None) -> MedicalRAGAgentOutput:
        self.logger.info(f"{self.agent_name} running for query: '{input_data.query}' with KB: {input_data.knowledge_base_id}")

        if not self.rag_tool_instance:
            self.logger.error("RAGTool not configured for MedicalRAGAgent.")
            # Return a structured error output
            return MedicalRAGAgentOutput(
                response="Agent failed: RAG tool not configured.",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation="Internal configuration error: RAG tool missing."
            )
        
        if not self.llm_adapter:
            self.logger.error("LLMAdapter not configured for MedicalRAGAgent.")
            return MedicalRAGAgentOutput(
                response="Agent failed: LLM adapter not configured.",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation="Internal configuration error: LLM adapter missing."
            )

        # 1. Use RAGTool to retrieve context
        rag_query = input_data.search_query_override if input_data.search_query_override else input_data.query
        try:
            rag_output: RAGToolOutput = await self.rag_tool_instance.execute(
                query=rag_query,
                knowledge_base_id=input_data.knowledge_base_id,
                top_k=input_data.top_k_retrieval
            )
            self.logger.info(f"RAGTool executed. Retrieved {len(rag_output.retrieved_documents) if rag_output.retrieved_documents else 0} documents.")
        except Exception as e:
            self.logger.error(f"RAGTool execution failed: {e}", exc_info=True)
            return MedicalRAGAgentOutput(
                response=f"Agent failed: Error during RAG tool execution - {str(e)[:100]}",
                retrieved_documents=None,
                sources_cited=None,
                full_explanation=f"RAGTool interaction failed: {str(e)}"
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
        
        context_str_for_llm = "\n\n".join(context_parts_for_llm) if context_parts_for_llm else "No relevant documents found."
        self.logger.debug(f"Context for LLM: {context_str_for_llm[:500]}...")

        # 2. Prepare prompt with retrieved context for the LLM
        formatted_prompt = self.prompt_template.format(query=input_data.query, retrieved_context_str=context_str_for_llm)
        messages_for_llm = [{"role": "user", "content": formatted_prompt}]
        model_to_use = self.model_name or self.default_model_name

        # 3. Call LLM to synthesize the answer
        try:
            self.logger.debug(f"Sending synthesis request to LLM ({model_to_use})")
            llm_api_response = await self.llm_adapter.chat_completion(
                messages=messages_for_llm,
                model_name=model_to_use,
                temperature=0.3 # Can be tuned
            )

            if llm_api_response.error:
                self.logger.error(f"LLM API call for synthesis failed: {llm_api_response.error}. Raw: {llm_api_response.raw_response}")
                synthesized_answer = f"Failed to synthesize answer: LLM API error - {llm_api_response.error}"
                explanation = f"LLM API interaction failed during synthesis: {llm_api_response.error[:100]}"
            elif not llm_api_response.content:
                self.logger.error("LLM synthesis response content is empty.")
                synthesized_answer = "Failed to synthesize answer: LLM returned empty content."
                explanation = "LLM provided no usable content for synthesis."
            else:
                synthesized_answer = llm_api_response.content
                explanation = f"Answer synthesized using {len(context_parts_for_llm)} document(s) and LLM ({model_to_use})."
                self.logger.info(f"Successfully synthesized answer from LLM for query: '{input_data.query}'")

        except Exception as e:
            self.logger.error(f"Unexpected error during LLM synthesis: {e}", exc_info=True)
            synthesized_answer = f"Failed to synthesize answer: Unexpected error - {str(e)}"
            explanation = f"An unexpected internal error occurred during synthesis: {str(e)[:100]}"

        return MedicalRAGAgentOutput(
            response=synthesized_answer,
            retrieved_documents=retrieved_docs_for_output,
            full_explanation=explanation,
            sources_cited=cited_sources_list
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

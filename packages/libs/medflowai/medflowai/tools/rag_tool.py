"""
Retrieval Augmented Generation (RAG) Tool for MedflowAI.

This tool is responsible for interacting with a RAG system (e.g., vector database, 
reranker) to fetch relevant documents from a knowledge base for a given query. 
It is designed to be used by agents within the MedflowAI library.
"""

from typing import Type, Any, List, Dict, Optional, Tuple
from pydantic import BaseModel, Field, PrivateAttr
from .base_tool import BaseTool # Correct: base_tool is in the same directory
import os
from supabase.client import Client, create_client
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document

class RAGToolInput(BaseModel):
    query: str = Field(..., description="The search query to retrieve relevant documents.")
    knowledge_base_id: Optional[str] = Field(None, description="Identifier for a specific knowledge base to target, if applicable.")
    top_k: Optional[int] = Field(5, description="The number of top documents to retrieve.")
    # Future RAG-specific parameters: filters, reranking flags, patient_context_id, etc.

class RAGToolOutput(BaseModel):
    retrieved_documents: List[Dict[str, Any]] = Field(..., description="A list of retrieved documents, each potentially containing content, metadata, score, etc.")
    # Example document: {"id": "doc_123", "content": "...", "source": "pubmed/xyz", "score": 0.9}
    summary: Optional[str] = Field(None, description="An optional summary of the retrieved documents, if generated.")

DEFAULT_KNOWLEDGE_BASE_TABLE = "documents"
DEFAULT_VECTOR_QUERY_FUNCTION = "match_documents"

class RAGTool(BaseTool):
    name: str = "medical_knowledge_retriever"
    description: str = "Searches a medical knowledge base for documents relevant to a clinical query using RAG techniques. Returns structured document snippets."
    input_schema: Type[BaseModel] = RAGToolInput
    output_schema: Type[BaseModel] = RAGToolOutput

    # Runtime-only attributes (not part of Pydantic validation)
    _vector_store: SupabaseVectorStore = PrivateAttr()
    _embeddings: OpenAIEmbeddings = PrivateAttr()
    _supabase_client: Client = PrivateAttr()

    def __init__(self, **data: Any):
        super().__init__(**data)
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        if not supabase_url:
            raise ValueError("SUPABASE_URL environment variable not set.")
        if not supabase_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable not set.")

        # Use 'api_key' named param for compatibility with tests' mock expectations
        self._embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        self._supabase_client = create_client(supabase_url, supabase_key)
        
        self._vector_store = SupabaseVectorStore(
            client=self._supabase_client,
            embedding=self._embeddings,
            table_name=DEFAULT_KNOWLEDGE_BASE_TABLE,
            query_name=DEFAULT_VECTOR_QUERY_FUNCTION
        )
        # print("Info: RAGTool initialized with SupabaseVectorStore.")

    async def execute(self, query: str, knowledge_base_id: Optional[str] = None, top_k: Optional[int] = 5, **kwargs: Any) -> RAGToolOutput:
        # print(f"RAGTool executing search for query: '{query}', KB: {knowledge_base_id}, top_k: {top_k}")
        
        search_kwargs = {}
        if knowledge_base_id:
            search_kwargs['filter'] = {"knowledge_base_id": knowledge_base_id}

        # Ensure top_k is not None and is positive, as expected by Langchain's k
        effective_top_k = top_k if top_k is not None and top_k > 0 else 5

        try:
            documents_with_scores: List[Tuple[Document, float]] = \
                await self._vector_store.asimilarity_search_with_relevance_scores(
                    query=query,
                    k=effective_top_k,
                    filter=search_kwargs.get('filter', None),
                )
        except Exception as e:
            # print(f"Error during RAGTool vector search: {e}")
            # Consider more specific error handling or logging
            # For now, return empty results or re-raise as appropriate for the agent framework
            return RAGToolOutput(retrieved_documents=[], summary=f"Error during search: {str(e)}")

        retrieved_documents: List[Dict[str, Any]] = []
        for idx, (doc, score) in enumerate(documents_with_scores):
            retrieved_documents.append({
                "id": doc.metadata.get("id", f"retrieved_doc_{idx}"),
                "content": doc.page_content,
                "source": doc.metadata.get("source"),
                "score": score,
                "metadata": doc.metadata
            })
        
        return RAGToolOutput(retrieved_documents=retrieved_documents, summary=None)

if __name__ == "__main__":
    print("MedflowAI RAGTool module (now in tools package).")
    
    async def test_rag_tool():
        rag_tool = RAGTool()
        print(f"\nTool: {rag_tool.name}\nDescription: {rag_tool.description}")
        print(f"LLM Schema:\n{rag_tool.to_llm_schema()}")
        
        test_query = "treatment options for pediatric asthma exacerbation"
        print(f"\nExecuting RAGTool with query: '{test_query}'")
        output = await rag_tool.execute(query=test_query, knowledge_base_id="pediatrics_v2", top_k=3)
        
        print("\nTool Execution Output:")
        print(output.model_dump_json(indent=2))

    import asyncio
    asyncio.run(test_rag_tool())

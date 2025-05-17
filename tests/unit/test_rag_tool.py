import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

from langchain_core.documents import Document

from medflowai.tools.rag_tool import RAGTool, RAGToolInput, RAGToolOutput
from supabase.client import create_client

# Define a fixture for the RAGTool instance if needed, or initialize in each test

@pytest.mark.asyncio
async def test_rag_tool_execute_success():
    """Test RAGTool execute method for successful document retrieval."""
    # Mock OpenAIEmbeddings
    mock_embeddings_instance = MagicMock()
    # mock_embeddings_instance.aembed_query = AsyncMock(return_value=[0.1, 0.2, 0.3]) # Example if direct call was needed

    # Mock SupabaseVectorStore
    mock_vector_store_instance = AsyncMock() # For the class instance
    mock_retrieved_docs_with_scores = [
        (Document(page_content="Test content 1", metadata={"source": "doc1", "id": "kb1-doc1"}), 0.9),
        (Document(page_content="Test content 2", metadata={"source": "doc2", "id": "kb1-doc2"}), 0.8)
    ]
    mock_vector_store_instance.asimilarity_search_with_relevance_scores = AsyncMock(
        return_value=mock_retrieved_docs_with_scores
    )
    mock_supabase_client_instance = MagicMock() # Mock for supabase client

    # Patch the LangChain components within the rag_tool module's scope
    with patch('medflowai.tools.rag_tool.os.getenv') as mock_os_getenv, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=mock_embeddings_instance) as mock_openai_embeddings, \
         patch('medflowai.tools.rag_tool.create_client', return_value=mock_supabase_client_instance) as mock_create_client, \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=mock_vector_store_instance) as mock_supabase_vector_store:
        
        # Mock os.getenv calls within RAGTool.__init__
        mock_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_key",
            "OPENAI_API_KEY": "mock_api_key",
        }.get(key, default)

        # Instantiating RAGTool should now work because __init__ dependencies are mocked
        rag_tool = RAGTool() 

        input_data = RAGToolInput(query="test query", top_k=2)
        result = await rag_tool.execute(**input_data.model_dump())

        # Assertions
        assert isinstance(result, RAGToolOutput)
        assert len(result.retrieved_documents) == 2 
        assert result.retrieved_documents[0]['id'] == "kb1-doc1" 
        assert result.retrieved_documents[0]['content'] == "Test content 1" 
        assert result.retrieved_documents[0]['score'] == 0.9 
        assert result.retrieved_documents[0]['metadata'] == {"source": "doc1", "id": "kb1-doc1"}
        assert result.retrieved_documents[1]['id'] == "kb1-doc2" 

        # Check that SupabaseVectorStore was called correctly
        mock_supabase_vector_store.from_documents.assert_not_called() # Should use existing table
        mock_vector_store_instance.asimilarity_search_with_relevance_scores.assert_called_once_with(
            query="test query",
            k=2,
            filter=None # No knowledge_base_id in this test
        )
        # Check that OpenAIEmbeddings was instantiated
        mock_openai_embeddings.assert_called_once_with(api_key="mock_api_key")

@pytest.mark.asyncio
async def test_rag_tool_execute_with_knowledge_base_id():
    """Test RAGTool execute method with knowledge_base_id filter."""
    mock_embeddings_instance = MagicMock()
    mock_vector_store_instance = AsyncMock()
    mock_retrieved_docs_with_scores = [
        (Document(page_content="Filtered content", metadata={"source": "doc_filtered", "id": "kb2-doc1", "knowledge_base_id": "kb2"}), 0.85)
    ]
    mock_vector_store_instance.asimilarity_search_with_relevance_scores = AsyncMock(
        return_value=mock_retrieved_docs_with_scores
    )
    mock_supabase_client_instance = MagicMock()

    with patch('medflowai.tools.rag_tool.os.getenv') as mock_os_getenv, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=mock_embeddings_instance), \
         patch('medflowai.tools.rag_tool.create_client', return_value=mock_supabase_client_instance), \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=mock_vector_store_instance):

        mock_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_key",
            "OPENAI_API_KEY": "mock_api_key",
        }.get(key, default)

        rag_tool = RAGTool()
        result = await rag_tool.execute(query="filter query", knowledge_base_id="kb2", top_k=1)

        assert len(result.retrieved_documents) == 1 
        assert result.retrieved_documents[0]['id'] == "kb2-doc1" 
        assert result.retrieved_documents[0]['metadata'].get("knowledge_base_id") == "kb2"

        expected_filter = {'knowledge_base_id': 'kb2'}
        mock_vector_store_instance.asimilarity_search_with_relevance_scores.assert_called_once_with(
            query="filter query",
            k=1,
            filter=expected_filter
        )

@pytest.mark.asyncio
async def test_rag_tool_execute_no_documents_found():
    """Test RAGTool execute method when no documents are found by the vector store."""
    mock_embeddings_instance = MagicMock()
    mock_vector_store_instance = AsyncMock()
    # Simulate no documents found
    mock_vector_store_instance.asimilarity_search_with_relevance_scores = AsyncMock(return_value=[])
    mock_supabase_client_instance = MagicMock()

    with patch('medflowai.tools.rag_tool.os.getenv') as mock_os_getenv, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=mock_embeddings_instance), \
         patch('medflowai.tools.rag_tool.create_client', return_value=mock_supabase_client_instance), \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=mock_vector_store_instance):

        mock_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_key",
            "OPENAI_API_KEY": "mock_api_key",
        }.get(key, default)

        rag_tool = RAGTool()
        result = await rag_tool.execute(query="query for no docs", top_k=5)

        assert isinstance(result, RAGToolOutput)
        assert len(result.retrieved_documents) == 0 
        mock_vector_store_instance.asimilarity_search_with_relevance_scores.assert_called_once_with(
            query="query for no docs",
            k=5,
            filter=None
        )

@pytest.mark.asyncio
async def test_rag_tool_execute_top_k_respected():
    """Test RAGTool execute method respects the top_k parameter."""
    mock_embeddings_instance = MagicMock()
    mock_vector_store_instance = AsyncMock()
    # Simulate vector store returning exactly top_k documents
    mock_retrieved_docs_with_scores = [
        (Document(page_content="Content 1", metadata={"id": "doc1"}), 0.9),
        (Document(page_content="Content 2", metadata={"id": "doc2"}), 0.8)
    ]
    mock_vector_store_instance.asimilarity_search_with_relevance_scores = AsyncMock(
        return_value=mock_retrieved_docs_with_scores
    )
    mock_supabase_client_instance = MagicMock()

    with patch('medflowai.tools.rag_tool.os.getenv') as mock_os_getenv, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=mock_embeddings_instance), \
         patch('medflowai.tools.rag_tool.create_client', return_value=mock_supabase_client_instance), \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=mock_vector_store_instance):

        mock_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_key",
            "OPENAI_API_KEY": "mock_api_key",
        }.get(key, default)

        rag_tool = RAGTool()
        # Request top_k=2
        result = await rag_tool.execute(query="test top k", top_k=2)

        assert isinstance(result, RAGToolOutput)
        assert len(result.retrieved_documents) == 2 

        mock_vector_store_instance.asimilarity_search_with_relevance_scores.assert_called_once_with(
            query="test top k",
            k=2, 
            filter=None
        )

# More tests to come: etc.

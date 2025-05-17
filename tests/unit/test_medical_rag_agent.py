# Unit tests for MedicalRAGAgent will go here

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from medflowai.agents.medical_rag_agent import MedicalRAGAgent, MedicalRAGAgentInput, MedicalRAGAgentOutput
from medflowai.tools.rag_tool import RAGToolOutput
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import create_client 

from medflowai.adapters.base_llm_adapter import UnifiedLLMResponse


@pytest.mark.asyncio
async def test_medical_rag_agent_run_success():
    """Test MedicalRAGAgent run method for successful execution."""
    # Mock RAGTool's execute method
    mock_rag_tool_instance = AsyncMock()
    mock_rag_output = RAGToolOutput(
        retrieved_documents=[
            {"id": "doc1", "content": "Relevant context from RAG.", "score": 0.9, "metadata": {}, "source": "mock_source1"} 
        ]
    )
    mock_rag_tool_instance.execute = AsyncMock(return_value=mock_rag_output)

    # Mock LLMAdapter's chat_completion method
    mock_llm_adapter_instance = AsyncMock()
    mock_llm_response = UnifiedLLMResponse(
        success=True,
        content="Synthesized answer based on context.",
        raw_response=MagicMock(),
        error_message=None,
        tool_calls=None
    )
    mock_llm_adapter_instance.chat_completion = AsyncMock(return_value=mock_llm_response)

    # Patch Agent's LLM Adapter and the RAGTool CLASS it might instantiate
    # Also patch RAGTool's *internal* dependencies if it gets instantiated
    with patch('medflowai.agents.medical_rag_agent.OpenAIAdapter', return_value=mock_llm_adapter_instance) as mock_llm_adapter_class, \
         patch('medflowai.agents.medical_rag_agent.RAGTool', return_value=mock_rag_tool_instance) as mock_rag_tool_class, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=MagicMock()) as mock_rag_embeddings, \
         patch('medflowai.tools.rag_tool.create_client', return_value=MagicMock()) as mock_rag_create_client, \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=MagicMock()) as mock_rag_vector_store, \
         patch('medflowai.tools.rag_tool.os.getenv') as mock_rag_os_getenv: 

        # Mock os.getenv for RAGTool's __init__ if it gets called
        mock_rag_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_rag_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key",
            "OPENAI_API_KEY": "mock_rag_llm_key",
        }.get(key, default)

        # Mock os.getenv for the Agent's potential direct use (if any)
        with patch('os.getenv') as mock_agent_os_getenv:
            mock_agent_os_getenv.side_effect = lambda key, default=None: {
                "OPENAI_API_KEY": "mock_agent_llm_key", 
                # Include RAG keys here too in case agent reads them directly before passing to RAGTool
                "SUPABASE_URL": "mock_rag_url_agent", 
                "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key_agent", 
            }.get(key, default)

            # Instantiate the agent. It might use the mocked RAGTool class OR try to instantiate one itself.
            # The patches for RAGTool's internals will cover the self-instantiation case.
            agent = MedicalRAGAgent() 

            input_data = MedicalRAGAgentInput(query="What is the treatment for condition X?", patient_context="Patient is Y years old.")
            result = await agent.run(input_data)

            assert isinstance(result, MedicalRAGAgentOutput)
            assert result.answer == "Synthesized answer based on context."
            # Adjust to use retrieved_documents and dictionary access
            assert len(result.retrieved_documents) == 1 
            assert result.retrieved_documents[0]['id'] == "doc1" 
            assert result.retrieved_documents[0]['content'] == "Relevant context from RAG." 

            # Verify RAGTool was called correctly
            mock_rag_tool_class.assert_called_once() 
            expected_rag_input_query = "What is the treatment for condition X? Patient is Y years old."
            # Access the arguments of the call to execute on the *instance*
            mock_rag_tool_instance.execute.assert_called_once()
            call_args, _ = mock_rag_tool_instance.execute.call_args
            assert call_args[0].query == expected_rag_input_query
            # assert call_args[0].knowledge_base_id is None 
            # assert call_args[0].top_k == agent.rag_top_k 

            # Verify LLMAdapter was called correctly
            mock_llm_adapter_class.assert_called_once() 
            mock_llm_adapter_instance.chat_completion.assert_called_once()
            # Inspect the messages passed to the LLM
            llm_call_args, llm_call_kwargs = mock_llm_adapter_instance.chat_completion.call_args
            messages = llm_call_args[0]
            assert any(expected_rag_input_query in msg['content'] for msg in messages if msg['role'] == 'user')
            assert any("Relevant context from RAG." in msg['content'] for msg in messages if msg['role'] == 'user' or msg['role'] == 'system')

@pytest.mark.asyncio
async def test_medical_rag_agent_run_no_rag_context():
    """Test MedicalRAGAgent run method when RAGTool finds no context."""
    mock_rag_tool_instance = AsyncMock()
    # RAGTool returns empty list for retrieved_documents
    mock_rag_no_context_output = RAGToolOutput(retrieved_documents=[]) 
    mock_rag_tool_instance.execute = AsyncMock(return_value=mock_rag_no_context_output)

    mock_llm_adapter_instance = AsyncMock()
    mock_llm_response = UnifiedLLMResponse(
        success=True,
        content="General answer, as no specific context was found.",
        raw_response=MagicMock(),
        error_message=None,
        tool_calls=None
    )
    mock_llm_adapter_instance.chat_completion = AsyncMock(return_value=mock_llm_response)

    # Apply the same comprehensive patching strategy
    with patch('medflowai.agents.medical_rag_agent.OpenAIAdapter', return_value=mock_llm_adapter_instance) as mock_llm_adapter_class, \
         patch('medflowai.agents.medical_rag_agent.RAGTool', return_value=mock_rag_tool_instance) as mock_rag_tool_class, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=MagicMock()) as mock_rag_embeddings, \
         patch('medflowai.tools.rag_tool.create_client', return_value=MagicMock()) as mock_rag_create_client, \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=MagicMock()) as mock_rag_vector_store, \
         patch('medflowai.tools.rag_tool.os.getenv') as mock_rag_os_getenv:

        mock_rag_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_rag_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key",
            "OPENAI_API_KEY": "mock_rag_llm_key",
        }.get(key, default)

        with patch('os.getenv') as mock_agent_os_getenv:
            mock_agent_os_getenv.side_effect = lambda key, default=None: {
                "OPENAI_API_KEY": "mock_agent_llm_key", 
                "SUPABASE_URL": "mock_rag_url_agent", 
                "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key_agent", 
            }.get(key, default)

            agent = MedicalRAGAgent()
            input_data = MedicalRAGAgentInput(query="Query with no context match?", patient_context="Patient details.")
            result = await agent.run(input_data)

            assert isinstance(result, MedicalRAGAgentOutput)
            assert result.answer == "General answer, as no specific context was found."
            assert len(result.retrieved_documents) == 0   # Check retrieved_documents

            mock_rag_tool_instance.execute.assert_called_once()
            mock_llm_adapter_instance.chat_completion.assert_called_once()

            # Verify the context part of the prompt passed to the LLM
            llm_call_args, _ = mock_llm_adapter_instance.chat_completion.call_args
            messages = llm_call_args[0]
            user_message_content = next((msg['content'] for msg in messages if msg['role'] == 'user'), None)
            assert user_message_content is not None
            # Based on agent's logic when no context is found:
            expected_context_str_in_prompt = "No specific context was retrieved from the knowledge base for this query."
            assert expected_context_str_in_prompt in user_message_content
            assert "Query with no context match? Patient details." in user_message_content

@pytest.mark.asyncio
async def test_medical_rag_agent_run_llm_failure():
    """Test MedicalRAGAgent run method when LLMAdapter reports a failure."""
    mock_rag_tool_instance = AsyncMock()
    mock_rag_output = RAGToolOutput(
        retrieved_documents=[
            {"id": "doc1", "content": "Some context.", "score": 0.8, "metadata": {}, "source": "mock_source_fail"} 
        ]
    )
    mock_rag_tool_instance.execute = AsyncMock(return_value=mock_rag_output)

    mock_llm_adapter_instance = AsyncMock()
    # Simulate LLM failure
    mock_llm_failure_response = UnifiedLLMResponse(
        success=False,
        content=None,
        raw_response=MagicMock(),
        error_message="LLM API error: Rate limit exceeded.",
        tool_calls=None
    )
    mock_llm_adapter_instance.chat_completion = AsyncMock(return_value=mock_llm_failure_response)

    # Apply the same comprehensive patching strategy
    with patch('medflowai.agents.medical_rag_agent.OpenAIAdapter', return_value=mock_llm_adapter_instance) as mock_llm_adapter_class, \
         patch('medflowai.agents.medical_rag_agent.RAGTool', return_value=mock_rag_tool_instance) as mock_rag_tool_class, \
         patch('medflowai.tools.rag_tool.OpenAIEmbeddings', return_value=MagicMock()) as mock_rag_embeddings, \
         patch('medflowai.tools.rag_tool.create_client', return_value=MagicMock()) as mock_rag_create_client, \
         patch('medflowai.tools.rag_tool.SupabaseVectorStore', return_value=MagicMock()) as mock_rag_vector_store, \
         patch('medflowai.tools.rag_tool.os.getenv') as mock_rag_os_getenv:

        mock_rag_os_getenv.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "mock_rag_url",
            "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key",
            "OPENAI_API_KEY": "mock_rag_llm_key",
        }.get(key, default)

        with patch('os.getenv') as mock_agent_os_getenv:
            mock_agent_os_getenv.side_effect = lambda key, default=None: {
                "OPENAI_API_KEY": "mock_agent_llm_key", 
                "SUPABASE_URL": "mock_rag_url_agent", 
                "SUPABASE_SERVICE_ROLE_KEY": "mock_rag_key_agent", 
            }.get(key, default)

            agent = MedicalRAGAgent()
            input_data = MedicalRAGAgentInput(query="A valid query.", patient_context="Patient info.")
            result = await agent.run(input_data)

            assert isinstance(result, MedicalRAGAgentOutput)
            assert result.answer == "Error: LLM processing failed. Details: LLM API error: Rate limit exceeded."
            # Current agent implementation clears sources on LLM failure, so empty is correct.
            assert result.retrieved_documents == []  # Check retrieved_documents
            assert result.error == "LLM API error: Rate limit exceeded."

            mock_rag_tool_instance.execute.assert_called_once()
            mock_llm_adapter_instance.chat_completion.assert_called_once()

# More tests to come: LLM failure, etc.

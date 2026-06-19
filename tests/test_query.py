import os
from unittest.mock import patch, MagicMock
from langchain_community.chat_models import FakeListChatModel
from core.query import get_conversational_rag_chain
from core.memory import get_file_chat_history, clear_session_history

@patch('core.query.ChatGroq')
@patch('core.query.get_retriever')
def test_chain_generation(mock_get_retriever, mock_chat_groq):
    # Setup mock retriever
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_get_retriever.return_value = mock_retriever
    
    # Since chat history is empty, create_history_aware_retriever bypasses the LLM rephrasing call.
    # Therefore, the LLM is only called once (for the QA answer).
    fake_llm = FakeListChatModel(responses=["This is a mocked answer."])
    mock_chat_groq.return_value = fake_llm
    
    # Setup test session
    session_id = "test_session_1"
    clear_session_history(session_id)
    
    try:
        # Get conversational chain
        chain = get_conversational_rag_chain(session_id)
        
        # Execute query
        response = chain.invoke(
            {"input": "What is attention?"},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Assertions
        assert "answer" in response
        assert response["answer"] == "This is a mocked answer."
    finally:
        # Clean up
        clear_session_history(session_id)

@patch('core.query.ChatGroq')
@patch('core.query.get_retriever')
def test_memory_integration(mock_get_retriever, mock_chat_groq):
    session_id = "test_memory_session"
    clear_session_history(session_id)
    
    # Setup mock retriever
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_get_retriever.return_value = mock_retriever
    
    # Trace of LLM calls:
    # 1. First question (history empty) -> rephrase bypassed -> QA runs (consumes "Answer 1")
    # 2. Second question (history populated) -> rephrase runs (consumes "standalone question 2") -> QA runs (consumes "Answer 2")
    fake_llm = FakeListChatModel(responses=[
        "Answer 1",
        "standalone question 2",
        "Answer 2"
    ])
    mock_chat_groq.return_value = fake_llm
    
    try:
        chain = get_conversational_rag_chain(session_id)
        
        # Send first question
        chain.invoke(
            {"input": "First question"},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Send second question (follow up)
        chain.invoke(
            {"input": "Second question"},
            config={"configurable": {"session_id": session_id}}
        )
        
        # Retrieve history and verify that both turns are persisted in history.json
        history = get_file_chat_history(session_id)
        messages = history.messages
        assert len(messages) == 4
        assert messages[0].content == "First question"
        assert messages[1].content == "Answer 1"
        assert messages[2].content == "Second question"
        assert messages[3].content == "Answer 2"
    finally:
        # Cleanup
        clear_session_history(session_id)

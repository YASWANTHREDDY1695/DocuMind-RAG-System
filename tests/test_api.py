from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.routes import app

client = TestClient(app)

@patch("api.routes.list_ingested_documents")
def test_get_documents(mock_list):
    """
    Test GET /api/documents returns the list of unique files mock-indexed.
    """
    mock_list.return_value = ["test1.pdf", "test2.pdf"]
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert response.json() == ["test1.pdf", "test2.pdf"]
    mock_list.assert_called_once()

@patch("api.routes.delete_document")
def test_delete_document_endpoint(mock_delete):
    """
    Test DELETE /api/documents/{filename} calls the delete core logic.
    """
    response = client.delete("/api/documents/test_doc.pdf")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Document 'test_doc.pdf' has been deleted from the index and S3 storage."
    }
    mock_delete.assert_called_once_with("test_doc.pdf")

@patch("api.routes.get_conversational_rag_chain")
def test_query_endpoint(mock_get_chain):
    """
    Test POST /api/query executes the query chain and formats responses correctly.
    """
    # Setup mock chain
    mock_chain = MagicMock()
    
    # Create a mock document representing context sources
    mock_doc = MagicMock()
    mock_doc.metadata = {
        "source": "attention.pdf",
        "page": 2,
        "chunk_id": "attention.pdf_p2_c5"
    }
    mock_doc.page_content = "This is a sample chunk content."
    
    mock_chain.invoke.return_value = {
        "answer": "Deep learning uses attention.",
        "context": [mock_doc]
    }
    mock_get_chain.return_value = mock_chain
    
    # Run request
    payload = {
        "question": "What is attention?",
        "session_id": "api_test_session"
    }
    response = client.post("/api/query", json=payload)
    
    # Assertions
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["answer"] == "Deep learning uses attention."
    assert len(res_data["sources"]) == 1
    assert res_data["sources"][0]["filename"] == "attention.pdf"
    assert res_data["sources"][0]["page"] == 2
    assert res_data["sources"][0]["chunk_id"] == "attention.pdf_p2_c5"
    assert res_data["sources"][0]["content"] == "This is a sample chunk content."
    
    mock_get_chain.assert_called_once_with("api_test_session")
    mock_chain.invoke.assert_called_once_with(
        {"input": "What is attention?"},
        config={"configurable": {"session_id": "api_test_session"}}
    )

@patch("api.routes.get_file_chat_history")
def test_get_session_history_endpoint(mock_get_history):
    """
    Test GET /api/sessions/{session_id} returns formatted chat messages.
    """
    # Mock message history
    mock_history = MagicMock()
    msg1 = MagicMock()
    msg1.type = "human"
    msg1.content = "Hello"
    msg2 = MagicMock()
    msg2.type = "ai"
    msg2.content = "Hi there"
    mock_history.messages = [msg1, msg2]
    mock_get_history.return_value = mock_history
    
    response = client.get("/api/sessions/test_api_session")
    assert response.status_code == 200
    assert response.json() == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    mock_get_history.assert_called_once_with("test_api_session")

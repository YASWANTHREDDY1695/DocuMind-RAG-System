import os
from unittest.mock import patch
from core.ingest import ingest_pdf

@patch('core.ingest.HuggingFaceEmbeddings')
@patch('core.ingest.Chroma')
def test_chunk_count(mock_chroma, mock_embeddings):
    # Setup test file path (assumes download was run)
    test_pdf = os.path.join("data", "attention.pdf")
    assert os.path.exists(test_pdf), "Please run download_sample.py first"
    
    # Run ingestion
    chunks = ingest_pdf(test_pdf)
    
    # Assert we got chunks back
    assert len(chunks) > 0

@patch('core.ingest.HuggingFaceEmbeddings')
@patch('core.ingest.Chroma')
def test_metadata_present(mock_chroma, mock_embeddings):
    test_pdf = os.path.join("data", "attention.pdf")
    assert os.path.exists(test_pdf), "Please run download_sample.py first"
    
    chunks = ingest_pdf(test_pdf)
    
    # Assert metadata fields are populated correctly for citation highlighting
    for chunk in chunks:
        assert "source" in chunk.metadata
        assert "page" in chunk.metadata
        assert "chunk_id" in chunk.metadata
        assert chunk.metadata["source"] == "attention.pdf"
        assert isinstance(chunk.metadata["page"], int)
        assert chunk.metadata["chunk_id"].startswith("attention.pdf_")

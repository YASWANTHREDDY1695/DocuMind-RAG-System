import sys
# Override sqlite3 on Linux to support ChromaDB requirement of SQLite >= 3.35.0
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

from core.ingest import ingest_pdf, delete_document
from core.retriever import list_ingested_documents
from core.query import get_conversational_rag_chain
from core.memory import get_file_chat_history, clear_session_history
from core.s3 import upload_file_to_s3, delete_file_from_s3

# Initialize FastAPI App
app = FastAPI(
    title="DocuMind API",
    description="Stateless Backend API for the RAG-based Document Intelligence System",
    version="1.0.0"
)

# ----------------- PYDANTIC SCHEMAS -----------------

class QueryRequest(BaseModel):
    question: str
    session_id: str

class SourceMetadata(BaseModel):
    filename: str
    page: int
    chunk_id: str
    content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceMetadata]

class StatusResponse(BaseModel):
    status: str
    message: str

# ----------------- API ENDPOINTS -----------------

@app.get("/api/documents", response_model=List[str])
async def get_documents():
    """
    Returns a list of all unique source filenames currently indexed in the system.
    """
    try:
        docs = list_ingested_documents()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.post("/api/ingest", response_model=StatusResponse)
async def upload_and_ingest(file: UploadFile = File(...)):
    """
    Uploads a PDF file and runs the ingestion pipeline to parse, chunk,
    embed, and index it into Chroma DB.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Create a temporary file to store the upload content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Run ingestion using core module
        # Note: We pass the original filename in metadata by saving temporary file
        # with a name, but we want the metadata source to be the uploaded filename.
        # Let's adjust ingest_pdf to allow specifying the logical filename, or we rename the file.
        logical_name = file.filename
        dest_path = os.path.join(tempfile.gettempdir(), logical_name)
        
        # Rename/move file to have its original name during ingestion
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(tmp_file_path, dest_path)
        
        ingest_pdf(dest_path)
        
        # Upload file to S3 (or copy to local data/ directory if credentials missing)
        upload_file_to_s3(dest_path, logical_name)
        
        # Clean up
        if os.path.exists(dest_path):
            os.remove(dest_path)
            
        return StatusResponse(
            status="success",
            message=f"Document '{logical_name}' has been successfully ingested and indexed."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

@app.post("/api/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Queries the RAG conversational chain. Reformulates the question based on session history,
    retrieves context from Chroma DB, and generates the final answer.
    """
    try:
        # Load modern conversational chain for the given session_id
        chain = get_conversational_rag_chain(request.session_id)
        
        # Invoke the chain
        response = chain.invoke(
            {"input": request.question},
            config={"configurable": {"session_id": request.session_id}}
        )
        
        answer = response.get("answer", "")
        context_docs = response.get("context", [])
        
        # Extract metadata from retrieved source documents
        sources = []
        seen_chunks = set()
        for doc in context_docs:
            meta = doc.metadata
            chunk_id = meta.get("chunk_id")
            if chunk_id and chunk_id not in seen_chunks:
                seen_chunks.add(chunk_id)
                sources.append(SourceMetadata(
                    filename=meta.get("source", "Unknown"),
                    page=meta.get("page", 0),
                    chunk_id=chunk_id,
                    content=doc.page_content
                ))
                
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}. Make sure your database is not empty and GROQ_API_KEY is set."
        )

@app.delete("/api/documents/{filename}", response_model=StatusResponse)
async def remove_document(filename: str):
    """
    Deletes all vector chunks matching the source filename from Chroma DB.
    """
    try:
        delete_document(filename)
        delete_file_from_s3(filename)
        return StatusResponse(
            status="success",
            message=f"Document '{filename}' has been deleted from the index and S3 storage."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.delete("/api/sessions/{session_id}", response_model=StatusResponse)
async def clear_session(session_id: str):
    """
    Clears the chat history JSON file associated with the session_id.
    """
    try:
        clear_session_history(session_id)
        return StatusResponse(
            status="success",
            message=f"Chat history for session '{session_id}' has been cleared."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear session: {str(e)}")

@app.get("/api/sessions/{session_id}", response_model=List[Dict[str, str]])
async def get_session_history(session_id: str):
    """
    Returns all messages for the given session_id.
    """
    try:
        history = get_file_chat_history(session_id)
        messages = []
        for msg in history.messages:
            messages.append({
                "role": "user" if msg.type == "human" else "assistant",
                "content": msg.content
            })
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

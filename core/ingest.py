import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.retriever import get_embeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import config

def ingest_pdf(file_path: str) -> List[Document]:
    """
    Loads a PDF file, splits it into chunks, injects metadata,
    and indexes/persists it in a local Chroma vector database.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")

    print(f"Loading PDF from {file_path}...")
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    print(f"Splitting {len(documents)} pages into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)
    
    # Enrich metadata for each chunk with source, page and unique chunk_id
    filename = os.path.basename(file_path)
    print(f"Enriching metadata for {len(chunks)} chunks...")
    for i, chunk in enumerate(chunks):
        page = chunk.metadata.get("page", 0)
        chunk.metadata["source"] = filename
        chunk.metadata["page"] = page
        chunk.metadata["chunk_id"] = f"{filename}_p{page}_c{i}"
        
    print(f"Initializing embedding model: {config.EMBEDDING_MODEL_NAME}...")
    embeddings = get_embeddings()
    
    print(f"Indexing chunks in Chroma DB at {config.CHROMA_DB_PATH}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=config.CHROMA_DB_PATH
    )
    
    print("Ingestion and persistence completed successfully!")
    return chunks

def delete_document(filename: str):
    """
    Deletes all chunks corresponding to the given filename from the Chroma vector store.
    """
    print(f"Loading Chroma DB to delete document: {filename}...")
    from core.retriever import get_vector_store
    try:
        vector_store = get_vector_store()
        # Delete items matching source == filename
        vector_store.delete(where={"source": filename})
        print(f"Successfully deleted document '{filename}' from Chroma vector store.")
    except FileNotFoundError:
        print("Chroma DB not found, nothing to delete.")

if __name__ == "__main__":
    # Test ingestion locally
    test_file = os.path.join(config.DATA_DIR, "attention.pdf")
    if os.path.exists(test_file):
        ingest_pdf(test_file)
    else:
        print(f"Test file not found at {test_file}. Please run download script first.")

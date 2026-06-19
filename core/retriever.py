import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import config

_embeddings = None

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)
    return _embeddings

def get_vector_store() -> Chroma:
    """
    Loads and returns the persisted Chroma vector store.
    Raises FileNotFoundError if the database directory does not exist or is empty.
    """
    # Check if directory exists and has files (ChromaDB creates multiple files/dirs)
    if not os.path.exists(config.CHROMA_DB_PATH) or not os.listdir(config.CHROMA_DB_PATH):
        raise FileNotFoundError(
            f"Chroma DB directory at '{config.CHROMA_DB_PATH}' is empty or does not exist. "
            "Please run ingestion first."
        )
        
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory=config.CHROMA_DB_PATH,
        embedding_function=embeddings
    )
    return vector_store

def get_retriever(k: int = 4):
    """
    Returns a retriever interface from the Chroma vector store.
    """
    vector_store = get_vector_store()
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )

def list_ingested_documents() -> list:
    """
    Queries Chroma DB and returns a list of unique source filenames indexed.
    """
    try:
        vector_store = get_vector_store()
        # Retrieve all metadatas in the collection
        results = vector_store.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        sources = set()
        for meta in metadatas:
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(list(sources))
    except FileNotFoundError:
        # If DB doesn't exist yet, return empty list
        return []

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_groq import ChatGroq
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from core.retriever import get_retriever
from core.memory import get_file_chat_history
import config

def get_conversational_rag_chain(session_id: str):
    """
    Assembles and returns a modern conversational RAG chain
    wrapped with persistent file-based chat history.
    """
    # 1. Initialize the LLM (Groq)
    llm = ChatGroq(
        groq_api_key=config.GROQ_API_KEY,
        model_name=config.LLM_MODEL_NAME,
        temperature=0.2
    )
    
    # 2. Setup the Retriever
    retriever = get_retriever()
    
    # 3. Create History-Aware Retriever
    # This reformulates the user's question to be standalone in the context of history
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )
    
    # 4. Create QA / Document Chain
    # This answers the formulated question using retrieved documents
    system_prompt = (
        "You are a helpful assistant for question-answering tasks. "
        "Use the following pieces of retrieved context to answer the question. "
        "If you don't know the answer, say that you don't know. "
        "Include details from the context, but keep it clear and structured. "
        "CRITICAL: For every sentence or factual claim in your response that relies on "
        "retrieved context, you MUST append an inline citation in the exact format "
        "[Source: filename, Page: X] at the end of that sentence. X must be the "
        "0-indexed page number of the context document plus 1 (e.g. Page 1 for page 0).\n\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # 5. Combine into Retrieval Chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # 6. Wrap with Chat Message History
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_file_chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer"
    )
    
    return conversational_rag_chain

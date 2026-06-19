import os
from langchain_community.chat_message_histories import FileChatMessageHistory
import config

def get_file_chat_history(session_id: str) -> FileChatMessageHistory:
    """
    Returns a FileChatMessageHistory instance associated with the session_id.
    Persists history to a JSON file under config.HISTORY_DIR.
    """
    # Sanitize session_id to prevent directory traversal and ensure it's a valid filename
    safe_session_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")).strip()
    if not safe_session_id:
        safe_session_id = "default_session"
        
    file_path = os.path.join(config.HISTORY_DIR, f"{safe_session_id}.json")
    return FileChatMessageHistory(file_path=file_path)

def clear_session_history(session_id: str):
    """
    Deletes the persistent chat history file for the given session.
    """
    safe_session_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")).strip()
    file_path = os.path.join(config.HISTORY_DIR, f"{safe_session_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as e:
            print(f"Error deleting history file: {e}")

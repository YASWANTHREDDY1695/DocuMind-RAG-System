import os
import streamlit as st
import requests
import uuid

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api"
try:
    if "API_BASE_URL" in st.secrets:
        API_BASE_URL = st.secrets["API_BASE_URL"]
    elif "api_base_url" in st.secrets:
        API_BASE_URL = st.secrets["api_base_url"]
    else:
        API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")
except Exception:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api")

print(f"DEBUG: Connecting to Backend API at: {API_BASE_URL}")

import re

def highlight_citations(text: str) -> str:
    """
    Parses LLM responses and highlights inline citations in a premium colored badge.
    Converts [Source: filename.pdf, Page: X] to :blue[**[📄 filename.pdf (P. X)]**]
    """
    pattern = r'\[Source:\s*([^,\]]+),\s*Page:\s*(\d+)\]'
    def repl(match):
        filename = match.group(1)
        page = match.group(2)
        return f" :blue[**[📄 {filename} (P. {page})]**]"
    return re.sub(pattern, repl, text)

# Set page configuration with custom title and layout
st.set_page_config(
    page_title="DocuMind RAG System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS for premium dark-mode / glassmorphism aesthetic
st.markdown("""
    <style>
    /* Main Background and Fonts */
    .stApp {
        background-color: #0d0f12;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #151922 !important;
        border-right: 1px solid #2d3748;
    }
    
    /* Header/Title styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .sub-header {
        font-size: 1.1rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card containers */
    .status-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.3rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
    }
    
    /* Trash button styling */
    .trash-btn>button {
        background: transparent !important;
        color: #ef4444 !important;
        border: 1px solid #ef4444 !important;
        padding: 0.2rem 0.5rem !important;
    }
    .trash-btn>button:hover {
        background: #ef4444 !important;
        color: white !important;
        box-shadow: none !important;
    }
    
    /* Chat bubbles styling */
    div[data-testid="chatAvatarIcon-user"] {
        background-color: #4f46e5 !important;
    }
    div[data-testid="chatAvatarIcon-assistant"] {
        background-color: #8b5cf6 !important;
    }
    
    /* Source box styling */
    .source-tag {
        display: inline-block;
        background-color: #1e293b;
        color: #3b82f6;
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 0.2rem 0.6rem;
        margin: 0.2rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- BACKEND CONNECTIVITY CHECK -----------------
def check_backend_running():
    try:
        response = requests.get(f"{API_BASE_URL}/documents", timeout=15)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"DEBUG CONNECTION ERROR: {e}")
        return False

backend_online = check_backend_running()

if not backend_online:
    st.markdown("<h1 class='main-header'>🧠 DocuMind</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>System Offline</p>", unsafe_allow_html=True)
    st.markdown("""
        <div class='status-card' style='border: 1px solid #ef4444; background: rgba(239, 68, 68, 0.05);'>
            <h3 style='color: #ef4444;'>❌ Backend API Server is Offline</h3>
            <p>The Streamlit frontend cannot communicate with the RAG pipeline because the FastAPI backend is not running.</p>
            <p><b>Please run the following command in a separate terminal:</b></p>
            <pre style='background: #1e1e1e; padding: 10px; border-radius: 6px;'>python main.py</pre>
            <p>Once started, refresh this page to connect.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# ----------------- SESSION STATE INIT -----------------

# Generate session_id to maintain persistent conversation history
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{uuid.uuid4().hex[:8]}"

# Fetch files list from backend
try:
    ingested_files = requests.get(f"{API_BASE_URL}/documents").json()
except Exception:
    ingested_files = []

db_exists = len(ingested_files) > 0

# ----------------- SIDEBAR -----------------

with st.sidebar:
    st.markdown("### 🛠️ Control Panel")
    
    st.markdown("#### 1. Ingest Documents")
    uploaded_file = st.file_uploader("Upload a PDF document", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Index Document"):
            with st.spinner("Uploading & processing PDF on the backend..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    res = requests.post(f"{API_BASE_URL}/ingest", files=files)
                    if res.status_code == 200:
                        st.success("Successfully ingested!")
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.json().get('detail')}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")
                    
    st.markdown("---")
    st.markdown("#### 2. Managed Documents")
    
    if db_exists:
        for idx, doc_name in enumerate(ingested_files):
            col1, col2 = st.columns([5, 1])
            col1.markdown(f"📄 `{doc_name}`", help=doc_name)
            # Create a delete button for each document
            if col2.button("🗑️", key=f"del_{idx}"):
                with st.spinner("Deleting..."):
                    try:
                        res = requests.delete(f"{API_BASE_URL}/documents/{doc_name}")
                        if res.status_code == 200:
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Delete failed")
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("No documents uploaded yet.")
        
    st.markdown("---")
    st.markdown("#### 3. System Status")
    st.success("Vector Store: Connected (FastAPI)")
    st.info(f"Session ID: `{st.session_state.session_id}`")
    
    # Reset Conversation Button
    if st.button("🧹 Clear Chat History"):
        try:
            res = requests.delete(f"{API_BASE_URL}/sessions/{st.session_state.session_id}")
            if res.status_code == 200:
                st.success("Chat history cleared!")
                st.rerun()
        except Exception as e:
            st.error(f"Failed to clear history: {e}")

# ----------------- MAIN UI -----------------

st.markdown("<h1 class='main-header'>🧠 DocuMind</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Enterprise-Grade RAG-Based Document Intelligence System</p>", unsafe_allow_html=True)

# Guide instructions if DB is empty
if not db_exists:
    st.markdown("""
        <div class='status-card'>
            <h3>Welcome to DocuMind!</h3>
            <p>To get started, upload a PDF document in the sidebar and click <b>Index Document</b>.</p>
            <p>For testing, we have pre-downloaded the <i>"Attention Is All You Need"</i> research paper in the <code>data/</code> folder. 
            Feel free to locate it and index it!</p>
        </div>
    """, unsafe_allow_html=True)
else:
    # ----------------- CHAT INTERFACE -----------------
    
    # Load and display chat messages directly from persistent backend history
    try:
        messages = requests.get(f"{API_BASE_URL}/sessions/{st.session_state.session_id}").json()
    except Exception:
        messages = []
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(highlight_citations(message["content"]))
            
    # Handle user query input
    if prompt := st.chat_input("Ask a question about the document..."):
        # Display user message in UI
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Run query through backend RAG pipeline
        with st.chat_message("assistant"):
            with st.spinner("Analyzing document contents..."):
                try:
                    payload = {
                        "question": prompt,
                        "session_id": st.session_state.session_id
                    }
                    res = requests.post(f"{API_BASE_URL}/query", json=payload)
                    
                    if res.status_code == 200:
                        data = res.json()
                        answer = data["answer"]
                        sources = data["sources"]
                        
                        # Render answer with inline citations highlighted
                        st.markdown(highlight_citations(answer))
                        
                        # Render citation sources if available
                        if sources:
                            st.markdown("---")
                            with st.expander("🔍 View Retrieved Source Snippets (Citation Highlight)"):
                                for idx, src in enumerate(sources):
                                    st.markdown(f"**📍 Chunk {idx+1}: {src['filename']} — Page {src['page'] + 1}**")
                                    st.info(src['content'])
                    else:
                        st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Error querying backend pipeline: {e}")
                    st.info("Make sure your Uvicorn backend is running and GROQ_API_KEY is correctly set.")

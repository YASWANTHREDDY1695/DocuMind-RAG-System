import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "chroma_db")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama-3.1-8b-instant")

# AWS Credentials and S3 configurations
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME", "")

# absolute path to database directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(BASE_DIR, CHROMA_DB_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_DIR = os.path.join(BASE_DIR, "chat_history")

# Create required folders
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

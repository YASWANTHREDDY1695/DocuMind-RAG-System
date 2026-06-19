import sys
# Override sqlite3 on Linux to support ChromaDB requirement of SQLite >= 3.35.0
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import uvicorn
import os

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting DocuMind FastAPI Backend server...")
    uvicorn.run("api.routes:app", host="127.0.0.1", port=8000, reload=False)

import uvicorn
import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting DocuMind FastAPI Backend server...")
    uvicorn.run("api.routes:app", host="127.0.0.1", port=8000, reload=False)

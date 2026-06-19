import requests
API_BASE_URL = "http://127.0.0.1:8000/api"
try:
    print("Attempting to connect to:", f"{API_BASE_URL}/documents")
    r = requests.get(f"{API_BASE_URL}/documents", timeout=5)
    print("STATUS:", r.status_code)
    print("JSON:", r.json())
except Exception as e:
    print("ERROR:", e)

import os
import requests
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def download_sample_pdf():
    pdf_url = "https://arxiv.org/pdf/1706.03762"
    target_path = os.path.join(config.DATA_DIR, "attention.pdf")
    
    if os.path.exists(target_path):
        print(f"Sample PDF already exists at {target_path}")
        return
        
    print(f"Downloading sample PDF from {pdf_url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    response = requests.get(pdf_url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded sample PDF to {target_path}")
    else:
        print(f"Failed to download PDF. Status code: {response.status_code}")
        # Write a fallback simple text-based pdf if the download failed, but let's assume it succeeds.
        sys.exit(1)

if __name__ == "__main__":
    download_sample_pdf()

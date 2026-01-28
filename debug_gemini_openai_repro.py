import requests
import os
from dotenv import load_dotenv

load_dotenv()

def repro_openai():
    api_key = os.getenv("GEMINI_API_KEY")
    # HARDCODED WORKING URL from Step 745
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try both variations that were in Step 745
    models = ["gemini-1.5-flash", "models/gemini-1.5-flash"]
    
    for m in models:
        print(f"\n--- Testing {m} ---")
        payload = {
            "model": m,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS")
                print(response.text[:100])
                return # Stop on success to know which one worked
            else:
                print(f"Error: {response.text[:100]}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    repro_openai()

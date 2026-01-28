import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_native():
    api_key = os.getenv("GEMINI_API_KEY")
    # Base URL from .env is https://generativelanguage.googleapis.com/v1beta
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    models_to_test = ["gemini-1.5-flash", "models/gemini-1.5-flash"]
    
    print(f"Key: {api_key[:5]}...")

    for model in models_to_test:
        print(f"\n--- Testing Model: {model} ---")
        # Ensure we don't double models/ prefix if already there
        if "models/" in model:
            # URL structure: .../v1beta/models/gemini-1.5-flash:generateContent
            # The model variable has models/ prefix already? 
            # If model is "models/gemini...", then `v1beta/{model}` -> `v1beta/models/gemini...`
             url = f"{base_url}/{model}:generateContent?key={api_key}"
        else:
             # Add models/ prefix manually
             url = f"{base_url}/models/{model}:generateContent?key={api_key}"
             
        print(f"URL: {url.replace(api_key, 'API_KEY')}")
        
        payload = {
            "contents": [{
                "parts": [{"text": "Hello, say test."}]
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS")
                print(f"Response: {response.text[:100]}")
            else:
                print(f"Error: {response.text[:200]}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    debug_native()

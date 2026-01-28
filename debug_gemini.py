import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    # Base URL from .env is currently native base
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai" # Revert to compat base for listing models on compat layer
    # OR use native listing: .../v1beta/models?key=...

    # Let's test BOTH endpoints for listing models
    
    print("\n--- 1. Listing Models (OpenAI Compat) ---")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/openai/models"
        response = requests.get(url, headers=headers)
        print(f"URL: {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json().get('data', [])
            print(f"Found {len(models)} models:")
            for m in models:
                mid = m.get('id')
                if "gemini" in mid:
                    print(f" - {mid}")
        else:
             print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- 2. Listing Models (Native) ---")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url)
        print(f"URL: {url.replace(api_key, 'API_KEY')}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"Found {len(models)} models:")
            for m in models:
                mid = m.get('name') # Native API returns 'name': 'models/gemini-pro'
                if "gemini" in mid:
                    print(f" - {mid}")
        else:
             print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_gemini()

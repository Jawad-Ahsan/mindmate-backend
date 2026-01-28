import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

def repro():
    api_key = os.getenv("GEMINI_API_KEY")
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    models = ["gemini-1.5-flash", "gemini-pro"]
    
    for m in models:
        print(f"\n--- Testing {m} ---")
        url = f"{base_url}/models/{m}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("SUCCESS")
                print(response.text[:100])
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    repro()

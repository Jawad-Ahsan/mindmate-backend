import os
import sys
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

import requests

def test_groq_connection():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment variables.")
        return

    print(f"Testing Groq API Key: {api_key[:10]}...")
    
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("✅ Groq API Authentication Successful!")
            print(f"Available Models: {len(response.json()['data'])}")
        elif response.status_code == 401:
            print("❌ Groq API Failed: 401 Unauthorized - The API key is invalid or expired.")
        else:
            print(f"❌ Groq API Failed: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")

if __name__ == "__main__":
    test_groq_connection()

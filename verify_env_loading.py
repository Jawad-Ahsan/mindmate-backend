import os
import sys
from dotenv import load_dotenv

load_dotenv()

def verify():
    key = os.getenv("GEMINI_API_KEY")
    url = os.getenv("GEMINI_BASE_URL")
    model = os.getenv("GEMINI_MODEL")
    
    print(f"Key loaded: '{key[:5]}...{key[-5:] if key else ''}' Length: {len(key) if key else 0}")
    print(f"URL loaded: '{url}'")
    print(f"Model loaded: '{model}'")
    
    if key and " " in key:
        print("WARNING: Spaces found in Main Key!")
        
    groq = os.getenv("GROQ_API_KEY")
    print(f"Groq loaded: '{groq[:5]}...'")

if __name__ == "__main__":
    verify()

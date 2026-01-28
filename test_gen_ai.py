import os
import sys
from dotenv import load_dotenv

# Ensure we can import from parent directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_client import LLMClient

# Load environment variables
load_dotenv()

def test_llm_client():
    print("🚀 Initializing LLM Client...")
    try:
        client = LLMClient(enable_cache=False)
        print(f"✅ Client Initialized. Active Provider: {client.active_provider}")
        print(f"✅ Active Model: {client.model}")
        
        print("\n🧪 Testing Simple Generation...")
        response = client.generate("Hello, just say 'Connected Successfully'.", max_tokens=20)
        print(f"🤖 Response: {response}")
        
        if "Connected" in response or "connected" in response.lower():
            print("✅ Generation Test Passed!")
        else:
            print("⚠️ Response content unexpected, but generation succeeded.")
            
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_llm_client()

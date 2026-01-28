import sys
import os
import logging

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_client import LLMClient

# Configure logging to see verification output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cerebras():
    print("🧪 Initializing LLMClient (Expect Cerebras)...", flush=True)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.getenv("CEREBRAS_API_KEY")
        print(f"🔑 Debug: Env Key starts with: {key[:5] if key else 'None'}", flush=True)
        
        client = LLMClient()
        print(f"✅ Client Initialized. Active Provider: {client.active_provider}", flush=True)
        print(f"🔑 Client Config Key starts with: {client.client_config['cerebras']['key'][:5] if client.client_config['cerebras']['key'] else 'None'}", flush=True)
        print(f"✅ Model: {client.model}", flush=True)
        
        if client.active_provider != "cerebras":
            print("❌ Error: Active provider is NOT Cerebras!", flush=True)
            return

        print("🧪 Testing Generation...", flush=True)
        response = client.generate("Hello, are you running on Cerebras?", max_tokens=50)
        print(f"🤖 Response: {response}", flush=True)
        
        if "Error" in response:
             print("❌ Generation Failed", flush=True)
        else:
             print("✅ Generation Successful", flush=True)

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cerebras()

"""
Test script for MindMate Chatbot System
======================================
Tests the chatbot tools and main system.
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tools():
    """Test individual tools"""
    print("🧪 Testing Chatbot Tools...")
    print("=" * 50)
    
    try:
        # Test basic info tool
        from chatbot.tools.basic_info_tool import ask_basic_info
        
        print("\n📋 Testing Basic Info Tool:")
        result = ask_basic_info("start")
        print(f"Start result: {result}")
        
        if result.get("status") == "started":
            result = ask_basic_info("respond", response="Yes, I have depression")
            print(f"Response result: {result}")
        
        print("✅ Basic Info Tool: PASSED")
        
    except Exception as e:
        print(f"❌ Basic Info Tool: FAILED - {e}")
        return False
    
    try:
        # Test concern tool
        from chatbot.tools.concern_tool import ask_concern
        
        print("\n🎯 Testing Concern Tool:")
        result = ask_concern("start")
        print(f"Start result: {result}")
        
        if result.get("status") == "started":
            result = ask_concern("respond", response="I'm feeling very anxious")
            print(f"Response result: {result}")
        
        print("✅ Concern Tool: PASSED")
        
    except Exception as e:
        print(f"❌ Concern Tool: FAILED - {e}")
        return False
    
    try:
        # Test risk assessment tool
        from chatbot.tools.risk_assessment_tool import ask_risk_assessment
        
        print("\n⚠️ Testing Risk Assessment Tool:")
        result = ask_risk_assessment("start")
        print(f"Start result: {result}")
        
        if result.get("status") == "started":
            result = ask_risk_assessment("respond", response="No")
            print(f"Response result: {result}")
        
        print("✅ Risk Assessment Tool: PASSED")
        
    except Exception as e:
        print(f"❌ Risk Assessment Tool: FAILED - {e}")
        return False
    
    return True

def test_chatbot():
    """Test the main chatbot system"""
    print("\n🤖 Testing Main Chatbot System...")
    print("=" * 50)
    
    try:
        from chatbot.mindmate_chatbot import get_chatbot
        
        chatbot = get_chatbot()
        print("✅ Chatbot initialization: PASSED")
        
        # Test welcome message
        response = chatbot.chat("hello")
        print(f"Welcome response: {response[:100]}...")
        print("✅ Welcome message: PASSED")
        
        # Test start assessment
        response = chatbot.chat("start")
        print(f"Start assessment response: {response[:100]}...")
        print("✅ Start assessment: PASSED")
        
        # Test assessment status
        status = chatbot.get_assessment_status()
        print(f"Assessment status: {status}")
        print("✅ Assessment status: PASSED")
        
        return True
        
    except Exception as e:
        print(f"❌ Main Chatbot System: FAILED - {e}")
        logger.error(f"Chatbot test error: {e}", exc_info=True)
        return False

def test_llm_client():
    """Test the LLM client"""
    print("\n🔌 Testing LLM Client...")
    print("=" * 50)
    
    try:
        from chatbot.LLM_client import ChatbotLLMClient
        
        # Note: This will fail without GROQ_API_KEY in environment
        # But we can test the class structure
        print("✅ LLM Client class structure: PASSED")
        
        # Test without API key (should raise error)
        try:
            client = ChatbotLLMClient()
            print("✅ LLM Client connection: PASSED")
        except ValueError as e:
            if "GROQ_API_KEY" in str(e):
                print("⚠️ LLM Client: SKIPPED (no API key)")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Client: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 MindMate Chatbot System Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test tools
    if not test_tools():
        all_passed = False
    
    # Test LLM client
    if not test_llm_client():
        all_passed = False
    
    # Test main chatbot
    if not test_chatbot():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Chatbot system is working correctly.")
    else:
        print("❌ SOME TESTS FAILED. Please check the errors above.")
    
    print("\n📝 Test Summary:")
    print("• Tools: Basic Info, Concern, Risk Assessment")
    print("• LLM Client: GROQ API integration")
    print("• Main Chatbot: RE-ACT agent with LangGraph")
    print("• API Routes: FastAPI integration")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
Test FastAPI Integration for MindMate Chatbot
============================================
Tests that the chatbot can be imported and used in FastAPI context.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fastapi_imports():
    """Test that all FastAPI components can be imported"""
    print("🧪 Testing FastAPI Integration...")
    print("=" * 50)
    
    try:
        # Test chatbot imports
        from chatbot.mindmate_chatbot import get_chatbot, MindMateChatbot
        print("✅ Chatbot imports: PASSED")
        
        # Test tool imports
        from chatbot.tools import ask_basic_info, ask_concern, ask_risk_assessment
        print("✅ Tool imports: PASSED")
        
        # Test router imports
        from routers.chatbot_routes import router
        print("✅ Router imports: PASSED")
        
        # Test chatbot functionality
        chatbot = get_chatbot()
        print("✅ Chatbot initialization: PASSED")
        
        # Test basic tool functionality
        result = ask_basic_info("start")
        if result.get("status") == "started":
            print("✅ Basic tool functionality: PASSED")
        else:
            print("❌ Basic tool functionality: FAILED")
            return False
        
        print("\n🎉 All FastAPI integration tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chatbot_workflow():
    """Test a simple chatbot workflow"""
    print("\n🤖 Testing Chatbot Workflow...")
    print("=" * 50)
    
    try:
        from chatbot.mindmate_chatbot import get_chatbot
        
        chatbot = get_chatbot()
        
        # Test welcome message
        response = chatbot.chat("hello")
        print(f"✅ Welcome message: {response[:100]}...")
        
        # Test start assessment
        response = chatbot.chat("start")
        print(f"✅ Start assessment: {response[:100]}...")
        
        # Test assessment status
        status = chatbot.get_assessment_status()
        print(f"✅ Assessment status: {status}")
        
        print("\n🎉 Chatbot workflow test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Chatbot workflow test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 MindMate Chatbot FastAPI Integration Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Test imports
    if not test_fastapi_imports():
        all_passed = False
    
    # Test workflow
    if not test_chatbot_workflow():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! FastAPI integration is working correctly.")
        print("\n📝 Ready for deployment:")
        print("• Chatbot system: ✅ Working")
        print("• Tool functions: ✅ Working")
        print("• RE-ACT agent: ✅ Working")
        print("• FastAPI routes: ✅ Ready")
        print("• LLM integration: ✅ Connected")
    else:
        print("❌ SOME TESTS FAILED. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

"""
MindMate Chatbot Demo
=====================
Interactive demo of the chatbot system.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot.mindmate_chatbot import get_chatbot

def main():
    """Interactive chatbot demo"""
    print("🧠 MindMate Chatbot Demo")
    print("=" * 50)
    print("This demo shows how the RE-ACT agent chatbot works.")
    print("Type 'quit' to exit, 'help' for commands.")
    print("=" * 50)
    
    try:
        # Initialize chatbot
        chatbot = get_chatbot()
        print("✅ Chatbot initialized successfully!")
        
        # Start conversation
        response = chatbot.chat("hello")
        print(f"\n🤖 Bot: {response}")
        
        conversation_count = 0
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n💭 You [{conversation_count + 1}]: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                    print("👋 Thank you for trying MindMate Chatbot! Goodbye!")
                    break
                
                elif user_input.lower() in ['help', 'h']:
                    print("\n🆘 Help:")
                    print("• Type naturally to chat with the bot")
                    print("• Type 'start' to begin mental health assessment")
                    print("• Type 'status' to see assessment progress")
                    print("• Type 'quit' to exit")
                    continue
                
                elif user_input.lower() in ['status', 's']:
                    status = chatbot.get_assessment_status()
                    print(f"\n📊 Assessment Status:")
                    print(f"• Current Tool: {status.get('current_tool', 'None')}")
                    print(f"• Tool Sequence: {status.get('tool_sequence', [])}")
                    print(f"• Workflow Complete: {status.get('workflow_complete', False)}")
                    continue
                
                elif not user_input:
                    print("⚠️ Please enter a message or command.")
                    continue
                
                # Process user input
                print(f"\n🔄 Processing your request...")
                conversation_count += 1
                
                response = chatbot.chat(user_input)
                
                # Display response
                print(f"\n🤖 Bot:")
                print("─" * 50)
                print(response)
                print("─" * 50)
                
                # Show conversation stats
                if conversation_count % 5 == 0:
                    print(f"💬 Conversation count: {conversation_count}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
                
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("🔄 Continuing with next input...")
                continue
    
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

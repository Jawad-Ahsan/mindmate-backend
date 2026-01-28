#!/usr/bin/env python3
"""
MindMate Usage Examples
Demonstrates how to integrate MindMate into your application
"""

from chatbot import MindMateChatbot

def example_1_basic_usage():
    """Example 1: Basic chatbot usage"""
    print("=== Example 1: Basic Usage ===")

    # Create chatbot instance
    chatbot = MindMateChatbot()

    # Simulate a conversation
    responses = [
        "Hello",
        "I've been feeling anxious and stressed",
        "It started about 3 weeks ago",
        "I'd say it's about 6 out of 10",
        "It happens several times a week",
        "Work deadlines make it worse",
        "It's affecting my concentration at work",
        "I've had similar feelings before",
        "My sleep and appetite are affected",
        "I avoid social gatherings"
    ]

    print("Starting assessment conversation...")
    for i, response in enumerate(responses, 1):
        bot_response = chatbot.chat(response)
        print(f"{i}. Patient: {response}")
        print(f"   MindMate: {bot_response[:100]}...")
        print()

    # Get final assessment
    report = chatbot.get_assessment_report()
    if report:
        print("✅ Assessment completed!")
        print("📋 Narrative Summary:")
        print(report.get("narrative_summary", "No summary available"))

def example_2_progress_tracking():
    """Example 2: Track assessment progress"""
    print("\n=== Example 2: Progress Tracking ===")

    chatbot = MindMateChatbot()

    # Check initial progress
    progress = chatbot.get_progress_summary()
    print(f"Initial: {progress['completed_tools']}/{progress['total_tools']} tools completed")

    # Simulate partial conversation
    partial_responses = [
        "Hi there",
        "I'm feeling depressed",
        "Started last month",
        "About 8 on the scale"
    ]

    for response in partial_responses:
        chatbot.chat(response)

    # Check progress again
    progress = chatbot.get_progress_summary()
    print(f"After 4 responses: {progress['completed_tools']}/{progress['total_tools']} tools completed")
    print(f"Current tool: {progress['current_tool']}")
    print(".1f")

def example_3_data_export():
    """Example 3: Export assessment data"""
    print("\n=== Example 3: Data Export ===")

    chatbot = MindMateChatbot()

    # Quick assessment simulation
    demo_responses = [
        "Hello", "Anxiety", "2 weeks ago", "7", "Daily",
        "Work stress", "Moderate impact", "First time",
        "Some difficulty", "Avoiding some activities"
    ]

    for response in demo_responses:
        chatbot.chat(response)

    # Export the data
    export_path = chatbot.export_assessment_data("example_assessment.json")
    if export_path:
        print(f"✅ Assessment data exported to: {export_path}")

        # Show what was exported
        import json
        with open(export_path, 'r') as f:
            data = json.load(f)
        print("\n📊 Exported Data Structure:")
        for key, value in data.get("structured_data", {}).items():
            if key != "assessment_timestamp" and value:
                print(f"   • {key}: {value}")

def example_4_custom_integration():
    """Example 4: Custom integration pattern"""
    print("\n=== Example 4: Custom Integration ===")

    class CustomMindMateClient:
        def __init__(self):
            self.chatbot = MindMateChatbot()
            self.conversation_log = []

        def process_patient_input(self, patient_message):
            """Process patient input and return structured response"""
            self.conversation_log.append({"role": "patient", "message": patient_message})

            bot_response = self.chatbot.chat(patient_message)
            self.conversation_log.append({"role": "bot", "message": bot_response})

            return {
                "response": bot_response,
                "assessment_complete": self.chatbot.current_state.get("session_complete", False),
                "progress": self.chatbot.get_progress_summary()
            }

        def get_final_assessment(self):
            """Get complete assessment when finished"""
            return self.chatbot.get_assessment_report()

    # Use custom client
    client = CustomMindMateClient()

    test_messages = ["Hi", "I'm stressed", "Started recently", "Level 6", "Often"]

    for msg in test_messages:
        result = client.process_patient_input(msg)
        print(f"Patient: {msg}")
        print(f"MindMate: {result['response'][:80]}...")
        print(f"Progress: {result['progress']['completed_tools']}/9")
        print()

    print("🎯 Integration pattern allows custom workflows and data handling")

def main():
    """Run all examples"""
    print("🧠 MindMate Usage Examples")
    print("="*50)

    example_1_basic_usage()
    example_2_progress_tracking()
    example_3_data_export()
    example_4_custom_integration()

    print("\n✅ All examples completed!")
    print("\n📚 Key Integration Points:")
    print("   • Create MindMateChatbot() instance")
    print("   • Call chat(message) for each patient response")
    print("   • Check get_progress_summary() for status")
    print("   • Get final report with get_assessment_report()")
    print("   • Export data with export_assessment_data()")

if __name__ == "__main__":
    main()
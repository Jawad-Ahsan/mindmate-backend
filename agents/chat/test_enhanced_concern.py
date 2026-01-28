#!/usr/bin/env python3
"""
Test script for Enhanced Concern Assessment
==========================================

This script demonstrates the enhanced concern assessment capabilities
with LLM integration and improved question flow.
"""

import json
from agents.llm_client import LLMClient
from .concern import PresentingConcernChatbot

def test_enhanced_concern_assessment():
    """Test the enhanced concern assessment functionality"""
    print("🧠 Testing Enhanced Concern Assessment")
    print("=" * 60)

    try:
        # Initialize LLM client
        llm_client = LLMClient()
        print("✅ LLM client initialized")

        # Create enhanced chatbot
        chatbot = PresentingConcernChatbot(llm_client=llm_client, max_questions=8)
        print("✅ Enhanced concern chatbot created")

        # Simulate patient responses
        test_responses = [
            "I've been feeling really anxious and worried all the time, especially about work and my health",
            "It started about 3 months ago when I had some family issues",
            "I'd say it's about a 7 out of 10 in terms of how much it's affecting me",
            "It's pretty constant - I feel anxious most days",
            "Stress at work and social situations make it worse",
            "It's affecting my sleep and concentration at work",
            "Yes, it impacts my relationships because I'm always worried",
            "I've had anxiety before but not this intense"
        ]

        print("\n📝 Simulating conversation:")
        print("-" * 40)

        # Start conversation
        response = chatbot.start_conversation()
        print(f"Bot: {response.get('question', 'Hello!')}")

        for i, patient_response in enumerate(test_responses, 1):
            print(f"\n[Turn {i}]")
            print(f"Patient: {patient_response}")

            # Process response
            processed = chatbot.process_response(
                response.get('question_id', 'unknown'),
                free_text=patient_response
            )

            if processed.get('status') == 'complete':
                print(f"Bot: {processed.get('message', 'Assessment complete')}")
                break
            elif processed.get('type') == 'follow_up':
                print(f"Bot (Follow-up): {processed.get('question', 'Can you elaborate?')}")
                # Simulate follow-up response
                followup_response = "It makes me feel overwhelmed and I can't focus"
                processed = chatbot.process_response(
                    processed.get('question_id', 'followup'),
                    free_text=followup_response
                )
                print(f"Patient: {followup_response}")
            elif processed.get('type') == 'clarification':
                print(f"Bot (Clarification): {processed.get('question', 'Can you clarify?')}")
            else:
                print(f"Bot: {processed.get('question', 'Next question...')}")

            response = processed

        print("\n📊 Assessment Results:")
        print("-" * 40)

        # Get goal completion summary
        goal_summary = chatbot._get_goal_completion_summary()
        print(f"Goals completed: {goal_summary['completion_percentage']}%")
        print(f"Completed goals: {goal_summary['completed_goals']}")
        print(f"Missing goals: {goal_summary['missing_goals']}")

        # Generate concern summary
        print("\n📋 Clinical Concern Report:")
        print("-" * 40)
        report = chatbot.create_primary_concern_report()
        print(report)

        # Export data
        print("\n💾 Exported Data (JSON):")
        print("-" * 40)
        export_data = json.loads(chatbot.export_as_json())

        print(f"Presenting concern: {export_data['presenting_concern_data']['presenting_concern']}")
        print(f"Severity: {export_data['presenting_concern_data']['hpi_severity']}")
        print(f"Questions asked: {export_data['conversation_metadata']['total_questions']}")
        print(f"Completion: {export_data['conversation_metadata']['goal_completion']['completion_percentage']}%")

        # Show conversation history
        print("\n📜 Conversation History:")
        print("-" * 40)
        for i, entry in enumerate(export_data['conversation_metadata']['conversation_history'][:5], 1):
            print(f"{i}. {entry['type']}: {entry.get('free_text', entry.get('message', 'N/A'))[:80]}...")

        print("\n✅ Enhanced concern assessment test completed successfully!")

        return {
            'success': True,
            'goal_completion': goal_summary['completion_percentage'],
            'report_length': len(report),
            'questions_asked': export_data['conversation_metadata']['total_questions']
        }

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def test_keyword_extraction():
    """Test the enhanced keyword extraction"""
    print("\n🔍 Testing Enhanced Keyword Extraction")
    print("=" * 60)

    try:
        llm_client = LLMClient()
        chatbot = PresentingConcernChatbot(llm_client=llm_client)

        test_concerns = [
            "I've been having severe headaches that won't go away",
            "My anxiety attacks are happening more frequently",
            "I feel depressed and can't get out of bed",
            "I'm having panic attacks when driving",
            "I can't stop worrying about everything",
            "I have intrusive thoughts about contamination"
        ]

        print("Test concerns and extracted keywords:")
        print("-" * 40)

        for concern in test_concerns:
            # Simulate setting the concern
            chatbot.data.presenting_concern = concern
            keyword = chatbot._extract_concern_keyword()
            print(f"Concern: {concern}")
            print(f"Keyword: {keyword}")
            print()

        print("✅ Keyword extraction test completed!")

    except Exception as e:
        print(f"❌ Keyword extraction test failed: {e}")

def test_response_understanding():
    """Test LLM response understanding"""
    print("\n🧠 Testing LLM Response Understanding")
    print("=" * 60)

    try:
        llm_client = LLMClient()
        chatbot = PresentingConcernChatbot(llm_client=llm_client)

        # Test response understanding
        test_question = "How often do you experience anxiety?"
        test_response = "I feel anxious almost every day, especially in the mornings"

        question_obj = chatbot.questions['frequency_pattern']
        understanding = chatbot._understand_response_with_llm('frequency_pattern', test_response)

        if understanding:
            print(f"Question: {test_question}")
            print(f"Response: {test_response}")
            print(f"Understanding: {json.dumps(understanding, indent=2)}")
        else:
            print("No understanding extracted (LLM may not be available)")

        print("✅ Response understanding test completed!")

    except Exception as e:
        print(f"❌ Response understanding test failed: {e}")

if __name__ == "__main__":
    # Run all tests
    print("🚀 Starting Enhanced Concern Assessment Tests")
    print("=" * 60)

    # Test basic functionality
    result = test_enhanced_concern_assessment()

    # Test keyword extraction
    test_keyword_extraction()

    # Test response understanding
    test_response_understanding()

    print("\n" + "=" * 60)
    if result.get('success', False):
        print(f"🎉 Overall test result: SUCCESS")
        print(f"   Goal completion: {result.get('goal_completion', 0)}%")
        print(f"   Report length: {result.get('report_length', 0)} characters")
        print(f"   Questions asked: {result.get('questions_asked', 0)}")
    else:
        print(f"❌ Overall test result: FAILED - {result.get('error', 'Unknown error')}")

    print("=" * 60)

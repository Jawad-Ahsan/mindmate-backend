#!/usr/bin/env python3
"""
Complete Assessment Workflow Test
=================================

This script demonstrates the complete mental health assessment workflow:
1. Patient profile collection
2. Enhanced concern assessment
3. Module selection
4. SCID deployment (simplified)
5. DA analysis (simplified)
6. Treatment plan generation
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assessment_workflow import AssessmentWorkflow
from agents.llm_client import LLMClient

def test_complete_workflow():
    """Test the complete assessment workflow"""
    print("🔬 Complete Assessment Workflow Test")
    print("=" * 60)

    try:
        # Initialize workflow
        workflow = AssessmentWorkflow(use_llm=True)
        print("✅ Assessment workflow initialized")

        # Start assessment
        session_id, welcome = workflow.start_assessment("test_patient_001")
        print(f"Session ID: {session_id}")
        print(f"Welcome: {welcome}")
        print()

        # Simulate profile collection
        print("📝 Phase 1: Profile Collection")
        print("-" * 40)

        profile_responses = [
            "I'm 28 years old",
            "female",
            "software developer",
            "San Francisco",
            "yes that's correct"
        ]

        current_response = {"status": "continue"}

        for i, response in enumerate(profile_responses, 1):
            if current_response.get("status") in ["continue", "confirm"]:
                print(f"[{i}] Patient: {response}")
                current_response = workflow.process_message(session_id, response)
                print(f"    Bot: {current_response.get('message', 'No response')}")
                print()

        # Simulate concern assessment
        print("🗣️  Phase 2: Concern Assessment")
        print("-" * 40)

        concern_responses = [
            "I've been feeling really anxious and having panic attacks",
            "It started about 2 months ago after some work stress",
            "I'd rate the severity as 8 out of 10",
            "It happens several times a week",
            "Work deadlines and social situations trigger it",
            "It's affecting my sleep and work performance",
            "Yes, it's impacting my relationships because I'm always worried",
            "I've had mild anxiety before but nothing this severe"
        ]

        for i, response in enumerate(concern_responses, 1):
            if current_response.get("status") == "continue":
                print(f"[{i}] Patient: {response}")
                current_response = workflow.process_message(session_id, response)
                print(f"    Bot: {current_response.get('message', 'No response')[:100]}...")
                print()

                # Break if assessment is complete
                if current_response.get("status") == "stage_complete":
                    print("    Concern assessment completed!")
                    break

        # Simulate module selection
        print("🎯 Phase 3: Module Selection")
        print("-" * 40)

        module_response = "yes"
        print(f"Patient: {module_response}")
        current_response = workflow.process_message(session_id, module_response)
        print(f"Bot: {current_response.get('message', 'No response')}")
        print()

        # Simulate SCID deployment
        print("📋 Phase 4: SCID Assessment (Simplified)")
        print("-" * 40)

        if current_response.get("stage") == "scid_deployment":
            print("SCID assessment would start here...")
            print("For demo purposes, marking as completed...")
            # In a real scenario, this would involve actual SCID interaction

        # Simulate DA analysis
        print("🧠 Phase 5: DA Analysis")
        print("-" * 40)

        print("Differential diagnosis analysis would be performed here...")
        print("For demo purposes, simulating completion...")

        # Simulate treatment planning
        print("💊 Phase 6: Treatment Planning")
        print("-" * 40)

        print("Treatment plan generation would occur here...")
        print("For demo purposes, simulating completion...")

        # Get final results
        print("📊 Final Results:")
        print("-" * 40)

        try:
            status = workflow.get_session_status(session_id)
            print(f"Session Status: {status}")

            export_data = workflow.export_assessment(session_id)
            print("Assessment data exported successfully!")

            # Show key information
            if isinstance(export_data, str):
                data = json.loads(export_data)
                print(f"Patient Profile: {data.get('patient_profile', {})}")
                print(f"Current Stage: {data.get('workflow_status', 'unknown')}")
                print(f"Is Complete: {data.get('is_complete', False)}")

        except Exception as e:
            print(f"Could not retrieve final results: {e}")

        print("\n✅ Complete workflow test simulation completed!")

        return {
            'success': True,
            'session_id': session_id,
            'stages_completed': ['profile', 'concern_assessment', 'module_selection']
        }

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def test_workflow_components():
    """Test individual workflow components"""
    print("\n🔧 Testing Workflow Components")
    print("=" * 60)

    try:
        from assessment_workflow import AssessmentWorkflow
        from concern import PresentingConcernChatbot
        from agents.tpa.utilize_tpa import TPAUtil

        # Test concern chatbot
        print("Testing concern chatbot...")
        llm_client = LLMClient()
        concern_bot = PresentingConcernChatbot(llm_client=llm_client, max_questions=3)
        response = concern_bot.start_conversation()
        print(f"✅ Concern chatbot: {response.get('question_id', 'unknown')}")

        # Test TPA utility
        print("Testing TPA utility...")
        tpa = TPAUtil()
        plan = tpa.get_treatment_plan({
            'age': 30,
            'gender': 'female',
            'primary_diagnosis': 'Generalized Anxiety Disorder',
            'severity': 'moderate',
            'symptoms': ['excessive worry', 'panic attacks']
        })
        print(f"✅ TPA utility: Plan created with {len(plan.top_actions)} actions")

        # Test workflow initialization
        print("Testing workflow initialization...")
        workflow = AssessmentWorkflow(use_llm=True)
        session_id, welcome = workflow.start_assessment("component_test")
        print(f"✅ Workflow: Session {session_id} created")

        print("✅ All components tested successfully!")

    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()

def demonstrate_enhanced_features():
    """Demonstrate enhanced features of the assessment system"""
    print("\n✨ Enhanced Features Demonstration")
    print("=" * 60)

    try:
        from concern import PresentingConcernChatbot
        from agents.llm_client import LLMClient

        llm_client = LLMClient()
        chatbot = PresentingConcernChatbot(llm_client=llm_client, max_questions=5)

        # Test enhanced keyword extraction
        print("🔍 Enhanced Keyword Extraction:")
        test_concerns = [
            "severe anxiety and panic attacks",
            "feeling depressed and hopeless",
            "intrusive thoughts about contamination",
            "difficulty sleeping and fatigue"
        ]

        for concern in test_concerns:
            chatbot.data.presenting_concern = concern
            keyword = chatbot._extract_concern_keyword()
            print(f"  '{concern}' → '{keyword}'")

        # Test conversation context building
        print("\n📝 Conversation Context Building:")
        chatbot.data.presenting_concern = "severe anxiety attacks"
        chatbot.data.hpi_severity = 8
        chatbot.data.hpi_frequency = "daily"

        context = chatbot._build_conversation_context()
        print(f"  Context: {context[:100]}...")

        # Test goal completion
        print("\n🎯 Goal Completion Tracking:")
        goal_summary = chatbot._get_goal_completion_summary()
        print(f"  Completion: {goal_summary['completion_percentage']}%")
        print(f"  Completed: {len(goal_summary['completed_goals'])} goals")
        print(f"  Remaining: {len(goal_summary['missing_goals'])} goals")

        print("✅ Enhanced features demonstrated successfully!")

    except Exception as e:
        print(f"❌ Enhanced features demo failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Complete Assessment Workflow Tests")
    print("=" * 60)

    # Test complete workflow
    workflow_result = test_complete_workflow()

    # Test individual components
    test_workflow_components()

    # Demonstrate enhanced features
    demonstrate_enhanced_features()

    print("\n" + "=" * 60)
    if workflow_result.get('success', False):
        print("🎉 Overall test result: SUCCESS")
        print(f"   Session ID: {workflow_result.get('session_id', 'unknown')}")
        print(f"   Stages completed: {workflow_result.get('stages_completed', [])}")
    else:
        print(f"❌ Overall test result: FAILED - {workflow_result.get('error', 'Unknown error')}")

    print("=" * 60)

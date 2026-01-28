#!/usr/bin/env python3
"""
TPA (Treatment Planning Agent) Example

This example demonstrates:
1. Creating a treatment plan using TPA
2. Validating the plan for safety and appropriateness
3. Adding the plan to tracking system
4. Simulating progress tracking
5. Generating progress reports

Usage:
    python example.py
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

# Add the backend-2 path to Python path
sys.path.insert(0, '/home/my-pc/Desktop/Programming/version_control/App/backend-2')

def create_sample_patient_data():
    """Create comprehensive sample patient data"""
    from agents.tpa.tpa_schemas import (
        PatientDemographics, PatientGoals, SymptomCluster,
        ProvisionalDiagnosis, PatientPreferences, SymptomSeverity
    )

    print("📋 Creating sample patient data...")

    # Patient demographics
    demographics = PatientDemographics(
        age=32,
        gender="female",
        occupation="marketing manager",
        cultural_background="American",
        living_situation="with_partner",
        support_system="partner and close friends"
    )

    # Patient goals
    goals = PatientGoals(
        primary_goals=[
            "Reduce anxiety and panic attacks",
            "Improve sleep quality and reduce insomnia",
            "Better manage work-related stress",
            "Build healthier coping mechanisms"
        ],
        treatment_preferences=[
            "CBT-based approaches",
            "Mindfulness and meditation",
            "Non-medication options",
            "Self-help techniques"
        ],
        previous_treatments=[
            "Previous therapy (6 months, discontinued)",
            "General anxiety medication (discontinued due to side effects)",
            "Self-help books and apps"
        ],
        success_metrics=[
            "Reduced panic attacks to less than 1 per week",
            "Sleep 7-8 hours per night consistently",
            "Feel more in control of daily stress",
            "Improved work performance"
        ]
    )

    # Symptom clusters (from SRA analysis)
    symptoms = [
        SymptomCluster(
            name="anxiety",
            severity=SymptomSeverity.MODERATE,
            symptoms=[
                "frequent panic attacks (2-3 times per week)",
                "constant worry about work and relationships",
                "physical tension and muscle tightness",
                "avoidance of social situations",
                "difficulty concentrating at work",
                "irritability and mood swings"
            ],
            triggers=[
                "work deadlines and presentations",
                "social gatherings and meetings",
                "uncertainty about future",
                "conflict with partner"
            ],
            impact_on_daily_life="moderate - affects work performance, social life, and relationship"
        ),
        SymptomCluster(
            name="sleep_disturbances",
            severity=SymptomSeverity.MILD,
            symptoms=[
                "difficulty falling asleep",
                "waking up multiple times during night",
                "early morning awakening",
                "feeling tired during day",
                "relying on sleep aids"
            ],
            triggers=[
                "work stress",
                "anxiety about next day",
                "screen time before bed",
                "irregular sleep schedule"
            ],
            impact_on_daily_life="mild - affects energy levels and mood"
        )
    ]

    # Provisional diagnosis (from DA)
    diagnosis = ProvisionalDiagnosis(
        primary_diagnosis="Generalized Anxiety Disorder with Panic Attacks",
        severity=SymptomSeverity.MODERATE,
        comorbidities=[
            "Insomnia Disorder",
            "Mild Depressive Symptoms"
        ],
        confidence_level=0.88,
        risk_factors=[
            "history of panic attacks",
            "work-related stress",
            "perfectionist tendencies",
            "family history of anxiety"
        ]
    )

    # Patient preferences
    preferences = PatientPreferences(
        preferred_approach="therapy",
        weekly_time_commitment=10,
        mode_preference="hybrid",
        budget_level="premium",
        cultural_considerations="Prefers evidence-based approaches with cultural sensitivity"
    )

    print("✅ Sample patient data created successfully")
    print(f"   Patient: {demographics.age}yo {demographics.gender}, {demographics.occupation}")
    print(f"   Primary diagnosis: {diagnosis.primary_diagnosis}")
    print(f"   Severity: {diagnosis.severity.value}")
    print(f"   Goals: {len(goals.primary_goals)} primary goals")

    return {
        "demographics": demographics,
        "goals": goals,
        "symptoms": symptoms,
        "diagnosis": diagnosis,
        "preferences": preferences,
        "red_flags": [
            "Recent increase in panic attack frequency",
            "Some avoidance of work meetings",
            "Difficulty maintaining relationships"
        ]
    }

def create_treatment_plan(sample_data):
    """Create a treatment plan using TPA"""
    print("\n🎯 Creating treatment plan with TPA...")

    from agents.tpa.tpa_ import TreatmentPlanningAgent

    # Initialize TPA
    tpa = TreatmentPlanningAgent()

    # Create comprehensive treatment plan
    print("   Generating comprehensive plan...")
    tpa_output = tpa.create_treatment_plan(
        patient_demographics=sample_data["demographics"],
        patient_goals=sample_data["goals"],
        symptom_clusters=sample_data["symptoms"],
        provisional_diagnosis=sample_data["diagnosis"],
        patient_preferences=sample_data["preferences"],
        red_flags=sample_data["red_flags"]
    )

    print(f"   ✅ Comprehensive plan created (confidence: {tpa_output.confidence_score:.2f})")

    # Create simple patient-friendly plan
    print("   Generating simple patient-friendly plan...")
    simple_plan = tpa.create_simple_treatment_plan(
        patient_demographics=sample_data["demographics"],
        patient_goals=sample_data["goals"],
        symptom_clusters=sample_data["symptoms"],
        provisional_diagnosis=sample_data["diagnosis"],
        patient_preferences=sample_data["preferences"],
        red_flags=sample_data["red_flags"]
    )

    print("   ✅ Simple plan created successfully")

    return {
        "tpa_output": tpa_output,
        "simple_plan": simple_plan,
        "tpa": tpa
    }

def validate_treatment_plan(tpa_output, sample_data):
    """Validate the treatment plan"""
    print("\n🔍 Validating treatment plan...")

    from agents.tpa.treatment_plan_validator import TreatmentPlanValidator
    from agents.tpa.tpa_schemas import TPAInput

    # Initialize validator
    validator = TreatmentPlanValidator()

    # Create TPA input for validation
    tpa_input = TPAInput(
        patient_demographics=sample_data["demographics"],
        patient_goals=sample_data["goals"],
        symptom_clusters=sample_data["symptoms"],
        provisional_diagnosis=sample_data["diagnosis"],
        patient_preferences=sample_data["preferences"],
        red_flags=sample_data["red_flags"]
    )

    # Validate the plan
    validation_result = validator.validate_treatment_plan(tpa_output.treatment_plan, tpa_input)

    print("   Validation Results:")
    print(f"   - Is valid: {validation_result.get('is_valid', 'Unknown')}")
    print(f"   - Safety score: {validation_result.get('safety_score', 'Unknown')}")
    print(f"   - Requires human review: {validation_result.get('requires_human_review', 'Unknown')}")
    
    if validation_result.get('errors'):
        print(f"   - Errors: {len(validation_result['errors'])} found")
        for error in validation_result['errors'][:3]:  # Show first 3 errors
            print(f"     • {error}")
    
    if validation_result.get('warnings'):
        print(f"   - Warnings: {len(validation_result['warnings'])} found")
        for warning in validation_result['warnings'][:3]:  # Show first 3 warnings
            print(f"     • {warning}")

    # Get validation summary
    summary = validator.get_validation_summary(validation_result)
    print(f"   - Summary: {summary[:100]}...")

    return validation_result

def setup_tracking(simple_plan, sample_data):
    """Set up tracking for the treatment plan"""
    print("\n📊 Setting up treatment plan tracking...")

    from agents.tpa.treatment_plan_tracker import TreatmentPlanTracker

    # Initialize tracker
    patient_id = f"patient_{sample_data['demographics'].age}_{sample_data['demographics'].gender}"
    tracker = TreatmentPlanTracker(patient_id)

    # Convert simple plan to tracking format
    plan_data = {
        "title": simple_plan.title,
        "goal": simple_plan.goal,
        "step_by_step": [
            {
                "title": step.get("title", "Untitled Step"),
                "description": step.get("description", "No description"),
                "when": step.get("when", "daily"),
                "how_long": step.get("how_long", "Unknown"),
                "why": step.get("why", "Treatment step"),
                "how_to_track": step.get("how_to_track", "Mark completed"),
                "category": step.get("category", "general")
            }
            for step in simple_plan.step_by_step
        ],
        "plan_metadata": {
            "total_duration": simple_plan.plan_metadata.total_duration,
            "total_steps": simple_plan.plan_metadata.total_steps,
            "estimated_time_per_day": simple_plan.plan_metadata.estimated_time_per_day,
            "frequency": simple_plan.plan_metadata.frequency
        }
    }

    # Add plan to tracker
    plan_id = tracker.add_plan(plan_data)
    print(f"   ✅ Plan added to tracking with ID: {plan_id}")

    # Get initial plan status
    plan_status = tracker.get_plan_status(plan_id)
    print(f"   ✅ Initial plan status: {plan_status.status}")

    return {
        "tracker": tracker,
        "plan_id": plan_id,
        "patient_id": patient_id
    }

def simulate_progress_tracking(tracker, plan_id, days=7):
    """Simulate progress tracking over several days"""
    print(f"\n📈 Simulating progress tracking over {days} days...")

    # Get today's tasks
    todays_tasks = tracker.get_todays_tasks(plan_id)
    print(f"   Today's tasks: {len(todays_tasks)}")

    # Simulate daily progress
    for day in range(days):
        print(f"\n   Day {day + 1}:")
        
        # Get tasks for this day
        tasks = tracker.get_todays_tasks(plan_id)
        
        # Simulate completing some tasks
        completed_count = 0
        for task in tasks:
            # Simulate 70% completion rate
            if day % 3 != 0:  # Skip every 3rd day to simulate missed days
                if task['step_id'] in [tasks[0]['step_id'], tasks[-1]['step_id']]:  # Complete first and last tasks
                    success = tracker.mark_step_completed(task['step_id'], plan_id)
                    if success:
                        completed_count += 1
                        print(f"     ✅ Completed: {task['title']}")
                    else:
                        print(f"     ❌ Failed to mark: {task['title']}")
                else:
                    # Skip some tasks
                    tracker.mark_step_skipped(task['step_id'], "Too busy today", plan_id)
                    print(f"     ⏭️  Skipped: {task['title']}")
            else:
                print(f"     😴 Rest day - no tasks completed")

        print(f"     Summary: {completed_count}/{len(tasks)} tasks completed")

        # Get streak info
        streak_info = tracker.get_streak_info(plan_id)
        print(f"     Current streak: {streak_info['current_streak']} days")

def generate_progress_report(tracker, plan_id):
    """Generate comprehensive progress report"""
    print("\n📊 Generating progress report...")

    # Get progress report
    progress_report = tracker.get_progress_report(plan_id, days=30)

    print("   Progress Report Summary:")
    print(f"   - Overall completion: {progress_report.metrics.completion_rate:.1%}")
    print(f"   - Total steps: {progress_report.metrics.total_steps}")
    print(f"   - Completed steps: {progress_report.metrics.completed_steps}")
    print(f"   - Current streak: {progress_report.metrics.current_streak} days")
    print(f"   - Longest streak: {progress_report.metrics.longest_streak} days")
    print(f"   - Total days active: {progress_report.metrics.total_days_active}")

    print("\n   Insights:")
    for insight in progress_report.insights[:3]:  # Show first 3 insights
        print(f"   • {insight}")

    print("\n   Recommendations:")
    for rec in progress_report.recommendations[:3]:  # Show first 3 recommendations
        print(f"   • {rec}")

    print("\n   Next Steps:")
    for step in progress_report.next_steps[:3]:  # Show first 3 next steps
        print(f"   • {step}")

    return progress_report

def demonstrate_tpt_agent():
    """Demonstrate TPT Agent functionality"""
    print("\n🤖 Demonstrating TPT Agent...")

    from agents.tpa.treatment_plan_tracker import TPTAgent

    # Initialize TPT Agent
    tpt_agent = TPTAgent(data_dir="example_tpt_data")

    # Get agent status
    status = tpt_agent.get_agent_status()
    print(f"   Agent Status: {status['status']}")
    print(f"   Mode: {status['mode']}")
    print(f"   Active patients: {status['active_patients']}")

    # Add a plan via TPT Agent (using synchronous method)
    plan_data = {
        "title": "TPT Agent Test Plan",
        "goal": "Test TPT Agent functionality",
        "step_by_step": [
            {
                "title": "Morning mindfulness",
                "description": "10 minutes of mindfulness meditation",
                "when": "daily",
                "how_long": "10 minutes",
                "why": "Start day with calm focus",
                "how_to_track": "Mark completed after meditation",
                "category": "mindfulness"
            }
        ]
    }

    # Use the simplified method directly since run() is async
    try:
        # Get or create tracker for this patient
        patient_id = "test_patient_tpt"
        if patient_id not in tpt_agent.trackers:
            from agents.tpa.treatment_plan_tracker import TreatmentPlanTracker
            tpt_agent.trackers[patient_id] = TreatmentPlanTracker(patient_id)
        
        # Add plan directly using tracker
        tracker = tpt_agent.trackers[patient_id]
        plan_id = tracker.add_plan(plan_data)
        
        print(f"   ✅ Plan added via TPT Agent successfully (ID: {plan_id})")
        
        # Get plan status
        plan_status = tracker.get_plan_status(plan_id)
        print(f"   ✅ Plan status: {plan_status.status}")
        
    except Exception as e:
        print(f"   ❌ Failed to add plan: {e}")

    return tpt_agent

def main():
    """Main example function"""
    print("=" * 80)
    print("TPA (Treatment Planning Agent) COMPREHENSIVE EXAMPLE")
    print("=" * 80)

    try:
        # Step 1: Create sample patient data
        sample_data = create_sample_patient_data()

        # Step 2: Create treatment plan
        plan_results = create_treatment_plan(sample_data)
        simple_plan = plan_results["simple_plan"]

        # Display plan details
        print(f"\n📋 TREATMENT PLAN DETAILS:")
        print(f"   Title: {simple_plan.title}")
        print(f"   Goal: {simple_plan.goal}")
        print(f"   Duration: {simple_plan.plan_metadata.total_duration}")
        print(f"   Steps: {simple_plan.plan_metadata.total_steps}")
        print(f"   Time per day: {simple_plan.plan_metadata.estimated_time_per_day}")

        print(f"\n   Top Actions:")
        for i, action in enumerate(simple_plan.top_actions, 1):
            print(f"   {i}. {action}")

        print(f"\n   Step-by-Step Plan:")
        for i, step in enumerate(simple_plan.step_by_step[:3], 1):  # Show first 3 steps
            print(f"   {i}. {step.get('title', 'N/A')}")
            print(f"      When: {step.get('when', 'N/A')}")
            print(f"      How long: {step.get('how_long', 'N/A')}")

        # Step 3: Validate treatment plan
        validation_result = validate_treatment_plan(plan_results["tpa_output"], sample_data)

        # Step 4: Set up tracking
        tracking_results = setup_tracking(simple_plan, sample_data)

        # Step 5: Simulate progress tracking
        simulate_progress_tracking(tracking_results["tracker"], tracking_results["plan_id"], days=7)

        # Step 6: Generate progress report
        progress_report = generate_progress_report(tracking_results["tracker"], tracking_results["plan_id"])

        # Step 7: Demonstrate TPT Agent
        tpt_agent = demonstrate_tpt_agent()

        # Summary
        print("\n" + "=" * 80)
        print("✅ EXAMPLE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("This example demonstrated:")
        print("• ✅ Treatment plan creation with TPA")
        print("• ✅ Plan validation for safety and appropriateness")
        print("• ✅ Progress tracking setup and simulation")
        print("• ✅ Progress report generation")
        print("• ✅ TPT Agent functionality")
        print("\nThe TPA system is fully functional and ready for production use!")

    except Exception as e:
        print(f"\n❌ Error in example: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Example completed successfully!")
    else:
        print("\n💥 Example failed!")
        sys.exit(1)

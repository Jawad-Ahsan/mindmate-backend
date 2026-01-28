#!/usr/bin/env python3
"""
TPA Utility Example Usage

This script demonstrates how to use the simplified TPA utility
to create and export treatment plans.
"""

import sys
import os
from pathlib import Path

# Add the backend path to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utilize_tpa import TPAUtil, PatientData, get_treatment_plan, export_plan

def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("BASIC TPA USAGE EXAMPLE")
    print("=" * 60)

    # Create patient data
    patient_data = {
        "age": 28,
        "gender": "female",
        "occupation": "software engineer",
        "primary_diagnosis": "Generalized Anxiety Disorder",
        "severity": "moderate",
        "symptoms": [
            "frequent panic attacks",
            "constant worry about work",
            "physical tension",
            "difficulty sleeping",
            "irritability"
        ],
        "primary_goals": [
            "Reduce anxiety and panic attacks",
            "Improve sleep quality",
            "Better manage work stress"
        ],
        "treatment_preferences": ["CBT approaches", "Mindfulness"],
        "weekly_time_commitment": 8,
        "preferred_approach": "self_help"
    }

    # Method 1: Using TPAUtil class
    print("\n1. Using TPAUtil class:")
    tpa = TPAUtil()
    plan = tpa.get_treatment_plan(patient_data)

    print(f"   ✅ Plan created: {plan.title}")
    print(f"   📋 Goal: {plan.goal}")
    print(f"   📊 Steps: {len(plan.step_by_step)}")
    print(f"   ⏰ Duration: {plan.plan_metadata.total_duration}")

    # Export to different formats
    print("\n   Exporting plan...")

    # Save as JSON
    json_output = tpa.export_plan(plan, 'json', 'treatment_plan.json')
    print("   💾 Saved as JSON")

    # Save as text
    text_output = tpa.export_plan(plan, 'text', 'treatment_plan.txt')
    print("   💾 Saved as text")

    # Save as markdown
    md_output = tpa.export_plan(plan, 'markdown', 'treatment_plan.md')
    print("   💾 Saved as markdown")

    # Method 2: Using convenience function
    print("\n2. Using convenience function:")
    plan2 = get_treatment_plan(patient_data)
    print(f"   ✅ Plan created: {plan2.title}")

    return plan

def example_patient_data_class():
    """Example using PatientData class"""
    print("\n" + "=" * 60)
    print("PATIENT DATA CLASS EXAMPLE")
    print("=" * 60)

    # Using PatientData class for type safety
    patient = PatientData(
        age=35,
        gender="male",
        occupation="teacher",
        primary_diagnosis="Major Depressive Disorder",
        severity="moderate",
        symptoms=[
            "persistent sadness",
            "loss of interest in activities",
            "fatigue",
            "difficulty concentrating",
            "changes in sleep and appetite"
        ],
        primary_goals=[
            "Improve mood and energy levels",
            "Reconnect with hobbies",
            "Better manage daily responsibilities"
        ],
        treatment_preferences=["Therapy", "Exercise"],
        weekly_time_commitment=12,
        preferred_approach="therapy",
        mode_preference="hybrid"
    )

    # Create plan
    tpa = TPAUtil()
    plan = tpa.get_treatment_plan(patient)

    print(f"Patient: {patient.age}yo {patient.gender}, {patient.occupation}")
    print(f"Diagnosis: {patient.primary_diagnosis} ({patient.severity})")
    print(f"Plan: {plan.title}")
    print(f"Duration: {plan.plan_metadata.total_duration}")

    # Show top actions
    print("\nTop Actions:")
    for i, action in enumerate(plan.top_actions, 1):
        print(f"{i}. {action}")

    return plan

def example_different_conditions():
    """Example with different mental health conditions"""
    print("\n" + "=" * 60)
    print("DIFFERENT CONDITIONS EXAMPLE")
    print("=" * 60)

    conditions = [
        {
            "name": "Social Anxiety Disorder",
            "severity": "mild",
            "symptoms": ["fear of social situations", "avoidance of public speaking", "physical symptoms in social settings"]
        },
        {
            "name": "Insomnia Disorder",
            "severity": "moderate",
            "symptoms": ["difficulty falling asleep", "frequent waking", "daytime fatigue", "racing thoughts at night"]
        },
        {
            "name": "PTSD",
            "severity": "severe",
            "symptoms": ["flashbacks", "hypervigilance", "emotional numbness", "avoidance of triggers"]
        }
    ]

    tpa = TPAUtil()

    for condition in conditions:
        print(f"\n📋 Condition: {condition['name']} ({condition['severity']})")

        patient_data = {
            "age": 30,
            "gender": "female",
            "primary_diagnosis": condition["name"],
            "severity": condition["severity"],
            "symptoms": condition["symptoms"],
            "primary_goals": ["Reduce symptoms and improve daily functioning"],
            "weekly_time_commitment": 10
        }

        plan = tpa.get_treatment_plan(patient_data)
        print(f"   📝 Plan: {plan.title}")
        print(f"   ⏱️  Duration: {plan.plan_metadata.total_duration}")
        print(f"   📊 Steps: {len(plan.step_by_step)}")

def example_quick_plan():
    """Example using quick_plan_from_dict method"""
    print("\n" + "=" * 60)
    print("QUICK PLAN DICTIONARY EXAMPLE")
    print("=" * 60)

    # Minimal data required
    minimal_data = {
        "age": 25,
        "gender": "male",
        "primary_diagnosis": "Panic Disorder",
        "severity": "moderate",
        "symptoms": ["panic attacks", "fear of dying", "chest pain", "shortness of breath"],
        "primary_goals": ["Reduce panic attacks", "Learn coping skills"]
    }

    tpa = TPAUtil()
    plan_dict = tpa.quick_plan_from_dict(minimal_data)

    print("Quick plan created:")
    print(f"Title: {plan_dict['title']}")
    print(f"Goal: {plan_dict['goal']}")
    print(f"Steps: {len(plan_dict['steps'])}")
    print(f"Duration: {plan_dict['duration']}")

    # Show first step
    if plan_dict['steps']:
        first_step = plan_dict['steps'][0]
        print(f"\nFirst step: {first_step.get('title', 'N/A')}")
        print(f"When: {first_step.get('when', 'N/A')}")

def main():
    """Run all examples"""
    print("🚀 TPA Utility Examples")
    print("This script demonstrates different ways to use the simplified TPA utility")

    try:
        # Run examples
        plan1 = example_basic_usage()
        plan2 = example_patient_data_class()
        example_different_conditions()
        example_quick_plan()

        print("\n" + "=" * 60)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe TPA utility provides:")
        print("• ✅ Simple get_treatment_plan(data) method")
        print("• ✅ Multiple export formats (JSON, text, markdown, HTML)")
        print("• ✅ Type-safe PatientData class")
        print("• ✅ Convenience functions")
        print("• ✅ No tracking complexity")
        print("\nFiles created:")
        print("• treatment_plan.json")
        print("• treatment_plan.txt")
        print("• treatment_plan.md")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

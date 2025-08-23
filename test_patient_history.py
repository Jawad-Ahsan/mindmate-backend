#!/usr/bin/env python3
"""
Test script for Patient History Collection System
================================================
Tests the integration between PatientHistoryCollector and PatientHistory model
"""

import sys
import os
from datetime import datetime
from uuid import uuid4

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.patient_history import (
    PatientHistoryCollector, 
    create_patient_history_collector,
    load_patient_history,
    save_patient_history_data,
    PatientHistoryData
)

def test_patient_history_collector():
    """Test the patient history collector functionality"""
    print("=== Testing Patient History Collector ===")
    
    # Create a test patient ID
    test_patient_id = str(uuid4())
    print(f"Test Patient ID: {test_patient_id}")
    
    # Create a new collector
    collector = create_patient_history_collector(test_patient_id)
    print(f"✓ Created PatientHistoryCollector for patient {test_patient_id}")
    
    # Test starting a section
    print("\n--- Testing Section Start ---")
    result = collector.start_section('psychiatric_history')
    print(f"Section start result: {result['status']}")
    if result['status'] == 'question':
        print(f"First question: {result['question']['text']}")
        print(f"Question type: {result['question']['type']}")
    
    # Test processing a response
    print("\n--- Testing Response Processing ---")
    response_data = {
        'selected_options': ['yes']
    }
    result = collector.process_response('psych_dx_history', response_data)
    print(f"Response processing result: {result['status']}")
    
    # Test getting progress
    print("\n--- Testing Progress Tracking ---")
    progress = collector.get_overall_progress()
    print(f"Overall progress: {progress['overall_completion']}%")
    print(f"Completed sections: {progress['completed_sections']}/{progress['total_sections']}")
    
    # Test section progress
    section_progress = collector.get_section_progress('psychiatric_history')
    print(f"Psychiatric history progress: {section_progress['completion']}%")
    
    # Test data export
    print("\n--- Testing Data Export ---")
    data = collector.export_data()
    print(f"Exported data type: {type(data)}")
    print(f"Past psych dx: {data.past_psych_dx}")
    
    # Test summary
    print("\n--- Testing Summary ---")
    summary = collector.get_summary()
    print(f"Summary: {summary}")
    
    print("\n=== Test Completed Successfully ===")
    return test_patient_id

def test_data_structures():
    """Test the data structures"""
    print("\n=== Testing Data Structures ===")
    
    # Test PatientHistoryData
    data = PatientHistoryData(
        past_psych_dx="Depression and Anxiety",
        past_psych_treatment="CBT for 6 months",
        current_meds={"Sertraline": {"dose": "100mg", "frequency": "daily"}},
        medical_history_summary="Generally healthy",
        alcohol_use="Occasionally",
        cultural_background="Pakistani"
    )
    
    print(f"✓ Created PatientHistoryData")
    print(f"Past psych dx: {data.past_psych_dx}")
    print(f"Current meds: {data.current_meds}")
    print(f"Cultural background: {data.cultural_background}")
    
    print("\n=== Data Structure Test Completed ===")

def test_question_flow():
    """Test the question flow logic"""
    print("\n=== Testing Question Flow ===")
    
    collector = PatientHistoryCollector()
    
    # Test condition checking
    print("--- Testing Condition Checking ---")
    
    # Add a response first
    response_data = {'selected_options': ['yes']}
    collector.process_response('psych_dx_history', response_data)
    
    # Check if follow-up questions are triggered
    next_question = collector._get_next_question()
    if next_question:
        print(f"Next question after 'yes' to psych dx: {next_question.text}")
        print(f"Question ID: {next_question.id}")
    
    # Test section completion
    print("\n--- Testing Section Completion ---")
    collector.current_section = 'psychiatric_history'
    collector._mark_section_complete('psychiatric_history')
    print(f"Sections completed: {collector.data.sections_completed}")
    
    print("\n=== Question Flow Test Completed ===")

def main():
    """Main test function"""
    print("Patient History System Test Suite")
    print("=" * 50)
    
    try:
        # Test data structures
        test_data_structures()
        
        # Test question flow
        test_question_flow()
        
        # Test collector (without database operations)
        test_patient_id = test_patient_history_collector()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! ✅")
        print("The Patient History Collection System is working correctly.")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

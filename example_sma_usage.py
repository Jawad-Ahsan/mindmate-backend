"""
SMA Usage Examples
=================
Demonstrates how to use the Specialist Matching Agent (SMA) system.
This script shows common use cases and patterns.
"""

import sys
import os
from datetime import datetime, timezone, timedelta
import uuid

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import get_db
from agents.sma.sma import SMA
from agents.sma.sma_schemas import (
    SpecialistSearchRequest, TopSpecialistsRequest, SlotHoldRequest,
    AppointmentConfirmRequest, ConsultationMode, SortOption
)

def example_1_basic_search():
    """Example 1: Basic specialist search"""
    print("🔍 Example 1: Basic Specialist Search")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # Create search request
        request = SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English", "Urdu"],
            page=1,
            size=5
        )
        
        # Perform search
        result = sma.search_specialists(request)
        
        print(f"Found {result['total_count']} specialists")
        print(f"Page {result['page']} of {(result['total_count'] + result['size'] - 1) // result['size']}")
        
        # Display results
        for i, specialist in enumerate(result['specialists'], 1):
            print(f"\n{i}. {specialist['full_name']}")
            print(f"   Type: {specialist['specialist_type']}")
            print(f"   Experience: {specialist['years_experience']} years")
            print(f"   Rating: {specialist['average_rating']}/5.0 ({specialist['total_reviews']} reviews)")
            print(f"   Fee: PKR {specialist['consultation_fee']}")
            print(f"   City: {specialist['city']}")
            print(f"   Specializations: {', '.join(specialist['specializations'])}")
        
        return result
        
    finally:
        db.close()

def example_2_advanced_search():
    """Example 2: Advanced search with filters"""
    print("\n🔍 Example 2: Advanced Search with Filters")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # Create advanced search request
        request = SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English"],
            specializations=["anxiety_disorders", "depression"],
            budget_max=5000.0,
            sort_by=SortOption.RATING_HIGH,
            page=1,
            size=3
        )
        
        # Perform search
        result = sma.search_specialists(request)
        
        print(f"Found {result['total_count']} specialists matching criteria")
        print(f"Applied filters: {result['search_criteria']['applied_filters']}")
        
        # Display top results
        for i, specialist in enumerate(result['specialists'], 1):
            print(f"\n{i}. {specialist['full_name']} (Rating: {specialist['average_rating']})")
            print(f"   Specializations: {', '.join(specialist['specializations'])}")
            print(f"   Fee: PKR {specialist['consultation_fee']}")
        
        return result
        
    finally:
        db.close()

def example_3_top_specialists():
    """Example 3: Get top specialists with recommendations"""
    print("\n🏆 Example 3: Top Specialists with Recommendations")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # Get top specialists
        request = TopSpecialistsRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English", "Urdu"],
            specializations=["depression"],
            limit=3
        )
        
        result = sma.get_top_specialists(request)
        
        print(f"Top {len(result['specialists'])} specialists for depression treatment:")
        
        for i, specialist in enumerate(result['specialists'], 1):
            print(f"\n{i}. {specialist['full_name']}")
            print(f"   Score: {specialist.get('match_score', 'N/A')}")
            print(f"   Experience: {specialist['years_experience']} years")
            print(f"   Rating: {specialist['average_rating']}/5.0")
        
        return result
        
    finally:
        db.close()

def example_4_specialist_details():
    """Example 4: Get specialist details and availability"""
    print("\n👨‍⚕️ Example 4: Specialist Details and Availability")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # First, get a specialist ID from search
        search_result = sma.search_specialists(SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            page=1,
            size=1
        ))
        
        if not search_result['specialists']:
            print("No specialists found")
            return None
        
        specialist_id = uuid.UUID(search_result['specialists'][0]['id'])
        
        # Get specialist details
        details = sma.get_specialist_details(specialist_id, include_slots=True)
        
        specialist = details['specialist']
        print(f"Specialist: {specialist['full_name']}")
        print(f"Type: {specialist['specialist_type']}")
        print(f"Bio: {specialist['bio'][:100]}..." if specialist['bio'] else "No bio available")
        print(f"Languages: {', '.join(specialist['languages_spoken'])}")
        print(f"Specializations: {', '.join(specialist['specializations'])}")
        
        # Show available slots
        slots = details['next_free_slots']
        print(f"\nNext {len(slots)} available slots:")
        for i, slot in enumerate(slots[:5], 1):  # Show first 5 slots
            slot_time = datetime.fromisoformat(slot['start_utc'].replace('Z', '+00:00'))
            print(f"   {i}. {slot_time.strftime('%Y-%m-%d %H:%M')} UTC")
        
        return details
        
    finally:
        db.close()

def example_5_appointment_booking():
    """Example 5: Appointment booking flow (simulated)"""
    print("\n📅 Example 5: Appointment Booking Flow (Simulated)")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # This is a simulation - in real usage, you'd have actual UUIDs
        print("Note: This is a simulation with mock data")
        
        # Simulate slot hold
        mock_slot_id = uuid.uuid4()
        mock_patient_id = uuid.uuid4()
        
        hold_request = SlotHoldRequest(
            slot_id=mock_slot_id,
            patient_id=mock_patient_id,
            hold_duration_minutes=10
        )
        
        print("1. Holding slot...")
        try:
            hold_result = sma.hold_slot(hold_request)
            print(f"   ✅ Slot held successfully")
            print(f"   Hold token: {hold_result['hold_token']}")
            print(f"   Expires at: {hold_result['expires_at']}")
            
            # Simulate appointment confirmation
            print("\n2. Confirming appointment...")
            confirm_request = AppointmentConfirmRequest(
                patient_id=mock_patient_id,
                hold_token=hold_result['hold_token'],
                consultation_mode=ConsultationMode.ONLINE,
                notes="First session - anxiety treatment"
            )
            
            appointment = sma.confirm_appointment(confirm_request)
            print(f"   ✅ Appointment confirmed")
            print(f"   Appointment ID: {appointment['appointment']['id']}")
            print(f"   Status: {appointment['appointment']['status']}")
            
        except ValueError as e:
            print(f"   ❌ Booking failed: {str(e)}")
            print("   (This is expected in simulation mode)")
        
        return True
        
    finally:
        db.close()

def example_6_health_check():
    """Example 6: System health check"""
    print("\n🏥 Example 6: System Health Check")
    print("-" * 50)
    
    db = next(get_db())
    sma = SMA(db)
    
    try:
        # Get health status
        health = sma.get_health_status()
        
        print(f"Status: {health['status']}")
        print(f"Service: {health['service']}")
        print(f"Version: {health['version']}")
        print(f"Message: {health['message']}")
        print(f"Timestamp: {health['timestamp']}")
        
        print(f"\nMetrics:")
        print(f"  - Total specialists: {health['metrics']['total_specialists']}")
        print(f"  - Total patients: {health['metrics']['total_patients']}")
        print(f"  - Active holds: {health['metrics']['active_holds']}")
        
        # Cleanup expired holds
        cleaned = sma.cleanup_expired_holds()
        print(f"  - Cleaned {cleaned} expired holds")
        
        return health
        
    finally:
        db.close()

def main():
    """Run all examples"""
    print("🚀 SMA Usage Examples")
    print("=" * 60)
    print("This script demonstrates common SMA usage patterns.\n")
    
    examples = [
        ("Basic Search", example_1_basic_search),
        ("Advanced Search", example_2_advanced_search),
        ("Top Specialists", example_3_top_specialists),
        ("Specialist Details", example_4_specialist_details),
        ("Appointment Booking", example_5_appointment_booking),
        ("Health Check", example_6_health_check)
    ]
    
    results = {}
    
    for name, example_func in examples:
        try:
            print(f"\n📋 Running {name}...")
            result = example_func()
            results[name] = "✅ Success"
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")
            results[name] = f"❌ Failed: {str(e)}"
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Example Results Summary:")
    for name, status in results.items():
        print(f"  {name}: {status}")
    
    print("\n🎉 Examples completed!")
    print("Note: Some examples may fail if no data exists in the database.")

if __name__ == "__main__":
    main()

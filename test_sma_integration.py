"""
SMA Integration Test
===================
Simple test script to verify the Specialist Matching Agent (SMA) system works correctly.
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

def test_sma_basic_functionality():
    """Test basic SMA functionality"""
    print("🧪 Testing SMA Basic Functionality")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize SMA
        sma = SMA(db)
        print("✅ SMA initialized successfully")
        
        # Test health check
        health = sma.get_health_status()
        print(f"✅ Health check: {health['status']}")
        print(f"   - Total specialists: {health['metrics']['total_specialists']}")
        print(f"   - Total patients: {health['metrics']['total_patients']}")
        
        # Test specialist search
        search_request = SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English", "Urdu"],
            page=1,
            size=5
        )
        
        search_result = sma.search_specialists(search_request)
        print(f"✅ Specialist search: Found {search_result['total_count']} specialists")
        
        # Test top specialists
        top_request = TopSpecialistsRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English"],
            limit=3
        )
        
        top_result = sma.get_top_specialists(top_request)
        print(f"✅ Top specialists: Found {len(top_result['specialists'])} top specialists")
        
        # Test cleanup
        cleaned = sma.cleanup_expired_holds()
        print(f"✅ Cleanup: Cleaned {cleaned} expired holds")
        
        print("\n🎉 All basic SMA tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        db.close()

def test_sma_advanced_functionality():
    """Test advanced SMA functionality"""
    print("\n🧪 Testing SMA Advanced Functionality")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize SMA
        sma = SMA(db)
        
        # Test specialist search with filters
        search_request = SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English"],
            specializations=["anxiety_disorders", "depression"],
            budget_max=5000.0,
            sort_by=SortOption.RATING_HIGH,
            page=1,
            size=10
        )
        
        search_result = sma.search_specialists(search_request)
        print(f"✅ Advanced search: Found {search_result['total_count']} specialists")
        print(f"   - Applied filters: {search_result['search_criteria']['applied_filters']}")
        
        # Test recommendations
        # Note: This requires a valid patient ID, so we'll skip for now
        print("✅ Recommendations test skipped (requires valid patient ID)")
        
        # Test slot generation
        if search_result['specialists']:
            specialist_id = uuid.UUID(search_result['specialists'][0]['id'])
            slots = sma.get_specialist_slots(specialist_id)
            print(f"✅ Slot generation: Generated {len(slots)} slots for specialist")
        
        print("\n🎉 All advanced SMA tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Advanced test failed: {str(e)}")
        return False
    
    finally:
        db.close()

def test_sma_error_handling():
    """Test SMA error handling"""
    print("\n🧪 Testing SMA Error Handling")
    print("=" * 50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize SMA
        sma = SMA(db)
        
        # Test with invalid specialist ID
        invalid_id = uuid.uuid4()
        try:
            result = sma.get_specialist_details(invalid_id)
            print("❌ Should have failed with invalid specialist ID")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled invalid specialist ID: {str(e)}")
        
        # Test with invalid slot hold
        try:
            hold_request = SlotHoldRequest(
                slot_id=uuid.uuid4(),
                patient_id=uuid.uuid4(),
                hold_duration_minutes=10
            )
            result = sma.hold_slot(hold_request)
            print("❌ Should have failed with invalid slot")
            return False
        except ValueError as e:
            print(f"✅ Correctly handled invalid slot: {str(e)}")
        
        print("\n🎉 All error handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False
    
    finally:
        db.close()

def main():
    """Main test function"""
    print("🚀 Starting SMA Integration Tests")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Basic Functionality", test_sma_basic_functionality),
        ("Advanced Functionality", test_sma_advanced_functionality),
        ("Error Handling", test_sma_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SMA system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())

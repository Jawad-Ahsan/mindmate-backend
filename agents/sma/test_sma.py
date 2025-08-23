"""
Test SMA - Demonstration of Specialist Matching Agent
====================================================
Simple test script to demonstrate SMA functionality
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Mock database session for testing
class MockDBSession:
    """Mock database session for testing"""
    def __init__(self):
        self.specialists = []
        self.patients = []
        self.appointments = []
    
    def query(self, model_class):
        return MockQuery(self, model_class)
    
    def add(self, obj):
        if hasattr(obj, 'id'):
            if 'specialist' in str(type(obj)).lower():
                self.specialists.append(obj)
            elif 'patient' in str(type(obj)).lower():
                self.patients.append(obj)
            elif 'appointment' in str(type(obj)).lower():
                self.appointments.append(obj)
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass

class MockQuery:
    """Mock query object"""
    def __init__(self, session, model_class):
        self.session = session
        self.model_class = model_class
        self.filters = []
    
    def filter(self, *args):
        self.filters.extend(args)
        return self
    
    def join(self, *args):
        return self
    
    def distinct(self):
        return self
    
    def all(self):
        return []
    
    def first(self):
        return None
    
    def count(self):
        return 0

def test_sma_functionality():
    """Test basic SMA functionality"""
    print("=== Testing SMA Functionality ===\n")
    
    # Create mock database session
    db = MockDBSession()
    
    # Import SMA components
    try:
        from sma import SMA
        from sma_schemas import (
            SpecialistSearchRequest, TopSpecialistsRequest, 
            ConsultationMode, SortOption
        )
        
        # Create SMA instance
        sma = SMA(db)
        
        # Test 1: Health check
        print("1. Testing Health Check:")
        health = sma.get_health_status()
        print(f"   Status: {health['status']}")
        print(f"   Service: {health['service']}")
        print(f"   Message: {health['message']}")
        print()
        
        # Test 2: Specialist search
        print("2. Testing Specialist Search:")
        search_request = SpecialistSearchRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English", "Urdu"],
            specializations=["depression", "anxiety"],
            budget_max=5000.0,
            sort_by=SortOption.BEST_MATCH,
            page=1,
            size=10
        )
        
        try:
            result = sma.search_specialists(search_request)
            print(f"   Found {result['total_count']} specialists")
            print(f"   Page: {result['page']}")
            print(f"   Has more: {result['has_more']}")
        except Exception as e:
            print(f"   Search error: {str(e)}")
        print()
        
        # Test 3: Top specialists
        print("3. Testing Top Specialists:")
        top_request = TopSpecialistsRequest(
            consultation_mode=ConsultationMode.ONLINE,
            languages=["English"],
            specializations=["depression"],
            limit=3
        )
        
        try:
            result = sma.get_top_specialists(top_request)
            print(f"   Found {len(result['specialists'])} top specialists")
            print(f"   Rationale keys: {list(result['rationale'].keys())}")
        except Exception as e:
            print(f"   Top specialists error: {str(e)}")
        print()
        
        # Test 4: Recommendations
        print("4. Testing Recommendations:")
        patient_id = uuid.uuid4()
        
        try:
            result = sma.get_matching_recommendations(
                patient_id=patient_id,
                specializations=["anxiety"],
                consultation_mode=ConsultationMode.ONLINE,
                budget_max=3000.0,
                limit=2
            )
            print(f"   Generated {len(result['specialists'])} recommendations")
            print(f"   Patient context: {result.get('patient_context', {})}")
        except Exception as e:
            print(f"   Recommendations error: {str(e)}")
        print()
        
        # Test 5: Cleanup
        print("5. Testing Cleanup:")
        cleaned = sma.cleanup_expired_holds()
        print(f"   Cleaned up {cleaned} expired holds")
        print()
        
        print("=== SMA Test Completed ===")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all SMA components are properly installed")
    except Exception as e:
        print(f"Test error: {e}")

def demonstrate_api_usage():
    """Demonstrate how to use SMA API endpoints"""
    print("=== SMA API Usage Examples ===\n")
    
    print("1. Search Specialists:")
    print("   GET /sma/specialists/search?")
    print("   - consultation_mode=online")
    print("   - specializations=depression,anxiety")
    print("   - budget_max=5000")
    print("   - sort_by=best_match")
    print("   - page=1&size=20")
    print()
    
    print("2. Get Top Specialists:")
    print("   POST /sma/specialists/top")
    print("   {")
    print('     "consultation_mode": "online",')
    print('     "languages": ["English", "Urdu"],')
    print('     "specializations": ["depression"],')
    print('     "limit": 3')
    print("   }")
    print()
    
    print("3. Hold Slot:")
    print("   POST /sma/appointments/hold")
    print("   {")
    print('     "slot_id": "uuid",')
    print('     "patient_id": "uuid",')
    print('     "hold_duration_minutes": 10')
    print("   }")
    print()
    
    print("4. Confirm Appointment:")
    print("   POST /sma/appointments/confirm")
    print("   {")
    print('     "hold_token": "uuid",')
    print('     "consultation_mode": "online",')
    print('     "notes": "Optional notes"')
    print("   }")
    print()
    
    print("5. Get Patient Appointments:")
    print("   GET /sma/appointments/patient/{patient_id}")
    print("   - page=1&size=20")
    print("   - status=confirmed")
    print()
    
    print("6. Get Recommendations:")
    print("   GET /sma/recommendations/{patient_id}")
    print("   - specializations=anxiety,depression")
    print("   - consultation_mode=online")
    print("   - budget_max=3000")
    print("   - limit=3")
    print()

if __name__ == "__main__":
    print("SMA - Specialist Matching Agent Test Suite")
    print("=" * 50)
    print()
    
    # Run functionality test
    test_sma_functionality()
    print()
    
    # Show API usage examples
    demonstrate_api_usage()
    
    print("Test completed successfully!")

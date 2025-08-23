"""
Test Script for Users Management Endpoints
==========================================
This script demonstrates how to use the users management API endpoints
"""

import requests
import json
import uuid
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust to your FastAPI server URL
API_BASE = f"{BASE_URL}/admin/users"

def test_get_specialist_profile():
    """Test getting specialist profile with documents"""
    print("\n=== Testing Get Specialist Profile ===")
    
    # Replace with actual specialist ID from your database
    specialist_id = "123e4567-e89b-12d3-a456-426614174000"  # Example UUID
    
    try:
        response = requests.get(f"{API_BASE}/specialists/{specialist_id}/profile")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Specialist profile retrieved successfully")
            print(f"Name: {data['first_name']} {data['last_name']}")
            print(f"Email: {data['email']}")
            print(f"Approval Status: {data['approval_status']}")
            print(f"Email Verified: {data['is_email_verified']}")
            
            if data['approval_data']:
                print(f"Documents: {len(data['approval_data']['documents'])} uploaded")
                for doc in data['approval_data']['documents']:
                    print(f"  - {doc['document_type']}: {doc['document_name']} ({doc['verification_status']})")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_approve_specialist():
    """Test approving a specialist"""
    print("\n=== Testing Approve Specialist ===")
    
    specialist_id = "123e4567-e89b-12d3-a456-426614174000"  # Example UUID
    
    payload = {
        "specialist_id": specialist_id,
        "action": "approve",
        "reason": "All documents verified and qualifications meet requirements. Specialist has valid license and appropriate experience.",
        "admin_notes": "Background check completed successfully. Ready for practice."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/specialists/{specialist_id}/action",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Specialist approved successfully")
            print(f"Action: {data['action']}")
            print(f"Previous Status: {data['previous_status']}")
            print(f"New Status: {data['new_status']}")
            print(f"Message: {data['message']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_reject_specialist():
    """Test rejecting a specialist"""
    print("\n=== Testing Reject Specialist ===")
    
    specialist_id = "123e4567-e89b-12d3-a456-426614174000"  # Example UUID
    
    payload = {
        "specialist_id": specialist_id,
        "action": "reject",
        "reason": "Incomplete documentation provided. Missing required license verification and professional certifications.",
        "admin_notes": "Applicant needs to resubmit with complete documentation package."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/specialists/{specialist_id}/action",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Specialist rejected successfully")
            print(f"Action: {data['action']}")
            print(f"Previous Status: {data['previous_status']}")
            print(f"New Status: {data['new_status']}")
            print(f"Reason: {data['reason']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_suspend_specialist():
    """Test suspending a specialist"""
    print("\n=== Testing Suspend Specialist ===")
    
    specialist_id = "123e4567-e89b-12d3-a456-426614174000"  # Example UUID
    
    payload = {
        "specialist_id": specialist_id,
        "action": "suspend",
        "reason": "Multiple patient complaints received regarding professional conduct. Investigation required.",
        "admin_notes": "Suspension pending investigation. Specialist notified of temporary suspension."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/specialists/{specialist_id}/action",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Specialist suspended successfully")
            print(f"Action: {data['action']}")
            print(f"Previous Status: {data['previous_status']}")
            print(f"New Status: {data['new_status']}")
            print(f"Message: {data['message']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_activate_patient():
    """Test activating a patient"""
    print("\n=== Testing Activate Patient ===")
    
    patient_id = "456e7890-e89b-12d3-a456-426614174000"  # Example UUID
    
    payload = {
        "patient_id": patient_id,
        "action": "activate",
        "reason": "Patient account verification completed. All required information provided and verified.",
        "admin_notes": "Patient can now access full platform features."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/patients/{patient_id}/action",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Patient activated successfully")
            print(f"Action: {data['action']}")
            print(f"Previous Status: {data['previous_status']}")
            print(f"New Status: {data['new_status']}")
            print(f"Message: {data['message']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_deactivate_patient():
    """Test deactivating a patient"""
    print("\n=== Testing Deactivate Patient ===")
    
    patient_id = "456e7890-e89b-12d3-a456-426614174000"  # Example UUID
    
    payload = {
        "patient_id": patient_id,
        "action": "deactivate",
        "reason": "Patient requested account deactivation. All data retention policies followed.",
        "admin_notes": "Patient data archived as per policy. Account can be reactivated if needed."
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/patients/{patient_id}/action",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Patient deactivated successfully")
            print(f"Action: {data['action']}")
            print(f"Previous Status: {data['previous_status']}")
            print(f"New Status: {data['new_status']}")
            print(f"Reason: {data['reason']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check successful")
            print(f"Status: {data['status']}")
            print(f"Service: {data['service']}")
            print(f"Message: {data['message']}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Users Management API Test Suite")
    print("=" * 50)
    
    # Test health check first
    test_health_check()
    
    # Test specialist management
    test_get_specialist_profile()
    test_approve_specialist()
    test_reject_specialist()
    test_suspend_specialist()
    
    # Test patient management
    test_activate_patient()
    test_deactivate_patient()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")

if __name__ == "__main__":
    main()

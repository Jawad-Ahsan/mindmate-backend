"""
Integration Test for Users Management System
===========================================
Simple test to verify all components work together
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly"""
    print("Testing imports...")
    
    try:
        # Test model imports
        from models.sql_models.patient_models import Patient, PatientAuthInfo
        from models.sql_models.specialist_models import Specialists, SpecialistsAuthInfo
        from models.sql_models.admin_models import Admin
        print("✅ SQL models imported successfully")
        
        # Test schema imports
        from models.pydantic_models.users_management_schema import (
            SpecialistProfileResponse, SpecialistActionRequest, 
            PatientActionRequest, ActionTypeEnum
        )
        print("✅ Pydantic schemas imported successfully")
        
        # Test service imports
        from services.admin.users_management import UsersManagementService
        print("✅ Users management service imported successfully")
        
        # Test router imports
        from routers.admin_routes.users_management import router
        print("✅ Admin router imported successfully")
        
        # Test authentication imports
        from routers.authentication.authenticate import (
            get_current_user_from_token, create_access_token
        )
        print("✅ Authentication module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_schema_validation():
    """Test schema validation"""
    print("\nTesting schema validation...")
    
    try:
        from models.pydantic_models.users_management_schema import (
            SpecialistActionRequest, PatientActionRequest, ActionTypeEnum
        )
        import uuid
        
        # Test specialist action request
        specialist_request = SpecialistActionRequest(
            specialist_id=uuid.uuid4(),
            action=ActionTypeEnum.APPROVE,
            reason="All documents verified and qualifications meet requirements. Specialist has valid license and appropriate experience.",
            admin_notes="Background check completed successfully."
        )
        print("✅ Specialist action request validation passed")
        
        # Test patient action request
        patient_request = PatientActionRequest(
            patient_id=uuid.uuid4(),
            action=ActionTypeEnum.ACTIVATE,
            reason="Patient account verification completed. All required information provided and verified.",
            admin_notes="Patient can now access full platform features."
        )
        print("✅ Patient action request validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False

def test_enum_values():
    """Test enum values"""
    print("\nTesting enum values...")
    
    try:
        from models.pydantic_models.users_management_schema import ActionTypeEnum, UserTypeEnum
        
        # Test action types
        assert ActionTypeEnum.APPROVE == "approve"
        assert ActionTypeEnum.REJECT == "reject"
        assert ActionTypeEnum.SUSPEND == "suspend"
        assert ActionTypeEnum.ACTIVATE == "activate"
        assert ActionTypeEnum.DEACTIVATE == "deactivate"
        assert ActionTypeEnum.UNSUSPEND == "unsuspend"
        print("✅ Action type enums working correctly")
        
        # Test user types
        assert UserTypeEnum.SPECIALIST == "specialist"
        assert UserTypeEnum.PATIENT == "patient"
        assert UserTypeEnum.ADMIN == "admin"
        print("✅ User type enums working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Enum test error: {e}")
        return False

def test_service_instantiation():
    """Test service instantiation"""
    print("\nTesting service instantiation...")
    
    try:
        from services.admin.users_management import UsersManagementService
        
        # This should not raise an error even without a real database session
        # The service should be able to be instantiated
        service = UsersManagementService(None)  # Pass None for testing
        print("✅ Users management service instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Service instantiation error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Users Management System Integration Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_schema_validation,
        test_enum_values,
        test_service_instantiation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for use.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

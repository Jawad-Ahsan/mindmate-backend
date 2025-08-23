#!/usr/bin/env python3
"""
Script to delete all specialist-related data from the database.
This will remove specialists and all related data without affecting other tables.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from database.database import get_db, engine
from models.sql_models.specialist_models import (
    Specialists, 
    SpecialistsAuthInfo, 
    SpecialistsApprovalData,
    SpecialistSpecializations
)
from sqlalchemy.orm import Session
from sqlalchemy import text

def delete_all_specialists():
    """Delete all specialist-related data from the database"""
    
    print("🔍 Starting specialist data deletion...")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Check current counts
        specialist_count = db.query(Specialists).count()
        auth_info_count = db.query(SpecialistsAuthInfo).count()
        approval_data_count = db.query(SpecialistsApprovalData).count()
        specializations_count = db.query(SpecialistSpecializations).count()
        
        print(f"📊 Current specialist data counts:")
        print(f"   - Specialists: {specialist_count}")
        print(f"   - Auth Info: {auth_info_count}")
        print(f"   - Approval Data: {approval_data_count}")
        print(f"   - Specializations: {specializations_count}")
        
        if specialist_count == 0:
            print("✅ No specialist data found. Database is already clean.")
            return
        
        # Confirm deletion
        print("\n⚠️  WARNING: This will permanently delete ALL specialist data!")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm != "DELETE":
            print("❌ Deletion cancelled.")
            return
        
        print("\n🗑️  Deleting specialist data...")
        
        # Delete in correct order to respect foreign key constraints
        # 1. Delete specializations first (references specialists)
        deleted_specs = db.query(SpecialistSpecializations).delete()
        print(f"   - Deleted {deleted_specs} specializations")
        
        # 2. Delete approval data (references specialists)
        deleted_approvals = db.query(SpecialistsApprovalData).delete()
        print(f"   - Deleted {deleted_approvals} approval records")
        
        # 3. Delete auth info (references specialists)
        deleted_auth = db.query(SpecialistsAuthInfo).delete()
        print(f"   - Deleted {deleted_auth} auth records")
        
        # 4. Delete specialists (main table)
        deleted_specialists = db.query(Specialists).delete()
        print(f"   - Deleted {deleted_specialists} specialists")
        
        # Commit the changes
        db.commit()
        
        print(f"\n✅ Successfully deleted all specialist data!")
        print(f"   - Total specialists removed: {deleted_specialists}")
        
        # Verify deletion
        remaining_specialists = db.query(Specialists).count()
        remaining_auth = db.query(SpecialistsAuthInfo).count()
        remaining_approvals = db.query(SpecialistsApprovalData).count()
        remaining_specs = db.query(SpecialistSpecializations).count()
        
        print(f"\n📊 Verification - Remaining data:")
        print(f"   - Specialists: {remaining_specialists}")
        print(f"   - Auth Info: {remaining_auth}")
        print(f"   - Approval Data: {remaining_approvals}")
        print(f"   - Specializations: {remaining_specs}")
        
        if all(count == 0 for count in [remaining_specialists, remaining_auth, remaining_approvals, remaining_specs]):
            print("✅ All specialist data successfully removed!")
        else:
            print("⚠️  Some data may still remain. Check manually if needed.")
            
    except Exception as e:
        print(f"❌ Error during deletion: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🧹 Specialist Data Cleanup Tool")
    print("=" * 40)
    delete_all_specialists()
    print("\n🏁 Cleanup complete!")


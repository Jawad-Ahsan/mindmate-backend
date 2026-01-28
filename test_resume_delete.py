import sys
import os
import uuid
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from agents.pima.scid.scid_assessment import SCIDAssessment
from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel

def test_resume_delete():
    db = SessionLocal()
    session_id = str(uuid.uuid4())
    patient_id = "550e8400-e29b-41d4-a716-446655440000" # Demo patient
    
    try:
        assessment_system = SCIDAssessment(use_llm=False)
        print(f"Starting test for Session: {session_id}")

        # 1. Manually create a dummy session in DB for testing
        print("Creating dummy session...")
        session_id, _ = assessment_system.start_assessment(
            db=db,
            patient_id=patient_id,
            module_id="MDD"
        )
        # Force set ID to ensure we track it (actually start_assessment generates one, let's use that)
        print(f"Session Created: {session_id}")
        
        # 2. Test Resume Context
        print("Testing Resume Context...")
        resume_context = assessment_system.get_resume_context(db, session_id)
        if resume_context and resume_context['session_id'] == session_id:
            print("Resume Context Retrieved Successfully")
            print(f"   Current Question: {resume_context['question_id']}")
        else:
            print("Failed to retrieve resume context")
            
        # 3. Test Delete
        print("Testing Delete...")
        assessment_system.delete_session(db, session_id)
        
        # 4. Verify Deletion
        print("Verifying Deletion...")
        deleted_session = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.session_id == session_id).first()
        if not deleted_session:
            print("Session Deleted Successfully from DB")
        else:
            print("Session still exists in DB!")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_resume_delete()

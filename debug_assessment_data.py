import sys
import os
import json
from uuid import UUID

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import SessionLocal
from agents.pima.scid.scid_assessment import SCIDAssessment
from routers.agents_routes.assessment_router import AssessmentResponse

def debug_assessment_results(session_id):
    db = SessionLocal()
    try:
        assessment_system = SCIDAssessment(use_llm=False)
        
        print(f"🔍 Fetching results for session: {session_id}")
        
        # Get results
        result = assessment_system.get_current_results(
            db=db,
            session_id=session_id,
            include_llm_summary=False # Skip LLM generation to just check data structure
        )
        
        # Construct response dict manually to mimic the router
        response_model = AssessmentResponse(
            session_id=result.session_id,
            patient_id=result.patient_id,
            module_id=result.module_id,
            module_name=result.module_name,
            assessment_data=result.assessment_data,
            clinical_insights={
                "diagnostic_summary": result.clinical_insights.diagnostic_summary,
                "key_symptoms": result.clinical_insights.key_symptoms,
                "severity_assessment": result.clinical_insights.severity_assessment,
                "functional_impairment": result.clinical_insights.functional_impairment,
                "differential_considerations": result.clinical_insights.differential_considerations,
                "treatment_implications": result.clinical_insights.treatment_implications,
                "risk_assessment": result.clinical_insights.risk_assessment,
                "follow_up_priorities": result.clinical_insights.follow_up_priorities,
                "clinical_notes": result.clinical_insights.clinical_notes
            },
            completion_percentage=result.completion_percentage,
            llm_summary=result.llm_summary,
            generated_at=result.generated_at
        )
        
        # Dump to JSON
        print("\n✅ JSON Output:")
        print(response_model.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Use the session ID from the user log
    debug_assessment_results("5ad1eefd-131a-4514-9772-944cf45a9ca3")

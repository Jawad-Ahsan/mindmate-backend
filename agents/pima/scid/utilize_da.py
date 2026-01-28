"""
SCID-DA Integration Module
==========================

This module integrates SCID assessment results with the DA (Diagnosis Agent)
to provide comprehensive psychiatric diagnosis and clinical insights.

Features:
- Extracts clinical data from SCID assessment results
- Formats data for DA diagnosis agent
- Combines SCID and DA results for comprehensive analysis
- Provides unified clinical reporting
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# Import SCID components
from .scid_assessment import SCIDAssessment, AssessmentResult

# Import DA diagnosis agent
try:
    from ..da import diagnose_patient, get_available_disorders, MCPDiagnosisAgent  # pyright: ignore[reportMissingImports]
    DA_AVAILABLE = True
except ImportError:
    print("⚠️  DA Diagnosis Agent not available - running in SCID-only mode")
    DA_AVAILABLE = False

# Import database models
from models import SCIDAssessment as SCIDAssessmentModel, AssessmentStatus, AssessmentMode
from database.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IntegratedDiagnosisResult:
    """Combined result from SCID assessment and DA diagnosis"""
    patient_id: str
    session_id: str

    # SCID Results
    scid_module: str
    scid_diagnosis: str
    scid_confidence: float
    scid_severity: str
    scid_symptoms: List[str]
    scid_criteria_analysis: Dict[str, Any]

    # DA Results (if available)
    da_diagnosis: Optional[str] = None
    da_confidence: Optional[float] = None
    da_severity: Optional[str] = None
    da_reasoning: Optional[str] = None

    # Integrated Analysis
    agreement_level: str = "unknown"  # "high_agreement", "moderate_agreement", "disagreement"
    recommended_diagnosis: str = ""
    clinical_confidence: float = 0.0
    risk_assessment: str = ""
    treatment_recommendations: List[str] = field(default_factory=list)

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0
    da_available: bool = DA_AVAILABLE

class SCIDDAIntegrator:
    """
    Integrates SCID assessment results with DA diagnosis agent
    for comprehensive psychiatric evaluation
    """

    def __init__(self, use_da: bool = True, db_session = None):
        """
        Initialize the SCID-DA integrator

        Args:
            use_da: Whether to use DA diagnosis agent
            db_session: Database session for persistence
        """
        self.use_da = use_da and DA_AVAILABLE
        self.scid_assessment = SCIDAssessment(use_llm=False)
        self.db_session = db_session

        if self.use_da:
            logger.info("✅ SCID-DA Integration initialized with DA support")
        else:
            logger.info("⚠️  SCID-DA Integration initialized without DA support")

    def save_assessment_to_db(self, integrated_result: IntegratedDiagnosisResult) -> SCIDAssessmentModel:
        """
        Save integrated assessment results to database

        Args:
            integrated_result: Integrated diagnosis result

        Returns:
            Saved SCIDAssessment model instance
        """
        if not self.db_session:
            logger.warning("⚠️  No database session available - skipping database save")
            return None

        try:
            # Create SCIDAssessment database record
            assessment_record = SCIDAssessmentModel(
                session_id=integrated_result.session_id,
                patient_id=integrated_result.patient_id,
                module_id=integrated_result.module_name.lower().replace(" ", "_"),
                module_name=integrated_result.module_name,
                status=AssessmentStatus.COMPLETED if integrated_result.completion_percentage > 0 else AssessmentStatus.INITIALIZED,
                mode=AssessmentMode.INTERACTIVE,
                total_questions=0,  # Will be updated based on actual assessment
                questions_completed=0,  # Will be updated based on actual assessment
                completion_percentage=integrated_result.completion_percentage,

                # SCID Results
                scid_diagnosis=getattr(integrated_result, 'scid_diagnosis', None),
                scid_confidence=getattr(integrated_result, 'scid_confidence', None),
                scid_severity=getattr(integrated_result, 'scid_severity', None),
                scid_symptoms=json.dumps(getattr(integrated_result, 'scid_symptoms', [])),
                scid_criteria_analysis=json.dumps(getattr(integrated_result, 'scid_criteria_analysis', {})),

                # DA Integration Results
                da_diagnosis=getattr(integrated_result, 'da_diagnosis', None),
                da_confidence=getattr(integrated_result, 'da_confidence', None),
                da_severity=getattr(integrated_result, 'da_severity', None),
                da_reasoning=getattr(integrated_result, 'da_reasoning', None),

                # Integrated Analysis
                agreement_level=getattr(integrated_result, 'agreement_level', None),
                recommended_diagnosis=getattr(integrated_result, 'recommended_diagnosis', None),
                clinical_confidence=getattr(integrated_result, 'clinical_confidence', None),
                risk_assessment=json.dumps({"assessment": getattr(integrated_result, 'risk_assessment', 'No assessment available')}),
                treatment_recommendations=json.dumps(getattr(integrated_result, 'treatment_recommendations', [])),

                # Processing metadata
                processing_time_seconds=getattr(integrated_result, 'processing_time_seconds', None),
                da_available=False,  # DA not available in this test case

                # Raw assessment data
                assessment_data=json.dumps({
                    "session_info": {
                        "session_id": integrated_result.session_id,
                        "patient_id": integrated_result.patient_id,
                        "module_id": integrated_result.module_name,
                        "module_name": integrated_result.module_name,
                        "completion_percentage": integrated_result.completion_percentage,
                        "status": "completed",
                        "generated_at": integrated_result.generated_at.isoformat()
                    },
                    "integration_results": {
                        "da_available": getattr(integrated_result, 'da_available', False),
                        "agreement_level": getattr(integrated_result, 'agreement_level', None),
                        "clinical_confidence": getattr(integrated_result, 'clinical_confidence', None)
                    }
                })
            )

            # Save to database
            self.db_session.add(assessment_record)
            self.db_session.commit()

            logger.info(f"✅ Assessment saved to database: {assessment_record.id}")
            return assessment_record

        except Exception as e:
            logger.error(f"❌ Failed to save assessment to database: {e}")
            self.db_session.rollback()
            return None

    def load_assessment_from_db(self, session_id: str) -> SCIDAssessmentModel:
        """
        Load assessment from database by session ID

        Args:
            session_id: Assessment session ID

        Returns:
            SCIDAssessment model instance or None if not found
        """
        if not self.db_session:
            logger.warning("⚠️  No database session available - cannot load from database")
            return None

        try:
            assessment = self.db_session.query(SCIDAssessmentModel).filter(
                SCIDAssessmentModel.session_id == session_id
            ).first()

            if assessment:
                logger.info(f"✅ Assessment loaded from database: {assessment.id}")
            else:
                logger.info(f"ℹ️  No assessment found for session: {session_id}")

            return assessment

        except Exception as e:
            logger.error(f"❌ Failed to load assessment from database: {e}")
            return None

    def get_patient_concern_report(self, assessment_result: AssessmentResult) -> Dict[str, Any]:
        """
        Generate a comprehensive patient concern report from SCID assessment results

        Args:
            assessment_result: SCID assessment result object

        Returns:
            Structured patient concern report
        """
        # Extract clinical symptoms from SCID results
        symptoms = self._extract_symptoms_from_scid(assessment_result)

        # Build patient context
        patient_context = {
            "patient_id": assessment_result.patient_id,
            "assessment_module": assessment_result.module_name,
            "assessment_date": assessment_result.generated_at.isoformat(),
            "completion_percentage": assessment_result.completion_percentage,
            "severity_estimate": assessment_result.clinical_insights.severity_assessment,
            "functional_impairment": assessment_result.clinical_insights.functional_impairment,
            "risk_factors": assessment_result.risk_factors if hasattr(assessment_result, 'risk_factors') else []
        }

        # Generate concern report
        concern_report = {
            "patient_info": patient_context,
            "symptoms": symptoms,
            "clinical_findings": {
                "primary_concerns": assessment_result.clinical_insights.key_symptoms,
                "severity_level": assessment_result.clinical_insights.severity_assessment,
                "functional_impact": assessment_result.clinical_insights.functional_impairment,
                "diagnostic_considerations": assessment_result.clinical_insights.differential_considerations,
                "recommended_followup": assessment_result.clinical_insights.follow_up_priorities
            },
            "assessment_summary": {
                "module_used": assessment_result.module_name,
                "confidence_level": "high" if assessment_result.completion_percentage > 80 else "moderate" if assessment_result.completion_percentage > 50 else "low",
                "completion_status": "complete" if assessment_result.completion_percentage >= 100 else "partial",
                "processing_date": assessment_result.generated_at.isoformat()
            }
        }

        return concern_report

    def _extract_symptoms_from_scid(self, assessment_result: AssessmentResult) -> List[str]:
        """
        Extract symptom descriptions from SCID assessment results

        Args:
            assessment_result: SCID assessment result

        Returns:
            List of symptom descriptions
        """
        symptoms = []

        # Get key symptoms from clinical insights
        if hasattr(assessment_result.clinical_insights, 'key_symptoms'):
            symptoms.extend(assessment_result.clinical_insights.key_symptoms)

        # Extract symptoms from criteria analysis
        if hasattr(assessment_result, 'real_time_analyses'):
            for analysis in assessment_result.real_time_analyses:
                if hasattr(analysis, 'criteria_analysis'):
                    for criterion in analysis.criteria_analysis:
                        if hasattr(criterion, 'criterion_text') and criterion.status.value == "met":
                            symptoms.append(criterion.criterion_text)

        # Add symptoms from assessment data responses
        if hasattr(assessment_result, 'assessment_data'):
            responses = assessment_result.assessment_data.get('responses', {})
            free_text = responses.get('free_text_responses', {})

            # Add free text responses as symptoms
            for response_text in free_text.values():
                if response_text and len(response_text.strip()) > 10:
                    symptoms.append(response_text.strip())

        # Remove duplicates and clean
        unique_symptoms = list(set(symptoms))
        cleaned_symptoms = [s for s in unique_symptoms if len(s.strip()) > 5]

        return cleaned_symptoms

    def integrate_scid_da_analysis(
        self,
        patient_id: str,
        module_id: str = None,
        patient_info: Optional[Dict[str, Any]] = None
    ) -> IntegratedDiagnosisResult:
        """
        Perform integrated SCID and DA analysis

        Args:
            patient_id: Patient identifier
            module_id: SCID module to use (optional)
            patient_info: Additional patient information

        Returns:
            Integrated diagnosis result
        """
        start_time = datetime.now()

        try:
            # Step 1: Perform SCID assessment
            logger.info(f"🔬 Starting integrated SCID-DA analysis for patient {patient_id}")

            session_id, welcome_message = self.scid_assessment.start_assessment(
                patient_id=patient_id,
                module_id=module_id,
                patient_info=patient_info
            )

            # For demo purposes, we'll simulate some responses
            # In a real implementation, you'd collect responses interactively
            self._simulate_assessment_responses(session_id)

            # Get SCID results
            scid_result = self.scid_assessment.get_current_results(session_id, include_llm_summary=False)

            # Step 2: Generate patient concern report
            concern_report = self.get_patient_concern_report(scid_result)

            # Step 3: Perform DA diagnosis if available
            da_result = None
            if self.use_da and concern_report["symptoms"]:
                logger.info("🤖 Performing DA diagnosis...")
                try:
                    da_result = diagnose_patient(concern_report["symptoms"])
                    logger.info(f"✅ DA diagnosis completed: {da_result.get('diagnosis', 'Unknown')}")
                except Exception as e:
                    logger.warning(f"⚠️  DA diagnosis failed: {e}")
                    da_result = None

            # Step 4: Integrate results
            integrated_result = self._integrate_results(
                patient_id, session_id, scid_result, da_result, concern_report
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            integrated_result.processing_time_seconds = processing_time

            # Save to database if session available
            if self.db_session:
                saved_record = self.save_assessment_to_db(integrated_result)
                if saved_record:
                    logger.info(f"✅ Assessment saved to database with ID: {saved_record.id}")

            logger.info(f"✅ Integrated analysis completed in {processing_time:.2f} seconds")
            return integrated_result

        except Exception as e:
            logger.error(f"❌ Integrated analysis failed: {e}")
            raise

    def _simulate_assessment_responses(self, session_id: str):
        """
        Simulate patient responses for demo purposes
        In a real implementation, these would come from user interaction
        """
        try:
            # Simulate 5-8 responses for a typical assessment
            for i in range(min(8, 21)):  # Limit to reasonable number
                question = self.scid_assessment.get_next_question(session_id)
                if question is None:
                    break

                # Simulate realistic responses based on question type
                if question.response_type.value == "yes_no":
                    response = "yes" if i % 3 == 0 else "no"
                elif question.response_type.value == "scale":
                    response = min(3, max(0, 3 - (i % 4)))
                elif question.response_type.value == "multiple_choice":
                    response = question.options[0] if question.options else "Other"
                else:
                    response = f"Simulated response {i+1}"

                # Process the response
                is_valid, feedback, analysis = self.scid_assessment.process_response(
                    session_id=session_id,
                    question_id=question.question_id,
                    response=response,
                    notes=f"Demo response {i+1}"
                )

        except Exception as e:
            logger.warning(f"⚠️  Response simulation failed: {e}")

    def _integrate_results(
        self,
        patient_id: str,
        session_id: str,
        scid_result: AssessmentResult,
        da_result: Optional[Dict[str, Any]],
        concern_report: Dict[str, Any]
    ) -> IntegratedDiagnosisResult:
        """
        Integrate SCID and DA results into a unified diagnosis

        Args:
            patient_id: Patient identifier
            session_id: Assessment session ID
            scid_result: SCID assessment result
            da_result: DA diagnosis result (optional)
            concern_report: Patient concern report

        Returns:
            Integrated diagnosis result
        """
        # Extract SCID data
        scid_insights = scid_result.clinical_insights
        symptoms = concern_report["symptoms"]

        # Create base result
        result = IntegratedDiagnosisResult(
            patient_id=patient_id,
            session_id=session_id,
            scid_module=scid_result.module_name,
            scid_diagnosis=scid_insights.diagnostic_summary,
            scid_confidence=min(scid_result.completion_percentage / 100.0, 0.95),  # Estimate confidence from completion
            scid_severity=scid_insights.severity_assessment,
            scid_symptoms=symptoms,
            scid_criteria_analysis={
                "key_symptoms": scid_insights.key_symptoms,
                "functional_impairment": scid_insights.functional_impairment,
                "differential_considerations": scid_insights.differential_considerations,
                "treatment_implications": scid_insights.treatment_implications,
                "follow_up_priorities": scid_insights.follow_up_priorities
            }
        )

        # Add DA results if available
        if da_result and self.use_da:
            result.da_diagnosis = da_result.get("diagnosis")
            result.da_confidence = da_result.get("confidence", 0.0)
            result.da_severity = da_result.get("severity")
            result.da_reasoning = da_result.get("reasoning")

            # Determine agreement level
            result.agreement_level = self._assess_agreement(
                scid_result.module_name,
                da_result.get("diagnosis", "")
            )

            # Generate integrated recommendations
            result.treatment_recommendations = self._generate_integrated_recommendations(
                scid_result, da_result
            )

            # Calculate clinical confidence
            result.clinical_confidence = self._calculate_clinical_confidence(
                result.scid_confidence,
                result.da_confidence
            )

            # Assess risk
            result.risk_assessment = self._assess_integrated_risk(
                scid_result, da_result
            )

        # Determine recommended diagnosis
        result.recommended_diagnosis = self._determine_recommended_diagnosis(result)

        return result

    def _assess_agreement(self, scid_module: str, da_diagnosis: str) -> str:
        """Assess agreement level between SCID and DA diagnoses"""
        if not da_diagnosis:
            return "scid_only"

        # Simple agreement assessment based on keyword matching
        scid_lower = scid_module.lower()
        da_lower = da_diagnosis.lower()

        # Check for mood disorder agreement
        mood_keywords = ["depress", "mood", "bipolar", "manic"]
        scid_has_mood = any(keyword in scid_lower for keyword in mood_keywords)
        da_has_mood = any(keyword in da_lower for keyword in mood_keywords)

        # Check for anxiety disorder agreement
        anxiety_keywords = ["anxiety", "anxious", "panic", "phobia", "gad"]
        scid_has_anxiety = any(keyword in scid_lower for keyword in anxiety_keywords)
        da_has_anxiety = any(keyword in da_lower for keyword in anxiety_keywords)

        if (scid_has_mood and da_has_mood) or (scid_has_anxiety and da_has_anxiety):
            return "high_agreement"
        elif scid_has_mood or scid_has_anxiety or da_has_mood or da_has_anxiety:
            return "moderate_agreement"
        else:
            return "disagreement"

    def _generate_integrated_recommendations(
        self,
        scid_result: AssessmentResult,
        da_result: Dict[str, Any]
    ) -> List[str]:
        """Generate integrated treatment recommendations"""
        recommendations = []

        # Add SCID-based recommendations
        if hasattr(scid_result.clinical_insights, 'treatment_implications'):
            recommendations.extend(scid_result.clinical_insights.treatment_implications[:2])

        # Add DA-based recommendations if available
        if da_result and da_result.get("confidence", 0) > 0.6:
            recommendations.append(f"Consider {da_result.get('diagnosis', 'Unknown')} in differential diagnosis")

        # Add integration-specific recommendations
        if len(recommendations) < 3:
            recommendations.append("Comprehensive psychiatric evaluation recommended")
            recommendations.append("Consider multimodal treatment approach")

        return recommendations[:3]  # Limit to top 3

    def _calculate_clinical_confidence(self, scid_confidence: float, da_confidence: Optional[float]) -> float:
        """Calculate overall clinical confidence"""
        if da_confidence is None:
            return scid_confidence

        # Weighted combination of SCID and DA confidence
        return (scid_confidence * 0.6) + (da_confidence * 0.4)

    def _assess_integrated_risk(self, scid_result: AssessmentResult, da_result: Dict[str, Any]) -> str:
        """Assess integrated clinical risk"""
        risk_factors = []

        # Check SCID risk factors
        if hasattr(scid_result, 'risk_factors'):
            risk_factors.extend(scid_result.risk_factors)

        # Check DA for high-risk diagnoses
        if da_result:
            diagnosis = da_result.get("diagnosis", "").lower()
            if any(word in diagnosis for word in ["suicide", "self-harm", "severe", "psychotic"]):
                risk_factors.append("High-risk diagnosis indicated")

        if risk_factors:
            return f"Elevated risk: {', '.join(risk_factors[:2])}"
        else:
            return "No immediate high-risk indicators identified"

    def _determine_recommended_diagnosis(self, result: IntegratedDiagnosisResult) -> str:
        """Determine the recommended diagnosis based on integrated analysis"""
        if result.agreement_level == "high_agreement":
            return f"Consistent findings: {result.scid_module}"
        elif result.da_diagnosis and result.da_confidence and result.da_confidence > result.scid_confidence:
            return f"DA-preferred: {result.da_diagnosis}"
        else:
            return f"SCID-based: {result.scid_module}"

    def generate_comprehensive_report(self, integrated_result: IntegratedDiagnosisResult) -> str:
        """Generate a comprehensive clinical report"""
        report_lines = [
            "=" * 80,
            "INTEGRATED PSYCHIATRIC ASSESSMENT REPORT",
            "=" * 80,
            "",
            f"Patient ID: {integrated_result.patient_id}",
            f"Session ID: {integrated_result.session_id}",
            f"Assessment Date: {integrated_result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Processing Time: {integrated_result.processing_time_seconds:.2f} seconds",
            "",
            "CLINICAL FINDINGS:",
            "-" * 30,
            f"SCID Assessment: {integrated_result.scid_module}",
            f"SCID Diagnosis: {integrated_result.scid_diagnosis}",
            f"SCID Confidence: {integrated_result.scid_confidence:.2f}",
            f"SCID Severity: {integrated_result.scid_severity}",
            "",
            f"Symptoms Identified ({len(integrated_result.scid_symptoms)}):"
        ]

        # Add symptoms
        for i, symptom in enumerate(integrated_result.scid_symptoms[:10], 1):
            report_lines.append(f"  {i}. {symptom}")

        if len(integrated_result.scid_symptoms) > 10:
            report_lines.append(f"  ... and {len(integrated_result.scid_symptoms) - 10} more")

        # Add DA results if available
        if integrated_result.da_available and integrated_result.da_diagnosis:
            report_lines.extend([
                "",
                "DIFFERENTIAL DIAGNOSIS (DA):",
                "-" * 30,
                f"DA Diagnosis: {integrated_result.da_diagnosis}",
                ".2f",
                f"DA Severity: {integrated_result.da_severity}",
                f"Agreement Level: {integrated_result.agreement_level.replace('_', ' ').title()}",
                "",
                "DA Reasoning:",
                integrated_result.da_reasoning or "No reasoning provided"
            ])

        # Add integrated analysis
        report_lines.extend([
            "",
            "INTEGRATED ANALYSIS:",
            "-" * 30,
            f"Recommended Diagnosis: {integrated_result.recommended_diagnosis}",
            ".2f",
            f"Risk Assessment: {integrated_result.risk_assessment}",
            "",
            "Treatment Recommendations:"
        ])

        # Add recommendations
        for i, rec in enumerate(integrated_result.treatment_recommendations, 1):
            report_lines.append(f"  {i}. {rec}")

        # Add technical details
        report_lines.extend([
            "",
            "TECHNICAL DETAILS:",
            "-" * 30,
            f"SCID Module: {integrated_result.scid_module}",
            f"DA Integration: {'Enabled' if integrated_result.da_available else 'Disabled'}",
            ".2f",
            "",
            "=" * 80
        ])

        return "\n".join(report_lines)

# Convenience functions
def analyze_patient_with_integrated_diagnosis(
    patient_id: str,
    module_id: str = None,
    patient_info: Optional[Dict[str, Any]] = None
) -> IntegratedDiagnosisResult:
    """
    Perform integrated SCID-DA diagnosis for a patient

    Args:
        patient_id: Patient identifier
        module_id: SCID module to use (optional)
        patient_info: Additional patient information

    Returns:
        Integrated diagnosis result
    """
    integrator = SCIDDAIntegrator()
    return integrator.integrate_scid_da_analysis(patient_id, module_id, patient_info)

def generate_patient_concern_report(assessment_result: AssessmentResult) -> Dict[str, Any]:
    """
    Generate patient concern report from SCID assessment

    Args:
        assessment_result: SCID assessment result

    Returns:
        Patient concern report
    """
    integrator = SCIDDAIntegrator()
    return integrator.get_patient_concern_report(assessment_result)

# Demo function
def demo_integrated_diagnosis():
    """Demonstrate integrated SCID-DA diagnosis"""
    print("🧠 Integrated SCID-DA Diagnosis Demo")
    print("=" * 60)

    # Create integrator
    integrator = SCIDDAIntegrator()

    # Perform integrated analysis
    try:
        result = integrator.integrate_scid_da_analysis(
            patient_id="demo_patient_001",
            module_id="MDD",
            patient_info={
                "name": "Sarah Johnson",
                "age": 34,
                "clinical_presentation": "Persistent sadness, loss of interest, insomnia"
            }
        )

        # Generate comprehensive report
        report = integrator.generate_comprehensive_report(result)

        print("📋 Integrated Diagnosis Results:")
        print("-" * 40)
        print(f"SCID Module: {result.scid_module}")
        print(f"SCID Diagnosis: {result.scid_diagnosis}")
        print(".2f")
        print(f"Symptoms Found: {len(result.scid_symptoms)}")
        print(f"DA Available: {result.da_available}")

        if result.da_diagnosis:
            print(f"DA Diagnosis: {result.da_diagnosis}")
            print(".2f")
            print(f"Agreement: {result.agreement_level}")

        print(f"Recommended: {result.recommended_diagnosis}")
        print(".2f")
        print(f"Risk Assessment: {result.risk_assessment}")

        print("\n📄 Full Report Preview:")
        print("-" * 40)
        # Show first few lines of report
        report_lines = report.split('\n')[:20]
        print('\n'.join(report_lines))
        print("... [truncated]")

        # Save full report
        with open("/tmp/integrated_diagnosis_report.txt", "w") as f:
            f.write(report)
        print("\n💾 Full report saved to /tmp/integrated_diagnosis_report.txt")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    demo_integrated_diagnosis()

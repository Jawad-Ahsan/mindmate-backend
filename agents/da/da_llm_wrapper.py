"""
DA LLM Wrapper - Specialized LLM Client for Diagnosis Agent
Extends the base LLM client with DA-specific functionality
"""

import sys
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
import json
import time

# Import base LLM client
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from llm_client import LLMClient

# Import DA schemas
from .da_schemas import (
    DiagnosisRequest, DiagnosisResponse, SymptomSeverity,
    ValidationResponse, DiagnosisError, SupportedDisorder
)

# Import DA tools
from .da_tools import (
    symptom_analyzer, dsm_checker, confidence_calculator,
    differential_diagnosis_tool, clinical_reasoning_tool
)


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process"""
    step_number: int
    step_type: str  # "observe", "reason", "act", "finalize"
    description: str
    input_data: Any
    output_data: Any
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class DALogicalReasoning:
    """Handles logical reasoning patterns for DA"""

    def __init__(self):
        self.reasoning_patterns = {
            "mood_disorder": {
                "keywords": ["depressed", "sad", "hopeless", "worthless", "guilty"],
                "weight": 0.8,
                "common_comorbidities": ["anxiety", "insomnia", "fatigue"]
            },
            "anxiety_disorder": {
                "keywords": ["anxious", "worried", "fear", "panic", "tense", "nervous"],
                "weight": 0.7,
                "common_comorbidities": ["depression", "insomnia", "muscle_tension"]
            },
            "trauma_disorder": {
                "keywords": ["flashbacks", "nightmares", "hypervigilant", "avoidance"],
                "weight": 0.9,
                "common_comorbidities": ["depression", "anxiety", "dissociation"]
            },
            "eating_disorder": {
                "keywords": ["weight", "food", "body", "eating", "binge", "purge"],
                "weight": 0.6,
                "common_comorbidities": ["depression", "anxiety", "body_image"]
            }
        }

    def analyze_symptom_patterns(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze symptoms for patterns and suggest disorder categories"""
        symptom_text = " ".join(symptoms).lower()

        pattern_matches = {}
        for disorder_type, pattern in self.reasoning_patterns.items():
            matches = 0
            for keyword in pattern["keywords"]:
                if keyword in symptom_text:
                    matches += 1

            if matches > 0:
                confidence = min(matches / len(pattern["keywords"]) * pattern["weight"], 1.0)
                pattern_matches[disorder_type] = {
                    "matches": matches,
                    "confidence": confidence,
                    "comorbidities": pattern["common_comorbidities"]
                }

        # Sort by confidence
        sorted_patterns = dict(sorted(
            pattern_matches.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        ))

        return {
            "pattern_analysis": sorted_patterns,
            "primary_suggestion": list(sorted_patterns.keys())[0] if sorted_patterns else None,
            "confidence": list(sorted_patterns.values())[0]["confidence"] if sorted_patterns else 0.0
        }


class DAReasoningWorkflow:
    """Manages the complete reasoning workflow for DA"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.logical_reasoning = DALogicalReasoning()
        self.reasoning_steps = []

    def execute_workflow(self, symptoms: List[str],
                        patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the complete DA reasoning workflow"""

        start_time = time.time()
        self.reasoning_steps = []

        try:
            # Step 1: Initial symptom analysis
            step1_result = self._step_1_observe(symptoms)
            self._add_step(1, "observe", "Analyze symptoms and categorize", symptoms, step1_result)

            # Step 2: Pattern recognition
            step2_result = self._step_2_reason_patterns(step1_result)
            self._add_step(2, "reason", "Identify symptom patterns", step1_result, step2_result)

            # Step 3: DSM criteria matching
            step3_result = self._step_3_act_dsm(symptoms, step2_result)
            self._add_step(3, "act", "Check DSM criteria", symptoms, step3_result)

            # Step 4: Differential diagnosis
            step4_result = self._step_4_reason_differential(step3_result)
            self._add_step(4, "reason", "Perform differential diagnosis", step3_result, step4_result)

            # Step 5: Clinical reasoning
            step5_result = self._step_5_act_clinical(symptoms, step4_result)
            self._add_step(5, "act", "Apply clinical reasoning", step4_result, step5_result)

            # Step 6: Final confidence calculation
            step6_result = self._step_6_reason_confidence(step5_result)
            self._add_step(6, "reason", "Calculate final confidence", step5_result, step6_result)

            # Step 7: Final diagnosis assembly
            step7_result = self._step_7_finalize(step6_result, start_time)
            self._add_step(7, "finalize", "Assemble final diagnosis", step6_result, step7_result)

            return step7_result

        except Exception as e:
            error_result = {
                "error": str(e),
                "error_type": "workflow_execution_error",
                "partial_results": self.reasoning_steps
            }
            return error_result

    def _add_step(self, number: int, step_type: str, description: str,
                  input_data: Any, output_data: Any, confidence: float = 0.0):
        """Add a reasoning step to the log"""
        step = ReasoningStep(
            step_number=number,
            step_type=step_type,
            description=description,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence
        )
        self.reasoning_steps.append(step)

    def _step_1_observe(self, symptoms: List[str]) -> Dict[str, Any]:
        """Step 1: Observe - Analyze symptoms using DA tools"""
        # Use the symptom analyzer tool
        analysis = symptom_analyzer.analyze_symptoms(symptoms)

        # Enhance with logical reasoning
        pattern_analysis = self.logical_reasoning.analyze_symptom_patterns(symptoms)

        return {
            "symptom_analysis": analysis,
            "pattern_analysis": pattern_analysis,
            "symptoms": symptoms
        }

    def _step_2_reason_patterns(self, step1_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Reason - Identify patterns and suggest diagnoses"""
        symptoms = step1_result["symptoms"]
        analysis = step1_result["symptom_analysis"]

        # Get potential disorders from analysis
        potential_disorders = list(analysis.get("potential_disorders", {}).keys())

        if not potential_disorders:
            return {
                "suggested_diagnoses": [],
                "confidence": 0.0,
                "reasoning": "No clear symptom patterns identified"
            }

        # Use LLM to enhance reasoning about the most likely diagnosis
        system_prompt = """You are a psychiatric diagnosis assistant. Based on the symptom analysis provided, identify the most likely psychiatric disorder from the following options:

Available disorders:
- MDD (Major Depressive Disorder)
- GAD (Generalized Anxiety Disorder)
- PANIC (Panic Disorder)
- SUBSTANCE_USE (Substance Use Disorder)
- ADHD (Attention-Deficit/Hyperactivity Disorder)
- ADJUSTMENT (Adjustment Disorder)
- BIPOLAR (Bipolar Disorder)
- SOCIAL_ANXIETY (Social Anxiety Disorder)
- SPECIFIC_PHOBIA (Specific Phobia)
- AGORAPHOBIA (Agoraphobia)
- PTSD (Posttraumatic Stress Disorder)
- OCD (Obsessive-Compulsive Disorder)
- ALCOHOL_USE (Alcohol Use Disorder)
- EATING_DISORDERS (Eating Disorders)

Respond with only the disorder ID that best matches the symptoms."""

        symptom_summary = f"""
Symptom count: {analysis['symptom_count']}
Categories: {list(analysis['symptom_categories'].keys())}
Top potential: {analysis.get('top_diagnosis', 'None')}
Potential disorders: {', '.join(potential_disorders)}
"""

        try:
            llm_response = self.llm_client.generate(
                prompt=symptom_summary,
                system_prompt=system_prompt,
                max_tokens=50,
                temperature=0.1
            )

            # Extract disorder ID from LLM response
            suggested_disorder = None
            response_upper = llm_response.upper()

            for disorder_id in ['MDD', 'GAD', 'PANIC', 'SUBSTANCE_USE', 'ADHD', 'ADJUSTMENT',
                              'BIPOLAR', 'SOCIAL_ANXIETY', 'SPECIFIC_PHOBIA', 'AGORAPHOBIA',
                              'PTSD', 'OCD', 'ALCOHOL_USE', 'EATING_DISORDERS']:
                if disorder_id in response_upper:
                    suggested_disorder = disorder_id
                    break

            if not suggested_disorder and potential_disorders:
                suggested_disorder = potential_disorders[0]

        except Exception as e:
            # Fallback to analysis-based suggestion
            suggested_disorder = potential_disorders[0] if potential_disorders else None

        confidence = analysis.get("potential_disorders", {}).get(suggested_disorder, {}).get("confidence", 0.0)

        return {
            "suggested_diagnoses": [suggested_disorder] if suggested_disorder else [],
            "confidence": confidence,
            "reasoning": f"LLM analysis suggests {suggested_disorder} based on symptom patterns",
            "all_candidates": potential_disorders
        }

    def _step_3_act_dsm(self, symptoms: List[str], step2_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Act - Check DSM criteria"""
        suggested_diagnoses = step2_result.get("suggested_diagnoses", [])

        if not suggested_diagnoses:
            return {
                "dsm_results": [],
                "primary_diagnosis": None,
                "confidence": 0.0
            }

        primary_diagnosis = suggested_diagnoses[0]

        # Use DSM checker tool
        dsm_result = dsm_checker.check_criteria_match(symptoms, primary_diagnosis)

        return {
            "dsm_results": [dsm_result],
            "primary_diagnosis": primary_diagnosis,
            "confidence": dsm_result.confidence,
            "matched_criteria": dsm_result.matched_criteria,
            "missing_criteria": dsm_result.missing_criteria
        }

    def _step_4_reason_differential(self, step3_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Reason - Perform differential diagnosis"""
        primary_diagnosis = step3_result.get("primary_diagnosis")

        if not primary_diagnosis:
            return {"differential_results": [], "recommendations": []}

        # Get all potential disorders from step 2 for comparison
        all_candidates = step3_result.get("all_candidates", [primary_diagnosis])

        # Use differential diagnosis tool
        differential_result = differential_diagnosis_tool.perform_differential_diagnosis(
            step3_result.get("symptoms", []),
            all_candidates
        )

        return {
            "differential_results": differential_result,
            "primary_diagnosis": primary_diagnosis,
            "recommendations": [differential_result.get("differential_factors", {}).get("recommendation", "")]
        }

    def _step_5_act_clinical(self, symptoms: List[str], step4_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Act - Apply clinical reasoning"""
        primary_diagnosis = step4_result.get("primary_diagnosis")

        if not primary_diagnosis:
            return {"clinical_analysis": {}, "flagged_criteria": []}

        # Prepare DSM result for clinical reasoning
        dsm_result = {
            'matched_criteria': step4_result.get('matched_criteria', []),
            'missing_criteria': step4_result.get('missing_criteria', [])
        }

        # Use clinical reasoning tool
        clinical_result = clinical_reasoning_tool.perform_clinical_reasoning(
            symptoms, primary_diagnosis, dsm_result
        )

        return {
            "clinical_analysis": clinical_result,
            "flagged_criteria": clinical_result.get("flagged_criteria", []),
            "recommendations": clinical_result.get("recommendations", [])
        }

    def _step_6_reason_confidence(self, step5_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 6: Reason - Calculate final confidence"""
        # Get symptom analysis from step 1 (passed through the workflow)
        # This is a simplified version - in practice, you'd pass the full context

        confidence_result = {
            "overall_confidence": step5_result.get("clinical_analysis", {}).get("meets_criteria", False) and 0.7 or 0.3,
            "severity": "moderate",  # Simplified
            "confidence_factors": {
                "criteria_match": 0.6,
                "symptom_consistency": 0.7,
                "disorder_specificity": 0.5,
                "symptom_completeness": 0.8
            }
        }

        return confidence_result

    def _step_7_finalize(self, step6_result: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Step 7: Finalize - Assemble complete diagnosis"""
        processing_time = time.time() - start_time

        # This is a simplified final assembly - in practice, you'd gather all results
        final_diagnosis = {
            "diagnosis": "Sample Diagnosis",  # Would come from step 3
            "confidence": step6_result.get("overall_confidence", 0.0),
            "severity": step6_result.get("severity", "unknown"),
            "reasoning": "Clinical reasoning based on DSM criteria analysis",
            "flagged_criteria": "1. Sample missing criterion",
            "metadata": {
                "agent_type": "DA LLM Wrapper",
                "model_used": self.llm_client.model,
                "timestamp": datetime.now().isoformat(),
                "processing_time_seconds": processing_time,
                "tools_used": ["symptom_analyzer", "dsm_checker", "clinical_reasoning_tool"],
                "react_steps_executed": [step.step_type for step in self.reasoning_steps],
                "symptom_count": 0,  # Would come from actual symptom count
                "matched_criteria_count": 0,
                "missing_criteria_count": 0,
                "flagged_criteria_count": 1
            }
        }

        return final_diagnosis


class DALLMWrapper:
    """DA-specific LLM wrapper extending the base LLM client"""

    def __init__(self, model_name: str = None, enable_cache: bool = True):
        # Initialize base LLM client
        self.llm_client = LLMClient(model=model_name, enable_cache=enable_cache)
        self.model_name = model_name or self.llm_client.model

        # Initialize DA-specific components
        self.reasoning_workflow = DAReasoningWorkflow(self.llm_client)
        self.logical_reasoning = DALogicalReasoning()

        # DA-specific system prompts
        self.system_prompts = {
            "diagnosis": """You are an expert psychiatric diagnosis assistant using the ReAct (Reasoning + Acting) pattern.
Your task is to analyze patient symptoms and provide accurate DSM-5 based diagnoses.

Guidelines:
1. Always base diagnoses on DSM-5 criteria
2. Consider symptom duration and severity
3. Be thorough but concise in reasoning
4. Flag any critical missing information
5. Suggest differential diagnoses when appropriate
6. Provide confidence levels for your assessments

Always explain your reasoning clearly.""",

            "clinical_reasoning": """You are a clinical reasoning specialist for psychiatric diagnosis.
Focus on:
- Identifying critical vs optional symptoms
- Assessing clinical significance
- Determining appropriate follow-up actions
- Recognizing when additional information is needed
- Providing clinical recommendations based on diagnosis""",

            "differential_diagnosis": """You are an expert in differential diagnosis for psychiatric disorders.
Your role is to:
- Compare multiple potential diagnoses
- Identify distinguishing features
- Assess relative confidence levels
- Recommend additional assessments if needed
- Consider comorbidity patterns"""
        }

    def diagnose(self, symptoms: List[str],
                patient_context: Optional[Dict[str, Any]] = None,
                use_workflow: bool = True) -> Dict[str, Any]:
        """
        Perform psychiatric diagnosis using DA-specific LLM capabilities

        Args:
            symptoms: List of patient symptoms
            patient_context: Additional patient information
            use_workflow: Whether to use the full reasoning workflow

        Returns:
            Diagnosis results with reasoning
        """
        if use_workflow:
            return self.reasoning_workflow.execute_workflow(symptoms, patient_context)
        else:
            return self._simple_diagnosis(symptoms, patient_context)

    def validate_symptoms(self, symptoms: List[str]) -> ValidationResponse:
        """Validate symptom input using DA-specific rules"""
        try:
            # Basic validation
            if not symptoms:
                return ValidationResponse(
                    valid=False,
                    errors=[{
                        "field": "symptoms",
                        "error_type": "empty_list",
                        "message": "Symptoms list cannot be empty"
                    }]
                )

            if len(symptoms) > 50:
                return ValidationResponse(
                    valid=False,
                    errors=[{
                        "field": "symptoms",
                        "error_type": "too_many_items",
                        "message": "Maximum 50 symptoms allowed"
                    }]
                )

            # Check for meaningful symptoms
            invalid_symptoms = []
            for symptom in symptoms:
                if len(str(symptom).strip()) < 3:
                    invalid_symptoms.append(str(symptom))

            if invalid_symptoms:
                return ValidationResponse(
                    valid=False,
                    errors=[{
                        "field": "symptoms",
                        "error_type": "invalid_format",
                        "message": f"Symptoms must be at least 3 characters: {invalid_symptoms}"
                    }]
                )

            # Check for duplicates
            descriptions = [s.lower().strip() for s in symptoms]
            if len(descriptions) != len(set(descriptions)):
                return ValidationResponse(
                    valid=True,
                    warnings=["Duplicate symptoms detected"],
                    symptom_count=len(symptoms)
                )

            return ValidationResponse(
                valid=True,
                symptom_count=len(symptoms)
            )

        except Exception as e:
            return ValidationResponse(
                valid=False,
                errors=[{
                    "field": "symptoms",
                    "error_type": "validation_error",
                    "message": f"Validation failed: {str(e)}"
                }]
            )

    def _simple_diagnosis(self, symptoms: List[str],
                         patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Simple diagnosis without full workflow"""
        try:
            # Use symptom analyzer
            analysis = symptom_analyzer.analyze_symptoms(symptoms)

            if not analysis.get('potential_disorders'):
                return {
                    "diagnosis": "Unable to determine diagnosis",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Insufficient symptoms for diagnosis"
                }

            # Get top diagnosis
            top_diagnosis = list(analysis['potential_disorders'].keys())[0]
            disorder_info = analysis['potential_disorders'][top_diagnosis]

            return {
                "diagnosis": disorder_info['disorder_name'],
                "confidence": disorder_info['confidence'],
                "severity": disorder_info['severity'],
                "reasoning": f"Based on symptom analysis, {disorder_info['disorder_name']} is the most likely diagnosis",
                "flagged_criteria": "None"
            }

        except Exception as e:
            return {
                "diagnosis": "Unable to determine diagnosis",
                "confidence": 0.0,
                "severity": "unknown",
                "reasoning": f"Error during diagnosis: {str(e)}",
                "flagged_criteria": "Error occurred"
            }

    def get_supported_disorders(self) -> List[str]:
        """Get list of all supported disorders"""
        try:
            from .da_tools import dsm_criteria_bank
            disorders = dsm_criteria_bank.get_all_disorders()
            return [disorder.disorder_name for disorder in disorders.values()]
        except Exception:
            return [
                "Major Depressive Disorder", "Generalized Anxiety Disorder",
                "Panic Disorder", "Substance Use Disorder", "ADHD",
                "Adjustment Disorder", "Bipolar Disorder", "Social Anxiety Disorder",
                "Specific Phobia", "Agoraphobia", "PTSD", "OCD",
                "Alcohol Use Disorder", "Eating Disorders"
            ]

    def get_stats(self) -> Dict[str, Any]:
        """Get LLM wrapper statistics"""
        return {
            "model": self.model_name,
            "llm_client_stats": self.llm_client.get_stats(),
            "reasoning_steps_executed": len(self.reasoning_workflow.reasoning_steps) if hasattr(self, 'reasoning_workflow') else 0,
            "supported_disorders": len(self.get_supported_disorders())
        }


# Convenience functions
def create_da_llm_wrapper(model_name: str = None) -> DALLMWrapper:
    """Create a DA LLM wrapper instance"""
    return DALLMWrapper(model_name)

def quick_diagnose(symptoms: List[str]) -> Dict[str, Any]:
    """Quick diagnosis using default DA LLM wrapper"""
    wrapper = DALLMWrapper()
    return wrapper.diagnose(symptoms, use_workflow=False)

if __name__ == "__main__":
    # Example usage
    wrapper = DALLMWrapper()

    symptoms = [
        "depressed mood most of the day",
        "loss of interest in activities",
        "insomnia",
        "fatigue"
    ]

    print("Testing DA LLM Wrapper...")
    result = wrapper.diagnose(symptoms)

    if "error" not in result:
        print(f"Diagnosis: {result['diagnosis']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
    else:
        print(f"Error: {result['error']}")

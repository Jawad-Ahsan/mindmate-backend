# scid_cv/utils.py
"""
Utility functions for SCID-CV administration and scoring
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_types import (
    SCIDModule, SCIDQuestion, SCIDResponse, ModuleResult, 
    SymptomExtraction, ResponseType, Severity
)

class SCIDAdministrator:
    """Utility class for administering SCID-CV modules"""
    
    def __init__(self):
        self.administration_history = []
    
    def administer_module(self, module: SCIDModule, responses: Dict[str, Any]) -> ModuleResult:
        """
        Administer a single SCID-CV module with given responses
        
        Args:
            module: SCIDModule to administer
            responses: Dict mapping question_id to response
            
        Returns:
            ModuleResult with scoring and analysis
        """
        start_time = datetime.now()
        
        # Validate responses
        validation_errors = module.validate_responses(responses)
        if validation_errors:
            raise ValueError(f"Response validation failed: {validation_errors}")
        
        # Convert responses to SCIDResponse objects
        scid_responses = []
        for question_id, response_value in responses.items():
            if isinstance(response_value, SCIDResponse):
                scid_responses.append(response_value)
            else:
                scid_responses.append(SCIDResponse(
                    question_id=question_id,
                    response=response_value,
                    timestamp=start_time
                ))
        
        # Calculate scores
        total_score, max_score, raw_scores = self._calculate_scores(module, responses)
        percentage_score = (total_score / max_score) if max_score > 0 else 0
        
        # Determine if diagnostic criteria are met
        criteria_met = percentage_score >= module.diagnostic_threshold
        
        # Extract symptoms
        symptoms_present = self._extract_symptoms(module, responses, scid_responses)
        
        # Determine severity level
        severity_level = self._determine_severity(module, percentage_score, symptoms_present)
        
        # Calculate administration time (simulated for now)
        admin_time_mins = max(1, int(len(responses) * 0.5))  # Rough estimate
        
        result = ModuleResult(
            module_id=module.id,
            module_name=module.name,
            total_score=total_score,
            max_possible_score=max_score,
            percentage_score=percentage_score,
            criteria_met=criteria_met,
            severity_level=severity_level,
            symptoms_present=symptoms_present,
            responses=scid_responses,
            administration_time_mins=admin_time_mins,
            completion_date=datetime.now(),
            raw_scores=raw_scores
        )
        
        self.administration_history.append(result)
        return result
    
    def administer_multiple_modules(
        self, 
        modules: List[SCIDModule], 
        responses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, ModuleResult]:
        """
        Administer multiple SCID-CV modules
        
        Args:
            modules: List of SCIDModule objects to administer
            responses: Dict mapping module_id to response dict
            
        Returns:
            Dict mapping module_id to ModuleResult
        """
        results = {}
        
        for module in modules:
            module_responses = responses.get(module.id, {})
            if module_responses:
                try:
                    results[module.id] = self.administer_module(module, module_responses)
                except Exception as e:
                    print(f"Error administering module {module.id}: {e}")
                    continue
        
        return results
    
    def _calculate_scores(self, module: SCIDModule, responses: Dict[str, Any]) -> tuple[float, float, Dict[str, float]]:
        """Calculate raw and weighted scores for a module"""
        total_score = 0.0
        max_possible_score = 0.0
        raw_scores = {}
        
        for question in module.questions:
            max_possible_score += question.criteria_weight
            
            if question.id in responses:
                response = responses[question.id]
                question_score = self._score_response(question, response)
                weighted_score = question_score * question.criteria_weight
                
                total_score += weighted_score
                raw_scores[question.id] = question_score
            else:
                raw_scores[question.id] = 0.0
        
        return total_score, max_possible_score, raw_scores
    
    def _score_response(self, question: SCIDQuestion, response: Any) -> float:
        """Score an individual response (0.0 to 1.0)"""
        if question.response_type == ResponseType.YES_NO:
            yes_responses = [True, "yes", "Yes", "YES", 1]
            return 1.0 if response in yes_responses else 0.0
        
        elif question.response_type == ResponseType.SCALE:
            try:
                val = float(response)
                max_val = question.scale_range[1]
                min_val = question.scale_range[0]
                # Normalize to 0-1 scale
                if max_val > min_val:
                    return (val - min_val) / (max_val - min_val)
                return 0.0
            except (ValueError, TypeError):
                return 0.0
        
        elif question.response_type == ResponseType.MULTIPLE_CHOICE:
            if not question.options:
                return 0.0
            
            # Define "no symptom" responses that should score 0
            no_symptom_patterns = [
                "no", "normal", "none", "never", "not at all", 
                "no significant", "no change", "no problem"
            ]
            
            if isinstance(response, str):
                response_lower = response.lower()
                # Check if it's a "no symptom" response
                if any(pattern in response_lower for pattern in no_symptom_patterns):
                    return 0.0
                # Otherwise, if it's a valid option, it indicates some level of symptom
                return 1.0 if response in question.options else 0.0
            
            elif isinstance(response, list):
                # Multiple selections - score based on number selected
                valid_responses = [r for r in response if r in question.options]
                non_symptom_responses = [
                    r for r in valid_responses 
                    if any(pattern in r.lower() for pattern in no_symptom_patterns)
                ]
                symptom_responses = [
                    r for r in valid_responses 
                    if not any(pattern in r.lower() for pattern in no_symptom_patterns)
                ]
                
                # If only non-symptom responses selected, score 0
                if symptom_responses:
                    return min(1.0, len(symptom_responses) / max(1, len(question.options) - 1))
                return 0.0
            
            return 0.0
        
        elif question.response_type == ResponseType.TEXT:
            # Text responses score 1.0 if non-empty, 0.0 if empty
            return 1.0 if response and str(response).strip() else 0.0
        
        elif question.response_type == ResponseType.DATE:
            # Date responses score 1.0 if valid date provided
            return 1.0 if response else 0.0
        
        return 0.0
    
    def _extract_symptoms(
        self, 
        module: SCIDModule, 
        responses: Dict[str, Any], 
        scid_responses: List[SCIDResponse]
    ) -> List[SymptomExtraction]:
        """Extract symptom information from responses"""
        symptoms = []
        
        # Group responses by symptom category
        response_by_question = {r.question_id: r for r in scid_responses}
        
        for question in module.questions:
            if question.id not in response_by_question:
                continue
            
            scid_response = response_by_question[question.id]
            question_score = self._score_response(question, scid_response.response)
            
            if question_score > 0:  # Only extract symptoms for positive responses
                symptom = self._create_symptom_extraction(
                    question, scid_response, question_score
                )
                if symptom:
                    symptoms.append(symptom)
        
        return symptoms
    
    def _create_symptom_extraction(
        self, 
        question: SCIDQuestion, 
        response: SCIDResponse, 
        score: float
    ) -> Optional[SymptomExtraction]:
        """Create a symptom extraction from a question and response"""
        # Clean up symptom name
        symptom_name = question.symptom_category.replace("_", " ").title()
        if not symptom_name or symptom_name.lower() in ["", "other", "misc"]:
            return None
        
        # Determine severity from score and response type
        severity = None
        if question.response_type == ResponseType.SCALE:
            if score >= 0.75:
                severity = Severity.SEVERE
            elif score >= 0.5:
                severity = Severity.MODERATE
            elif score > 0:
                severity = Severity.MILD
        elif score > 0.7:
            severity = Severity.MODERATE
        elif score > 0:
            severity = Severity.MILD
        
        # Extract frequency information
        frequency = None
        if "daily" in question.simple_text.lower() or "every day" in question.simple_text.lower():
            frequency = "daily"
        elif "week" in question.simple_text.lower():
            frequency = "weekly"
        elif "month" in question.simple_text.lower():
            frequency = "monthly"
        
        # Extract triggers from multiple choice responses
        triggers = []
        if (question.response_type == ResponseType.MULTIPLE_CHOICE and 
            isinstance(response.response, list)):
            triggers = response.response
        
        # Determine impact areas based on symptom category
        impact_areas = []
        if any(term in symptom_name.lower() for term in ["work", "school", "job"]):
            impact_areas.append("occupational")
        if any(term in symptom_name.lower() for term in ["social", "relationship", "family"]):
            impact_areas.append("interpersonal")
        if any(term in symptom_name.lower() for term in ["daily", "activities", "function"]):
            impact_areas.append("daily_functioning")
        
        return SymptomExtraction(
            symptom_name=symptom_name,
            present=True,
            severity=severity,
            frequency=frequency,
            triggers=triggers,
            impact_areas=impact_areas,
            confidence=score
        )
    
    def _determine_severity(
        self, 
        module: SCIDModule, 
        percentage_score: float, 
        symptoms: List[SymptomExtraction]
    ) -> Optional[Severity]:
        """Determine overall severity level for the module"""
        if not symptoms or percentage_score < module.diagnostic_threshold:
            return None
        
        # Use module-specific severity thresholds if available
        if module.severity_thresholds:
            for severity_name in ["extreme", "severe", "moderate", "mild"]:
                if (severity_name in module.severity_thresholds and 
                    percentage_score >= module.severity_thresholds[severity_name]):
                    return Severity(severity_name)
        
        # Default severity determination based on score and symptom severity
        severe_symptoms = sum(1 for s in symptoms if s.severity == Severity.SEVERE)
        moderate_symptoms = sum(1 for s in symptoms if s.severity == Severity.MODERATE)
        
        if percentage_score >= 0.8 or severe_symptoms >= 2:
            return Severity.SEVERE
        elif percentage_score >= 0.6 or moderate_symptoms >= 3 or severe_symptoms >= 1:
            return Severity.MODERATE
        elif percentage_score >= 0.4 or moderate_symptoms >= 1:
            return Severity.MILD
        
        return Severity.MILD
    
    def export_results_as_json(
        self, 
        results: List[ModuleResult], 
        include_raw_responses: bool = True,
        include_symptom_details: bool = True
    ) -> str:
        """
        Export results as JSON
        
        Args:
            results: List of ModuleResult objects to export
            include_raw_responses: Whether to include raw response data
            include_symptom_details: Whether to include detailed symptom information
            
        Returns:
            JSON string with results
        """
        export_data = {
            "scid_cv_export": {
                "version": "1.0",
                "export_timestamp": datetime.now().isoformat(),
                "total_modules": len(results),
                "modules_meeting_criteria": sum(1 for r in results if r.criteria_met),
                "overall_summary": self._generate_summary_stats(results)
            },
            "results": []
        }
        
        for result in results:
            result_data = {
                "module_id": result.module_id,
                "module_name": result.module_name,
                "completion_date": result.completion_date.isoformat(),
                "administration_time_mins": result.administration_time_mins,
                "scoring": {
                    "total_score": result.total_score,
                    "max_possible_score": result.max_possible_score,
                    "percentage_score": round(result.percentage_score * 100, 1),
                    "criteria_met": result.criteria_met,
                    "severity_level": result.severity_level.value if result.severity_level else None
                },
                "symptoms_count": len(result.symptoms_present),
                "notes": result.notes
            }
            
            if include_symptom_details:
                result_data["symptoms_present"] = [
                    {
                        "symptom_name": symptom.symptom_name,
                        "severity": symptom.severity.value if symptom.severity else None,
                        "frequency": symptom.frequency,
                        "triggers": symptom.triggers,
                        "impact_areas": symptom.impact_areas,
                        "confidence": round(symptom.confidence, 3)
                    }
                    for symptom in result.symptoms_present
                ]
            
            if include_raw_responses:
                result_data["responses"] = [
                    {
                        "question_id": response.question_id,
                        "response": response.response,
                        "timestamp": response.timestamp.isoformat(),
                        "notes": response.notes,
                        "confidence": response.confidence
                    }
                    for response in result.responses
                ]
                result_data["raw_scores"] = result.raw_scores
            
            export_data["results"].append(result_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _generate_summary_stats(self, results: List[ModuleResult]) -> Dict[str, Any]:
        """Generate summary statistics for a set of results"""
        if not results:
            return {}
        
        scores = [r.percentage_score for r in results]
        positive_results = [r for r in results if r.criteria_met]
        
        summary = {
            "average_score": round(np.mean(scores) * 100, 1),
            "score_range": {
                "min": round(min(scores) * 100, 1),
                "max": round(max(scores) * 100, 1)
            },
            "positive_modules": [r.module_name for r in positive_results],
            "total_symptoms_identified": sum(len(r.symptoms_present) for r in results),
            "most_severe_module": None,
            "total_administration_time": sum(r.administration_time_mins for r in results)
        }
        
        if positive_results:
            most_severe = max(positive_results, key=lambda x: x.percentage_score)
            summary["most_severe_module"] = {
                "name": most_severe.module_name,
                "score": round(most_severe.percentage_score * 100, 1),
                "severity": most_severe.severity_level.value if most_severe.severity_level else None
            }
        
        return summary
    
    def get_administration_history(self) -> List[ModuleResult]:
        """Get the history of all administered modules"""
        return self.administration_history.copy()
    
    def clear_history(self):
        """Clear the administration history"""
        self.administration_history.clear()
    
    def generate_summary_report(self, results: List[ModuleResult]) -> str:
        """Generate a human-readable summary report"""
        if not results:
            return "No results to summarize."
        
        summary = self._generate_summary_stats(results)
        positive_count = len(summary.get("positive_modules", []))
        
        report_lines = [
            "=" * 50,
            "SCID-CV ADMINISTRATION SUMMARY REPORT",
            "=" * 50,
            "",
            f"Assessment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Modules Administered: {len(results)}",
            f"Modules Meeting Diagnostic Criteria: {positive_count}",
            f"Average Score: {summary.get('average_score', 0)}%",
            f"Total Administration Time: {summary.get('total_administration_time', 0)} minutes",
            "",
            "MODULE RESULTS:",
            "-" * 20
        ]
        
        for result in sorted(results, key=lambda x: x.percentage_score, reverse=True):
            status = "POSITIVE" if result.criteria_met else "NEGATIVE"
            severity_str = f" ({result.severity_level.value})" if result.severity_level else ""
            
            report_lines.extend([
                f"{result.module_name}: {result.percentage_score*100:.1f}% [{status}]{severity_str}",
                f"  • Symptoms Present: {len(result.symptoms_present)}",
                f"  • Administration Time: {result.administration_time_mins} minutes",
                ""
            ])
        
        if positive_count > 0:
            report_lines.extend([
                "POSITIVE MODULES:",
                "-" * 15
            ])
            for module_name in summary.get("positive_modules", []):
                report_lines.append(f"• {module_name}")
        
        report_lines.extend([
            "",
            "=" * 50,
            "END OF REPORT",
            "=" * 50
        ])
        
        return "\n".join(report_lines)
# scid_pd/utils.py
"""
Utility functions for SCID-PD administration and scoring
Specialized for personality disorder assessment
"""

import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_types import (
    SCIDPDModule, SCIDPDQuestion, SCIDPDResponse, PersonalityModuleResult,
    PersonalityPatternExtraction, PersonalityProfile, ResponseType, 
    Severity, DSMCluster, PersonalityDimensionType, PervasivenessCriteria, OnsetCriteria
)

class SCIDPDAdministrator:
    """Utility class for administering SCID-PD modules"""
    
    def __init__(self):
        self.administration_history = []
        self.current_profile: Optional[PersonalityProfile] = None
    
    def start_personality_assessment(self) -> PersonalityProfile:
        """Start a new comprehensive personality assessment"""
        self.current_profile = PersonalityProfile()
        return self.current_profile
    
    def administer_module(self, module: SCIDPDModule, responses: Dict[str, Any]) -> PersonalityModuleResult:
        """
        Administer a single SCID-PD module with given responses
        
        Args:
            module: SCIDPDModule to administer
            responses: Dict mapping question_id to response
            
        Returns:
            PersonalityModuleResult with scoring and analysis
        """
        start_time = datetime.now()
        
        # Validate responses
        validation_errors = module.validate_responses(responses)
        if validation_errors:
            raise ValueError(f"Response validation failed: {validation_errors}")
        
        # Convert responses to SCIDPDResponse objects
        scid_responses = []
        for question_id, response_value in responses.items():
            if isinstance(response_value, SCIDPDResponse):
                scid_responses.append(response_value)
            else:
                # Handle complex response with onset age and examples
                if isinstance(response_value, dict):
                    scid_responses.append(SCIDPDResponse(
                        question_id=question_id,
                        response=response_value.get("response"),
                        onset_age=response_value.get("onset_age"),
                        examples_provided=response_value.get("examples", []),
                        notes=response_value.get("notes", ""),
                        timestamp=start_time
                    ))
                else:
                    scid_responses.append(SCIDPDResponse(
                        question_id=question_id,
                        response=response_value,
                        timestamp=start_time
                    ))
        
        # Calculate scores
        total_score, max_score, raw_scores = self._calculate_scores(module, responses)
        percentage_score = (total_score / max_score) if max_score > 0 else 0
        dimensional_score = self._calculate_dimensional_score(module, responses, percentage_score)
        
        # Determine if diagnostic criteria are met
        criteria_met = self._assess_diagnostic_criteria(module, percentage_score, responses)
        
        # Extract personality patterns
        patterns_present = self._extract_personality_patterns(module, responses, scid_responses)
        
        # Determine severity level
        severity_level = self._determine_severity(module, percentage_score, patterns_present)
        
        # Assess onset and pervasiveness
        onset_pattern = self._assess_onset_pattern(module, scid_responses)
        pervasiveness = self._assess_pervasiveness(module, responses, patterns_present)
        
        # Generate differential considerations
        differential_considerations = self._generate_differential_considerations(
            module, patterns_present, percentage_score
        )
        
        # Calculate administration time (estimated)
        admin_time_mins = max(5, int(len(responses) * 0.8))  # PD assessments take longer
        
        result = PersonalityModuleResult(
            module_id=module.id,
            module_name=module.name,
            dsm_cluster=module.dsm_cluster,
            total_score=total_score,
            max_possible_score=max_score,
            percentage_score=percentage_score,
            dimensional_score=dimensional_score,
            criteria_met=criteria_met,
            severity_level=severity_level,
            patterns_present=patterns_present,
            responses=scid_responses,
            administration_time_mins=admin_time_mins,
            completion_date=datetime.now(),
            raw_scores=raw_scores,
            onset_pattern=onset_pattern,
            pervasiveness_assessment=pervasiveness,
            differential_considerations=differential_considerations
        )
        
        self.administration_history.append(result)
        
        # Add to current profile if one is active
        if self.current_profile:
            self.current_profile.module_results.append(result)
            self._update_profile_summary(self.current_profile)
        
        return result
    
    def complete_personality_assessment(self) -> Optional[PersonalityProfile]:
        """Complete the current personality assessment and return the profile"""
        if not self.current_profile:
            return None
        
        self._finalize_profile(self.current_profile)
        completed_profile = self.current_profile
        self.current_profile = None
        return completed_profile
    
    def _calculate_scores(self, module: SCIDPDModule, responses: Dict[str, Any]) -> tuple[float, float, Dict[str, float]]:
        """Calculate raw and weighted scores for a personality disorder module"""
        total_score = 0.0
        max_possible_score = 0.0
        raw_scores = {}
        
        for question in module.questions:
            max_possible_score += question.criteria_weight
            
            if question.id in responses:
                response = responses[question.id]
                question_score = self._score_personality_response(question, response)
                weighted_score = question_score * question.criteria_weight
                
                total_score += weighted_score
                raw_scores[question.id] = question_score
            else:
                raw_scores[question.id] = 0.0
        
        return total_score, max_possible_score, raw_scores
    
    def _score_personality_response(self, question: SCIDPDQuestion, response: Any) -> float:
        """Score an individual personality disorder response (0.0 to 1.0)"""
        # Handle complex response objects
        if isinstance(response, dict):
            actual_response = response.get("response")
            has_examples = bool(response.get("examples", []))
            onset_age = response.get("onset_age")
        else:
            actual_response = response
            has_examples = False
            onset_age = None
        
        base_score = self._get_base_response_score(question, actual_response)
        
        # Adjust score based on personality-specific factors
        adjusted_score = base_score
        
        # Bonus for providing concrete examples when required
        if question.requires_examples and has_examples and base_score > 0:
            adjusted_score = min(1.0, base_score * 1.1)
        
        # Penalty for lack of examples when pattern is endorsed but no examples given
        if question.requires_examples and base_score > 0.5 and not has_examples:
            adjusted_score = base_score * 0.8
        
        # Onset considerations for personality disorders
        if question.onset_relevant and base_score > 0 and onset_age:
            if onset_age <= 18:  # Early onset is more consistent with personality disorders
                adjusted_score = min(1.0, base_score * 1.05)
            elif onset_age > 25:  # Late onset may suggest other conditions
                adjusted_score = base_score * 0.9
        
        return adjusted_score
    
    def _get_base_response_score(self, question: SCIDPDQuestion, response: Any) -> float:
        """Get base score for response without personality-specific adjustments"""
        if question.response_type == ResponseType.YES_NO:
            yes_responses = [True, "yes", "Yes", "YES", 1]
            return 1.0 if response in yes_responses else 0.0
        
        elif question.response_type == ResponseType.SCALE:
            try:
                val = float(response)
                max_val = question.scale_range[1]
                min_val = question.scale_range[0]
                if max_val > min_val:
                    return (val - min_val) / (max_val - min_val)
                return 0.0
            except (ValueError, TypeError):
                return 0.0
        
        elif question.response_type == ResponseType.FREQUENCY:
            # Frequency responses: never, rarely, sometimes, often, very often
            frequency_map = {
                "never": 0.0,
                "rarely": 0.2, 
                "sometimes": 0.4,
                "often": 0.7,
                "very often": 0.9,
                "always": 1.0
            }
            if isinstance(response, str):
                return frequency_map.get(response.lower(), 0.0)
            return 0.0
        
        elif question.response_type == ResponseType.MULTIPLE_CHOICE:
            if not question.options:
                return 0.0
            
            no_symptom_patterns = [
                "no", "never", "not at all", "none", "normal",
                "no problems", "no issues", "not applicable"
            ]
            
            if isinstance(response, str):
                response_lower = response.lower()
                if any(pattern in response_lower for pattern in no_symptom_patterns):
                    return 0.0
                return 1.0 if response in question.options else 0.0
            
            elif isinstance(response, list):
                valid_responses = [r for r in response if r in question.options]
                non_symptom_responses = [
                    r for r in valid_responses 
                    if any(pattern in r.lower() for pattern in no_symptom_patterns)
                ]
                symptom_responses = [
                    r for r in valid_responses 
                    if not any(pattern in r.lower() for pattern in no_symptom_patterns)
                ]
                
                if symptom_responses:
                    return min(1.0, len(symptom_responses) / max(1, len(question.options) - 1))
                return 0.0
        
        elif question.response_type == ResponseType.TEXT:
            return 1.0 if response and str(response).strip() else 0.0
        
        elif question.response_type in [ResponseType.DATE, ResponseType.ONSET_AGE]:
            return 1.0 if response else 0.0
        
        return 0.0
    
    def _calculate_dimensional_score(self, module: SCIDPDModule, responses: Dict[str, Any], percentage_score: float) -> float:
        """Calculate dimensional score (0-100) for personality disorder severity"""
        # Dimensional scoring considers not just presence/absence but degree of impairment
        base_dimensional = percentage_score * 100
        
        # Adjust based on pervasiveness and severity indicators
        severity_indicators = 0
        pervasiveness_indicators = 0
        
        for question in module.questions:
            if question.id not in responses:
                continue
            
            response = responses[question.id]
            
            # Check for severity indicators in responses
            if isinstance(response, dict):
                examples = response.get("examples", [])
                if len(examples) >= 2:  # Multiple examples indicate pervasiveness
                    pervasiveness_indicators += 1
                if any(word in " ".join(examples).lower() 
                      for word in ["severe", "extreme", "major", "significant"]):
                    severity_indicators += 1
            
            # Scale responses provide direct severity info
            if question.response_type == ResponseType.SCALE:
                try:
                    val = float(response)
                    max_val = question.scale_range[1]
                    if val >= max_val * 0.8:  # High scale responses
                        severity_indicators += 1
                except:
                    pass
        
        # Adjust dimensional score
        total_questions = len(module.questions)
        severity_adjustment = (severity_indicators / max(1, total_questions)) * 15
        pervasiveness_adjustment = (pervasiveness_indicators / max(1, total_questions)) * 10
        
        dimensional_score = min(100.0, base_dimensional + severity_adjustment + pervasiveness_adjustment)
        return round(dimensional_score, 1)
    
    def _assess_diagnostic_criteria(self, module: SCIDPDModule, percentage_score: float, responses: Dict[str, Any]) -> bool:
        """Assess if diagnostic criteria are met using both threshold and criteria count"""
        # Must meet percentage threshold
        if percentage_score < module.diagnostic_threshold:
            return False
        
        # Count number of individual criteria met
        criteria_count = 0
        for question in module.get_core_criteria_questions():
            if question.id in responses:
                score = self._score_personality_response(question, responses[question.id])
                if score >= 0.5:  # Criterion is met if score >= 0.5
                    criteria_count += 1
        
        # Must meet minimum criteria count (usually 5 for most personality disorders)
        return criteria_count >= module.minimum_criteria_count
    
    def _extract_personality_patterns(
        self, 
        module: SCIDPDModule, 
        responses: Dict[str, Any], 
        scid_responses: List[SCIDPDResponse]
    ) -> List[PersonalityPatternExtraction]:
        """Extract personality patterns from responses"""
        patterns = []
        response_by_question = {r.question_id: r for r in scid_responses}
        
        # Group questions by trait/pattern
        trait_questions = {}
        for question in module.questions:
            trait = question.trait_measured or question.dimension_type.value
            if trait not in trait_questions:
                trait_questions[trait] = []
            trait_questions[trait].append(question)
        
        # Extract patterns for each trait
        for trait, questions in trait_questions.items():
            pattern = self._extract_single_pattern(trait, questions, response_by_question, responses)
            if pattern and pattern.present:
                patterns.append(pattern)
        
        return patterns
    
    def _extract_single_pattern(
        self, 
        trait: str, 
        questions: List[SCIDPDQuestion], 
        response_by_question: Dict[str, SCIDPDResponse],
        all_responses: Dict[str, Any]
    ) -> Optional[PersonalityPatternExtraction]:
        """Extract a single personality pattern"""
        if not questions:
            return None
        
        # Calculate pattern strength
        total_score = 0.0
        max_score = 0.0
        examples = []
        contexts = []
        onset_ages = []
        
        for question in questions:
            if question.id not in response_by_question:
                continue
            
            scid_response = response_by_question[question.id]
            question_score = self._score_personality_response(question, all_responses[question.id])
            
            total_score += question_score * question.criteria_weight
            max_score += question.criteria_weight
            
            # Collect examples and context information
            if scid_response.examples_provided:
                examples.extend(scid_response.examples_provided)
            
            if scid_response.onset_age:
                onset_ages.append(scid_response.onset_age)
        
        if max_score == 0:
            return None
        
        pattern_strength = total_score / max_score
        
        # Only extract patterns that are present (strength > 0.3)
        if pattern_strength <= 0.3:
            return None
        
        # Determine severity
        severity = None
        if pattern_strength >= 0.8:
            severity = Severity.SEVERE
        elif pattern_strength >= 0.6:
            severity = Severity.MODERATE
        elif pattern_strength > 0.3:
            severity = Severity.MILD
        
        # Determine onset
        onset_period = None
        avg_onset_age = None
        if onset_ages:
            avg_onset_age = int(np.mean(onset_ages))
            if avg_onset_age < 12:
                onset_period = OnsetCriteria.CHILDHOOD
            elif avg_onset_age < 18:
                onset_period = OnsetCriteria.ADOLESCENCE
            elif avg_onset_age < 25:
                onset_period = OnsetCriteria.EARLY_ADULTHOOD
        
        # Determine dimension type from questions
        dimension_types = [q.dimension_type for q in questions]
        primary_dimension = max(set(dimension_types), key=dimension_types.count)
        
        return PersonalityPatternExtraction(
            pattern_name=trait.replace("_", " ").title(),
            present=True,
            severity=severity,
            dimension_type=primary_dimension,
            onset_period=onset_period,
            onset_age=avg_onset_age,
            behavioral_examples=examples[:5],  # Limit to top 5 examples
            contexts_affected=contexts,
            stability_over_time=True,  # Assume stable for personality patterns
            confidence=pattern_strength
        )
    
    def _assess_onset_pattern(self, module: SCIDPDModule, responses: List[SCIDPDResponse]) -> Optional[OnsetCriteria]:
        """Assess overall onset pattern for the personality disorder"""
        onset_ages = [r.onset_age for r in responses if r.onset_age is not None]
        
        if not onset_ages:
            return OnsetCriteria.UNKNOWN
        
        avg_onset = np.mean(onset_ages)
        
        if avg_onset < 12:
            return OnsetCriteria.CHILDHOOD
        elif avg_onset < 18:
            return OnsetCriteria.ADOLESCENCE
        elif avg_onset < 25:
            return OnsetCriteria.EARLY_ADULTHOOD
        else:
            return OnsetCriteria.UNKNOWN
    
    def _assess_pervasiveness(
        self, 
        module: SCIDPDModule, 
        responses: Dict[str, Any], 
        patterns: List[PersonalityPatternExtraction]
    ) -> Optional[PervasivenessCriteria]:
        """Assess how pervasive the personality patterns are across contexts"""
        if not patterns:
            return None
        
        # Count contexts mentioned across all patterns
        all_contexts = set()
        for pattern in patterns:
            all_contexts.update(pattern.contexts_affected)
        
        # Look for pervasiveness indicators in responses
        pervasiveness_count = 0
        total_relevant_questions = 0
        
        for question in module.questions:
            if not question.pervasiveness_check:
                continue
            
            total_relevant_questions += 1
            
            if question.id in responses:
                response = responses[question.id]
                
                # Check for pervasiveness keywords in text responses
                if isinstance(response, dict):
                    examples = response.get("examples", [])
                    example_text = " ".join(examples).lower()
                    
                    pervasiveness_indicators = [
                        "everywhere", "all situations", "always", "every relationship",
                        "work and home", "with everyone", "in all contexts"
                    ]
                    
                    if any(indicator in example_text for indicator in pervasiveness_indicators):
                        pervasiveness_count += 1
                
                # High scale scores suggest pervasiveness
                if question.response_type == ResponseType.SCALE:
                    try:
                        val = float(response)
                        max_val = question.scale_range[1]
                        if val >= max_val * 0.8:
                            pervasiveness_count += 1
                    except:
                        pass
        
        if total_relevant_questions == 0:
            return PervasivenessCriteria.MODERATE
        
        pervasiveness_ratio = pervasiveness_count / total_relevant_questions
        
        if pervasiveness_ratio >= 0.75:
            return PervasivenessCriteria.PERVASIVE
        elif pervasiveness_ratio >= 0.5:
            return PervasivenessCriteria.EXTENSIVE
        elif pervasiveness_ratio >= 0.25:
            return PervasivenessCriteria.MODERATE
        else:
            return PervasivenessCriteria.LIMITED
    
    def _determine_severity(
        self, 
        module: SCIDPDModule, 
        percentage_score: float, 
        patterns: List[PersonalityPatternExtraction]
    ) -> Optional[Severity]:
        """Determine overall severity level for the personality disorder"""
        if not patterns or percentage_score < module.diagnostic_threshold:
            return None
        
        # Use module-specific severity thresholds if available
        if module.severity_thresholds:
            for severity_name in ["extreme", "severe", "moderate", "mild"]:
                if (severity_name in module.severity_thresholds and 
                    percentage_score >= module.severity_thresholds[severity_name]):
                    return Severity(severity_name)
        
        # Count patterns by severity
        severe_patterns = sum(1 for p in patterns if p.severity == Severity.SEVERE)
        moderate_patterns = sum(1 for p in patterns if p.severity == Severity.MODERATE)
        
        # Determine overall severity
        if percentage_score >= 0.85 or severe_patterns >= 3:
            return Severity.SEVERE
        elif percentage_score >= 0.7 or severe_patterns >= 1 or moderate_patterns >= 3:
            return Severity.MODERATE
        elif percentage_score >= module.diagnostic_threshold:
            return Severity.MILD
        
        return Severity.MILD
    
    def _generate_differential_considerations(
        self, 
        module: SCIDPDModule, 
        patterns: List[PersonalityPatternExtraction], 
        percentage_score: float
    ) -> List[str]:
        """Generate differential diagnostic considerations"""
        considerations = []
        
        # Add module's predefined differential diagnoses
        considerations.extend(module.differential_diagnoses)
        
        # Add considerations based on patterns present
        pattern_names = [p.pattern_name.lower() for p in patterns]
        
        # Common differential considerations based on patterns
        if any("mood" in name or "emotional" in name for name in pattern_names):
            considerations.extend(["Major Depressive Disorder", "Bipolar Disorder"])
        
        if any("anxiety" in name or "fear" in name for name in pattern_names):
            considerations.extend(["Generalized Anxiety Disorder", "Social Anxiety Disorder"])
        
        if any("paranoid" in name or "suspicious" in name for name in pattern_names):
            considerations.extend(["Delusional Disorder", "Paranoid Personality Disorder"])
        
        # Remove duplicates and return
        return list(set(considerations))
    
    def _update_profile_summary(self, profile: PersonalityProfile):
        """Update the overall profile summary as modules are added"""
        if not profile.module_results:
            return
        
        # Update cluster summary
        profile.cluster_summary = {cluster: 0 for cluster in DSMCluster}
        for result in profile.module_results:
            if result.criteria_met:
                profile.cluster_summary[result.dsm_cluster] += 1
        
        # Update dimensional scores
        profile.dimensional_scores = {
            result.module_name: result.dimensional_score or 0.0 
            for result in profile.module_results
        }
        
        # Update primary diagnoses
        profile.primary_diagnoses = [
            result.module_name for result in profile.module_results 
            if result.criteria_met
        ]
        
        # Update total assessment time
        profile.total_assessment_time = sum(
            result.administration_time_mins for result in profile.module_results
        )
    
    def _finalize_profile(self, profile: PersonalityProfile):
        """Finalize the personality profile with overall assessments"""
        positive_results = profile.get_positive_diagnoses()
        
        if not positive_results:
            profile.overall_severity = None
            return
        
        # Determine overall severity
        severity_scores = {
            Severity.MILD: 1,
            Severity.MODERATE: 2, 
            Severity.SEVERE: 3,
            Severity.EXTREME: 4
        }
        
        max_severity_score = max(
            severity_scores.get(result.severity_level, 0) 
            for result in positive_results
        )
        
        for severity, score in severity_scores.items():
            if score == max_severity_score:
                profile.overall_severity = severity
                break
        
        # Generate recommendations
        profile.recommendations = self._generate_recommendations(profile)
    
    def _generate_recommendations(self, profile: PersonalityProfile) -> List[str]:
        """Generate clinical recommendations based on the personality profile"""
        recommendations = []
        positive_diagnoses = profile.get_positive_diagnoses()
        
        if not positive_diagnoses:
            recommendations.append("No personality disorder criteria met at this time")
            return recommendations
        
        # General recommendations
        recommendations.append("Consider comprehensive psychiatric evaluation")
        recommendations.append("Assess for comorbid Axis I disorders")
        
        # Cluster-specific recommendations
        cluster_dist = profile.get_cluster_distribution()
        
        if cluster_dist[DSMCluster.CLUSTER_A]:
            recommendations.append("Consider evaluation for thought disorder or psychotic symptoms")
            recommendations.append("Assess social functioning and support systems")
        
        if cluster_dist[DSMCluster.CLUSTER_B]:
            recommendations.append("Assess suicide risk and self-harm behaviors")
            recommendations.append("Consider dialectical behavior therapy (DBT) or similar interventions")
            recommendations.append("Evaluate impulse control and emotional regulation")
        
        if cluster_dist[DSMCluster.CLUSTER_C]:
            recommendations.append("Assess for anxiety disorders and depression")
            recommendations.append("Consider cognitive-behavioral therapy (CBT)")
        
        # Multiple personality disorders
        if len(positive_diagnoses) > 1:
            recommendations.append("Multiple personality disorder features present - consider complex case consultation")
            recommendations.append("Prioritize treatment targets based on functional impairment")
        
        # Severity-based recommendations
        severe_cases = [r for r in positive_diagnoses if r.severity_level == Severity.SEVERE]
        if severe_cases:
            recommendations.append("Severe personality pathology - consider intensive treatment approach")
            recommendations.append("Monitor for safety concerns and functional impairment")
        
        return recommendations
    
    def export_personality_profile_json(
        self, 
        profile: PersonalityProfile, 
        include_raw_responses: bool = True,
        include_pattern_details: bool = True
    ) -> str:
        """Export personality profile as comprehensive JSON"""
        export_data = {
            "scid_pd_export": {
                "version": "1.0",
                "export_timestamp": datetime.now().isoformat(),
                "assessment_date": profile.assessment_date.isoformat(),
                "total_modules": len(profile.module_results),
                "positive_diagnoses_count": len(profile.get_positive_diagnoses()),
                "total_assessment_time": profile.total_assessment_time,
                "overall_severity": profile.overall_severity.value if profile.overall_severity else None
            },
            "personality_profile": {
                "primary_diagnoses": profile.primary_diagnoses,
                "secondary_features": profile.secondary_features,
                "dimensional_scores": profile.dimensional_scores,
                "cluster_distribution": {
                    cluster.value: diagnoses 
                    for cluster, diagnoses in profile.get_cluster_distribution().items()
                },
                "recommendations": profile.recommendations,
                "clinician_notes": profile.clinician_notes
            },
            "module_results": []
        }
        
        for result in profile.module_results:
            result_data = {
                "module_id": result.module_id,
                "module_name": result.module_name,
                "dsm_cluster": result.dsm_cluster.value,
                "completion_date": result.completion_date.isoformat(),
                "administration_time_mins": result.administration_time_mins,
                "scoring": {
                    "total_score": result.total_score,
                    "max_possible_score": result.max_possible_score,
                    "percentage_score": round(result.percentage_score * 100, 1),
                    "dimensional_score": result.dimensional_score,
                    "criteria_met": result.criteria_met,
                    "severity_level": result.severity_level.value if result.severity_level else None
                },
                "onset_pattern": result.onset_pattern.value if result.onset_pattern else None,
                "pervasiveness": result.pervasiveness_assessment.value if result.pervasiveness_assessment else None,
                "patterns_count": len(result.patterns_present),
                "differential_considerations": result.differential_considerations,
                "notes": result.notes
            }
            
            if include_pattern_details:
                result_data["patterns_present"] = [
                    {
                        "pattern_name": pattern.pattern_name,
                        "dimension_type": pattern.dimension_type.value,
                        "severity": pattern.severity.value if pattern.severity else None,
                        "pervasiveness": pattern.pervasiveness.value if pattern.pervasiveness else None,
                        "onset_period": pattern.onset_period.value if pattern.onset_period else None,
                        "onset_age": pattern.onset_age,
                        "contexts_affected": pattern.contexts_affected,
                        "behavioral_examples": pattern.behavioral_examples,
                        "confidence": round(pattern.confidence, 3)
                    }
                    for pattern in result.patterns_present
                ]
            
            if include_raw_responses:
                result_data["responses"] = [
                    {
                        "question_id": response.question_id,
                        "response": response.response,
                        "onset_age": response.onset_age,
                        "examples_provided": response.examples_provided,
                        "timestamp": response.timestamp.isoformat(),
                        "notes": response.notes,
                        "confidence": response.confidence
                    }
                    for response in result.responses
                ]
                result_data["raw_scores"] = result.raw_scores
            
            export_data["module_results"].append(result_data)
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def generate_personality_report(self, profile: PersonalityProfile) -> str:
        """Generate a comprehensive personality assessment report"""
        if not profile.module_results:
            return "No personality assessment data available."
        
        positive_diagnoses = profile.get_positive_diagnoses()
        cluster_dist = profile.get_cluster_distribution()
        
        report_lines = [
            "=" * 60,
            "SCID-PD PERSONALITY ASSESSMENT REPORT",
            "=" * 60,
            "",
            f"Assessment Date: {profile.assessment_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Assessment Time: {profile.total_assessment_time} minutes",
            f"Overall Severity: {profile.overall_severity.value if profile.overall_severity else 'Not applicable'}",
            "",
            "SUMMARY:",
            "-" * 20,
            f"Total Personality Disorders Assessed: {len(profile.module_results)}",
            f"Personality Disorders Meeting Criteria: {len(positive_diagnoses)}",
            "",
        ]
        
        if positive_diagnoses:
            report_lines.extend([
                "PRIMARY DIAGNOSES:",
                "-" * 20
            ])
            for result in sorted(positive_diagnoses, key=lambda x: x.percentage_score, reverse=True):
                severity_str = f" ({result.severity_level.value})" if result.severity_level else ""
                dimensional_str = f" [Dimensional: {result.dimensional_score:.1f}/100]" if result.dimensional_score else ""
                
                report_lines.extend([
                    f"• {result.module_name}: {result.percentage_score*100:.1f}%{severity_str}{dimensional_str}",
                    f"  Cluster: {result.dsm_cluster.value.replace('_', ' ').title()}",
                    f"  Patterns Present: {len(result.patterns_present)}",
                    ""
                ])
        
        # Cluster analysis
        report_lines.extend([
            "CLUSTER ANALYSIS:",
            "-" * 20
        ])
        
        for cluster, diagnoses in cluster_dist.items():
            cluster_name = cluster.value.replace("_", " ").title()
            if diagnoses:
                report_lines.append(f"{cluster_name}: {', '.join(diagnoses)}")
            else:
                report_lines.append(f"{cluster_name}: No criteria met")
        
        report_lines.append("")
        
        # Dimensional scores
        if profile.dimensional_scores:
            report_lines.extend([
                "DIMENSIONAL SCORES (0-100):",
                "-" * 20
            ])
            for pd_name, score in sorted(profile.dimensional_scores.items(), 
                                       key=lambda x: x[1], reverse=True):
                score_interpretation = "High" if score >= 70 else "Moderate" if score >= 50 else "Low"
                report_lines.append(f"{pd_name}: {score:.1f} ({score_interpretation})")
            
            report_lines.append("")
        
        # Recommendations
        if profile.recommendations:
            report_lines.extend([
                "CLINICAL RECOMMENDATIONS:",
                "-" * 20
            ])
            for i, rec in enumerate(profile.recommendations, 1):
                report_lines.append(f"{i}. {rec}")
            
            report_lines.append("")
        
        # Clinician notes
        if profile.clinician_notes:
            report_lines.extend([
                "CLINICIAN NOTES:",
                "-" * 20,
                profile.clinician_notes,
                ""
            ])
        
        report_lines.extend([
            "=" * 60,
            "END OF PERSONALITY ASSESSMENT REPORT",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
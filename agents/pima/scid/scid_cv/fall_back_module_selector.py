# scid_cv/module_selector.py
"""
SCID-CV Module Selector using ReAct Agent Pattern
Implements an observe-reason-act cycle to select the most appropriate module
"""

from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime
import json

from langgraph.graph import StateGraph, END
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# Import SCID modules registry
from scid_cv.base_types import SCIDModule
from scid_cv import MODULE_REGISTRY, list_available_modules

class ReasoningStep(Enum):
    OBSERVE = "observe"
    REASON = "reason"
    DECIDE = "decide"

@dataclass 
class ClinicalEvidence:
    """Evidence extracted from clinical presentation"""
    symptom_type: str
    severity: str
    duration: str
    frequency: str
    triggers: List[str] = field(default_factory=list)
    functional_impact: List[str] = field(default_factory=list)
    confidence: float = 1.0
    text_snippet: str = ""

@dataclass
class ModuleMatch:
    """Module matching result"""
    module_id: str
    module_name: str
    relevance_score: float
    matching_evidence: List[ClinicalEvidence] = field(default_factory=list)
    reasoning: str = ""

class AgentState(TypedDict):
    """State for the ReAct agent"""
    input_text: str
    observations: List[str]
    extracted_evidence: List[ClinicalEvidence]
    reasoning_steps: List[str]
    module_scores: Dict[str, float]
    final_selection: Optional[ModuleMatch]
    messages: List[BaseMessage]

class ModuleSelector:
    """ReAct agent for SCID-CV module selection"""
    
    def __init__(self):
        self.available_modules = list_available_modules()
        self.symptom_patterns = self._initialize_symptom_patterns()
        self.graph = self._create_graph()
    
    def _initialize_symptom_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize symptom pattern matching rules for each module"""
        return {
            "MDD": {
                "keywords": ["depress", "sad", "hopeless", "worthless", "anhedonia", "fatigue", "sleep", "appetite", "concentration", "guilt", "suicid"],
                "severity_indicators": ["severe", "significant", "major", "persistent", "chronic"],
                "duration_patterns": [r"(\d+)\s*(week|month|year)", r"ongoing", r"persistent", r"chronic"],
                "functional_impact": ["work", "social", "relationship", "daily activit", "perform"]
            },
            "GAD": {
                "keywords": ["worry", "anxious", "anxiety", "nervous", "restless", "tense", "muscle tension", "fatigue", "concentration", "irritab", "sleep"],
                "severity_indicators": ["excessive", "uncontrollable", "persistent", "chronic"],
                "duration_patterns": [r"(\d+)\s*(month)", r"ongoing", r"persistent", r"chronic"],
                "functional_impact": ["work", "social", "daily", "perform"]
            },
            "PANIC": {
                "keywords": ["panic", "attack", "palpitation", "heart racing", "shortness of breath", "chest pain", "dizz", "sweat", "tremble", "fear of dying", "fear of losing control"],
                "severity_indicators": ["sudden", "intense", "severe", "overwhelming"],
                "duration_patterns": [r"minutes", r"brief", r"sudden"],
                "functional_impact": ["avoid", "restrict", "limit"]
            },
            "SOCIAL_ANXIETY": {
                "keywords": ["social", "embarrass", "humiliat", "judge", "scrutin", "perform", "public", "speak", "blush", "tremble"],
                "severity_indicators": ["intense", "severe", "overwhelming", "paralyzing"],
                "duration_patterns": [r"(\d+)\s*(month|year)", r"lifelong", r"since"],
                "functional_impact": ["avoid social", "isolat", "work meetings", "presentation"]
            },
            "SPECIFIC_PHOBIA": {
                "keywords": ["phobia", "fear of", "afraid of", "terrified", "specific", "avoid", "animal", "height", "flying", "blood", "inject"],
                "severity_indicators": ["intense", "irrational", "overwhelming", "extreme"],
                "duration_patterns": [r"(\d+)\s*(year)", r"since childhood", r"lifelong"],
                "functional_impact": ["avoid", "restrict", "limit", "interfere"]
            },
            "AGORAPHOBIA": {
                "keywords": ["agoraphob", "crowded", "open space", "enclosed", "public transport", "outside home", "escape", "trap"],
                "severity_indicators": ["intense", "severe", "overwhelming"],
                "duration_patterns": [r"(\d+)\s*(month|year)", r"ongoing"],
                "functional_impact": ["housebound", "avoid leaving", "restrict travel"]
            },
            "PTSD": {
                "keywords": ["trauma", "flashback", "nightmare", "intrusive", "avoid", "hypervigilant", "startle", "numb", "detach", "irritab"],
                "severity_indicators": ["severe", "intense", "overwhelming", "debilitating"],
                "duration_patterns": [r"since", r"after", r"(\d+)\s*(month|year)", r"ongoing"],
                "functional_impact": ["avoid", "isolat", "work", "relationship", "sleep"]
            },
            "OCD": {
                "keywords": ["obsess", "compuls", "ritual", "repetitive", "check", "wash", "count", "arrange", "intrusive thought", "contamination"],
                "severity_indicators": ["excessive", "time-consuming", "interfering"],
                "duration_patterns": [r"hours", r"daily", r"multiple times"],
                "functional_impact": ["time consuming", "interfere", "prevent", "delay"]
            },
            "BIPOLAR": {
                "keywords": ["manic", "hypomanic", "elevated mood", "grandiose", "racing thoughts", "sleep", "talkative", "impulsive", "mood episode"],
                "severity_indicators": ["extreme", "severe", "marked", "significant"],
                "duration_patterns": [r"episode", r"(\d+)\s*(day|week)", r"period of"],
                "functional_impact": ["hospitalization", "work", "relationship", "judgment"]
            },
            "SUBSTANCE_USE": {
                "keywords": ["alcohol", "drug", "substance", "drinking", "using", "addiction", "tolerance", "withdrawal", "craving"],
                "severity_indicators": ["excessive", "problematic", "dependent", "addicted"],
                "duration_patterns": [r"daily", r"(\d+)\s*(month|year)", r"ongoing"],
                "functional_impact": ["work", "relationship", "health", "legal", "financial"]
            },
            "ALCOHOL_USE": {
                "keywords": ["alcohol", "drinking", "drunk", "intoxicated", "tolerance", "withdrawal", "craving", "hangover"],
                "severity_indicators": ["excessive", "heavy", "problematic", "dependent"],
                "duration_patterns": [r"daily", r"(\d+)\s*(month|year)", r"ongoing"],
                "functional_impact": ["work", "relationship", "health", "legal", "driving"]
            },
            "EATING_DISORDERS": {
                "keywords": ["eating", "weight", "body image", "restrict", "binge", "purge", "vomit", "laxative", "anorex", "bulim"],
                "severity_indicators": ["severe", "extreme", "significant weight", "dangerous"],
                "duration_patterns": [r"(\d+)\s*(month|year)", r"ongoing", r"chronic"],
                "functional_impact": ["health", "social", "work", "relationship", "medical"]
            },
            "ADHD": {
                "keywords": ["attention", "concentration", "focus", "distractib", "hyperactiv", "impulsiv", "restless", "forgetful", "disorganiz"],
                "severity_indicators": ["significant", "severe", "marked", "persistent"],
                "duration_patterns": [r"since childhood", r"lifelong", r"(\d+)\s*(year)"],
                "functional_impact": ["work", "school", "relationship", "organization", "task completion"]
            },
            "ADJUSTMENT": {
                "keywords": ["stress", "stressor", "adjust", "life change", "recent", "reaction", "response to"],
                "severity_indicators": ["significant", "marked", "severe"],
                "duration_patterns": [r"since", r"after", r"recent", r"(\d+)\s*(month)"],
                "functional_impact": ["work", "social", "relationship", "daily function"]
            }
        }
    
    def _create_graph(self) -> StateGraph:
        """Create the ReAct agent graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("observe", self._observe_step)
        workflow.add_node("reason", self._reason_step)  
        workflow.add_node("decide", self._decide_step)
        
        # Add edges
        workflow.set_entry_point("observe")
        workflow.add_edge("observe", "reason")
        workflow.add_edge("reason", "decide")
        workflow.add_edge("decide", END)
        
        return workflow.compile()
    
    def _observe_step(self, state: AgentState) -> AgentState:
        """Step 1: Observe and extract clinical evidence from input"""
        input_text = state["input_text"]
        
        observations = []
        extracted_evidence = []
        
        # Extract basic clinical information
        observations.append("Analyzing clinical presentation...")
        
        # Extract symptoms and their characteristics
        for symptom_type, patterns in self.symptom_patterns.items():
            evidence = self._extract_evidence_for_pattern(input_text, symptom_type, patterns)
            if evidence:
                extracted_evidence.extend(evidence)
                observations.append(f"Found evidence for {symptom_type}: {len(evidence)} indicators")
        
        # Extract temporal information
        duration_info = self._extract_temporal_information(input_text)
        if duration_info:
            observations.append(f"Temporal information: {duration_info}")
        
        # Extract severity information  
        severity_info = self._extract_severity_information(input_text)
        if severity_info:
            observations.append(f"Severity indicators: {severity_info}")
        
        # Extract functional impact
        functional_impact = self._extract_functional_impact(input_text)
        if functional_impact:
            observations.append(f"Functional impact: {functional_impact}")
        
        state["observations"] = observations
        state["extracted_evidence"] = extracted_evidence
        state["messages"].append(HumanMessage(content=f"Observed: {len(extracted_evidence)} pieces of clinical evidence"))
        
        return state
    
    def _reason_step(self, state: AgentState) -> AgentState:
        """Step 2: Reason about evidence and calculate module relevance scores"""
        extracted_evidence = state["extracted_evidence"]
        reasoning_steps = []
        module_scores = {}
        
        reasoning_steps.append("Analyzing evidence patterns for module matching...")
        
        # Calculate relevance scores for each module
        for module_info in self.available_modules:
            module_id = module_info["id"]
            module_name = module_info["name"]
            
            score = self._calculate_module_relevance_score(
                module_id, extracted_evidence, reasoning_steps
            )
            module_scores[module_id] = score
            
            if score > 0.1:  # Only reason about relevant modules
                reasoning_steps.append(
                    f"{module_name} relevance: {score:.2f} - "
                    f"Based on {self._get_matching_evidence_count(module_id, extracted_evidence)} matching indicators"
                )
        
        # Apply clinical reasoning rules
        refined_scores = self._apply_clinical_reasoning_rules(module_scores, extracted_evidence, reasoning_steps)
        
        state["reasoning_steps"] = reasoning_steps
        state["module_scores"] = refined_scores
        state["messages"].append(AIMessage(content=f"Reasoned about {len([s for s in refined_scores.values() if s > 0])} relevant modules"))
        
        return state
    
    def _decide_step(self, state: AgentState) -> AgentState:
        """Step 3: Decide on the most appropriate module"""
        module_scores = state["module_scores"]
        extracted_evidence = state["extracted_evidence"]
        
        if not module_scores or max(module_scores.values()) == 0:
            # No clear match - default to adjustment disorder or general screening
            final_selection = ModuleMatch(
                module_id="ADJUSTMENT",
                module_name="Adjustment Disorder",
                relevance_score=0.3,
                reasoning="No specific psychiatric syndrome clearly indicated. Adjustment disorder assessment recommended as starting point."
            )
        else:
            # Select highest scoring module
            best_module_id = max(module_scores.keys(), key=lambda k: module_scores[k])
            best_score = module_scores[best_module_id]
            
            # Get module info
            module_info = next((m for m in self.available_modules if m["id"] == best_module_id), None)
            module_name = module_info["name"] if module_info else best_module_id
            
            # Get matching evidence for this module
            matching_evidence = [
                evidence for evidence in extracted_evidence
                if evidence.symptom_type == best_module_id
            ]
            
            # Generate reasoning
            reasoning = self._generate_final_reasoning(
                best_module_id, best_score, matching_evidence, state["reasoning_steps"]
            )
            
            final_selection = ModuleMatch(
                module_id=best_module_id,
                module_name=module_name,
                relevance_score=best_score,
                matching_evidence=matching_evidence,
                reasoning=reasoning
            )
        
        state["final_selection"] = final_selection
        state["messages"].append(AIMessage(content=f"Selected: {final_selection.module_name} (score: {final_selection.relevance_score:.2f})"))
        
        return state
    
    def _extract_evidence_for_pattern(self, text: str, symptom_type: str, patterns: Dict[str, Any]) -> List[ClinicalEvidence]:
        """Extract evidence matching a specific pattern"""
        evidence = []
        text_lower = text.lower()
        
        # Check for keyword matches
        keyword_matches = sum(1 for keyword in patterns["keywords"] if keyword in text_lower)
        
        if keyword_matches > 0:
            # Extract severity
            severity = "moderate"  # default
            for severity_indicator in patterns["severity_indicators"]:
                if severity_indicator in text_lower:
                    if severity_indicator in ["severe", "extreme", "overwhelming", "debilitating"]:
                        severity = "severe"
                    elif severity_indicator in ["significant", "marked", "major"]:
                        severity = "moderate"
                    break
            
            # Extract duration
            duration = "unspecified"
            for pattern in patterns["duration_patterns"]:
                if isinstance(pattern, str):
                    if pattern in text_lower:
                        duration = pattern
                        break
                else:  # regex pattern
                    match = re.search(pattern, text_lower)
                    if match:
                        duration = match.group(0)
                        break
            
            # Extract functional impact
            functional_impact = []
            for impact_area in patterns["functional_impact"]:
                if impact_area in text_lower:
                    functional_impact.append(impact_area)
            
            evidence.append(ClinicalEvidence(
                symptom_type=symptom_type,
                severity=severity,
                duration=duration,
                frequency="unspecified",
                triggers=[],
                functional_impact=functional_impact,
                confidence=min(1.0, keyword_matches / len(patterns["keywords"])),
                text_snippet=self._extract_relevant_snippet(text, patterns["keywords"])
            ))
        
        return evidence
    
    def _extract_temporal_information(self, text: str) -> str:
        """Extract temporal information from text"""
        temporal_patterns = [
            r"(\d+)\s*(day|week|month|year)s?",
            r"since\s+\w+",
            r"for\s+the\s+past\s+\w+",
            r"ongoing",
            r"chronic",
            r"acute",
            r"sudden"
        ]
        
        for pattern in temporal_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0)
        
        return "unspecified"
    
    def _extract_severity_information(self, text: str) -> str:
        """Extract severity information from text"""
        severity_patterns = {
            "severe": ["severe", "extreme", "intense", "overwhelming", "debilitating", "9/10", "10/10"],
            "moderate": ["moderate", "significant", "marked", "considerable", "6/10", "7/10", "8/10"],
            "mild": ["mild", "slight", "minor", "3/10", "4/10", "5/10"]
        }
        
        text_lower = text.lower()
        for severity, indicators in severity_patterns.items():
            for indicator in indicators:
                if indicator in text_lower:
                    return severity
        
        return "unspecified"
    
    def _extract_functional_impact(self, text: str) -> List[str]:
        """Extract functional impact areas from text"""
        impact_areas = []
        impact_patterns = {
            "work": ["work", "job", "employment", "productivity", "performance"],
            "social": ["social", "friends", "relationship", "family"],
            "daily_activities": ["daily", "routine", "activities", "functioning"],
            "academic": ["school", "academic", "studying", "concentration"],
            "self_care": ["self-care", "hygiene", "eating", "sleeping"]
        }
        
        text_lower = text.lower()
        for area, patterns in impact_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                impact_areas.append(area)
        
        return impact_areas
    
    def _extract_relevant_snippet(self, text: str, keywords: List[str]) -> str:
        """Extract relevant text snippet containing keywords"""
        sentences = text.split('. ')
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords[:3]):  # Check first 3 keywords
                return sentence.strip()
        return ""
    
    def _calculate_module_relevance_score(self, module_id: str, evidence: List[ClinicalEvidence], reasoning_steps: List[str]) -> float:
        """Calculate relevance score for a specific module"""
        relevant_evidence = [e for e in evidence if e.symptom_type == module_id]
        
        if not relevant_evidence:
            return 0.0
        
        # Base score from evidence count and confidence
        base_score = sum(e.confidence for e in relevant_evidence) / len(evidence) if evidence else 0
        
        # Severity multiplier
        severity_multiplier = 1.0
        for evidence_item in relevant_evidence:
            if evidence_item.severity == "severe":
                severity_multiplier *= 1.5
            elif evidence_item.severity == "moderate":
                severity_multiplier *= 1.2
        
        # Functional impact multiplier
        impact_multiplier = 1.0
        total_impact_areas = sum(len(e.functional_impact) for e in relevant_evidence)
        if total_impact_areas > 0:
            impact_multiplier = 1.0 + (total_impact_areas * 0.1)
        
        final_score = base_score * severity_multiplier * impact_multiplier
        return min(1.0, final_score)  # Cap at 1.0
    
    def _get_matching_evidence_count(self, module_id: str, evidence: List[ClinicalEvidence]) -> int:
        """Get count of evidence matching a module"""
        return len([e for e in evidence if e.symptom_type == module_id])
    
    def _apply_clinical_reasoning_rules(self, scores: Dict[str, float], evidence: List[ClinicalEvidence], reasoning_steps: List[str]) -> Dict[str, float]:
        """Apply clinical reasoning rules to refine scores"""
        refined_scores = scores.copy()
        
        # Rule 1: If substance use indicators present, boost substance use modules
        substance_indicators = any("substance" in e.text_snippet.lower() or "alcohol" in e.text_snippet.lower() for e in evidence)
        if substance_indicators:
            refined_scores["SUBSTANCE_USE"] = refined_scores.get("SUBSTANCE_USE", 0) * 1.3
            refined_scores["ALCOHOL_USE"] = refined_scores.get("ALCOHOL_USE", 0) * 1.3
            reasoning_steps.append("Applied rule: Substance use indicators detected")
        
        # Rule 2: If panic symptoms present, consider both panic disorder and GAD
        panic_indicators = any("panic" in e.text_snippet.lower() or "heart racing" in e.text_snippet.lower() for e in evidence)
        if panic_indicators:
            refined_scores["PANIC"] = refined_scores.get("PANIC", 0) * 1.2
            refined_scores["GAD"] = refined_scores.get("GAD", 0) * 1.1
            reasoning_steps.append("Applied rule: Panic symptoms may indicate panic disorder or GAD")
        
        # Rule 3: If trauma history mentioned, boost PTSD
        trauma_indicators = any("trauma" in e.text_snippet.lower() or "after" in e.text_snippet.lower() for e in evidence)
        if trauma_indicators:
            refined_scores["PTSD"] = refined_scores.get("PTSD", 0) * 1.4
            reasoning_steps.append("Applied rule: Trauma history indicators boost PTSD consideration")
        
        # Rule 4: If recent stressor mentioned, boost adjustment disorder
        recent_stressor = any("recent" in e.text_snippet.lower() or "since" in e.text_snippet.lower() for e in evidence)
        if recent_stressor:
            refined_scores["ADJUSTMENT"] = refined_scores.get("ADJUSTMENT", 0.2) * 1.3
            reasoning_steps.append("Applied rule: Recent stressor boosts adjustment disorder consideration")
        
        return refined_scores
    
    def _generate_final_reasoning(self, module_id: str, score: float, evidence: List[ClinicalEvidence], reasoning_steps: List[str]) -> str:
        """Generate final reasoning for the selected module"""
        reasoning_parts = []
        
        # Evidence summary
        evidence_summary = f"Clinical presentation contains {len(evidence)} indicators supporting {module_id} assessment"
        reasoning_parts.append(evidence_summary)
        
        # Severity justification
        severe_evidence = [e for e in evidence if e.severity == "severe"]
        if severe_evidence:
            reasoning_parts.append(f"Severity level is concerning with {len(severe_evidence)} severe indicators")
        
        # Functional impact justification
        impact_areas = set()
        for e in evidence:
            impact_areas.update(e.functional_impact)
        
        if impact_areas:
            reasoning_parts.append(f"Functional impairment noted in: {', '.join(impact_areas)}")
        
        # Confidence statement
        if score > 0.7:
            confidence = "High confidence"
        elif score > 0.4:
            confidence = "Moderate confidence"
        else:
            confidence = "Low confidence"
        
        reasoning_parts.append(f"{confidence} in module selection based on symptom pattern matching")
        
        return ". ".join(reasoning_parts) + "."
    
    def select_module(self, clinical_presentation: str) -> Dict[str, Any]:
        """Main method to select appropriate SCID-CV module"""
        
        # Initialize state
        initial_state = AgentState(
            input_text=clinical_presentation,
            observations=[],
            extracted_evidence=[],
            reasoning_steps=[],
            module_scores={},
            final_selection=None,
            messages=[]
        )
        
        # Run the ReAct agent
        result = self.graph.invoke(initial_state)
        final_selection = result["final_selection"]
        
        # Return structured result
        return {
            "most_relevant_module": final_selection.module_id,
            "module_name": final_selection.module_name,
            "relevance_score": final_selection.relevance_score,
            "reason": final_selection.reasoning,
            "supporting_evidence": [
                {
                    "symptom_type": e.symptom_type,
                    "severity": e.severity,
                    "duration": e.duration,
                    "functional_impact": e.functional_impact,
                    "confidence": e.confidence,
                    "text_snippet": e.text_snippet
                }
                for e in final_selection.matching_evidence
            ],
            "alternative_considerations": {
                module_id: score for module_id, score in result["module_scores"].items() 
                if score > 0.1 and module_id != final_selection.module_id
            },
            "reasoning_trace": result["reasoning_steps"],
            "observations": result["observations"]
        }

# Example usage function
def analyze_clinical_presentation(clinical_text: str) -> Dict[str, Any]:
    """
    Analyze clinical presentation and return module recommendation
    
    Args:
        clinical_text: Clinical presentation text
        
    Returns:
        Dict with most_relevant_module and reason
    """
    selector = ModuleSelector()
    result = selector.select_module(clinical_text)
    
    return {
        "most_relevant_module": result["most_relevant_module"],
        "reason": result["reason"]
    }

# Test with the provided example
if __name__ == "__main__":
    example_presentation = """
    Patient presents with severe headaches. The headache reportedly began suddenly on Monday morning 
    and has been ongoing for one week. Patient rates the severity as 8/10. The headache occurs daily 
    and is triggered by stress and bright lights, specifically fluorescent lighting and stress at work.
    Functionally, the patient reports difficulty performing daily activities. Work performance has been 
    impacted, with decreased concentration and productivity. Social relationships and activities have been 
    affected, with cancellation of plans with friends.
    Prior episodes of similar severity have not been reported by the patient.
    """
    
    result = analyze_clinical_presentation(example_presentation)
    print(json.dumps(result, indent=2))
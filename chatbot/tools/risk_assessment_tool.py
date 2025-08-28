"""
Risk Assessment Tool for MindMate Chatbot
========================================
Tool for suicide risk and safety evaluation.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class RiskAssessmentData(BaseModel):
    """Data collected from risk assessment"""
    suicide_ideation: Optional[bool] = None
    suicide_plan: Optional[str] = None
    suicide_intent: Optional[bool] = None
    past_attempts: Optional[str] = None
    self_harm_history: Optional[str] = None
    homicidal_thoughts: Optional[bool] = None
    access_means: Optional[str] = None
    protective_factors: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    risk_reason: Optional[str] = None
    completion_timestamp: Optional[datetime] = None

class RiskAssessmentTool:
    """Tool for risk assessment"""
    
    def __init__(self):
        self.data = RiskAssessmentData()
        self.current_question = 0
        self.questions = [
            {
                "id": "suicide_ideation",
                "text": "Have you had thoughts of harming yourself or ending your life?",
                "type": "yes_no",
                "field": "suicide_ideation",
                "critical": True
            },
            {
                "id": "suicide_plan",
                "text": "If yes, do you have a specific plan for how you would do this?",
                "type": "open_ended",
                "field": "suicide_plan",
                "condition": "suicide_ideation==True"
            },
            {
                "id": "suicide_intent",
                "text": "Do you intend to act on these thoughts?",
                "type": "yes_no",
                "field": "suicide_intent",
                "condition": "suicide_ideation==True",
                "critical": True
            },
            {
                "id": "past_attempts",
                "text": "Have you ever attempted to harm yourself in the past?",
                "type": "open_ended",
                "field": "past_attempts"
            },
            {
                "id": "self_harm_history",
                "text": "Have you engaged in any self-harming behaviors?",
                "type": "open_ended",
                "field": "self_harm_history"
            },
            {
                "id": "homicidal_thoughts",
                "text": "Have you had thoughts of harming others?",
                "type": "yes_no",
                "field": "homicidal_thoughts",
                "critical": True
            },
            {
                "id": "access_means",
                "text": "Do you have access to means that could be used for self-harm?",
                "type": "open_ended",
                "field": "access_means"
            },
            {
                "id": "protective_factors",
                "text": "What keeps you safe? What reasons do you have for living?",
                "type": "open_ended",
                "field": "protective_factors"
            }
        ]
    
    def start_assessment(self) -> Dict[str, Any]:
        """Start the risk assessment"""
        self.current_question = 0
        return {
            "status": "started",
            "question": self.questions[0],
            "progress": f"1/{len(self.questions)}",
            "warning": "This assessment contains sensitive questions about safety and risk."
        }
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process user response and get next question"""
        if self.current_question >= len(self.questions):
            return {"error": "Assessment already completed"}
        
        # Store the response
        current_q = self.questions[self.current_question]
        
        # Convert response to appropriate type
        if current_q["type"] == "yes_no":
            bool_response = response.lower() in ["yes", "y", "true", "1"]
            setattr(self.data, current_q["field"], bool_response)
        else:
            setattr(self.data, current_q["field"], response)
        
        # Check for critical responses that need immediate attention
        if current_q.get("critical") and getattr(self.data, current_q["field"]):
            return {
                "status": "critical",
                "message": "This response indicates immediate safety concerns. Please contact emergency services or a mental health professional immediately.",
                "data": self.data.dict(),
                "risk_level": "critical"
            }
        
        self.current_question += 1
        
        # Check if assessment is complete
        if self.current_question >= len(self.questions):
            self.data.completion_timestamp = datetime.now()
            risk_assessment = self._assess_risk()
            self.data.risk_level = risk_assessment["level"]
            self.data.risk_reason = risk_assessment["reason"]
            
            return {
                "status": "completed",
                "data": self.data.dict(),
                "risk_assessment": risk_assessment,
                "summary": self._generate_summary()
            }
        
        # Get next question, considering conditions
        next_question = self._get_next_question()
        if next_question:
            return {
                "status": "question",
                "question": next_question,
                "progress": f"{self.current_question + 1}/{len(self.questions)}"
            }
        else:
            # Skip to end if no more applicable questions
            self.current_question = len(self.questions)
            return self.process_response("")  # Recursive call to complete
    
    def _get_next_question(self) -> Optional[Dict]:
        """Get the next question considering conditions"""
        while self.current_question < len(self.questions):
            question = self.questions[self.current_question]
            
            # Check if question should be asked based on condition
            if self._should_ask_question(question):
                return question
            
            self.current_question += 1
        
        return None
    
    def _should_ask_question(self, question: Dict) -> bool:
        """Check if a question should be asked based on conditions"""
        condition = question.get("condition")
        if not condition:
            return True
        
        # Simple condition checking
        if "==" in condition:
            field_name, expected_value = condition.split("==")
            if expected_value.lower() == "true":
                expected_value = True
            elif expected_value.lower() == "false":
                expected_value = False
            
            field_value = getattr(self.data, field_name)
            return field_value == expected_value
        
        return True
    
    def _assess_risk(self) -> Dict[str, Any]:
        """Assess overall risk level based on collected data"""
        risk_score = 0
        reasons = []
        
        # Suicide ideation (high weight)
        if self.data.suicide_ideation:
            risk_score += 8
            reasons.append("Active suicidal thoughts")
        
        # Suicide intent (critical weight)
        if self.data.suicide_intent:
            risk_score += 10
            reasons.append("Intent to act on suicidal thoughts")
        
        # Suicide plan (high weight)
        if self.data.suicide_plan:
            risk_score += 6
            reasons.append("Specific suicide plan")
        
        # Past attempts (moderate weight)
        if self.data.past_attempts:
            risk_score += 4
            reasons.append("History of suicide attempts")
        
        # Self-harm (moderate weight)
        if self.data.self_harm_history:
            risk_score += 3
            reasons.append("History of self-harm")
        
        # Homicidal thoughts (high weight)
        if self.data.homicidal_thoughts:
            risk_score += 7
            reasons.append("Homicidal thoughts")
        
        # Access to means (moderate weight)
        if self.data.access_means:
            risk_score += 3
            reasons.append("Access to means for self-harm")
        
        # Protective factors (negative weight)
        if self.data.protective_factors:
            risk_score -= 2
            reasons.append("Identified protective factors")
        
        # Determine risk level
        if risk_score >= 15:
            level = RiskLevel.CRITICAL
        elif risk_score >= 10:
            level = RiskLevel.HIGH
        elif risk_score >= 5:
            level = RiskLevel.MODERATE
        else:
            level = RiskLevel.LOW
        
        return {
            "level": level,
            "score": risk_score,
            "reasons": reasons,
            "recommendation": self._get_recommendation(level)
        }
    
    def _get_recommendation(self, risk_level: RiskLevel) -> str:
        """Get recommendation based on risk level"""
        recommendations = {
            RiskLevel.LOW: "Continue with regular monitoring and support.",
            RiskLevel.MODERATE: "Increase monitoring and consider professional support.",
            RiskLevel.HIGH: "Immediate professional evaluation recommended.",
            RiskLevel.CRITICAL: "Emergency intervention required immediately."
        }
        return recommendations.get(risk_level, "Assessment incomplete.")
    
    def _generate_summary(self) -> str:
        """Generate a summary of collected data"""
        summary_parts = []
        
        if self.data.suicide_ideation is not None:
            summary_parts.append(f"Suicidal Thoughts: {'Yes' if self.data.suicide_ideation else 'No'}")
        if self.data.suicide_plan:
            summary_parts.append(f"Suicide Plan: {self.data.suicide_plan}")
        if self.data.suicide_intent is not None:
            summary_parts.append(f"Suicide Intent: {'Yes' if self.data.suicide_intent else 'No'}")
        if self.data.past_attempts:
            summary_parts.append(f"Past Attempts: {self.data.past_attempts}")
        if self.data.self_harm_history:
            summary_parts.append(f"Self-Harm History: {self.data.self_harm_history}")
        if self.data.homicidal_thoughts is not None:
            summary_parts.append(f"Homicidal Thoughts: {'Yes' if self.data.homicidal_thoughts else 'No'}")
        if self.data.access_means:
            summary_parts.append(f"Access to Means: {self.data.access_means}")
        if self.data.protective_factors:
            summary_parts.append(f"Protective Factors: {self.data.protective_factors}")
        if self.data.risk_level:
            summary_parts.append(f"Risk Level: {self.data.risk_level.value.upper()}")
        
        return "; ".join(summary_parts) if summary_parts else "No information collected"

# Global instance
_risk_assessment_tool = RiskAssessmentTool()

def ask_risk_assessment(action: str, **kwargs) -> Dict[str, Any]:
    """Tool function for risk assessment"""
    try:
        if action == "start":
            return _risk_assessment_tool.start_assessment()
        elif action == "respond":
            response = kwargs.get("response")
            if not response:
                return {"error": "response is required"}
            return _risk_assessment_tool.process_response(response)
        elif action == "get_data":
            return _risk_assessment_tool.data.dict()
        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"Error in ask_risk_assessment: {e}")
        return {"error": f"Tool execution failed: {str(e)}"}

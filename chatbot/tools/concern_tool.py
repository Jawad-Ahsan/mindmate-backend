"""
Concern Tool for MindMate Chatbot
=================================
Tool for collecting presenting concerns and HPI information.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

class ConcernData(BaseModel):
    """Data collected from concern assessment"""
    presenting_concern: Optional[str] = None
    onset_timing: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[str] = None
    frequency: Optional[str] = None
    triggers: Optional[str] = None
    impact_work: Optional[str] = None
    impact_relationships: Optional[str] = None
    prior_episodes: Optional[str] = None
    completion_timestamp: Optional[datetime] = None

class ConcernTool:
    """Tool for collecting presenting concerns"""
    
    def __init__(self):
        self.data = ConcernData()
        self.current_question = 0
        self.questions = [
            {
                "id": "presenting_concern",
                "text": "What brings you here today? What's your main concern?",
                "type": "open_ended",
                "field": "presenting_concern"
            },
            {
                "id": "onset_timing",
                "text": "When did this problem first start?",
                "type": "open_ended",
                "field": "onset_timing"
            },
            {
                "id": "duration",
                "text": "How long has this been going on?",
                "type": "open_ended",
                "field": "duration"
            },
            {
                "id": "severity",
                "text": "On a scale of 1-10, how severe is this problem? (1=mild, 10=very severe)",
                "type": "scale",
                "field": "severity"
            },
            {
                "id": "frequency",
                "text": "How often do you experience this problem?",
                "type": "open_ended",
                "field": "frequency"
            },
            {
                "id": "triggers",
                "text": "What makes this problem worse or triggers it?",
                "type": "open_ended",
                "field": "triggers"
            },
            {
                "id": "impact_work",
                "text": "How does this problem affect your work or daily activities?",
                "type": "open_ended",
                "field": "impact_work"
            },
            {
                "id": "impact_relationships",
                "text": "How does this problem affect your relationships?",
                "type": "open_ended",
                "field": "impact_relationships"
            },
            {
                "id": "prior_episodes",
                "text": "Have you experienced this problem before?",
                "type": "open_ended",
                "field": "prior_episodes"
            }
        ]
    
    def start_assessment(self) -> Dict[str, Any]:
        """Start the concern assessment"""
        self.current_question = 0
        return {
            "status": "started",
            "question": self.questions[0],
            "progress": f"1/{len(self.questions)}"
        }
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process user response and get next question"""
        if self.current_question >= len(self.questions):
            return {"error": "Assessment already completed"}
        
        # Store the response
        current_q = self.questions[self.current_question]
        setattr(self.data, current_q["field"], response)
        
        self.current_question += 1
        
        # Check if assessment is complete
        if self.current_question >= len(self.questions):
            self.data.completion_timestamp = datetime.now()
            return {
                "status": "completed",
                "data": self.data.dict(),
                "summary": self._generate_summary()
            }
        
        # Return next question
        return {
            "status": "question",
            "question": self.questions[self.current_question],
            "progress": f"{self.current_question + 1}/{len(self.questions)}"
        }
    
    def _generate_summary(self) -> str:
        """Generate a summary of collected data"""
        summary_parts = []
        
        if self.data.presenting_concern:
            summary_parts.append(f"Main Concern: {self.data.presenting_concern}")
        if self.data.onset_timing:
            summary_parts.append(f"Onset: {self.data.onset_timing}")
        if self.data.duration:
            summary_parts.append(f"Duration: {self.data.duration}")
        if self.data.severity:
            summary_parts.append(f"Severity: {self.data.severity}/10")
        if self.data.frequency:
            summary_parts.append(f"Frequency: {self.data.frequency}")
        if self.data.triggers:
            summary_parts.append(f"Triggers: {self.data.triggers}")
        if self.data.impact_work:
            summary_parts.append(f"Work Impact: {self.data.impact_work}")
        if self.data.impact_relationships:
            summary_parts.append(f"Relationship Impact: {self.data.impact_relationships}")
        if self.data.prior_episodes:
            summary_parts.append(f"Prior Episodes: {self.data.prior_episodes}")
        
        return "; ".join(summary_parts) if summary_parts else "No information collected"

# Global instance
_concern_tool = ConcernTool()

def ask_concern(action: str, **kwargs) -> Dict[str, Any]:
    """Tool function for concern collection"""
    try:
        if action == "start":
            return _concern_tool.start_assessment()
        elif action == "respond":
            response = kwargs.get("response")
            if not response:
                return {"error": "response is required"}
            return _concern_tool.process_response(response)
        elif action == "get_data":
            return _concern_tool.data.dict()
        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"Error in ask_concern: {e}")
        return {"error": f"Tool execution failed: {str(e)}"}

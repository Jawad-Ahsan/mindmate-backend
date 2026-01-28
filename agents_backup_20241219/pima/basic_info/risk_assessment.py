import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class QuestionType(Enum):
    OPEN_ENDED = "open_ended"
    YES_NO = "yes_no"
    MCQ = "mcq"
    SCALE = "scale"

@dataclass
class QuestionOption:
    value: str
    display: str

@dataclass
class Question:
    id: str
    text: str
    type: QuestionType
    options: List[QuestionOption] = None
    allow_free_text: bool = True
    required: bool = True
    follow_up_questions: Dict[str, str] = None

@dataclass
class Response:
    question_id: str
    selected_option: str = None
    free_text: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class RiskAssessmentData:
    # Safety/Risk Assessment Fields
    suicide_ideation: bool = None
    suicide_plan: str = None
    suicide_intent: bool = None
    past_attempts: str = None
    self_harm_history: str = None
    homicidal_thoughts: bool = None
    access_means: str = None
    protective_factors: str = None
    
    # Assessment results
    risk_level: RiskLevel = None
    risk_value: float = None
    risk_reason: str = None
    assessment_timestamp: datetime = None

@dataclass
class RiskAssessmentResult:
    risk_level: RiskLevel
    risk_value: float
    reason: str

class RiskAssessmentChatbot:
    """
    Risk assessment chatbot focusing on suicide and safety evaluation
    with semantic analysis and intelligent question flow.
    """
    
    def __init__(self, llm_client=None, max_questions: int = 8):
        self.llm_client = llm_client
        self.max_questions = max_questions
        self.current_question_count = 0
        self.conversation_history: List[Dict] = []
        self.responses: Dict[str, Response] = {}
        self.data = RiskAssessmentData()
        self.presenting_concern_data = None  # Will be populated from main chatbot
        
        # Risk keywords for semantic analysis
        self._init_risk_keywords()
        self._init_questions()
    
    def _init_risk_keywords(self):
        """Initialize keyword sets for semantic risk analysis"""
        self.suicide_keywords = {
            'high_risk': [
                'kill myself', 'end my life', 'suicide', 'want to die', 'better off dead',
                'no point living', 'end it all', 'take my own life', 'not worth living'
            ],
            'moderate_risk': [
                'hopeless', 'worthless', 'burden', 'trapped', 'no way out', 'give up',
                'pointless', 'empty', 'numb', 'disappear', 'escape'
            ]
        }
        
        self.self_harm_keywords = [
            'cut myself', 'hurt myself', 'self harm', 'cutting', 'burning myself',
            'hitting myself', 'scratching', 'self injury'
        ]
        
        self.violence_keywords = [
            'hurt others', 'kill someone', 'violence', 'revenge', 'get back at',
            'make them pay', 'harm others', 'dangerous thoughts'
        ]
        
        self.protective_keywords = [
            'family', 'children', 'pets', 'friends', 'hope', 'future', 'goals',
            'religion', 'therapy', 'support', 'love', 'responsibility'
        ]
    
    def _init_questions(self):
        """Initialize risk assessment questions with intelligent flow"""
        self.questions = {
            'safety_screen': Question(
                id='safety_screen',
                text="I need to ask some important questions about your safety and wellbeing. Have you had any thoughts about wanting to hurt yourself or end your life?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                required=True
            ),
            
            'suicide_ideation': Question(
                id='suicide_ideation',
                text="Can you tell me more about these thoughts? When did they start?",
                type=QuestionType.OPEN_ENDED,
                allow_free_text=True,
                required=True
            ),
            
            'suicide_plan': Question(
                id='suicide_plan',
                text="Have you thought about how you might hurt yourself or made any specific plans?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "Can you tell me about these plans? This helps me understand how to best support you."
                }
            ),
            
            'suicide_intent': Question(
                id='suicide_intent',
                text="Do you intend to act on these thoughts in the near future?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No"),
                    QuestionOption("unsure", "I'm not sure")
                ],
                allow_free_text=True,
                required=True
            ),
            
            'past_attempts': Question(
                id='past_attempts',
                text="Have you ever tried to hurt yourself or attempt suicide in the past?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "When was this, and what happened? This information helps me provide better support."
                }
            ),
            
            'self_harm_current': Question(
                id='self_harm_current',
                text="Are you currently hurting yourself in other ways, such as cutting, burning, or hitting yourself?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "Can you tell me about this? How often does this happen?"
                }
            ),
            
            'homicidal_thoughts': Question(
                id='homicidal_thoughts',
                text="Have you had thoughts about wanting to hurt someone else?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "Can you tell me more about these thoughts? Do you have someone specific in mind?"
                }
            ),
            
            'protective_factors': Question(
                id='protective_factors',
                text="What are some things in your life that give you hope or reasons to keep going? This could be family, friends, pets, goals, or beliefs.",
                type=QuestionType.OPEN_ENDED,
                allow_free_text=True,
                required=True
            ),
            
            'access_means': Question(
                id='access_means',
                text="Do you have access to things that could be used to hurt yourself or others, such as medications, weapons, or other means?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "What do you have access to? Is there someone who could help secure these items?"
                }
            )
        }
    
    def set_presenting_concern_data(self, presenting_data: str):
        """Set the presenting concern data for risk analysis"""
        self.presenting_concern_data = presenting_data
    
    def _analyze_presenting_concern_risk(self) -> float:
        """Analyze presenting concern text for risk indicators"""
        if not self.presenting_concern_data:
            return 0.0
        
        text = self.presenting_concern_data.lower()
        risk_score = 0.0
        
        # Check for high-risk suicide keywords
        for keyword in self.suicide_keywords['high_risk']:
            if keyword in text:
                risk_score += 0.8
                logger.warning(f"High-risk keyword detected: {keyword}")
        
        # Check for moderate-risk keywords
        for keyword in self.suicide_keywords['moderate_risk']:
            if keyword in text:
                risk_score += 0.3
        
        # Check for self-harm keywords
        for keyword in self.self_harm_keywords:
            if keyword in text:
                risk_score += 0.6
        
        # Check for violence keywords
        for keyword in self.violence_keywords:
            if keyword in text:
                risk_score += 0.7
        
        # Reduce score for protective factors
        for keyword in self.protective_keywords:
            if keyword in text:
                risk_score -= 0.2
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def _should_skip_remaining_questions(self) -> bool:
        """Determine if remaining questions should be skipped based on responses"""
        safety_response = self.responses.get('safety_screen')
        if safety_response and safety_response.selected_option == 'no':
            # If no suicide ideation, skip detailed suicide questions
            return True
        return False
    
    def _get_next_question(self) -> Optional[Question]:
        """Get next question based on conversation flow and responses"""
        if self.current_question_count >= self.max_questions:
            return None
        
        # Always start with safety screen
        if not self.responses.get('safety_screen'):
            return self.questions['safety_screen']
        
        # If no safety concerns indicated, skip to protective factors and access means
        if self._should_skip_remaining_questions():
            if not self.responses.get('homicidal_thoughts'):
                return self.questions['homicidal_thoughts']
            elif not self.responses.get('protective_factors'):
                return self.questions['protective_factors']
            elif not self.responses.get('access_means'):
                return self.questions['access_means']
            else:
                return None
        
        # Full assessment flow for those with safety concerns
        if not self.responses.get('suicide_ideation'):
            return self.questions['suicide_ideation']
        
        if not self.responses.get('suicide_plan'):
            return self.questions['suicide_plan']
        
        if not self.responses.get('suicide_intent'):
            return self.questions['suicide_intent']
        
        if not self.responses.get('past_attempts'):
            return self.questions['past_attempts']
        
        if not self.responses.get('self_harm_current'):
            return self.questions['self_harm_current']
        
        if not self.responses.get('homicidal_thoughts'):
            return self.questions['homicidal_thoughts']
        
        if not self.responses.get('protective_factors'):
            return self.questions['protective_factors']
        
        if not self.responses.get('access_means'):
            return self.questions['access_means']
        
        return None
    
    def start_assessment(self) -> Dict:
        """Start the risk assessment"""
        self.conversation_history.append({
            'type': 'system',
            'message': "I need to ask some important questions about your safety and wellbeing to ensure you get the appropriate care.",
            'timestamp': datetime.now().isoformat()
        })
        
        question = self._get_next_question()
        if question:
            return self._format_question_response(question)
        return {'status': 'error', 'message': 'Unable to start assessment'}
    
    def _format_question_response(self, question: Question) -> Dict:
        """Format question for response"""
        response = {
            'question_id': question.id,
            'question': question.text,
            'type': question.type.value,
            'allow_free_text': question.allow_free_text,
            'question_number': self.current_question_count + 1,
            'max_questions': self.max_questions
        }
        
        if question.options:
            response['options'] = [{'value': opt.value, 'display': opt.display} for opt in question.options]
        
        return response
    
    def process_response(self, question_id: str, selected_option: str = None, free_text: str = None) -> Dict:
        """Process user response and return next question or completion"""
        
        if not selected_option and not free_text:
            return {'status': 'error', 'message': 'Please provide a response'}
        
        # Store response
        response = Response(
            question_id=question_id,
            selected_option=selected_option,
            free_text=free_text
        )
        self.responses[question_id] = response
        
        # Update conversation history
        self.conversation_history.append({
            'type': 'user_response',
            'question_id': question_id,
            'selected_option': selected_option,
            'free_text': free_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update data structure
        self._update_data_structure(question_id, response)
        
        self.current_question_count += 1
        
        # Check for follow-up questions
        current_question = self.questions.get(question_id)
        if (current_question and current_question.follow_up_questions and 
            selected_option in current_question.follow_up_questions):
            
            follow_up_text = current_question.follow_up_questions[selected_option]
            return {
                'type': 'follow_up',
                'question': follow_up_text,
                'question_id': f"{question_id}_followup",
                'allow_free_text': True
            }
        
        # Get next question
        next_question = self._get_next_question()
        
        if next_question and self.current_question_count < self.max_questions:
            return self._format_question_response(next_question)
        else:
            # Assessment complete - calculate risk
            risk_result = self.calculate_risk_level()
            return {
                'status': 'complete',
                'message': 'Risk assessment completed.',
                'risk_assessment': {
                    'risk_level': risk_result.risk_level.value,
                    'risk_value': risk_result.risk_value,
                    'reason': risk_result.reason
                }
            }
    
    def _update_data_structure(self, question_id: str, response: Response):
        """Update the RiskAssessmentData structure"""
        value = response.free_text or response.selected_option
        
        if question_id == 'safety_screen':
            self.data.suicide_ideation = (response.selected_option == 'yes')
        elif question_id == 'suicide_ideation':
            if self.data.suicide_ideation is None:
                self.data.suicide_ideation = True
        elif question_id == 'suicide_plan':
            self.data.suicide_plan = value
        elif question_id == 'suicide_intent':
            self.data.suicide_intent = (response.selected_option == 'yes')
        elif question_id == 'past_attempts':
            self.data.past_attempts = value
        elif question_id == 'self_harm_current':
            self.data.self_harm_history = value
        elif question_id == 'homicidal_thoughts':
            self.data.homicidal_thoughts = (response.selected_option == 'yes')
        elif question_id == 'protective_factors':
            self.data.protective_factors = value
        elif question_id == 'access_means':
            self.data.access_means = value
        
        # Handle follow-up responses
        if 'followup' in question_id:
            base_question = question_id.replace('_followup', '')
            if base_question == 'suicide_plan':
                self.data.suicide_plan = f"{self.data.suicide_plan}. Details: {value}"
            elif base_question == 'past_attempts':
                self.data.past_attempts = f"{self.data.past_attempts}. Details: {value}"
            elif base_question == 'self_harm_current':
                self.data.self_harm_history = f"{self.data.self_harm_history}. Details: {value}"
            elif base_question == 'homicidal_thoughts':
                current = self.data.homicidal_thoughts or False
                self.data.homicidal_thoughts = f"{current}. Details: {value}"
            elif base_question == 'access_means':
                self.data.access_means = f"{self.data.access_means}. Details: {value}"
    
    def calculate_risk_level(self) -> RiskAssessmentResult:
        """
        Calculate comprehensive risk level using semantic analysis
        Returns risk level (0-1) and categorization
        """
        risk_score = 0.0
        risk_factors = []
        
        # 1. Analyze presenting concern (20% weight)
        presenting_risk = self._analyze_presenting_concern_risk()
        risk_score += presenting_risk * 0.2
        if presenting_risk > 0.3:
            risk_factors.append("concerning language in presenting concern")
        
        # 2. Current suicide ideation (25% weight)
        if self.data.suicide_ideation:
            risk_score += 0.25
            risk_factors.append("current suicidal thoughts")
        
        # 3. Suicide plan (20% weight)
        if self.data.suicide_plan:
            plan_text = str(self.data.suicide_plan).lower()
            if any(word in plan_text for word in ['yes', 'plan', 'method', 'how']):
                risk_score += 0.20
                risk_factors.append("specific suicide plan")
        
        # 4. Intent to act (15% weight)
        if self.data.suicide_intent:
            risk_score += 0.15
            risk_factors.append("intent to act on thoughts")
        
        # 5. Past attempts (10% weight)
        if self.data.past_attempts:
            attempt_text = str(self.data.past_attempts).lower()
            if any(word in attempt_text for word in ['yes', 'tried', 'attempted']):
                risk_score += 0.10
                risk_factors.append("history of suicide attempts")
        
        # 6. Current self-harm (8% weight)
        if self.data.self_harm_history:
            harm_text = str(self.data.self_harm_history).lower()
            if any(word in harm_text for word in ['yes', 'cutting', 'burning', 'hurt']):
                risk_score += 0.08
                risk_factors.append("current self-harm behavior")
        
        # 7. Homicidal thoughts (7% weight)
        if self.data.homicidal_thoughts:
            risk_score += 0.07
            risk_factors.append("thoughts of harming others")
        
        # 8. Access to means (5% weight)
        if self.data.access_means:
            access_text = str(self.data.access_means).lower()
            if any(word in access_text for word in ['yes', 'have', 'access', 'weapon', 'medication']):
                risk_score += 0.05
                risk_factors.append("access to lethal means")
        
        # Protective factors reduce risk (up to -0.1)
        if self.data.protective_factors:
            protective_text = str(self.data.protective_factors).lower()
            protective_count = sum(1 for keyword in self.protective_keywords if keyword in protective_text)
            risk_reduction = min(protective_count * 0.02, 0.1)
            risk_score -= risk_reduction
        
        # Ensure risk score is between 0 and 1
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.2:
            risk_level = RiskLevel.MODERATE
        else:
            risk_level = RiskLevel.LOW
        
        # Generate reason
        if not risk_factors:
            reason = f"Risk assessment shows {risk_level.value} risk based on responses indicating minimal safety concerns. No significant risk factors identified in current presentation."
        else:
            factor_text = ", ".join(risk_factors[:3])  # Limit to top 3 factors
            reason = f"Risk level {risk_level.value} (score: {risk_score:.2f}) based on: {factor_text}. "
            
            if len(risk_factors) > 3:
                reason += f"Additional factors considered. "
            
            if self.data.protective_factors:
                reason += f"Protective factors noted which help mitigate risk."
            else:
                reason += f"Limited protective factors identified."
        
        # Update data structure
        self.data.risk_level = risk_level
        self.data.risk_value = risk_score
        self.data.risk_reason = reason
        self.data.assessment_timestamp = datetime.now()
        
        return RiskAssessmentResult(
            risk_level=risk_level,
            risk_value=risk_score,
            reason=reason
        )
    
    def export_assessment_json(self) -> str:
        """Export risk assessment data as JSON"""
        export_data = {
            'risk_assessment_data': asdict(self.data),
            'conversation_metadata': {
                'total_questions': self.current_question_count,
                'conversation_history': self.conversation_history
            },
            'export_timestamp': datetime.now().isoformat()
        }
        return json.dumps(export_data, indent=2, default=str)


# Usage example
def demo_risk_assessment():
    """Demonstrate the risk assessment functionality"""
    print("Risk Assessment Chatbot Demo")
    print("=" * 40)
    
    # Initialize risk assessment
    risk_bot = RiskAssessmentChatbot(max_questions=8)
    
    # Set presenting concern data for analysis
    presenting_concern = "I feel hopeless and have been thinking about ending my life. Nothing seems worth it anymore."
    risk_bot.set_presenting_concern_data(presenting_concern)
    
    # Start assessment
    response = risk_bot.start_assessment()
    print(f"\nBot: {response.get('question')}")
    
    # Simulate responses for demo
    demo_responses = [
        ("safety_screen", "yes", "Yes, I have been having these thoughts"),
        ("suicide_ideation", None, "Started about two weeks ago when I lost my job. They're getting stronger."),
        ("suicide_plan", "yes", "I've thought about it but haven't made specific plans"),
        ("suicide_intent", "unsure", "I'm not sure, sometimes I feel like I might"),
        ("past_attempts", "no", "No, never tried before"),
        ("self_harm_current", "no", "No cutting or anything like that"),
        ("homicidal_thoughts", "no", "No thoughts about hurting others"),
        ("protective_factors", None, "My family, especially my daughter. I don't want to hurt her.")
    ]
    
    for question_id, selected, free_text in demo_responses:
        print(f"\nUser Response: {selected or free_text}")
        
        response = risk_bot.process_response(question_id, selected, free_text)
        
        if response.get('status') == 'complete':
            risk_data = response.get('risk_assessment')
            print(f"\n{'='*50}")
            print("RISK ASSESSMENT COMPLETE")
            print("="*50)
            print(f"Risk Level: {risk_data['risk_level'].upper()}")
            print(f"Risk Score: {risk_data['risk_value']:.2f}")
            print(f"Reasoning: {risk_data['reason']}")
            break
        elif response.get('type') == 'follow_up':
            print(f"\nBot (Follow-up): {response.get('question')}")
        else:
            print(f"\nBot: {response.get('question')}")

if __name__ == "__main__":
    demo_risk_assessment()
    
#export all
__all__ = [
    'RiskAssessmentChatbot',
    'RiskAssessmentData',
    'RiskAssessmentResult',
    'RiskLevel',
    'QuestionType',
    'QuestionOption',
    'Question',
    'Response'
]
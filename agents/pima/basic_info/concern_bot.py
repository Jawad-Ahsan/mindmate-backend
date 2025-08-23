import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    follow_up_questions: Dict[str, str] = None  # Value -> follow-up question

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
class PresentingConcernData:
    # Core fields from your schema
    presenting_concern: str = None
    presenting_onset: str = None
    
    hpi_onset: str = None
    hpi_duration: str = None
    hpi_course: str = None
    hpi_severity: int = None
    hpi_frequency: str = None
    hpi_triggers: str = None
    hpi_impact_work: str = None
    hpi_impact_relationships: str = None
    hpi_prior_episodes: str = None
    
    function_ADL: str = None
    social_activities: str = None
    
    # Additional metadata
    conversation_complete: bool = False
    total_questions_asked: int = 0
    completion_timestamp: datetime = None

class PresentingConcernChatbot:
    """
    Intelligent chatbot for gathering presenting concern information through 
    conversational questions with context awareness and goal tracking.
    """
    
    def __init__(self, llm_client=None, max_questions: int = 10):
        self.llm_client = llm_client
        self.max_questions = max_questions
        self.current_question_count = 0
        self.conversation_history: List[Dict] = []
        self.responses: Dict[str, Response] = {}
        self.data = PresentingConcernData()
        self.goal_completion = {}
        
        # Initialize goal tracking
        self._init_goals()
        
        # Define the question flow
        self._init_question_flow()
    
    def _init_goals(self):
        """Initialize goal tracking for information gathering"""
        self.goals = {
            'primary_concern': {'completed': False, 'priority': 1, 'required': True},
            'onset_timing': {'completed': False, 'priority': 2, 'required': True},
            'severity_assessment': {'completed': False, 'priority': 3, 'required': True},
            'frequency_pattern': {'completed': False, 'priority': 4, 'required': True},
            'triggers_factors': {'completed': False, 'priority': 5, 'required': False},
            'functional_impact': {'completed': False, 'priority': 6, 'required': True},
            'prior_episodes': {'completed': False, 'priority': 7, 'required': False},
            'course_progression': {'completed': False, 'priority': 8, 'required': False}
        }
    
    def _init_question_flow(self):
        """Initialize the dynamic question flow"""
        self.questions = {
            'initial_concern': Question(
                id='initial_concern',
                text="What brings you in today? Please describe your main concern in your own words.",
                type=QuestionType.OPEN_ENDED,
                allow_free_text=True,
                required=True
            ),
            
            'concern_details': Question(
                id='concern_details',
                text="Can you tell me more about this {concern}? When did you first notice it?",
                type=QuestionType.OPEN_ENDED,
                allow_free_text=True,
                required=True
            ),
            
            'onset_timing': Question(
                id='onset_timing',
                text="When did this problem start?",
                type=QuestionType.MCQ,
                options=[
                    QuestionOption("today", "Today"),
                    QuestionOption("this_week", "This week"),
                    QuestionOption("this_month", "This month"),
                    QuestionOption("longer", "Longer than a month")
                ],
                allow_free_text=True,
                required=True
            ),
            
            'severity_scale': Question(
                id='severity_scale',
                text="you described your main concern as \"{concern}\" On a scale of 1-10, how would you rate its severity? (1 = very mild, 10 = extremely severe)",
                type=QuestionType.SCALE,
                allow_free_text=True,
                required=True
            ),
            
            'frequency_pattern': Question(
                id='frequency_pattern',
                text="How often do you experience this {concern}?",
                type=QuestionType.MCQ,
                options=[
                    QuestionOption("constant", "Constant/All the time"),
                    QuestionOption("daily", "Daily"),
                    QuestionOption("weekly", "Weekly"),
                    QuestionOption("occasional", "Occasionally")
                ],
                allow_free_text=True,
                required=True
            ),
            
            'triggers': Question(
                id='triggers',
                text="Is there anything that makes your {concern} worse or better?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "What specifically makes it worse or better?"
                }
            ),
            
            'functional_impact': Question(
                id='functional_impact',
                text="How is this {concern} affecting your daily activities?",
                type=QuestionType.MCQ,
                options=[
                    QuestionOption("no_impact", "No impact on daily activities"),
                    QuestionOption("mild_impact", "Mild impact - can do most things"),
                    QuestionOption("moderate_impact", "Moderate impact - some limitations"),
                    QuestionOption("severe_impact", "Severe impact - significant limitations")
                ],
                allow_free_text=True,
                required=True
            ),
            
            'work_impact': Question(
                id='work_impact',
                text="Is this affecting your work or school performance?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "How specifically is it affecting your work/school?"
                }
            ),
            
            'social_impact': Question(
                id='social_impact',
                text="Has this {concern} affected your relationships or social activities?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "In what ways has it affected your social life?"
                }
            ),
            
            'prior_episodes': Question(
                id='prior_episodes',
                text="Have you experienced anything like this {concern} before?",
                type=QuestionType.YES_NO,
                options=[
                    QuestionOption("yes", "Yes"),
                    QuestionOption("no", "No")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "yes": "When did it happen before and was it similar?"
                }
            )
        }
    
    def _update_goals(self, question_id: str, response: Response):
        """Update goal completion based on response"""
        goal_mapping = {
            'initial_concern': 'primary_concern',
            'concern_details': 'primary_concern',
            'onset_timing': 'onset_timing',
            'severity_scale': 'severity_assessment',
            'frequency_pattern': 'frequency_pattern',
            'triggers': 'triggers_factors',
            'functional_impact': 'functional_impact',
            'work_impact': 'functional_impact',
            'social_impact': 'functional_impact',
            'prior_episodes': 'prior_episodes'
        }
        
        if question_id in goal_mapping:
            goal_key = goal_mapping[question_id]
            if response.selected_option or response.free_text:
                self.goals[goal_key]['completed'] = True
                logger.info(f"Goal '{goal_key}' marked as completed")
    
    def _extract_concern_keyword(self) -> str:
        """Extract the main concern keyword for dynamic questions using LLM if available"""
        if not self.data.presenting_concern:
            return "concern"
            
        if self.llm_client:
            try:
                prompt = f"""
                Extract the most relevant medical keyword or symptom from this concern:
                "{self.data.presenting_concern}"
                
                Rules:
                1. Return only ONE word or a phrase that best represents the main medical concern or symptom
                2. Ensure the word is a medical symptom, condition, or recognizable health issue
                3. Return the word in lowercase
                4. Do not include any punctuation or explanation
                
                Example inputs and outputs:
                "I've been having severe headaches" -> "headaches"
                "My anxiety is getting worse lately" -> "anxiety"
                "I can't sleep and feel depressed" -> "depression"
                """
                
                keyword = self.llm_client.generate(
                    prompt,
                    system_prompt="You are a medical keyword extractor. Respond with exactly one lowercase word.",
                    max_tokens=10
                ).strip().lower()
                
                return keyword if keyword else "concern"
            except Exception as e:
                logger.warning(f"LLM keyword extraction failed: {e}")
                # Fall back to basic extraction
                pass
        
        # Basic fallback extraction if LLM fails or is not available
        concern = self.data.presenting_concern.lower()
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'have', 'am', 'is', 'are']
        words = [w for w in concern.split() if w not in stop_words and len(w) > 2]
        return words[0] if words else "concern"
    
    def _get_next_question(self) -> Optional[Question]:
        """Determine the next question based on conversation history and goals"""
        if self.current_question_count >= self.max_questions:
            return None
        
        # Question flow logic
        if not self.responses.get('initial_concern'):
            return self.questions['initial_concern']
        
        if not self.responses.get('concern_details'):
            question = self.questions['concern_details']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('onset_timing'):
            return self.questions['onset_timing']
        
        if not self.responses.get('severity_scale'):
            question = self.questions['severity_scale']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('frequency_pattern'):
            question = self.questions['frequency_pattern']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('triggers'):
            question = self.questions['triggers']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('functional_impact'):
            question = self.questions['functional_impact']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('work_impact'):
            return self.questions['work_impact']
        
        if not self.responses.get('social_impact'):
            question = self.questions['social_impact']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        if not self.responses.get('prior_episodes'):
            question = self.questions['prior_episodes']
            concern = self._extract_concern_keyword()
            question.text = question.text.format(concern=concern)
            return question
        
        return None
    
    def start_conversation(self) -> Dict:
        """Start the conversation and return the first question"""
        self.conversation_history.append({
            'type': 'system',
            'message': "Hello! I'm here to understand your health concern better. I'll ask you some questions to get a complete picture.",
            'timestamp': datetime.now().isoformat()
        })
        
        question = self._get_next_question()
        if question:
            return self._format_question_response(question)
        return {'status': 'error', 'message': 'Unable to start conversation'}
    
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
        
        if question.type == QuestionType.SCALE:
            response['scale'] = {'min': 1, 'max': 10}
        
        return response
    
    def process_response(self, question_id: str, selected_option: str = None, free_text: str = None) -> Dict:
        """Process user response and return next question or completion"""
        
        # Validate response
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
        
        # Update goals
        self._update_goals(question_id, response)
        
        # Increment question count
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
            # Conversation complete
            self.data.conversation_complete = True
            self.data.total_questions_asked = self.current_question_count
            self.data.completion_timestamp = datetime.now()
            
            return {
                'status': 'complete',
                'message': 'Thank you! I have gathered enough information about your concern.',
                'summary': self._get_goal_completion_summary()
            }
    
    def _update_data_structure(self, question_id: str, response: Response):
        """Update the PresentingConcernData structure"""
        value = response.free_text or response.selected_option
        
        if question_id == 'initial_concern':
            self.data.presenting_concern = value
        elif question_id == 'concern_details':
            if self.data.presenting_concern:
                self.data.presenting_concern += f" - {value}"
            else:
                self.data.presenting_concern = value
            self.data.presenting_onset = value
        elif question_id == 'onset_timing':
            self.data.hpi_onset = value
            self.data.hpi_duration = value
        elif question_id == 'severity_scale':
            try:
                self.data.hpi_severity = int(response.selected_option or response.free_text or 0)
            except (ValueError, TypeError):
                self.data.hpi_severity = None
        elif question_id == 'frequency_pattern':
            self.data.hpi_frequency = value
        elif question_id == 'triggers':
            self.data.hpi_triggers = value
        elif question_id == 'functional_impact':
            self.data.function_ADL = value
        elif question_id == 'work_impact':
            self.data.hpi_impact_work = value
        elif question_id == 'social_impact':
            self.data.hpi_impact_relationships = value
            self.data.social_activities = value
        elif question_id == 'prior_episodes':
            self.data.hpi_prior_episodes = value
        
        # Handle follow-up responses
        if 'followup' in question_id:
            base_question = question_id.replace('_followup', '')
            if base_question == 'triggers':
                self.data.hpi_triggers = f"{self.data.hpi_triggers}. Details: {value}"
            elif base_question == 'work_impact':
                self.data.hpi_impact_work = f"{self.data.hpi_impact_work}. Details: {value}"
            elif base_question == 'social_impact':
                self.data.hpi_impact_relationships = f"{self.data.hpi_impact_relationships}. Details: {value}"
            elif base_question == 'prior_episodes':
                self.data.hpi_prior_episodes = f"{self.data.hpi_prior_episodes}. Details: {value}"
    
    def _get_goal_completion_summary(self) -> Dict:
        """Get summary of goal completion"""
        completed = sum(1 for goal in self.goals.values() if goal['completed'])
        total = len(self.goals)
        
        return {
            'goals_completed': completed,
            'total_goals': total,
            'completion_percentage': round((completed / total) * 100, 1),
            'completed_goals': [name for name, goal in self.goals.items() if goal['completed']],
            'missing_goals': [name for name, goal in self.goals.items() if not goal['completed'] and goal.get('required', False)]
        }
    
    def export_as_json(self) -> str:
        """Export collected data as JSON"""
        export_data = {
            'presenting_concern_data': asdict(self.data),
            'conversation_metadata': {
                'total_questions': self.current_question_count,
                'conversation_complete': self.data.conversation_complete,
                'goal_completion': self._get_goal_completion_summary(),
                'conversation_history': self.conversation_history
            },
            'export_timestamp': datetime.now().isoformat()
        }
        return json.dumps(export_data, indent=2, default=str)
    
    def create_primary_concern_report(self) -> str:
        """Create a comprehensive clinical report using LLM if available"""
        
        # Collect all relevant information
        report_data = {
            'concern': self.data.presenting_concern,
            'onset': self.data.hpi_onset,
            'duration': self.data.hpi_duration,
            'severity': self.data.hpi_severity,
            'frequency': self.data.hpi_frequency,
            'triggers': self.data.hpi_triggers,
            'functional_impact': self.data.function_ADL,
            'work_impact': self.data.hpi_impact_work,
            'social_impact': self.data.hpi_impact_relationships,
            'prior_episodes': self.data.hpi_prior_episodes
        }
        
        if self.llm_client:
            return self._generate_llm_report(report_data)
        else:
            return self._generate_template_report(report_data)
    
    def _generate_llm_report(self, data: Dict) -> str:
        """Generate report using LLM"""
        prompt = f"""
        Create a professional clinical presenting concern report based on the following patient information:
        
        Primary Concern: {data['concern']}
        Onset: {data['onset']}
        Duration: {data['duration']}
        Severity (1-10): {data['severity']}
        Frequency: {data['frequency']}
        Triggers/Factors: {data['triggers']}
        Functional Impact: {data['functional_impact']}
        Work Impact: {data['work_impact']}
        Social Impact: {data['social_impact']}
        Prior Episodes: {data['prior_episodes']}
        
        Format the report as a professional clinical assessment in the style:
        "Patient presents with [concern description]. The [symptom/concern] reportedly began [onset details] and has been ongoing for [duration]. Patient rates the severity as [X/10]. The [concern] occurs [frequency] and is [triggered by/associated with]. 
        
        Functionally, the patient reports [impact on daily activities]. Work/academic performance has been [impacted/not impacted] with [details]. Social relationships and activities have been [affected/unaffected] [details].
        
        [Include prior episodes information if relevant]."
        
        Keep it concise, professional, and clinically relevant.
        """
        
        try:
            system_prompt = "You are a medical professional writing clinical documentation. Be precise, professional, and use appropriate medical terminology."
            report = self.llm_client.generate(prompt, system_prompt=system_prompt, max_tokens=600)
            return report
        except Exception as e:
            logger.error(f"LLM report generation failed: {e}")
            return self._generate_template_report(data)
    
    def _generate_template_report(self, data: Dict) -> str:
        """Generate report using template"""
        concern = data.get('concern', 'unspecified concern')
        onset = data.get('onset', 'unknown onset')
        severity = data.get('severity', 'unrated')
        frequency = data.get('frequency', 'unspecified frequency')
        
        report = f"PRESENTING CONCERN REPORT\n"
        report += f"========================\n\n"
        report += f"Patient presents with {concern}. "
        
        if onset and onset != 'unknown onset':
            report += f"The concern reportedly began {onset}. "
        
        if severity and str(severity) != 'unrated':
            report += f"Patient rates the severity as {severity}/10. "
        
        if frequency and frequency != 'unspecified frequency':
            report += f"The concern occurs {frequency}. "
        
        if data.get('triggers'):
            report += f"Patient reports it is triggered by or associated with: {data['triggers']}. "
        
        if data.get('functional_impact'):
            report += f"Functionally, the patient reports: {data['functional_impact']}. "
        
        if data.get('work_impact'):
            report += f"Work/academic impact: {data['work_impact']}. "
        
        if data.get('social_impact'):
            report += f"Social impact: {data['social_impact']}. "
        
        if data.get('prior_episodes'):
            report += f"Prior episodes: {data['prior_episodes']}. "
        
        report += f"\n\nReport generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return report
    
    def get_conversation_status(self) -> Dict:
        """Get current status of the conversation"""
        return {
            'questions_asked': self.current_question_count,
            'max_questions': self.max_questions,
            'conversation_complete': self.data.conversation_complete,
            'goal_completion': self._get_goal_completion_summary(),
            'next_question_available': self._get_next_question() is not None,
            'data_completeness': self._calculate_data_completeness()
        }
    
    def _calculate_data_completeness(self) -> Dict:
        """Calculate how complete the collected data is"""
        fields = [
            'presenting_concern', 'hpi_onset', 'hpi_severity', 'hpi_frequency',
            'hpi_triggers', 'function_ADL', 'hpi_impact_work', 'hpi_impact_relationships'
        ]
        
        completed_fields = sum(1 for field in fields if getattr(self.data, field) is not None)
        
        return {
            'completed_fields': completed_fields,
            'total_fields': len(fields),
            'completion_percentage': round((completed_fields / len(fields)) * 100, 1)
        }


# Usage example and testing
def demo_chatbot():
    """Demonstrate the chatbot functionality"""
    print("Medical Concern Chatbot Demo")
    print("=" * 40)
    from agents.llm_client import LLMClient  # Assuming you have an LLM client implementation
    
    llm = LLMClient()
    # Initialize chatbot (without LLM for demo)
    chatbot = PresentingConcernChatbot(llm_client=llm, max_questions=10)

    # Start conversation
    response = chatbot.start_conversation()
    print(f"\nBot: {response.get('question')}")
    
    # Simulate some responses
    demo_responses = [
        ("initial_concern", None, "I've been having severe headaches for the past week"),
        ("concern_details", None, "The headaches started suddenly last Monday morning and they're really intense"),
        ("onset_timing", "this_week", "Started this week, specifically Monday"),
        ("severity_scale", "8", "I'd say it's about an 8 out of 10"),
        ("frequency_pattern", "daily", "I get them every day now"),
        ("triggers", "yes", "Stress and bright lights seem to make them worse"),
        ("functional_impact", "moderate_impact", "I can do some things but it's difficult"),
        ("work_impact", "yes", "Hard to concentrate at work"),
        ("social_impact", "yes", "I've cancelled plans with friends"),
        ("prior_episodes", "no", "Never had headaches this bad before")
    ]
    
    for question_id, selected, free_text in demo_responses:
        print(f"\nUser Response: {selected or free_text}")
        
        response = chatbot.process_response(question_id, selected, free_text)
        
        if response.get('status') == 'complete':
            print(f"\nBot: {response.get('message')}")
            print(f"Summary: {response.get('summary')}")
            break
        elif response.get('type') == 'follow_up':
            print(f"\nBot (Follow-up): {response.get('question')}")
            # Simulate follow-up response
            if 'triggers' in question_id:
                follow_response = chatbot.process_response(f"{question_id}_followup", None, "Stress at work and fluorescent lighting")
                print(f"User Follow-up: Stress at work and fluorescent lighting")
                if follow_response.get('question'):
                    print(f"\nBot: {follow_response.get('question')}")
        else:
            print(f"\nBot: {response.get('question')}")
    
    # Show final report
    print("\n" + "="*50)
    print("FINAL CLINICAL REPORT")
    print("="*50)
    report = chatbot.create_primary_concern_report()
    print(report)
    
    # Show JSON export (truncated for demo)
    print("\n" + "="*50)
    print("JSON EXPORT (Sample)")
    print("="*50)
    json_data = json.loads(chatbot.export_as_json())
    print(f"Concern: {json_data['presenting_concern_data']['presenting_concern']}")
    print(f"Severity: {json_data['presenting_concern_data']['hpi_severity']}")
    print(f"Questions Asked: {json_data['conversation_metadata']['total_questions']}")
    print(f"Completion: {json_data['conversation_metadata']['goal_completion']['completion_percentage']}%")

if __name__ == "__main__":
    demo_chatbot()
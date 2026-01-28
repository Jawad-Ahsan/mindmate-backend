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
                Analyze this patient concern and extract the PRIMARY medical symptom or condition:
                "{self.data.presenting_concern}"

                Instructions:
                1. Identify the main symptom/condition (not secondary effects)
                2. Return ONE word or short phrase (2-3 words max)
                3. Use standard medical terminology when possible
                4. Return in lowercase, no punctuation
                5. Focus on the core issue, not triggers or impacts

                Examples:
                "I've been having severe headaches that won't go away" -> "headaches"
                "My anxiety attacks are happening more frequently" -> "anxiety attacks"
                "I feel depressed and can't get out of bed" -> "depression"
                "I'm having panic attacks when driving" -> "panic attacks"
                "I can't stop worrying about everything" -> "excessive worry"
                "I have intrusive thoughts about contamination" -> "contamination obsessions"

                Primary concern:
                """

                keyword = self.llm_client.generate(
                    prompt,
                    system_prompt="You are a clinical keyword extractor. Return only the primary medical concern, nothing else.",
                    max_tokens=15
                ).strip().lower()

                # Clean up the response
                keyword = re.sub(r'[^\w\s]', '', keyword).strip()

                if keyword and len(keyword) > 2:
                    return keyword
                else:
                    logger.warning(f"LLM returned invalid keyword: '{keyword}'")

            except Exception as e:
                logger.warning(f"LLM keyword extraction failed: {e}")

        # Enhanced fallback extraction
        concern = self.data.presenting_concern.lower()

        # Medical keyword patterns
        medical_keywords = {
            'depression': ['depressed', 'depression', 'sad', 'hopeless', 'worthless'],
            'anxiety': ['anxious', 'anxiety', 'worried', 'nervous', 'panic', 'fear'],
            'insomnia': ['sleep', 'insomnia', 'sleepless', 'tired', 'fatigue'],
            'ptsd': ['trauma', 'ptsd', 'flashbacks', 'nightmares', 'triggered'],
            'ocd': ['obsessive', 'compulsive', 'ocd', 'rituals', 'contamination'],
            'bipolar': ['mood swings', 'manic', 'bipolar', 'elevated mood'],
            'schizophrenia': ['hallucinations', 'delusions', 'psychosis', 'paranoid'],
            'eating': ['eating', 'anorexia', 'bulimia', 'binge', 'weight'],
            'substance': ['alcohol', 'drugs', 'addiction', 'substance', 'withdrawal']
        }

        for condition, keywords in medical_keywords.items():
            for keyword in keywords:
                if keyword in concern:
                    return condition

        # Generic fallback
        stop_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'i', 'have', 'am', 'is', 'are', 'feel', 'feeling']
        words = [w for w in concern.split() if w not in stop_words and len(w) > 3]

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
        """Process user response and return next question or completion with LLM-enhanced understanding"""

        # Validate response
        if not selected_option and not free_text:
            return {'status': 'error', 'message': 'Please provide a response'}

        # Combine selected option and free text for processing
        full_response = free_text or selected_option or ""

        # Use LLM to understand and categorize the response if available
        if self.llm_client and full_response:
            try:
                understanding = self._understand_response_with_llm(question_id, full_response)
                if understanding:
                    # Update response with LLM understanding
                    if understanding.get('categorized_response'):
                        full_response = understanding['categorized_response']
                    if understanding.get('extracted_severity'):
                        selected_option = str(understanding['extracted_severity'])
            except Exception as e:
                logger.warning(f"LLM response understanding failed: {e}")

        # Store response
        response = Response(
            question_id=question_id,
            selected_option=selected_option,
            free_text=full_response
        )
        self.responses[question_id] = response

        # Update conversation history
        self.conversation_history.append({
            'type': 'user_response',
            'question_id': question_id,
            'selected_option': selected_option,
            'free_text': full_response,
            'timestamp': datetime.now().isoformat()
        })

        # Update data structure
        self._update_data_structure(question_id, response)

        # Update goals
        self._update_goals(question_id, response)

        # Increment question count
        self.current_question_count += 1

        # Check for follow-up questions with LLM enhancement
        current_question = self.questions.get(question_id)
        if (current_question and current_question.follow_up_questions and
            selected_option in current_question.follow_up_questions):

            follow_up_text = current_question.follow_up_questions[selected_option]

            # Use LLM to generate more contextual follow-up if needed
            if self.llm_client and len(full_response.split()) > 3:
                try:
                    enhanced_followup = self._generate_contextual_followup(
                        current_question.text, full_response, follow_up_text
                    )
                    if enhanced_followup:
                        follow_up_text = enhanced_followup
                except Exception as e:
                    logger.warning(f"LLM followup enhancement failed: {e}")

            return {
                'type': 'follow_up',
                'question': follow_up_text,
                'question_id': f"{question_id}_followup",
                'allow_free_text': True
            }

        # Use LLM to determine if we need additional clarification
        if self.llm_client and self._needs_clarification(question_id, full_response):
            clarification_question = self._generate_clarification_question(question_id, full_response)
            if clarification_question:
                return {
                    'type': 'clarification',
                    'question': clarification_question,
                    'question_id': f"{question_id}_clarification",
                    'allow_free_text': True
                }

        # Get next question with LLM prioritization
        next_question = self._get_next_question_with_llm()

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

    def _understand_response_with_llm(self, question_id: str, response: str) -> Optional[Dict[str, Any]]:
        """Use LLM to understand and categorize user response"""
        if not self.llm_client:
            return None

        try:
            question = self.questions.get(question_id)
            if not question:
                return None

            prompt = f"""
            Analyze this patient response to the question: "{question.text}"

            Patient response: "{response}"

            Task: Extract and structure the key information from this response.

            Return a JSON object with these fields if applicable:
            {{
                "categorized_response": "standardized version of their answer",
                "extracted_severity": "severity score 1-10 if mentioned",
                "key_symptoms": ["list", "of", "mentioned", "symptoms"],
                "emotional_state": "patient's current emotional state",
                "triggers_identified": ["list", "of", "triggers", "mentioned"],
                "functional_impact": "impact on daily functioning",
                "temporal_pattern": "when symptoms occur (constant/daily/weekly/etc)",
                "confidence_level": "your confidence in this analysis (high/medium/low)"
            }}

            Only include fields that are clearly evident in the response. Return valid JSON.
            """

            llm_response = self.llm_client.generate(
                prompt,
                system_prompt="You are a clinical data extractor. Return only valid JSON.",
                max_tokens=200
            )

            # Try to parse JSON response
            try:
                import json
                result = json.loads(llm_response.strip())
                return result
            except json.JSONDecodeError:
                logger.warning(f"LLM returned invalid JSON: {llm_response}")
                return None

        except Exception as e:
            logger.warning(f"LLM response understanding failed: {e}")
            return None

    def _generate_contextual_followup(self, original_question: str, patient_response: str, base_followup: str) -> Optional[str]:
        """Generate more contextual follow-up question using LLM"""
        if not self.llm_client:
            return None

        try:
            prompt = f"""
            Original question: "{original_question}"
            Patient response: "{patient_response}"
            Base follow-up: "{base_followup}"

            Create a more contextual and empathetic follow-up question that:
            1. Acknowledges what the patient just said
            2. Asks for more specific details about their experience
            3. Maintains clinical relevance
            4. Uses natural, conversational language

            Return only the follow-up question, nothing else.
            """

            enhanced_question = self.llm_client.generate(
                prompt,
                system_prompt="You are a clinical interviewer. Create natural, empathetic follow-up questions.",
                max_tokens=100
            ).strip()

            return enhanced_question if enhanced_question else None

        except Exception as e:
            logger.warning(f"LLM followup generation failed: {e}")
            return None

    def _needs_clarification(self, question_id: str, response: str) -> bool:
        """Determine if response needs clarification using LLM"""
        if not self.llm_client:
            return False

        # Basic heuristics for when clarification might be needed
        if len(response.split()) < 3:
            return True
        if any(word in response.lower() for word in ['idk', 'not sure', 'maybe', 'sometimes', 'kinda']):
            return True

        try:
            question = self.questions.get(question_id)
            if not question:
                return False

            prompt = f"""
            Question: "{question.text}"
            Response: "{response}"

            Does this response need clarification or more detail to be clinically useful?
            Consider:
            - Is the response specific enough?
            - Does it directly address the question?
            - Is more context needed?

            Return only "yes" or "no".
            """

            needs_clarification = self.llm_client.generate(
                prompt,
                system_prompt="You are a clinical assessor. Return only 'yes' or 'no'.",
                max_tokens=10
            ).strip().lower()

            return needs_clarification == "yes"

        except Exception as e:
            logger.warning(f"Clarification check failed: {e}")
            return False

    def _generate_clarification_question(self, question_id: str, response: str) -> Optional[str]:
        """Generate clarification question using LLM"""
        if not self.llm_client:
            return None

        try:
            question = self.questions.get(question_id)
            if not question:
                return None

            prompt = f"""
            Original question: "{question.text}"
            Patient response: "{response}"

            The patient's response needs clarification. Create a gentle, natural question that asks for more specific information while acknowledging their original answer.

            Return only the clarification question.
            """

            clarification = self.llm_client.generate(
                prompt,
                system_prompt="You are a clinical interviewer. Create gentle clarification questions.",
                max_tokens=80
            ).strip()

            return clarification if clarification else None

        except Exception as e:
            logger.warning(f"Clarification question generation failed: {e}")
            return None

    def _get_next_question_with_llm(self) -> Optional[Question]:
        """Get next question with LLM prioritization based on conversation context"""
        # First try the basic logic
        basic_question = self._get_next_question()
        if not basic_question or not self.llm_client:
            return basic_question

        try:
            # Get conversation context for LLM
            context = self._build_conversation_context()

            prompt = f"""
            Based on this conversation context, determine what information would be most valuable to collect next:

            CONVERSATION CONTEXT:
            {context}

            COMPLETED GOALS: {', '.join([name for name, goal in self.goals.items() if goal['completed']])}
            REMAINING GOALS: {', '.join([name for name, goal in self.goals.items() if not goal['completed']])}

            Available question types:
            - primary_concern: Get main presenting concern
            - onset_timing: When did symptoms start?
            - severity_assessment: Rate symptom severity
            - frequency_pattern: How often do symptoms occur?
            - triggers_factors: What triggers symptoms?
            - functional_impact: Impact on daily activities
            - prior_episodes: Previous similar episodes?

            Which goal should be prioritized next? Return only the goal name.
            """

            priority_goal = self.llm_client.generate(
                prompt,
                system_prompt="You are a clinical assessment coordinator. Return only the goal name.",
                max_tokens=20
            ).strip().lower()

            # Map goal to question
            goal_question_map = {
                'primary_concern': 'initial_concern',
                'onset_timing': 'onset_timing',
                'severity_assessment': 'severity_scale',
                'frequency_pattern': 'frequency_pattern',
                'triggers_factors': 'triggers',
                'functional_impact': 'functional_impact',
                'prior_episodes': 'prior_episodes'
            }

            if priority_goal in goal_question_map:
                question_id = goal_question_map[priority_goal]
                if question_id in self.questions and not self.responses.get(question_id):
                    return self.questions[question_id]

        except Exception as e:
            logger.warning(f"LLM question prioritization failed: {e}")

        return basic_question

    def _build_conversation_context(self) -> str:
        """Build conversation context for LLM analysis"""
        context_parts = []

        if self.data.presenting_concern:
            context_parts.append(f"Presenting concern: {self.data.presenting_concern}")

        if self.data.hpi_onset:
            context_parts.append(f"Onset: {self.data.hpi_onset}")

        if self.data.hpi_severity:
            context_parts.append(f"Severity: {self.data.hpi_severity}/10")

        if self.data.hpi_frequency:
            context_parts.append(f"Frequency: {self.data.hpi_frequency}")

        if self.data.hpi_triggers:
            context_parts.append(f"Triggers: {self.data.hpi_triggers}")

        if self.data.function_ADL:
            context_parts.append(f"Functional impact: {self.data.function_ADL}")

        recent_responses = []
        for resp in list(self.responses.values())[-3:]:  # Last 3 responses
            recent_responses.append(f"Q: {self.questions.get(resp.question_id, resp.question_id).text[:50]}...")
            recent_responses.append(f"A: {resp.free_text or resp.selected_option}")

        if recent_responses:
            context_parts.append("Recent Q&A:\n" + "\n".join(recent_responses))

        return "\n".join(context_parts) if context_parts else "Initial assessment - no information collected yet"
    
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
            'prior_episodes': self.data.hpi_prior_episodes,
            'conversation_context': self._build_conversation_context(),
            'goal_completion': self._get_goal_completion_summary(),
            'question_count': self.current_question_count
        }

        if self.llm_client:
            return self._generate_enhanced_llm_report(report_data)
        else:
            return self._generate_template_report(report_data)
    
    def _generate_enhanced_llm_report(self, data: Dict) -> str:
        """Generate enhanced report using LLM with conversation context"""
        prompt = f"""
        Create a comprehensive clinical presenting concern report based on the following patient information:

        PRIMARY CONCERN: {data['concern']}
        ONSET: {data['onset']}
        DURATION: {data['duration']}
        SEVERITY: {data['severity']}/10
        FREQUENCY: {data['frequency']}
        TRIGGERS: {data['triggers']}
        FUNCTIONAL IMPACT: {data['functional_impact']}
        WORK IMPACT: {data['work_impact']}
        SOCIAL IMPACT: {data['social_impact']}
        PRIOR EPISODES: {data['prior_episodes']}

        CONVERSATION CONTEXT:
        {data['conversation_context']}

        ASSESSMENT COMPLETENESS:
        Goals completed: {data['goal_completion']['completion_percentage']}%
        Questions asked: {data['question_count']}

        Please write a professional clinical report that includes:

        1. PRESENTING CONCERN SUMMARY (2-3 sentences)
        2. HISTORY OF PRESENT ILLNESS (detailed timeline and progression)
        3. SYMPTOM ANALYSIS (severity, frequency, triggers)
        4. FUNCTIONAL ASSESSMENT (impact on daily activities, work, relationships)
        5. CLINICAL IMPRESSION (initial diagnostic considerations)
        6. RECOMMENDED NEXT STEPS

        Use professional medical terminology and structure the report clearly with headers.
        Be comprehensive but concise. Focus on clinically relevant details.
        """

        try:
            system_prompt = """You are a clinical psychologist writing an initial assessment report.
            Structure your response with clear clinical language, proper formatting, and clinical reasoning.
            Be thorough but concise. Use DSM-informed terminology where appropriate."""

            report = self.llm_client.generate(
                prompt,
                system_prompt=system_prompt,
                max_tokens=800
            )

            return report

        except Exception as e:
            logger.error(f"Enhanced LLM report generation failed: {e}")
            return self._generate_llm_report(data)
    
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
    
    # Async methods for integration with PIMA orchestrator
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and return response"""
        # For now, we'll use a simple approach to handle the conversation flow
        # use LLM to understand the message better
        
        if not self.data.presenting_concern:
            # First message - extract the concern
            self.data.presenting_concern = message
            return {
                "message": "Thank you for sharing that. Can you tell me more about when this started and how it's affecting you?",
                "question_id": "concern_details"
            }
        
        # For simplicity, we'll simulate the conversation flow
        # In a real implementation, you'd use LLM to understand the context
        
        if not self.data.hpi_onset:
            self.data.hpi_onset = message
            return {
                "message": "On a scale of 1-10, how would you rate the severity of this concern? (1 = very mild, 10 = extremely severe)",
                "question_id": "severity_scale"
            }
        
        if not self.data.hpi_severity:
            try:
                self.data.hpi_severity = int(message)
            except ValueError:
                self.data.hpi_severity = 5  # Default if can't parse
        
        if not self.data.hpi_frequency:
            self.data.hpi_frequency = message
            return {
                "message": "How is this affecting your daily activities and relationships?",
                "question_id": "functional_impact"
            }
        
        if not self.data.function_ADL:
            self.data.function_ADL = message
            self.data.conversation_complete = True
            return {
                "message": "Thank you for sharing that information. I have enough details about your concern now.",
                "question_id": "complete"
            }
        
        return {
            "message": "Thank you for that information. Is there anything else you'd like to share about your concern?",
            "question_id": "additional_info"
        }
    
    def is_complete(self) -> bool:
        """Check if the conversation is complete"""
        return self.data.conversation_complete
    
    def get_data(self) -> Dict[str, Any]:
        """Get the collected data"""
        return asdict(self.data)


from agents.llm_client import LLMClient

def concern_assessment():
    """Run an interactive presenting concern assessment"""
    print("\n=== Interactive Presenting Concern Assessment ===")
    print("Please answer the questions below. Type 'exit' anytime to quit.\n")
    
    #using the LLMClient
    
    llm_client = LLMClient()
    

    chatbot = PresentingConcernChatbot(llm_client=llm_client, max_questions=10)

    # Start conversation
    response = chatbot.start_conversation()
    print(f"Bot: {response.get('question')}")

    while True:
        # Take user input
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("\nAssessment aborted.")
            return

        # Identify current question id
        question_id = response.get("question_id", "unknown")

        # Process response
        processed = chatbot.process_response(question_id, None, user_input)

        # If complete → show report
        if processed.get("status") == "complete":
            print(f"\nBot: {processed.get('message')}")
            print("\n=== FINAL CLINICAL REPORT ===")
            print(chatbot.create_primary_concern_report())

            print("\n=== JSON EXPORT (summary) ===")
            data = json.loads(chatbot.export_as_json())
            print(f"Concern: {data['presenting_concern_data']['presenting_concern']}")
            print(f"Severity: {data['presenting_concern_data']['hpi_severity']}")
            print(f"Questions Asked: {data['conversation_metadata']['total_questions']}")
            print(f"Completion: {data['conversation_metadata']['goal_completion']['completion_percentage']}%")
            break

        # If follow-up
        elif processed.get("type") == "follow_up":
            print(f"Bot (Follow-up): {processed.get('question')}")

        # Otherwise → next normal question
        else:
            print(f"Bot: {processed.get('question')}")

        # Update loop with latest response
        response = processed


if __name__ == "__main__":
    concern_assessment()

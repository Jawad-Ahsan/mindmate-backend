import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

# Configure logging medical_history_summary
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionType(Enum):
    OPEN_ENDED = "open_ended"
    YES_NO = "yes_no"
    MCQ = "mcq"
    SCALE = "scale"
    CHECKBOX = "checkbox"
    DATE = "date"

@dataclass
class QuestionOption:
    value: str
    display: str
    triggers_followup: bool = False

@dataclass
class Question:
    id: str
    text: str
    type: QuestionType
    category: str
    options: List[QuestionOption] = None
    allow_free_text: bool = True
    required: bool = True
    placeholder: str = None
    example: str = None
    follow_up_questions: Dict[str, List[str]] = None  # value -> list of follow-up question IDs
    condition: str = None  # Condition to show this question

@dataclass
class Response:
    question_id: str
    selected_options: List[str] = None
    free_text: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.selected_options is None:
            self.selected_options = []

@dataclass
class PatientHistoryData:
    # Past Psychiatric History
    past_psych_dx: str = None
    past_psych_treatment: str = None
    hospitalizations: str = None
    ect_history: str = None
    
    # Current Medications & Allergies
    current_meds: Dict = field(default_factory=dict)
    med_allergies: str = None
    otc_supplements: str = None
    medication_adherence: str = None
    
    # Medical History
    medical_history_summary: str = None
    chronic_illnesses: str = None
    neurological_problems: str = None
    head_injury: str = None
    seizure_history: str = None
    pregnancy_status: str = None
    recent_infections: str = None
    
    # Substance & Alcohol Use
    alcohol_use: str = None
    drug_use: str = None
    prescription_drug_abuse: str = None
    last_use_date: str = None
    substance_treatment: str = None
    tobacco_use: str = None
    
    # Cultural, Spiritual Factors
    cultural_background: str = None
    cultural_beliefs: str = None
    spiritual_supports: str = None
    family_mental_health_stigma: str = None
    
    # Metadata
    completion_timestamp: datetime = None
    sections_completed: List[str] = field(default_factory=list)

class PatientHistoryCollector:
    """
    Comprehensive patient history data collection system with intelligent
    conditional logic and cultural sensitivity.
    """
    
    def __init__(self, max_questions_per_section: int = 15):
        self.max_questions_per_section = max_questions_per_section
        self.responses: Dict[str, Response] = {}
        self.data = PatientHistoryData()
        self.conversation_history: List[Dict] = []
        self.current_section = None
        self.sections_to_complete = []
        
        self._init_questions()
        self._init_sections()
    
    def _init_sections(self):
        """Initialize available sections"""
        self.sections = [
            'psychiatric_history',
            'medications',
            'medical_history',
            'substance_use',
            'cultural_spiritual'
        ]
    
    def _init_questions(self):
        """Initialize all questions with conditional logic"""
        self.questions = {
            
            # ============= PSYCHIATRIC HISTORY =============
            'psych_dx_history': Question(
                id='psych_dx_history',
                text="Have you ever been diagnosed with a mental health condition?",
                type=QuestionType.YES_NO,
                category='psychiatric_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['psych_dx_details', 'psych_dx_when']
                }
            ),
            
            'psych_dx_details': Question(
                id='psych_dx_details',
                text="What mental health conditions have you been diagnosed with?",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="e.g., Depression, Anxiety, Bipolar Disorder, PTSD",
                example="Depression and Generalized Anxiety Disorder",
                condition="psych_dx_history==yes"
            ),
            
            'psych_dx_when': Question(
                id='psych_dx_when',
                text="When were you first diagnosed?",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="e.g., 2020, Age 25, Last year",
                condition="psych_dx_history==yes"
            ),
            
            'psych_treatment_history': Question(
                id='psych_treatment_history',
                text="Have you ever received treatment for mental health issues?",
                type=QuestionType.MCQ,
                category='psychiatric_history',
                options=[
                    QuestionOption("therapy", "Therapy/Counseling only"),
                    QuestionOption("medication", "Medication only"),
                    QuestionOption("both", "Both therapy and medication"),
                    QuestionOption("none", "No treatment"),
                    QuestionOption("other", "Other treatment")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "therapy": ['therapy_details'],
                    "medication": ['past_medications'],
                    "both": ['therapy_details', 'past_medications'],
                    "other": ['other_treatment_details']
                }
            ),
            
            'therapy_details': Question(
                id='therapy_details',
                text="What type of therapy have you received and for how long?",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="e.g., CBT for 6 months, Family therapy for 1 year",
                condition="psych_treatment_history==therapy,both"
            ),
            
            'past_medications': Question(
                id='past_medications',
                text="What psychiatric medications have you taken in the past?",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="e.g., Prozac, Zoloft, Abilify",
                example="Sertraline 50mg for 2 years, stopped in 2022",
                condition="psych_treatment_history==medication,both"
            ),
            
            'hospitalizations': Question(
                id='hospitalizations',
                text="Have you ever been hospitalized for mental health reasons?",
                type=QuestionType.YES_NO,
                category='psychiatric_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['hospitalization_details']
                }
            ),
            
            'hospitalization_details': Question(
                id='hospitalization_details',
                text="Please provide details about your psychiatric hospitalizations.",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="When, where, how long, reason",
                example="St. Mary's Hospital, March 2023, 5 days, severe depression",
                condition="hospitalizations==yes"
            ),
            
            'ect_history': Question(
                id='ect_history',
                text="Have you ever received ECT (electroconvulsive therapy) or other brain stimulation treatments?",
                type=QuestionType.YES_NO,
                category='psychiatric_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['ect_details']
                }
            ),
            
            'ect_details': Question(
                id='ect_details',
                text="Please provide details about your ECT or brain stimulation treatment.",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="When, how many sessions, effectiveness",
                condition="ect_history==yes"
            ),
            
            # ============= MEDICATIONS =============
            'current_meds_taking': Question(
                id='current_meds_taking',
                text="Are you currently taking any medications?",
                type=QuestionType.YES_NO,
                category='medications',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['current_meds_list', 'medication_adherence']
                }
            ),
            
            'current_meds_list': Question(
                id='current_meds_list',
                text="Please list all medications you're currently taking (include dose and frequency).",
                type=QuestionType.OPEN_ENDED,
                category='medications',
                placeholder="Medication name, dose, frequency",
                example="Sertraline 100mg once daily, Lisinopril 10mg once daily",
                condition="current_meds_taking==yes"
            ),
            
            'medication_adherence': Question(
                id='medication_adherence',
                text="How well do you stick to taking your medications as prescribed?",
                type=QuestionType.MCQ,
                category='medications',
                options=[
                    QuestionOption("always", "I always take them as prescribed"),
                    QuestionOption("usually", "I usually take them, but sometimes miss doses"),
                    QuestionOption("sometimes", "I sometimes take them"),
                    QuestionOption("rarely", "I rarely take them as prescribed")
                ],
                condition="current_meds_taking==yes"
            ),
            
            'med_allergies': Question(
                id='med_allergies',
                text="Do you have any medication allergies or adverse reactions?",
                type=QuestionType.YES_NO,
                category='medications',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No"),
                    QuestionOption("unsure", "I'm not sure")
                ],
                follow_up_questions={
                    "yes": ['allergy_details']
                }
            ),
            
            'allergy_details': Question(
                id='allergy_details',
                text="What medications are you allergic to and what reaction did you have?",
                type=QuestionType.OPEN_ENDED,
                category='medications',
                placeholder="Medication name and reaction",
                example="Penicillin - rash and swelling, Codeine - nausea and vomiting",
                condition="med_allergies==yes"
            ),
            
            'otc_supplements': Question(
                id='otc_supplements',
                text="Do you take any over-the-counter medications, vitamins, or supplements?",
                type=QuestionType.YES_NO,
                category='medications',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['otc_details']
                }
            ),
            
            'otc_details': Question(
                id='otc_details',
                text="What over-the-counter medications, vitamins, or supplements do you take?",
                type=QuestionType.OPEN_ENDED,
                category='medications',
                placeholder="Include names and frequency",
                example="Vitamin D 1000 IU daily, Ibuprofen as needed for headaches",
                condition="otc_supplements==yes"
            ),
            
            # ============= MEDICAL HISTORY =============
            'chronic_conditions': Question(
                id='chronic_conditions',
                text="Do you have any ongoing medical conditions or chronic illnesses?",
                type=QuestionType.YES_NO,
                category='medical_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['chronic_conditions_list']
                }
            ),
            
            'chronic_conditions_list': Question(
                id='chronic_conditions_list',
                text="What chronic medical conditions do you have?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="List your ongoing medical conditions",
                example="Diabetes Type 2, High blood pressure, Asthma",
                condition="chronic_conditions==yes"
            ),
            
            'neurological_history': Question(
                id='neurological_history',
                text="Have you ever had any neurological problems?",
                type=QuestionType.MCQ,
                category='medical_history',
                options=[
                    QuestionOption("none", "No neurological problems"),
                    QuestionOption("seizures", "Seizures or epilepsy"),
                    QuestionOption("head_injury", "Head injury or concussion"),
                    QuestionOption("stroke", "Stroke or mini-stroke"),
                    QuestionOption("other", "Other neurological condition")
                ],
                allow_free_text=True,
                follow_up_questions={
                    "seizures": ['seizure_details'],
                    "head_injury": ['head_injury_details'],
                    "stroke": ['stroke_details'],
                    "other": ['neuro_other_details']
                }
            ),
            
            'seizure_details': Question(
                id='seizure_details',
                text="Please provide details about your seizure history.",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="When diagnosed, frequency, medications",
                example="Diagnosed 2018, controlled with Keppra, last seizure 6 months ago",
                condition="neurological_history==seizures"
            ),
            
            'head_injury_details': Question(
                id='head_injury_details',
                text="Please describe your head injury or concussion.",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="When, how it happened, severity, treatment",
                example="Car accident 2020, concussion with 2-day hospitalization",
                condition="neurological_history==head_injury"
            ),
            
            'pregnancy_status': Question(
                id='pregnancy_status',
                text="Are you currently pregnant or could you be pregnant?",
                type=QuestionType.MCQ,
                category='medical_history',
                options=[
                    QuestionOption("not_applicable", "Not applicable"),
                    QuestionOption("no", "No"),
                    QuestionOption("yes", "Yes"),
                    QuestionOption("possible", "Possibly"),
                    QuestionOption("trying", "Trying to conceive"),
                    QuestionOption("breastfeeding", "Currently breastfeeding")
                ]
            ),
            
            'recent_infections': Question(
                id='recent_infections',
                text="Have you had any infections or been sick in the past month?",
                type=QuestionType.YES_NO,
                category='medical_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['infection_details']
                }
            ),
            
            'infection_details': Question(
                id='infection_details',
                text="What type of infection or illness did you have?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="Type of infection, treatment received",
                example="COVID-19 2 weeks ago, treated at home with rest",
                condition="recent_infections==yes"
            ),
            
            # ============= SUBSTANCE USE =============
            'alcohol_use': Question(
                id='alcohol_use',
                text="Do you drink alcohol?",
                type=QuestionType.MCQ,
                category='substance_use',
                options=[
                    QuestionOption("never", "Never"),
                    QuestionOption("rarely", "Rarely (few times a year)"),
                    QuestionOption("occasionally", "Occasionally (1-2 times per month)"),
                    QuestionOption("regularly", "Regularly (1-2 times per week)"),
                    QuestionOption("frequently", "Frequently (3+ times per week)"),
                    QuestionOption("daily", "Daily")
                ],
                follow_up_questions={
                    "regularly": ['alcohol_amount'],
                    "frequently": ['alcohol_amount', 'alcohol_problems'],
                    "daily": ['alcohol_amount', 'alcohol_problems']
                }
            ),
            
            'alcohol_amount': Question(
                id='alcohol_amount',
                text="When you drink, how many drinks do you typically have?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Number of drinks per occasion",
                example="2-3 beers or 1-2 glasses of wine",
                condition="alcohol_use==regularly,frequently,daily"
            ),
            
            'alcohol_problems': Question(
                id='alcohol_problems',
                text="Has alcohol use ever caused problems in your life?",
                type=QuestionType.YES_NO,
                category='substance_use',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                condition="alcohol_use==frequently,daily",
                follow_up_questions={
                    "yes": ['alcohol_problem_details']
                }
            ),
            
            'drug_use': Question(
                id='drug_use',
                text="Do you use any recreational drugs or substances?",
                type=QuestionType.MCQ,
                category='substance_use',
                options=[
                    QuestionOption("never", "Never"),
                    QuestionOption("past_only", "Used in the past, but not currently"),
                    QuestionOption("occasionally", "Occasionally"),
                    QuestionOption("regularly", "Regularly")
                ],
                follow_up_questions={
                    "past_only": ['past_drug_details'],
                    "occasionally": ['current_drug_details', 'last_use'],
                    "regularly": ['current_drug_details', 'last_use', 'drug_problems']
                }
            ),
            
            'current_drug_details': Question(
                id='current_drug_details',
                text="What substances do you currently use?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Type of substances and frequency",
                example="Marijuana 2-3 times per week, cocaine occasionally",
                condition="drug_use==occasionally,regularly"
            ),
            
            'last_use': Question(
                id='last_use',
                text="When did you last use any recreational substances?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="When was your last use",
                example="Yesterday, last week, 2 months ago",
                condition="drug_use==occasionally,regularly"
            ),
            
            'prescription_abuse': Question(
                id='prescription_abuse',
                text="Have you ever used prescription medications in ways other than prescribed?",
                type=QuestionType.YES_NO,
                category='substance_use',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['prescription_abuse_details']
                }
            ),
            
            'prescription_abuse_details': Question(
                id='prescription_abuse_details',
                text="What prescription medications have you misused and how?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Medication names and how misused",
                example="Took extra Percocet for pain, used friend's Adderall to study",
                condition="prescription_abuse==yes"
            ),
            
            'tobacco_use': Question(
                id='tobacco_use',
                text="Do you use tobacco products?",
                type=QuestionType.MCQ,
                category='substance_use',
                options=[
                    QuestionOption("never", "Never smoked"),
                    QuestionOption("former", "Former smoker"),
                    QuestionOption("current", "Current smoker"),
                    QuestionOption("vaping", "Vaping/E-cigarettes"),
                    QuestionOption("other", "Other tobacco products")
                ],
                follow_up_questions={
                    "former": ['smoking_history'],
                    "current": ['current_smoking'],
                    "vaping": ['vaping_details'],
                    "other": ['other_tobacco_details']
                }
            ),
            
            'current_smoking': Question(
                id='current_smoking',
                text="How much do you currently smoke per day?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Number of cigarettes per day",
                example="Half a pack (10 cigarettes) per day",
                condition="tobacco_use==current"
            ),
            
            'substance_treatment': Question(
                id='substance_treatment',
                text="Have you ever received treatment for alcohol or drug use?",
                type=QuestionType.YES_NO,
                category='substance_use',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={
                    "yes": ['treatment_details']
                }
            ),
            
            # ============= CULTURAL & SPIRITUAL =============
            'cultural_background': Question(
                id='cultural_background',
                text="How would you describe your cultural or ethnic background?",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="Your cultural, ethnic, or racial identity",
                example="Mexican-American, African American, South Asian, Mixed heritage",
                required=False
            ),
            
            'cultural_beliefs_mental_health': Question(
                id='cultural_beliefs_mental_health',
                text="Are there cultural beliefs or traditions that influence how you view mental health?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption("no_influence", "No particular cultural influence"),
                    QuestionOption("some_influence", "Some cultural considerations"),
                    QuestionOption("strong_influence", "Strong cultural beliefs about mental health"),
                    QuestionOption("prefer_not_say", "Prefer not to say")
                ],
                follow_up_questions={
                    "some_influence": ['cultural_details'],
                    "strong_influence": ['cultural_details']
                },
                required=False
            ),
            
            'cultural_details': Question(
                id='cultural_details',
                text="Can you share more about how your cultural background influences your views on mental health?",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="Cultural perspectives on mental health, healing, treatment",
                example="In my culture, family support is very important for healing",
                condition="cultural_beliefs_mental_health==some_influence,strong_influence",
                required=False
            ),
            
            'spiritual_religious': Question(
                id='spiritual_religious',
                text="Do spiritual or religious beliefs play a role in your life?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption("not_important", "Not important to me"),
                    QuestionOption("somewhat_important", "Somewhat important"),
                    QuestionOption("very_important", "Very important"),
                    QuestionOption("prefer_not_say", "Prefer not to say")
                ],
                follow_up_questions={
                    "somewhat_important": ['spiritual_support'],
                    "very_important": ['spiritual_support']
                },
                required=False
            ),
            
            'spiritual_support': Question(
                id='spiritual_support',
                text="Do your spiritual or religious beliefs provide support for dealing with mental health challenges?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption("very_helpful", "Very helpful"),
                    QuestionOption("somewhat_helpful", "Somewhat helpful"),
                    QuestionOption("not_helpful", "Not particularly helpful"),
                    QuestionOption("complicated", "It's complicated"),
                    QuestionOption("conflict", "Sometimes creates conflict")
                ],
                allow_free_text=True,
                condition="spiritual_religious==somewhat_important,very_important",
                required=False
            ),
            
            'family_stigma': Question(
                id='family_stigma',
                text="How does your family view mental health treatment?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption("very_supportive", "Very supportive of treatment"),
                    QuestionOption("somewhat_supportive", "Somewhat supportive"),
                    QuestionOption("neutral", "Neutral/no strong opinion"),
                    QuestionOption("somewhat_negative", "Somewhat negative about treatment"),
                    QuestionOption("very_negative", "Very negative/stigmatizing"),
                    QuestionOption("dont_know", "Don't discuss it with family")
                ],
                allow_free_text=True,
                required=False
            ),
            
            'language_preference': Question(
                id='language_preference',
                text="What language do you prefer to use when discussing personal or emotional topics?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption("english", "English"),
                    QuestionOption("native_primary", "My native/first language"),
                    QuestionOption("bilingual", "Comfortable in multiple languages"),
                    QuestionOption("interpreter", "Would prefer an interpreter")
                ],
                allow_free_text=True,
                placeholder="Please specify language if not English",
                required=False
            )
        }
    
    def start_section(self, section_name: str) -> Dict:
        """Start data collection for a specific section"""
        if section_name not in self.sections:
            return {'status': 'error', 'message': f'Invalid section: {section_name}'}
        
        self.current_section = section_name
        self.conversation_history.append({
            'type': 'section_start',
            'section': section_name,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get first question for this section
        first_question = self._get_next_question_for_section(section_name)
        if first_question:
            return self._format_question_response(first_question)
        
        return {'status': 'error', 'message': 'No questions available for this section'}
    
    def _get_next_question_for_section(self, section: str) -> Optional[Question]:
        """Get the next unanswered question for a section"""
        section_questions = [q for q in self.questions.values() if q.category == section]
        
        for question in section_questions:
            if question.id not in self.responses:
                # Check if question meets conditions
                if question.condition and not self._check_condition(question.condition):
                    continue
                return question
        
        return None
    
    def _check_condition(self, condition: str) -> bool:
        """Check if a question condition is met"""
        if not condition:
            return True
        
        # Parse condition (e.g., "psych_dx_history==yes")
        if '==' in condition:
            question_id, expected_values = condition.split('==', 1)
            expected_values = expected_values.split(',')
            
            response = self.responses.get(question_id)
            if not response:
                return False
            
            # Check selected options
            if response.selected_options:
                return any(option in expected_values for option in response.selected_options)
            
            # Check if any expected value matches
            return any(value in (response.free_text or '') for value in expected_values)
        
        return True
    
    def _format_question_response(self, question: Question) -> Dict:
        """Format question for frontend response"""
        response = {
            'question_id': question.id,
            'question': question.text,
            'type': question.type.value,
            'category': question.category,
            'allow_free_text': question.allow_free_text,
            'required': question.required
        }
        
        if question.options:
            response['options'] = [
                {'value': opt.value, 'display': opt.display, 'triggers_followup': opt.triggers_followup}
                for opt in question.options
            ]
        
        if question.placeholder:
            response['placeholder'] = question.placeholder
        
        if question.example:
            response['example'] = question.example
        
        return response
    
    def process_response(self, question_id: str, selected_options: List[str] = None, free_text: str = None) -> Dict:
        """Process user response and return next question or section completion"""
        
        # Validate response
        if not selected_options and not free_text:
            return {'status': 'error', 'message': 'Please provide a response'}
        
        # Store response
        response = Response(
            question_id=question_id,
            selected_options=selected_options or [],
            free_text=free_text
        )
        self.responses[question_id] = response
        
        # Update conversation history
        self.conversation_history.append({
            'type': 'user_response',
            'question_id': question_id,
            'selected_options': selected_options,
            'free_text': free_text,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update data structure
        self._update_data_structure(question_id, response)
        
        # Check for follow-up questions
        current_question = self.questions.get(question_id)
        follow_up_questions = []
        
        if current_question and current_question.follow_up_questions and selected_options:
            for option in selected_options:
                if option in current_question.follow_up_questions:
                    follow_up_questions.extend(current_question.follow_up_questions[option])
        
        # Return follow-up questions if any
        if follow_up_questions:
            next_question_id = follow_up_questions[0]  # Get first follow-up
            if next_question_id in self.questions:
                next_question = self.questions[next_question_id]
                if self._check_condition(next_question.condition):
                    return self._format_question_response(next_question)
        
        # Get next question in current section
        if self.current_section:
            next_question = self._get_next_question_for_section(self.current_section)
            if next_question:
                return self._format_question_response(next_question)
            else:
                # Section complete
                self.data.sections_completed.append(self.current_section)
                return {
                    'status': 'section_complete',
                    'message': f'{self.current_section.replace("_", " ").title()} section completed.',
                    'completed_section': self.current_section,
                    'sections_completed': len(self.data.sections_completed),
                    'total_sections': len(self.sections)
                }
        
        return {'status': 'error', 'message': 'No more questions available'}
    
    def _update_data_structure(self, question_id: str, response: Response):
        """Update the PatientHistoryData structure based on responses"""
        selected = response.selected_options[0] if response.selected_options else None
        text_value = response.free_text or selected
        
        # Psychiatric History
        if question_id == 'psych_dx_details':
            self.data.past_psych_dx = text_value
        elif question_id == 'therapy_details' or question_id == 'past_medications':
            if self.data.past_psych_treatment:
                self.data.past_psych_treatment += f"; {text_value}"
            else:
                self.data.past_psych_treatment = text_value
        elif question_id == 'hospitalization_details':
            self.data.hospitalizations = text_value
        elif question_id == 'ect_details':
            self.data.ect_history = text_value
        
        # Medications
        elif question_id == 'current_meds_list':
            self.data.current_meds['list'] = text_value
        elif question_id == 'medication_adherence':
            self.data.medication_adherence = selected
        elif question_id == 'allergy_details':
            self.data.med_allergies = text_value
        elif question_id == 'otc_details':
            self.data.otc_supplements = text_value
        
        # Medical History
        elif question_id == 'chronic_conditions_list':
            self.data.chronic_illnesses = text_value
        elif question_id == 'seizure_details':
            self.data.seizure_history = text_value
        elif question_id == 'head_injury_details':
            self.data.head_injury = text_value
        elif question_id == 'neurological_history':
            if selected not in ['none']:
                self.data.neurological_problems = selected
        elif question_id == 'pregnancy_status':
            self.data.pregnancy_status = selected
        elif question_id == 'infection_details':
            self.data.recent_infections = text_value
        
        # Substance Use
        elif question_id == 'alcohol_use':
            self.data.alcohol_use = selected
        elif question_id == 'current_drug_details':
            self.data.drug_use = text_value
        elif question_id == 'last_use':
            self.data.last_use_date = text_value
        elif question_id == 'prescription_abuse_details':
            self.data.prescription_drug_abuse = text_value
        elif question_id == 'current_smoking':
            self.data.tobacco_use = text_value
        elif question_id == 'treatment_details':
            self.data.substance_treatment = text_value
        
        # Cultural & Spiritual
        elif question_id == 'cultural_background':
            self.data.cultural_background = text_value
        elif question_id == 'cultural_details':
            self.data.cultural_beliefs = text_value
        elif question_id == 'spiritual_support':
            self.data.spiritual_supports = text_value
        elif question_id == 'family_stigma':
            self.data.family_mental_health_stigma = selected
            if response.free_text:
                self.data.family_mental_health_stigma += f": {response.free_text}"
    
    def get_section_progress(self, section: str) -> Dict:
        """Get progress information for a specific section"""
        section_questions = [q for q in self.questions.values() if q.category == section]
        total_questions = len(section_questions)
        
        answered_questions = 0
        applicable_questions = 0
        
        for question in section_questions:
            if question.condition and not self._check_condition(question.condition):
                continue  # Skip non-applicable questions
            
            applicable_questions += 1
            if question.id in self.responses:
                answered_questions += 1
        
        return {
            'section': section,
            'answered': answered_questions,
            'applicable': applicable_questions,
            'total': total_questions,
            'completion_percentage': round((answered_questions / applicable_questions * 100), 1) if applicable_questions > 0 else 0,
            'is_complete': answered_questions >= applicable_questions
        }
    
    def get_overall_progress(self) -> Dict:
        """Get overall progress across all sections"""
        total_answered = 0
        total_applicable = 0
        
        section_progress = {}
        for section in self.sections:
            progress = self.get_section_progress(section)
            section_progress[section] = progress
            total_answered += progress['answered']
            total_applicable += progress['applicable']
        
        return {
            'total_answered': total_answered,
            'total_applicable': total_applicable,
            'overall_completion': round((total_answered / total_applicable * 100), 1) if total_applicable > 0 else 0,
            'sections_completed': len(self.data.sections_completed),
            'section_details': section_progress
        }
    
    def export_collected_data(self) -> str:
        """Export all collected data as JSON"""
        export_data = {
            'patient_history_data': asdict(self.data),
            'collection_metadata': {
                'sections_completed': self.data.sections_completed,
                'total_responses': len(self.responses),
                'overall_progress': self.get_overall_progress(),
                'conversation_history': self.conversation_history
            },
            'export_timestamp': datetime.now().isoformat()
        }
        return json.dumps(export_data, indent=2, default=str)
    
    def generate_clinical_summary(self) -> str:
        """Generate a clinical summary of collected information"""
        summary_parts = []
        
        # Psychiatric History
        if self.data.past_psych_dx:
            summary_parts.append(f"PSYCHIATRIC HISTORY: {self.data.past_psych_dx}")
            if self.data.past_psych_treatment:
                summary_parts.append(f"Previous treatment: {self.data.past_psych_treatment}")
            if self.data.hospitalizations:
                summary_parts.append(f"Hospitalizations: {self.data.hospitalizations}")
        
        # Current Medications
        if self.data.current_meds.get('list'):
            summary_parts.append(f"CURRENT MEDICATIONS: {self.data.current_meds['list']}")
            if self.data.medication_adherence:
                summary_parts.append(f"Adherence: {self.data.medication_adherence}")
        
        if self.data.med_allergies:
            summary_parts.append(f"ALLERGIES: {self.data.med_allergies}")
        
        # Medical History
        if self.data.chronic_illnesses:
            summary_parts.append(f"CHRONIC CONDITIONS: {self.data.chronic_illnesses}")
        
        if self.data.neurological_problems:
            summary_parts.append(f"NEUROLOGICAL: {self.data.neurological_problems}")
        
        # Substance Use
        substance_summary = []
        if self.data.alcohol_use and self.data.alcohol_use != 'never':
            substance_summary.append(f"Alcohol: {self.data.alcohol_use}")
        
        if self.data.drug_use:
            substance_summary.append(f"Substances: {self.data.drug_use}")
        
        if self.data.tobacco_use and self.data.tobacco_use not in ['never']:
            substance_summary.append(f"Tobacco: {self.data.tobacco_use}")
        
        if substance_summary:
            summary_parts.append(f"SUBSTANCE USE: {'; '.join(substance_summary)}")
        
        # Cultural Considerations
        cultural_summary = []
        if self.data.cultural_background:
            cultural_summary.append(f"Background: {self.data.cultural_background}")
        
        if self.data.cultural_beliefs:
            cultural_summary.append(f"Beliefs about mental health: {self.data.cultural_beliefs}")
        
        if self.data.family_mental_health_stigma:
            cultural_summary.append(f"Family attitude: {self.data.family_mental_health_stigma}")
        
        if cultural_summary:
            summary_parts.append(f"CULTURAL FACTORS: {'; '.join(cultural_summary)}")
        
        if not summary_parts:
            return "No significant history reported across collected domains."
        
        return "\n\n".join(summary_parts)
    
    def get_critical_alerts(self) -> List[Dict]:
        """Identify critical information that needs immediate attention"""
        alerts = []
        
        # Medication interactions or concerns
        if self.data.med_allergies and 'severe' in self.data.med_allergies.lower():
            alerts.append({
                'type': 'medication_allergy',
                'level': 'high',
                'message': 'Patient reports severe medication allergies',
                'details': self.data.med_allergies
            })
        
        # Pregnancy considerations
        if self.data.pregnancy_status in ['yes', 'possible']:
            alerts.append({
                'type': 'pregnancy',
                'level': 'high',
                'message': 'Patient may be pregnant - medication considerations needed',
                'details': self.data.pregnancy_status
            })
        
        # Substance use concerns
        if self.data.alcohol_use in ['frequently', 'daily']:
            alerts.append({
                'type': 'substance_use',
                'level': 'moderate',
                'message': 'Frequent alcohol use reported',
                'details': self.data.alcohol_use
            })
        
        # Neurological history
        if self.data.seizure_history:
            alerts.append({
                'type': 'neurological',
                'level': 'high',
                'message': 'History of seizures - medication considerations needed',
                'details': self.data.seizure_history
            })
        
        # Recent infections
        if self.data.recent_infections:
            alerts.append({
                'type': 'medical',
                'level': 'low',
                'message': 'Recent infection reported',
                'details': self.data.recent_infections
            })
        
        return alerts


# Usage examples and testing
def demo_patient_history_collector():
    """Demonstrate the patient history collection system"""
    print("Patient History Collection System Demo")
    print("=" * 50)
    
    collector = PatientHistoryCollector()
    
    # Start psychiatric history section
    print("\nStarting Psychiatric History Section...")
    response = collector.start_section('psychiatric_history')
    print(f"First Question: {response['question']}")
    
    # Simulate some responses
    demo_responses = [
        # Psychiatric History
        ('psych_dx_history', ['yes'], None),
        ('psych_dx_details', [], "Depression and anxiety disorder"),
        ('psych_dx_when', [], "Diagnosed in 2020"),
        ('psych_treatment_history', ['both'], None),
        ('therapy_details', [], "CBT for 8 months, very helpful"),
        ('past_medications', [], "Sertraline 100mg, discontinued due to side effects"),
        ('hospitalizations', ['no'], None),
        ('ect_history', ['no'], None),
        
        # Medications section
        ('current_meds_taking', ['yes'], None),
        ('current_meds_list', [], "Escitalopram 10mg daily, Vitamin D 2000 IU daily"),
        ('medication_adherence', ['usually'], None),
        ('med_allergies', ['yes'], None),
        ('allergy_details', [], "Sulfa drugs cause severe rash"),
        ('otc_supplements', ['yes'], None),
        ('otc_details', [], "Melatonin 3mg for sleep, Fish oil"),
        
        # Substance Use section  
        ('alcohol_use', ['occasionally'], None),
        ('drug_use', ['never'], None),
        ('prescription_abuse', ['no'], None),
        ('tobacco_use', ['never'], None),
        ('substance_treatment', ['no'], None),
        
        # Cultural section
        ('cultural_background', [], "South Asian American"),
        ('cultural_beliefs_mental_health', ['some_influence'], None),
        ('cultural_details', [], "Family prefers traditional healing alongside therapy"),
        ('spiritual_religious', ['very_important'], None),
        ('spiritual_support', ['very_helpful'], "Prayer and meditation help with anxiety"),
        ('family_stigma', ['somewhat_supportive'], "Getting better but still some hesitation")
    ]
    
    current_section = 'psychiatric_history'
    
    for question_id, selected_options, free_text in demo_responses:
        print(f"\nUser Response: {selected_options or []} - {free_text or 'N/A'}")
        
        response = collector.process_response(question_id, selected_options, free_text)
        
        if response.get('status') == 'section_complete':
            print(f"\n{'='*30}")
            print(f"SECTION COMPLETED: {response['completed_section']}")
            print(f"Progress: {response['sections_completed']}/{response['total_sections']}")
            print(f"{'='*30}")
            
            # Start next section
            next_sections = ['medications', 'substance_use', 'cultural_spiritual']
            for section in next_sections:
                if section not in collector.data.sections_completed:
                    current_section = section
                    next_response = collector.start_section(section)
                    print(f"\nStarting {section.replace('_', ' ').title()} Section...")
                    if next_response.get('question'):
                        print(f"Next Question: {next_response['question']}")
                    break
        elif response.get('question'):
            print(f"Next Question: {response['question']}")
            if response.get('example'):
                print(f"Example: {response['example']}")
    
    # Show final summary
    print(f"\n{'='*60}")
    print("CLINICAL SUMMARY")
    print("="*60)
    summary = collector.generate_clinical_summary()
    print(summary)
    
    # Show progress
    print(f"\n{'='*60}")
    print("COLLECTION PROGRESS")
    print("="*60)
    progress = collector.get_overall_progress()
    print(f"Overall Completion: {progress['overall_completion']}%")
    print(f"Total Questions Answered: {progress['total_answered']}")
    
    for section, details in progress['section_details'].items():
        print(f"{section.replace('_', ' ').title()}: {details['completion_percentage']}% ({details['answered']}/{details['applicable']})")
    
    # Show critical alerts
    print(f"\n{'='*60}")
    print("CRITICAL ALERTS")
    print("="*60)
    alerts = collector.get_critical_alerts()
    if alerts:
        for alert in alerts:
            print(f"⚠️  {alert['level'].upper()}: {alert['message']}")
            print(f"    Details: {alert['details']}")
    else:
        print("No critical alerts identified.")

if __name__ == "__main__":
    demo_patient_history_collector()
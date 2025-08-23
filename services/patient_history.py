import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from sqlalchemy.orm import Session
from database.database import get_sync_db_session, create_session
from models.sql_models.patient_models import (
    Patient, PatientHistory, PatientHistoryData,
    LanguageEnum, GenderEnum
)

# Configure logging
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
    follow_up_questions: Dict[str, List[str]] = None
    condition: str = None

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

class PatientHistoryCollector:
    """
    Database-integrated patient history collection system.
    Fully compatible with PatientHistory model.
    """
    
    def __init__(self, patient_id: str = None, max_questions_per_section: int = 15):
        self.patient_id = patient_id
        self.max_questions_per_section = max_questions_per_section
        self.responses: Dict[str, Response] = {}
        self.data = PatientHistoryData()
        self.conversation_history: List[Dict] = []
        self.current_section = None
        
        self._init_questions()
        self._init_sections()
        
        # Load existing data if patient_id provided
        if self.patient_id:
            self._load_existing_data()
    
    def _init_sections(self):
        """Initialize available sections - exactly matching PatientHistory model"""
        self.sections = [
            'psychiatric_history',
            'medications', 
            'medical_history',
            'substance_use',
            'cultural_spiritual'
        ]
    
    def _init_questions(self):
        """Initialize questions - only fields that exist in PatientHistory model"""
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
                follow_up_questions={"yes": ['psych_dx_details', 'psych_dx_when']}
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
                follow_up_questions={"yes": ['hospitalization_details']}
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
                follow_up_questions={"yes": ['ect_details']}
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
                follow_up_questions={"yes": ['current_meds_list', 'medication_adherence']}
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
                follow_up_questions={"yes": ['allergy_details']}
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
                follow_up_questions={"yes": ['otc_details']}
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
            'medical_history_summary': Question(
                id='medical_history_summary',
                text="Can you provide a brief summary of your overall medical history?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="Brief overview of your medical background",
                example="Generally healthy, had appendectomy in 2018, family history of diabetes",
                required=False
            ),
            
            'chronic_conditions': Question(
                id='chronic_conditions',
                text="Do you have any ongoing medical conditions or chronic illnesses?",
                type=QuestionType.YES_NO,
                category='medical_history',
                options=[
                    QuestionOption("yes", "Yes", triggers_followup=True),
                    QuestionOption("no", "No")
                ],
                follow_up_questions={"yes": ['chronic_conditions_list']}
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
                follow_up_questions={"yes": ['alcohol_problem_details']}
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
                example="Marijuana 2-3 times per week",
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
                follow_up_questions={"yes": ['prescription_abuse_details']}
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
                follow_up_questions={"yes": ['treatment_details']}
            ),
            
            'treatment_details': Question(
                id='treatment_details',
                text="What type of substance use treatment have you received?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Type of treatment, when, duration",
                example="AA meetings for 6 months, outpatient rehab in 2021",
                condition="substance_treatment==yes"
            ),
            
            # ============= CULTURAL & SPIRITUAL =============
            'cultural_background': Question(
                id='cultural_background',
                text="How would you describe your cultural or ethnic background?",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="Your cultural, ethnic, or racial identity",
                example="Pakistani, Punjabi, South Asian",
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
            )
        }
    
    def _load_existing_data(self):
        """Load existing patient history from database"""
        try:
            with get_sync_db_session() as db:
                patient_history = db.query(PatientHistory).filter(
                    PatientHistory.patient_id == self.patient_id
                ).first()
                
                if patient_history:
                    # Load existing data into our structure
                    self.data.past_psych_dx = patient_history.past_psych_dx
                    self.data.past_psych_treatment = patient_history.past_psych_treatment
                    self.data.hospitalizations = patient_history.hospitalizations
                    self.data.ect_history = patient_history.ect_history
                    self.data.current_meds = patient_history.current_meds or {}
                    self.data.med_allergies = patient_history.med_allergies
                    self.data.otc_supplements = patient_history.otc_supplements
                    self.data.medication_adherence = patient_history.medication_adherence
                    self.data.medical_history_summary = patient_history.medical_history_summary
                    self.data.chronic_illnesses = patient_history.chronic_illnesses
                    self.data.neurological_problems = patient_history.neurological_problems
                    self.data.head_injury = patient_history.head_injury
                    self.data.seizure_history = patient_history.seizure_history
                    self.data.pregnancy_status = patient_history.pregnancy_status
                    self.data.alcohol_use = patient_history.alcohol_use
                    self.data.drug_use = patient_history.drug_use
                    self.data.prescription_drug_abuse = patient_history.prescription_drug_abuse
                    self.data.last_use_date = patient_history.last_use_date
                    self.data.substance_treatment = patient_history.substance_treatment
                    self.data.tobacco_use = patient_history.tobacco_use
                    self.data.cultural_background = patient_history.cultural_background
                    self.data.cultural_beliefs = patient_history.cultural_beliefs
                    self.data.spiritual_supports = patient_history.spiritual_supports
                    self.data.family_mental_health_stigma = patient_history.family_mental_health_stigma
                    self.data.sections_completed = patient_history.sections_completed or []
                    
                    logger.info(f"Loaded existing patient history for patient {self.patient_id}")
        except Exception as e:
            logger.error(f"Failed to load existing patient history: {e}")
    
    def save_to_database(self) -> bool:
        """Save current data to database"""
        if not self.patient_id:
            logger.error("Cannot save to database: no patient_id provided")
            return False
        
        try:
            with get_sync_db_session() as db:
                # Check if patient history already exists
                patient_history = db.query(PatientHistory).filter(
                    PatientHistory.patient_id == self.patient_id
                ).first()
                
                if not patient_history:
                    # Create new patient history record
                    patient_history = PatientHistory(patient_id=self.patient_id)
                    db.add(patient_history)
                
                # Update all fields from our data structure
                patient_history.past_psych_dx = self.data.past_psych_dx
                patient_history.past_psych_treatment = self.data.past_psych_treatment
                patient_history.hospitalizations = self.data.hospitalizations
                patient_history.ect_history = self.data.ect_history
                patient_history.current_meds = self.data.current_meds
                patient_history.med_allergies = self.data.med_allergies
                patient_history.otc_supplements = self.data.otc_supplements
                patient_history.medication_adherence = self.data.medication_adherence
                patient_history.medical_history_summary = self.data.medical_history_summary
                patient_history.chronic_illnesses = self.data.chronic_illnesses
                patient_history.neurological_problems = self.data.neurological_problems
                patient_history.head_injury = self.data.head_injury
                patient_history.seizure_history = self.data.seizure_history
                patient_history.pregnancy_status = self.data.pregnancy_status
                patient_history.alcohol_use = self.data.alcohol_use
                patient_history.drug_use = self.data.drug_use
                patient_history.prescription_drug_abuse = self.data.prescription_drug_abuse
                patient_history.last_use_date = self.data.last_use_date
                patient_history.substance_treatment = self.data.substance_treatment
                patient_history.tobacco_use = self.data.tobacco_use
                patient_history.cultural_background = self.data.cultural_background
                patient_history.cultural_beliefs = self.data.cultural_beliefs
                patient_history.spiritual_supports = self.data.spiritual_supports
                patient_history.family_mental_health_stigma = self.data.family_mental_health_stigma
                patient_history.sections_completed = self.data.sections_completed
                patient_history.completion_timestamp = datetime.utcnow()
                
                # Calculate completion status
                progress = self.get_overall_progress()
                patient_history.is_complete = progress['overall_completion'] >= 80
                
                db.commit()
                logger.info(f"Patient history saved to database for patient {self.patient_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save patient history to database: {e}")
            return False
    
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
        
        # Parse condition (e.g., "psych_dx_history==yes" or "alcohol_use==regularly,frequently,daily")
        try:
            if '==' in condition:
                field, values = condition.split('==')
                field = field.strip()
                values = [v.strip() for v in values.split(',')]
                
                # Get the response for this field
                if field in self.responses:
                    response = self.responses[field]
                    if response.selected_options:
                        return any(option in values for option in response.selected_options)
                    elif response.free_text:
                        return response.free_text.lower() in [v.lower() for v in values]
                return False
            else:
                # Simple field existence check
                return condition in self.responses
        except Exception as e:
            logger.error(f"Error checking condition '{condition}': {e}")
            return False
    
    def process_response(self, question_id: str, response_data: Dict) -> Dict:
        """Process a response to a question"""
        if question_id not in self.questions:
            return {'status': 'error', 'message': f'Invalid question ID: {question_id}'}
        
        question = self.questions[question_id]
        
        # Create response object
        response = Response(question_id=question_id)
        
        # Process based on question type
        if question.type == QuestionType.YES_NO:
            if 'selected_options' in response_data:
                response.selected_options = response_data['selected_options']
            elif 'free_text' in response_data:
                # Convert free text to yes/no
                text = response_data['free_text'].lower().strip()
                if text in ['yes', 'y', 'true', '1']:
                    response.selected_options = ['yes']
                elif text in ['no', 'n', 'false', '0']:
                    response.selected_options = ['no']
        
        elif question.type == QuestionType.MCQ:
            if 'selected_options' in response_data:
                response.selected_options = response_data['selected_options']
            if 'free_text' in response_data and question.allow_free_text:
                response.free_text = response_data['free_text']
        
        elif question.type == QuestionType.OPEN_ENDED:
            if 'free_text' in response_data:
                response.free_text = response_data['free_text']
        
        elif question.type == QuestionType.SCALE:
            if 'selected_options' in response_data:
                response.selected_options = response_data['selected_options']
        
        elif question.type == QuestionType.CHECKBOX:
            if 'selected_options' in response_data:
                response.selected_options = response_data['selected_options']
        
        elif question.type == QuestionType.DATE:
            if 'free_text' in response_data:
                response.free_text = response_data['free_text']
        
        # Store the response
        self.responses[question_id] = response
        
        # Update the data structure
        self._update_data_from_response(question_id, response)
        
        # Add to conversation history
        self.conversation_history.append({
            'type': 'response',
            'question_id': question_id,
            'response': response_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get next question
        next_question = self._get_next_question()
        
        if next_question:
            return self._format_question_response(next_question)
        else:
            # Section or entire form is complete
            if self.current_section:
                self._mark_section_complete(self.current_section)
                return self._format_completion_response()
            else:
                return {'status': 'complete', 'message': 'All questions completed'}
    
    def _update_data_from_response(self, question_id: str, response: Response):
        """Update the data structure based on a response"""
        if question_id == 'psych_dx_history':
            self.data.past_psych_dx = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'psych_dx_details':
            self.data.past_psych_dx = response.free_text
        elif question_id == 'psych_dx_when':
            # Combine with existing diagnosis info
            existing = self.data.past_psych_dx or ""
            self.data.past_psych_dx = f"{existing} (Diagnosed: {response.free_text})"
        elif question_id == 'psych_treatment_history':
            self.data.past_psych_treatment = ', '.join(response.selected_options)
            if response.free_text:
                self.data.past_psych_treatment += f" - {response.free_text}"
        elif question_id == 'therapy_details':
            self.data.past_psych_treatment = response.free_text
        elif question_id == 'past_medications':
            self.data.past_psych_treatment = response.free_text
        elif question_id == 'hospitalizations':
            self.data.hospitalizations = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'hospitalization_details':
            self.data.hospitalizations = response.free_text
        elif question_id == 'ect_history':
            self.data.ect_history = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'ect_details':
            self.data.ect_history = response.free_text
        elif question_id == 'current_meds_taking':
            if 'yes' in response.selected_options:
                # Will be filled by current_meds_list
                pass
            else:
                self.data.current_meds = {}
        elif question_id == 'current_meds_list':
            # Parse medication list into structured format
            if response.free_text:
                meds = {}
                lines = response.free_text.split('\n')
                for line in lines:
                    if line.strip():
                        # Simple parsing - can be enhanced
                        meds[line.strip()] = {'dose': 'as prescribed', 'frequency': 'as prescribed'}
                self.data.current_meds = meds
        elif question_id == 'medication_adherence':
            self.data.medication_adherence = ', '.join(response.selected_options)
        elif question_id == 'med_allergies':
            self.data.med_allergies = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'allergy_details':
            self.data.med_allergies = response.free_text
        elif question_id == 'otc_supplements':
            self.data.otc_supplements = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'otc_details':
            self.data.otc_supplements = response.free_text
        elif question_id == 'medical_history_summary':
            self.data.medical_history_summary = response.free_text
        elif question_id == 'chronic_conditions':
            self.data.chronic_illnesses = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'chronic_conditions_list':
            self.data.chronic_illnesses = response.free_text
        elif question_id == 'neurological_history':
            self.data.neurological_problems = ', '.join(response.selected_options)
            if response.free_text:
                self.data.neurological_problems += f" - {response.free_text}"
        elif question_id == 'seizure_details':
            self.data.seizure_history = response.free_text
        elif question_id == 'head_injury_details':
            self.data.head_injury = response.free_text
        elif question_id == 'pregnancy_status':
            self.data.pregnancy_status = ', '.join(response.selected_options)
        elif question_id == 'alcohol_use':
            self.data.alcohol_use = ', '.join(response.selected_options)
        elif question_id == 'alcohol_amount':
            existing = self.data.alcohol_use or ""
            self.data.alcohol_use = f"{existing} - Amount: {response.free_text}"
        elif question_id == 'alcohol_problems':
            if 'yes' in response.selected_options:
                existing = self.data.alcohol_use or ""
                self.data.alcohol_use = f"{existing} - Has caused problems"
        elif question_id == 'alcohol_problem_details':
            existing = self.data.alcohol_use or ""
            self.data.alcohol_use = f"{existing} - Problems: {response.free_text}"
        elif question_id == 'drug_use':
            self.data.drug_use = ', '.join(response.selected_options)
        elif question_id == 'current_drug_details':
            existing = self.data.drug_use or ""
            self.data.drug_use = f"{existing} - Current use: {response.free_text}"
        elif question_id == 'last_use':
            self.data.last_use_date = response.free_text
        elif question_id == 'prescription_abuse':
            self.data.prescription_drug_abuse = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'prescription_abuse_details':
            self.data.prescription_drug_abuse = response.free_text
        elif question_id == 'tobacco_use':
            self.data.tobacco_use = ', '.join(response.selected_options)
        elif question_id == 'current_smoking':
            existing = self.data.tobacco_use or ""
            self.data.tobacco_use = f"{existing} - Amount: {response.free_text}"
        elif question_id == 'substance_treatment':
            self.data.substance_treatment = 'yes' if 'yes' in response.selected_options else 'no'
        elif question_id == 'treatment_details':
            self.data.substance_treatment = response.free_text
        elif question_id == 'cultural_background':
            self.data.cultural_background = response.free_text
        elif question_id == 'cultural_beliefs_mental_health':
            self.data.cultural_beliefs = ', '.join(response.selected_options)
        elif question_id == 'cultural_details':
            existing = self.data.cultural_beliefs or ""
            self.data.cultural_beliefs = f"{existing} - Details: {response.free_text}"
        elif question_id == 'spiritual_religious':
            self.data.spiritual_supports = ', '.join(response.selected_options)
        elif question_id == 'spiritual_support':
            existing = self.data.spiritual_supports or ""
            self.data.spiritual_supports = f"{existing} - Support level: {', '.join(response.selected_options)}"
            if response.free_text:
                self.data.spiritual_supports += f" - Notes: {response.free_text}"
        elif question_id == 'family_stigma':
            self.data.family_mental_health_stigma = ', '.join(response.selected_options)
            if response.free_text:
                self.data.family_mental_health_stigma += f" - Notes: {response.free_text}"
    
    def _get_next_question(self) -> Optional[Question]:
        """Get the next question to ask"""
        if not self.current_section:
            return None
        
        # Get all questions for current section
        section_questions = [q for q in self.questions.values() if q.category == self.current_section]
        
        # Check for follow-up questions first
        for response in self.responses.values():
            if response.question_id in self.questions:
                question = self.questions[response.question_id]
                if question.follow_up_questions and response.selected_options:
                    for option in response.selected_options:
                        if option in question.follow_up_questions:
                            for follow_up_id in question.follow_up_questions[option]:
                                if follow_up_id not in self.responses:
                                    follow_up_question = self.questions.get(follow_up_id)
                                    if follow_up_question and self._check_condition(follow_up_question.condition):
                                        return follow_up_question
        
        # Get next regular question
        for question in section_questions:
            if question.id not in self.responses:
                if self._check_condition(question.condition):
                    return question
        
        return None
    
    def _format_question_response(self, question: Question) -> Dict:
        """Format a question for API response"""
        options = []
        if question.options:
            for option in question.options:
                options.append({
                    'value': option.value,
                    'display': option.display,
                    'triggers_followup': option.triggers_followup
                })
        
        return {
            'status': 'question',
            'question': {
                'id': question.id,
                'text': question.text,
                'type': question.type.value,
                'category': question.category,
                'options': options,
                'allow_free_text': question.allow_free_text,
                'required': question.required,
                'placeholder': question.placeholder,
                'example': question.example
            },
            'progress': self.get_section_progress(question.category)
        }
    
    def _format_completion_response(self) -> Dict:
        """Format completion response"""
        return {
            'status': 'section_complete',
            'message': f'Section "{self.current_section}" completed',
            'progress': self.get_overall_progress(),
            'next_section': self._get_next_incomplete_section()
        }
    
    def _mark_section_complete(self, section: str):
        """Mark a section as complete"""
        if section not in self.data.sections_completed:
            self.data.sections_completed.append(section)
    
    def _get_next_incomplete_section(self) -> Optional[str]:
        """Get the next incomplete section"""
        for section in self.sections:
            if section not in self.data.sections_completed:
                return section
        return None
    
    def get_section_progress(self, section: str) -> Dict:
        """Get progress for a specific section"""
        if section not in self.sections:
            return {'completion': 0, 'total_questions': 0, 'answered_questions': 0}
        
        section_questions = [q for q in self.questions.values() if q.category == section]
        total_questions = len(section_questions)
        answered_questions = len([q for q in section_questions if q.id in self.responses])
        
        completion = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'completion': round(completion, 1),
            'total_questions': total_questions,
            'answered_questions': answered_questions
        }
    
    def get_overall_progress(self) -> Dict:
        """Get overall progress across all sections"""
        total_sections = len(self.sections)
        completed_sections = len(self.data.sections_completed)
        
        section_progresses = {}
        total_completion = 0
        
        for section in self.sections:
            progress = self.get_section_progress(section)
            section_progresses[section] = progress
            total_completion += progress['completion']
        
        overall_completion = total_completion / total_sections if total_sections > 0 else 0
        
        return {
            'overall_completion': round(overall_completion, 1),
            'total_sections': total_sections,
            'completed_sections': completed_sections,
            'section_progress': section_progresses
        }
    
    def get_summary(self) -> Dict:
        """Get a summary of collected data"""
        return {
            'patient_id': self.patient_id,
            'progress': self.get_overall_progress(),
            'sections_completed': self.data.sections_completed,
            'data_summary': {
                'has_psychiatric_history': bool(self.data.past_psych_dx),
                'has_medications': bool(self.data.current_meds),
                'has_medical_history': bool(self.data.medical_history_summary),
                'has_substance_use': bool(self.data.alcohol_use or self.data.drug_use),
                'has_cultural_info': bool(self.data.cultural_background)
            },
            'conversation_length': len(self.conversation_history)
        }
    
    def export_data(self) -> PatientHistoryData:
        """Export the collected data"""
        return self.data
    
    def reset_section(self, section: str) -> bool:
        """Reset a specific section"""
        if section not in self.sections:
            return False
        
        # Remove responses for this section
        section_questions = [q.id for q in self.questions.values() if q.category == section]
        for question_id in section_questions:
            if question_id in self.responses:
                del self.responses[question_id]
        
        # Remove from completed sections
        if section in self.data.sections_completed:
            self.data.sections_completed.remove(section)
        
        # Reset data for this section
        if section == 'psychiatric_history':
            self.data.past_psych_dx = None
            self.data.past_psych_treatment = None
            self.data.hospitalizations = None
            self.data.ect_history = None
        elif section == 'medications':
            self.data.current_meds = {}
            self.data.med_allergies = None
            self.data.otc_supplements = None
            self.data.medication_adherence = None
        elif section == 'medical_history':
            self.data.medical_history_summary = None
            self.data.chronic_illnesses = None
            self.data.neurological_problems = None
            self.data.head_injury = None
            self.data.seizure_history = None
            self.data.pregnancy_status = None
        elif section == 'substance_use':
            self.data.alcohol_use = None
            self.data.drug_use = None
            self.data.prescription_drug_abuse = None
            self.data.last_use_date = None
            self.data.substance_treatment = None
            self.data.tobacco_use = None
        elif section == 'cultural_spiritual':
            self.data.cultural_background = None
            self.data.cultural_beliefs = None
            self.data.spiritual_supports = None
            self.data.family_mental_health_stigma = None
        
        return True
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a question by its ID"""
        return self.questions.get(question_id)
    
    def get_section_questions(self, section: str) -> List[Question]:
        """Get all questions for a section"""
        if section not in self.sections:
            return []
        return [q for q in self.questions.values() if q.category == section]
    
    def get_response(self, question_id: str) -> Optional[Response]:
        """Get a response by question ID"""
        return self.responses.get(question_id)
    
    def get_section_responses(self, section: str) -> Dict[str, Response]:
        """Get all responses for a section"""
        if section not in self.sections:
            return {}
        
        section_questions = [q.id for q in self.questions.values() if q.category == section]
        return {qid: self.responses[qid] for qid in section_questions if qid in self.responses}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_patient_history_collector(patient_id: str) -> PatientHistoryCollector:
    """Create a new patient history collector for a patient"""
    return PatientHistoryCollector(patient_id=patient_id)


def load_patient_history(patient_id: str) -> Optional[PatientHistoryData]:
    """Load existing patient history data"""
    try:
        with get_sync_db_session() as db:
            patient_history = db.query(PatientHistory).filter(
                PatientHistory.patient_id == patient_id
            ).first()
            
            if patient_history:
                return PatientHistoryData(
                    past_psych_dx=patient_history.past_psych_dx,
                    past_psych_treatment=patient_history.past_psych_treatment,
                    hospitalizations=patient_history.hospitalizations,
                    ect_history=patient_history.ect_history,
                    current_meds=patient_history.current_meds or {},
                    med_allergies=patient_history.med_allergies,
                    otc_supplements=patient_history.otc_supplements,
                    medication_adherence=patient_history.medication_adherence,
                    medical_history_summary=patient_history.medical_history_summary,
                    chronic_illnesses=patient_history.chronic_illnesses,
                    neurological_problems=patient_history.neurological_problems,
                    head_injury=patient_history.head_injury,
                    seizure_history=patient_history.seizure_history,
                    pregnancy_status=patient_history.pregnancy_status,
                    alcohol_use=patient_history.alcohol_use,
                    drug_use=patient_history.drug_use,
                    prescription_drug_abuse=patient_history.prescription_drug_abuse,
                    last_use_date=patient_history.last_use_date,
                    substance_treatment=patient_history.substance_treatment,
                    tobacco_use=patient_history.tobacco_use,
                    cultural_background=patient_history.cultural_background,
                    cultural_beliefs=patient_history.cultural_beliefs,
                    spiritual_supports=patient_history.spiritual_supports,
                    family_mental_health_stigma=patient_history.family_mental_health_stigma,
                    completion_timestamp=patient_history.completion_timestamp,
                    sections_completed=patient_history.sections_completed or []
                )
    except Exception as e:
        logger.error(f"Failed to load patient history: {e}")
    
    return None


def save_patient_history_data(patient_id: str, data: PatientHistoryData) -> bool:
    """Save patient history data to database"""
    try:
        with get_sync_db_session() as db:
            patient_history = db.query(PatientHistory).filter(
                PatientHistory.patient_id == patient_id
            ).first()
            
            if not patient_history:
                patient_history = PatientHistory(patient_id=patient_id)
                db.add(patient_history)
            
            # Update all fields
            patient_history.past_psych_dx = data.past_psych_dx
            patient_history.past_psych_treatment = data.past_psych_treatment
            patient_history.hospitalizations = data.hospitalizations
            patient_history.ect_history = data.ect_history
            patient_history.current_meds = data.current_meds
            patient_history.med_allergies = data.med_allergies
            patient_history.otc_supplements = data.otc_supplements
            patient_history.medication_adherence = data.medication_adherence
            patient_history.medical_history_summary = data.medical_history_summary
            patient_history.chronic_illnesses = data.chronic_illnesses
            patient_history.neurological_problems = data.neurological_problems
            patient_history.head_injury = data.head_injury
            patient_history.seizure_history = data.seizure_history
            patient_history.pregnancy_status = data.pregnancy_status
            patient_history.alcohol_use = data.alcohol_use
            patient_history.drug_use = data.drug_use
            patient_history.prescription_drug_abuse = data.prescription_drug_abuse
            patient_history.last_use_date = data.last_use_date
            patient_history.substance_treatment = data.substance_treatment
            patient_history.tobacco_use = data.tobacco_use
            patient_history.cultural_background = data.cultural_background
            patient_history.cultural_beliefs = data.cultural_beliefs
            patient_history.spiritual_supports = data.spiritual_supports
            patient_history.family_mental_health_stigma = data.family_mental_health_stigma
            patient_history.sections_completed = data.sections_completed
            patient_history.completion_timestamp = datetime.utcnow()
            
            # Calculate completion
            total_fields = 24
            filled_fields = sum(1 for field in [
                data.past_psych_dx, data.past_psych_treatment, data.hospitalizations,
                data.ect_history, data.med_allergies, data.otc_supplements,
                data.medication_adherence, data.medical_history_summary,
                data.chronic_illnesses, data.neurological_problems, data.head_injury,
                data.seizure_history, data.pregnancy_status, data.alcohol_use,
                data.drug_use, data.prescription_drug_abuse, data.last_use_date,
                data.substance_treatment, data.tobacco_use, data.cultural_background,
                data.cultural_beliefs, data.spiritual_supports, data.family_mental_health_stigma
            ] if field is not None)
            
            if data.current_meds and len(data.current_meds) > 0:
                filled_fields += 1
            
            completion_percentage = (filled_fields / total_fields) * 100
            patient_history.is_complete = completion_percentage >= 80
            
            db.commit()
            return True
            
    except Exception as e:
        logger.error(f"Failed to save patient history data: {e}")
        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'QuestionType',
    'QuestionOption',
    'Question',
    'Response',
    'PatientHistoryCollector',
    'create_patient_history_collector',
    'load_patient_history',
    'save_patient_history_data'
]
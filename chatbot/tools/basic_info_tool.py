"""
Basic Info Tool for MindMate Chatbot
====================================
Comprehensive tool for collecting patient medical history, family history, and other basic information.
Based on the original basic_info_bot.py with enhanced functionality.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionType(str, Enum):
    OPEN_ENDED = "open_ended"
    YES_NO = "yes_no"
    MCQ = "mcq"
    SCALE = "scale"
    CHECKBOX = "checkbox"
    DATE = "date"

class QuestionOption(BaseModel):
    value: str
    display: str
    triggers_followup: bool = False

class Question(BaseModel):
    id: str
    text: str
    type: QuestionType
    category: str
    options: Optional[List[QuestionOption]] = None
    allow_free_text: bool = True
    required: bool = True
    placeholder: Optional[str] = None
    example: Optional[str] = None
    follow_up_questions: Optional[Dict[str, List[str]]] = None
    condition: Optional[str] = None

class Response(BaseModel):
    question_id: str
    selected_options: List[str] = field(default_factory=list)
    free_text: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PatientHistoryData(BaseModel):
    """Comprehensive patient history data model"""
    # Past Psychiatric History
    past_psych_dx: Optional[str] = None
    past_psych_treatment: Optional[str] = None
    hospitalizations: Optional[str] = None
    ect_history: Optional[str] = None
    
    # Current Medications & Allergies
    current_meds: Dict = Field(default_factory=dict)
    med_allergies: Optional[str] = None
    otc_supplements: Optional[str] = None
    medication_adherence: Optional[str] = None
    
    # Medical History
    medical_history_summary: Optional[str] = None
    chronic_illnesses: Optional[str] = None
    neurological_problems: Optional[str] = None
    head_injury: Optional[str] = None
    seizure_history: Optional[str] = None
    pregnancy_status: Optional[str] = None
    recent_infections: Optional[str] = None
    
    # Substance & Alcohol Use
    alcohol_use: Optional[str] = None
    drug_use: Optional[str] = None
    prescription_drug_abuse: Optional[str] = None
    last_use_date: Optional[str] = None
    substance_treatment: Optional[str] = None
    tobacco_use: Optional[str] = None
    
    # Cultural, Spiritual Factors
    cultural_background: Optional[str] = None
    cultural_beliefs: Optional[str] = None
    spiritual_supports: Optional[str] = None
    family_mental_health_stigma: Optional[str] = None
    
    # Family History
    family_psych_history: Optional[str] = None
    family_medical_history: Optional[str] = None
    family_substance_history: Optional[str] = None
    
    # Social & Environmental
    living_situation: Optional[str] = None
    employment_status: Optional[str] = None
    financial_stress: Optional[str] = None
    social_support: Optional[str] = None
    
    # Metadata
    completion_timestamp: Optional[datetime] = None
    sections_completed: List[str] = Field(default_factory=list)

class BasicInfoTool:
    """
    Comprehensive tool for collecting basic patient information.
    Transformed from the original PatientHistoryCollector class.
    """
    
    def __init__(self):
        self.responses: Dict[str, Response] = {}
        self.data = PatientHistoryData()
        self.current_question = None
        self.current_section = None
        self.sections_to_complete = []
        self.question_sequence = []
        
        self._init_questions()
        self._init_sections()
        self._init_question_sequence()
    
    def _init_sections(self):
        """Initialize available sections"""
        self.sections = [
            'psychiatric_history',
            'medications',
            'medical_history',
            'substance_use',
            'cultural_spiritual',
            'family_history',
            'social_environmental'
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
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
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
                    QuestionOption(value="therapy", display="Therapy/Counseling only"),
                    QuestionOption(value="medication", display="Medication only"),
                    QuestionOption(value="both", display="Both therapy and medication"),
                    QuestionOption(value="none", display="No treatment"),
                    QuestionOption(value="other", display="Other treatment")
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
            
            'other_treatment_details': Question(
                id='other_treatment_details',
                text="Please describe the other treatment you received.",
                type=QuestionType.OPEN_ENDED,
                category='psychiatric_history',
                placeholder="e.g., TMS, ketamine therapy, alternative medicine",
                condition="psych_treatment_history==other"
            ),
            
            'hospitalizations': Question(
                id='hospitalizations',
                text="Have you ever been hospitalized for mental health reasons?",
                type=QuestionType.YES_NO,
                category='psychiatric_history',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
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
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
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
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
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
                    QuestionOption(value="always", display="I always take them as prescribed"),
                    QuestionOption(value="usually", display="I usually take them, but sometimes miss doses"),
                    QuestionOption(value="sometimes", display="I sometimes take them"),
                    QuestionOption(value="rarely", display="I rarely take them as prescribed")
                ],
                condition="current_meds_taking==yes"
            ),
            
            'med_allergies': Question(
                id='med_allergies',
                text="Do you have any medication allergies or adverse reactions?",
                type=QuestionType.YES_NO,
                category='medications',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No"),
                    QuestionOption(value="unsure", display="I'm not sure")
                ],
                follow_up_questions={
                    "yes": ['allergy_details']
                }
            ),
            
            'allergy_details': Question(
                id='allergy_details',
                text="Please describe your medication allergies or adverse reactions.",
                type=QuestionType.OPEN_ENDED,
                category='medications',
                placeholder="e.g., Severe rash with sulfa drugs, nausea with codeine",
                condition="med_allergies==yes"
            ),
            
            'otc_supplements': Question(
                id='otc_supplements',
                text="Do you take any over-the-counter medications, vitamins, or supplements?",
                type=QuestionType.YES_NO,
                category='medications',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
                ],
                follow_up_questions={
                    "yes": ['otc_details']
                }
            ),
            
            'otc_details': Question(
                id='otc_details',
                text="Please list all over-the-counter medications, vitamins, and supplements you take.",
                type=QuestionType.OPEN_ENDED,
                category='medications',
                placeholder="e.g., Vitamin D 2000 IU daily, Melatonin 3mg for sleep",
                condition="otc_supplements==yes"
            ),
            
            # ============= MEDICAL HISTORY =============
            'medical_history_summary': Question(
                id='medical_history_summary',
                text="Do you have any significant medical conditions or health issues?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="e.g., Diabetes, heart disease, thyroid problems, none",
                example="Type 2 diabetes, high blood pressure"
            ),
            
            'chronic_illnesses': Question(
                id='chronic_illnesses',
                text="Do you have any chronic illnesses or ongoing health problems?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="e.g., Asthma, arthritis, chronic pain, none",
                example="Asthma since childhood, managed with inhaler"
            ),
            
            'neurological_problems': Question(
                id='neurological_problems',
                text="Do you have any neurological problems or brain-related conditions?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="e.g., Epilepsy, migraines, stroke history, none",
                example="Occasional migraines, no other neurological issues"
            ),
            
            'head_injury': Question(
                id='head_injury',
                text="Have you ever had a significant head injury or concussion?",
                type=QuestionType.YES_NO,
                category='medical_history',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
                ],
                follow_up_questions={
                    "yes": ['head_injury_details']
                }
            ),
            
            'head_injury_details': Question(
                id='head_injury_details',
                text="Please provide details about your head injury or concussion.",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="When, how it happened, severity, recovery",
                condition="head_injury==yes"
            ),
            
            'seizure_history': Question(
                id='seizure_history',
                text="Do you have a history of seizures or epilepsy?",
                type=QuestionType.YES_NO,
                category='medical_history',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
                ],
                follow_up_questions={
                    "yes": ['seizure_details']
                }
            ),
            
            'seizure_details': Question(
                id='seizure_details',
                text="Please provide details about your seizure history.",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="Type, frequency, triggers, last occurrence",
                condition="seizure_history==yes"
            ),
            
            'pregnancy_status': Question(
                id='pregnancy_status',
                text="Are you currently pregnant or could you be pregnant?",
                type=QuestionType.MCQ,
                category='medical_history',
                options=[
                    QuestionOption(value="yes", display="Yes, I am pregnant"),
                    QuestionOption(value="possible", display="It's possible, I'm not sure"),
                    QuestionOption(value="no", display="No, I'm not pregnant"),
                    QuestionOption(value="not_applicable", display="Not applicable to me")
                ]
            ),
            
            'recent_infections': Question(
                id='recent_infections',
                text="Have you had any recent infections or illnesses?",
                type=QuestionType.OPEN_ENDED,
                category='medical_history',
                placeholder="e.g., COVID-19 in January, urinary tract infection last month, none",
                example="Recovered from COVID-19 about 2 months ago"
            ),
            
            # ============= SUBSTANCE USE =============
            'alcohol_use': Question(
                id='alcohol_use',
                text="How often do you drink alcohol?",
                type=QuestionType.MCQ,
                category='substance_use',
                options=[
                    QuestionOption(value="never", display="I don't drink alcohol"),
                    QuestionOption(value="rarely", display="Rarely (few times a year)"),
                    QuestionOption(value="occasionally", display="Occasionally (few times a month)"),
                    QuestionOption(value="sometimes", display="Sometimes (few times a week)"),
                    QuestionOption(value="frequently", display="Frequently (most days)"),
                    QuestionOption(value="daily", display="Daily")
                ]
            ),
            
            'drug_use': Question(
                id='drug_use',
                text="Do you use any recreational drugs or substances?",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="e.g., Marijuana occasionally, no drug use, prescription drug misuse",
                example="No recreational drug use"
            ),
            
            'prescription_abuse': Question(
                id='prescription_abuse',
                text="Have you ever misused prescription medications?",
                type=QuestionType.YES_NO,
                category='substance_use',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
                ],
                follow_up_questions={
                    "yes": ['prescription_abuse_details']
                }
            ),
            
            'prescription_abuse_details': Question(
                id='prescription_abuse_details',
                text="Please describe your prescription medication misuse.",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="What medications, when, how often",
                condition="prescription_abuse==yes"
            ),
            
            'tobacco_use': Question(
                id='tobacco_use',
                text="Do you use tobacco products (cigarettes, vaping, chewing tobacco)?",
                type=QuestionType.MCQ,
                category='substance_use',
                options=[
                    QuestionOption(value="never", display="I don't use tobacco"),
                    QuestionOption(value="former", display="I used to but quit"),
                    QuestionOption(value="occasionally", display="Occasionally"),
                    QuestionOption(value="regular", display="Regular use"),
                    QuestionOption(value="heavy", display="Heavy use")
                ]
            ),
            
            'substance_treatment': Question(
                id='substance_treatment',
                text="Have you ever received treatment for substance use or addiction?",
                type=QuestionType.YES_NO,
                category='substance_use',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No")
                ],
                follow_up_questions={
                    "yes": ['substance_treatment_details']
                }
            ),
            
            'substance_treatment_details': Question(
                id='substance_treatment_details',
                text="Please describe your substance use treatment.",
                type=QuestionType.OPEN_ENDED,
                category='substance_use',
                placeholder="Type of treatment, when, duration, outcome",
                condition="substance_treatment==yes"
            ),
            
            # ============= CULTURAL & SPIRITUAL =============
            'cultural_background': Question(
                id='cultural_background',
                text="What is your cultural or ethnic background?",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="e.g., Pakistani, South Asian, Middle Eastern, European",
                example="Pakistani, specifically from Punjab region"
            ),
            
            'cultural_beliefs_mental_health': Question(
                id='cultural_beliefs_mental_health',
                text="How do your cultural beliefs influence your views on mental health?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption(value="strong_influence", display="Strong influence on my views"),
                    QuestionOption(value="some_influence", display="Some influence on my views"),
                    QuestionOption(value="little_influence", display="Little influence on my views"),
                    QuestionOption(value="no_influence", display="No influence on my views")
                ],
                allow_free_text=True
            ),
            
            'cultural_details': Question(
                id='cultural_details',
                text="Please elaborate on how your cultural background affects your mental health views.",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="Specific beliefs, family attitudes, cultural practices",
                condition="cultural_beliefs_mental_health==strong_influence,some_influence"
            ),
            
            'spiritual_religious': Question(
                id='spiritual_religious',
                text="How important are spirituality or religious beliefs in your life?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption(value="very_important", display="Very important"),
                    QuestionOption(value="somewhat_important", display="Somewhat important"),
                    QuestionOption(value="not_very_important", display="Not very important"),
                    QuestionOption(value="not_important", display="Not important at all")
                ]
            ),
            
            'spiritual_support': Question(
                id='spiritual_support',
                text="Do you find spiritual or religious practices helpful for your mental health?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption(value="very_helpful", display="Very helpful", triggers_followup=True),
                    QuestionOption(value="somewhat_helpful", display="Somewhat helpful"),
                    QuestionOption(value="not_helpful", display="Not helpful"),
                    QuestionOption(value="not_applicable", display="Not applicable")
                ],
                follow_up_questions={
                    "very_helpful": ['spiritual_support_details']
                }
            ),
            
            'spiritual_support_details': Question(
                id='spiritual_support_details',
                text="Please describe how spiritual practices help your mental health.",
                type=QuestionType.OPEN_ENDED,
                category='cultural_spiritual',
                placeholder="Specific practices, how they help, frequency",
                condition="spiritual_support==very_helpful"
            ),
            
            'family_stigma': Question(
                id='family_stigma',
                text="How supportive is your family regarding mental health treatment?",
                type=QuestionType.MCQ,
                category='cultural_spiritual',
                options=[
                    QuestionOption(value="very_supportive", display="Very supportive"),
                    QuestionOption(value="somewhat_supportive", display="Somewhat supportive"),
                    QuestionOption(value="neutral", display="Neutral"),
                    QuestionOption(value="somewhat_unsupportive", display="Somewhat unsupportive"),
                    QuestionOption(value="very_unsupportive", display="Very unsupportive")
                ]
            ),
            
            # ============= FAMILY HISTORY =============
            'family_psych_history': Question(
                id='family_psych_history',
                text="Do you have a family history of mental health conditions?",
                type=QuestionType.YES_NO,
                category='family_history',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No"),
                    QuestionOption(value="unsure", display="I'm not sure")
                ],
                follow_up_questions={
                    "yes": ['family_psych_details']
                }
            ),
            
            'family_psych_details': Question(
                id='family_psych_details',
                text="Please describe your family's mental health history.",
                type=QuestionType.OPEN_ENDED,
                category='family_history',
                placeholder="e.g., Mother has depression, father has anxiety, sibling with bipolar",
                condition="family_psych_history==yes"
            ),
            
            'family_medical_history': Question(
                id='family_medical_history',
                text="Do you have a family history of significant medical conditions?",
                type=QuestionType.OPEN_ENDED,
                category='family_history',
                placeholder="e.g., Heart disease, diabetes, cancer, none",
                example="Father had heart disease, mother has diabetes"
            ),
            
            'family_substance_history': Question(
                id='family_substance_history',
                text="Do you have a family history of substance use or addiction?",
                type=QuestionType.YES_NO,
                category='family_history',
                options=[
                    QuestionOption(value="yes", display="Yes", triggers_followup=True),
                    QuestionOption(value="no", display="No"),
                    QuestionOption(value="unsure", display="I'm not sure")
                ],
                follow_up_questions={
                    "yes": ['family_substance_details']
                }
            ),
            
            'family_substance_details': Question(
                id='family_substance_details',
                text="Please describe your family's substance use history.",
                type=QuestionType.OPEN_ENDED,
                category='family_history',
                placeholder="e.g., Father was alcoholic, sibling struggled with drug addiction",
                condition="family_substance_history==yes"
            ),
            
            # ============= SOCIAL & ENVIRONMENTAL =============
            'living_situation': Question(
                id='living_situation',
                text="What is your current living situation?",
                type=QuestionType.MCQ,
                category='social_environmental',
                options=[
                    QuestionOption(value="alone", display="Living alone"),
                    QuestionOption(value="with_family", display="Living with family"),
                    QuestionOption(value="with_partner", display="Living with partner/spouse"),
                    QuestionOption(value="with_roommates", display="Living with roommates"),
                    QuestionOption(value="homeless", display="Currently homeless"),
                    QuestionOption(value="other", display="Other")
                ],
                allow_free_text=True
            ),
            
            'employment_status': Question(
                id='employment_status',
                text="What is your current employment status?",
                type=QuestionType.MCQ,
                category='social_environmental',
                options=[
                    QuestionOption(value="full_time", display="Full-time employed"),
                    QuestionOption(value="part_time", display="Part-time employed"),
                    QuestionOption(value="self_employed", display="Self-employed"),
                    QuestionOption(value="unemployed", display="Unemployed"),
                    QuestionOption(value="student", display="Student"),
                    QuestionOption(value="retired", display="Retired"),
                    QuestionOption(value="disabled", display="On disability"),
                    QuestionOption(value="other", display="Other")
                ]
            ),
            
            'financial_stress': Question(
                id='financial_stress',
                text="How would you rate your current financial stress level?",
                type=QuestionType.SCALE,
                category='social_environmental',
                options=[
                    QuestionOption(value="1", display="1 - No stress at all"),
                    QuestionOption(value="2", display="2"),
                    QuestionOption(value="3", display="3"),
                    QuestionOption(value="4", display="4"),
                    QuestionOption(value="5", display="5 - Moderate stress"),
                    QuestionOption(value="6", display="6"),
                    QuestionOption(value="7", display="7"),
                    QuestionOption(value="8", display="8"),
                    QuestionOption(value="9", display="9"),
                    QuestionOption(value="10", display="10 - Extreme stress")
                ]
            ),
            
            'social_support': Question(
                id='social_support',
                text="How would you rate your current level of social support?",
                type=QuestionType.SCALE,
                category='social_environmental',
                options=[
                    QuestionOption(value="1", display="1 - No support at all"),
                    QuestionOption(value="2", display="2"),
                    QuestionOption(value="3", display="3"),
                    QuestionOption(value="4", display="4"),
                    QuestionOption(value="5", display="5 - Moderate support"),
                    QuestionOption(value="6", display="6"),
                    QuestionOption(value="7", display="7"),
                    QuestionOption(value="8", display="8"),
                    QuestionOption(value="9", display="9"),
                    QuestionOption(value="10", display="10 - Excellent support")
                ]
            )
        }
    
    def _init_question_sequence(self):
        """Initialize the sequence of questions to ask."""
        # Build a comprehensive question sequence based on categories
        self.question_sequence = []
        
        # Psychiatric History Section
        self.question_sequence.extend([
            'psych_dx_history',
            'psych_dx_details',
            'psych_dx_when',
            'psych_treatment_history',
            'therapy_details',
            'past_medications',
            'other_treatment_details',
            'hospitalizations',
            'hospitalization_details',
            'ect_history',
            'ect_details'
        ])
        
        # Medications Section
        self.question_sequence.extend([
            'current_meds_taking',
            'current_meds_list',
            'medication_adherence',
            'med_allergies',
            'allergy_details',
            'otc_supplements',
            'otc_details'
        ])
        
        # Medical History Section
        self.question_sequence.extend([
            'medical_history_summary',
            'chronic_illnesses',
            'neurological_problems',
            'head_injury',
            'head_injury_details',
            'seizure_history',
            'seizure_details',
            'pregnancy_status',
            'recent_infections'
        ])
        
        # Substance Use Section
        self.question_sequence.extend([
            'alcohol_use',
            'drug_use',
            'prescription_abuse',
            'prescription_abuse_details',
            'tobacco_use',
            'substance_treatment',
            'substance_treatment_details'
        ])
        
        # Cultural & Spiritual Section
        self.question_sequence.extend([
            'cultural_background',
            'cultural_beliefs_mental_health',
            'cultural_details',
            'spiritual_religious',
            'spiritual_support',
            'spiritual_support_details',
            'family_stigma'
        ])
        
        # Family History Section
        self.question_sequence.extend([
            'family_psych_history',
            'family_psych_details',
            'family_medical_history',
            'family_substance_history',
            'family_substance_details'
        ])
        
        # Social & Environmental Section
        self.question_sequence.extend([
            'living_situation',
            'employment_status',
            'financial_stress',
            'social_support'
        ])
        
        # Filter out conditional questions that may not be applicable
        self.question_sequence = [q for q in self.question_sequence if q in self.questions]
    
    def start_assessment(self) -> Dict[str, Any]:
        """Start the basic info assessment"""
        self.current_question = 0
        self.current_section = 'psychiatric_history'
        return {
            "status": "started",
            "question": self._get_question_by_id(self.question_sequence[0]),
            "progress": f"1/{len(self.question_sequence)}",
            "section": self.current_section
        }
    
    def _get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a question by its ID"""
        return self.questions.get(question_id)
    
    def _evaluate_condition(self, condition: str, response: str) -> bool:
        """Evaluate if a condition is met based on the response"""
        if not condition:
            return True
        
        # Simple condition evaluation - can be enhanced
        if "==" in condition:
            field, value = condition.split("==")
            return response.lower() == value.lower()
        return True
    
    def _get_next_question(self, current_response: str) -> Optional[str]:
        """Determine the next question based on current response and conditions"""
        if self.current_question >= len(self.question_sequence):
            return None
        
        current_q_id = self.question_sequence[self.current_question]
        current_q = self._get_question_by_id(current_q_id)
        
        if not current_q:
            return None
        
        # Check if current question has follow-up questions
        if current_q.follow_up_questions:
            for option_value, followup_list in current_q.follow_up_questions.items():
                if option_value.lower() in current_response.lower():
                    # Insert follow-up questions into sequence
                    insert_index = self.current_question + 1
                    for followup_id in followup_list:
                        if followup_id not in self.question_sequence:
                            self.question_sequence.insert(insert_index, followup_id)
                            insert_index += 1
                    break
        
        # Move to next question
        self.current_question += 1
        
        # Update current section
        if self.current_question < len(self.question_sequence):
            next_q_id = self.question_sequence[self.current_question]
            next_q = self._get_question_by_id(next_q_id)
            if next_q:
                self.current_section = next_q.category
        
        return self.question_sequence[self.current_question] if self.current_question < len(self.question_sequence) else None
    
    def process_response(self, response: str) -> Dict[str, Any]:
        """Process user response and get next question"""
        if self.current_question >= len(self.question_sequence):
            return {"error": "Assessment already completed"}
        
        # Store the response
        current_q_id = self.question_sequence[self.current_question]
        current_q = self._get_question_by_id(current_q_id)
        
        if current_q:
            # Store response in the data model
            self._store_response(current_q, response)
        
        # Get next question
        next_q_id = self._get_next_question(response)
        
        # Check if assessment is complete
        if not next_q_id:
            self.data.completion_timestamp = datetime.now()
            self.data.sections_completed = list(set(self.sections))
            return {
                "status": "completed",
                "data": self.data.dict(),
                "summary": self._generate_summary(),
                "sections_completed": self.data.sections_completed
            }
        
        # Return next question
        next_q = self._get_question_by_id(next_q_id)
        return {
            "status": "question",
            "question": next_q,
            "progress": f"{self.current_question + 1}/{len(self.question_sequence)}",
            "section": self.current_section
        }
    
    def _store_response(self, question: Question, response: str):
        """Store the response in the appropriate data field"""
        # Map question IDs to data model fields
        field_mapping = {
            'psych_dx_history': 'past_psych_dx',
            'psych_dx_details': 'past_psych_dx',
            'psych_dx_when': 'past_psych_dx',
            'psych_treatment_history': 'past_psych_treatment',
            'therapy_details': 'past_psych_treatment',
            'past_medications': 'past_psych_treatment',
            'other_treatment_details': 'past_psych_treatment',
            'hospitalizations': 'hospitalizations',
            'hospitalization_details': 'hospitalizations',
            'ect_history': 'ect_history',
            'ect_details': 'ect_history',
            'current_meds_taking': 'current_meds',
            'current_meds_list': 'current_meds',
            'medication_adherence': 'medication_adherence',
            'med_allergies': 'med_allergies',
            'allergy_details': 'med_allergies',
            'otc_supplements': 'otc_supplements',
            'otc_details': 'otc_supplements',
            'medical_history_summary': 'medical_history_summary',
            'chronic_illnesses': 'chronic_illnesses',
            'neurological_problems': 'neurological_problems',
            'head_injury': 'head_injury',
            'head_injury_details': 'head_injury',
            'seizure_history': 'seizure_history',
            'seizure_details': 'seizure_history',
            'pregnancy_status': 'pregnancy_status',
            'recent_infections': 'recent_infections',
            'alcohol_use': 'alcohol_use',
            'drug_use': 'drug_use',
            'prescription_abuse': 'prescription_drug_abuse',
            'prescription_abuse_details': 'prescription_drug_abuse',
            'tobacco_use': 'tobacco_use',
            'substance_treatment': 'substance_treatment',
            'substance_treatment_details': 'substance_treatment',
            'cultural_background': 'cultural_background',
            'cultural_beliefs_mental_health': 'cultural_beliefs',
            'cultural_details': 'cultural_beliefs',
            'spiritual_religious': 'spiritual_supports',
            'spiritual_support': 'spiritual_supports',
            'spiritual_support_details': 'spiritual_supports',
            'family_stigma': 'family_mental_health_stigma',
            'family_psych_history': 'family_psych_history',
            'family_psych_details': 'family_psych_history',
            'family_medical_history': 'family_medical_history',
            'family_substance_history': 'family_substance_history',
            'family_substance_details': 'family_substance_history',
            'living_situation': 'living_situation',
            'employment_status': 'employment_status',
            'financial_stress': 'financial_stress',
            'social_support': 'social_support'
        }
        
        field_name = field_mapping.get(question.id)
        if field_name:
            # Handle special cases
            if field_name == 'current_meds' and question.id == 'current_meds_list':
                # Store medication list as a dictionary
                self.data.current_meds['medications'] = response
            elif field_name in ['past_psych_dx', 'past_psych_treatment', 'hospitalizations', 'ect_history']:
                # Append to existing field if it already has content
                current_value = getattr(self.data, field_name)
                if current_value:
                    setattr(self.data, field_name, f"{current_value}; {response}")
                else:
                    setattr(self.data, field_name, response)
            else:
                setattr(self.data, field_name, response)
    
    def _generate_summary(self) -> str:
        """Generate a comprehensive summary of collected data"""
        summary_parts = []
        
        # Psychiatric History
        if self.data.past_psych_dx:
            summary_parts.append(f"Psychiatric History: {self.data.past_psych_dx}")
        if self.data.past_psych_treatment:
            summary_parts.append(f"Treatment: {self.data.past_psych_treatment}")
        if self.data.hospitalizations:
            summary_parts.append(f"Hospitalizations: {self.data.hospitalizations}")
        if self.data.ect_history:
            summary_parts.append(f"ECT History: {self.data.ect_history}")
        
        # Medications
        if self.data.current_meds:
            summary_parts.append(f"Current Medications: {self.data.current_meds}")
        if self.data.med_allergies:
            summary_parts.append(f"Medication Allergies: {self.data.med_allergies}")
        if self.data.otc_supplements:
            summary_parts.append(f"OTC/Supplements: {self.data.otc_supplements}")
        
        # Medical History
        if self.data.medical_history_summary:
            summary_parts.append(f"Medical History: {self.data.medical_history_summary}")
        if self.data.chronic_illnesses:
            summary_parts.append(f"Chronic Illnesses: {self.data.chronic_illnesses}")
        if self.data.neurological_problems:
            summary_parts.append(f"Neurological Issues: {self.data.neurological_problems}")
        
        # Substance Use
        if self.data.alcohol_use:
            summary_parts.append(f"Alcohol Use: {self.data.alcohol_use}")
        if self.data.drug_use:
            summary_parts.append(f"Drug Use: {self.data.drug_use}")
        if self.data.tobacco_use:
            summary_parts.append(f"Tobacco Use: {self.data.tobacco_use}")
        
        # Cultural & Spiritual
        if self.data.cultural_background:
            summary_parts.append(f"Cultural Background: {self.data.cultural_background}")
        if self.data.spiritual_supports:
            summary_parts.append(f"Spiritual/Religious: {self.data.spiritual_supports}")
        
        # Family History
        if self.data.family_psych_history:
            summary_parts.append(f"Family Mental Health: {self.data.family_psych_history}")
        if self.data.family_medical_history:
            summary_parts.append(f"Family Medical: {self.data.family_medical_history}")
        
        # Social & Environmental
        if self.data.living_situation:
            summary_parts.append(f"Living Situation: {self.data.living_situation}")
        if self.data.employment_status:
            summary_parts.append(f"Employment: {self.data.employment_status}")
        if self.data.financial_stress:
            summary_parts.append(f"Financial Stress: {self.data.financial_stress}")
        if self.data.social_support:
            summary_parts.append(f"Social Support: {self.data.social_support}")
        
        return "; ".join(summary_parts) if summary_parts else "No information collected"
    
    def get_assessment_progress(self) -> Dict[str, Any]:
        """Get current assessment progress"""
        if not self.question_sequence:
            return {"error": "Assessment not started"}
        
        total_questions = len(self.question_sequence)
        completed_questions = self.current_question if self.current_question > 0 else 0
        progress_percentage = (completed_questions / total_questions) * 100 if total_questions > 0 else 0
        
        return {
            "total_questions": total_questions,
            "completed_questions": completed_questions,
            "progress_percentage": round(progress_percentage, 1),
            "current_section": self.current_section,
            "sections_completed": self.data.sections_completed
        }

# Global instance
_basic_info_tool = BasicInfoTool()

def ask_basic_info(action: str, **kwargs) -> Dict[str, Any]:
    """Tool function for basic info collection"""
    try:
        if action == "start":
            return _basic_info_tool.start_assessment()
        elif action == "respond":
            response = kwargs.get("response")
            if not response:
                return {"error": "response is required"}
            return _basic_info_tool.process_response(response)
        elif action == "get_data":
            return _basic_info_tool.data.dict()
        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        logger.error(f"Error in ask_basic_info: {e}")
        return {"error": f"Tool execution failed: {str(e)}"} 
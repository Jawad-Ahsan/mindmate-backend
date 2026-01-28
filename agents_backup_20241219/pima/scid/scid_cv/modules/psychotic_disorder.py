# scid_cv/modules/psychotic_disorders.py
"""
SCID-CV Psychotic Disorders Module
Implements DSM-5 criteria for Schizophrenia and related psychotic disorders
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_psychotic_module() -> SCIDModule:
    """
    Create the Psychotic Disorders module for SCID-CV
    
    DSM-5 Criteria for Schizophrenia:
    A. Two or more positive/negative symptoms for significant time during 1-month period
    B. Functional decline
    C. Continuous signs for at least 6 months
    D. Exclusion of other disorders
    E. Not due to substance/medical condition
    """
    
    questions = [
        # Initial screening
        SCIDQuestion(
            id="ps_001",
            text="Have you ever experienced unusual thoughts, perceptions, or beliefs that others found strange?",
            simple_text="Have you ever had unusual thoughts, seen or heard things others didn't, or believed things others thought were strange?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="psychotic_screening",
            help_text="This includes hearing voices, seeing things, or having beliefs others don't share"
        ),
        
        # Criterion A1: Delusions
        SCIDQuestion(
            id="ps_002",
            text="Have you had strong beliefs that others thought were unrealistic or untrue?",
            simple_text="Have you believed things very strongly that other people said weren't real or true?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="delusions",
            help_text="These might be beliefs about being followed, having special powers, or conspiracy theories"
        ),
        
        SCIDQuestion(
            id="ps_003",
            text="What types of unusual beliefs have you had?",
            simple_text="What kinds of things have you believed that others thought were strange?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "People were following me or watching me",
                "I had special powers or abilities",
                "People were trying to harm me or poison me",
                "I was someone famous or important",
                "My thoughts were being controlled by others",
                "Others could read my thoughts",
                "Messages on TV/radio were meant for me",
                "My body was changing in unusual ways",
                "I was being tested or experimented on",
                "Religious or spiritual beliefs others found extreme",
                "I haven't had unusual beliefs"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="delusion_types"
        ),
        
        SCIDQuestion(
            id="ps_004",
            text="How convinced were you that these beliefs were true?",
            simple_text="How sure were you that these things you believed were really happening?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not convinced", "Somewhat convinced", "Very convinced", "Completely certain"],
            required=False,
            criteria_weight=1.0,
            symptom_category="delusion_conviction"
        ),
        
        # Criterion A2: Hallucinations
        SCIDQuestion(
            id="ps_005",
            text="Have you heard voices or sounds that others couldn't hear?",
            simple_text="Have you heard voices talking or other sounds when no one else was around or when others couldn't hear them?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="auditory_hallucinations"
        ),
        
        SCIDQuestion(
            id="ps_006",
            text="What did the voices say or sound like?",
            simple_text="What did you hear when you heard these voices or sounds?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Voices talking about me",
                "Voices giving me commands or instructions",
                "Voices commenting on what I was doing",
                "Multiple voices talking to each other",
                "My own thoughts spoken out loud",
                "Unclear mumbling or whispering",
                "Music or other sounds",
                "Calling my name",
                "Threatening or scary voices",
                "I haven't heard voices or unusual sounds"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="hallucination_content"
        ),
        
        SCIDQuestion(
            id="ps_007",
            text="Have you seen things that others couldn't see?",
            simple_text="Have you seen things (people, objects, lights, shadows) that others couldn't see or said weren't there?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="visual_hallucinations"
        ),
        
        SCIDQuestion(
            id="ps_008",
            text="Have you experienced unusual sensations in your body?",
            simple_text="Have you felt strange physical sensations that others couldn't explain?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Feeling like insects crawling on skin",
                "Unusual smells that others couldn't smell", 
                "Strange tastes in mouth",
                "Feeling touched when no one was there",
                "Feeling like body parts were changing",
                "Electric or burning sensations",
                "I haven't had unusual physical sensations"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="other_hallucinations"
        ),
        
        # Criterion A3: Disorganized thinking/speech
        SCIDQuestion(
            id="ps_009",
            text="Have people told you that your speech or thinking was hard to follow?",
            simple_text="Have people said that the way you talk or your thoughts are confusing or hard to understand?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="disorganized_thinking"
        ),
        
        SCIDQuestion(
            id="ps_010",
            text="Have you experienced problems with your thinking or speech?",
            simple_text="Have you had trouble with thinking clearly or speaking in a way others understand?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Thoughts jumping from topic to topic quickly",
                "Losing track of what I was saying mid-sentence",
                "Making up new words that others don't understand",
                "Speaking in rhymes or word games",
                "Thoughts feeling blocked or stopped",
                "Ideas not connecting logically",
                "Others saying I'm not making sense",
                "I haven't had these problems"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="thought_disorganization"
        ),
        
        # Criterion A4: Disorganized or abnormal motor behavior
        SCIDQuestion(
            id="ps_011",
            text="Have you behaved in ways that others found very strange or inappropriate?",
            simple_text="Have you acted in ways that others thought were very odd or didn't make sense for the situation?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="disorganized_behavior"
        ),
        
        SCIDQuestion(
            id="ps_012",
            text="What kinds of unusual behaviors have you shown?",
            simple_text="What have you done that others found strange or concerning?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Dressing inappropriately for weather/situation",
                "Acting childlike or silly at wrong times",
                "Doing repetitive movements or gestures",
                "Staying in unusual positions for long periods",
                "Not moving or responding when spoken to",
                "Being very agitated or restless",
                "Unpredictable or aggressive behavior",
                "I haven't behaved unusually"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="behavior_examples"
        ),
        
        # Criterion A5: Negative symptoms
        SCIDQuestion(
            id="ps_013",
            text="Have you experienced a significant decrease in emotions or motivation?",
            simple_text="Have you had much less emotion, motivation, or interest in things than usual?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="negative_symptoms"
        ),
        
        SCIDQuestion(
            id="ps_014",
            text="Which of these changes have you experienced?",
            simple_text="What changes have you noticed in yourself?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Much less emotional expression on my face",
                "Speaking much less than usual",
                "Little interest in activities I used to enjoy", 
                "Difficulty starting or finishing activities",
                "Less interest in being around other people",
                "Difficulty experiencing pleasure",
                "Poor hygiene or self-care",
                "I haven't experienced these changes"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="negative_symptom_types"
        ),
        
        SCIDQuestion(
            id="ps_015",
            text="How long did these symptoms last when they were most severe?",
            simple_text="During the worst period, how long did these experiences continue?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "A few days",
                "About a week",
                "2-3 weeks", 
                "About a month",
                "2-3 months",
                "4-6 months",
                "More than 6 months",
                "They're ongoing"
            ],
            required=True,
            criteria_weight=2.0,
            symptom_category="symptom_duration"
        ),
        
        # Criterion B: Functional decline
        SCIDQuestion(
            id="ps_016",
            text="During these experiences, was there a significant decline in how well you functioned?",
            simple_text="When you had these experiences, did you have much more trouble with work, relationships, or taking care of yourself?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="functional_decline"
        ),
        
        SCIDQuestion(
            id="ps_017",
            text="In which areas did your functioning decline?",
            simple_text="What areas of your life became much more difficult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family and friends",
                "Taking care of personal hygiene",
                "Managing daily tasks and responsibilities",
                "Living independently",
                "Social interactions and communication",
                "My functioning didn't decline significantly"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="functional_areas"
        ),
        
        # Criterion C: Duration (6 months)
        SCIDQuestion(
            id="ps_018",
            text="How long in total have you experienced any of these difficulties?",
            simple_text="Overall, how long have you been dealing with any of these problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-3 months",
                "3-6 months",
                "6 months to 1 year", 
                "1-2 years",
                "2-5 years",
                "More than 5 years"
            ],
            required=True,
            criteria_weight=2.0,
            symptom_category="total_duration"
        ),
        
        # Onset and course
        SCIDQuestion(
            id="ps_019",
            text="How did these problems begin?",
            simple_text="How did these difficulties start?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Very suddenly over a few days",
                "Gradually over several weeks",
                "Gradually over several months",
                "So gradually I can't pinpoint when",
                "After a stressful event",
                "I'm not sure how they began"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="onset_pattern"
        ),
        
        SCIDQuestion(
            id="ps_020",
            text="At what age did you first experience these types of problems?",
            simple_text="How old were you when these kinds of problems first started?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Childhood (under 13)",
                "Early teens (13-16)",
                "Late teens (17-19)",
                "Early twenties (20-25)",
                "Late twenties (26-30)",
                "Thirties (31-40)",
                "Over 40"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="age_onset"
        ),
        
        # Hospitalization history
        SCIDQuestion(
            id="ps_021",
            text="Have you ever been hospitalized because of these experiences?",
            simple_text="Have you ever had to stay in a hospital because of these problems?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="hospitalization"
        ),
        
        # Current status
        SCIDQuestion(
            id="ps_022",
            text="How are these symptoms affecting you currently?",
            simple_text="How are these problems affecting you right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No current problems", "Mild problems", "Moderate problems", "Severe problems"],
            required=True,
            criteria_weight=1.5,
            symptom_category="current_severity"
        ),
        
        # Insight
        SCIDQuestion(
            id="ps_023",
            text="Do you believe that these experiences indicate a mental health condition?",
            simple_text="Do you think these experiences show that you might have a mental health problem?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I believe I have a mental health condition",
                "I'm not sure but it's possible",
                "I don't think so, but others say I do",
                "No, I don't believe there's anything wrong",
                "I'm confused about what's happening"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="insight_level"
        ),
        
        # Impact on daily life
        SCIDQuestion(
            id="ps_024",
            text="How much do these experiences interfere with your daily life?",
            simple_text="How much do these problems make it hard to do everyday things?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="daily_interference"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A. Two or more of the following for significant portion of time during 1-month period: delusions, hallucinations, disorganized speech, grossly disorganized or abnormal motor behavior, negative symptoms",
        "B. For significant portion of time, level of functioning is markedly below level achieved prior to onset",
        "C. Continuous signs of disturbance persist for at least 6 months",
        "D. Schizoaffective disorder and depressive/bipolar disorder with psychotic features ruled out",
        "E. Not attributable to physiological effects of substance or medical condition",
        "F. If autism spectrum disorder or communication disorder present, prominent delusions/hallucinations must be present for at least 1 month"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.5,      # Minimal functional impairment
        "moderate": 0.65, # Some functional impairment
        "severe": 0.8     # Significant functional impairment
    }
    
    return SCIDModule(
        id="PSYCHOTIC_DISORDERS",
        name="Psychotic Disorders (Schizophrenia Spectrum)",
        description="Assessment module for Schizophrenia and related psychotic disorders based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.65,
        estimated_time_mins=20,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="psychotic_disorders",
        version="1.0",
        clinical_notes="This module screens for psychotic symptoms and should be interpreted by qualified mental health professionals. Positive findings warrant comprehensive clinical evaluation."
    )
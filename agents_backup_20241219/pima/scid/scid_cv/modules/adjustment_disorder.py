# scid_cv/modules/adjustment_disorder.py
"""
SCID-CV Adjustment Disorder Module
Implements DSM-5 criteria for Adjustment Disorder assessment
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_adjustment_disorder_module() -> SCIDModule:
    """
    Create the Adjustment Disorder module for SCID-CV
    
    DSM-5 Criteria for Adjustment Disorder:
    A. Emotional/behavioral symptoms in response to identifiable stressor
    B. Symptoms are clinically significant (out of proportion OR significant impairment)
    C. Symptoms do not meet criteria for another disorder
    D. Symptoms not normal bereavement
    E. Once stressor terminated, symptoms don't persist >6 months
    """
    
    questions = [
        # Initial screening and stressor identification
        SCIDQuestion(
            id="ad_001",
            text="Have you experienced a significant stressful event or major life change recently?",
            simple_text="Have you gone through a stressful event or big life change recently?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="stressor_present",
            help_text="This could be within the past 6 months and includes any major life change"
        ),
        
        SCIDQuestion(
            id="ad_002",
            text="What stressful event or life change occurred?",
            simple_text="What stressful thing happened or what big change occurred in your life?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Job loss or work problems",
                "Relationship breakup or divorce",
                "Death of someone close (not spouse/child/parent)",
                "Serious illness or injury (self or loved one)",
                "Financial problems or bankruptcy",
                "Moving to a new place",
                "Starting school or changing schools",
                "Retirement",
                "Legal problems",
                "Family conflict or problems",
                "Other major life change",
                "No significant stressful events"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="stressor_type"
        ),
        
        SCIDQuestion(
            id="ad_003",
            text="When did this stressful event occur?",
            simple_text="How long ago did this stressful event happen?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Within the past month",
                "1-3 months ago",
                "3-6 months ago",
                "6 months to 1 year ago",
                "More than 1 year ago"
            ],
            required=True,
            criteria_weight=2.0,
            symptom_category="stressor_timing",
            help_text="For Adjustment Disorder, symptoms should begin within 6 months of the stressor"
        ),
        
        # Criterion A: Emotional/behavioral symptoms in response to stressor
        SCIDQuestion(
            id="ad_004",
            text="Did emotional or behavioral problems begin within 6 months of this stressful event?",
            simple_text="Did you start having emotional problems or behavior changes within 6 months after this stressful event?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="symptom_onset"
        ),
        
        SCIDQuestion(
            id="ad_005",
            text="What emotional or behavioral symptoms did you develop?",
            simple_text="What emotional problems or behavior changes did you start having?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Feeling very sad or depressed",
                "Feeling very anxious or worried",
                "Feeling angry or irritable",
                "Feeling hopeless about the future",
                "Having trouble sleeping",
                "Losing interest in activities",
                "Withdrawing from family and friends",
                "Acting out or being rebellious",
                "Having trouble at work or school",
                "Using alcohol or drugs more than usual",
                "I didn't develop new symptoms"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="symptom_types"
        ),
        
        SCIDQuestion(
            id="ad_006",
            text="How quickly did these symptoms begin after the stressful event?",
            simple_text="How soon after the stressful event did these problems start?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Within days of the event",
                "Within 2-4 weeks",
                "Within 1-3 months",
                "Within 3-6 months",
                "More than 6 months later",
                "The symptoms didn't start after the event"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="symptom_timeline"
        ),
        
        # Criterion B: Clinical significance
        SCIDQuestion(
            id="ad_007",
            text="Are your emotional reactions much stronger than would be expected?",
            simple_text="Are your emotional reactions much stronger than most people would have in this situation?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="disproportionate_response"
        ),
        
        SCIDQuestion(
            id="ad_008",
            text="Have these symptoms caused significant problems in your life?",
            simple_text="Have these emotional problems caused big difficulties in your life?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="significant_impairment"
        ),
        
        SCIDQuestion(
            id="ad_009",
            text="In which areas have these symptoms caused problems?",
            simple_text="What areas of your life have been affected by these emotional problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family",
                "Friendships and social relationships",
                "Romantic relationships",
                "Parenting or caregiving responsibilities",
                "Daily activities and self-care",
                "Physical health",
                "Overall quality of life",
                "These symptoms haven't caused significant problems"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="impairment_areas"
        ),
        
        # Severity and interference
        SCIDQuestion(
            id="ad_010",
            text="How much do these symptoms interfere with your daily functioning?",
            simple_text="How much do these emotional problems make it hard to do everyday things?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="functional_interference"
        ),
        
        # Symptoms by subtype
        # With depressed mood
        SCIDQuestion(
            id="ad_011",
            text="Since the stressful event, have you felt persistently sad or hopeless?",
            simple_text="Since the stressful event, have you felt very sad or hopeless most of the time?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="depressed_mood"
        ),
        
        SCIDQuestion(
            id="ad_012",
            text="How often do you feel sad or down since the stressful event?",
            simple_text="How often have you felt sad or down since the stressful event?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Rarely", "Sometimes", "Often", "Most of the time"],
            required=False,
            criteria_weight=1.0,
            symptom_category="sadness_frequency"
        ),
        
        # With anxiety
        SCIDQuestion(
            id="ad_013",
            text="Since the stressful event, have you felt persistently anxious or worried?",
            simple_text="Since the stressful event, have you felt very anxious or worried most of the time?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="anxiety_symptoms"
        ),
        
        SCIDQuestion(
            id="ad_014",
            text="What do you feel anxious or worried about?",
            simple_text="What makes you feel anxious or worried?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "The same stressful situation happening again",
                "Not being able to cope with problems",
                "The future in general",
                "Work or school performance",
                "Relationships with others",
                "Financial security",
                "Health concerns",
                "I don't feel particularly anxious"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="anxiety_content"
        ),
        
        # With mixed anxiety and depressed mood
        SCIDQuestion(
            id="ad_015",
            text="Do you experience both significant sadness and anxiety since the event?",
            simple_text="Since the stressful event, do you feel both very sad and very anxious?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="mixed_symptoms"
        ),
        
        # With disturbance of conduct
        SCIDQuestion(
            id="ad_016",
            text="Since the stressful event, have you acted out or behaved in problematic ways?",
            simple_text="Since the stressful event, have you done things that got you in trouble or that you normally wouldn't do?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="conduct_problems"
        ),
        
        SCIDQuestion(
            id="ad_017",
            text="What behavioral problems have you had since the stressful event?",
            simple_text="What problem behaviors have you had since the stressful event?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Being much more aggressive or angry",
                "Violating rules or breaking laws",
                "Reckless or dangerous behavior",
                "Destroying property",
                "Fighting with others",
                "Skipping work or school frequently",
                "Using alcohol or drugs excessively",
                "I haven't had behavioral problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="behavioral_symptoms"
        ),
        
        # With mixed disturbance of emotions and conduct
        SCIDQuestion(
            id="ad_018",
            text="Do you have both emotional symptoms and behavioral problems since the event?",
            simple_text="Since the stressful event, do you have both emotional problems AND behavior problems?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="mixed_emotional_behavioral"
        ),
        
        # Duration and course
        SCIDQuestion(
            id="ad_019",
            text="How long have you been experiencing these symptoms?",
            simple_text="How long have you been having these emotional or behavioral problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-3 months",
                "3-6 months",
                "6 months to 1 year",
                "More than 1 year"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="symptom_duration"
        ),
        
        SCIDQuestion(
            id="ad_020",
            text="Is the stressful situation ongoing or has it been resolved?",
            simple_text="Is the stressful situation still happening, or is it over?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "The situation is completely resolved",
                "The situation is mostly resolved",
                "The situation is partly resolved",
                "The situation is ongoing",
                "The situation has gotten worse"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="stressor_status"
        ),
        
        # Criterion E: Duration after stressor resolution
        SCIDQuestion(
            id="ad_021",
            text="If the stressful situation is over, are your symptoms improving?",
            simple_text="If the stressful situation has ended, are your emotional problems getting better?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "The stressful situation is still ongoing",
                "Yes, symptoms are clearly improving",
                "Symptoms are slowly improving",
                "Symptoms are about the same",
                "Symptoms are getting worse",
                "It's too soon to tell"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="symptom_improvement"
        ),
        
        # Coping and support
        SCIDQuestion(
            id="ad_022",
            text="How are you coping with the stressful situation?",
            simple_text="What are you doing to deal with the stressful situation?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Talking to family and friends",
                "Seeking professional help or counseling",
                "Using relaxation or stress management techniques",
                "Staying busy with activities",
                "Avoiding thinking about it",
                "Using alcohol or drugs to cope",
                "I'm not actively coping",
                "I don't know how to cope"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="coping_strategies"
        ),
        
        SCIDQuestion(
            id="ad_023",
            text="Do you have adequate social support?",
            simple_text="Do you have enough support from family, friends, or others?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I have strong support",
                "I have some support but could use more",
                "I have minimal support",
                "I have no support",
                "I prefer to handle things alone"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="social_support"
        ),
        
        # Comparison to previous functioning
        SCIDQuestion(
            id="ad_024",
            text="How does your current functioning compare to before the stressful event?",
            simple_text="How well are you doing now compared to before the stressful event happened?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Much worse", "Somewhat worse", "About the same", "Better"],
            required=True,
            criteria_weight=1.5,
            symptom_category="functioning_comparison"
        ),
        
        # Risk assessment
        SCIDQuestion(
            id="ad_025",
            text="Have you had thoughts of hurting yourself since the stressful event?",
            simple_text="Since the stressful event, have you thought about hurting yourself?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="self_harm_thoughts"
        ),
        
        # Treatment and help-seeking
        SCIDQuestion(
            id="ad_026",
            text="Are you currently receiving any help for these problems?",
            simple_text="Are you getting any help or treatment for these emotional problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I'm not getting any help",
                "I'm in counseling or therapy",
                "I'm taking medication",
                "I'm using self-help resources",
                "I'm getting help from family/friends",
                "I'm considering getting professional help"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="current_treatment"
        ),
        
        # Overall severity
        SCIDQuestion(
            id="ad_027",
            text="How would you rate the overall severity of your adjustment difficulties?",
            simple_text="Overall, how bad are your problems adjusting to the stressful situation?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problems", "Mild problems", "Moderate problems", "Severe problems"],
            required=True,
            criteria_weight=1.0,
            symptom_category="overall_severity"
        ),
        
        # Insight and understanding
        SCIDQuestion(
            id="ad_028",
            text="Do you believe your emotional problems are related to the stressful event?",
            simple_text="Do you think your emotional problems are connected to the stressful event that happened?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="insight_connection"
        ),
        
        # Resilience factors
        SCIDQuestion(
            id="ad_029",
            text="What strengths or resources are helping you get through this difficult time?",
            simple_text="What strengths or resources are helping you deal with this difficult situation?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Strong family relationships",
                "Good friends who support me",
                "Religious or spiritual beliefs",
                "Previous experience handling stress",
                "Good problem-solving skills",
                "Physical health and energy",
                "Financial resources",
                "Professional help",
                "I don't feel I have many strengths or resources"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="resilience_factors"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A. The development of emotional or behavioral symptoms in response to an identifiable stressor(s) occurring within 3 months of the onset of the stressor(s)",
        "B. These symptoms or behaviors are clinically significant, as evidenced by one or both of the following:",
        "   1. Marked distress that is out of proportion to the severity or intensity of the stressor",
        "   2. Significant impairment in social, occupational, or other important areas of functioning",
        "C. The stress-related disturbance does not meet the criteria for another mental disorder",
        "D. The symptoms do not represent normal bereavement",
        "E. Once the stressor or its consequences have terminated, the symptoms do not persist for more than an additional 6 months",
        "",
        "SUBTYPES:",
        "- With depressed mood",
        "- With anxiety", 
        "- With mixed anxiety and depressed mood",
        "- With disturbance of conduct",
        "- With mixed disturbance of emotions and conduct",
        "- Unspecified"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.4,      # Minimal impairment, symptoms manageable
        "moderate": 0.6,  # Moderate impairment and distress
        "severe": 0.8     # Significant impairment and distress
    }
    
    return SCIDModule(
        id="ADJUSTMENT_DISORDER",
        name="Adjustment Disorder",
        description="Assessment module for Adjustment Disorder based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.5,
        estimated_time_mins=15,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="trauma_stressor_disorders",
        version="1.0",
        clinical_notes="Adjustment Disorder requires symptoms beginning within 3 months of an identifiable stressor, causing marked distress or significant impairment, not meeting criteria for another disorder, and resolving within 6 months after stressor termination."
    )
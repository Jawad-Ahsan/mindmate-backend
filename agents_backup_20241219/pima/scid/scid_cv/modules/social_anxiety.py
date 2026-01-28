# scid_cv/modules/social_anxiety.py
"""
SCID-CV Social Anxiety Disorder (Social Phobia) Module
Implements DSM-5 criteria for Social Anxiety Disorder assessment
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_social_anxiety_module() -> SCIDModule:
    """
    Create the Social Anxiety Disorder module for SCID-CV
    
    DSM-5 Criteria for Social Anxiety Disorder:
    A. Marked fear or anxiety about social situations
    B. Fear of negative evaluation
    C. Social situations almost always provoke fear/anxiety
    D. Social situations avoided or endured with distress
    E. Fear/anxiety out of proportion to actual threat
    F. Persistent (6+ months)
    G. Significant distress or impairment
    H. Not due to substance/medical condition
    I. Not better explained by another disorder
    """
    
    questions = [
        # Criterion A: Marked fear or anxiety about social situations
        SCIDQuestion(
            id="sa_001",
            text="Do you have a strong fear or anxiety about social situations where you might be watched or judged by other people?",
            simple_text="Are you very afraid or nervous in social situations where people might watch or judge you?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="social_fear",
            help_text="This includes situations like meeting new people, eating in public, or giving presentations"
        ),
        
        SCIDQuestion(
            id="sa_002",
            text="Which of these social situations make you feel very afraid or anxious?",
            simple_text="Which social situations make you feel very scared or nervous?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Meeting new people or strangers",
                "Talking in groups or at parties",
                "Eating or drinking in front of others",
                "Speaking up in meetings or classes", 
                "Making phone calls in public",
                "Using public restrooms",
                "Dating or romantic situations",
                "Being the center of attention",
                "Giving presentations or speeches",
                "Performing in front of others",
                "Writing or signing documents while being watched",
                "None of these situations bother me"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="social_situations",
            help_text="Select all situations that cause you significant fear or anxiety"
        ),
        
        SCIDQuestion(
            id="sa_003",
            text="How intense is your fear or anxiety in these social situations?",
            simple_text="How strong is your fear when you're in these social situations?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No fear", "Mild fear", "Moderate fear", "Severe fear"],
            required=True,
            criteria_weight=1.0,
            symptom_category="fear_intensity"
        ),
        
        # Criterion B: Fear of negative evaluation
        SCIDQuestion(
            id="sa_004",
            text="Are you specifically afraid that you will act in a way that will be embarrassing or humiliating?",
            simple_text="Are you worried that you'll do something embarrassing or that will make you look bad?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="embarrassment_fear",
            help_text="This includes fears of saying something wrong, looking nervous, or being rejected"
        ),
        
        SCIDQuestion(
            id="sa_005",
            text="Are you afraid that others will judge you negatively, criticize you, or reject you?",
            simple_text="Do you worry that other people will think badly of you or reject you?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="negative_evaluation",
            help_text="This includes fears of being seen as anxious, weird, boring, or stupid"
        ),
        
        SCIDQuestion(
            id="sa_006",
            text="What specific things are you afraid people will notice about you?",
            simple_text="What are you worried people will notice about you that would be embarrassing?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Signs of anxiety (sweating, shaking, blushing)",
                "My voice trembling or breaking",
                "Not knowing what to say",
                "Looking nervous or uncomfortable",
                "Making mistakes when speaking",
                "My appearance or how I look",
                "Being boring or uninteresting",
                "Acting weird or different",
                "Showing that I'm not confident",
                "I'm not worried about people noticing anything"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="feared_observations"
        ),
        
        # Criterion C: Social situations almost always provoke fear/anxiety
        SCIDQuestion(
            id="sa_007",
            text="Do these social situations almost always make you feel afraid or anxious?",
            simple_text="Do you feel scared or nervous almost every time you're in these social situations?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Usually", "Almost always"],
            required=True,
            criteria_weight=1.5,
            symptom_category="consistency"
        ),
        
        SCIDQuestion(
            id="sa_008",
            text="How quickly do you start feeling anxious when you enter a social situation?",
            simple_text="How fast do you start feeling nervous when you're in a social situation?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Immediately or within seconds",
                "Within a few minutes",
                "After 10-15 minutes",
                "It varies by situation",
                "I don't usually feel anxious",
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="anxiety_onset"
        ),
        
        # Criterion D: Social situations avoided or endured with distress
        SCIDQuestion(
            id="sa_009",
            text="Do you avoid social situations because of your fear or anxiety?",
            simple_text="Do you stay away from social situations because they make you too scared or nervous?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="avoidance"
        ),
        
        SCIDQuestion(
            id="sa_010",
            text="Which of these do you do because of your social anxiety?",
            simple_text="What do you do because social situations make you anxious?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Avoid parties or social gatherings",
                "Don't speak up in groups",
                "Avoid dating or romantic relationships",
                "Skip work meetings or school presentations",
                "Eat alone instead of with others",
                "Avoid making phone calls",
                "Stay home instead of going out",
                "Leave social situations early",
                "Bring a friend everywhere for support",
                "Use alcohol or drugs to cope",
                "I don't avoid social situations"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="avoidance_behaviors"
        ),
        
        SCIDQuestion(
            id="sa_011",
            text="When you can't avoid social situations, how distressed do you feel?",
            simple_text="When you have to be in social situations, how upset or uncomfortable do you feel?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not distressed", "Mildly distressed", "Moderately distressed", "Severely distressed"],
            required=True,
            criteria_weight=1.5,
            symptom_category="distress_level"
        ),
        
        # Physical symptoms during social situations
        SCIDQuestion(
            id="sa_012",
            text="Do you experience physical symptoms when in social situations?",
            simple_text="Do you have physical symptoms like sweating or shaking in social situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Sweating or feeling hot",
                "Hands shaking or trembling",
                "Voice trembling",
                "Blushing or turning red",
                "Heart racing or pounding",
                "Feeling dizzy or lightheaded",
                "Nausea or upset stomach",
                "Muscle tension",
                "Difficulty breathing",
                "Feeling like I might faint",
                "No physical symptoms"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="physical_symptoms"
        ),
        
        # Criterion E: Fear/anxiety out of proportion
        SCIDQuestion(
            id="sa_013",
            text="Do you think your fear of social situations is much stronger than it should be?",
            simple_text="Do you think you're more afraid of social situations than you should be?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="disproportionate_fear"
        ),
        
        SCIDQuestion(
            id="sa_014",
            text="Do other people tell you that your social fears are excessive or unrealistic?",
            simple_text="Do other people say that your social fears are too much or don't make sense?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="external_perspective"
        ),
        
        # Criterion F: Duration (6+ months)
        SCIDQuestion(
            id="sa_015",
            text="How long have you been experiencing this fear of social situations?",
            simple_text="How long have you been afraid of social situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-3 months", 
                "3-6 months",
                "6 months to 1 year",
                "1-2 years",
                "2-5 years",
                "More than 5 years",
                "As long as I can remember"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="duration"
        ),
        
        # Criterion G: Significant distress or impairment
        SCIDQuestion(
            id="sa_016",
            text="Has your social anxiety caused significant problems in your life?",
            simple_text="Has being afraid of social situations caused big problems in your life?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="impairment"
        ),
        
        SCIDQuestion(
            id="sa_017",
            text="In which areas has your social anxiety caused problems?",
            simple_text="Where in your life has social anxiety caused problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family",
                "Friendships and social relationships", 
                "Romantic relationships or dating",
                "Daily activities and errands",
                "Career or education opportunities",
                "Hobbies and recreational activities",
                "Overall happiness and well-being",
                "My social anxiety hasn't caused problems"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="impairment_areas"
        ),
        
        # Impact on functioning
        SCIDQuestion(
            id="sa_018",
            text="How much has your social anxiety interfered with your work or school?",
            simple_text="How much has social anxiety made it hard to do well at work or school?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.0,
            symptom_category="work_interference"
        ),
        
        SCIDQuestion(
            id="sa_019",
            text="How much has your social anxiety affected your relationships?",
            simple_text="How much has social anxiety affected your relationships with other people?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No effect", "Mild effect", "Moderate effect", "Severe effect"],
            required=True,
            criteria_weight=1.0,
            symptom_category="relationship_impact"
        ),
        
        # Current severity
        SCIDQuestion(
            id="sa_020",
            text="How would you rate your current social anxiety overall?",
            simple_text="Overall, how bad is your social anxiety right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Minimal", "Mild", "Moderate", "Severe"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_severity"
        )
    ]
    
    # DSM-5 diagnostic criteria for reference
    dsm_criteria = [
        "A. Marked fear or anxiety about social situations where scrutiny by others is possible",
        "B. Fear that they will act in a way or show symptoms that will be negatively evaluated", 
        "C. Social situations almost always provoke fear or anxiety",
        "D. Social situations are avoided or endured with intense fear or anxiety",
        "E. Fear or anxiety is out of proportion to actual threat posed",
        "F. Fear, anxiety, or avoidance is persistent, typically lasting 6 or more months",
        "G. Fear, anxiety, or avoidance causes significant distress or impairment",
        "H. Fear, anxiety, or avoidance is not attributable to substance use or medical condition",
        "I. Fear, anxiety, or avoidance is not better explained by another mental disorder"
    ]
    
    # Severity thresholds based on functional impairment
    severity_thresholds = {
        "mild": 0.4,      # Some avoidance but minimal impairment
        "moderate": 0.6,   # Clear avoidance and moderate impairment  
        "severe": 0.8      # Extensive avoidance and severe impairment
    }
    
    return SCIDModule(
        id="SOCIAL_ANXIETY",
        name="Social Anxiety Disorder (Social Phobia)",
        description="Assessment module for Social Anxiety Disorder based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=15,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="anxiety_disorders",
        version="1.0"
    )
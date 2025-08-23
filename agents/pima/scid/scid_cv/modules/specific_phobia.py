# scid_cv/modules/specific_phobia.py
"""
SCID-CV Specific Phobia Module
Implements DSM-5 criteria for Specific Phobia assessment
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_specific_phobia_module() -> SCIDModule:
    """
    Create the Specific Phobia module for SCID-CV
    
    DSM-5 Criteria for Specific Phobia:
    A. Marked fear or anxiety about a specific object or situation
    B. Phobic object/situation almost always provokes immediate fear/anxiety
    C. Phobic object/situation is actively avoided or endured with distress
    D. Fear/anxiety is out of proportion to actual danger
    E. Fear/anxiety/avoidance is persistent (6+ months)
    F. Significant distress or impairment
    G. Not better explained by another mental disorder
    """
    
    questions = [
        # Initial screening
        SCIDQuestion(
            id="sp_001",
            text="Do you have an intense fear of any specific things, animals, or situations?",
            simple_text="Are you very afraid of any specific things, animals, or situations?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="specific_fear",
            help_text="This could be things like spiders, heights, flying, blood, or enclosed spaces"
        ),
        
        # Criterion A: Marked fear or anxiety about specific object/situation
        SCIDQuestion(
            id="sp_002",
            text="Which of these specific things or situations do you fear intensely?",
            simple_text="What specific things or situations are you very afraid of?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Animals (spiders, dogs, cats, snakes, birds, insects)",
                "Natural environment (heights, storms, water, darkness)",
                "Blood, injections, or medical procedures", 
                "Flying in airplanes",
                "Enclosed spaces (elevators, tunnels, small rooms)",
                "Driving or being in cars",
                "Bridges or overpasses",
                "Vomiting or seeing others vomit",
                "Choking or swallowing",
                "Loud noises or sudden sounds",
                "Clowns or costumed characters",
                "Specific textures or materials",
                "Other specific fear (please specify)",
                "I don't have intense fears of specific things"
            ],
            required=True,
            criteria_weight=2.0,
            symptom_category="phobia_types",
            help_text="Select all that apply - you can have more than one specific phobia"
        ),
        
        SCIDQuestion(
            id="sp_003",
            text="What is your most troublesome or severe specific fear?",
            simple_text="Which fear bothers you the most or is the strongest?",
            response_type=ResponseType.TEXT,
            required=True,
            criteria_weight=1.0,
            symptom_category="primary_phobia",
            help_text="Please describe the one fear that causes you the most problems"
        ),
        
        SCIDQuestion(
            id="sp_004",
            text="How intense is your fear when you encounter this object or situation?",
            simple_text="How strong is your fear when you see or are near this thing?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No fear", "Mild fear", "Moderate fear", "Extreme fear"],
            required=True,
            criteria_weight=1.5,
            symptom_category="fear_intensity"
        ),
        
        # Criterion B: Almost always provokes immediate fear/anxiety
        SCIDQuestion(
            id="sp_005",
            text="Does encountering this feared object or situation almost always cause immediate fear or anxiety?",
            simple_text="Do you almost always feel scared or anxious right away when you see or encounter this thing?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Usually", "Almost always"],
            required=True,
            criteria_weight=2.0,
            symptom_category="immediate_response"
        ),
        
        SCIDQuestion(
            id="sp_006",
            text="How quickly does the fear start when you encounter the feared object or situation?",
            simple_text="How fast do you start feeling afraid when you see or encounter this thing?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Immediately (within seconds)",
                "Within 1-2 minutes",
                "Within 5 minutes",
                "It takes longer than 5 minutes",
                "The fear doesn't start right away"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="fear_onset"
        ),
        
        # Physical symptoms
        SCIDQuestion(
            id="sp_007",
            text="What physical symptoms do you experience when encountering your feared object or situation?",
            simple_text="What happens to your body when you encounter the thing you're afraid of?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Heart racing or pounding",
                "Sweating heavily",
                "Shaking or trembling",
                "Difficulty breathing or shortness of breath",
                "Feeling dizzy or lightheaded",
                "Nausea or upset stomach",
                "Feeling like I might faint",
                "Chest pain or tightness",
                "Hot or cold flashes",
                "Feeling like I'm choking",
                "Muscle tension",
                "No physical symptoms"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="physical_symptoms"
        ),
        
        # Criterion C: Active avoidance or endured with distress
        SCIDQuestion(
            id="sp_008",
            text="Do you actively avoid the object or situation you fear?",
            simple_text="Do you try hard to stay away from the thing you're afraid of?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="avoidance"
        ),
        
        SCIDQuestion(
            id="sp_009",
            text="How much do you go out of your way to avoid your feared object or situation?",
            simple_text="How much effort do you put into staying away from the thing you fear?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No avoidance", "Mild avoidance", "Moderate avoidance", "Extreme avoidance"],
            required=True,
            criteria_weight=1.5,
            symptom_category="avoidance_level"
        ),
        
        SCIDQuestion(
            id="sp_010",
            text="What specific things do you do to avoid your fear?",
            simple_text="What do you do to stay away from the thing you're afraid of?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Take different routes or paths",
                "Don't go to certain places",
                "Ask others to check for the feared object first",
                "Leave situations where it might appear",
                "Don't watch movies or TV shows that might show it",
                "Avoid certain activities or hobbies",
                "Don't travel to certain places",
                "Have someone else handle situations involving it",
                "Use alternative transportation methods",
                "Stay indoors more than necessary",
                "I don't avoid my feared object/situation"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="avoidance_behaviors"
        ),
        
        SCIDQuestion(
            id="sp_011",
            text="When you can't avoid the feared object or situation, how distressed do you feel?",
            simple_text="When you can't get away from the thing you fear, how upset do you feel?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not distressed", "Mildly distressed", "Moderately distressed", "Extremely distressed"],
            required=True,
            criteria_weight=1.5,
            symptom_category="unavoidable_distress"
        ),
        
        # Criterion D: Fear out of proportion to actual danger
        SCIDQuestion(
            id="sp_012",
            text="Do you recognize that your fear is much stronger than the actual danger?",
            simple_text="Do you know that you're much more afraid than you need to be based on real danger?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="disproportionate_fear"
        ),
        
        SCIDQuestion(
            id="sp_013",
            text="Do other people tell you that your fear is excessive or unreasonable?",
            simple_text="Do other people say that your fear is too much or doesn't make sense?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="external_perspective"
        ),
        
        # Criterion E: Duration (6+ months)
        SCIDQuestion(
            id="sp_014",
            text="How long have you had this intense fear?",
            simple_text="How long have you been very afraid of this thing or situation?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-3 months",
                "3-6 months", 
                "6 months to 1 year",
                "1-2 years",
                "2-5 years",
                "More than 5 years",
                "Since childhood - as long as I can remember"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="duration"
        ),
        
        # Age of onset
        SCIDQuestion(
            id="sp_015",
            text="At what age did this fear first start?",
            simple_text="How old were you when this fear first began?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Early childhood (before age 7)",
                "Childhood (ages 7-12)",
                "Teenage years (ages 13-17)",
                "Early adulthood (ages 18-25)",
                "Adulthood (ages 26-40)",
                "Later adulthood (over age 40)",
                "I can't remember when it started"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="onset_age"
        ),
        
        # Criterion F: Significant distress or impairment
        SCIDQuestion(
            id="sp_016",
            text="Has this fear caused significant problems or distress in your life?",
            simple_text="Has this fear caused big problems or made you very upset?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="impairment"
        ),
        
        SCIDQuestion(
            id="sp_017",
            text="In which areas of your life has this fear caused problems?",
            simple_text="Where in your life has this fear caused problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school activities",
                "Travel and transportation",
                "Social activities and relationships",
                "Family activities and events",
                "Recreational activities and hobbies",
                "Medical or dental care",
                "Daily errands and routine tasks",
                "Living arrangements or housing choices",
                "Career or educational opportunities",
                "Overall quality of life and happiness",
                "My fear hasn't caused significant problems"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="impairment_areas"
        ),
        
        SCIDQuestion(
            id="sp_018",
            text="How much has this fear interfered with your daily life?",
            simple_text="How much has this fear made it hard to do things in your daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="daily_interference"
        ),
        
        # Panic attacks in relation to phobia
        SCIDQuestion(
            id="sp_019",
            text="Do you ever have panic attacks when encountering your feared object or situation?",
            simple_text="Do you ever have panic attacks (sudden intense fear with physical symptoms) when you encounter the thing you're afraid of?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="panic_attacks"
        ),
        
        # Current severity assessment
        SCIDQuestion(
            id="sp_020",
            text="How would you rate the current severity of your specific phobia?",
            simple_text="Overall, how bad is your fear of this specific thing right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Minimal", "Mild", "Moderate", "Severe"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_severity"
        ),
        
        # Impact on others
        SCIDQuestion(
            id="sp_021",
            text="Has your fear affected other people in your life?",
            simple_text="Has your fear caused problems for family members or friends?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Family members have to accommodate my fear",
                "Friends avoid certain activities because of my fear",
                "Others have to do things for me because of my fear",
                "My fear has caused conflict with others",
                "Others worry about my fear",
                "My fear limits what my family/friends can do",
                "My fear hasn't affected other people"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="impact_on_others"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A. Marked fear or anxiety about a specific object or situation",
        "B. The phobic object or situation almost always provokes immediate fear or anxiety",
        "C. The phobic object or situation is actively avoided or endured with intense fear or anxiety",
        "D. The fear or anxiety is out of proportion to the actual danger posed",
        "E. The fear, anxiety, or avoidance is persistent, typically lasting for 6 months or more",
        "F. The fear, anxiety, or avoidance causes clinically significant distress or impairment",
        "G. The disturbance is not better explained by symptoms of another mental disorder"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.4,      # Minimal avoidance, mild distress
        "moderate": 0.6,  # Some avoidance and interference
        "severe": 0.8     # Extensive avoidance and significant impairment
    }
    
    return SCIDModule(
        id="SPECIFIC_PHOBIA", 
        name="Specific Phobia",
        description="Assessment module for Specific Phobia based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=12,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="anxiety_disorders",
        version="1.0"
    )
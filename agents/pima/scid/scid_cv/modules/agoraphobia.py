# scid_cv/modules/agoraphobia.py
"""
SCID-5 Clinical Version - Agoraphobia Module
Structured clinical interview questions for Agoraphobia diagnosis
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_agoraphobia_module() -> SCIDModule:
    """
    Create the Agoraphobia module for SCID-CV
    
    Based on DSM-5 criteria for Agoraphobia:
    - Marked fear or anxiety about situations where escape might be difficult
    - Fear occurs in at least 2 of 5 specific situations
    - Situations consistently provoke fear/anxiety
    - Situations are actively avoided or require companion
    - Fear/anxiety is out of proportion to actual danger
    - Duration: 6 months or more
    - Causes significant distress or impairment
    """
    
    questions = [
        # Core Agoraphobic Situations - Criterion A & B
        SCIDQuestion(
            id="AGO_001",
            text="Do you have marked fear or anxiety about using public transportation (buses, trains, planes, ships)?",
            simple_text="Are you very afraid or anxious when you have to use buses, trains, planes, or boats?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No fear or anxiety",
                "Mild discomfort but manageable",
                "Moderate fear - causes distress",
                "Severe fear - very distressing",
                "Extreme fear - overwhelming panic"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="public_transportation",
            help_text="Think about your feelings when using any form of public transportation",
            examples=["Taking the bus to work", "Flying on an airplane", "Riding the subway"]
        ),
        
        SCIDQuestion(
            id="AGO_002",
            text="Do you have marked fear or anxiety about being in open spaces (parking lots, marketplaces, bridges)?",
            simple_text="Are you very afraid or anxious when you're in wide open areas like parking lots, markets, or on bridges?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No fear or anxiety",
                "Mild discomfort but manageable",
                "Moderate fear - causes distress",
                "Severe fear - very distressing",
                "Extreme fear - overwhelming panic"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="open_spaces",
            help_text="Consider your comfort level in wide, open areas where you feel exposed",
            examples=["Large parking lots", "Open marketplaces", "Wide bridges", "Fields or parks"]
        ),
        
        SCIDQuestion(
            id="AGO_003",
            text="Do you have marked fear or anxiety about being in enclosed spaces (shops, theaters, small rooms)?",
            simple_text="Are you very afraid or anxious when you're in closed-in spaces like stores, movie theaters, or small rooms?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No fear or anxiety",
                "Mild discomfort but manageable",
                "Moderate fear - causes distress",
                "Severe fear - very distressing",
                "Extreme fear - overwhelming panic"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="enclosed_spaces",
            help_text="Think about how you feel in confined or enclosed areas",
            examples=["Shopping in stores", "Sitting in movie theaters", "Small elevators", "Crowded restaurants"]
        ),
        
        SCIDQuestion(
            id="AGO_004",
            text="Do you have marked fear or anxiety about standing in lines or being in crowds?",
            simple_text="Are you very afraid or anxious when you have to wait in lines or be around lots of people?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No fear or anxiety",
                "Mild discomfort but manageable",
                "Moderate fear - causes distress",
                "Severe fear - very distressing",
                "Extreme fear - overwhelming panic"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="crowds_lines",
            help_text="Consider your feelings when waiting in line or being surrounded by people",
            examples=["Waiting in grocery store lines", "Being in crowded concerts", "Standing in bank queues"]
        ),
        
        SCIDQuestion(
            id="AGO_005",
            text="Do you have marked fear or anxiety about being outside of the home alone?",
            simple_text="Are you very afraid or anxious when you're away from home by yourself?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No fear or anxiety",
                "Mild discomfort but manageable",
                "Moderate fear - causes distress",
                "Severe fear - very distressing",
                "Extreme fear - overwhelming panic"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="alone_outside_home",
            help_text="Think about how you feel when you're out in public places by yourself",
            examples=["Going to the store alone", "Walking in the neighborhood", "Running errands by yourself"]
        ),
        
        # Avoidance Behavior - Criterion C
        SCIDQuestion(
            id="AGO_006",
            text="Do you actively avoid these situations because of your fear or anxiety?",
            simple_text="Do you stay away from these places or situations because they make you afraid or anxious?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't avoid any situations",
                "I avoid some situations occasionally",
                "I avoid situations regularly",
                "I avoid most feared situations",
                "I avoid all feared situations completely"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="avoidance_behavior",
            help_text="Consider how often you change your plans or routes to avoid feared situations"
        ),
        
        SCIDQuestion(
            id="AGO_007",
            text="Do you require the presence of a companion when facing these situations?",
            simple_text="Do you need someone with you to feel safe in these situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I can handle situations alone",
                "I occasionally prefer company",
                "I often need someone with me",
                "I usually require a companion",
                "I always need someone with me"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="companion_dependence",
            help_text="Think about whether having someone with you makes these situations more manageable"
        ),
        
        # Escape Concerns - Criterion A continued
        SCIDQuestion(
            id="AGO_008",
            text="In these situations, do you worry about not being able to escape or get help if you have panic-like symptoms?",
            simple_text="In these situations, do you worry that you won't be able to get away or get help if you start to panic?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="escape_concerns",
            help_text="Consider whether your fear is specifically about being trapped or unable to get help"
        ),
        
        SCIDQuestion(
            id="AGO_009",
            text="Do you worry about having embarrassing symptoms (like losing control of bowels or bladder, vomiting, falling) in these situations?",
            simple_text="Do you worry about having embarrassing symptoms like losing control of your body or falling down in these places?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="embarrassing_symptoms",
            help_text="Think about fears of having physical symptoms that others might notice"
        ),
        
        # Proportionality - Criterion D
        SCIDQuestion(
            id="AGO_010",
            text="Is your fear or anxiety out of proportion to the actual danger posed by these situations?",
            simple_text="Is your fear much stronger than the real danger in these situations?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "Slightly excessive", "Moderately excessive", "Very excessive", "Extremely excessive"],
            required=True,
            criteria_weight=1.0,
            symptom_category="fear_proportionality",
            help_text="Consider whether your fear level matches the actual risk in these situations"
        ),
        
        # Duration - Criterion E
        SCIDQuestion(
            id="AGO_011",
            text="Have these fears and avoidance behaviors been present for 6 months or longer?",
            simple_text="Have you been having these fears and avoiding these situations for at least 6 months?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="duration",
            help_text="Think about when these fears first started becoming a regular problem"
        ),
        
        # Impairment - Criterion F
        SCIDQuestion(
            id="AGO_012",
            text="Do these fears and avoidance behaviors cause significant distress in your life?",
            simple_text="Do these fears and avoiding situations cause you a lot of emotional pain or upset?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["No distress", "Mild distress", "Moderate distress", "Severe distress", "Extreme distress"],
            required=True,
            criteria_weight=1.0,
            symptom_category="emotional_distress",
            help_text="Consider how much emotional suffering these fears cause you"
        ),
        
        SCIDQuestion(
            id="AGO_013",
            text="Do these fears and avoidance behaviors significantly interfere with your work, school, or other important activities?",
            simple_text="Do these fears and avoiding situations make it hard for you to work, go to school, or do other important things?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference", "Extreme interference"],
            required=True,
            criteria_weight=1.0,
            symptom_category="functional_impairment",
            help_text="Think about how these fears affect your daily responsibilities and activities"
        ),
        
        SCIDQuestion(
            id="AGO_014",
            text="Do these fears and avoidance behaviors interfere with your social relationships?",
            simple_text="Do these fears and avoiding situations cause problems with your family, friends, or other relationships?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference", "Extreme interference"],
            required=True,
            criteria_weight=1.0,
            symptom_category="social_impairment",
            help_text="Consider how these fears affect your relationships with others"
        ),
        
        # Physical Symptoms
        SCIDQuestion(
            id="AGO_015",
            text="When you're in these feared situations, what physical symptoms do you experience?",
            simple_text="When you're in these scary situations, what happens to your body?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No physical symptoms",
                "Rapid heartbeat or pounding heart",
                "Sweating or trembling",
                "Difficulty breathing or shortness of breath",
                "Nausea or stomach problems",
                "Dizziness or feeling faint",
                "Multiple symptoms at once"
            ],
            required=False,
            criteria_weight=0.5,
            symptom_category="physical_symptoms",
            help_text="Select the physical sensations you notice when anxious in these situations"
        ),
        
        # Onset and Development
        SCIDQuestion(
            id="AGO_016",
            text="Can you remember when these fears first started?",
            simple_text="Do you remember when you first started having these fears?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No clear memory of onset",
                "Gradually developed over time",
                "Started after a specific scary event",
                "Started after having panic attacks",
                "Started during a stressful period",
                "Started in childhood or adolescence"
            ],
            required=False,
            criteria_weight=0.3,
            symptom_category="onset_pattern",
            help_text="Think about what might have triggered the start of these fears"
        ),
        
        # Current Severity
        SCIDQuestion(
            id="AGO_017",
            text="How much do these agoraphobic fears currently limit your daily life?",
            simple_text="Right now, how much do these fears limit what you can do in your daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "Slightly limiting", "Moderately limiting", "Very limiting", "Extremely limiting"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_limitation",
            help_text="Consider your current level of restriction due to these fears"
        ),
        
        # Safety Behaviors
        SCIDQuestion(
            id="AGO_018",
            text="Do you use any specific strategies to cope with these situations when you must face them?",
            simple_text="When you have to go to these scary places, what do you do to help yourself feel safer?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't use any special strategies",
                "I take medication before going",
                "I plan escape routes in advance",
                "I carry items that make me feel safe",
                "I use breathing or relaxation techniques",
                "I focus on distracting activities",
                "Multiple coping strategies"
            ],
            required=False,
            criteria_weight=0.3,
            symptom_category="coping_strategies",
            help_text="Think about what helps you manage when you must face feared situations"
        )
    ]
    
    return SCIDModule(
        id="AGORAPHOBIA",
        name="Agoraphobia",
        description="Structured clinical interview for Agoraphobia based on DSM-5 criteria. Assesses marked fear or anxiety about situations where escape might be difficult or help unavailable.",
        questions=questions,
        diagnostic_threshold=0.7,  # 70% of criteria must be met
        estimated_time_mins=15,
        dsm_criteria=[
            "A. Marked fear or anxiety about two (or more) of the following five situations: public transportation, open spaces, enclosed spaces, standing in line or being in a crowd, being outside home alone",
            "B. The individual fears or avoids these situations because of thoughts that escape might be difficult or help might not be available",
            "C. The agoraphobic situations almost always provoke fear or anxiety",
            "D. The agoraphobic situations are actively avoided, require presence of companion, or endured with intense fear",
            "E. Fear or anxiety is out of proportion to actual danger posed by situation",
            "F. Fear, anxiety, or avoidance is persistent, typically lasting 6 months or more",
            "G. Fear, anxiety, or avoidance causes clinically significant distress or impairment"
        ],
        severity_thresholds={
            "mild": 0.5,
            "moderate": 0.7,
            "severe": 0.85
        },
        category="anxiety_disorders",
        version="1.0",
        clinical_notes="Agoraphobia involves fear of situations where escape might be difficult. Key feature is avoidance of multiple situations due to fear of panic-like symptoms or other incapacitating symptoms. Often co-occurs with panic disorder but can occur independently."
    )
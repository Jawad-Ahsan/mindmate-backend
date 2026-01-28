# scid_cv/modules/panic_disorder.py
"""
SCID-CV Module: Panic Disorder
Assessment of panic attacks and panic disorder according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_panic_module() -> SCIDModule:
    """Create the Panic Disorder SCID-CV module"""
    
    questions = [
        # Panic Attack Screening
        SCIDQuestion(
            id="PAN_01",
            text="Have you ever had a panic attack - a sudden rush of intense fear or anxiety?",
            simple_text="Have you ever had a panic attack - when you suddenly felt very scared or anxious for no clear reason?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="panic_attacks",
            help_text="A panic attack comes on suddenly and reaches peak intensity within minutes",
            examples=["Sudden overwhelming fear", "Feeling like something terrible is happening", "Intense anxiety out of nowhere"]
        ),
        
        SCIDQuestion(
            id="PAN_02",
            text="How quickly did these feelings of fear or anxiety reach their peak?",
            simple_text="How quickly did the fear or anxiety get to its worst point?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Gradually over an hour or more",
                "Within 30-60 minutes",
                "Within 10-30 minutes", 
                "Within 5-10 minutes",
                "Almost immediately - within a few minutes"
            ],
            symptom_category="onset_speed",
            help_text="True panic attacks reach peak intensity within 10 minutes"
        ),
        
        # Physical Symptoms of Panic
        SCIDQuestion(
            id="PAN_03",
            text="During these attacks, did your heart pound, race, or skip beats?",
            simple_text="During panic attacks, did you feel your heart beating very fast, hard, or irregularly?",
            response_type=ResponseType.YES_NO,
            symptom_category="palpitations",
            help_text="This includes feeling your heart racing or pounding in your chest",
            examples=["Heart racing", "Feeling your heartbeat strongly", "Heart skipping beats"]
        ),
        
        SCIDQuestion(
            id="PAN_04",
            text="Did you sweat or have hot or cold flashes?",
            simple_text="Did you suddenly start sweating a lot, or feel very hot or very cold?",
            response_type=ResponseType.YES_NO,
            symptom_category="sweating_flashes",
            help_text="Sudden sweating or temperature changes during the attack",
            examples=["Breaking out in a sweat", "Feeling flushed", "Sudden chills"]
        ),
        
        SCIDQuestion(
            id="PAN_05",
            text="Did you tremble, shake, or feel shaky inside?",
            simple_text="Did you shake, tremble, or feel shaky on the inside?",
            response_type=ResponseType.YES_NO,
            symptom_category="trembling",
            help_text="This can be visible shaking or internal feelings of trembling",
            examples=["Hands shaking", "Feeling jittery", "Internal trembling sensation"]
        ),
        
        SCIDQuestion(
            id="PAN_06",
            text="Did you have trouble breathing, feel short of breath, or feel like you were choking?",
            simple_text="Did you have trouble breathing, feel like you couldn't get enough air, or feel like you were choking?",
            response_type=ResponseType.YES_NO,
            symptom_category="breathing_difficulties",
            help_text="Feeling like you can't breathe properly or get enough air",
            examples=["Can't catch your breath", "Feeling suffocated", "Throat closing up"]
        ),
        
        SCIDQuestion(
            id="PAN_07",
            text="Did you have chest pain or discomfort?",
            simple_text="Did you feel pain, pressure, or discomfort in your chest?",
            response_type=ResponseType.YES_NO,
            symptom_category="chest_pain",
            help_text="Any uncomfortable sensation in the chest area",
            examples=["Chest tightness", "Sharp chest pain", "Heavy feeling on chest"]
        ),
        
        SCIDQuestion(
            id="PAN_08",
            text="Did you feel nauseated or have stomach problems?",
            simple_text="Did you feel sick to your stomach or have stomach upset?",
            response_type=ResponseType.YES_NO,
            symptom_category="nausea",
            help_text="Stomach discomfort or feeling like you might vomit",
            examples=["Feeling queasy", "Stomach churning", "Wanting to throw up"]
        ),
        
        SCIDQuestion(
            id="PAN_09",
            text="Did you feel dizzy, lightheaded, or faint?",
            simple_text="Did you feel dizzy, lightheaded, or like you might faint?",
            response_type=ResponseType.YES_NO,
            symptom_category="dizziness",
            help_text="Feeling unsteady or like you might pass out",
            examples=["Room spinning", "Feeling off-balance", "Like you might collapse"]
        ),
        
        SCIDQuestion(
            id="PAN_10",
            text="Did you have feelings of unreality or feel detached from yourself?",
            simple_text="Did you feel like things around you weren't real, or like you were watching yourself from outside your body?",
            response_type=ResponseType.YES_NO,
            symptom_category="derealization_depersonalization",
            help_text="Feeling disconnected from reality or yourself",
            examples=["Things seem dreamlike", "Feeling like you're floating", "World seems unreal"]
        ),
        
        # Catastrophic Thoughts
        SCIDQuestion(
            id="PAN_11",
            text="Were you afraid you were going crazy or losing control?",
            simple_text="Were you afraid you were going crazy or completely losing control of yourself?",
            response_type=ResponseType.YES_NO,
            symptom_category="fear_losing_control",
            help_text="Fear of mental breakdown or losing your mind",
            examples=["Thinking you're going insane", "Fear of doing something crazy", "Losing your grip on reality"]
        ),
        
        SCIDQuestion(
            id="PAN_12",
            text="Were you afraid you were having a heart attack or dying?",
            simple_text="Were you afraid you were having a heart attack or that you might die?",
            response_type=ResponseType.YES_NO,
            symptom_category="fear_dying",
            help_text="Fear of immediate physical catastrophe or death",
            examples=["Thinking you're having a heart attack", "Fear of dying", "Feeling like this is the end"]
        ),
        
        # Additional Physical Symptoms
        SCIDQuestion(
            id="PAN_13",
            text="Did you feel numbness or tingling in your hands, feet, or face?",
            simple_text="Did parts of your body feel numb or tingly, like pins and needles?",
            response_type=ResponseType.YES_NO,
            symptom_category="numbness_tingling",
            help_text="Unusual sensations in extremities or face",
            examples=["Hands going numb", "Tingling lips", "Pins and needles in feet"]
        ),
        
        # Panic Attack Characteristics
        SCIDQuestion(
            id="PAN_14",
            text="How long did these panic attacks usually last?",
            simple_text="How long did these panic attacks usually last from start to finish?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "A few minutes (5-10 minutes)",
                "10-20 minutes",
                "20-30 minutes",
                "30-60 minutes",
                "Several hours",
                "The length varied a lot"
            ],
            symptom_category="attack_duration",
            help_text="Most panic attacks peak quickly and subside within 30 minutes"
        ),
        
        SCIDQuestion(
            id="PAN_15",
            text="How many panic attacks have you had in your lifetime?",
            simple_text="About how many panic attacks have you had altogether?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Just one",
                "2-3 attacks",
                "4-10 attacks",
                "10-20 attacks",
                "More than 20 attacks",
                "Too many to count"
            ],
            symptom_category="attack_frequency",
            help_text="Multiple attacks are needed for panic disorder diagnosis"
        ),
        
        # Triggers and Context
        SCIDQuestion(
            id="PAN_16",
            text="Do your panic attacks happen in specific situations or do they come out of the blue?",
            simple_text="Do your panic attacks happen in certain places or situations, or do they come out of nowhere?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Always in specific situations (elevators, crowds, etc.)",
                "Usually in certain situations but sometimes out of nowhere",
                "Mostly out of the blue with no clear trigger",
                "Always completely unexpected",
                "Only when thinking about certain things"
            ],
            symptom_category="attack_triggers",
            help_text="Unexpected attacks are key for panic disorder diagnosis"
        ),
        
        SCIDQuestion(
            id="PAN_16A",
            text="What situations tend to trigger your panic attacks?",
            simple_text="What places or situations tend to bring on your panic attacks?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Crowded places like malls or stores",
                "Driving or being in cars",
                "Flying or other transportation",
                "Enclosed spaces like elevators",
                "Social situations or being watched",
                "Being alone or far from help",
                "Physical exercise or exertion",
                "Medical settings or procedures"
            ],
            required=False,
            symptom_category="specific_triggers",
            help_text="Choose all situations that tend to trigger panic attacks"
        ),
        
        # Anticipatory Anxiety
        SCIDQuestion(
            id="PAN_17",
            text="Do you worry about having more panic attacks?",
            simple_text="Do you spend time worrying about having another panic attack?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.5,
            symptom_category="anticipatory_anxiety",
            help_text="Persistent concern about future attacks is part of panic disorder"
        ),
        
        SCIDQuestion(
            id="PAN_18",
            text="Do you worry about what panic attacks mean or their consequences?",
            simple_text="Do you worry about what panic attacks might mean about your health, or what bad things might happen if you have one?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't worry much about them",
                "I worry they mean I have a serious medical problem",
                "I worry I might go crazy or lose control",
                "I worry I might embarrass myself in public",
                "I worry something terrible will happen",
                "I worry about multiple consequences"
            ],
            symptom_category="consequence_worries",
            help_text="Worries about the meaning or consequences of panic attacks"
        ),
        
        # Avoidance Behavior
        SCIDQuestion(
            id="PAN_19",
            text="Have you avoided places or situations because you're afraid of having a panic attack?",
            simple_text="Have you avoided going places or doing things because you're afraid you might have a panic attack?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.5,
            symptom_category="avoidance_behavior",
            help_text="Behavioral changes due to fear of panic attacks"
        ),
        
        SCIDQuestion(
            id="PAN_19A",
            text="What places or activities do you avoid?",
            simple_text="What places or activities do you avoid because of fear of panic attacks?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Crowded places like malls or theaters",
                "Driving, especially on highways",
                "Flying or other forms of transportation",
                "Being far from home or medical help",
                "Exercise or physical activity",
                "Social events or gatherings",
                "Being alone in certain places",
                "Medical appointments or procedures"
            ],
            required=False,
            symptom_category="avoided_situations",
            help_text="Choose all places or activities you avoid"
        ),
        
        # Safety Behaviors
        SCIDQuestion(
            id="PAN_20",
            text="Do you do things to feel safer or prevent panic attacks?",
            simple_text="Do you carry certain things with you or do special things to feel safer or prevent panic attacks?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't do anything special",
                "Carry medication 'just in case'",
                "Always stay near exits or bathrooms",
                "Bring a trusted person with me",
                "Carry water, phone, or other comfort items",
                "Plan escape routes or safe places",
                "Use breathing or relaxation techniques",
                "Avoid caffeine or other triggers"
            ],
            symptom_category="safety_behaviors",
            help_text="Safety behaviors can provide temporary relief but may maintain anxiety"
        ),
        
        # Impact on Functioning
        SCIDQuestion(
            id="PAN_21",
            text="How much do panic attacks and fear of panic attacks interfere with your daily life?",
            simple_text="How much do panic attacks and worrying about them interfere with your work, relationships, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not at all", "A little bit", "Quite a bit", "Extremely"],
            symptom_category="functional_impairment",
            help_text="Consider the impact of both the attacks and the fear of having them"
        ),
        
        SCIDQuestion(
            id="PAN_22",
            text="Which areas of your life are most affected?",
            simple_text="Which parts of your life have been most affected by panic attacks or fear of having them?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Social activities and relationships",
                "Driving or transportation",
                "Shopping or errands",
                "Travel or being away from home",
                "Physical activities or exercise",
                "Medical care or appointments",
                "General independence and freedom"
            ],
            required=False,
            symptom_category="impairment_areas",
            help_text="Choose all areas significantly affected"
        ),
        
        # Onset and Duration
        SCIDQuestion(
            id="PAN_23",
            text="When did you have your first panic attack?",
            simple_text="About when did you have your very first panic attack?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Within the past month",
                "1-6 months ago",
                "6 months to 1 year ago",
                "1-2 years ago",
                "2-5 years ago",
                "More than 5 years ago",
                "I can't remember exactly"
            ],
            symptom_category="onset_timing",
            help_text="Age of onset can be helpful for treatment planning"
        ),
        
        SCIDQuestion(
            id="PAN_24",
            text="For how long have you been worried about having panic attacks?",
            simple_text="For about how long have you been worrying about having more panic attacks?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-6 months",
                "6 months to 1 year",
                "1-2 years", 
                "More than 2 years",
                "I don't really worry about them"
            ],
            symptom_category="worry_duration",
            help_text="Persistent worry for at least 1 month is needed for diagnosis"
        ),
        
        # Treatment and Coping
        SCIDQuestion(
            id="PAN_25",
            text="Are you currently getting any treatment for panic attacks?",
            simple_text="Are you currently taking medication or getting any treatment for panic attacks?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Taking anti-anxiety medication as needed",
                "Taking daily medication for anxiety",
                "Seeing a therapist or counselor",
                "Both medication and therapy",
                "Using self-help or relaxation techniques",
                "Have tried treatment but not currently receiving any"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="Current treatment status helps with planning"
        )
    ]
    
    return SCIDModule(
        id="PANIC",
        name="Panic Disorder",
        description="Assessment of panic attacks and panic disorder according to DSM-5 criteria. Evaluates panic symptoms, anticipatory anxiety, avoidance behaviors, and functional impairment.",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=15,
        dsm_criteria=[
            "Recurrent unexpected panic attacks",
            "Palpitations or accelerated heart rate",
            "Sweating",
            "Trembling or shaking",
            "Shortness of breath or smothering",
            "Feeling of choking",
            "Chest pain or discomfort",
            "Nausea or abdominal distress",
            "Dizziness or lightheadedness",
            "Derealization or depersonalization",
            "Fear of losing control or going crazy",
            "Fear of dying",
            "Numbness or tingling",
            "Chills or hot flushes"
        ],
        severity_thresholds={
            "mild": 0.4,
            "moderate": 0.6,
            "severe": 0.8
        },
        category="anxiety_disorders",
        version="1.0",
        clinical_notes="Requires recurrent unexpected panic attacks with at least 1 month of concern about attacks or behavioral changes. At least 4 physical/cognitive symptoms must occur during attacks."
    )
# scid_cv/modules/generalized_anxiety.py
"""
SCID-CV Module: Generalized Anxiety Disorder (GAD)
Assessment of excessive worry and GAD according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_gad_module() -> SCIDModule:
    """Create the Generalized Anxiety Disorder SCID-CV module"""
    
    questions = [
        # Core Worry Symptoms
        SCIDQuestion(
            id="GAD_01",
            text="Do you worry excessively about many different things in your life?",
            simple_text="Do you worry too much about many different things - more than most people would?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="excessive_worry",
            help_text="This is worry that is out of proportion to the situation",
            examples=["Worrying about everything", "Constant 'what if' thoughts", "Others say you worry too much"]
        ),
        
        SCIDQuestion(
            id="GAD_02",
            text="Is it difficult for you to control or stop your worrying?",
            simple_text="Is it hard for you to stop worrying once you start, or to control your worried thoughts?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="uncontrollable_worry",
            help_text="The worry feels like it has a mind of its own",
            examples=["Can't turn off worried thoughts", "Worry spirals out of control", "Can't just 'stop worrying'"]
        ),
        
        SCIDQuestion(
            id="GAD_03",
            text="What kinds of things do you worry about most?",
            simple_text="What kinds of things do you find yourself worrying about? (Choose all that apply)",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance and responsibilities",
                "Health of yourself or family members",
                "Money, finances, or paying bills",
                "Relationships with family or friends",
                "Daily responsibilities and getting things done",
                "World events, news, or politics",
                "Future events or what might happen",
                "Minor matters and everyday activities",
                "Safety of yourself or loved ones",
                "Being on time or being late",
                "Making mistakes or not being perfect"
            ],
            symptom_category="worry_content",
            help_text="GAD involves worry about multiple life domains"
        ),
        
        SCIDQuestion(
            id="GAD_04",
            text="How much of your day do you spend worrying?",
            simple_text="On a typical day, how much time do you spend worrying or having anxious thoughts?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Very little - less than 30 minutes",
                "Some time - about 1-2 hours",
                "Much of the day - 3-6 hours",
                "Most of the day - more than 6 hours",
                "Almost constantly - it's hard to think about anything else"
            ],
            symptom_category="worry_time",
            help_text="Excessive worry typically takes up significant time each day"
        ),
        
        # Physical Symptoms Associated with Worry
        SCIDQuestion(
            id="GAD_05",
            text="When you worry, do you feel restless, keyed up, or on edge?",
            simple_text="When you're worrying, do you feel restless, wound up, or on edge?",
            response_type=ResponseType.YES_NO,
            symptom_category="restlessness",
            help_text="Feeling unable to relax or settle down",
            examples=["Can't sit still", "Feeling jittery", "Like you're wound up tight"]
        ),
        
        SCIDQuestion(
            id="GAD_06",
            text="Do you get tired easily, especially when you're worried?",
            simple_text="Do you get tired easily, especially when you're worrying a lot?",
            response_type=ResponseType.YES_NO,
            symptom_category="easy_fatigue",
            help_text="Worry can be mentally and physically exhausting",
            examples=["Feeling drained from worrying", "Worry wears you out", "Tired but wired"]
        ),
        
        SCIDQuestion(
            id="GAD_07",
            text="When you're worried, is it hard to concentrate or focus?",
            simple_text="When you're worried, do you have trouble concentrating on other things or focusing?",
            response_type=ResponseType.YES_NO,
            symptom_category="concentration_problems",
            help_text="Worry takes up mental energy and makes focusing difficult",
            examples=["Mind goes blank", "Can't focus on work", "Thoughts keep drifting to worries"]
        ),
        
        SCIDQuestion(
            id="GAD_08",
            text="Are you more irritable when you're worried?",
            simple_text="When you're worried, do you get more easily annoyed or irritated with others?",
            response_type=ResponseType.YES_NO,
            symptom_category="irritability",
            help_text="Worry and anxiety can make people more short-tempered",
            examples=["Snapping at people", "Less patient than usual", "Small things bother you more"]
        ),
        
        SCIDQuestion(
            id="GAD_09",
            text="Do you have muscle tension, aches, or soreness when worried?",
            simple_text="When you're worried, do your muscles feel tense, achy, or sore?",
            response_type=ResponseType.YES_NO,
            symptom_category="muscle_tension",
            help_text="Anxiety often causes physical tension in the body",
            examples=["Tight shoulders", "Clenched jaw", "Headaches from tension", "Back pain"]
        ),
        
        SCIDQuestion(
            id="GAD_10",
            text="Do you have trouble sleeping when you're worried?",
            simple_text="When you're worried, do you have trouble falling asleep, staying asleep, or getting restful sleep?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Sleep is not affected by worry",
                "Sometimes have trouble falling asleep",
                "Often lie awake worrying instead of sleeping",
                "Wake up during the night with worried thoughts",
                "Wake up early and can't get back to sleep because of worry",
                "Have multiple sleep problems due to worry"
            ],
            symptom_category="sleep_disturbance",
            help_text="Worry often interferes with sleep in various ways"
        ),
        
        # Duration and Persistence
        SCIDQuestion(
            id="GAD_11",
            text="How long have you been worrying excessively like this?",
            simple_text="For about how long have you been worrying too much about things?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 6 months",
                "6 months to 1 year",
                "1 to 2 years",
                "2 to 5 years",
                "More than 5 years",
                "As long as I can remember"
            ],
            symptom_category="worry_duration",
            help_text="GAD requires excessive worry for at least 6 months"
        ),
        
        SCIDQuestion(
            id="GAD_12",
            text="Does your worrying happen more days than not?",
            simple_text="Do you have these worrying days more often than days when you don't worry much?",
            response_type=ResponseType.YES_NO,
            symptom_category="worry_frequency",
            help_text="GAD involves worry occurring more days than not"
        ),
        
        # Interference and Impairment
        SCIDQuestion(
            id="GAD_13",
            text="How much does your worrying interfere with your daily life?",
            simple_text="How much does your worrying interfere with your work, relationships, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not at all", "A little bit", "Quite a bit", "Extremely"],
            symptom_category="functional_impairment",
            help_text="Consider the overall impact of worry on your life"
        ),
        
        SCIDQuestion(
            id="GAD_13A",
            text="Which areas of your life are most affected by worrying?",
            simple_text="Which parts of your life have been most affected by excessive worrying?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family or friends",
                "Social activities and going out",
                "Making decisions big and small",
                "Enjoying activities or relaxation",
                "Physical health and sleep",
                "Daily tasks and responsibilities",
                "Overall quality of life and happiness"
            ],
            required=False,
            symptom_category="impairment_areas",
            help_text="Choose all areas significantly affected by worry"
        ),
        
        # Worry Characteristics
        SCIDQuestion(
            id="GAD_14",
            text="Do you tend to expect the worst outcome in situations?",
            simple_text="When something is uncertain, do you tend to imagine the worst thing that could happen?",
            response_type=ResponseType.YES_NO,
            symptom_category="catastrophizing",
            help_text="This is called catastrophic thinking",
            examples=["Always expecting disasters", "Imagining worst-case scenarios", "Assuming things will go wrong"]
        ),
        
        SCIDQuestion(
            id="GAD_15",
            text="Do you worry about things that most people wouldn't worry about?",
            simple_text="Do you worry about things that your family or friends say aren't worth worrying about?",
            response_type=ResponseType.YES_NO,
            symptom_category="disproportionate_worry",
            help_text="Others may tell you that your worry is excessive",
            examples=["Worrying about unlikely events", "Others say you worry too much", "Worry about small things"]
        ),
        
        SCIDQuestion(
            id="GAD_16",
            text="Do you have 'what if' thoughts that go round and round?",
            simple_text="Do you get stuck thinking 'what if this happens' or 'what if that goes wrong' over and over?",
            response_type=ResponseType.YES_NO,
            symptom_category="what_if_thinking",
            help_text="Repetitive 'what if' thoughts are common in GAD",
            examples=["'What if I'm late?'", "'What if something bad happens?'", "'What if I mess up?'"]
        ),
        
        # Coping and Control Attempts
        SCIDQuestion(
            id="GAD_17",
            text="Do you do things to try to prevent bad things from happening?",
            simple_text="Do you do special things to try to make sure bad things don't happen, like checking, planning, or asking for reassurance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't do anything special to prevent problems",
                "I plan excessively to avoid problems",
                "I check things repeatedly to make sure they're okay",
                "I ask others for reassurance frequently",
                "I avoid situations that might cause worry",
                "I research everything extensively before making decisions",
                "I do several of these things regularly"
            ],
            symptom_category="worry_behaviors",
            help_text="People often develop behaviors to try to manage their worry"
        ),
        
        SCIDQuestion(
            id="GAD_18",
            text="Do other people tell you that you worry too much?",
            simple_text="Do family members, friends, or others tell you that you worry too much or need to relax?",
            response_type=ResponseType.YES_NO,
            symptom_category="others_notice",
            help_text="Others often notice when someone's worry is excessive",
            examples=["'You worry too much'", "'Try to relax'", "'It'll be fine'", "'You're overthinking'"]
        ),
        
        # Physical Health Impact
        SCIDQuestion(
            id="GAD_19",
            text="Has worrying affected your physical health?",
            simple_text="Has worrying caused you physical problems like headaches, stomach issues, or other health problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No physical health problems from worry",
                "Frequent headaches or migraines",
                "Stomach problems or digestive issues",
                "Muscle tension or pain",
                "Heart palpitations or chest tightness",
                "Fatigue or feeling worn out",
                "Multiple physical symptoms from worry"
            ],
            symptom_category="physical_symptoms",
            help_text="Chronic worry can cause various physical symptoms"
        ),
        
        # Onset and Development
        SCIDQuestion(
            id="GAD_20",
            text="When did you first start worrying excessively like this?",
            simple_text="Can you remember when you first started worrying too much about things?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Within the past year",
                "1-2 years ago",
                "During my teenage years",
                "As a young adult",
                "After a stressful life event",
                "I've been a worrier as long as I can remember",
                "I'm not sure when it started"
            ],
            symptom_category="worry_onset",
            help_text="Understanding when worry started can help with treatment"
        ),
        
        # Triggers and Stressors
        SCIDQuestion(
            id="GAD_21",
            text="Are there specific things that make your worrying worse?",
            simple_text="Are there certain situations, events, or things that make you worry even more than usual?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Nothing specific makes it worse",
                "Work or school deadlines and pressure",
                "Family problems or relationship issues",
                "Financial stress or money problems",
                "Health concerns for myself or others",
                "Major life changes or decisions",
                "News or world events",
                "Being alone with my thoughts"
            ],
            required=False,
            symptom_category="worry_triggers",
            help_text="Identifying triggers can help with coping strategies"
        ),
        
        # Current Coping
        SCIDQuestion(
            id="GAD_22",
            text="What do you do when you're feeling very worried?",
            simple_text="When you're feeling very worried or anxious, what do you do to try to feel better?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't do anything - just endure it",
                "Try to distract myself with activities",
                "Talk to someone about my worries",
                "Use breathing or relaxation techniques",
                "Exercise or do physical activity",
                "Avoid the situation causing worry",
                "Research or plan to try to solve problems",
                "Use alcohol or substances to relax"
            ],
            required=False,
            symptom_category="coping_strategies",
            help_text="Understanding current coping helps with treatment planning"
        ),
        
        # Treatment History
        SCIDQuestion(
            id="GAD_23",
            text="Are you currently getting any treatment for anxiety or worry?",
            simple_text="Are you currently taking medication or getting any treatment for anxiety or excessive worrying?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Taking anti-anxiety medication as needed",
                "Taking daily medication for anxiety",
                "Seeing a therapist or counselor",
                "Both medication and therapy",
                "Using self-help techniques or apps",
                "Have tried treatment but not currently receiving any"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="Current treatment status helps with coordination of care"
        ),
        
        # Impact on Others
        SCIDQuestion(
            id="GAD_24",
            text="How does your worrying affect your relationships?",
            simple_text="How does your worrying affect your relationships with family, friends, or coworkers?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "It doesn't affect my relationships much",
                "Sometimes I seek reassurance from others too much",
                "I worry about my relationships and ask for reassurance",
                "Others get frustrated with my worrying",
                "I avoid social situations because I'm worried",
                "My worry makes me irritable with others",
                "It significantly strains my relationships"
            ],
            required=False,
            symptom_category="relationship_impact",
            help_text="GAD can significantly impact relationships"
        )
    ]
    
    return SCIDModule(
        id="GAD",
        name="Generalized Anxiety Disorder",
        description="Assessment of excessive worry and generalized anxiety according to DSM-5 criteria. Evaluates worry content, controllability, associated physical symptoms, and functional impairment.",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=18,
        dsm_criteria=[
            "Excessive anxiety and worry occurring more days than not for at least 6 months",
            "Difficult to control the worry",
            "Associated with three or more of: restlessness, easily fatigued, difficulty concentrating, irritability, muscle tension, sleep disturbance",
            "Significant distress or impairment in functioning"
        ],
        severity_thresholds={
            "mild": 0.4,
            "moderate": 0.6,
            "severe": 0.8
        },
        category="anxiety_disorders",
        version="1.0",
        clinical_notes="Requires excessive worry occurring more days than not for at least 6 months, with difficulty controlling the worry and associated physical/cognitive symptoms causing significant impairment."
    )
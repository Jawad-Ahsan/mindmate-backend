# scid_cv/modules/bipolar_disorder.py
"""
SCID-CV Module: Bipolar Disorder
Assessment of manic and hypomanic episodes according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_bipolar_module() -> SCIDModule:
    """Create the Bipolar Disorder SCID-CV module"""
    
    questions = [
        # Mood Episodes Screening
        SCIDQuestion(
            id="BP_01",
            text="Have you ever had a period when you felt so good, high, or excited that it was unusual for you?",
            simple_text="Have you ever felt so happy, high, or excited that other people thought it was unusual or too much?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="elevated_mood",
            help_text="This is different from normal happiness - others would notice it as being 'too much'",
            examples=["Feeling on top of the world", "Unusually energetic and happy", "Others saying you seem 'high'"]
        ),
        
        SCIDQuestion(
            id="BP_02",
            text="Have you ever had a period when you were so irritable that you got into arguments or fights?",
            simple_text="Have you ever been so irritable or angry that you got into more arguments or fights than usual?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="irritable_mood",
            help_text="This is more than normal irritability - it would be noticeable to others",
            examples=["Snapping at everyone", "Getting into arguments over small things", "Road rage incidents"]
        ),
        
        SCIDQuestion(
            id="BP_03",
            text="During these periods, how long did these feelings last?",
            simple_text="When you felt this way, how long did it last?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "A few hours",
                "Most of a day",
                "2-3 days",
                "4-6 days (about a week)",
                "1-2 weeks",
                "Several weeks",
                "A month or longer"
            ],
            symptom_category="episode_duration",
            help_text="For mania: at least 1 week. For hypomania: at least 4 days"
        ),
        
        # Manic/Hypomanic Symptoms
        SCIDQuestion(
            id="BP_04",
            text="During these periods, did you need much less sleep than usual but still feel energetic?",
            simple_text="During these times, did you sleep much less (like 2-4 hours) but still feel full of energy?",
            response_type=ResponseType.YES_NO,
            symptom_category="decreased_sleep",
            help_text="This is feeling rested with much less sleep than normal",
            examples=["Sleeping 3 hours and feeling great", "Not feeling tired despite little sleep"]
        ),
        
        SCIDQuestion(
            id="BP_05",
            text="Were you much more talkative than usual or felt pressure to keep talking?",
            simple_text="Were you talking much more than usual, or felt like you couldn't stop talking?",
            response_type=ResponseType.YES_NO,
            symptom_category="pressured_speech",
            help_text="Others might have trouble getting a word in",
            examples=["Talking non-stop", "Jumping from topic to topic", "Speaking very fast"]
        ),
        
        SCIDQuestion(
            id="BP_06",
            text="Did your thoughts race or jump quickly from one idea to another?",
            simple_text="Did your thoughts move very fast or jump from one idea to another quickly?",
            response_type=ResponseType.YES_NO,
            symptom_category="racing_thoughts",
            help_text="Your mind feels like it's going at high speed",
            examples=["Thoughts coming too fast", "Hard to focus on one thing", "Mind feels like it's racing"]
        ),
        
        SCIDQuestion(
            id="BP_07",
            text="Were you easily distracted by things around you?",
            simple_text="Were you easily distracted by sounds, sights, or things happening around you?",
            response_type=ResponseType.YES_NO,
            symptom_category="distractibility",
            help_text="More distracted than usual - attention jumps around",
            examples=["Can't finish conversations", "Attention pulled to everything", "Starting many tasks but not finishing"]
        ),
        
        SCIDQuestion(
            id="BP_08",
            text="Were you much more active or restless than usual?",
            simple_text="Were you much more active than normal - moving around a lot, starting many projects?",
            response_type=ResponseType.YES_NO,
            symptom_category="increased_activity",
            help_text="Increased goal-directed activity or physical restlessness",
            examples=["Starting multiple projects", "Cleaning house at 3 AM", "Excessive exercising"]
        ),
        
        SCIDQuestion(
            id="BP_09",
            text="Did you feel much more self-confident than usual or have grandiose ideas?",
            simple_text="Did you feel much more confident about yourself than normal, or have big ideas about yourself?",
            response_type=ResponseType.YES_NO,
            symptom_category="grandiosity",
            help_text="Unrealistic confidence or belief in your abilities",
            examples=["Feeling like you have special powers", "Thinking you're famous", "Believing you can do anything"]
        ),
        
        SCIDQuestion(
            id="BP_09A",
            text="What kinds of confident feelings or big ideas did you have?",
            simple_text="What kinds of special feelings about yourself or big ideas did you have?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Felt like I had special talents or abilities",
                "Thought I was more important than usual",
                "Had big plans or ideas for projects",
                "Felt like I could do anything",
                "Thought I was chosen for something special",
                "Believed I had connections to famous people",
                "Felt like I had special powers or knowledge"
            ],
            required=False,
            symptom_category="grandiosity_content",
            help_text="Choose all that describe your experience"
        ),
        
        SCIDQuestion(
            id="BP_10",
            text="Did you do things that were risky or that you later regretted?",
            simple_text="Did you do risky things you normally wouldn't do, like spending too much money or making big decisions quickly?",
            response_type=ResponseType.YES_NO,
            symptom_category="risky_behavior",
            help_text="Poor judgment that could have negative consequences"
        ),
        
        SCIDQuestion(
            id="BP_10A",
            text="What kinds of risky things did you do?",
            simple_text="What kinds of risky or impulsive things did you do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Spent much more money than I could afford",
                "Made big decisions without thinking them through",
                "Drove recklessly or too fast",
                "Had sexual encounters I later regretted",
                "Quit my job or ended relationships impulsively",
                "Invested money in risky ventures",
                "Started big projects without planning",
                "Other reckless behaviors"
            ],
            required=False,
            symptom_category="risky_behavior_examples",
            help_text="Choose all that apply - this helps assess severity"
        ),
        
        # Social and Sexual Behavior
        SCIDQuestion(
            id="BP_11",
            text="Were you much more social or outgoing than usual?",
            simple_text="Were you much more social, friendly, or outgoing with people than you normally are?",
            response_type=ResponseType.YES_NO,
            symptom_category="social_behavior",
            help_text="Unusually social, even with strangers",
            examples=["Talking to everyone", "Being overly friendly", "Inappropriate social boundaries"]
        ),
        
        SCIDQuestion(
            id="BP_12",
            text="Were you much more interested in sex than usual?",
            simple_text="Were you much more interested in sex than normal?",
            response_type=ResponseType.YES_NO,
            symptom_category="hypersexuality",
            help_text="Significantly increased sexual interest or behavior"
        ),
        
        # Impact and Consequences
        SCIDQuestion(
            id="BP_13",
            text="Did these symptoms cause serious problems in your life or require hospitalization?",
            simple_text="Did these symptoms cause serious problems with work, relationships, or daily life? Or did you need to go to the hospital?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No significant problems - others just noticed I was different",
                "Some problems with work or relationships", 
                "Major problems - couldn't work or maintain relationships",
                "Required hospitalization for my safety",
                "Legal problems or dangerous situations",
                "Lost job, relationships, or housing"
            ],
            symptom_category="impairment_severity",
            help_text="This helps distinguish between mania and hypomania"
        ),
        
        SCIDQuestion(
            id="BP_14",
            text="Did other people notice these changes in your behavior?",
            simple_text="Did family, friends, or coworkers notice that you were acting very differently?",
            response_type=ResponseType.YES_NO,
            symptom_category="observable_changes",
            help_text="Changes noticeable to others are important for diagnosis"
        ),
        
        SCIDQuestion(
            id="BP_14A",
            text="What did other people say about your behavior?",
            simple_text="What did other people say about how you were acting differently?",
            response_type=ResponseType.TEXT,
            required=False,
            symptom_category="observer_comments",
            help_text="Comments from others help validate the episode"
        ),
        
        # Mixed Features
        SCIDQuestion(
            id="BP_15",
            text="During these high or irritable periods, did you also feel sad or depressed at the same time?",
            simple_text="During these times when you felt high or irritable, did you also feel sad or depressed at the same time?",
            response_type=ResponseType.YES_NO,
            symptom_category="mixed_features",
            help_text="Some people experience both manic and depressive symptoms simultaneously"
        ),
        
        # Frequency and Pattern
        SCIDQuestion(
            id="BP_16",
            text="How many times have you had periods like this?",
            simple_text="About how many times have you had periods of feeling this high, energetic, or irritable?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "This was the only time",
                "2-3 times total",
                "4-5 times",
                "6-10 times",
                "More than 10 times",
                "Too many to count - happens regularly"
            ],
            symptom_category="episode_frequency",
            help_text="Multiple episodes suggest bipolar disorder"
        ),
        
        SCIDQuestion(
            id="BP_17",
            text="When was the most recent time you felt this way?",
            simple_text="When was the last time you had one of these periods?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Currently experiencing this",
                "Within the past month",
                "1-6 months ago",
                "6 months to 1 year ago",
                "1-2 years ago",
                "More than 2 years ago"
            ],
            symptom_category="recency",
            help_text="Recent episodes are more clinically relevant"
        ),
        
        # Substance Use Context  
        SCIDQuestion(
            id="BP_18",
            text="During these periods, were you using alcohol or drugs?",
            simple_text="When you felt this way, were you drinking alcohol or using any drugs?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No alcohol or drug use",
                "Normal/social drinking only",
                "More alcohol than usual",
                "Using drugs (marijuana, cocaine, etc.)",
                "Heavy alcohol and drug use",
                "These feelings started before any substance use"
            ],
            symptom_category="substance_context",
            help_text="Important to rule out substance-induced mood episodes"
        ),
        
        # Current Mood State
        SCIDQuestion(
            id="BP_19",
            text="How would you describe your mood over the past week?",
            simple_text="How has your mood been over the past week?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Normal, stable mood",
                "Somewhat elevated or energetic",
                "Mildly depressed or down",
                "Very high, energetic, or irritable",
                "Very depressed or sad",
                "Mood changes frequently throughout the day"
            ],
            symptom_category="current_mood_state",
            help_text="Current mood state helps with treatment planning"
        ),
        
        SCIDQuestion(
            id="BP_20",
            text="Are you currently taking any medication for mood problems?",
            simple_text="Are you currently taking any medication for bipolar disorder, depression, or mood problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No medications",
                "Antidepressants only",
                "Mood stabilizers (lithium, valproate, etc.)",
                "Antipsychotic medications",
                "Combination of mood medications",
                "Have taken medications but not currently"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="Current treatments affect assessment and planning"
        )
    ]
    
    return SCIDModule(
        id="BIPOLAR",
        name="Bipolar Disorder",
        description="Assessment of manic and hypomanic episodes according to DSM-5 criteria. Evaluates mood elevation, decreased sleep, grandiosity, risky behavior, and functional impairment.",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=20,
        dsm_criteria=[
            "Elevated, expansive, or irritable mood",
            "Decreased need for sleep",
            "More talkative than usual or pressure to keep talking",
            "Flight of ideas or racing thoughts",
            "Distractibility",
            "Increased goal-directed activity or psychomotor agitation",
            "Excessive involvement in risky activities"
        ],
        severity_thresholds={
            "mild": 0.4,
            "moderate": 0.6, 
            "severe": 0.8
        },
        category="mood_disorders",
        version="1.0",
        clinical_notes="Mania requires 1 week duration (or hospitalization). Hypomania requires 4 days. Must be observable by others and represent clear change from usual functioning."
    )
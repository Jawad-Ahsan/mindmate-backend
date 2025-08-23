# scid_cv/modules/major_depression.py
"""
SCID-CV Module: Major Depressive Disorder (MDD)
Assessment of major depressive episodes and disorder according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_mdd_module() -> SCIDModule:
    """Create the Major Depressive Disorder SCID-CV module"""
    
    questions = [
        # Core Mood Symptoms
        SCIDQuestion(
            id="MDD_01",
            text="During the past month, have you felt sad, down, or depressed most of the day nearly every day?",
            simple_text="In the past month, have you felt very sad or down almost every day, for most of the day?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="depressed_mood",
            help_text="This refers to feeling persistently sad, empty, or down - not just occasional sadness",
            examples=["Feeling empty inside", "Crying frequently", "Feeling hopeless"]
        ),
        
        SCIDQuestion(
            id="MDD_01A",
            text="How would you describe this sad mood?",
            simple_text="Can you tell me more about how this sadness feels?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Empty or hollow feeling inside",
                "Deep sadness that won't go away", 
                "Feeling hopeless about everything",
                "Crying spells or feeling tearful",
                "Feeling numb or unable to feel emotions",
                "Heavy or weighted down feeling"
            ],
            required=False,
            symptom_category="mood_description",
            help_text="Choose all that describe your experience"
        ),
        
        SCIDQuestion(
            id="MDD_02",
            text="During the past month, have you lost interest or pleasure in activities you usually enjoy?",
            simple_text="In the past month, have you stopped enjoying things you normally like to do?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="anhedonia",
            help_text="This includes hobbies, social activities, work, or things you used to find pleasurable",
            examples=["Not enjoying favorite TV shows", "Food doesn't taste good", "No interest in sex"]
        ),
        
        SCIDQuestion(
            id="MDD_02A",
            text="What activities have you lost interest in?",
            simple_text="What things did you used to enjoy that you don't enjoy anymore?",
            response_type=ResponseType.TEXT,
            required=False,
            symptom_category="anhedonia_specific",
            help_text="Please be specific - activities, hobbies, social interactions, etc."
        ),
        
        # Neurovegetative Symptoms
        SCIDQuestion(
            id="MDD_03",
            text="Have you experienced significant changes in your appetite or weight?",
            simple_text="Has your appetite changed a lot, or have you lost or gained weight without trying?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No significant changes in appetite or weight",
                "Much less appetite than usual - barely want to eat",
                "Much more appetite than usual - eating much more",
                "Lost weight without trying (5+ pounds in a month)",
                "Gained weight without trying (5+ pounds in a month)",
                "Both appetite and weight changes"
            ],
            symptom_category="appetite_weight",
            help_text="Significant means noticeable changes that others might comment on"
        ),
        
        SCIDQuestion(
            id="MDD_04",
            text="Have you been sleeping much more or much less than usual nearly every day?",
            simple_text="Has your sleep been very different than normal - either much more or much less?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Sleeping normally - no major changes",
                "Sleeping much more than usual (10+ hours, hard to get out of bed)",
                "Trouble falling asleep - lying awake for hours",
                "Waking up frequently during the night",
                "Waking up very early (3-5 AM) and can't go back to sleep",
                "Combination of different sleep problems"
            ],
            symptom_category="sleep_disturbance",
            help_text="Consider changes that happen most nights, not just occasionally"
        ),
        
        SCIDQuestion(
            id="MDD_05",
            text="Have others noticed that you've been moving or speaking more slowly, or that you've been restless?",
            simple_text="Have people noticed you moving very slowly, or being very restless and unable to sit still?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No noticeable changes in how I move or act",
                "Moving and talking much slower than usual",
                "Feeling very restless - can't sit still, pacing, fidgeting",
                "Sometimes slow, sometimes restless",
                "Others have commented on these changes"
            ],
            symptom_category="psychomotor_changes",
            help_text="This refers to changes that are noticeable to other people"
        ),
        
        SCIDQuestion(
            id="MDD_06",
            text="Have you felt tired or had very little energy nearly every day?",
            simple_text="Have you felt very tired or had no energy almost every day?",
            response_type=ResponseType.YES_NO,
            symptom_category="fatigue",
            help_text="This is feeling exhausted even with normal or extra sleep",
            examples=["Feeling drained", "Everything requires huge effort", "Too tired to do basic tasks"]
        ),
        
        # Cognitive Symptoms
        SCIDQuestion(
            id="MDD_07",
            text="Have you felt worthless or excessively guilty about things?",
            simple_text="Have you felt like you're worthless as a person, or felt very guilty about things?",
            response_type=ResponseType.YES_NO,
            symptom_category="guilt_worthlessness"
        ),
        
        SCIDQuestion(
            id="MDD_07A",
            text="Can you give me examples of what makes you feel guilty or worthless?",
            simple_text="What kinds of things make you feel guilty or worthless?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Feeling like I'm a burden to others",
                "Guilt about past mistakes or decisions",
                "Feeling like I'm not good enough at anything",
                "Blaming myself for things that aren't my fault",
                "Feeling like I don't deserve good things",
                "Guilt about not being able to function normally",
                "Feeling responsible for other people's problems"
            ],
            required=False,
            symptom_category="guilt_content",
            help_text="Choose all that apply to your experience"
        ),
        
        SCIDQuestion(
            id="MDD_08",
            text="Have you had trouble thinking, concentrating, or making decisions nearly every day?",
            simple_text="Have you had trouble thinking clearly, focusing, or making decisions almost every day?",
            response_type=ResponseType.YES_NO,
            symptom_category="concentration_problems",
            help_text="This includes difficulty at work, reading, watching TV, or making simple decisions",
            examples=["Can't focus on conversations", "Reading the same paragraph over", "Can't decide what to wear"]
        ),
        
        # Suicidal Ideation
        SCIDQuestion(
            id="MDD_09",
            text="Have you had repeated thoughts of death or suicide?",
            simple_text="Have you thought about death or suicide repeatedly?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.5,
            symptom_category="suicidal_ideation",
            help_text="This is a serious symptom that requires immediate attention if present"
        ),
        
        SCIDQuestion(
            id="MDD_09A",
            text="How often do you have these thoughts?",
            simple_text="How often do you think about death or suicide?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Rarely - just occasional thoughts",
                "Sometimes - a few times a week",
                "Often - almost daily thoughts",
                "Very frequently - multiple times every day",
                "Constantly - it's hard to think about anything else"
            ],
            required=False,
            symptom_category="suicidal_frequency",
            help_text="Please be honest - this helps us understand how to help you"
        ),
        
        SCIDQuestion(
            id="MDD_09B",
            text="Have you made any specific plans or attempts to harm yourself?",
            simple_text="Have you made any plans to hurt yourself or actually tried to hurt yourself?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No plans or attempts",
                "Vague thoughts but no specific plans",
                "Have thought about specific methods",
                "Have made specific plans but not acted on them",
                "Have made attempts to harm myself"
            ],
            required=False,
            criteria_weight=2.0,
            symptom_category="suicide_plan_attempt",
            help_text="This information is crucial for your safety"
        ),
        
        # Duration and Onset
        SCIDQuestion(
            id="MDD_10",
            text="How long have these symptoms been present?",
            simple_text="How long have you been feeling this way?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 2 weeks",
                "2 weeks to 1 month", 
                "1 to 3 months",
                "3 to 6 months",
                "6 months to 1 year",
                "More than 1 year",
                "On and off for several years"
            ],
            symptom_category="symptom_duration",
            help_text="For diagnosis, symptoms need to be present for at least 2 weeks"
        ),
        
        SCIDQuestion(
            id="MDD_11",
            text="When did these feelings first start?",
            simple_text="Can you remember when these feelings first began? Was there anything that happened around that time?",
            response_type=ResponseType.TEXT,
            required=False,
            symptom_category="onset_timing",
            help_text="This might include stressful events, losses, or life changes"
        ),
        
        # Functional Impairment
        SCIDQuestion(
            id="MDD_12",
            text="How much do these symptoms interfere with your daily life?",
            simple_text="How much do these feelings interfere with your work, relationships, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not at all", "A little bit", "Quite a bit", "Extremely"],
            symptom_category="functional_impairment",
            help_text="Consider impact on work, relationships, self-care, and daily tasks"
        ),
        
        SCIDQuestion(
            id="MDD_12A",
            text="Which areas of your life are most affected?",
            simple_text="Which parts of your life have been most affected by these feelings?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family or friends", 
                "Taking care of myself (hygiene, eating, etc.)",
                "Household responsibilities",
                "Social activities and hobbies",
                "Physical health and exercise",
                "Sleep and daily routine"
            ],
            required=False,
            symptom_category="impairment_areas",
            help_text="Choose all areas that have been significantly affected"
        ),
        
        # Previous Episodes
        SCIDQuestion(
            id="MDD_13",
            text="Have you ever had a period like this before in your life?",
            simple_text="Have you felt this depressed before at other times in your life?",
            response_type=ResponseType.YES_NO,
            symptom_category="previous_episodes",
            help_text="This helps determine if this is a first episode or recurrent depression"
        ),
        
        SCIDQuestion(
            id="MDD_13A",
            text="How many times have you felt this depressed before?",
            simple_text="About how many times before have you had periods of feeling this depressed?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "This is the first time",
                "One time before",
                "2-3 times before",
                "4-5 times before", 
                "More than 5 times",
                "Too many to count - it comes and goes"
            ],
            required=False,
            symptom_category="episode_count",
            help_text="Think about distinct periods of depression, not daily ups and downs"
        ),
        
        # Current Functioning
        SCIDQuestion(
            id="MDD_14",
            text="Are you currently getting any treatment for these feelings?",
            simple_text="Are you currently taking any medication or getting any treatment for depression?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Taking antidepressant medication",
                "Seeing a therapist or counselor",
                "Both medication and therapy",
                "Other treatments (support groups, etc.)",
                "Have tried treatment but not currently in treatment"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="This helps understand your current support and treatment status"
        )
    ]
    
    return SCIDModule(
        id="MDD",
        name="Major Depressive Disorder",
        description="Assessment of major depressive episodes according to DSM-5 criteria. Evaluates core mood symptoms, neurovegetative changes, cognitive symptoms, and functional impairment.",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=15,
        dsm_criteria=[
            "Depressed mood most of the day, nearly every day",
            "Markedly diminished interest or pleasure in activities", 
            "Significant weight loss/gain or appetite changes",
            "Insomnia or hypersomnia nearly every day",
            "Psychomotor agitation or retardation",
            "Fatigue or loss of energy nearly every day",
            "Feelings of worthlessness or inappropriate guilt",
            "Diminished ability to think or concentrate",
            "Recurrent thoughts of death or suicidal ideation"
        ],
        severity_thresholds={
            "mild": 0.4,
            "moderate": 0.6,
            "severe": 0.8
        },
        category="mood_disorders",
        version="1.0",
        clinical_notes="Requires at least 5 symptoms for at least 2 weeks, with at least one being depressed mood or anhedonia. Must cause significant distress or impairment."
    )
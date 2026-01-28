# scid_pd/modules/borderline_pd.py
"""
SCID-PD Module: Borderline Personality Disorder (BPD)
Assessment of borderline personality disorder according to DSM-5 criteria
"""

from ..base_types import (
    SCIDPDModule, SCIDPDQuestion, ResponseType, DSMCluster, 
    PersonalityDimensionType
)

def create_borderline_pd_module() -> SCIDPDModule:
    """Create the Borderline Personality Disorder SCID-PD module"""
    
    questions = [
        # Criterion 1: Frantic efforts to avoid abandonment
        SCIDPDQuestion(
            id="BPD_01",
            text="Do you go to great lengths to avoid being abandoned or left alone, even when the abandonment might not be real?",
            simple_text="Do you do whatever it takes to avoid being abandoned or left by important people in your life?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="abandonment_avoidance",
            requires_examples=True,
            help_text="This includes both real and imagined abandonment fears",
            examples=[
                "Begging someone not to leave you", 
                "Threatening suicide to prevent abandonment",
                "Following someone who tries to leave",
                "Checking up on people constantly"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_01A",
            text="What kinds of things have you done to try to prevent abandonment?",
            simple_text="Can you give me specific examples of what you've done to keep people from leaving you?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Threatened to hurt myself if they left",
                "Begged or pleaded with them to stay", 
                "Followed them or refused to let them leave",
                "Made dramatic gestures or scenes",
                "Promised to change completely",
                "Checked up on them constantly (calls, texts, showing up)",
                "Tried to control their other relationships",
                "Other desperate measures"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="abandonment_behaviors",
            help_text="Select all that apply to your experience"
        ),
        
        # Criterion 2: Unstable interpersonal relationships
        SCIDPDQuestion(
            id="BPD_02", 
            text="Do you have intense relationships that alternate between extremes of idealizing and devaluing the other person?",
            simple_text="Do your close relationships go back and forth between thinking someone is perfect and thinking they're terrible?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="relationship_instability",
            requires_examples=True,
            help_text="This means seeing people as all good or all bad, with little middle ground",
            examples=[
                "Putting someone on a pedestal then hating them",
                "Intense love turning to intense hatred quickly", 
                "Thinking someone is perfect then feeling betrayed"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_02A",
            text="How quickly do your feelings about important people in your life change?",
            simple_text="How fast do your feelings about people you're close to go from very positive to very negative?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "My feelings about people are generally stable",
                "They change over weeks or months",
                "They change within days", 
                "They change within hours",
                "They can change within minutes during a conversation",
                "They change constantly - multiple times per day"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="emotional_instability_interpersonal",
            help_text="Think about your closest relationships"
        ),
        
        # Criterion 3: Identity disturbance
        SCIDPDQuestion(
            id="BPD_03",
            text="Do you have an unstable sense of who you are, with your self-image or identity changing frequently?",
            simple_text="Does your sense of who you are as a person change a lot? Do you often feel confused about your identity?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="identity_disturbance",
            requires_examples=True,
            help_text="This includes changes in values, goals, career plans, friends, or personality",
            examples=[
                "Changing career goals frequently",
                "Not knowing your own values or beliefs",
                "Feeling like a different person in different situations",
                "Changing your appearance dramatically"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_03A",
            text="In what ways does your sense of self change?",
            simple_text="What aspects of yourself change or feel unclear to you?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "My career goals and life direction",
                "My values and what I believe in",
                "My personality and how I act",
                "My sexual orientation or preferences", 
                "My political or religious beliefs",
                "What kind of person I want to be with",
                "My interests and hobbies",
                "How I see myself physically"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="identity_areas",
            help_text="Select all areas where you experience confusion or frequent changes"
        ),
        
        # Criterion 4: Impulsivity
        SCIDPDQuestion(
            id="BPD_04",
            text="Are you impulsive in ways that could be harmful to you, such as with spending, sex, substance use, reckless driving, or binge eating?",
            simple_text="Do you do impulsive things that could hurt you, like spending too much money, risky sexual behavior, using drugs/alcohol, dangerous driving, or eating binges?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impulsivity",
            requires_examples=True,
            help_text="This refers to acting on urges without thinking about consequences",
            examples=[
                "Spending sprees that cause financial problems",
                "Risky sexual encounters",
                "Substance abuse binges",
                "Reckless driving or dangerous activities"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_04A",
            text="Which impulsive behaviors have been problems for you?",
            simple_text="What kinds of impulsive things do you do that cause problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Spending money I don't have",
                "Risky sexual behavior or promiscuity",
                "Binge drinking or drug use",
                "Reckless driving or dangerous activities",
                "Binge eating or purging",
                "Quitting jobs or relationships suddenly",
                "Moving or traveling impulsively",
                "Getting tattoos or piercings impulsively",
                "Online shopping sprees",
                "Gambling"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impulsive_behaviors",
            help_text="Select all that apply to your experience"
        ),
        
        # Criterion 5: Suicidal behavior or self-injury
        SCIDPDQuestion(
            id="BPD_05",
            text="Do you have recurrent suicidal behavior, gestures, threats, or self-harming behavior?",
            simple_text="Do you repeatedly have thoughts of suicide, make suicide threats, or hurt yourself on purpose?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.5,  # Higher weight due to safety concerns
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="self_harm_suicidality",
            help_text="This is very important for safety assessment",
            examples=[
                "Cutting or burning yourself",
                "Suicide attempts or threats",
                "Talking about wanting to die",
                "Other forms of self-injury"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_05A",
            text="What forms of self-harm or suicidal behavior have you engaged in?",
            simple_text="What ways have you hurt yourself or thought about ending your life?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Cutting myself with sharp objects",
                "Burning myself",
                "Hitting myself or banging head against things",
                "Overdosing on medications",
                "Making suicide attempts",
                "Making suicide threats to others",
                "Having detailed suicide plans",
                "Thinking about suicide frequently",
                "Other forms of self-injury"
            ],
            required=False,
            criteria_weight=1.5,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="self_harm_methods",
            help_text="Please be honest - this information is crucial for your safety"
        ),
        
        # Criterion 6: Emotional instability
        SCIDPDQuestion(
            id="BPD_06",
            text="Do you have intense mood swings, with periods of feeling very depressed, anxious, or irritable that usually last a few hours to a few days?",
            simple_text="Do your moods change very intensely and quickly - like going from very sad to very angry to very anxious within hours or days?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="affective_instability",
            help_text="These mood changes are usually much more intense than normal mood variations",
            examples=[
                "Going from happy to furious within hours",
                "Intense depression that lifts suddenly",
                "Extreme anxiety that comes and goes",
                "Feeling emotionally out of control"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_06A", 
            text="How long do these intense moods typically last?",
            simple_text="When you have these intense mood changes, how long do they usually last?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have significant mood swings",
                "Several weeks or months",
                "About a week",
                "A few days",
                "Several hours to a day",
                "A few hours",
                "Minutes to an hour",
                "They change constantly throughout the day"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="mood_duration",
            help_text="Think about your typical pattern of mood changes"
        ),
        
        # Criterion 7: Chronic emptiness
        SCIDPDQuestion(
            id="BPD_07",
            text="Do you often feel empty inside?",
            simple_text="Do you often feel empty, like there's nothing inside you or like you're hollow?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="chronic_emptiness",
            help_text="This is a persistent feeling of inner emptiness or void",
            examples=[
                "Feeling like there's nothing inside you",
                "Feeling hollow or vacant",
                "Feeling like you don't exist",
                "Needing constant stimulation to feel alive"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_07A",
            text="How often do you experience this feeling of emptiness?",
            simple_text="How often do you feel empty inside?",
            response_type=ResponseType.FREQUENCY,
            options=[
                "never",
                "rarely", 
                "sometimes",
                "often",
                "very often",
                "almost constantly"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="emptiness_frequency",
            help_text="Consider your overall pattern over recent months"
        ),
        
        # Criterion 8: Inappropriate anger
        SCIDPDQuestion(
            id="BPD_08",
            text="Do you have intense, inappropriate anger or difficulty controlling your anger?",
            simple_text="Do you get very angry in ways that seem too intense, or do you have trouble controlling your anger?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="anger_dysregulation",
            requires_examples=True,
            help_text="This includes anger that's too intense for the situation or hard to control",
            examples=[
                "Explosive outbursts over minor things",
                "Physical fights or throwing things",
                "Intense rage that's hard to control",
                "Anger that seems inappropriate to others"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_08A",
            text="How do you typically express intense anger?",
            simple_text="When you get very angry, what do you usually do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't usually get intensely angry",
                "Yell or scream at people",
                "Throw or break objects",
                "Get into physical fights",
                "Slam doors or punch walls",
                "Say cruel or hurtful things",
                "Have explosive outbursts then feel guilty",
                "Withdraw and give people silent treatment",
                "Turn the anger on myself instead"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="anger_expression",
            help_text="Select all ways you typically express intense anger"
        ),
        
        # Criterion 9: Dissociation/paranoid ideation
        SCIDPDQuestion(
            id="BPD_09",
            text="During times of stress, do you have paranoid thoughts or feel disconnected from yourself or reality?",
            simple_text="When you're very stressed, do you become suspicious of others or feel like you're not really there or that things aren't real?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="stress_related_dissociation_paranoia",
            help_text="This includes both paranoid thoughts and dissociative symptoms during stress",
            examples=[
                "Feeling like people are plotting against you",
                "Feeling disconnected from your body",
                "Feeling like you're watching yourself from outside",
                "Things feeling unreal or dreamlike"
            ]
        ),
        
        SCIDPDQuestion(
            id="BPD_09A",
            text="What kinds of stress-related symptoms do you experience?",
            simple_text="When you're very stressed, which of these things happen to you?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't experience these symptoms when stressed",
                "Feeling like people are talking about me or plotting",
                "Becoming very suspicious of others' motives",
                "Feeling like I'm outside my body watching myself",
                "Feeling disconnected from my emotions or thoughts",
                "Things around me feel unreal or dreamlike",
                "Feeling like I'm not really there or existing",
                "Having trouble remembering what happened during stress",
                "Feeling like I'm going crazy or losing my mind"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="dissociation_paranoia_types",
            help_text="Select all that apply to your experience during high stress"
        ),
        
        # Timeline and Onset Questions
        SCIDPDQuestion(
            id="BPD_10",
            text="When did you first notice these patterns of intense emotions and relationship difficulties?",
            simple_text="When did these intense emotions and relationship problems first start?",
            response_type=ResponseType.ONSET_AGE,
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="onset_timing",
            onset_relevant=True,
            help_text="Personality disorders typically begin by early adulthood"
        ),
        
        SCIDPDQuestion(
            id="BPD_10A",
            text="Did anything specific trigger the start of these problems?",
            simple_text="Was there anything that happened around the time these problems started?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No specific trigger that I can remember",
                "Family problems or trauma in childhood",
                "Abuse (physical, sexual, or emotional)",
                "Parents' divorce or family breakup",
                "Death of someone important",
                "Starting school or major life transition",
                "First romantic relationship ending",
                "Moving to a new place",
                "Other traumatic or stressful events"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="onset_triggers",
            help_text="Select all that might have contributed to the start of these patterns"
        ),
        
        # Pervasiveness across contexts
        SCIDPDQuestion(
            id="BPD_11",
            text="Do these emotional and relationship patterns occur across different areas of your life?",
            simple_text="Do you have these same emotional and relationship problems at work, with family, with friends, and in romantic relationships?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Only in romantic relationships",
                "Only with family members",
                "Only with close friends",
                "In most of my close relationships",
                "In all my relationships regardless of type",
                "At work/school and in personal relationships",
                "In every area of my life"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="pervasiveness",
            pervasiveness_check=True,
            help_text="Personality patterns typically occur across multiple contexts"
        ),
        
        # Functional impairment
        SCIDPDQuestion(
            id="BPD_12",
            text="How much do these emotional and relationship patterns interfere with your daily life?",
            simple_text="How much do these intense emotions and relationship problems affect your ability to function in daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "A little", "Moderately", "Quite a bit", "Extremely"],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="functional_impairment",
            help_text="Consider impact on work, relationships, self-care, and daily activities"
        ),
        
        SCIDPDQuestion(
            id="BPD_12A",
            text="Which areas of your life are most affected by these patterns?",
            simple_text="Which parts of your life are most impacted by these emotional and relationship difficulties?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Romantic relationships",
                "Friendships and social relationships",
                "Family relationships",
                "Parenting (if applicable)",
                "Financial stability",
                "Physical health and self-care",
                "Legal problems",
                "Housing stability",
                "Overall life satisfaction"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impairment_areas",
            help_text="Select all areas significantly affected"
        ),
        
        # Stability of patterns
        SCIDPDQuestion(
            id="BPD_13",
            text="Have these emotional and relationship patterns been consistent throughout your adult life?",
            simple_text="Have you had these same emotional and relationship problems consistently since you became an adult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, these are recent problems (less than 2 years)",
                "They've been present for 2-5 years",
                "They've been present for 5-10 years", 
                "They've been consistent since my late teens/early twenties",
                "They've been present as long as I can remember",
                "They come and go - sometimes better, sometimes worse",
                "They've gotten worse over time",
                "They've gotten somewhat better with age"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="pattern_stability",
            help_text="Personality disorders involve stable, long-term patterns"
        ),
        
        # Current treatment and coping
        SCIDPDQuestion(
            id="BPD_14",
            text="Are you currently receiving any treatment for these emotional difficulties?",
            simple_text="Are you currently getting any help or treatment for these emotional problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Individual therapy/counseling",
                "Group therapy (like DBT skills group)",
                "Psychiatric medication",
                "Both therapy and medication",
                "Hospitalization or intensive treatment",
                "Support groups",
                "Alternative treatments (meditation, etc.)"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="current_treatment",
            help_text="This helps understand current support and treatment status"
        ),
        
        SCIDPDQuestion(
            id="BPD_15",
            text="What strategies do you use to cope with intense emotions?",
            simple_text="What do you do to try to deal with very intense emotions?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have effective coping strategies",
                "Talk to friends or family",
                "Use breathing or relaxation techniques",
                "Exercise or physical activity",
                "Listen to music or creative activities",
                "Use alcohol or drugs",
                "Engage in self-harm",
                "Isolate myself until it passes",
                "Try to distract myself with activities",
                "Use skills learned in therapy"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="coping_strategies",
            help_text="Select all strategies you use, both healthy and unhealthy"
        )
    ]
    
    return SCIDPDModule(
        id="BPD",
        name="Borderline Personality Disorder",
        description="Assessment of borderline personality disorder according to DSM-5 criteria. Evaluates emotional dysregulation, interpersonal instability, identity disturbance, and behavioral impulsivity.",
        dsm_cluster=DSMCluster.CLUSTER_B,
        questions=questions,
        diagnostic_threshold=0.65,
        dimensional_threshold=60.0,
        estimated_time_mins=35,
        dsm_criteria=[
            "Frantic efforts to avoid real or imagined abandonment",
            "Pattern of unstable and intense interpersonal relationships",
            "Identity disturbance: markedly and persistently unstable self-image",
            "Impulsivity in potentially self-damaging areas",
            "Recurrent suicidal behavior, gestures, or threats, or self-mutilating behavior",
            "Affective instability due to marked reactivity of mood",
            "Chronic feelings of emptiness",
            "Inappropriate, intense anger or difficulty controlling anger",
            "Transient, stress-related paranoid ideation or severe dissociative symptoms"
        ],
        severity_thresholds={
            "mild": 0.5,
            "moderate": 0.65,
            "severe": 0.8,
            "extreme": 0.9
        },
        core_features=[
            "Emotional dysregulation",
            "Interpersonal instability", 
            "Identity disturbance",
            "Behavioral impulsivity",
            "Self-harm and suicidality"
        ],
        differential_diagnoses=[
            "Bipolar Disorder",
            "Major Depressive Disorder",
            "Histrionic Personality Disorder",
            "Narcissistic Personality Disorder", 
            "Antisocial Personality Disorder",
            "Post-Traumatic Stress Disorder",
            "Complex PTSD"
        ],
        minimum_criteria_count=5,
        requires_onset_before_18=False,  # BPD can be diagnosed at 18+
        version="1.0",
        clinical_notes="Requires at least 5 of 9 criteria. Pattern must be pervasive across contexts and stable over time. Consider developmental trauma history and attachment difficulties. High risk for self-harm and suicide - assess safety carefully."
    )
# scid_pd/modules/antisocial_pd.py
"""
SCID-PD Module: Antisocial Personality Disorder (ASPD)
Assessment of antisocial personality disorder according to DSM-5 criteria
"""

from ..base_types import (
    SCIDPDModule, SCIDPDQuestion, ResponseType, DSMCluster, 
    PersonalityDimensionType
)

def create_antisocial_pd_module() -> SCIDPDModule:
    """Create the Antisocial Personality Disorder SCID-PD module"""
    
    questions = [
        # Criterion A: Age requirement (18+)
        SCIDPDQuestion(
            id="ASPD_01",
            text="Are you at least 18 years of age?",
            simple_text="Are you 18 years old or older?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="age_requirement",
            required=True,
            help_text="ASPD cannot be diagnosed before age 18"
        ),
        
        # Criterion B1: Failure to conform to social norms with respect to lawful behaviors
        SCIDPDQuestion(
            id="ASPD_02",
            text="Do you repeatedly perform acts that could lead to arrest, whether or not you were actually arrested?",
            simple_text="Do you often do things that are against the law or that could get you arrested?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="lawful_behavior_failure",
            requires_examples=True,
            help_text="This includes any illegal activities, regardless of whether arrested",
            examples=[
                "Theft or shoplifting",
                "Drug dealing or possession",
                "Assault or fighting",
                "Driving violations or reckless driving",
                "Vandalism or property destruction"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_02A",
            text="What types of illegal activities have you engaged in?",
            simple_text="What kinds of illegal things have you done?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I haven't engaged in illegal activities",
                "Minor traffic violations",
                "Theft, shoplifting, or burglary",
                "Drug use or possession",
                "Drug dealing or distribution",
                "Physical fights or assault",
                "Vandalism or property destruction",
                "Fraud or financial crimes",
                "Weapons-related offenses",
                "Other serious criminal activities"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="illegal_activities",
            help_text="Select all that apply - this information is confidential"
        ),
        
        # Criterion B2: Deceitfulness
        SCIDPDQuestion(
            id="ASPD_03",
            text="Are you deceitful, as indicated by repeatedly lying, using aliases, or conning others for personal profit or pleasure?",
            simple_text="Do you frequently lie, use fake names, or trick people to get what you want or for fun?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="deceitfulness",
            requires_examples=True,
            help_text="This includes lies for profit, pleasure, or to avoid consequences",
            examples=[
                "Lying frequently to family, friends, or employers",
                "Using false identities or aliases",
                "Conning or scamming others for money",
                "Creating elaborate deceptions"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_03A",
            text="How often do you lie or deceive others?",
            simple_text="How frequently do you lie to other people?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I rarely lie except for minor social courtesies",
                "I occasionally lie to avoid hurting feelings",
                "I sometimes lie to avoid getting in trouble",
                "I often lie to make myself look better",
                "I frequently lie to get what I want",
                "I lie so often it's become automatic",
                "I enjoy deceiving others and seeing if I can get away with it",
                "Lying and manipulation are just part of how I operate"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="lying_frequency",
            help_text="Be honest about your patterns of deception"
        ),
        
        # Criterion B3: Impulsivity
        SCIDPDQuestion(
            id="ASPD_04",
            text="Are you impulsive or do you fail to plan ahead?",
            simple_text="Do you act on impulse without thinking ahead, or do you have trouble making plans for the future?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impulsivity_planning",
            requires_examples=True,
            help_text="This includes acting without considering consequences",
            examples=[
                "Making major decisions on the spur of the moment",
                "Quitting jobs without having another lined up",
                "Moving frequently without planning",
                "Spending money impulsively"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_04A",
            text="How do you typically make important decisions?",
            simple_text="When you have to make big decisions, what do you usually do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I carefully plan and consider all options",
                "I think it through and consult others",
                "I make quick decisions but usually good ones",
                "I often decide based on what feels right at the moment",
                "I act on impulse and figure it out later",
                "I rarely plan ahead - I just go with the flow",
                "Planning feels boring - I prefer to be spontaneous",
                "I make decisions based on immediate desires or needs"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="decision_making_style",
            help_text="Think about your typical approach to major life decisions"
        ),
        
        # Criterion B4: Irritability and aggressiveness
        SCIDPDQuestion(
            id="ASPD_05",
            text="Are you irritable and aggressive, as indicated by repeated physical fights or assaults?",
            simple_text="Do you get into physical fights or assault people repeatedly because you're easily irritated or aggressive?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="irritability_aggression",
            requires_examples=True,
            help_text="This refers to a pattern of physical aggression",
            examples=[
                "Getting into frequent fights",
                "Hitting or pushing people when angry",
                "Road rage incidents",
                "Assaulting others during arguments"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_05A",
            text="How do you typically handle anger or frustration?",
            simple_text="When you get really angry or frustrated, what do you usually do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I take time to cool down before responding",
                "I express my feelings verbally but stay in control",
                "I might raise my voice but don't get physical",
                "I sometimes slam doors or throw objects",
                "I've pushed or shoved people when very angry",
                "I've gotten into physical fights multiple times",
                "I often threaten violence when angry",
                "I have a hard time controlling my violent impulses"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="anger_expression",
            help_text="Consider your typical responses to anger"
        ),
        
        # Criterion B5: Reckless disregard for safety
        SCIDPDQuestion(
            id="ASPD_06",
            text="Do you have reckless disregard for the safety of yourself or others?",
            simple_text="Do you do dangerous things without caring about the safety of yourself or other people?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="safety_disregard",
            requires_examples=True,
            help_text="This includes behaviors that endanger self or others",
            examples=[
                "Driving recklessly or under the influence",
                "Engaging in dangerous activities without precautions",
                "Putting others at risk through your actions",
                "Ignoring safety rules or warnings"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_06A",
            text="What kinds of risky or dangerous behaviors have you engaged in?",
            simple_text="What dangerous things have you done that could have hurt you or others?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I'm generally careful about safety",
                "Occasional risky driving when in a hurry",
                "Driving under the influence of alcohol or drugs",
                "Extreme sports or dangerous activities without proper safety gear",
                "Putting others at risk through reckless behavior",
                "Ignoring safety rules at work or in public",
                "Engaging in dangerous activities for thrills",
                "Repeatedly doing things that could seriously injure myself or others"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="risky_behaviors",
            help_text="Select all that apply to your behavior patterns"
        ),
        
        # Criterion B6: Consistent irresponsibility
        SCIDPDQuestion(
            id="ASPD_07",
            text="Are you consistently irresponsible, as indicated by repeated failure to sustain consistent work behavior or honor financial obligations?",
            simple_text="Do you have trouble keeping jobs or paying your bills because you're irresponsible?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="irresponsibility",
            requires_examples=True,
            help_text="This includes work and financial irresponsibility",
            examples=[
                "Frequently changing or losing jobs",
                "Not paying bills or debts",
                "Failing to provide for dependents",
                "Not following through on commitments"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_07A",
            text="How would you describe your work and financial history?",
            simple_text="How consistent have you been with keeping jobs and paying your bills?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I have a stable work history and pay bills on time",
                "I've had some job changes but generally responsible",
                "I've had several jobs but usually for good reasons",
                "I have trouble staying at jobs for extended periods",
                "I frequently quit or get fired from jobs",
                "I often don't pay bills on time or default on debts",
                "I have trouble meeting basic financial obligations",
                "Work and financial responsibility are ongoing problems for me"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="responsibility_patterns",
            help_text="Consider your overall pattern of work and financial behavior"
        ),
        
        # Criterion B7: Lack of remorse
        SCIDPDQuestion(
            id="ASPD_08",
            text="Do you lack remorse, as indicated by being indifferent to or rationalizing having hurt, mistreated, or stolen from another?",
            simple_text="When you hurt, mistreat, or steal from someone, do you feel bad about it, or do you not care or make excuses?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="lack_of_remorse",
            requires_examples=True,
            help_text="This involves lack of guilt or empathy for victims",
            examples=[
                "Not feeling bad after hurting someone",
                "Justifying harmful behavior",
                "Blaming victims for what happened to them",
                "Being indifferent to others' pain"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_08A",
            text="How do you typically feel after you've hurt someone or done something wrong?",
            simple_text="When you've hurt someone or done something you shouldn't have, how do you usually feel?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel genuinely guilty and want to make amends",
                "I feel bad and try to apologize or fix things",
                "I feel somewhat guilty but get over it quickly",
                "I feel justified if they deserved it somehow",
                "I don't really feel bad - they should have been more careful",
                "I think people are too sensitive about these things",
                "I rarely feel guilty about my actions",
                "People bring problems on themselves"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="guilt_remorse_patterns",
            help_text="Be honest about your typical emotional responses"
        ),
        
        # Criterion C: Evidence of conduct disorder before age 15
        SCIDPDQuestion(
            id="ASPD_09",
            text="Before you were 15 years old, did you have problems with lying, stealing, fighting, skipping school, or other serious behavioral problems?",
            simple_text="When you were a child or young teenager (before 15), did you have serious behavior problems like lying, stealing, fighting, or skipping school?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.5,  # Higher weight as it's required for diagnosis
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="childhood_conduct_problems",
            requires_examples=True,
            help_text="This is required - ASPD must have roots in childhood conduct disorder",
            examples=[
                "Frequent lying or stealing as a child",
                "Getting into fights at school",
                "Skipping school or running away",
                "Cruelty to animals or people"
            ]
        ),
        
        SCIDPDQuestion(
            id="ASPD_09A",
            text="What kinds of behavioral problems did you have before age 15?",
            simple_text="What specific behavior problems did you have as a child or young teenager?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I didn't have significant behavioral problems as a child",
                "Occasional lying or minor rule-breaking",
                "Frequent lying to parents or teachers",
                "Stealing from stores, school, or family",
                "Getting into fights with other children",
                "Bullying or being cruel to others",
                "Skipping school or truancy",
                "Running away from home",
                "Destroying property or vandalism",
                "Cruelty to animals",
                "Early sexual behavior or aggression",
                "Fire-setting or other dangerous behaviors"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="childhood_problem_types",
            help_text="Select all that applied to you before age 15"
        ),
        
        SCIDPDQuestion(
            id="ASPD_09B",
            text="At what age did these serious behavioral problems first begin?",
            simple_text="How old were you when these behavior problems first started?",
            response_type=ResponseType.ONSET_AGE,
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="conduct_disorder_onset",
            onset_relevant=True,
            help_text="Try to remember when these patterns first appeared"
        ),
        
        # Timeline and pattern assessment
        SCIDPDQuestion(
            id="ASPD_10",
            text="Have these antisocial behaviors been consistent since you became an adult?",
            simple_text="Since you became an adult, have you continued to have these kinds of problems with following rules and treating others fairly?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I outgrew these problems in adulthood",
                "They decreased significantly but still occur occasionally",
                "They've continued at about the same level",
                "They've gotten worse as an adult",
                "They come and go depending on my circumstances",
                "They're worse when I'm under stress",
                "They've been consistent since my late teens"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="adult_pattern_consistency",
            help_text="Consider the overall pattern since age 18"
        ),
        
        # Pervasiveness across contexts
        SCIDPDQuestion(
            id="ASPD_11",
            text="Do these antisocial behaviors occur across different areas of your life?",
            simple_text="Do you have these same problems with rules and treating people fairly at work, with family, with friends, and in romantic relationships?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Only in specific situations or with certain people",
                "Mainly when I'm under stress or pressure",
                "More at work/school than in personal relationships",
                "More in personal relationships than at work/school",
                "In most areas of my life",
                "In all areas of my life consistently",
                "It depends on whether people respect me or not"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="pervasiveness",
            pervasiveness_check=True,
            help_text="Personality patterns typically occur across multiple contexts"
        ),
        
        # Functional impairment
        SCIDPDQuestion(
            id="ASPD_12",
            text="How much do these antisocial behaviors interfere with your daily functioning?",
            simple_text="How much do these behaviors cause problems in your work, relationships, or daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "A little", "Moderately", "Quite a bit", "Extremely"],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="functional_impairment",
            help_text="Consider impact on relationships, work, legal status, and life satisfaction"
        ),
        
        SCIDPDQuestion(
            id="ASPD_12A",
            text="Which areas of your life are most affected by these behavioral patterns?",
            simple_text="What parts of your life have the most problems because of these behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or career advancement",
                "Romantic relationships and intimacy",
                "Friendships and social relationships",
                "Family relationships",
                "Parenting responsibilities (if applicable)",
                "Financial stability",
                "Legal problems or criminal justice involvement",
                "Housing stability",
                "Physical health and safety",
                "Overall life satisfaction",
                "No significant impairment"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impairment_areas",
            help_text="Select all areas significantly affected"
        ),
        
        # Substance use consideration
        SCIDPDQuestion(
            id="ASPD_13",
            text="Do these antisocial behaviors occur when you are not under the influence of alcohol or drugs?",
            simple_text="Do you have these behavioral problems even when you're not drinking or using drugs?",
            response_type=ResponseType.YES_NO,
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="substance_independence",
            help_text="ASPD behaviors must not be solely due to substance use"
        ),
        
        SCIDPDQuestion(
            id="ASPD_13A",
            text="How does alcohol or drug use affect these behaviors?",
            simple_text="Do drugs or alcohol make these behaviors better, worse, or about the same?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't use alcohol or drugs",
                "Substances don't really affect these behaviors",
                "I'm actually better behaved when using substances",
                "Substances make these behaviors somewhat worse",
                "Substances make these behaviors much worse",
                "I only have these problems when using substances",
                "These behaviors led me to use substances to cope"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="substance_interaction",
            help_text="Consider the relationship between substance use and antisocial behavior"
        ),
        
        # Legal history
        SCIDPDQuestion(
            id="ASPD_14",
            text="Have you had legal problems or been arrested?",
            simple_text="Have you been arrested, charged with crimes, or had other legal problems?",
            response_type=ResponseType.YES_NO,
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="legal_history",
            help_text="This helps understand the severity and consequences of antisocial behavior"
        ),
        
        SCIDPDQuestion(
            id="ASPD_14A",
            text="What types of legal problems have you had?",
            simple_text="What kinds of arrests, charges, or legal issues have you experienced?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No legal problems",
                "Minor traffic violations only",
                "Arrests but no convictions",
                "Misdemeanor convictions",
                "Felony convictions",
                "Multiple arrests or convictions",
                "Juvenile legal problems",
                "Currently on probation or parole",
                "Time in jail or prison",
                "Restraining orders or domestic violence charges"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="legal_problem_types",
            help_text="Select all that apply to your legal history"
        ),
        
        # Treatment and insight
        SCIDPDQuestion(
            id="ASPD_15",
            text="How do you view your pattern of antisocial behavior?",
            simple_text="Do you see these behaviors as a problem, or do you think they're justified given how the world works?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't see myself as having antisocial behaviors",
                "These behaviors are necessary to survive in this world",
                "Other people are too naive or weak",
                "I do what I need to do to get ahead",
                "Maybe I have some problems with following rules",
                "I sometimes feel bad about how I treat others",
                "I recognize these behaviors cause problems for me",
                "I wish I could change these patterns but it's hard"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="insight_level",
            help_text="Consider your level of awareness and concern about these patterns"
        )
    ]
    
    return SCIDPDModule(
        id="ASPD",
        name="Antisocial Personality Disorder",
        description="Assessment of antisocial personality disorder according to DSM-5 criteria. Evaluates pervasive pattern of disregard for and violation of others' rights, with onset in childhood (conduct disorder) continuing into adulthood.",
        dsm_cluster=DSMCluster.CLUSTER_B,
        questions=questions,
        diagnostic_threshold=0.70,  # Slightly higher threshold due to severity
        dimensional_threshold=65.0,
        estimated_time_mins=40,
        dsm_criteria=[
            "Age at least 18 years",
            "Failure to conform to social norms with respect to lawful behaviors",
            "Deceitfulness (lying, aliases, conning others)",
            "Impulsivity or failure to plan ahead",
            "Irritability and aggressiveness (repeated fights or assaults)",
            "Reckless disregard for safety of self or others",
            "Consistent irresponsibility (work behavior, financial obligations)",
            "Lack of remorse (indifferent to or rationalizing harm to others)",
            "Evidence of conduct disorder with onset before age 15"
        ],
        severity_thresholds={
            "mild": 0.55,
            "moderate": 0.70,
            "severe": 0.85,
            "extreme": 0.95
        },
        core_features=[
            "Disregard for others' rights",
            "Deceitfulness and manipulation",
            "Impulsivity and poor planning",
            "Aggressiveness and irritability",
            "Irresponsibility",
            "Lack of remorse or empathy",
            "Childhood conduct disorder"
        ],
        differential_diagnoses=[
            "Borderline Personality Disorder",
            "Narcissistic Personality Disorder",
            "Substance Use Disorders",
            "Bipolar Disorder (Manic Episodes)",
            "Schizophrenia or Delusional Disorder",
            "Adult Antisocial Behavior (V-code, not a mental disorder)",
            "Conduct Disorder (if under 18)"
        ],
        minimum_criteria_count=3,  # Only need 3+ of criteria B plus A and C
        requires_onset_before_18=False,  # Age 18+ required but pattern starts in childhood
        version="1.0",
        clinical_notes="Requires evidence of conduct disorder before age 15, current age 18+, and at least 3 of 7 adult antisocial criteria. Antisocial behavior must not occur exclusively during manic episodes or be better explained by substance use. High risk for violence, criminal behavior, and treatment non-compliance. Consider safety and legal/ethical obligations."
    )
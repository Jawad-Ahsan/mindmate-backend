# scid_pd/modules/narcissistic_pd.py
"""
SCID-PD Module: Narcissistic Personality Disorder (NPD)
Assessment of narcissistic personality disorder according to DSM-5 criteria
"""

from ..base_types import (
    SCIDPDModule, SCIDPDQuestion, ResponseType, DSMCluster, 
    PersonalityDimensionType
)

def create_narcissistic_pd_module() -> SCIDPDModule:
    """Create the Narcissistic Personality Disorder SCID-PD module"""
    
    questions = [
        # Criterion 1: Grandiose sense of self-importance
        SCIDPDQuestion(
            id="NPD_01",
            text="Do you have a grandiose sense of self-importance, such as exaggerating your achievements and talents or expecting to be recognized as superior without commensurate achievements?",
            simple_text="Do you feel you're more important or special than most people, or expect others to see you as superior even when your achievements don't match that?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="grandiose_self_importance",
            requires_examples=True,
            help_text="This includes inflated self-image and expectations of recognition",
            examples=[
                "Exaggerating your accomplishments or talents",
                "Expecting to be treated as special or superior",
                "Believing you're more important than you really are",
                "Taking credit for things you didn't fully accomplish"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_01A",
            text="How do you typically present yourself to others?",
            simple_text="How do you usually talk about yourself and your accomplishments to other people?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I'm modest about my achievements",
                "I'm honest about both strengths and weaknesses",
                "I emphasize my best qualities and downplay weaknesses",
                "I exaggerate my achievements to impress others",
                "I expect people to recognize my superiority",
                "I often embellish stories to make myself look better",
                "I believe I'm destined for greatness",
                "I feel others don't appreciate how special I am"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="self_presentation",
            help_text="Select all that describe how you present yourself"
        ),
        
        # Criterion 2: Preoccupied with fantasies of unlimited success, power, brilliance, beauty, or ideal love
        SCIDPDQuestion(
            id="NPD_02",
            text="Are you preoccupied with fantasies of unlimited success, power, brilliance, beauty, or ideal love?",
            simple_text="Do you spend a lot of time daydreaming about being incredibly successful, powerful, brilliant, beautiful, or finding perfect love?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="grandiose_fantasies",
            requires_examples=True,
            help_text="These are recurring fantasies about achieving extraordinary things",
            examples=[
                "Fantasizing about unlimited wealth or success",
                "Imagining having great power or influence",
                "Dreaming of being recognized as brilliant",
                "Fantasizing about perfect beauty or perfect love"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_02A",
            text="What kinds of fantasies do you have about your future or potential?",
            simple_text="What do you daydream about regarding your future success or achievements?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have particular fantasies about success",
                "Becoming wealthy or financially successful",
                "Having power or influence over others",
                "Being recognized as exceptionally talented or brilliant",
                "Being famous or widely admired",
                "Finding the perfect romantic partner",
                "Being considered exceptionally attractive",
                "Achieving something that will make me immortal or legendary",
                "Having unlimited freedom or resources"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="fantasy_types",
            help_text="Select all types of fantasies you regularly have"
        ),
        
        # Criterion 3: Believes they are "special" and unique
        SCIDPDQuestion(
            id="NPD_03",
            text="Do you believe that you are 'special' and unique and can only be understood by, or should associate with, other special or high-status people?",
            simple_text="Do you feel you're so special and unique that only other very special or important people can really understand you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="special_unique_beliefs",
            requires_examples=True,
            help_text="This includes believing you should only associate with high-status individuals",
            examples=[
                "Feeling only certain elite people can understand you",
                "Wanting to associate only with high-status people",
                "Believing you're too unique for ordinary people",
                "Thinking regular people are beneath you"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_03A",
            text="How do you choose who to spend time with or associate with?",
            simple_text="What kind of people do you prefer to be around, and why?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I enjoy spending time with all kinds of people",
                "I prefer people who share my interests",
                "I gravitate toward successful or accomplished people",
                "I prefer people who appreciate my special qualities",
                "I only feel comfortable with high-status individuals",
                "I avoid people I consider beneath my level",
                "I seek out people who can enhance my image",
                "I feel most understood by other exceptional people"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="social_selectivity",
            help_text="Consider your typical preferences in relationships"
        ),
        
        # Criterion 4: Requires excessive admiration
        SCIDPDQuestion(
            id="NPD_04",
            text="Do you require excessive admiration from others?",
            simple_text="Do you need a lot of praise, compliments, or admiration from other people to feel good about yourself?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="admiration_seeking",
            requires_examples=True,
            help_text="This goes beyond normal desire for approval to excessive need",
            examples=[
                "Getting upset when not praised enough",
                "Constantly seeking compliments",
                "Fishing for admiration in conversations",
                "Feeling empty without constant validation"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_04A",
            text="How do you typically seek or respond to praise and admiration?",
            simple_text="What do you do to get praise from others, and how do you feel when you don't get it?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't actively seek praise from others",
                "I appreciate compliments but don't seek them out",
                "I often steer conversations toward my accomplishments",
                "I feel hurt when my efforts aren't acknowledged",
                "I regularly fish for compliments in conversations",
                "I get upset when others don't notice my achievements",
                "I need constant reassurance about my worth",
                "I feel empty or deflated without regular praise"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="admiration_behaviors",
            help_text="Select all that describe your relationship with praise and admiration"
        ),
        
        # Criterion 5: Sense of entitlement
        SCIDPDQuestion(
            id="NPD_05",
            text="Do you have a sense of entitlement - unreasonable expectations of especially favorable treatment or automatic compliance with your expectations?",
            simple_text="Do you expect to be treated better than others or expect people to automatically go along with what you want?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="entitlement",
            requires_examples=True,
            help_text="This includes expecting special treatment and automatic compliance",
            examples=[
                "Expecting to skip lines or get special treatment",
                "Getting angry when rules apply to you",
                "Expecting others to drop everything for you",
                "Believing you deserve more than others"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_05A",
            text="How do you typically react when you don't get what you expect?",
            simple_text="What happens when people don't treat you the way you think you should be treated?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I accept it and move on",
                "I feel disappointed but understand",
                "I feel frustrated but try to be reasonable",
                "I get angry and express my displeasure",
                "I can't believe people would treat me that way",
                "I become furious and demand better treatment",
                "I feel deeply insulted and may retaliate",
                "I assume they don't know who I am or my importance"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="entitlement_reactions",
            help_text="Consider your typical emotional and behavioral responses"
        ),
        
        # Criterion 6: Interpersonally exploitative
        SCIDPDQuestion(
            id="NPD_06",
            text="Are you interpersonally exploitative - do you take advantage of others to achieve your own ends?",
            simple_text="Do you use other people to get what you want, even if it's not fair to them?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="interpersonal_exploitation",
            requires_examples=True,
            help_text="This involves using others without regard for their wellbeing",
            examples=[
                "Using people's feelings to manipulate them",
                "Taking credit for others' work",
                "Making promises you don't intend to keep",
                "Using relationships primarily for personal gain"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_06A",
            text="How do you typically approach getting what you want from others?",
            simple_text="When you need something from someone, what do you usually do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I ask directly and accept their decision",
                "I try to make fair exchanges or agreements",
                "I emphasize how it would benefit them too",
                "I use my charm or persuasion skills",
                "I make them feel guilty if they don't help",
                "I use their feelings for me to get compliance",
                "I promise things I may not deliver to get agreement",
                "I find ways to make them feel obligated to help me"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="influence_tactics",
            help_text="Select approaches you commonly use"
        ),
        
        # Criterion 7: Lacks empathy
        SCIDPDQuestion(
            id="NPD_07",
            text="Do you lack empathy - are you unwilling to recognize or identify with the feelings and needs of others?",
            simple_text="Do you have trouble understanding or caring about other people's feelings and needs?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="empathy_deficits",
            help_text="This involves difficulty understanding and responding to others' emotions",
            examples=[
                "Not noticing when others are upset",
                "Not caring about others' problems",
                "Being impatient with others' emotional needs",
                "Difficulty putting yourself in others' shoes"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_07A",
            text="How do you typically respond when others are upset or in need?",
            simple_text="When someone you know is having problems or feeling bad, what do you usually do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel their pain and want to help immediately",
                "I try to understand and offer support",
                "I listen but focus on practical solutions",
                "I acknowledge it but don't get too involved",
                "I find it hard to know what to say or do",
                "I get impatient with their emotional needs",
                "I change the subject or avoid the situation",
                "I don't see why they can't just handle it themselves"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="empathic_responses",
            help_text="Think about your typical reactions to others' distress"
        ),
        
        # Criterion 8: Often envious of others or believes others are envious of them
        SCIDPDQuestion(
            id="NPD_08",
            text="Are you often envious of others or believe that others are envious of you?",
            simple_text="Do you often feel jealous of other people's success, or do you think other people are jealous of you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="envy_patterns",
            requires_examples=True,
            help_text="This includes both feeling envious and believing others envy you",
            examples=[
                "Feeling resentful of others' success",
                "Believing others are jealous of your achievements",
                "Getting upset when others get recognition",
                "Assuming others' negative reactions are due to envy"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_08A",
            text="How do you typically feel when others achieve success or recognition?",
            simple_text="When other people get praise, promotions, or good things happening to them, how do you feel?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel genuinely happy for them",
                "I feel pleased if I care about the person",
                "I feel neutral - it doesn't affect me much",
                "I feel a bit envious but try to be supportive",
                "I feel jealous and find it hard to be happy for them",
                "I feel they don't deserve it as much as I would",
                "I assume they got lucky or had unfair advantages",
                "I believe they're trying to show me up or compete with me"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="success_reactions",
            help_text="Be honest about your initial emotional reactions"
        ),
        
        SCIDPDQuestion(
            id="NPD_08B",
            text="Do you believe others are envious of you?",
            simple_text="Do you think other people are jealous of your life, achievements, or qualities?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't think others envy me",
                "Maybe some people are envious occasionally",
                "I think some people are envious of certain things about me",
                "I believe many people are envious of my success/qualities",
                "I think most people wish they had my life",
                "I assume negative reactions from others are due to envy",
                "I believe envy explains most criticism I receive"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="perceived_envy",
            help_text="Consider how you interpret others' reactions to you"
        ),
        
        # Criterion 9: Shows arrogant behaviors or attitudes
        SCIDPDQuestion(
            id="NPD_09",
            text="Do you show arrogant, haughty behaviors or attitudes?",
            simple_text="Do you act in ways that might seem arrogant, snobbish, or like you think you're better than others?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="arrogant_behaviors",
            requires_examples=True,
            help_text="This includes condescending or superior attitudes toward others",
            examples=[
                "Looking down on people you consider inferior",
                "Acting condescending in conversations",
                "Showing off or bragging frequently",
                "Dismissing others' opinions as unimportant"
            ]
        ),
        
        SCIDPDQuestion(
            id="NPD_09A",
            text="How do others typically respond to your behavior in social situations?",
            simple_text="What kind of reactions do you usually get from people when you interact with them?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "People generally seem comfortable and engaged",
                "Most people respond positively to me",
                "People seem to admire or look up to me",
                "Some people seem intimidated by my confidence",
                "People sometimes seem put off or annoyed",
                "Some people have called me arrogant or conceited",
                "People often seem to avoid me or cut conversations short",
                "Others have said I come across as thinking I'm better than them"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="social_feedback",
            help_text="Think about the feedback you've received, both direct and indirect"
        ),
        
        # Timeline and Onset Questions
        SCIDPDQuestion(
            id="NPD_10",
            text="When did you first notice these patterns of grandiosity and need for admiration?",
            simple_text="When did you first start feeling this special or superior, or needing lots of admiration from others?",
            response_type=ResponseType.ONSET_AGE,
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="onset_timing",
            onset_relevant=True,
            help_text="These patterns typically begin by early adulthood"
        ),
        
        SCIDPDQuestion(
            id="NPD_10A",
            text="What contributed to your sense of being special or superior?",
            simple_text="What experiences or factors do you think led to your feeling special or different from others?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I've always felt this way naturally",
                "Exceptional achievements or talents in childhood",
                "Being told I was special or gifted by parents/teachers",
                "Coming from a privileged or high-status family",
                "Early success that made me stand out",
                "Being treated differently due to appearance or abilities",
                "Overcoming significant challenges or trauma",
                "Religious or spiritual experiences",
                "I'm not sure what contributed to these feelings"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="grandiosity_origins",
            help_text="Select factors that may have contributed to your self-image"
        ),
        
        # Pervasiveness across contexts
        SCIDPDQuestion(
            id="NPD_11",
            text="Do these patterns of grandiosity and need for admiration occur across different areas of your life?",
            simple_text="Do you feel and act this way at work, with family, with friends, and in romantic relationships?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Only in certain specific situations",
                "Mainly at work or in professional settings",
                "Mainly in romantic relationships",
                "With most people but not family",
                "In most of my relationships and situations",
                "In all areas of my life consistently",
                "It varies depending on whether people appreciate me"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="pervasiveness",
            pervasiveness_check=True,
            help_text="Personality patterns typically occur across multiple contexts"
        ),
        
        # Functional impairment
        SCIDPDQuestion(
            id="NPD_12",
            text="How much do these patterns of grandiosity and interpersonal difficulties affect your daily functioning?",
            simple_text="How much do these attitudes and behaviors interfere with your work, relationships, or daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "A little", "Moderately", "Quite a bit", "Extremely"],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="functional_impairment",
            help_text="Consider impact on relationships, work performance, and life satisfaction"
        ),
        
        SCIDPDQuestion(
            id="NPD_12A",
            text="Which areas of your life are most affected by these patterns?",
            simple_text="What parts of your life have problems because of these attitudes and behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work relationships and career advancement",
                "Romantic relationships and intimacy",
                "Friendships and social connections",
                "Family relationships",
                "Parenting relationships (if applicable)",
                "Financial decisions and stability",
                "Legal or ethical issues",
                "Overall life satisfaction",
                "Mental health and self-esteem",
                "No significant impairment"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impairment_areas",
            help_text="Select all areas significantly affected"
        ),
        
        # Stability of patterns
        SCIDPDQuestion(
            id="NPD_13",
            text="Have these patterns of grandiosity and interpersonal behavior been consistent throughout your adult life?",
            simple_text="Have you felt and acted this way consistently since becoming an adult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, these feelings are relatively recent",
                "They've developed over the past few years",
                "They've been consistent since my early twenties",
                "They've been present as long as I can remember",
                "They've gotten stronger over time",
                "They vary with my life circumstances",
                "They've gotten somewhat better with age",
                "They fluctuate but always return"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="pattern_stability",
            help_text="Personality disorders involve stable, long-term patterns"
        ),
        
        # Self-awareness and insight
        SCIDPDQuestion(
            id="NPD_14",
            text="How do you view your need for admiration and sense of superiority?",
            simple_text="Do you see your confidence and need for recognition as a problem, or as natural given your qualities?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't see myself as needing excessive admiration",
                "My confidence is justified by my actual abilities",
                "I deserve the recognition I seek",
                "Others just don't appreciate excellence when they see it",
                "Maybe I need validation more than most people",
                "I sometimes worry I'm too focused on what others think",
                "I recognize this causes problems in my relationships",
                "I wish I didn't need so much validation from others"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="self_awareness",
            help_text="Consider your level of insight into these patterns"
        ),
        
        # Current coping and treatment
        SCIDPDQuestion(
            id="NPD_15",
            text="What strategies do you use when you don't receive the recognition or treatment you expect?",
            simple_text="What do you do when people don't give you the respect, praise, or treatment you think you deserve?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I try to understand their perspective",
                "I work harder to prove my worth",
                "I find others who appreciate me more",
                "I get angry and express my displeasure",
                "I withdraw and feel hurt or depressed",
                "I convince myself they're jealous or inferior",
                "I retaliate or try to show them up",
                "I question whether I'm expecting too much"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="coping_strategies",
            help_text="Select strategies you commonly use"
        )
    ]
    
    return SCIDPDModule(
        id="NPD",
        name="Narcissistic Personality Disorder",
        description="Assessment of narcissistic personality disorder according to DSM-5 criteria. Evaluates grandiosity, need for admiration, lack of empathy, and interpersonal exploitation patterns.",
        dsm_cluster=DSMCluster.CLUSTER_B,
        questions=questions,
        diagnostic_threshold=0.65,
        dimensional_threshold=60.0,
        estimated_time_mins=30,
        dsm_criteria=[
            "Grandiose sense of self-importance",
            "Preoccupied with fantasies of unlimited success, power, brilliance, beauty, or ideal love",
            "Believes they are 'special' and unique",
            "Requires excessive admiration",
            "Has a sense of entitlement",
            "Is interpersonally exploitative",
            "Lacks empathy",
            "Is often envious of others or believes others are envious of them",
            "Shows arrogant, haughty behaviors or attitudes"
        ],
        severity_thresholds={
            "mild": 0.5,
            "moderate": 0.65,
            "severe": 0.8,
            "extreme": 0.9
        },
        core_features=[
            "Grandiose self-image",
            "Need for excessive admiration",
            "Lack of empathy",
            "Sense of entitlement",
            "Interpersonal exploitation"
        ],
        differential_diagnoses=[
            "Borderline Personality Disorder",
            "Histrionic Personality Disorder",
            "Antisocial Personality Disorder",
            "Bipolar Disorder (Manic Episodes)",
            "Substance Use Disorders",
            "Normal self-confidence and ambition"
        ],
        minimum_criteria_count=5,
        requires_onset_before_18=True,
        version="1.0",
        clinical_notes="Requires at least 5 of 9 criteria. Pattern must be pervasive across contexts and stable over time. Often presents with fragile self-esteem underneath grandiose exterior. May have difficulty maintaining long-term relationships due to empathy deficits."
    )
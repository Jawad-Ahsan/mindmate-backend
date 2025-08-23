# scid_pd/modules/dependent_pd.py
"""
SCID-PD Module: Dependent Personality Disorder (DPD)
Assessment of dependent personality disorder according to DSM-5 criteria
"""

from ..base_types import (
    SCIDPDModule, SCIDPDQuestion, ResponseType, DSMCluster, 
    PersonalityDimensionType
)

def create_dependent_pd_module() -> SCIDPDModule:
    """Create the Dependent Personality Disorder SCID-PD module"""
    
    questions = [
        # Criterion 1: Difficulty making everyday decisions
        SCIDPDQuestion(
            id="DPD_01",
            text="Do you have difficulty making everyday decisions without an excessive amount of advice and reassurance from others?",
            simple_text="Do you have trouble making daily decisions without getting a lot of advice and reassurance from other people?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="decision_making_difficulty",
            requires_examples=True,
            help_text="This includes difficulty with both major and minor life decisions",
            examples=[
                "Needing others to help decide what to wear",
                "Getting multiple opinions before making purchases",
                "Asking for advice about routine daily choices",
                "Feeling paralyzed without others' input"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_01A",
            text="What kinds of decisions do you have trouble making without others' help?",
            simple_text="What types of decisions do you need help from others to make?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "What to wear or how to look",
                "What to eat or where to eat",
                "How to spend my free time",
                "Financial decisions and purchases",
                "Work or career choices",
                "Medical decisions and health choices",
                "Social decisions and relationships",
                "Major life changes like moving or jobs",
                "Almost all decisions, even very small ones"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="decision_types",
            help_text="Select all types of decisions you struggle with"
        ),
        
        # Criterion 2: Needs others to assume responsibility
        SCIDPDQuestion(
            id="DPD_02",
            text="Do you need others to assume responsibility for most major areas of your life?",
            simple_text="Do you rely on other people to take care of the major parts of your life for you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="responsibility_avoidance",
            requires_examples=True,
            help_text="This means letting others handle important life areas rather than managing them yourself",
            examples=[
                "Having others manage your finances",
                "Letting others make major decisions for you",
                "Having someone else handle your career planning",
                "Relying on others to manage your daily schedule"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_02A",
            text="Which major life areas do others handle for you?",
            simple_text="What important parts of your life do other people take care of for you?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Financial management and bills",
                "Career decisions and job searching",
                "Health and medical care coordination",
                "Social planning and relationships",
                "Household management and organization",
                "Legal matters and important paperwork",
                "Major purchases and life decisions",
                "Daily scheduling and time management",
                "Most aspects of adult responsibility"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="responsibility_areas",
            help_text="Select all areas where others take primary responsibility"
        ),
        
        # Criterion 3: Difficulty expressing disagreement
        SCIDPDQuestion(
            id="DPD_03",
            text="Do you have difficulty expressing disagreement with others because you fear losing support or approval?",
            simple_text="Is it hard for you to disagree with people because you're afraid they'll stop liking or helping you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="disagreement_difficulty",
            requires_examples=True,
            help_text="This includes avoiding conflict even when you have different opinions",
            examples=[
                "Going along with plans you don't like",
                "Pretending to agree when you don't",
                "Avoiding expressing your real opinions",
                "Saying yes when you want to say no"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_03A",
            text="What do you typically do when you disagree with someone important to you?",
            simple_text="What do you usually do when you disagree with someone you depend on?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I express my disagreement openly and honestly",
                "I hint at my disagreement but don't state it directly",
                "I go along with them even though I disagree",
                "I ask questions to try to understand their view better",
                "I change my opinion to match theirs",
                "I avoid the topic entirely",
                "I agree outwardly but feel resentful inside",
                "I get someone else to express the disagreement for me",
                "I become upset but don't explain why"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="disagreement_responses",
            help_text="Think about your typical pattern with people you depend on"
        ),
        
        # Criterion 4: Difficulty initiating projects
        SCIDPDQuestion(
            id="DPD_04",
            text="Do you have difficulty initiating projects or doing things on your own because you lack confidence in your judgment or abilities?",
            simple_text="Is it hard for you to start projects or do things by yourself because you don't trust your own judgment or abilities?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="initiative_difficulty",
            requires_examples=True,
            help_text="This includes both work projects and personal activities",
            examples=[
                "Needing others to get projects started",
                "Waiting for permission or encouragement to begin tasks",
                "Doubting your ability to handle things independently",
                "Avoiding taking on new responsibilities"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_04A",
            text="What holds you back from starting projects or doing things independently?",
            simple_text="What stops you from starting things on your own?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't trust my own judgment about how to do things",
                "I'm afraid I'll make mistakes or do it wrong",
                "I don't think I have the skills or abilities needed",
                "I need someone else's approval before starting",
                "I worry about taking responsibility if something goes wrong",
                "I prefer when others take the lead",
                "I don't know where to begin without guidance",
                "I'm afraid others will criticize my efforts",
                "I feel more comfortable when someone else is in charge"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="initiative_barriers",
            help_text="Select all factors that prevent you from taking initiative"
        ),
        
        # Criterion 5: Goes to excessive lengths to obtain support
        SCIDPDQuestion(
            id="DPD_05",
            text="Do you go to excessive lengths to obtain nurturance and support from others, to the point of volunteering to do things that are unpleasant?",
            simple_text="Do you do unpleasant or difficult things for people just to get their care and support?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="excessive_support_seeking",
            requires_examples=True,
            help_text="This includes doing things you don't want to do just to maintain relationships",
            examples=[
                "Volunteering for tasks you hate to please others",
                "Doing favors you can't afford (time/money) to keep people happy",
                "Accepting mistreatment to maintain a relationship",
                "Going way beyond what's reasonable to help others"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_05A",
            text="What kinds of things have you done to maintain others' support?",
            simple_text="What unpleasant or difficult things have you done just to keep people's care and support?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Volunteered for tasks I hate or find very difficult",
                "Lent money I couldn't afford to lose",
                "Did extensive favors that took up all my free time",
                "Tolerated disrespectful or hurtful treatment",
                "Sacrificed my own needs completely for others",
                "Took on responsibilities that overwhelmed me",
                "Agreed to things that went against my values",
                "Put others' needs before urgent needs of my own",
                "Stayed in harmful situations to avoid losing support"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="support_seeking_behaviors",
            help_text="Select all behaviors you've engaged in to maintain relationships"
        ),
        
        # Criterion 6: Feels uncomfortable or helpless when alone
        SCIDPDQuestion(
            id="DPD_06",
            text="Do you feel uncomfortable or helpless when alone because of exaggerated fears of being unable to care for yourself?",
            simple_text="Do you feel very uncomfortable or helpless when you're alone because you're afraid you can't take care of yourself?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="alone_discomfort",
            requires_examples=True,
            help_text="This refers to fear about your ability to function independently",
            examples=[
                "Feeling panicked when left alone for extended periods",
                "Worrying you can't handle basic tasks without help",
                "Feeling lost or confused about what to do when alone",
                "Needing constant contact with others for reassurance"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_06A",
            text="What specifically worries you about being alone?",
            simple_text="What are you most afraid of when you have to be by yourself?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I won't know what to do with my time",
                "I can't handle emergencies or problems that come up",
                "I'll make bad decisions without someone to guide me",
                "I'll feel too lonely or depressed",
                "I won't be able to take care of basic needs",
                "Something bad will happen and no one will help me",
                "I'll fall apart emotionally without support",
                "I won't be motivated to do anything productive",
                "I feel like I don't exist without others around"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="alone_fears",
            help_text="Select all fears you have about being alone"
        ),
        
        # Criterion 7: Urgently seeks new relationships
        SCIDPDQuestion(
            id="DPD_07",
            text="When a close relationship ends, do you urgently seek another relationship as a source of care and support?",
            simple_text="When an important relationship ends, do you quickly look for someone else to take care of you and support you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="relationship_replacement",
            requires_examples=True,
            help_text="This includes romantic relationships, friendships, or other supportive relationships",
            examples=[
                "Immediately dating someone new after a breakup",
                "Quickly forming intense friendships after losing a friend",
                "Seeking new mentors or parental figures when others leave",
                "Feeling desperate to replace the lost support"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_07A",
            text="How quickly do you typically seek new relationships after losing important ones?",
            simple_text="How soon after losing an important relationship do you look for a replacement?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't usually seek immediate replacements",
                "Within a few weeks",
                "Within a few days", 
                "Almost immediately",
                "I start looking before the relationship has even ended",
                "I always maintain backup relationships in case one ends",
                "I become desperate and will accept almost anyone",
                "I can't function until I find someone new"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="replacement_urgency",
            help_text="Think about your typical pattern when relationships end"
        ),
        
        # Criterion 8: Preoccupied with fears of being left alone
        SCIDPDQuestion(
            id="DPD_08",
            text="Are you unrealistically preoccupied with fears of being left to take care of yourself?",
            simple_text="Do you spend a lot of time worrying about having to take care of yourself if others leave you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="abandonment_preoccupation",
            requires_examples=True,
            help_text="This includes excessive worry about future independence",
            examples=[
                "Constantly worrying about what would happen if your partner left",
                "Imagining worst-case scenarios about being alone",
                "Planning your life around never being without support",
                "Feeling panicked at thoughts of independence"
            ]
        ),
        
        SCIDPDQuestion(
            id="DPD_08A",
            text="How much time do you spend worrying about being left to care for yourself?",
            simple_text="How often do you worry about having to take care of yourself?",
            response_type=ResponseType.FREQUENCY,
            options=[
                "rarely",
                "sometimes",
                "often", 
                "most days",
                "almost constantly",
                "it's always on my mind"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="worry_frequency",
            help_text="Consider your typical daily experience"
        ),
        
        # Timeline and Onset Questions
        SCIDPDQuestion(
            id="DPD_09",
            text="When did you first notice these patterns of needing others to take care of you?",
            simple_text="When did you first start relying heavily on others to take care of you and make decisions?",
            response_type=ResponseType.ONSET_AGE,
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="onset_timing",
            onset_relevant=True,
            help_text="Dependent patterns often begin in childhood or early adulthood"
        ),
        
        SCIDPDQuestion(
            id="DPD_09A",
            text="What do you think contributed to developing these dependent patterns?",
            simple_text="What experiences do you think made you become so dependent on others?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Overprotective parents who did everything for me",
                "Being discouraged from being independent as a child",
                "Having my decisions criticized or corrected frequently",
                "Being told I was incapable or couldn't handle things",
                "Experiencing trauma that made me feel helpless",
                "Having anxiety that made independence feel overwhelming",
                "Being rewarded for being dependent and compliant",
                "Never being taught how to be independent",
                "Cultural or family expectations about dependence"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="developmental_factors",
            help_text="Select all factors that may have contributed"
        ),
        
        # Current relationship patterns
        SCIDPDQuestion(
            id="DPD_10",
            text="Who do you currently depend on most for support and decision-making?",
            simple_text="Who is the main person you rely on to help you with decisions and support?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Romantic partner or spouse",
                "Parent or family member",
                "Close friend",
                "Multiple people for different areas",
                "Therapist or counselor",
                "Boss or supervisor",
                "I don't currently have anyone to depend on",
                "Anyone who will help me"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="dependency_targets",
            help_text="Think about who you turn to most often"
        ),
        
        SCIDPDQuestion(
            id="DPD_11",
            text="How do you feel when the people you depend on are unavailable?",
            simple_text="What happens to you emotionally when the people you rely on aren't available to help?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel fine and can manage on my own",
                "I feel a little anxious but can cope",
                "I feel moderately anxious and uncomfortable",
                "I feel very anxious and panicked",
                "I feel helpless and unable to function",
                "I feel angry that they're not available for me",
                "I immediately look for someone else to help",
                "I feel lost and don't know what to do"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="unavailability_response",
            help_text="Think about your emotional response"
        ),
        
        # Functional impairment assessment
        SCIDPDQuestion(
            id="DPD_12",
            text="How much do these dependent patterns interfere with your life?",
            simple_text="How much do your patterns of depending on others interfere with your daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "A little", "Moderately", "Quite a bit", "Extremely"],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="functional_impairment",
            help_text="Consider impact on independence, relationships, and personal growth"
        ),
        
        SCIDPDQuestion(
            id="DPD_12A",
            text="Which areas of your life are most affected by dependency patterns?",
            simple_text="What parts of your life suffer most because of depending on others?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Career advancement and professional growth",
                "Financial independence and management",
                "Personal relationships and social life",
                "Self-confidence and self-esteem",
                "Decision-making abilities",
                "Living independently",
                "Personal interests and hobbies",
                "Overall life satisfaction",
                "Ability to handle crises or emergencies"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impairment_areas",
            help_text="Select all significantly affected areas"
        ),
        
        # Pervasiveness assessment
        SCIDPDQuestion(
            id="DPD_13",
            text="Do these dependent patterns occur across different types of relationships?",
            simple_text="Do you depend on people in the same ways whether they're romantic partners, family, friends, or coworkers?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Only in romantic relationships",
                "Only with family members",
                "Only with certain types of people",
                "In most of my close relationships",
                "In all my relationships regardless of type",
                "At work and in personal relationships",
                "With anyone who will let me depend on them"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="pervasiveness",
            pervasiveness_check=True,
            help_text="Personality patterns typically occur across multiple relationship types"
        ),
        
        # Stability over time
        SCIDPDQuestion(
            id="DPD_14",
            text="Have these dependent patterns been consistent throughout your adult life?",
            simple_text="Have you consistently depended on others in these ways since you became an adult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, this is a recent change (less than 2 years)",
                "These patterns developed in the last 2-5 years", 
                "These patterns have been present for 5+ years",
                "I've been this way since my teenage years",
                "I've been this way as long as I can remember",
                "The patterns come and go depending on my relationships",
                "They've gotten worse over time",
                "They've gotten somewhat better but are still present"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="pattern_stability",
            help_text="Personality disorders involve stable, enduring patterns"
        ),
        
        # Distinction from normal interdependence
        SCIDPDQuestion(
            id="DPD_15",
            text="Do you think your level of dependence on others goes beyond what most people would consider normal?",
            simple_text="Do you think you depend on others more than most people do?",
            response_type=ResponseType.YES_NO,
            criteria_weight=0.5,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="dependence_awareness",
            help_text="This assesses insight into the excessive nature of the dependence"
        ),
        
        # Current coping and treatment
        SCIDPDQuestion(
            id="DPD_16",
            text="What do you do when you need to make decisions or handle things independently?",
            simple_text="What strategies do you use when you have to make decisions or do things on your own?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel paralyzed and can't function until someone helps",
                "I call or text multiple people for advice",
                "I delay the decision as long as possible",
                "I guess and hope for the best",
                "I try to imagine what someone I trust would do",
                "I use decision-making skills I've learned",
                "I push through my anxiety and do my best",
                "I find ways to avoid having to decide",
                "I make the decision but constantly second-guess myself"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="independence_coping",
            help_text="Select all strategies you use when forced to be independent"
        ),
        
        SCIDPDQuestion(
            id="DPD_17",
            text="Have you ever received treatment or tried to work on becoming more independent?",
            simple_text="Have you ever gotten help or tried to become more independent and self-reliant?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I haven't sought help for this",
                "I've considered it but haven't taken action",
                "I'm currently in therapy working on independence",
                "I've tried therapy but found it too difficult",
                "I've read self-help materials about independence",
                "I've worked on it with support from family/friends",
                "I don't think I need to become more independent",
                "I want to but I'm afraid of losing relationships"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="treatment_history",
            help_text="This helps understand motivation and treatment experience"
        )
    ]
    
    return SCIDPDModule(
        id="DPD",
        name="Dependent Personality Disorder",
        description="Assessment of dependent personality disorder according to DSM-5 criteria. Evaluates excessive need to be taken care of, submissive and clinging behavior, and fears of separation.",
        dsm_cluster=DSMCluster.CLUSTER_C,
        questions=questions,
        diagnostic_threshold=0.6,
        dimensional_threshold=55.0,
        estimated_time_mins=28,
        dsm_criteria=[
            "Difficulty making everyday decisions without excessive advice and reassurance",
            "Needs others to assume responsibility for most major areas of life",
            "Difficulty expressing disagreement due to fear of loss of support or approval",
            "Difficulty initiating projects or doing things independently due to lack of self-confidence",
            "Goes to excessive lengths to obtain nurturance and support, including volunteering for unpleasant tasks",
            "Feels uncomfortable or helpless when alone due to exaggerated fears of inability to care for self",
            "Urgently seeks another relationship as source of care and support when close relationship ends",
            "Unrealistically preoccupied with fears of being left to take care of self"
        ],
        severity_thresholds={
            "mild": 0.45,
            "moderate": 0.6,
            "severe": 0.75,
            "extreme": 0.9
        },
        core_features=[
            "Excessive need to be taken care of",
            "Submissive and clinging behavior",
            "Fears of separation and abandonment",
            "Difficulty with independent functioning",
            "Lack of self-confidence"
        ],
        differential_diagnoses=[
            "Agoraphobia",
            "Borderline Personality Disorder",
            "Histrionic Personality Disorder",
            "Avoidant Personality Disorder",
            "Major Depressive Disorder",
            "Panic Disorder",
            "Medical conditions causing dependency"
        ],
        minimum_criteria_count=5,
        requires_onset_before_18=True,
        version="1.0",
        clinical_notes="Requires at least 5 of 8 criteria. Pattern must be pervasive across contexts and stable over time. Distinguish from normal interdependence by the excessive and dysfunctional nature. Often develops in overprotective family environments. May have cultural considerations."
    )
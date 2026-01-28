# scid_pd/modules/avoidant_pd.py
"""
SCID-PD Module: Avoidant Personality Disorder (AVPD)
Assessment of avoidant personality disorder according to DSM-5 criteria
"""

from ..base_types import (
    SCIDPDModule, SCIDPDQuestion, ResponseType, DSMCluster, 
    PersonalityDimensionType
)

def create_avoidant_pd_module() -> SCIDPDModule:
    """Create the Avoidant Personality Disorder SCID-PD module"""
    
    questions = [
        # Criterion 1: Avoids occupational activities due to fear of criticism
        SCIDPDQuestion(
            id="AVPD_01",
            text="Do you avoid work activities or jobs that involve a lot of contact with people because you're afraid of being criticized, disapproved of, or rejected?",
            simple_text="Do you avoid jobs or work situations where you have to deal with people because you're afraid they'll criticize or reject you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="occupational_avoidance",
            requires_examples=True,
            help_text="This includes avoiding promotions, presentations, or leadership roles due to fear of criticism",
            examples=[
                "Turning down promotions that require more social interaction",
                "Avoiding presentations or speaking in meetings",
                "Choosing jobs with minimal human contact",
                "Declining leadership opportunities"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_01A",
            text="What work or career situations do you tend to avoid?",
            simple_text="Which work situations do you avoid because of fear of criticism or rejection?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Presentations or public speaking",
                "Leadership roles or supervising others",
                "Jobs requiring frequent customer contact",
                "Team meetings or group discussions",
                "Networking events or professional gatherings",
                "Performance reviews or evaluations",
                "Training new employees",
                "Jobs that require selling or persuading",
                "Any role where I might be judged"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="work_avoidance_behaviors",
            help_text="Select all that apply to your work experience"
        ),
        
        # Criterion 2: Unwilling to get involved unless certain of being liked
        SCIDPDQuestion(
            id="AVPD_02",
            text="Are you unwilling to get involved with people unless you're certain they will like you?",
            simple_text="Do you avoid getting involved with people unless you're sure they'll like you and accept you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="relationship_avoidance",
            requires_examples=True,
            help_text="This means needing strong guarantees of acceptance before engaging socially",
            examples=[
                "Waiting for clear signs someone likes you before approaching",
                "Only socializing with people who have already shown interest",
                "Avoiding new social situations without a 'safe' person present",
                "Needing repeated reassurance before engaging"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_02A",
            text="How do you determine if it's 'safe' to get involved with someone?",
            simple_text="What signs do you look for to know that someone will accept you before you get close to them?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "They have to approach me first and show clear interest",
                "I need repeated reassurance that they like me",
                "I wait to see how they treat other people",
                "I need a mutual friend to vouch for them",
                "They have to prove they won't judge or criticize me",
                "I look for people who seem 'safe' and non-threatening",
                "I avoid anyone who seems confident or intimidating",
                "I need to know they have problems too so they won't judge mine"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="acceptance_criteria",
            help_text="Select all strategies you use to assess social safety"
        ),
        
        # Criterion 3: Shows restraint in intimate relationships
        SCIDPDQuestion(
            id="AVPD_03",
            text="Do you show restraint within intimate relationships because of fear of being shamed or ridiculed?",
            simple_text="Even in close relationships, do you hold back or hide parts of yourself because you're afraid of being embarrassed or made fun of?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="intimacy_restraint",
            requires_examples=True,
            help_text="This includes not sharing feelings, thoughts, or aspects of yourself even with close people",
            examples=[
                "Not sharing personal thoughts even with close friends",
                "Hiding emotions or vulnerabilities from partners",
                "Avoiding physical intimacy due to body shame",
                "Not expressing needs or desires in relationships"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_03A",
            text="What do you tend to hold back in close relationships?",
            simple_text="What parts of yourself do you hide even from people you're close to?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "My true feelings and emotions",
                "Personal problems or struggles", 
                "My opinions on important topics",
                "Physical affection or intimacy",
                "My needs and what I want from them",
                "Embarrassing experiences or mistakes",
                "My insecurities and self-doubts",
                "Parts of my personality I think they won't like",
                "My past or family background"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="intimacy_barriers",
            help_text="Select all aspects you tend to keep hidden"
        ),
        
        # Criterion 4: Preoccupied with being criticized or rejected
        SCIDPDQuestion(
            id="AVPD_04",
            text="Are you preoccupied with being criticized or rejected in social situations?",
            simple_text="Do you spend a lot of time worrying about being criticized, rejected, or embarrassed when you're around other people?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="rejection_preoccupation",
            requires_examples=True,
            help_text="This means constantly thinking about potential criticism or rejection",
            examples=[
                "Constantly worrying about what others think of you",
                "Analyzing every interaction for signs of rejection",
                "Expecting criticism even in neutral situations",
                "Ruminating about potential embarrassing moments"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_04A",
            text="How much time do you spend thinking about potential criticism or rejection?",
            simple_text="How often do you worry about being criticized or rejected by others?",
            response_type=ResponseType.FREQUENCY,
            options=[
                "rarely",
                "sometimes", 
                "often",
                "most of the time",
                "almost constantly",
                "it's always on my mind"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="worry_frequency",
            help_text="Consider your typical daily experience"
        ),
        
        # Criterion 5: Inhibited in new interpersonal situations
        SCIDPDQuestion(
            id="AVPD_05",
            text="Are you inhibited in new interpersonal situations because you feel inadequate?",
            simple_text="In new social situations, do you become very quiet or withdrawn because you feel like you're not good enough?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="social_inhibition",
            requires_examples=True,
            help_text="This includes becoming quiet, withdrawn, or unable to participate normally",
            examples=[
                "Becoming very quiet in new groups",
                "Feeling frozen or unable to speak naturally",
                "Withdrawing to the background in social situations",
                "Feeling like you don't belong or fit in"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_05A",
            text="How do you typically act in new social situations?",
            simple_text="What do you usually do when you're in a new social situation with people you don't know well?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I act naturally and engage normally",
                "I become much quieter than usual",
                "I stay on the sidelines and observe",
                "I try to leave as soon as possible",
                "I freeze up and can't think of what to say",
                "I speak very little and give short answers",
                "I focus on one 'safe' person and stick close to them",
                "I make excuses to avoid participating",
                "I feel physically uncomfortable (sweating, shaking, etc.)"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="social_behaviors",
            help_text="Think about your typical response pattern"
        ),
        
        # Criterion 6: Views self as socially inept
        SCIDPDQuestion(
            id="AVPD_06",
            text="Do you view yourself as socially inept, personally unappealing, or inferior to others?",
            simple_text="Do you see yourself as awkward socially, unattractive as a person, or not as good as other people?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="negative_self_view",
            requires_examples=True,
            help_text="This includes persistent negative beliefs about your social abilities and personal worth",
            examples=[
                "Believing you're boring or have nothing interesting to say",
                "Thinking you're awkward or don't know how to act socially",
                "Feeling inferior to others in most ways",
                "Believing others are more attractive, smart, or successful"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_06A",
            text="Which negative beliefs about yourself are strongest?",
            simple_text="What negative things do you believe most strongly about yourself?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I'm socially awkward and don't know how to act around people",
                "I'm boring and have nothing interesting to contribute",
                "I'm not attractive or appealing to others",
                "I'm not as smart or capable as other people",
                "I'm fundamentally flawed or defective",
                "I'm weak or inadequate compared to others",
                "I don't deserve to be liked or accepted",
                "I'm too sensitive or emotional",
                "I'm a burden to others"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="self_criticism_areas",
            help_text="Select the beliefs that feel most true to you"
        ),
        
        # Criterion 7: Reluctant to take personal risks
        SCIDPDQuestion(
            id="AVPD_07",
            text="Are you unusually reluctant to take personal risks or engage in new activities because they may prove embarrassing?",
            simple_text="Do you avoid trying new things or taking risks because you might embarrass yourself or fail?",
            response_type=ResponseType.YES_NO,
            criteria_weight=1.0,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="risk_avoidance",
            requires_examples=True,
            help_text="This includes avoiding activities where you might look foolish or incompetent",
            examples=[
                "Avoiding learning new skills in front of others",
                "Not trying new hobbies or activities",
                "Refusing invitations to unfamiliar events",
                "Not expressing opinions in case you're wrong"
            ]
        ),
        
        SCIDPDQuestion(
            id="AVPD_07A",
            text="What kinds of activities or risks do you avoid?",
            simple_text="What types of things do you avoid doing because you might be embarrassed?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Learning new skills (sports, instruments, etc.)",
                "Trying new foods or restaurants",
                "Attending social events or parties",
                "Dating or romantic activities",
                "Creative pursuits where others might judge my work",
                "Physical activities where I might look uncoordinated",
                "Speaking up in groups or expressing opinions",
                "Traveling to new places",
                "Any activity where I might fail or look foolish"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="avoidance_areas",
            help_text="Select all types of activities you tend to avoid"
        ),
        
        # Timeline and Onset Questions
        SCIDPDQuestion(
            id="AVPD_08",
            text="When did you first notice these patterns of social anxiety and avoidance?",
            simple_text="When did you first start being very shy and avoiding social situations?",
            response_type=ResponseType.ONSET_AGE,
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="onset_timing",
            onset_relevant=True,
            help_text="Avoidant patterns often begin in childhood or adolescence"
        ),
        
        SCIDPDQuestion(
            id="AVPD_08A",
            text="What do you think contributed to developing these patterns?",
            simple_text="What experiences do you think made you become so shy and avoidant?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I've always been this way since I can remember",
                "Being bullied or teased at school",
                "Critical or rejecting parents/family",
                "Embarrassing experiences that made me more cautious",
                "Being compared negatively to others",
                "Social anxiety that got worse over time",
                "Trauma or abuse that made me withdraw",
                "Moving frequently or being the outsider",
                "Other people's reactions to my appearance or behavior"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="developmental_factors",
            help_text="Select all factors that may have contributed"
        ),
        
        # Severity and Impact Assessment
        SCIDPDQuestion(
            id="AVPD_09",
            text="How much do these patterns of avoidance interfere with your life?",
            simple_text="How much do your shyness and avoidance of social situations affect your daily life?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["Not at all", "A little", "Moderately", "Quite a bit", "Extremely"],
            required=True,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="functional_impairment",
            help_text="Consider impact on relationships, work, and personal satisfaction"
        ),
        
        SCIDPDQuestion(
            id="AVPD_09A",
            text="Which areas of your life are most affected by social avoidance?",
            simple_text="What parts of your life suffer most because of your shyness and avoidance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Romantic relationships and dating",
                "Friendships and social connections",
                "Work or career advancement",
                "Educational opportunities", 
                "Family relationships",
                "Personal interests and hobbies",
                "Self-esteem and confidence",
                "Overall life satisfaction",
                "Physical health (due to isolation stress)"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="impairment_areas",
            help_text="Select all significantly affected areas"
        ),
        
        # Social Isolation Assessment
        SCIDPDQuestion(
            id="AVPD_10",
            text="How many close friendships do you currently have?",
            simple_text="How many people would you consider close friends right now?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "None - I don't have any close friends",
                "One close friend",
                "2-3 close friends",
                "4-5 close friends",
                "More than 5 close friends"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="social_connections",
            help_text="Consider people you feel comfortable sharing personal things with"
        ),
        
        SCIDPDQuestion(
            id="AVPD_11",
            text="Do you often feel lonely or wish you had more social connections?",
            simple_text="Do you feel lonely and wish you had more friends or social relationships?",
            response_type=ResponseType.YES_NO,
            criteria_weight=0.5,
            dimension_type=PersonalityDimensionType.AFFECTIVE,
            trait_measured="loneliness",
            help_text="This assesses the emotional impact of social avoidance"
        ),
        
        # Differentiation from Social Anxiety Disorder
        SCIDPDQuestion(
            id="AVPD_12",
            text="Is your avoidance specifically about being judged or criticized, or do you also avoid social situations for other reasons?",
            simple_text="Do you avoid social situations mainly because you're afraid of being judged, or are there other reasons too?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Mainly fear of being judged or criticized",
                "I also feel like I don't know how to act socially",
                "I believe I'm fundamentally different or inferior to others",
                "I don't think I have anything valuable to contribute",
                "I feel like I don't deserve to be included",
                "Social situations are physically exhausting for me",
                "I prefer being alone most of the time",
                "I have trouble trusting that people really like me"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.COGNITIVE,
            trait_measured="avoidance_reasons",
            help_text="This helps distinguish from simple social anxiety"
        ),
        
        # Pervasiveness Assessment
        SCIDPDQuestion(
            id="AVPD_13",
            text="Do these avoidant patterns occur in most areas of your life?",
            simple_text="Do you have these same patterns of shyness and avoidance at work, with family, with potential friends, and in other situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Only in certain specific situations",
                "Mainly in work/professional settings",
                "Mainly in social/friendship situations", 
                "Mainly in romantic/dating situations",
                "In most social and work situations",
                "In virtually all interpersonal situations",
                "In every area of my life involving other people"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.INTERPERSONAL,
            trait_measured="pervasiveness",
            pervasiveness_check=True,
            help_text="Personality patterns are typically pervasive across contexts"
        ),
        
        # Stability over time
        SCIDPDQuestion(
            id="AVPD_14",
            text="Have these avoidant patterns been consistent throughout your adult life?",
            simple_text="Have you been consistently shy and avoidant since you became an adult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, this is a recent change (less than 2 years)",
                "These patterns developed in the last 2-5 years",
                "These patterns have been present for 5+ years",
                "I've been this way since my teenage years",
                "I've been this way as long as I can remember",
                "The patterns come and go depending on life circumstances",
                "They've gotten worse over time",
                "They've gotten somewhat better but are still present"
            ],
            required=True,
            dimension_type=PersonalityDimensionType.IDENTITY,
            trait_measured="pattern_stability",
            help_text="Personality disorders involve stable, enduring patterns"
        ),
        
        # Current coping and treatment
        SCIDPDQuestion(
            id="AVPD_15",
            text="What do you do to cope with social anxiety and the desire to avoid people?",
            simple_text="What strategies do you use to deal with social anxiety or to handle situations where you have to interact with people?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have effective strategies - I just suffer through it",
                "I avoid the situations entirely when possible",
                "I prepare extensively before social interactions",
                "I use alcohol or other substances to feel more comfortable",
                "I bring a trusted friend for support",
                "I use breathing techniques or relaxation methods",
                "I give myself pep talks or try to think positively",
                "I focus on being helpful so I don't have to talk about myself",
                "I use skills learned in therapy",
                "I take medication for anxiety"
            ],
            required=False,
            dimension_type=PersonalityDimensionType.BEHAVIORAL,
            trait_measured="coping_strategies",
            help_text="Select all strategies you use, both healthy and unhealthy"
        )
    ]
    
    return SCIDPDModule(
        id="AVPD",
        name="Avoidant Personality Disorder", 
        description="Assessment of avoidant personality disorder according to DSM-5 criteria. Evaluates social inhibition, feelings of inadequacy, and hypersensitivity to negative evaluation.",
        dsm_cluster=DSMCluster.CLUSTER_C,
        questions=questions,
        diagnostic_threshold=0.6,
        dimensional_threshold=55.0,
        estimated_time_mins=30,
        dsm_criteria=[
            "Avoids occupational activities due to fear of criticism, disapproval, or rejection",
            "Unwilling to get involved with people unless certain of being liked",
            "Shows restraint within intimate relationships because of fear of being shamed or ridiculed",
            "Preoccupied with being criticized or rejected in social situations", 
            "Inhibited in new interpersonal situations because of feelings of inadequacy",
            "Views self as socially inept, personally unappealing, or inferior to others",
            "Unusually reluctant to take personal risks or engage in new activities because they may prove embarrassing"
        ],
        severity_thresholds={
            "mild": 0.45,
            "moderate": 0.6, 
            "severe": 0.75,
            "extreme": 0.9
        },
        core_features=[
            "Social inhibition",
            "Feelings of inadequacy", 
            "Hypersensitivity to negative evaluation",
            "Avoidance of interpersonal situations",
            "Fear of criticism and rejection"
        ],
        differential_diagnoses=[
            "Social Anxiety Disorder",
            "Agoraphobia",
            "Schizoid Personality Disorder",
            "Paranoid Personality Disorder",
            "Major Depressive Disorder",
            "Autism Spectrum Disorder"
        ],
        minimum_criteria_count=4,
        requires_onset_before_18=True,
        version="1.0",
        clinical_notes="Requires at least 4 of 7 criteria. Pattern must be pervasive and stable. Distinguish from social anxiety disorder by presence of negative self-concept and broader avoidance. Often comorbid with depression and anxiety disorders."
    )
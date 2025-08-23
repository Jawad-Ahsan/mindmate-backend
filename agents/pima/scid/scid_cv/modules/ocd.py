# scid_cv/modules/ocd.py
"""
SCID-CV Module: Obsessive-Compulsive Disorder (OCD)
Assessment of obsessions and compulsions according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_ocd_module() -> SCIDModule:
    """Create the OCD SCID-CV module"""
    
    questions = [
        # Obsessions Screening
        SCIDQuestion(
            id="OCD_01",
            text="Do you have recurring, unwanted thoughts that come into your mind and cause you distress?",
            simple_text="Do you have unwanted thoughts that keep coming back into your mind and bother or upset you?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="obsessions",
            help_text="These are thoughts that you don't want to have but keep coming anyway",
            examples=["Worries about germs", "Doubts about safety", "Unwanted violent thoughts", "Need for order"]
        ),
        
        SCIDQuestion(
            id="OCD_02",
            text="What kinds of unwanted thoughts do you have?",
            simple_text="What kinds of unwanted thoughts keep bothering you? (Choose all that apply)",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Thoughts about contamination, germs, or dirt",
                "Doubts about safety (did I lock the door? turn off the stove?)",
                "Need for things to be in exact order or symmetrical",
                "Aggressive or violent thoughts that scare me",
                "Sexual thoughts that are unwanted or disturbing",
                "Religious or moral concerns (blasphemous thoughts, sins)",
                "Thoughts about harm coming to loved ones",
                "Thoughts about making mistakes or being responsible for disasters",
                "Other disturbing thoughts that keep coming back"
            ],
            symptom_category="obsession_content",
            help_text="Choose all types of unwanted thoughts you experience"
        ),
        
        SCIDQuestion(
            id="OCD_03",
            text="Do you try to ignore or suppress these thoughts, or try to neutralize them with other thoughts or actions?",
            simple_text="Do you try to push these unwanted thoughts away, ignore them, or do something to make them go away?",
            response_type=ResponseType.YES_NO,
            symptom_category="thought_resistance",
            help_text="Most people with OCD try to fight or neutralize their obsessive thoughts",
            examples=["Trying to think of something else", "Saying prayers to cancel out bad thoughts", "Doing rituals"]
        ),
        
        # Compulsions Screening
        SCIDQuestion(
            id="OCD_04",
            text="Do you feel compelled to repeat certain behaviors or mental acts over and over?",
            simple_text="Do you feel like you have to do certain things over and over again, even when you know it doesn't make sense?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="compulsions",
            help_text="These are behaviors or mental acts you feel driven to perform",
            examples=["Washing hands repeatedly", "Checking locks multiple times", "Counting", "Arranging things perfectly"]
        ),
        
        SCIDQuestion(
            id="OCD_05",
            text="What behaviors do you repeat over and over?",
            simple_text="What things do you feel you have to do over and over? (Choose all that apply)",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Washing hands or cleaning excessively",
                "Checking things (locks, appliances, doors, etc.)",
                "Counting or repeating numbers silently",
                "Arranging or organizing things in a specific way",
                "Asking for reassurance from others repeatedly",
                "Mental rituals (praying, repeating phrases in my head)",
                "Touching or tapping things a certain number of times",
                "Retracing steps or redoing actions until they feel 'right'",
                "Avoiding certain numbers, colors, or objects",
                "Other repetitive behaviors"
            ],
            symptom_category="compulsion_content",
            help_text="Choose all repetitive behaviors you feel compelled to do"
        ),
        
        SCIDQuestion(
            id="OCD_06",
            text="Do you perform these behaviors to prevent something bad from happening or to reduce distress?",
            simple_text="Do you do these repetitive behaviors to stop something bad from happening or to make yourself feel less anxious?",
            response_type=ResponseType.YES_NO,
            symptom_category="compulsion_purpose",
            help_text="Compulsions are aimed at preventing harm or reducing anxiety",
            examples=["Checking to prevent disasters", "Washing to prevent contamination", "Counting to prevent bad luck"]
        ),
        
        # Time and Interference
        SCIDQuestion(
            id="OCD_07",
            text="How much time do these thoughts and behaviors take up each day?",
            simple_text="How much time each day do you spend on these unwanted thoughts and repetitive behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 hour per day",
                "1 to 3 hours per day",
                "3 to 8 hours per day",
                "More than 8 hours per day",
                "Almost all of my waking time"
            ],
            symptom_category="time_consumed",
            help_text="OCD diagnosis requires at least 1 hour per day or significant interference"
        ),
        
        SCIDQuestion(
            id="OCD_08",
            text="Do these thoughts and behaviors significantly interfere with your daily life?",
            simple_text="Do these thoughts and behaviors significantly interfere with your work, relationships, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not at all", "A little bit", "Quite a bit", "Extremely"],
            symptom_category="functional_impairment",
            help_text="Consider interference even if you spend less than 1 hour on symptoms"
        ),
        
        SCIDQuestion(
            id="OCD_08A",
            text="Which areas of your life are most affected?",
            simple_text="Which parts of your life have been most affected by these thoughts and behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family or friends",
                "Daily routines and getting ready",
                "Household tasks and chores",
                "Social activities and going out",
                "Personal hygiene and self-care",
                "Sleep and rest",
                "Overall quality of life"
            ],
            required=False,
            symptom_category="impairment_areas",
            help_text="Choose all areas significantly affected"
        ),
        
        # Insight and Recognition
        SCIDQuestion(
            id="OCD_09",
            text="Do you recognize that these thoughts and behaviors are excessive or unreasonable?",
            simple_text="Do you know that these thoughts and behaviors are more than they should be or don't make complete sense?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I know they're excessive and don't make sense",
                "I know they're probably excessive but I'm not completely sure",
                "I'm not sure if they're excessive - they might be reasonable",
                "I don't think they're excessive - they seem necessary",
                "I'm completely convinced they're necessary and reasonable"
            ],
            symptom_category="insight_level",
            help_text="People with OCD have varying levels of insight into their symptoms"
        ),
        
        # Avoidance Behaviors
        SCIDQuestion(
            id="OCD_10",
            text="Do you avoid certain places, objects, or situations because of your obsessions or compulsions?",
            simple_text="Do you avoid certain places, things, or situations because they trigger your unwanted thoughts or make you feel like you have to do your repetitive behaviors?",
            response_type=ResponseType.YES_NO,
            symptom_category="avoidance_behavior",
            help_text="Avoidance is common in OCD to prevent triggering obsessions or compulsions"
        ),
        
        SCIDQuestion(
            id="OCD_10A",
            text="What do you avoid?",
            simple_text="What places, things, or situations do you avoid because of your OCD symptoms?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Public restrooms or dirty places",
                "Shaking hands or touching certain objects",
                "Certain numbers, words, or colors",
                "Places where I might cause harm (kitchens with knives, etc.)",
                "Religious places or objects",
                "Situations where I can't perform my rituals",
                "Places that are disorganized or messy",
                "Other specific triggers"
            ],
            required=False,
            symptom_category="avoided_triggers",
            help_text="Choose all things you avoid because of OCD"
        ),
        
        # Relationship with Others
        SCIDQuestion(
            id="OCD_11",
            text="Do you involve family members or others in your rituals or ask them for reassurance?",
            simple_text="Do you ask family members or friends to help with your repetitive behaviors or to reassure you about your worries?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't involve others in my OCD behaviors",
                "I ask others to check things for me",
                "I ask for reassurance about my worries repeatedly",
                "I ask others to help me avoid contamination",
                "I make others follow certain rules to help my anxiety",
                "I involve others in multiple ways"
            ],
            symptom_category="family_accommodation",
            help_text="Family members often get pulled into OCD rituals"
        ),
        
        # Onset and Duration
        SCIDQuestion(
            id="OCD_12",
            text="How long have you had these obsessive thoughts and compulsive behaviors?",
            simple_text="For about how long have you had these unwanted thoughts and repetitive behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 6 months",
                "6 months to 1 year",
                "1 to 2 years",
                "2 to 5 years",
                "5 to 10 years",
                "More than 10 years",
                "As long as I can remember"
            ],
            symptom_category="symptom_duration",
            help_text="OCD often starts in childhood or young adulthood"
        ),
        
        SCIDQuestion(
            id="OCD_13",
            text="When did these symptoms first start?",
            simple_text="Can you remember when these obsessive thoughts and compulsive behaviors first started?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "In early childhood (before age 10)",
                "In late childhood (ages 10-12)",
                "In adolescence (ages 13-18)",
                "In early adulthood (ages 19-25)",
                "In my twenties or thirties",
                "Later in adulthood",
                "I can't remember when they started"
            ],
            symptom_category="age_of_onset",
            help_text="Age of onset can be important for treatment planning"
        ),
        
        # Triggers and Worsening Factors
        SCIDQuestion(
            id="OCD_14",
            text="Are there things that make your obsessions and compulsions worse?",
            simple_text="Are there certain situations, feelings, or events that make your unwanted thoughts and repetitive behaviors worse?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Stress from work, school, or relationships",
                "Being tired or not sleeping well",
                "Major life changes or transitions",
                "Feeling sad or depressed",
                "Being around mess or disorder",
                "Having too much responsibility",
                "Certain times of day or situations",
                "Nothing specific makes them worse"
            ],
            required=False,
            symptom_category="worsening_factors",
            help_text="Identifying triggers can help with treatment planning"
        ),
        
        # Impact on Functioning
        SCIDQuestion(
            id="OCD_15",
            text="How do these symptoms affect your ability to work or go to school?",
            simple_text="How do your obsessive thoughts and compulsive behaviors affect your ability to work or attend school?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "They don't affect my work or school much",
                "I'm sometimes late or distracted because of them",
                "They significantly interfere with my performance",
                "I've missed work or school because of them",
                "I've had to change jobs or leave school because of them",
                "I'm unable to work or attend school because of them"
            ],
            symptom_category="occupational_impairment",
            help_text="OCD can significantly impact work and academic performance"
        ),
        
        SCIDQuestion(
            id="OCD_16",
            text="How do these symptoms affect your relationships?",
            simple_text="How do your obsessive thoughts and compulsive behaviors affect your relationships with family, friends, or romantic partners?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "They don't affect my relationships much",
                "Others sometimes get frustrated with my behaviors",
                "I hide my symptoms from others",
                "They cause tension or arguments in my relationships",
                "Others have to change their behavior to accommodate me",
                "They've seriously damaged important relationships"
            ],
            symptom_category="relationship_impairment",
            help_text="OCD often impacts close relationships"
        ),
        
        # Coping and Resistance
        SCIDQuestion(
            id="OCD_17",
            text="Do you try to resist or fight against these thoughts and behaviors?",
            simple_text="Do you try to resist having these thoughts or try to stop yourself from doing the repetitive behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I always try to resist them",
                "I usually try to resist them",
                "I sometimes try to resist them",
                "I rarely try to resist them",
                "I never try to resist them - I just go along with them"
            ],
            symptom_category="resistance_level",
            help_text="People with OCD often struggle between wanting to resist and feeling compelled"
        ),
        
        SCIDQuestion(
            id="OCD_18",
            text="What happens when you try to resist or delay these behaviors?",
            simple_text="When you try not to do your repetitive behaviors or ignore your unwanted thoughts, what happens?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I feel fine and the urge goes away",
                "I feel anxious but can manage it",
                "I feel very anxious and uncomfortable",
                "I feel extremely anxious and eventually give in",
                "I feel panic or terror until I do the behavior",
                "I can't resist - the urge is too strong"
            ],
            symptom_category="resistance_anxiety",
            help_text="This shows how strong the compulsions are"
        ),
        
        # Treatment History
        SCIDQuestion(
            id="OCD_19",
            text="Are you currently getting any treatment for OCD?",
            simple_text="Are you currently taking medication or getting any treatment for these obsessive thoughts and compulsive behaviors?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Taking medication for OCD",
                "In therapy that focuses on OCD (like CBT or ERP)",
                "In general therapy or counseling",
                "Both medication and specialized therapy",
                "Using self-help techniques",
                "Have tried treatment but not currently receiving any"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="Current treatment helps with coordination of care"
        ),
        
        # Severity Self-Assessment
        SCIDQuestion(
            id="OCD_20",
            text="Overall, how severe would you say your OCD symptoms are?",
            simple_text="Overall, how severe do you think your obsessive thoughts and compulsive behaviors are?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 4),
            scale_labels=["None", "Mild", "Moderate", "Severe", "Extreme"],
            symptom_category="severity_self_rating",
            help_text="Consider the time spent, distress caused, and interference with life"
        )
    ]
    
    return SCIDModule(
        id="OCD",
        name="Obsessive-Compulsive Disorder",
        description="Assessment of obsessions and compulsions according to DSM-5 criteria. Evaluates intrusive thoughts, repetitive behaviors, time consumption, and functional impairment.",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=20,
        dsm_criteria=[
            "Presence of obsessions, compulsions, or both",
            "Obsessions: recurrent, persistent thoughts/urges/images that are intrusive and unwanted",
            "Compulsions: repetitive behaviors or mental acts performed to prevent/reduce anxiety",
            "Time-consuming (>1 hour/day) or cause significant distress/impairment",
            "Not attributable to physiological effects of substances or medical conditions"
        ],
        severity_thresholds={
            "mild": 0.4,
            "moderate": 0.6,
            "severe": 0.8
        },
        category="obsessive_compulsive_disorders",
        version="1.0",
        clinical_notes="Requires presence of obsessions and/or compulsions that are time-consuming or cause significant distress/impairment. Assess insight level and degree of resistance."
    )
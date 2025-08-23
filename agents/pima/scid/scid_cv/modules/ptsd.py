# scid_cv/modules/ptsd.py
"""
SCID-CV Module: Post-Traumatic Stress Disorder (PTSD)
Assessment of trauma exposure and PTSD symptoms according to DSM-5 criteria
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_ptsd_module() -> SCIDModule:
    """Create the PTSD SCID-CV module"""
    
    questions = [
        # Trauma Exposure (Criterion A)
        SCIDQuestion(
            id="PTSD_01",
            text="Have you experienced or witnessed a very traumatic or life-threatening event?",
            simple_text="Have you been through or seen something very traumatic that involved death, serious injury, or sexual violence?",
            response_type=ResponseType.YES_NO,
            criteria_weight=2.0,
            symptom_category="trauma_exposure",
            help_text="This could be something that happened to you, someone close to you, or that you witnessed",
            examples=["Serious accident", "Physical or sexual assault", "Combat", "Natural disaster"]
        ),
        
        SCIDQuestion(
            id="PTSD_01A",
            text="What type of traumatic event was it?",
            simple_text="What kind of traumatic event was it? (You don't have to give details if you don't want to)",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Serious accident (car crash, workplace accident)",
                "Physical assault or attack",
                "Sexual assault or abuse",
                "Combat or war experience",
                "Terrorist attack or mass violence",
                "Natural disaster (earthquake, hurricane, fire)",
                "Life-threatening illness or medical emergency",
                "Sudden unexpected death of someone very close",
                "Witnessed violence or trauma happening to others",
                "Other traumatic event",
                "I prefer not to specify"
            ],
            required=False,
            symptom_category="trauma_type",
            help_text="Choose the option that best describes what happened"
        ),
        
        SCIDQuestion(
            id="PTSD_02",
            text="How did you experience this traumatic event?",
            simple_text="How were you involved in this traumatic event?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "It happened directly to me",
                "I witnessed it happening to someone else",
                "I learned it happened to a close family member or friend",
                "I was repeatedly exposed to details (like first responders, police)",
                "Multiple ways - it affected me in several ways"
            ],
            symptom_category="trauma_exposure_type",
            help_text="There are different ways people can be traumatized by events"
        ),
        
        # Intrusive Symptoms (Criterion B)
        SCIDQuestion(
            id="PTSD_03",
            text="Do you have repeated, unwanted memories of the traumatic event?",
            simple_text="Do you have unwanted memories or thoughts about the traumatic event that keep coming back?",
            response_type=ResponseType.YES_NO,
            symptom_category="intrusive_memories",
            help_text="These are memories that pop into your mind when you don't want them to",
            examples=["Sudden vivid memories", "Can't stop thinking about it", "Images that won't go away"]
        ),
        
        SCIDQuestion(
            id="PTSD_04",
            text="Do you have repeated, disturbing dreams or nightmares about the event?",
            simple_text="Do you have nightmares or disturbing dreams about the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="nightmares",
            help_text="Dreams that are clearly related to the traumatic event",
            examples=["Reliving the event in dreams", "Waking up scared", "Dreams with similar themes"]
        ),
        
        SCIDQuestion(
            id="PTSD_05",
            text="Do you ever feel like the traumatic event is happening again?",
            simple_text="Do you sometimes feel like the traumatic event is happening again, like you're back there? (flashbacks)",
            response_type=ResponseType.YES_NO,
            symptom_category="flashbacks",
            help_text="This is more intense than just remembering - you feel like you're actually there again",
            examples=["Feeling like you're back in the situation", "Acting as if it's happening now", "Losing awareness of present"]
        ),
        
        SCIDQuestion(
            id="PTSD_06",
            text="Do you become very upset when something reminds you of the event?",
            simple_text="Do you get very upset or distressed when something reminds you of the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="emotional_reactivity",
            help_text="Strong emotional reactions to reminders of the trauma",
            examples=["Sudden intense fear", "Breaking down crying", "Extreme anger or panic"]
        ),
        
        SCIDQuestion(
            id="PTSD_07",
            text="Do you have physical reactions when reminded of the event?",
            simple_text="When something reminds you of the traumatic event, do you have physical reactions like sweating, heart racing, or feeling sick?",
            response_type=ResponseType.YES_NO,
            symptom_category="physical_reactivity",
            help_text="Your body reacts as if you're in danger again",
            examples=["Heart pounding", "Sweating", "Feeling sick", "Muscle tension"]
        ),
        
        # Avoidance (Criterion C)
        SCIDQuestion(
            id="PTSD_08",
            text="Do you try to avoid thoughts, feelings, or conversations about the event?",
            simple_text="Do you try to avoid thinking about, talking about, or having feelings about the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="cognitive_avoidance",
            help_text="Trying to push away internal reminders of the trauma",
            examples=["Changing the subject", "Trying not to think about it", "Avoiding feelings"]
        ),
        
        SCIDQuestion(
            id="PTSD_09",
            text="Do you avoid places, people, or activities that remind you of the event?",
            simple_text="Do you avoid places, people, or activities that remind you of the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="behavioral_avoidance",
            help_text="Staying away from external reminders of the trauma",
            examples=["Avoiding certain locations", "Not seeing certain people", "Stopping activities you used to do"]
        ),
        
        # Negative Changes in Thoughts and Mood (Criterion D)
        SCIDQuestion(
            id="PTSD_10",
            text="Are you unable to remember important parts of the traumatic event?",
            simple_text="Are there important parts of the traumatic event that you can't remember?",
            response_type=ResponseType.YES_NO,
            symptom_category="memory_gaps",
            help_text="Memory problems not due to head injury or substances",
            examples=["Blank spots in memory", "Can't recall how it ended", "Missing chunks of time"]
        ),
        
        SCIDQuestion(
            id="PTSD_11",
            text="Do you have very negative thoughts about yourself, others, or the world?",
            simple_text="Do you have very negative thoughts like 'I am bad', 'The world is completely dangerous', or 'No one can be trusted'?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have these kinds of negative thoughts",
                "I blame myself for what happened or for not preventing it",
                "I think I'm permanently damaged or changed",
                "I believe the world is completely dangerous",
                "I think other people can't be trusted",
                "I believe bad things always happen to me",
                "I have several of these negative thoughts"
            ],
            symptom_category="negative_cognitions",
            help_text="Persistent negative beliefs that started or got worse after the trauma"
        ),
        
        SCIDQuestion(
            id="PTSD_12",
            text="Do you blame yourself or others for the traumatic event or its consequences?",
            simple_text="Do you blame yourself or other people for causing the traumatic event or for what happened afterward?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't blame anyone",
                "I blame myself for what happened",
                "I blame myself for not preventing it",
                "I blame myself for how I responded",
                "I blame other people who should have helped",
                "I blame multiple people including myself"
            ],
            symptom_category="blame_distortions",
            help_text="Unrealistic blame about the trauma or its consequences"
        ),
        
        SCIDQuestion(
            id="PTSD_13",
            text="Do you have persistent negative emotions like fear, horror, anger, guilt, or shame?",
            simple_text="Do you frequently feel very negative emotions like fear, anger, guilt, or shame since the traumatic event?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "My emotions are mostly normal",
                "I feel afraid or scared most of the time",
                "I feel angry or irritated constantly",
                "I feel guilty about what happened",
                "I feel ashamed or embarrassed",
                "I feel horror about what I experienced",
                "I feel several of these emotions regularly"
            ],
            symptom_category="persistent_negative_emotions",
            help_text="Negative emotions that are present most of the time"
        ),
        
        SCIDQuestion(
            id="PTSD_14",
            text="Have you lost interest in activities you used to enjoy?",
            simple_text="Have you lost interest in activities you used to enjoy since the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="diminished_interest",
            help_text="Activities that were important or enjoyable before now seem meaningless",
            examples=["Stopped hobbies", "No interest in work", "Don't enjoy entertainment"]
        ),
        
        SCIDQuestion(
            id="PTSD_15",
            text="Do you feel detached or distant from other people?",
            simple_text="Do you feel disconnected or distant from other people since the traumatic event?",
            response_type=ResponseType.YES_NO,
            symptom_category="detachment",
            help_text="Feeling cut off or alienated from others",
            examples=["Don't feel close to family", "Feel like an outsider", "Can't connect with people"]
        ),
        
        SCIDQuestion(
            id="PTSD_16",
            text="Are you unable to feel positive emotions like happiness, love, or satisfaction?",
            simple_text="Since the traumatic event, have you had trouble feeling positive emotions like happiness, love, or satisfaction?",
            response_type=ResponseType.YES_NO,
            symptom_category="emotional_numbing",
            help_text="Inability to experience positive feelings",
            examples=["Can't feel joy", "Numbness instead of love", "No satisfaction from achievements"]
        ),
        
        # Alterations in Arousal and Reactivity (Criterion E)
        SCIDQuestion(
            id="PTSD_17",
            text="Are you more irritable or have angry outbursts than before the event?",
            simple_text="Since the traumatic event, have you been more irritable or had angry outbursts with little or no reason?",
            response_type=ResponseType.YES_NO,
            symptom_category="irritability_anger",
            help_text="Increased anger that's different from before the trauma",
            examples=["Snapping at people", "Road rage", "Violent outbursts", "Can't control anger"]
        ),
        
        SCIDQuestion(
            id="PTSD_18",
            text="Do you engage in reckless or self-destructive behavior?",
            simple_text="Since the traumatic event, have you done reckless or dangerous things that you wouldn't normally do?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't engage in reckless behavior",
                "I drive recklessly or too fast",
                "I drink too much alcohol or use drugs",
                "I take unnecessary risks",
                "I engage in dangerous sexual behavior",
                "I do things that could harm me",
                "I engage in several risky behaviors"
            ],
            symptom_category="reckless_behavior",
            help_text="Behaviors that started or increased after the trauma"
        ),
        
        SCIDQuestion(
            id="PTSD_19",
            text="Are you overly alert or constantly watching for danger?",
            simple_text="Since the traumatic event, are you always on guard or watching out for danger, even when you're safe?",
            response_type=ResponseType.YES_NO,
            symptom_category="hypervigilance",
            help_text="Being constantly alert for threats, even in safe situations",
            examples=["Scanning rooms for exits", "Constantly checking surroundings", "Can't relax even at home"]
        ),
        
        SCIDQuestion(
            id="PTSD_20",
            text="Are you easily startled or jumpy?",
            simple_text="Since the traumatic event, do you get startled or jump easily when surprised by sounds or movements?",
            response_type=ResponseType.YES_NO,
            symptom_category="startle_response",
            help_text="Exaggerated startle response to unexpected sounds or movements",
            examples=["Jumping at car doors slamming", "Startled by people approaching", "Overreacting to sudden noises"]
        ),
        
        SCIDQuestion(
            id="PTSD_21",
            text="Do you have trouble concentrating or focusing?",
            simple_text="Since the traumatic event, have you had trouble focusing or concentrating on things?",
            response_type=ResponseType.YES_NO,
            symptom_category="concentration_problems",
            help_text="Difficulty maintaining attention on tasks or activities",
            examples=["Can't focus on work", "Mind wanders constantly", "Can't follow TV shows or books"]
        ),
        
        SCIDQuestion(
            id="PTSD_22",
            text="Do you have trouble falling asleep or staying asleep?",
            simple_text="Since the traumatic event, have you had trouble falling asleep or staying asleep?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I sleep normally",
                "I have trouble falling asleep",
                "I wake up frequently during the night",
                "I wake up very early and can't go back to sleep",
                "I have nightmares that wake me up",
                "I have several sleep problems"
            ],
            symptom_category="sleep_problems",
            help_text="Sleep disturbances that started or got worse after the trauma"
        ),
        
        # Duration and Onset
        SCIDQuestion(
            id="PTSD_23",
            text="How long have you had these trauma-related symptoms?",
            simple_text="For about how long have you had these symptoms related to the traumatic event?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1 to 3 months",
                "3 to 6 months",
                "6 months to 1 year",
                "1 to 2 years",
                "More than 2 years",
                "On and off since the event"
            ],
            symptom_category="symptom_duration",
            help_text="PTSD requires symptoms to be present for more than 1 month"
        ),
        
        SCIDQuestion(
            id="PTSD_24",
            text="When did these symptoms first start after the traumatic event?",
            simple_text="How soon after the traumatic event did these symptoms first start?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Right away - within hours or days",
                "Within the first month",
                "1 to 6 months later",
                "More than 6 months later",
                "Some symptoms started right away, others came later",
                "I'm not sure exactly when they started"
            ],
            symptom_category="onset_timing",
            help_text="Symptoms can start immediately or be delayed"
        ),
        
        # Functional Impairment
        SCIDQuestion(
            id="PTSD_25",
            text="How much do these symptoms interfere with your daily life?",
            simple_text="How much do these trauma-related symptoms interfere with your work, relationships, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Not at all", "A little bit", "Quite a bit", "Extremely"],
            symptom_category="functional_impairment",
            help_text="Consider the overall impact on your ability to function"
        ),
        
        SCIDQuestion(
            id="PTSD_25A",
            text="Which areas of your life are most affected by these symptoms?",
            simple_text="Which parts of your life have been most affected by these trauma-related symptoms?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Close relationships with family or friends",
                "Parenting or caring for others",
                "Social activities and going out",
                "Physical health and self-care",
                "Sleep and daily routines",
                "Feeling safe and secure",
                "Overall quality of life"
            ],
            required=False,
            symptom_category="impairment_areas",
            help_text="Choose all areas significantly affected"
        ),
        
        # Trauma History
        SCIDQuestion(
            id="PTSD_26",
            text="Have you experienced other traumatic events in your life?",
            simple_text="Besides the event we've been talking about, have you experienced other traumatic events?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No other traumatic events",
                "One other traumatic event",
                "2-3 other traumatic events",
                "Several other traumatic events",
                "Many traumatic experiences throughout my life",
                "I prefer not to answer"
            ],
            required=False,
            symptom_category="trauma_history",
            help_text="Multiple traumas can affect symptoms and treatment"
        ),
        
        # Dissociation
        SCIDQuestion(
            id="PTSD_27",
            text="Do you ever feel like you're outside of your body or that things around you are unreal?",
            simple_text="Do you sometimes feel like you're watching yourself from outside your body, or like the world around you isn't real?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't experience these feelings",
                "Sometimes I feel detached from myself",
                "Sometimes things around me seem unreal or dreamlike",
                "I feel like I'm watching myself from outside",
                "Both - I feel detached from myself and things seem unreal",
                "These feelings are very frequent or intense"
            ],
            symptom_category="dissociative_symptoms",
            help_text="These are dissociative symptoms that can occur with PTSD"
        ),
        
        # Substance Use
        SCIDQuestion(
            id="PTSD_28",
            text="Since the traumatic event, have you used alcohol or drugs to cope with your symptoms?",
            simple_text="Since the traumatic event, have you used alcohol or drugs to help deal with your symptoms or feelings?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I don't use substances to cope",
                "Occasionally drink alcohol to relax or sleep",
                "Regularly use alcohol to cope with symptoms",
                "Use marijuana or other drugs to cope",
                "Use prescription medications not as prescribed",
                "Use multiple substances to manage symptoms"
            ],
            required=False,
            symptom_category="substance_coping",
            help_text="Substance use to cope with trauma symptoms is common but can be problematic"
        ),
        
        # Social Support
        SCIDQuestion(
            id="PTSD_29",
            text="Do you have people you can talk to about what happened?",
            simple_text="Do you have family members, friends, or others you feel comfortable talking to about the traumatic event?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I have several people I can talk to",
                "Yes, I have one or two people I trust",
                "I have people around but don't feel comfortable talking",
                "I don't really have anyone to talk to",
                "I don't want to talk to anyone about it",
                "People try to help but don't understand"
            ],
            required=False,
            symptom_category="social_support",
            help_text="Social support can be important for recovery"
        ),
        
        # Current Treatment
        SCIDQuestion(
            id="PTSD_30",
            text="Are you currently getting any treatment for trauma-related symptoms?",
            simple_text="Are you currently taking medication or getting any treatment for these trauma-related symptoms?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No treatment currently",
                "Taking medication for anxiety/depression",
                "Taking medication specifically for PTSD",
                "Seeing a therapist who specializes in trauma",
                "In general counseling or therapy",
                "Both medication and therapy",
                "Using self-help or support groups",
                "Have tried treatment but not currently receiving any"
            ],
            required=False,
            symptom_category="current_treatment",
            help_text="Current treatment status helps with planning and coordination"
        ),
        
        # Safety Assessment
        SCIDQuestion(
            id="PTSD_31",
            text="Since the traumatic event, have you had thoughts of hurting yourself or ending your life?",
            simple_text="Since the traumatic event, have you had thoughts about hurting yourself or not wanting to live?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No thoughts of self-harm",
                "Sometimes wish I weren't here but no plans to hurt myself",
                "Have thought about hurting myself but wouldn't act on it",
                "Have had thoughts about ending my life",
                "Have made plans to hurt myself",
                "Have attempted to hurt myself"
            ],
            criteria_weight=2.0,
            symptom_category="suicidal_ideation",
            help_text="This is important safety information - please be honest"
        ),
        
        # Recovery and Resilience
        SCIDQuestion(
            id="PTSD_32",
            text="Are there times when you feel stronger or more hopeful about recovering?",
            simple_text="Despite these difficulties, are there times when you feel stronger or more hopeful about getting better?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I rarely feel hopeful about recovery",
                "Sometimes I have moments of hope",
                "I have good days mixed with bad days",
                "I feel hopeful when I'm with supportive people",
                "I'm starting to feel like I can get better",
                "I feel confident I will recover with help"
            ],
            required=False,
            symptom_category="recovery_hope",
            help_text="Hope and resilience are important for treatment planning"
        )
    ]
    
    return SCIDModule(
        id="PTSD",
        name="Post-Traumatic Stress Disorder",
        description="Assessment of trauma exposure and PTSD symptoms according to DSM-5 criteria. Evaluates intrusive symptoms, avoidance, negative alterations in cognition and mood, and alterations in arousal and reactivity.",
        questions=questions,
        diagnostic_threshold=0.7,
        estimated_time_mins=25,
        dsm_criteria=[
            "Exposure to actual or threatened death, serious injury, or sexual violence",
            "Intrusive symptoms (memories, dreams, flashbacks, distress, reactivity)",
            "Avoidance of trauma-related stimuli",
            "Negative alterations in cognitions and mood",
            "Alterations in arousal and reactivity",
            "Duration more than 1 month",
            "Clinically significant distress or impairment"
        ],
        severity_thresholds={
            "mild": 0.5,
            "moderate": 0.7,
            "severe": 0.85
        },
        category="trauma_disorders",
        version="1.0",
        clinical_notes="Requires exposure to trauma (Criterion A), plus symptoms from each cluster B-E, lasting >1 month with significant impairment. Assess for dissociative symptoms and suicide risk."
    )
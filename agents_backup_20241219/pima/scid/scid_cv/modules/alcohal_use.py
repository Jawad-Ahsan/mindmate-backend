# scid_cv/modules/alcohol_use.py
"""
SCID-CV Alcohol Use Disorder Module
Implements DSM-5 criteria for Alcohol Use Disorder assessment
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_alcohol_use_module() -> SCIDModule:
    """
    Create the Alcohol Use Disorder module for SCID-CV
    
    DSM-5 Criteria for Alcohol Use Disorder:
    A problematic pattern of alcohol use leading to significant impairment or distress,
    manifested by at least 2 of the following within a 12-month period:
    
    1. Taken in larger amounts/longer period than intended
    2. Persistent desire/unsuccessful efforts to cut down
    3. Great deal of time spent obtaining/using/recovering
    4. Craving or strong desire to use
    5. Failure to fulfill major role obligations
    6. Continued use despite social/interpersonal problems
    7. Important activities given up/reduced
    8. Use in physically hazardous situations
    9. Continued use despite physical/psychological problems
    10. Tolerance
    11. Withdrawal
    """
    
    questions = [
        # Initial screening
        SCIDQuestion(
            id="au_001",
            text="Do you drink alcoholic beverages?",
            simple_text="Do you drink alcohol (beer, wine, liquor, etc.)?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="alcohol_use",
            help_text="This includes beer, wine, liquor, mixed drinks, etc."
        ),
        
        SCIDQuestion(
            id="au_002",
            text="How often do you drink alcohol?",
            simple_text="How often do you drink alcohol?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't drink alcohol",
                "Less than once a month",
                "Once a month",
                "2-3 times a month",
                "Once a week",
                "2-3 times a week", 
                "4-5 times a week",
                "Daily or almost daily"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="frequency"
        ),
        
        # Criterion 1: Larger amounts or longer than intended
        SCIDQuestion(
            id="au_003",
            text="Do you often drink more alcohol than you planned to?",
            simple_text="Do you often end up drinking more than you meant to?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="loss_of_control",
            help_text="This means starting with the intention to have 1-2 drinks but having many more"
        ),
        
        SCIDQuestion(
            id="au_004",
            text="Do you often drink for longer periods than you intended?",
            simple_text="Do you often drink for much longer than you planned to?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="extended_use"
        ),
        
        SCIDQuestion(
            id="au_005",
            text="How often does this happen?",
            simple_text="How often do you drink more or longer than you planned?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Almost always"],
            required=False,
            criteria_weight=1.0,
            symptom_category="control_frequency"
        ),
        
        # Criterion 2: Persistent desire/unsuccessful efforts to cut down
        SCIDQuestion(
            id="au_006",
            text="Have you wanted to cut down or stop drinking?",
            simple_text="Have you wanted to drink less or stop drinking completely?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="desire_to_quit"
        ),
        
        SCIDQuestion(
            id="au_007",
            text="Have you tried to cut down or stop drinking but been unsuccessful?",
            simple_text="Have you tried to drink less or stop but couldn't do it?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="failed_attempts"
        ),
        
        SCIDQuestion(
            id="au_008",
            text="How many times have you tried to cut down or quit drinking?",
            simple_text="How many times have you tried to drink less or stop drinking?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I haven't tried to cut down or stop",
                "Once",
                "2-3 times",
                "4-5 times",
                "6-10 times",
                "More than 10 times",
                "I've lost count of how many times"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="quit_attempts"
        ),
        
        # Criterion 3: Great deal of time spent
        SCIDQuestion(
            id="au_009",
            text="Do you spend a lot of time drinking, getting alcohol, or recovering from drinking?",
            simple_text="Do you spend a lot of time drinking, buying alcohol, or getting over hangovers?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="time_consumed"
        ),
        
        SCIDQuestion(
            id="au_010",
            text="Which activities take up significant time in your life?",
            simple_text="What alcohol-related activities take up a lot of your time?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Going to bars, liquor stores, or places to drink",
                "Actually drinking alcohol",
                "Recovering from hangovers",
                "Thinking about drinking or planning when to drink",
                "Dealing with problems caused by drinking",
                "None of these take up significant time"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="time_activities"
        ),
        
        # Criterion 4: Craving
        SCIDQuestion(
            id="au_011",
            text="Do you have strong cravings or urges to drink alcohol?",
            simple_text="Do you get strong urges or cravings to drink alcohol?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="cravings"
        ),
        
        SCIDQuestion(
            id="au_012",
            text="How intense are these cravings?",
            simple_text="How strong are these urges to drink?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No cravings", "Mild cravings", "Moderate cravings", "Intense cravings"],
            required=False,
            criteria_weight=1.0,
            symptom_category="craving_intensity"
        ),
        
        # Criterion 5: Failure to fulfill role obligations
        SCIDQuestion(
            id="au_013",
            text="Has drinking interfered with your responsibilities at work, school, or home?",
            simple_text="Has drinking caused problems with your job, school, or taking care of your home and family?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="role_interference"
        ),
        
        SCIDQuestion(
            id="au_014",
            text="Which responsibilities have been affected by your drinking?",
            simple_text="What responsibilities have been harder to do because of drinking?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Missing work or calling in sick due to hangovers",
                "Poor performance at work or school",
                "Missing important deadlines or appointments",
                "Not taking care of children properly",
                "Not doing household chores or responsibilities",
                "Missing family events or obligations",
                "My drinking hasn't interfered with responsibilities"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="affected_responsibilities"
        ),
        
        # Criterion 6: Social/interpersonal problems
        SCIDQuestion(
            id="au_015",
            text="Has drinking caused problems in your relationships?",
            simple_text="Has drinking caused arguments, fights, or problems with family, friends, or coworkers?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="relationship_problems"
        ),
        
        SCIDQuestion(
            id="au_016",
            text="Do you continue drinking even though it causes relationship problems?",
            simple_text="Do you keep drinking even though it causes problems with people you care about?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="continued_use_relationships"
        ),
        
        SCIDQuestion(
            id="au_017",
            text="What relationship problems has drinking caused?",
            simple_text="What problems with other people has drinking caused?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Arguments with spouse/partner about drinking",
                "Family members worried about my drinking",
                "Lost friendships due to drinking behavior",
                "Embarrassing behavior while drinking",
                "Verbal or physical fights while drinking",
                "People avoiding me because of my drinking",
                "Drinking hasn't caused relationship problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="relationship_issues"
        ),
        
        # Criterion 7: Important activities given up
        SCIDQuestion(
            id="au_018",
            text="Have you given up important activities because of drinking?",
            simple_text="Have you stopped doing important things you used to enjoy because of drinking?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="activities_abandoned"
        ),
        
        SCIDQuestion(
            id="au_019",
            text="What activities have you reduced or stopped?",
            simple_text="What activities have you done less or stopped doing because of drinking?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Sports or exercise activities",
                "Hobbies or recreational activities",
                "Social activities with non-drinking friends",
                "Work-related social events",
                "Family activities and events",
                "Educational or self-improvement activities",
                "I haven't reduced any activities"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="reduced_activities"
        ),
        
        # Criterion 8: Physically hazardous use
        SCIDQuestion(
            id="au_020",
            text="Have you used alcohol in situations where it was physically dangerous?",
            simple_text="Have you drunk alcohol in situations where it could be dangerous to your safety?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="hazardous_use"
        ),
        
        SCIDQuestion(
            id="au_021",
            text="In which dangerous situations have you used alcohol?",
            simple_text="When have you drunk alcohol in dangerous situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Before or while driving a car",
                "While operating machinery or equipment",
                "Before swimming or water activities",
                "While taking care of small children",
                "In combination with medications",
                "While doing dangerous work tasks",
                "I haven't used alcohol in dangerous situations"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="dangerous_situations"
        ),
        
        # Criterion 9: Continued use despite problems
        SCIDQuestion(
            id="au_022",
            text="Do you continue drinking even though you know it's causing health problems?",
            simple_text="Do you keep drinking even though you know it's hurting your health?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="continued_despite_health"
        ),
        
        SCIDQuestion(
            id="au_023",
            text="What health or psychological problems do you think are related to drinking?",
            simple_text="What health or mental problems do you think drinking has caused or made worse?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Liver problems or stomach issues",
                "High blood pressure or heart problems",
                "Sleep problems",
                "Depression or anxiety",
                "Memory or thinking problems",
                "Injuries from falls or accidents",
                "I don't think drinking has caused health problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="health_consequences"
        ),
        
        # Criterion 10: Tolerance
        SCIDQuestion(
            id="au_024",
            text="Do you need to drink more alcohol now to feel the same effects you used to get?",
            simple_text="Do you need to drink more alcohol now than you used to in order to feel the same effects?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="tolerance"
        ),
        
        SCIDQuestion(
            id="au_025",
            text="How much more do you need to drink now compared to when you started?",
            simple_text="How much more do you need to drink now compared to when you first started drinking regularly?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "About the same amount",
                "About 25% more",
                "About 50% more",
                "About twice as much",
                "About 3 times as much",
                "Much more than 3 times as much"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="tolerance_amount"
        ),
        
        # Criterion 11: Withdrawal
        SCIDQuestion(
            id="au_026",
            text="When you stop drinking or drink less, do you experience withdrawal symptoms?",
            simple_text="When you stop drinking or drink much less, do you feel sick or have uncomfortable symptoms?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="withdrawal"
        ),
        
        SCIDQuestion(
            id="au_027",
            text="What withdrawal symptoms have you experienced?",
            simple_text="What symptoms do you get when you stop drinking or drink less?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Shaking or trembling hands",
                "Sweating",
                "Nausea or vomiting",
                "Anxiety or nervousness",
                "Difficulty sleeping",
                "Restlessness or agitation",
                "Feeling depressed or irritable",
                "Headaches",
                "Seeing or hearing things that aren't there",
                "I don't get withdrawal symptoms"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="withdrawal_symptoms"
        ),
        
        SCIDQuestion(
            id="au_028",
            text="Do you drink alcohol to avoid or relieve withdrawal symptoms?",
            simple_text="Do you drink alcohol to stop feeling sick or uncomfortable when you haven't been drinking?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.5,
            symptom_category="relief_drinking"
        ),
        
        # Timing and pattern
        SCIDQuestion(
            id="au_029",
            text="During your heaviest period of drinking, how much did you typically drink per day?",
            simple_text="When you were drinking the most, how much did you usually drink in one day?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "1-2 drinks per day",
                "3-4 drinks per day",
                "5-6 drinks per day",
                "7-10 drinks per day",
                "11-15 drinks per day",
                "16-20 drinks per day",
                "More than 20 drinks per day"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="peak_consumption",
            help_text="One drink = 12 oz beer, 5 oz wine, or 1.5 oz liquor"
        ),
        
        SCIDQuestion(
            id="au_030",
            text="How long have you been experiencing problems related to alcohol use?",
            simple_text="How long have you been having problems because of drinking?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 6 months",
                "6 months to 1 year",
                "1-2 years",
                "2-5 years",
                "5-10 years",
                "More than 10 years"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="problem_duration"
        ),
        
        # Current status
        SCIDQuestion(
            id="au_031",
            text="How would you rate your current alcohol problem?",
            simple_text="How bad would you say your alcohol problem is right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problem", "Mild problem", "Moderate problem", "Severe problem"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_severity"
        ),
        
        SCIDQuestion(
            id="au_032",
            text="Are you currently trying to address your alcohol use?",
            simple_text="Are you currently trying to do something about your drinking?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I'm not trying to change my drinking",
                "I'm trying to cut back on my own",
                "I'm in counseling or therapy",
                "I'm attending AA or support groups",
                "I'm taking medication to help with drinking",
                "I've recently stopped drinking completely",
                "Other treatment or help"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="current_treatment"
        ),
        
        # Impact assessment
        SCIDQuestion(
            id="au_033",
            text="Overall, how much has alcohol use interfered with your life?",
            simple_text="Overall, how much has drinking alcohol made your life more difficult?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="life_interference"
        ),
        
        SCIDQuestion(
            id="au_034",
            text="Has anyone close to you expressed concern about your drinking?",
            simple_text="Have family members, friends, or doctors said they're worried about your drinking?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="others_concerned"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A problematic pattern of alcohol use leading to clinically significant impairment or distress, manifested by at least 2 of the following within a 12-month period:",
        "1. Alcohol taken in larger amounts or over longer period than intended",
        "2. Persistent desire or unsuccessful efforts to cut down or control use",
        "3. Great deal of time spent obtaining, using, or recovering from alcohol",
        "4. Craving or strong desire/urge to use alcohol",
        "5. Recurrent use resulting in failure to fulfill major obligations",
        "6. Continued use despite persistent social or interpersonal problems",
        "7. Important activities given up or reduced because of alcohol use",
        "8. Recurrent use in physically hazardous situations",
        "9. Continued use despite knowledge of physical or psychological problems",
        "10. Tolerance (need for increased amounts or diminished effect)",
        "11. Withdrawal (characteristic syndrome or alcohol used to relieve symptoms)"
    ]
    
    # Severity thresholds based on number of criteria met
    severity_thresholds = {
        "mild": 0.4,      # 2-3 criteria (mild severity)
        "moderate": 0.6,  # 4-5 criteria (moderate severity)  
        "severe": 0.8     # 6+ criteria (severe severity)
    }
    
    return SCIDModule(
        id="ALCOHOL_USE",
        name="Alcohol Use Disorder",
        description="Assessment module for Alcohol Use Disorder based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.4,  # Lower threshold as 2+ criteria indicate disorder
        estimated_time_mins=18,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="substance_use_disorders",
        version="1.0",
        clinical_notes="Severity is determined by number of criteria met: Mild (2-3), Moderate (4-5), Severe (6+)"
    )
                
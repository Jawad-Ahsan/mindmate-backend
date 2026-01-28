# scid_cv/modules/substance_use.py
"""
SCID-CV Substance Use Disorder Module
Implements DSM-5 criteria for Substance Use Disorder assessment (non-alcohol substances)
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_substance_use_module() -> SCIDModule:
    """
    Create the Substance Use Disorder module for SCID-CV
    
    DSM-5 Criteria for Substance Use Disorder:
    Same 11 criteria as Alcohol Use Disorder but applied to other substances
    """
    
    questions = [
        # Initial screening and substance identification
        SCIDQuestion(
            id="su_001",
            text="Do you use any drugs or substances other than alcohol?",
            simple_text="Do you use any drugs or other substances (not including alcohol)?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="substance_use",
            help_text="This includes illegal drugs, prescription medications used non-medically, and other substances"
        ),
        
        SCIDQuestion(
            id="su_002",
            text="Which substances do you use or have you used?",
            simple_text="What drugs or substances do you use or have you used?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Marijuana/cannabis",
                "Cocaine or crack cocaine",
                "Heroin or other opioids",
                "Prescription painkillers (not as prescribed)",
                "Methamphetamine or amphetamines",
                "Prescription stimulants (not as prescribed)",
                "Sedatives/sleeping pills (not as prescribed)",
                "Hallucinogens (LSD, mushrooms, etc.)",
                "Ecstasy/MDMA",
                "Inhalants (glue, paint, etc.)",
                "Other substances",
                "I don't use any substances"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="substance_types"
        ),
        
        SCIDQuestion(
            id="su_003",
            text="Which substance has caused you the most problems?",
            simple_text="Which drug or substance has caused you the biggest problems?",
            response_type=ResponseType.TEXT,
            required=True,
            criteria_weight=1.0,
            symptom_category="primary_substance",
            help_text="Please name the one substance that has been most problematic for you"
        ),
        
        SCIDQuestion(
            id="su_004",
            text="How often do you use this substance?",
            simple_text="How often do you use this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't currently use it",
                "Less than once a month",
                "Once a month",
                "2-3 times a month", 
                "Once a week",
                "2-3 times a week",
                "4-6 times a week",
                "Daily or almost daily"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="frequency"
        ),
        
        # Criterion 1: Larger amounts or longer than intended
        SCIDQuestion(
            id="su_005",
            text="Do you often use more of the substance than you planned to?",
            simple_text="Do you often end up using more of this substance than you meant to?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="loss_of_control"
        ),
        
        SCIDQuestion(
            id="su_006",
            text="Do you often use the substance for longer periods than you intended?",
            simple_text="Do you often use this substance for much longer than you planned to?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="extended_use"
        ),
        
        # Criterion 2: Persistent desire/unsuccessful efforts to cut down
        SCIDQuestion(
            id="su_007",
            text="Have you wanted to cut down or stop using this substance?",
            simple_text="Have you wanted to use less of this substance or stop using it completely?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="desire_to_quit"
        ),
        
        SCIDQuestion(
            id="su_008",
            text="Have you tried to cut down or stop using but been unsuccessful?",
            simple_text="Have you tried to use less or stop but couldn't do it?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="failed_attempts"
        ),
        
        SCIDQuestion(
            id="su_009",
            text="How many times have you tried to cut down or quit?",
            simple_text="How many times have you tried to use less or stop using this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I haven't tried to cut down or stop",
                "Once", 
                "2-3 times",
                "4-5 times",
                "6-10 times",
                "More than 10 times",
                "I've lost count"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="quit_attempts"
        ),
        
        # Criterion 3: Great deal of time spent
        SCIDQuestion(
            id="su_010",
            text="Do you spend a lot of time getting, using, or recovering from this substance?",
            simple_text="Do you spend a lot of time getting this substance, using it, or getting over its effects?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="time_consumed"
        ),
        
        SCIDQuestion(
            id="su_011",
            text="Which activities take up significant time in your life?",
            simple_text="What substance-related activities take up a lot of your time?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Finding dealers or places to get substances",
                "Traveling to get substances",
                "Actually using the substance",
                "Recovering from using (coming down, sleeping it off)",
                "Thinking about using or planning when to use",
                "Dealing with problems caused by using",
                "None of these take up significant time"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="time_activities"
        ),
        
        # Criterion 4: Craving
        SCIDQuestion(
            id="su_012",
            text="Do you have strong cravings or urges to use this substance?",
            simple_text="Do you get strong urges or cravings to use this substance?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="cravings"
        ),
        
        SCIDQuestion(
            id="su_013",
            text="How intense are these cravings?",
            simple_text="How strong are these urges to use?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No cravings", "Mild cravings", "Moderate cravings", "Intense cravings"],
            required=False,
            criteria_weight=1.0,
            symptom_category="craving_intensity"
        ),
        
        # Criterion 5: Failure to fulfill role obligations
        SCIDQuestion(
            id="su_014",
            text="Has using this substance interfered with your responsibilities at work, school, or home?",
            simple_text="Has using this substance caused problems with your job, school, or taking care of your home and family?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="role_interference"
        ),
        
        SCIDQuestion(
            id="su_015",
            text="Which responsibilities have been affected?",
            simple_text="What responsibilities have been harder to do because of using this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Missing work or school due to using or being high",
                "Poor performance at work or school",
                "Missing important deadlines or appointments",
                "Not taking care of children properly",
                "Not doing household chores or responsibilities",
                "Missing family events or obligations",
                "Using hasn't interfered with responsibilities"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="affected_responsibilities"
        ),
        
        # Criterion 6: Social/interpersonal problems
        SCIDQuestion(
            id="su_016",
            text="Has using this substance caused problems in your relationships?",
            simple_text="Has using this substance caused arguments, fights, or problems with family, friends, or coworkers?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="relationship_problems"
        ),
        
        SCIDQuestion(
            id="su_017",
            text="Do you continue using even though it causes relationship problems?",
            simple_text="Do you keep using this substance even though it causes problems with people you care about?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="continued_use_relationships"
        ),
        
        # Criterion 7: Important activities given up
        SCIDQuestion(
            id="su_018",
            text="Have you given up important activities because of using this substance?",
            simple_text="Have you stopped doing important things you used to enjoy because of using this substance?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="activities_abandoned"
        ),
        
        SCIDQuestion(
            id="su_019",
            text="What activities have you reduced or stopped?",
            simple_text="What activities have you done less or stopped doing because of using this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Sports or exercise activities",
                "Hobbies or recreational activities",
                "Social activities with non-using friends",
                "Work-related or school activities",
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
            id="su_020",
            text="Have you used this substance in situations where it was physically dangerous?",
            simple_text="Have you used this substance in situations where it could be dangerous to your safety?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="hazardous_use"
        ),
        
        SCIDQuestion(
            id="su_021",
            text="In which dangerous situations have you used this substance?",
            simple_text="When have you used this substance in dangerous situations?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Before or while driving",
                "While operating machinery or equipment",
                "While taking care of small children",
                "In combination with other drugs or alcohol",
                "While doing dangerous work tasks",
                "In unsafe locations or with dangerous people",
                "I haven't used in dangerous situations"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="dangerous_situations"
        ),
        
        # Criterion 9: Continued use despite problems
        SCIDQuestion(
            id="su_022",
            text="Do you continue using even though you know it's causing health problems?",
            simple_text="Do you keep using this substance even though you know it's hurting your health?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="continued_despite_health"
        ),
        
        SCIDQuestion(
            id="su_023",
            text="What health or psychological problems do you think are related to using this substance?",
            simple_text="What health or mental problems do you think using this substance has caused or made worse?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Physical health problems or injuries",
                "Sleep problems",
                "Depression or anxiety", 
                "Memory or thinking problems",
                "Paranoia or feeling suspicious",
                "Problems with appetite or weight",
                "I don't think using has caused health problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="health_consequences"
        ),
        
        # Criterion 10: Tolerance
        SCIDQuestion(
            id="su_024",
            text="Do you need to use more of this substance now to feel the same effects?",
            simple_text="Do you need to use more of this substance now than you used to in order to feel the same effects?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="tolerance"
        ),
        
        SCIDQuestion(
            id="su_025",
            text="How much more do you need to use now compared to when you started?",
            simple_text="How much more do you need to use now compared to when you first started using regularly?",
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
            id="su_026",
            text="When you stop using or use less, do you experience withdrawal symptoms?",
            simple_text="When you stop using this substance or use much less, do you feel sick or have uncomfortable symptoms?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="withdrawal"
        ),
        
        SCIDQuestion(
            id="su_027",
            text="What withdrawal symptoms have you experienced?",
            simple_text="What symptoms do you get when you stop using or use less of this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Anxiety, nervousness, or restlessness",
                "Depression or sadness",
                "Fatigue or tiredness",
                "Sleep problems or insomnia",
                "Increased appetite",
                "Irritability or anger",
                "Physical discomfort or aches",
                "Nausea or stomach problems",
                "Shaking or trembling",
                "I don't get withdrawal symptoms"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="withdrawal_symptoms"
        ),
        
        SCIDQuestion(
            id="su_028",
            text="Do you use this substance to avoid or relieve withdrawal symptoms?",
            simple_text="Do you use this substance to stop feeling sick or uncomfortable when you haven't been using?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.5,
            symptom_category="relief_using"
        ),
        
        # Additional assessment questions
        SCIDQuestion(
            id="su_029",
            text="How long have you been experiencing problems related to using this substance?",
            simple_text="How long have you been having problems because of using this substance?",
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
        
        SCIDQuestion(
            id="su_030",
            text="How would you rate your current substance use problem?",
            simple_text="How bad would you say your substance use problem is right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problem", "Mild problem", "Moderate problem", "Severe problem"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_severity"
        ),
        
        SCIDQuestion(
            id="su_031",
            text="Have you ever had legal problems because of using this substance?",
            simple_text="Have you gotten in trouble with the law because of using this substance?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Arrested for possession",
                "Arrested for being under the influence",
                "Arrested for driving under the influence",
                "Other drug-related legal problems",
                "No legal problems related to substance use"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="legal_problems"
        ),
        
        SCIDQuestion(
            id="su_032",
            text="Are you currently trying to address your substance use?",
            simple_text="Are you currently trying to do something about your substance use?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I'm not trying to change my substance use",
                "I'm trying to cut back on my own",
                "I'm in counseling or therapy",
                "I'm attending NA or support groups",
                "I'm in a treatment program",
                "I'm taking medication to help",
                "I've recently stopped using completely"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="current_treatment"
        ),
        
        SCIDQuestion(
            id="su_033",
            text="Overall, how much has substance use interfered with your life?",
            simple_text="Overall, how much has using substances made your life more difficult?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="life_interference"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A problematic pattern of substance use leading to clinically significant impairment or distress, manifested by at least 2 of the following within a 12-month period:",
        "1. Substance taken in larger amounts or over longer period than intended",
        "2. Persistent desire or unsuccessful efforts to cut down or control use",
        "3. Great deal of time spent obtaining, using, or recovering from substance",
        "4. Craving or strong desire/urge to use substance",
        "5. Recurrent use resulting in failure to fulfill major obligations",
        "6. Continued use despite persistent social or interpersonal problems",
        "7. Important activities given up or reduced because of substance use",
        "8. Recurrent use in physically hazardous situations",
        "9. Continued use despite knowledge of physical or psychological problems",
        "10. Tolerance (need for increased amounts or diminished effect)",
        "11. Withdrawal (characteristic syndrome or substance used to relieve symptoms)"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.4,      # 2-3 criteria (mild severity)
        "moderate": 0.6,  # 4-5 criteria (moderate severity)
        "severe": 0.8     # 6+ criteria (severe severity)
    }
    
    return SCIDModule(
        id="SUBSTANCE_USE",
        name="Substance Use Disorder",
        description="Assessment module for Substance Use Disorder (non-alcohol) based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.4,  # Lower threshold as 2+ criteria indicate disorder
        estimated_time_mins=20,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="substance_use_disorders",
        version="1.0",
        clinical_notes="Severity is determined by number of criteria met: Mild (2-3), Moderate (4-5), Severe (6+). Can be used for various substances including cannabis, cocaine, opioids, stimulants, etc."
    )
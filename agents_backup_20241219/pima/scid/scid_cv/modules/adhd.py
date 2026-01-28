# scid_cv/modules/adhd.py
"""
SCID-CV Attention-Deficit/Hyperactivity Disorder (ADHD) Module
Implements DSM-5 criteria for ADHD assessment
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_adhd_module() -> SCIDModule:
    """
    Create the ADHD module for SCID-CV
    
    DSM-5 Criteria for ADHD:
    A. Persistent pattern of inattention and/or hyperactivity-impulsivity
    B. Several symptoms present before age 12
    C. Several symptoms present in 2+ settings
    D. Clear evidence symptoms interfere with functioning
    E. Symptoms not better explained by another disorder
    """
    
    questions = [
        # Initial screening
        SCIDQuestion(
            id="adhd_001",
            text="Do you have ongoing problems with attention, concentration, or hyperactivity?",
            simple_text="Do you have continuing problems with paying attention, focusing, or being hyperactive?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="adhd_screening",
            help_text="These problems should be present most of the time and interfere with daily life"
        ),
        
        # Inattention symptoms (Criterion A1)
        SCIDQuestion(
            id="adhd_002",
            text="Do you often fail to give close attention to details or make careless mistakes?",
            simple_text="Do you often miss details or make careless mistakes in work, school, or other activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="inattention_details"
        ),
        
        SCIDQuestion(
            id="adhd_003",
            text="Do you often have trouble keeping your attention on tasks or activities?",
            simple_text="Do you often have trouble staying focused on tasks or fun activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="sustaining_attention"
        ),
        
        SCIDQuestion(
            id="adhd_004",
            text="Do you often seem like you're not listening when spoken to directly?",
            simple_text="Do people often say you don't seem to be listening when they talk to you?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="not_listening"
        ),
        
        SCIDQuestion(
            id="adhd_005",
            text="Do you often not follow through on instructions or fail to finish tasks?",
            simple_text="Do you often start tasks but not finish them, or not follow instructions completely?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="not_finishing"
        ),
        
        SCIDQuestion(
            id="adhd_006",
            text="Do you often have trouble organizing tasks and activities?",
            simple_text="Do you often have trouble organizing your work, activities, or belongings?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="organization_problems"
        ),
        
        SCIDQuestion(
            id="adhd_007",
            text="Do you often avoid or dislike tasks that require sustained mental effort?",
            simple_text="Do you often avoid or really dislike tasks that require a lot of thinking or concentration?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="avoids_mental_effort"
        ),
        
        SCIDQuestion(
            id="adhd_008",
            text="Do you often lose things necessary for tasks or activities?",
            simple_text="Do you often lose things you need for work, school, or daily activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="loses_things"
        ),
        
        SCIDQuestion(
            id="adhd_009",
            text="Are you often easily distracted by outside stimuli or unrelated thoughts?",
            simple_text="Are you often easily distracted by things around you or thoughts that pop into your head?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="easily_distracted"
        ),
        
        SCIDQuestion(
            id="adhd_010",
            text="Are you often forgetful in daily activities?",
            simple_text="Do you often forget to do daily activities like chores, errands, or appointments?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="forgetful"
        ),
        
        # Hyperactivity-Impulsivity symptoms (Criterion A2)
        SCIDQuestion(
            id="adhd_011",
            text="Do you often fidget with your hands or feet or squirm in your seat?",
            simple_text="Do you often fidget, tap, or squirm when you're supposed to sit still?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="fidgets"
        ),
        
        SCIDQuestion(
            id="adhd_012",
            text="Do you often leave your seat when you're expected to remain seated?",
            simple_text="Do you often get up and move around when you're supposed to stay seated?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="leaves_seat"
        ),
        
        SCIDQuestion(
            id="adhd_013",
            text="Do you often feel restless or like you need to be moving?",
            simple_text="Do you often feel restless or like you have to keep moving or doing something?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="restless"
        ),
        
        SCIDQuestion(
            id="adhd_014",
            text="Do you often have trouble engaging in leisure activities quietly?",
            simple_text="Do you often have trouble doing fun, relaxing activities quietly?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="trouble_quiet_activities"
        ),
        
        SCIDQuestion(
            id="adhd_015",
            text="Are you often 'on the go' or act as if 'driven by a motor'?",
            simple_text="Are you often constantly active or feel like you can't slow down or relax?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="driven_by_motor"
        ),
        
        SCIDQuestion(
            id="adhd_016",
            text="Do you often talk excessively?",
            simple_text="Do you often talk much more than other people or have trouble stopping yourself from talking?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="talks_excessively"
        ),
        
        SCIDQuestion(
            id="adhd_017",
            text="Do you often blurt out answers before questions are completed?",
            simple_text="Do you often start answering questions before the person is done asking them?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="blurts_answers"
        ),
        
        SCIDQuestion(
            id="adhd_018",
            text="Do you often have trouble waiting your turn?",
            simple_text="Do you often have trouble waiting in lines or waiting for your turn?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="trouble_waiting"
        ),
        
        SCIDQuestion(
            id="adhd_019",
            text="Do you often interrupt or intrude on others?",
            simple_text="Do you often interrupt other people's conversations or activities?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["Never", "Sometimes", "Often", "Very often"],
            required=True,
            criteria_weight=1.0,
            symptom_category="interrupts_others"
        ),
        
        # Criterion B: Age of onset
        SCIDQuestion(
            id="adhd_020",
            text="Did these problems begin before you were 12 years old?",
            simple_text="Did these attention or hyperactivity problems start before you turned 12?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="early_onset"
        ),
        
        SCIDQuestion(
            id="adhd_021",
            text="At what age did you first notice these problems?",
            simple_text="How old were you when you or others first noticed these problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Preschool (ages 3-5)",
                "Early elementary (ages 6-8)",
                "Late elementary (ages 9-11)",
                "Middle school (ages 12-14)",
                "High school (ages 15-18)",
                "Adulthood (over 18)",
                "I'm not sure when they started"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="age_first_noticed"
        ),
        
        # Criterion C: Multiple settings
        SCIDQuestion(
            id="adhd_022",
            text="Do these problems occur in multiple settings?",
            simple_text="Do you have these problems in different places, not just at home or just at work/school?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="multiple_settings"
        ),
        
        SCIDQuestion(
            id="adhd_023",
            text="In which settings do you experience these problems?",
            simple_text="Where do you have these attention or hyperactivity problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "At home",
                "At work or school",
                "In social situations with friends",
                "In romantic relationships",
                "While driving",
                "During leisure activities",
                "In all or most situations",
                "Only in one specific setting"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="problem_settings"
        ),
        
        # Criterion D: Functional impairment
        SCIDQuestion(
            id="adhd_024",
            text="Do these problems significantly interfere with your functioning?",
            simple_text="Do these problems make it much harder to do well at work, school, or in relationships?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="functional_impairment"
        ),
        
        SCIDQuestion(
            id="adhd_025",
            text="Which areas of your life are most affected?",
            simple_text="What areas of your life are most impacted by these problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Relationships with family",
                "Friendships and social relationships",
                "Romantic relationships",
                "Parenting responsibilities",
                "Managing household tasks",
                "Financial management",
                "Driving safety",
                "Overall quality of life",
                "These problems don't significantly affect my life"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="affected_areas"
        ),
        
        # Work/School specific impacts
        SCIDQuestion(
            id="adhd_026",
            text="How do these problems affect your work or school performance?",
            simple_text="How do these problems make work or school more difficult?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Difficulty completing assignments or projects",
                "Missing deadlines frequently",
                "Making careless errors",
                "Trouble staying organized",
                "Difficulty sitting through meetings or classes",
                "Problems following through on instructions",
                "Trouble managing time effectively",
                "They don't affect my work/school performance"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="work_school_impact"
        ),
        
        # Relationship impacts
        SCIDQuestion(
            id="adhd_027",
            text="How do these problems affect your relationships?",
            simple_text="How do these problems affect your relationships with other people?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Others say I don't listen to them",
                "I interrupt people frequently",
                "I'm often late or forget commitments",
                "I have trouble with household responsibilities",
                "I'm restless during conversations or activities",
                "I lose important things that belong to others",
                "They don't affect my relationships"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="relationship_impact"
        ),
        
        # Severity assessment
        SCIDQuestion(
            id="adhd_028",
            text="How would you rate your current attention problems?",
            simple_text="How bad are your attention and concentration problems right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problems", "Mild problems", "Moderate problems", "Severe problems"],
            required=True,
            criteria_weight=1.0,
            symptom_category="attention_severity"
        ),
        
        SCIDQuestion(
            id="adhd_029",
            text="How would you rate your current hyperactivity/impulsivity problems?",
            simple_text="How bad are your hyperactivity and impulsivity problems right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problems", "Mild problems", "Moderate problems", "Severe problems"],
            required=True,
            criteria_weight=1.0,
            symptom_category="hyperactivity_severity"
        ),
        
        # Coping strategies
        SCIDQuestion(
            id="adhd_030",
            text="What strategies do you use to manage these problems?",
            simple_text="What do you do to try to deal with these attention or hyperactivity problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Use lists and reminders",
                "Set multiple alarms or timers",
                "Break tasks into smaller steps",
                "Use fidget objects or tools",
                "Take frequent breaks",
                "Exercise regularly",
                "Avoid distracting environments",
                "Take medication",
                "I don't use any strategies"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="coping_strategies"
        ),
        
        # Treatment history
        SCIDQuestion(
            id="adhd_031",
            text="Have you ever received treatment for attention or hyperactivity problems?",
            simple_text="Have you ever gotten help or treatment for ADHD or attention problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I haven't received treatment",
                "I'm currently taking medication",
                "I've taken medication in the past",
                "I'm currently in counseling or therapy",
                "I've had counseling or therapy in the past",
                "I received accommodations at school or work",
                "I'm considering getting help"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="treatment_history"
        ),
        
        # Family history
        SCIDQuestion(
            id="adhd_032",
            text="Do any family members have ADHD or similar problems?",
            simple_text="Do any of your family members have ADHD or attention/hyperactivity problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Parents or siblings",
                "Children",
                "Other relatives",
                "No family members that I know of",
                "I'm not sure"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="family_history"
        ),
        
        # Time management
        SCIDQuestion(
            id="adhd_033",
            text="Do you have significant problems with time management?",
            simple_text="Do you have big problems managing your time and being on time?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="time_management"
        ),
        
        SCIDQuestion(
            id="adhd_034",
            text="Which time management problems do you experience?",
            simple_text="What time management problems do you have?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Frequently running late",
                "Underestimating how long tasks will take",
                "Procrastinating until the last minute",
                "Forgetting appointments or commitments",
                "Difficulty prioritizing tasks",
                "Getting distracted and losing track of time",
                "I don't have significant time management problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="time_problems"
        ),
        
        # Overall assessment
        SCIDQuestion(
            id="adhd_035",
            text="Overall, how much do these problems interfere with your daily life?",
            simple_text="Overall, how much do these attention and hyperactivity problems make your daily life more difficult?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="overall_interference"
        ),
        
        # Insight
        SCIDQuestion(
            id="adhd_036",
            text="Do you believe you have ADHD?",
            simple_text="Do you think you have ADHD?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I believe I have ADHD",
                "I'm not sure but it's possible",
                "I don't think so, but others have suggested it",
                "No, I don't think I have ADHD",
                "I'm confused about whether I have it"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="self_assessment"
        )
    ]
    
    # DSM-5 diagnostic criteria
    dsm_criteria = [
        "A. A persistent pattern of inattention and/or hyperactivity-impulsivity that interferes with functioning or development:",
        "   INATTENTION: 6+ symptoms for 6+ months (5+ for adults 17+):",
        "   1. Fails to give close attention to details/makes careless mistakes",
        "   2. Has trouble sustaining attention in tasks or activities",
        "   3. Does not seem to listen when spoken to directly",
        "   4. Does not follow through on instructions/fails to finish tasks",
        "   5. Has trouble organizing tasks and activities",
        "   6. Avoids/dislikes tasks requiring sustained mental effort",
        "   7. Loses things necessary for tasks/activities",
        "   8. Easily distracted by extraneous stimuli",
        "   9. Forgetful in daily activities",
        "",
        "   HYPERACTIVITY-IMPULSIVITY: 6+ symptoms for 6+ months (5+ for adults 17+):",
        "   1. Fidgets/taps hands or feet/squirms in seat",
        "   2. Leaves seat when expected to remain seated",
        "   3. Feels restless",
        "   4. Unable to engage in leisure activities quietly",
        "   5. 'On the go'/acts as if 'driven by a motor'",
        "   6. Talks excessively",
        "   7. Blurts out answers before questions completed",
        "   8. Has trouble waiting turn",
        "   9. Interrupts or intrudes on others",
        "",
        "B. Several inattentive or hyperactive-impulsive symptoms present before age 12",
        "C. Several symptoms present in 2+ settings",
        "D. Clear evidence symptoms interfere with/reduce quality of functioning",
        "E. Symptoms not better explained by another mental disorder"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.4,      # Few symptoms beyond required, minimal impairment
        "moderate": 0.6,  # Moderate symptoms and impairment
        "severe": 0.8     # Many symptoms, severe functional impairment
    }
    
    return SCIDModule(
        id="ADHD",
        name="Attention-Deficit/Hyperactivity Disorder (ADHD)",
        description="Assessment module for ADHD based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=20,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="neurodevelopmental_disorders",
        version="1.0",
        clinical_notes="Requires 6+ inattentive OR 6+ hyperactive-impulsive symptoms for children (5+ for adults 17+), with onset before age 12, present in multiple settings, and causing significant impairment."
    )
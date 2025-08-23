# scid_cv/modules/eating_disorders.py
"""
SCID-CV Eating Disorders Module
Implements DSM-5 criteria for Anorexia Nervosa, Bulimia Nervosa, and Binge Eating Disorder
"""

from ..base_types import SCIDModule, SCIDQuestion, ResponseType

def create_eating_disorders_module() -> SCIDModule:
    """
    Create the Eating Disorders module for SCID-CV
    
    Covers DSM-5 criteria for:
    - Anorexia Nervosa
    - Bulimia Nervosa  
    - Binge Eating Disorder
    """
    
    questions = [
        # Initial screening
        SCIDQuestion(
            id="ed_001",
            text="Have you had concerns about your eating, weight, or body shape?",
            simple_text="Have you been worried about your eating, weight, or how your body looks?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="eating_concerns",
            help_text="This includes worrying about being overweight, restricting food, or binge eating"
        ),
        
        # Weight and BMI assessment  
        SCIDQuestion(
            id="ed_002",
            text="What is your current height and weight?",
            simple_text="How tall are you and how much do you weigh now?",
            response_type=ResponseType.TEXT,
            required=True,
            criteria_weight=1.0,
            symptom_category="current_weight",
            help_text="Please provide height in feet/inches and weight in pounds"
        ),
        
        SCIDQuestion(
            id="ed_003",
            text="What was your lowest adult weight?",
            simple_text="What is the least you have weighed as an adult?",
            response_type=ResponseType.TEXT,
            required=True,
            criteria_weight=1.0,
            symptom_category="lowest_weight"
        ),
        
        # Anorexia Nervosa Criteria
        # Criterion A: Restriction of energy intake leading to low body weight
        SCIDQuestion(
            id="ed_004",
            text="Have you deliberately restricted your food intake to lose weight or prevent weight gain?",
            simple_text="Have you purposely eaten much less food to lose weight or to keep from gaining weight?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="food_restriction"
        ),
        
        SCIDQuestion(
            id="ed_005",
            text="How would you describe your current weight?",
            simple_text="How would you describe your weight right now?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Significantly underweight for my height and age",
                "Somewhat underweight",
                "Normal weight",
                "Somewhat overweight", 
                "Significantly overweight",
                "I'm not sure"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="weight_status"
        ),
        
        # Criterion B: Intense fear of gaining weight
        SCIDQuestion(
            id="ed_006",
            text="Do you have an intense fear of gaining weight or becoming fat?",
            simple_text="Are you very afraid of gaining weight or getting fat?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="weight_fear"
        ),
        
        SCIDQuestion(
            id="ed_007",
            text="Even when underweight, do you still fear gaining weight?",
            simple_text="Even when you weigh less than you should, are you still afraid of gaining weight?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.5,
            symptom_category="persistent_fear"
        ),
        
        # Criterion C: Disturbed body image
        SCIDQuestion(
            id="ed_008",
            text="Do you see yourself as overweight even when others say you're underweight?",
            simple_text="Do you think you look fat or overweight even when other people say you're too thin?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="body_image_distortion"
        ),
        
        SCIDQuestion(
            id="ed_009",
            text="Is your self-worth heavily influenced by your body weight or shape?",
            simple_text="Do you feel good or bad about yourself mainly based on your weight or how your body looks?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="weight_based_self_worth"
        ),
        
        SCIDQuestion(
            id="ed_010",
            text="Do you deny the seriousness of your current low body weight?",
            simple_text="Do you think your low weight is not a serious problem, even when others are worried?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="weight_denial"
        ),
        
        # Binge eating assessment (for Bulimia and Binge Eating Disorder)
        SCIDQuestion(
            id="ed_011",
            text="Do you have episodes where you eat much more food than most people would in a short time?",
            simple_text="Do you sometimes eat a very large amount of food in a short period of time?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="binge_eating",
            help_text="This means eating much more than others would in the same situation and time period"
        ),
        
        SCIDQuestion(
            id="ed_012",
            text="During these episodes, do you feel like you can't stop eating or control what you eat?",
            simple_text="When you eat these large amounts, do you feel like you can't stop or control your eating?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="loss_of_control"
        ),
        
        SCIDQuestion(
            id="ed_013",
            text="How often do these binge eating episodes occur?",
            simple_text="How often do you have these episodes of eating very large amounts of food?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't have binge eating episodes",
                "Less than once a week",
                "Once a week",
                "Twice a week",
                "Three times a week",
                "Four or more times a week",
                "Daily or almost daily"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="binge_frequency"
        ),
        
        SCIDQuestion(
            id="ed_014",
            text="What characterizes your binge eating episodes?",
            simple_text="What happens during your binge eating episodes?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Eating much more rapidly than normal",
                "Eating until feeling uncomfortably full",
                "Eating large amounts when not physically hungry",
                "Eating alone due to embarrassment",
                "Feeling disgusted, depressed, or guilty afterward",
                "I don't have binge eating episodes"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="binge_characteristics"
        ),
        
        # Compensatory behaviors (for Bulimia)
        SCIDQuestion(
            id="ed_015",
            text="Do you try to prevent weight gain after eating large amounts?",
            simple_text="After eating too much, do you do things to try to prevent gaining weight?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="compensatory_behaviors"
        ),
        
        SCIDQuestion(
            id="ed_016",
            text="What do you do to prevent weight gain after eating?",
            simple_text="What do you do to try to prevent weight gain after eating too much?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Make myself vomit",
                "Use laxatives",
                "Use diuretics (water pills)",
                "Use diet pills or other medications",
                "Fast or skip meals for days",
                "Exercise excessively",
                "I don't do anything to prevent weight gain"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="compensation_methods"
        ),
        
        SCIDQuestion(
            id="ed_017",
            text="How often do you engage in these compensatory behaviors?",
            simple_text="How often do you do these things to prevent weight gain?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I don't do compensatory behaviors",
                "Less than once a week",
                "Once a week",
                "Twice a week", 
                "Three times a week",
                "Four or more times a week",
                "Daily or multiple times daily"
            ],
            required=False,
            criteria_weight=1.5,
            symptom_category="compensation_frequency"
        ),
        
        # Duration and persistence
        SCIDQuestion(
            id="ed_018",
            text="How long have you been having these eating problems?",
            simple_text="How long have you been dealing with these eating issues?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Less than 1 month",
                "1-3 months",
                "3-6 months",
                "6 months to 1 year",
                "1-2 years",
                "2-5 years",
                "More than 5 years"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="duration"
        ),
        
        # Distress and impairment
        SCIDQuestion(
            id="ed_019",
            text="Do your eating patterns cause you significant distress?",
            simple_text="Do your eating patterns make you very upset or worried?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=2.0,
            symptom_category="eating_distress"
        ),
        
        SCIDQuestion(
            id="ed_020",
            text="Have your eating patterns interfered with your life?",
            simple_text="Have your eating problems made it hard to do important things in your life?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Work or school performance",
                "Social activities and relationships",
                "Family relationships",
                "Physical health",
                "Daily activities and routine",
                "Overall quality of life",
                "My eating hasn't interfered with my life"
            ],
            required=True,
            criteria_weight=1.5,
            symptom_category="impairment_areas"
        ),
        
        # Food rules and restrictions
        SCIDQuestion(
            id="ed_021",
            text="Do you have strict rules about what, when, or how much you can eat?",
            simple_text="Do you have strict rules about your eating that you must follow?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="food_rules"
        ),
        
        SCIDQuestion(
            id="ed_022",
            text="What types of food rules do you follow?",
            simple_text="What kinds of eating rules do you have?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Avoiding certain types of food completely",
                "Eating only at specific times",
                "Limiting calories to a very low number",
                "Only eating 'safe' or 'good' foods",
                "Measuring or weighing all food",
                "Following rigid meal plans",
                "I don't have strict food rules"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="rule_types"
        ),
        
        # Body checking and weight monitoring
        SCIDQuestion(
            id="ed_023",
            text="Do you frequently check your body weight, shape, or size?",
            simple_text="Do you often weigh yourself or check how your body looks?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.0,
            symptom_category="body_checking"
        ),
        
        SCIDQuestion(
            id="ed_024",
            text="How often do you weigh yourself?",
            simple_text="How often do you step on a scale to check your weight?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "I avoid weighing myself",
                "Once a month or less",
                "Once a week",
                "2-3 times a week",
                "Daily",
                "Multiple times per day",
                "Constantly throughout the day"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="weighing_frequency"
        ),
        
        # Physical consequences
        SCIDQuestion(
            id="ed_025",
            text="Have you experienced any physical problems related to your eating patterns?",
            simple_text="Have you had any health problems because of how you eat?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Feeling weak or tired all the time",
                "Dizziness or fainting",
                "Hair loss or thinning",
                "Feeling cold all the time",
                "Dental problems from vomiting",
                "Irregular or stopped menstrual periods",
                "Digestive problems",
                "I haven't had physical problems"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="physical_consequences"
        ),
        
        # Social and occupational impact
        SCIDQuestion(
            id="ed_026",
            text="Do you avoid social situations that involve food?",
            simple_text="Do you stay away from social events where there will be food?",
            response_type=ResponseType.YES_NO,
            required=True,
            criteria_weight=1.5,
            symptom_category="social_avoidance"
        ),
        
        SCIDQuestion(
            id="ed_027",
            text="Which social situations do you avoid because of eating concerns?",
            simple_text="What social situations do you avoid because of worries about eating?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Restaurants and dining out",
                "Parties and celebrations",
                "Family meals and gatherings",
                "Work or school events with food",
                "Dating situations involving food",
                "Traveling where food choices are limited",
                "I don't avoid social situations"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="avoided_situations"
        ),
        
        # Treatment history and insight
        SCIDQuestion(
            id="ed_028",
            text="Do you believe you have an eating disorder?",
            simple_text="Do you think you have an eating disorder?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Yes, I believe I have an eating disorder",
                "I'm not sure but it's possible",
                "I don't think so, but others are concerned",
                "No, I don't have an eating disorder",
                "I'm confused about whether I have a problem"
            ],
            required=True,
            criteria_weight=1.0,
            symptom_category="insight_level"
        ),
        
        SCIDQuestion(
            id="ed_029",
            text="Have you received treatment for eating problems?",
            simple_text="Have you gotten help or treatment for eating problems?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "No, I haven't received treatment",
                "I'm currently in counseling/therapy",
                "I've had outpatient treatment in the past",
                "I've been hospitalized for eating problems",
                "I've tried treatment but it didn't help",
                "I'm considering getting help"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="treatment_history"
        ),
        
        # Current severity
        SCIDQuestion(
            id="ed_030",
            text="How would you rate the severity of your eating problems currently?",
            simple_text="How bad would you say your eating problems are right now?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No problems", "Mild problems", "Moderate problems", "Severe problems"],
            required=True,
            criteria_weight=1.0,
            symptom_category="current_severity"
        ),
        
        SCIDQuestion(
            id="ed_031",
            text="How much do your eating patterns interfere with your daily life?",
            simple_text="How much do your eating problems make it hard to do everyday things?",
            response_type=ResponseType.SCALE,
            scale_range=(0, 3),
            scale_labels=["No interference", "Mild interference", "Moderate interference", "Severe interference"],
            required=True,
            criteria_weight=1.5,
            symptom_category="daily_interference"
        ),
        
        # Exercise patterns
        SCIDQuestion(
            id="ed_032",
            text="Do you exercise excessively or compulsively?",
            simple_text="Do you feel like you have to exercise too much or can't stop exercising?",
            response_type=ResponseType.YES_NO,
            required=False,
            criteria_weight=1.0,
            symptom_category="excessive_exercise"
        ),
        
        SCIDQuestion(
            id="ed_033",
            text="How do you feel if you can't exercise as planned?",
            simple_text="How do you feel when you can't exercise like you planned to?",
            response_type=ResponseType.MULTIPLE_CHOICE,
            options=[
                "Very anxious or upset",
                "Guilty or bad about myself",
                "Worried I'll gain weight",
                "Like I need to eat less to make up for it",
                "It doesn't bother me much",
                "This doesn't apply to me"
            ],
            required=False,
            criteria_weight=1.0,
            symptom_category="exercise_distress"
        )
    ]
    
    # DSM-5 diagnostic criteria summary
    dsm_criteria = [
        "ANOREXIA NERVOSA:",
        "A. Restriction of energy intake leading to significantly low body weight",
        "B. Intense fear of gaining weight or persistent behavior preventing weight gain",
        "C. Disturbance in self-perceived weight/shape or lack of recognition of seriousness of low weight",
        "",
        "BULIMIA NERVOSA:", 
        "A. Recurrent binge eating episodes",
        "B. Recurrent compensatory behaviors to prevent weight gain",
        "C. Binge eating and compensatory behaviors occur at least once weekly for 3 months",
        "D. Self-evaluation unduly influenced by body shape and weight",
        "E. Disturbance does not occur exclusively during anorexia nervosa",
        "",
        "BINGE EATING DISORDER:",
        "A. Recurrent binge eating episodes with loss of control",
        "B. Binge episodes associated with distress and specific characteristics",
        "C. Occurs at least once weekly for 3 months",
        "D. Not associated with compensatory behaviors"
    ]
    
    # Severity thresholds
    severity_thresholds = {
        "mild": 0.4,      # Some symptoms with minimal impairment
        "moderate": 0.6,  # Clear symptoms with moderate impairment
        "severe": 0.8     # Severe symptoms with significant impairment
    }
    
    return SCIDModule(
        id="EATING_DISORDERS",
        name="Eating Disorders",
        description="Assessment module for Anorexia Nervosa, Bulimia Nervosa, and Binge Eating Disorder based on DSM-5 criteria",
        questions=questions,
        diagnostic_threshold=0.6,
        estimated_time_mins=25,
        dsm_criteria=dsm_criteria,
        severity_thresholds=severity_thresholds,
        category="eating_disorders", 
        version="1.0",
        clinical_notes="This module covers multiple eating disorders. Medical evaluation recommended for all positive cases due to potential physical health complications."
    )
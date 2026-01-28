from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from .tpa_schemas import TherapyType, SymptomSeverity, Intervention, InterventionLevel


class DisorderCategory(Enum):
    """DSM-5 disorder categories"""
    MOOD_DISORDERS = "mood_disorders"
    ANXIETY_DISORDERS = "anxiety_disorders"
    TRAUMA_STRESSOR_DISORDERS = "trauma_stressor_disorders"
    OBSESSIVE_COMPULSIVE_DISORDERS = "obsessive_compulsive_disorders"
    SUBSTANCE_USE_DISORDERS = "substance_use_disorders"
    EATING_DISORDERS = "eating_disorders"
    NEURODEVELOPMENTAL_DISORDERS = "neurodevelopmental_disorders"
    PERSONALITY_DISORDERS = "personality_disorders"
    PSYCHOTIC_DISORDERS = "psychotic_disorders"
    OTHER_DISORDERS = "other_disorders"

@dataclass
class DSMReference:
    """DSM-5 reference information"""
    dsm_section: str
    diagnostic_criteria: List[str]
    severity_specifiers: List[str]
    clinical_notes: str
    differential_diagnosis: List[str]

@dataclass
class DisorderSpecificGuidelines:
    """Treatment guidelines specific to a disorder"""
    disorder_id: str
    disorder_name: str
    dsm_reference: DSMReference
    first_line_interventions: List[str]
    second_line_interventions: List[str]
    adjunctive_interventions: List[str]
    contraindicated_interventions: List[str]
    monitoring_parameters: List[str]
    expected_timeline: str
    escalation_criteria: List[str]
    specialist_referral_criteria: List[str]

class TreatmentGuidelines:
    """
    Comprehensive evidence-based treatment guidelines for all SCID modules.
    Maps symptoms and severity to appropriate non-medication interventions.
    Includes DSM-5 references and disorder-specific guidelines.
    """
    
    def __init__(self):
        self.intervention_database = self._initialize_interventions()
        self.dsm_references = self._initialize_dsm_references()
        self.disorder_guidelines = self._initialize_disorder_guidelines()
        self.severity_guidelines = self._initialize_severity_guidelines()
        self.symptom_mapping = self._initialize_symptom_mapping()
    
    def _initialize_dsm_references(self) -> Dict[str, DSMReference]:
        """Initialize DSM-5 reference information for all disorders"""
        return {
            "MDD": DSMReference(
                dsm_section="Depressive Disorders",
                diagnostic_criteria=[
                    "Depressed mood most of the day, nearly every day",
                    "Markedly diminished interest or pleasure in activities",
                    "Significant weight loss/gain or appetite changes",
                    "Insomnia or hypersomnia nearly every day",
                    "Psychomotor agitation or retardation",
                    "Fatigue or loss of energy nearly every day",
                    "Feelings of worthlessness or inappropriate guilt",
                    "Diminished ability to think or concentrate",
                    "Recurrent thoughts of death or suicidal ideation"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe", "With psychotic features"],
                clinical_notes="Requires at least 5 symptoms for at least 2 weeks, with at least one being depressed mood or anhedonia.",
                differential_diagnosis=["Bipolar Disorder", "Persistent Depressive Disorder", "Adjustment Disorder", "Substance-Induced Depression"]
            ),
            "BIPOLAR": DSMReference(
                dsm_section="Bipolar and Related Disorders",
                diagnostic_criteria=[
                    "Distinct period of abnormally elevated, expansive, or irritable mood",
                    "Inflated self-esteem or grandiosity",
                    "Decreased need for sleep",
                    "More talkative than usual or pressure to keep talking",
                    "Flight of ideas or racing thoughts",
                    "Distractibility",
                    "Increase in goal-directed activity or psychomotor agitation",
                    "Excessive involvement in pleasurable activities with high potential for painful consequences"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe", "With psychotic features"],
                clinical_notes="Mania requires 1 week duration (or hospitalization). Hypomania requires 4 days.",
                differential_diagnosis=["Major Depressive Disorder", "Cyclothymic Disorder", "Substance-Induced Mood Disorder", "ADHD"]
            ),
            "GAD": DSMReference(
                dsm_section="Anxiety Disorders",
                diagnostic_criteria=[
                    "Excessive anxiety and worry occurring more days than not for at least 6 months",
                    "Difficult to control the worry",
                    "Restlessness or feeling keyed up or on edge",
                    "Easily fatigued",
                    "Difficulty concentrating or mind going blank",
                    "Irritability",
                    "Muscle tension",
                    "Sleep disturbance"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe"],
                clinical_notes="Requires excessive worry occurring more days than not for at least 6 months.",
                differential_diagnosis=["Panic Disorder", "Social Anxiety Disorder", "Depression", "Substance Use Disorder"]
            ),
            "PANIC": DSMReference(
                dsm_section="Anxiety Disorders",
                diagnostic_criteria=[
                    "Recurrent unexpected panic attacks",
                    "At least 1 month of concern about attacks",
                    "Worry about consequences of attacks",
                    "Significant change in behavior related to attacks"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe"],
                clinical_notes="Requires recurrent unexpected panic attacks with at least 1 month of concern about attacks.",
                differential_diagnosis=["Agoraphobia", "Social Anxiety Disorder", "Specific Phobia", "Medical conditions"]
            ),
            "PTSD": DSMReference(
                dsm_section="Trauma- and Stressor-Related Disorders",
                diagnostic_criteria=[
                    "Exposure to actual or threatened death, serious injury, or sexual violence",
                    "Intrusive memories, nightmares, or flashbacks",
                    "Avoidance of trauma-related stimuli",
                    "Negative alterations in cognition and mood",
                    "Marked alterations in arousal and reactivity"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe"],
                clinical_notes="Requires exposure to trauma plus symptoms from intrusion, avoidance, negative alterations, and arousal clusters.",
                differential_diagnosis=["Acute Stress Disorder", "Adjustment Disorder", "Major Depressive Disorder", "Anxiety Disorders"]
            ),
            "OCD": DSMReference(
                dsm_section="Obsessive-Compulsive and Related Disorders",
                diagnostic_criteria=[
                    "Presence of obsessions, compulsions, or both",
                    "Obsessions are recurrent and persistent thoughts, urges, or images",
                    "Compulsions are repetitive behaviors or mental acts",
                    "Obsessions or compulsions are time-consuming or cause significant distress"
                ],
                severity_specifiers=["Mild (1-3 hours/day)", "Moderate (3-8 hours/day)", "Severe (>8 hours/day)"],
                clinical_notes="Requires presence of obsessions, compulsions, or both that are time-consuming or cause significant distress.",
                differential_diagnosis=["Anxiety Disorders", "Depressive Disorders", "Psychotic Disorders", "Tic Disorders"]
            ),
            "ADHD": DSMReference(
                dsm_section="Neurodevelopmental Disorders",
                diagnostic_criteria=[
                    "Persistent pattern of inattention and/or hyperactivity-impulsivity",
                    "Several symptoms present before age 12",
                    "Several symptoms present in 2+ settings",
                    "Clear evidence symptoms interfere with functioning",
                    "Symptoms not better explained by another disorder"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe"],
                clinical_notes="Requires persistent pattern of inattention and/or hyperactivity-impulsivity that interferes with functioning.",
                differential_diagnosis=["Anxiety Disorders", "Mood Disorders", "Learning Disorders", "Substance Use Disorder"]
            ),
            "EATING_DISORDERS": DSMReference(
                dsm_section="Feeding and Eating Disorders",
                diagnostic_criteria=[
                    "Restriction of energy intake relative to requirements",
                    "Intense fear of gaining weight or becoming fat",
                    "Disturbance in way body weight or shape is experienced",
                    "Recurrent episodes of binge eating",
                    "Recurrent inappropriate compensatory behaviors"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe", "Extreme"],
                clinical_notes="Includes anorexia nervosa, bulimia nervosa, and binge-eating disorder.",
                differential_diagnosis=["Depression", "Anxiety Disorders", "OCD", "Medical conditions"]
            ),
            "SUBSTANCE_USE": DSMReference(
                dsm_section="Substance-Related and Addictive Disorders",
                diagnostic_criteria=[
                    "Substance taken in larger amounts or over longer period than intended",
                    "Persistent desire or unsuccessful efforts to cut down or control use",
                    "Great deal of time spent obtaining, using, or recovering from substance",
                    "Craving or strong desire/urge to use substance",
                    "Recurrent use resulting in failure to fulfill major obligations"
                ],
                severity_specifiers=["Mild (2-3 criteria)", "Moderate (4-5 criteria)", "Severe (6+ criteria)"],
                clinical_notes="Requires problematic pattern of substance use leading to clinically significant impairment or distress.",
                differential_diagnosis=["Depression", "Anxiety Disorders", "Bipolar Disorder", "Personality Disorders"]
            ),
            "PERSONALITY_DISORDERS": DSMReference(
                dsm_section="Personality Disorders",
                diagnostic_criteria=[
                    "Enduring pattern of inner experience and behavior",
                    "Pattern deviates markedly from cultural expectations",
                    "Pattern is pervasive and inflexible",
                    "Pattern leads to distress or impairment",
                    "Pattern is stable and of long duration"
                ],
                severity_specifiers=["Mild", "Moderate", "Severe"],
                clinical_notes="Personality disorders require pervasive, inflexible patterns that cause distress or impairment.",
                differential_diagnosis=["Mood Disorders", "Anxiety Disorders", "Psychotic Disorders", "Substance Use Disorders"]
            )
        }
    
    def _initialize_disorder_guidelines(self) -> Dict[str, DisorderSpecificGuidelines]:
        """Initialize disorder-specific treatment guidelines"""
        return {
            "MDD": DisorderSpecificGuidelines(
                disorder_id="MDD",
                disorder_name="Major Depressive Disorder",
                dsm_reference=self.dsm_references["MDD"],
                first_line_interventions=[
                    "cbt_cognitive_restructuring",
                    "interpersonal_therapy",
                    "behavioral_activation"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "exercise_therapy",
                    "social_support"
                ],
                adjunctive_interventions=[
                    "sleep_hygiene",
                    "journaling",
                    "psychoeducation"
                ],
                contraindicated_interventions=[
                    "cbt_exposure"  # Not appropriate for depression
                ],
                monitoring_parameters=[
                    "Mood scores (PHQ-9)",
                    "Sleep patterns",
                    "Social engagement",
                    "Suicidal ideation"
                ],
                expected_timeline="8-12 weeks for initial response",
                escalation_criteria=[
                    "No improvement after 6 weeks",
                    "Suicidal ideation",
                    "Severe functional impairment"
                ],
                specialist_referral_criteria=[
                    "Treatment-resistant depression",
                    "Bipolar features",
                    "Psychotic symptoms"
                ]
            ),
            "BIPOLAR": DisorderSpecificGuidelines(
                disorder_id="BIPOLAR",
                disorder_name="Bipolar Disorder",
                dsm_reference=self.dsm_references["BIPOLAR"],
                first_line_interventions=[
                    "psychoeducation",
                    "sleep_hypnotherapy",
                    "family_focused_therapy"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "social_rhythm_therapy",
                    "cognitive_remediation"
                ],
                adjunctive_interventions=[
                    "exercise_therapy",
                    "social_support",
                    "relaxation_techniques"
                ],
                contraindicated_interventions=[
                    "cbt_exposure",
                    "journaling"  # May trigger mood episodes
                ],
                monitoring_parameters=[
                    "Mood tracking",
                    "Sleep patterns",
                    "Energy levels",
                    "Risk-taking behavior"
                ],
                expected_timeline="Ongoing management",
                escalation_criteria=[
                    "Mania or hypomania",
                    "Severe depression",
                    "Suicidal ideation",
                    "Psychotic symptoms"
                ],
                specialist_referral_criteria=[
                    "First episode",
                    "Severe episodes",
                    "Treatment resistance"
                ]
            ),
            "GAD": DisorderSpecificGuidelines(
                disorder_id="GAD",
                disorder_name="Generalized Anxiety Disorder",
                dsm_reference=self.dsm_references["GAD"],
                first_line_interventions=[
                    "cbt_cognitive_restructuring",
                    "cbt_exposure",
                    "applied_relaxation"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "acceptance_commitment_therapy",
                    "progressive_muscle_relaxation"
                ],
                adjunctive_interventions=[
                    "exercise_therapy",
                    "sleep_hygiene",
                    "social_support"
                ],
                contraindicated_interventions=[
                    "journaling"  # May increase worry
                ],
                monitoring_parameters=[
                    "Anxiety levels (GAD-7)",
                    "Worry time",
                    "Physical symptoms",
                    "Functional impairment"
                ],
                expected_timeline="8-16 weeks for significant improvement",
                escalation_criteria=[
                    "No improvement after 8 weeks",
                    "Panic attacks",
                    "Severe functional impairment"
                ],
                specialist_referral_criteria=[
                    "Treatment resistance",
                    "Comorbid conditions",
                    "Severe impairment"
                ]
            ),
            "PANIC": DisorderSpecificGuidelines(
                disorder_id="PANIC",
                disorder_name="Panic Disorder",
                dsm_reference=self.dsm_references["PANIC"],
                first_line_interventions=[
                    "cbt_exposure",
                    "panic_control_treatment",
                    "breathing_retraining"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "progressive_muscle_relaxation",
                    "cognitive_restructuring"
                ],
                adjunctive_interventions=[
                    "exercise_therapy",
                    "sleep_hygiene",
                    "psychoeducation"
                ],
                contraindicated_interventions=[
                    "journaling"  # May trigger panic
                ],
                monitoring_parameters=[
                    "Panic attack frequency",
                    "Agoraphobic avoidance",
                    "Anxiety sensitivity",
                    "Functional impairment"
                ],
                expected_timeline="8-16 weeks for panic control",
                escalation_criteria=[
                    "Frequent panic attacks",
                    "Severe agoraphobia",
                    "Suicidal ideation"
                ],
                specialist_referral_criteria=[
                    "Severe agoraphobia",
                    "Treatment resistance",
                    "Comorbid conditions"
                ]
            ),
            "PTSD": DisorderSpecificGuidelines(
                disorder_id="PTSD",
                disorder_name="Posttraumatic Stress Disorder",
                dsm_reference=self.dsm_references["PTSD"],
                first_line_interventions=[
                    "prolonged_exposure_therapy",
                    "cognitive_processing_therapy",
                    "eye_movement_desensitization"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "narrative_exposure_therapy",
                    "trauma_focused_cbt"
                ],
                adjunctive_interventions=[
                    "exercise_therapy",
                    "social_support",
                    "psychoeducation"
                ],
                contraindicated_interventions=[
                    "journaling"  # May trigger trauma memories
                ],
                monitoring_parameters=[
                    "PTSD symptoms (PCL-5)",
                    "Sleep quality",
                    "Flashback frequency",
                    "Functional impairment"
                ],
                expected_timeline="12-20 weeks for significant improvement",
                escalation_criteria=[
                    "No improvement after 8 weeks",
                    "Suicidal ideation",
                    "Severe dissociation"
                ],
                specialist_referral_criteria=[
                    "Complex PTSD",
                    "Treatment resistance",
                    "Comorbid conditions"
                ]
            ),
            "OCD": DisorderSpecificGuidelines(
                disorder_id="OCD",
                disorder_name="Obsessive-Compulsive Disorder",
                dsm_reference=self.dsm_references["OCD"],
                first_line_interventions=[
                    "exposure_response_prevention",
                    "cbt_cognitive_restructuring",
                    "acceptance_commitment_therapy"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "cbt_exposure",
                    "psychoeducation"
                ],
                adjunctive_interventions=[
                    "psychoeducation",
                    "social_support",
                    "relaxation_techniques"
                ],
                contraindicated_interventions=[
                    "journaling"  # May reinforce obsessions
                ],
                monitoring_parameters=[
                    "OCD severity (Y-BOCS)",
                    "Compulsion time",
                    "Distress levels",
                    "Functional impairment"
                ],
                expected_timeline="12-20 weeks for significant improvement",
                escalation_criteria=[
                    "No improvement after 12 weeks",
                    "Severe functional impairment",
                    "Suicidal ideation"
                ],
                specialist_referral_criteria=[
                    "Treatment resistance",
                    "Severe OCD",
                    "Comorbid conditions"
                ]
            ),
            "ADHD": DisorderSpecificGuidelines(
                disorder_id="ADHD",
                disorder_name="Attention-Deficit/Hyperactivity Disorder",
                dsm_reference=self.dsm_references["ADHD"],
                first_line_interventions=[
                    "behavioral_therapy",
                    "cognitive_behavioral_therapy",
                    "parent_training"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "exercise_therapy",
                    "organizational_skills_training"
                ],
                adjunctive_interventions=[
                    "sleep_hygiene",
                    "social_skills_training",
                    "psychoeducation"
                ],
                contraindicated_interventions=[
                    "cbt_exposure"  # Not appropriate for ADHD
                ],
                monitoring_parameters=[
                    "ADHD symptoms (ADHD-RS)",
                    "Academic/work performance",
                    "Social functioning",
                    "Organization skills"
                ],
                expected_timeline="Ongoing management",
                escalation_criteria=[
                    "No improvement after 12 weeks",
                    "Severe functional impairment",
                    "Comorbid conditions"
                ],
                specialist_referral_criteria=[
                    "Complex ADHD",
                    "Treatment resistance",
                    "Comorbid conditions"
                ]
            ),
            "EATING_DISORDERS": DisorderSpecificGuidelines(
                disorder_id="EATING_DISORDERS",
                disorder_name="Eating Disorders",
                dsm_reference=self.dsm_references["EATING_DISORDERS"],
                first_line_interventions=[
                    "family_based_therapy",
                    "cognitive_behavioral_therapy",
                    "dialectical_behavior_therapy"
                ],
                second_line_interventions=[
                    "interpersonal_therapy",
                    "acceptance_commitment_therapy",
                    "mindfulness_meditation"
                ],
                adjunctive_interventions=[
                    "nutritional_counseling",
                    "body_image_work",
                    "social_support"
                ],
                contraindicated_interventions=[
                    "journaling"  # May reinforce disordered thoughts
                ],
                monitoring_parameters=[
                    "Weight and BMI",
                    "Eating behaviors",
                    "Body image concerns",
                    "Medical complications"
                ],
                expected_timeline="6-12 months for significant improvement",
                escalation_criteria=[
                    "Rapid weight loss",
                    "Medical complications",
                    "Suicidal ideation"
                ],
                specialist_referral_criteria=[
                    "Severe eating disorders",
                    "Medical complications",
                    "Treatment resistance"
                ]
            ),
            "SUBSTANCE_USE": DisorderSpecificGuidelines(
                disorder_id="SUBSTANCE_USE",
                disorder_name="Substance Use Disorder",
                dsm_reference=self.dsm_references["SUBSTANCE_USE"],
                first_line_interventions=[
                    "motivational_interviewing",
                    "cognitive_behavioral_therapy",
                    "contingency_management"
                ],
                second_line_interventions=[
                    "mindfulness_meditation",
                    "acceptance_commitment_therapy",
                    "relapse_prevention"
                ],
                adjunctive_interventions=[
                    "12_step_programs",
                    "family_therapy",
                    "social_support"
                ],
                contraindicated_interventions=[
                    "journaling"  # May trigger cravings
                ],
                monitoring_parameters=[
                    "Substance use frequency",
                    "Cravings intensity",
                    "Triggers identification",
                    "Relapse risk"
                ],
                expected_timeline="Ongoing management",
                escalation_criteria=[
                    "Continued substance use",
                    "Overdose risk",
                    "Legal problems"
                ],
                specialist_referral_criteria=[
                    "Severe addiction",
                    "Medical complications",
                    "Treatment resistance"
                ]
            ),
            "PERSONALITY_DISORDERS": DisorderSpecificGuidelines(
                disorder_id="PERSONALITY_DISORDERS",
                disorder_name="Personality Disorders",
                dsm_reference=self.dsm_references["PERSONALITY_DISORDERS"],
                first_line_interventions=[
                    "dialectical_behavior_therapy",
                    "mentalization_based_therapy",
                    "transference_focused_therapy"
                ],
                second_line_interventions=[
                    "schema_therapy",
                    "acceptance_commitment_therapy",
                    "mindfulness_meditation"
                ],
                adjunctive_interventions=[
                    "social_skills_training",
                    "emotion_regulation_skills",
                    "psychoeducation"
                ],
                contraindicated_interventions=[
                    "cbt_exposure"  # May be overwhelming
                ],
                monitoring_parameters=[
                    "Interpersonal functioning",
                    "Emotion regulation",
                    "Impulse control",
                    "Quality of life"
                ],
                expected_timeline="1-3 years for significant improvement",
                escalation_criteria=[
                    "Self-harm behavior",
                    "Suicidal ideation",
                    "Severe interpersonal problems"
                ],
                specialist_referral_criteria=[
                    "Severe personality disorders",
                    "Treatment resistance",
                    "Comorbid conditions"
                ]
            )
        }
    
    def _initialize_interventions(self) -> Dict[str, Intervention]:
        """Initialize the comprehensive database of evidence-based interventions"""
        return {
            # CBT Interventions
            "cbt_cognitive_restructuring": Intervention(
                name="Cognitive Behavioral Therapy - Cognitive Restructuring",
                type=TherapyType.CBT,
                description="Identify and challenge negative thought patterns to improve mood and behavior",
                evidence_level="Strong evidence for depression, anxiety, and PTSD",
                duration="8-12 weeks",
                frequency="Weekly sessions",
                resources_needed=["CBT workbook", "Thought record worksheets", "Therapist or guided app"],
                contraindications=["Active psychosis", "Severe cognitive impairment"]
            ),
            "cbt_exposure": Intervention(
                name="CBT Exposure Therapy",
                type=TherapyType.CBT,
                description="Gradual exposure to feared situations to reduce anxiety and avoidance",
                evidence_level="Strong evidence for phobias, OCD, and anxiety disorders",
                duration="8-16 weeks",
                frequency="Weekly sessions with daily practice",
                resources_needed=["Exposure hierarchy worksheet", "Therapist guidance", "Safe practice environment"],
                contraindications=["Unstable medical conditions", "Severe depression with suicidal ideation"]
            ),
            "behavioral_activation": Intervention(
                name="Behavioral Activation",
                type=TherapyType.CBT,
                description="Increase engagement in positive activities to improve mood and reduce depression",
                evidence_level="Strong evidence for depression",
                duration="8-12 weeks",
                frequency="Weekly sessions with daily practice",
                resources_needed=["Activity scheduling worksheets", "Therapist guidance", "Goal setting tools"],
                contraindications=["Severe depression with suicidal ideation", "Active psychosis"]
            ),
            "interpersonal_therapy": Intervention(
                name="Interpersonal Therapy",
                type=TherapyType.CBT,
                description="Focus on interpersonal relationships and social functioning to improve mood",
                evidence_level="Strong evidence for depression",
                duration="12-16 weeks",
                frequency="Weekly sessions",
                resources_needed=["Therapist guidance", "Relationship assessment tools", "Communication skills training"],
                contraindications=["Severe cognitive impairment", "Active psychosis"]
            ),
            
            # Mindfulness and Acceptance Interventions
            "mindfulness_meditation": Intervention(
                name="Mindfulness Meditation",
                type=TherapyType.MINDFULNESS,
                description="Present-moment awareness practice to reduce stress and improve emotional regulation",
                evidence_level="Strong evidence for stress reduction, moderate for depression and anxiety",
                duration="Ongoing practice",
                frequency="Daily 10-20 minute sessions",
                resources_needed=["Meditation app or guided recordings", "Quiet space", "Timer"],
                contraindications=["Active psychosis", "Severe dissociation"]
            ),
            "acceptance_commitment_therapy": Intervention(
                name="Acceptance and Commitment Therapy",
                type=TherapyType.ACT,
                description="Accept difficult thoughts and feelings while committing to value-based actions",
                evidence_level="Strong evidence for depression, anxiety, and chronic pain",
                duration="8-12 weeks",
                frequency="Weekly sessions",
                resources_needed=["ACT workbook", "Values clarification exercises", "Therapist guidance"],
                contraindications=["Severe cognitive impairment", "Active psychosis"]
            ),
            
            # Specialized Therapies
            "dialectical_behavior_therapy": Intervention(
                name="Dialectical Behavior Therapy Skills",
                type=TherapyType.DBT,
                description="Skills training in mindfulness, distress tolerance, emotion regulation, and interpersonal effectiveness",
                evidence_level="Strong evidence for borderline personality disorder, moderate for other conditions",
                duration="6-12 months",
                frequency="Weekly group sessions + daily practice",
                resources_needed=["DBT skills manual", "Group therapy", "Daily practice worksheets"],
                contraindications=["Severe cognitive impairment", "Active substance abuse"]
            ),
            "prolonged_exposure_therapy": Intervention(
                name="Prolonged Exposure Therapy",
                type=TherapyType.CBT,
                description="Systematic exposure to trauma memories to reduce PTSD symptoms",
                evidence_level="Strong evidence for PTSD",
                duration="8-15 weeks",
                frequency="Weekly sessions with daily practice",
                resources_needed=["Therapist guidance", "Trauma narrative tools", "Safe environment"],
                contraindications=["Unstable medical conditions", "Active psychosis", "Severe dissociation"]
            ),
            "exposure_response_prevention": Intervention(
                name="Exposure Response Prevention",
                type=TherapyType.CBT,
                description="Exposure to obsessions while preventing compulsions to treat OCD",
                evidence_level="Strong evidence for OCD",
                duration="12-20 weeks",
                frequency="Weekly sessions with daily practice",
                resources_needed=["Therapist guidance", "Exposure hierarchy", "Response prevention tools"],
                contraindications=["Severe depression with suicidal ideation", "Active psychosis"]
            ),
            
            # Behavioral and Lifestyle Interventions
            "sleep_hypnotherapy": Intervention(
                name="Sleep Hypnotherapy",
                type=TherapyType.SLEEP_HYGIENE,
                description="Hypnotic techniques to improve sleep quality and regulate sleep patterns",
                evidence_level="Moderate evidence for insomnia and sleep disorders",
                duration="4-8 weeks",
                frequency="Weekly sessions with daily practice",
                resources_needed=["Hypnotherapist", "Audio recordings", "Sleep diary"],
                contraindications=["Severe sleep apnea", "Narcolepsy", "Active psychosis"]
            ),
            "exercise_therapy": Intervention(
                name="Exercise Therapy",
                type=TherapyType.EXERCISE,
                description="Regular physical activity to improve mood, reduce anxiety, and enhance well-being",
                evidence_level="Strong evidence for depression, moderate for anxiety",
                duration="Ongoing",
                frequency="3-5 times per week, 30-60 minutes",
                resources_needed=["Exercise plan", "Comfortable clothing", "Safe exercise environment"],
                contraindications=["Unstable medical conditions", "Severe physical limitations"]
            ),
            "social_rhythm_therapy": Intervention(
                name="Social Rhythm Therapy",
                type=TherapyType.PSYCHOEDUCATION,
                description="Regularize daily routines and social rhythms to stabilize mood in bipolar disorder",
                evidence_level="Moderate evidence for bipolar disorder",
                duration="Ongoing",
                frequency="Weekly sessions initially, then monthly",
                resources_needed=["Daily routine planner", "Social rhythm tracking", "Therapist guidance"],
                contraindications=["Severe mania", "Active psychosis"]
            ),
            
            # Additional Interventions
            "journaling": Intervention(
                name="Therapeutic Journaling",
                type=TherapyType.JOURNALING,
                description="Structured writing to process emotions, track progress, and gain insights",
                evidence_level="Moderate evidence for emotional processing and stress reduction",
                duration="Ongoing practice",
                frequency="Daily or as needed",
                resources_needed=["Journal or digital app", "Writing prompts", "Private space"],
                contraindications=["Severe dissociation", "Trauma-related writing triggers"]
            ),
            "social_support": Intervention(
                name="Social Support Enhancement",
                type=TherapyType.SOCIAL_SUPPORT,
                description="Building and strengthening supportive relationships and social connections",
                evidence_level="Strong evidence for depression and general well-being",
                duration="Ongoing",
                frequency="Regular social interactions",
                resources_needed=["Social skills training", "Community resources", "Support groups"],
                contraindications=["Abusive relationships", "Severe social anxiety without support"]
            ),
            "relaxation_techniques": Intervention(
                name="Progressive Muscle Relaxation",
                type=TherapyType.RELAXATION_TECHNIQUES,
                description="Systematic tensing and relaxing of muscle groups to reduce physical tension",
                evidence_level="Strong evidence for anxiety and stress reduction",
                duration="Ongoing practice",
                frequency="Daily practice, 10-15 minutes",
                resources_needed=["Quiet space", "Audio guidance", "Comfortable position"],
                contraindications=["Severe muscle conditions", "Active psychosis"]
            ),
            "psychoeducation": Intervention(
                name="Mental Health Psychoeducation",
                type=TherapyType.PSYCHOEDUCATION,
                description="Education about mental health conditions, treatment options, and coping strategies",
                evidence_level="Strong evidence for improving treatment adherence and outcomes",
                duration="Ongoing learning",
                frequency="As needed",
                resources_needed=["Educational materials", "Reliable sources", "Professional guidance"],
                contraindications=["Severe cognitive impairment"]
            )
        }
    
    def _initialize_severity_guidelines(self) -> Dict[SymptomSeverity, Dict[str, Any]]:
        """Guidelines for intervention selection based on severity"""
        return {
            SymptomSeverity.MILD: {
                "primary_level": InterventionLevel.SELF_HELP,
                "complementary_level": InterventionLevel.GUIDED_SELF_HELP,
                "duration": "4-8 weeks",
                "follow_up": "Monthly check-ins",
                "escalation_criteria": ["No improvement after 4 weeks", "Symptom worsening"]
            },
            SymptomSeverity.MODERATE: {
                "primary_level": InterventionLevel.GUIDED_SELF_HELP,
                "complementary_level": InterventionLevel.THERAPY,
                "duration": "8-16 weeks",
                "follow_up": "Bi-weekly check-ins",
                "escalation_criteria": ["No improvement after 6 weeks", "Functional impairment", "Safety concerns"]
            },
            SymptomSeverity.SEVERE: {
                "primary_level": InterventionLevel.THERAPY,
                "complementary_level": InterventionLevel.SPECIALIST_REFERRAL,
                "duration": "16+ weeks",
                "follow_up": "Weekly monitoring",
                "escalation_criteria": ["Immediate safety concerns", "No improvement after 4 weeks", "Functional impairment"]
            }
        }
    
    # Public Methods for Accessing Guidelines
    
    def get_disorder_guidelines(self, disorder_id: str) -> Optional[DisorderSpecificGuidelines]:
        """Get comprehensive treatment guidelines for a specific disorder"""
        return self.disorder_guidelines.get(disorder_id.upper())
    
    def get_dsm_reference(self, disorder_id: str) -> Optional[DSMReference]:
        """Get DSM-5 reference information for a disorder"""
        return self.dsm_references.get(disorder_id.upper())
    
    def get_interventions_for_disorder(
        self, 
        disorder_id: str, 
        severity: SymptomSeverity,
        intervention_line: str = "first_line"
    ) -> List[Intervention]:
        """Get appropriate interventions for a specific disorder and severity"""
        guidelines = self.get_disorder_guidelines(disorder_id)
        if not guidelines:
            return []
        
        # Select intervention line based on severity and preference
        if intervention_line == "first_line":
            intervention_names = guidelines.first_line_interventions
        elif intervention_line == "second_line":
            intervention_names = guidelines.second_line_interventions
        elif intervention_line == "adjunctive":
            intervention_names = guidelines.adjunctive_interventions
        else:
            intervention_names = guidelines.first_line_interventions
        
        # Filter interventions based on severity appropriateness
        interventions = []
        for intervention_name in intervention_names:
            if intervention_name in self.intervention_database:
                intervention = self.intervention_database[intervention_name]
                if self._is_intervention_appropriate(intervention, severity, disorder_id):
                    interventions.append(intervention)
        
        return interventions
    
    def get_comprehensive_treatment_plan(
        self, 
        disorder_id: str, 
        severity: SymptomSeverity
    ) -> Dict[str, Any]:
        """Get a comprehensive treatment plan for a disorder"""
        guidelines = self.get_disorder_guidelines(disorder_id)
        dsm_ref = self.get_dsm_reference(disorder_id)
        severity_guide = self.get_severity_guidelines(severity)
        
        if not guidelines or not dsm_ref:
            return {}
        
        return {
            "disorder_info": {
                "id": guidelines.disorder_id,
                "name": guidelines.disorder_name,
                "dsm_reference": dsm_ref.dsm_section
            },
            "treatment_approach": {
                "first_line": self.get_interventions_for_disorder(disorder_id, severity, "first_line"),
                "second_line": self.get_interventions_for_disorder(disorder_id, severity, "second_line"),
                "adjunctive": self.get_interventions_for_disorder(disorder_id, severity, "adjunctive")
            },
            "monitoring": {
                "parameters": guidelines.monitoring_parameters,
                "timeline": guidelines.expected_timeline,
                "escalation_criteria": guidelines.escalation_criteria
            },
            "severity_guidelines": severity_guide,
            "specialist_referral": guidelines.specialist_referral_criteria
        }
    
    def get_interventions_for_symptoms(
        self, 
        symptom_clusters: List[str], 
        severity: SymptomSeverity
    ) -> List[Intervention]:
        """Get appropriate interventions for given symptoms and severity (backward compatibility)"""
        # Map symptom clusters to disorder IDs
        symptom_to_disorder = {
            "depression": "MDD",
            "anxiety": "GAD",
            "insomnia": "MDD",  # Often comorbid with depression
            "ocd": "OCD",
            "ptsd": "PTSD",
            "adhd": "ADHD",
            "bipolar": "BIPOLAR",
            "personality_disorders": "PERSONALITY_DISORDERS"
        }
        
        interventions = []
        for cluster in symptom_clusters:
            disorder_id = symptom_to_disorder.get(cluster.lower())
            if disorder_id:
                cluster_interventions = self.get_interventions_for_disorder(disorder_id, severity)
                interventions.extend(cluster_interventions)
        
        # Remove duplicates
        seen_names = set()
        unique_interventions = []
        for intervention in interventions:
            if intervention.name not in seen_names:
                seen_names.add(intervention.name)
                unique_interventions.append(intervention)
        
        return unique_interventions
    
    def _is_intervention_appropriate(
        self, 
        intervention: Intervention, 
        severity: SymptomSeverity,
        disorder_id: Optional[str] = None
    ) -> bool:
        """Check if intervention is appropriate for given severity level and disorder"""
        # Some interventions are not suitable for severe cases without professional supervision
        if severity == SymptomSeverity.SEVERE:
            contraindicated_for_severe = [
                "journaling",  # May trigger overwhelming emotions
                "cbt_exposure",  # Requires professional supervision
                "dbt_skills"  # Complex, requires group setting
            ]
            if any(contraindicated in intervention.name.lower() for contraindicated in contraindicated_for_severe):
                return False
        
        # Check disorder-specific contraindications
        if disorder_id and disorder_id in self.disorder_guidelines:
            guidelines = self.disorder_guidelines[disorder_id]
            if intervention.name.lower() in [name.lower() for name in guidelines.contraindicated_interventions]:
                return False
        
        return True
    
    def get_severity_guidelines(self, severity: SymptomSeverity) -> Dict[str, Any]:
        """Get treatment guidelines for specific severity level"""
        return self.severity_guidelines.get(severity, self.severity_guidelines[SymptomSeverity.MILD])
    
    def get_intervention_by_name(self, name: str) -> Optional[Intervention]:
        """Get intervention by name"""
        return self.intervention_database.get(name)
    
    def get_all_interventions(self) -> List[Intervention]:
        """Get all available interventions"""
        return list(self.intervention_database.values())
    
    def get_interventions_by_type(self, therapy_type: TherapyType) -> List[Intervention]:
        """Get all interventions of a specific type"""
        return [
            intervention for intervention in self.intervention_database.values()
            if intervention.type == therapy_type
        ]
    
    def get_evidence_based_interventions(self, condition: str) -> List[Intervention]:
        """Get evidence-based interventions for specific conditions"""
        # Try to map condition to disorder ID
        condition_mapping = {
            "depression": "MDD",
            "anxiety": "GAD",
            "bipolar": "BIPOLAR",
            "ptsd": "PTSD",
            "ocd": "OCD",
            "adhd": "ADHD",
            "eating_disorder": "EATING_DISORDERS",
            "substance_use": "SUBSTANCE_USE",
            "personality_disorder": "PERSONALITY_DISORDERS"
        }
        
        disorder_id = condition_mapping.get(condition.lower())
        if disorder_id:
            return self.get_interventions_for_disorder(disorder_id, SymptomSeverity.MODERATE)
        
        # Fallback to symptom-based mapping
        if condition.lower() in self.symptom_mapping:
            intervention_names = self.symptom_mapping[condition.lower()]
            return [
                self.intervention_database[name] 
                for name in intervention_names 
                if name in self.intervention_database
            ]
        return []
    
    def get_all_disorder_guidelines(self) -> Dict[str, DisorderSpecificGuidelines]:
        """Get all available disorder-specific guidelines"""
        return self.disorder_guidelines.copy()
    
    def get_guidelines_by_category(self, category: DisorderCategory) -> Dict[str, DisorderSpecificGuidelines]:
        """Get guidelines for disorders in a specific category"""
        category_mapping = {
            DisorderCategory.MOOD_DISORDERS: ["MDD", "BIPOLAR"],
            DisorderCategory.ANXIETY_DISORDERS: ["GAD", "PANIC", "SOCIAL_ANXIETY", "SPECIFIC_PHOBIA", "AGORAPHOBIA"],
            DisorderCategory.TRAUMA_STRESSOR_DISORDERS: ["PTSD", "ADJUSTMENT_DISORDER"],
            DisorderCategory.OBSESSIVE_COMPULSIVE_DISORDERS: ["OCD"],
            DisorderCategory.SUBSTANCE_USE_DISORDERS: ["SUBSTANCE_USE", "ALCOHOL_USE"],
            DisorderCategory.EATING_DISORDERS: ["EATING_DISORDERS"],
            DisorderCategory.NEURODEVELOPMENTAL_DISORDERS: ["ADHD"],
            DisorderCategory.PERSONALITY_DISORDERS: ["PERSONALITY_DISORDERS"],
            DisorderCategory.PSYCHOTIC_DISORDERS: ["PSYCHOTIC_DISORDERS"],
            DisorderCategory.OTHER_DISORDERS: ["ADJUSTMENT_DISORDER"]
        }
        
        disorder_ids = category_mapping.get(category, [])
        return {
            disorder_id: self.disorder_guidelines[disorder_id]
            for disorder_id in disorder_ids
            if disorder_id in self.disorder_guidelines
        }
    
    def search_interventions(self, search_term: str) -> List[Intervention]:
        """Search interventions by name or description"""
        search_term_lower = search_term.lower()
        matching_interventions = []
        
        for intervention in self.intervention_database.values():
            if (search_term_lower in intervention.name.lower() or 
                search_term_lower in intervention.description.lower()):
                matching_interventions.append(intervention)
        
        return matching_interventions
    
    def get_interventions_by_evidence_level(self, evidence_level: str) -> List[Intervention]:
        """Get interventions with a specific evidence level"""
        evidence_level_lower = evidence_level.lower()
        return [
            intervention for intervention in self.intervention_database.values()
            if evidence_level_lower in intervention.evidence_level.lower()
        ]
    
    def validate_intervention_combination(self, interventions: List[Intervention]) -> Dict[str, Any]:
        """Validate if combination of interventions is appropriate"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "conflicts": [],
            "recommendations": []
        }
        
        # Check for potential conflicts
        therapy_types = [intervention.type for intervention in interventions]
        if len(set(therapy_types)) < len(therapy_types):
            validation_result["warnings"].append("Multiple interventions of same type may be redundant")
        
        # Check for complementary interventions
        has_cbt = any(intervention.type == TherapyType.CBT for intervention in interventions)
        has_mindfulness = any(intervention.type == TherapyType.MINDFULNESS for intervention in interventions)
        
        if has_cbt and not has_mindfulness:
            validation_result["recommendations"].append("Consider adding mindfulness to complement CBT")
        
        if len(interventions) > 5:
            validation_result["warnings"].append("Too many interventions may reduce effectiveness")
            validation_result["recommendations"].append("Focus on 3-4 core interventions")
        
        # Check for contraindicated combinations
        contraindicated_combinations = [
            (["cbt_exposure", "journaling"], "Exposure therapy with journaling may be overwhelming"),
            (["dbt_skills", "cbt_exposure"], "DBT skills with exposure may conflict"),
            (["sleep_hypnotherapy", "cbt_exposure"], "Sleep therapy with exposure may interfere")
        ]
        
        for combo, reason in contraindicated_combinations:
            intervention_names = [intervention.name.lower() for intervention in interventions]
            if all(name in intervention_names for name in combo):
                validation_result["conflicts"].append(f"Contraindicated combination: {reason}")
                validation_result["is_valid"] = False
        
        return validation_result
    
    def generate_treatment_summary(self, disorder_id: str, severity: SymptomSeverity) -> str:
        """Generate a human-readable treatment summary for a disorder"""
        guidelines = self.get_disorder_guidelines(disorder_id)
        dsm_ref = self.get_dsm_reference(disorder_id)
        
        if not guidelines or not dsm_ref:
            return f"No treatment guidelines available for {disorder_id}"
        
        summary_lines = [
            f"TREATMENT GUIDELINES FOR {guidelines.disorder_name.upper()}",
            "=" * 60,
            "",
            f"DSM-5 Section: {dsm_ref.dsm_section}",
            f"Severity Level: {severity.value.upper()}",
            "",
            "FIRST-LINE INTERVENTIONS:",
            "-" * 25
        ]
        
        # Add first-line interventions
        first_line = self.get_interventions_for_disorder(disorder_id, severity, "first_line")
        for intervention in first_line:
            summary_lines.append(f"• {intervention.name}")
            summary_lines.append(f"  - {intervention.description}")
            summary_lines.append(f"  - Duration: {intervention.duration}")
            summary_lines.append(f"  - Evidence: {intervention.evidence_level}")
            summary_lines.append("")
        
        summary_lines.extend([
            "SECOND-LINE INTERVENTIONS:",
            "-" * 25
        ])
        
        # Add second-line interventions
        second_line = self.get_interventions_for_disorder(disorder_id, severity, "second_line")
        for intervention in second_line:
            summary_lines.append(f"• {intervention.name}")
            summary_lines.append(f"  - {intervention.description}")
            summary_lines.append("")
        
        summary_lines.extend([
            "MONITORING PARAMETERS:",
            "-" * 25
        ])
        
        for param in guidelines.monitoring_parameters:
            summary_lines.append(f"• {param}")
        
        summary_lines.extend([
            "",
            f"EXPECTED TIMELINE: {guidelines.expected_timeline}",
            "",
            "ESCALATION CRITERIA:",
            "-" * 25
        ])
        
        for criterion in guidelines.escalation_criteria:
            summary_lines.append(f"• {criterion}")
        
        summary_lines.extend([
            "",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])
        
        return "\n".join(summary_lines)
    
    def export_guidelines_as_json(self, disorder_id: Optional[str] = None) -> str:
        """Export treatment guidelines as JSON"""
        import json
        
        if disorder_id:
            # Export specific disorder guidelines
            guidelines = self.get_disorder_guidelines(disorder_id)
            dsm_ref = self.get_dsm_reference(disorder_id)
            
            if not guidelines or not dsm_ref:
                return json.dumps({"error": f"No guidelines found for {disorder_id}"})
            
            export_data = {
                "disorder_id": disorder_id,
                "guidelines": {
                    "disorder_name": guidelines.disorder_name,
                    "dsm_reference": {
                        "section": dsm_ref.dsm_section,
                        "diagnostic_criteria": dsm_ref.diagnostic_criteria,
                        "severity_specifiers": dsm_ref.severity_specifiers,
                        "clinical_notes": dsm_ref.clinical_notes,
                        "differential_diagnosis": dsm_ref.differential_diagnosis
                    },
                    "interventions": {
                        "first_line": guidelines.first_line_interventions,
                        "second_line": guidelines.second_line_interventions,
                        "adjunctive": guidelines.adjunctive_interventions,
                        "contraindicated": guidelines.contraindicated_interventions
                    },
                    "monitoring": {
                        "parameters": guidelines.monitoring_parameters,
                        "timeline": guidelines.expected_timeline,
                        "escalation_criteria": guidelines.escalation_criteria,
                        "specialist_referral": guidelines.specialist_referral_criteria
                    }
                }
            }
        else:
            # Export all guidelines
            export_data = {
                "all_guidelines": {},
                "interventions": {},
                "dsm_references": {}
            }
            
            for disorder_id, guidelines in self.disorder_guidelines.items():
                export_data["all_guidelines"][disorder_id] = {
                    "disorder_name": guidelines.disorder_name,
                    "first_line_interventions": guidelines.first_line_interventions,
                    "second_line_interventions": guidelines.second_line_interventions,
                    "adjunctive_interventions": guidelines.adjunctive_interventions,
                    "contraindicated_interventions": guidelines.contraindicated_interventions,
                    "monitoring_parameters": guidelines.monitoring_parameters,
                    "expected_timeline": guidelines.expected_timeline,
                    "escalation_criteria": guidelines.escalation_criteria,
                    "specialist_referral_criteria": guidelines.specialist_referral_criteria
                }
            
            for disorder_id, dsm_ref in self.dsm_references.items():
                export_data["dsm_references"][disorder_id] = {
                    "dsm_section": dsm_ref.dsm_section,
                    "diagnostic_criteria": dsm_ref.diagnostic_criteria,
                    "severity_specifiers": dsm_ref.severity_specifiers,
                    "clinical_notes": dsm_ref.clinical_notes,
                    "differential_diagnosis": dsm_ref.differential_diagnosis
                }
            
            for intervention_id, intervention in self.intervention_database.items():
                export_data["interventions"][intervention_id] = {
                    "name": intervention.name,
                    "type": intervention.type.value,
                    "description": intervention.description,
                    "evidence_level": intervention.evidence_level,
                    "duration": intervention.duration,
                    "frequency": intervention.frequency,
                    "resources_needed": intervention.resources_needed,
                    "contraindications": intervention.contraindications
                }
        
        return json.dumps(export_data, indent=2)
    
    def _initialize_symptom_mapping(self) -> Dict[str, List[str]]:
        """Map symptom clusters to appropriate interventions (backward compatibility)"""
        return {
            "depression": [
                "cbt_cognitive_restructuring",
                "mindfulness_meditation",
                "exercise_therapy",
                "social_support",
                "journaling",
                "psychoeducation"
            ],
            "anxiety": [
                "cbt_exposure",
                "mindfulness_meditation",
                "relaxation_techniques",
                "cbt_cognitive_restructuring",
                "exercise_therapy",
                "psychoeducation"
            ],
            "insomnia": [
                "sleep_hypnotherapy",
                "mindfulness_meditation",
                "relaxation_techniques",
                "cbt_cognitive_restructuring"
            ],
            "ocd": [
                "exposure_response_prevention",
                "mindfulness_meditation",
                "cbt_cognitive_restructuring"
            ],
            "ptsd": [
                "prolonged_exposure_therapy",
                "mindfulness_meditation",
                "relaxation_techniques",
                "psychoeducation"
            ],
            "adhd": [
                "mindfulness_meditation",
                "exercise_therapy",
                "psychoeducation",
                "social_support"
            ],
            "bipolar": [
                "mindfulness_meditation",
                "sleep_hypnotherapy",
                "psychoeducation",
                "social_support"
            ],
            "personality_disorders": [
                "dialectical_behavior_therapy",
                "mindfulness_meditation",
                "social_support",
                "psychoeducation"
            ]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the treatment guidelines system"""
        total_disorders = len(self.disorder_guidelines)
        total_interventions = len(self.intervention_database)
        total_dsm_references = len(self.dsm_references)
        
        # Count interventions by type
        interventions_by_type = {}
        for intervention in self.intervention_database.values():
            therapy_type = intervention.type.value
            interventions_by_type[therapy_type] = interventions_by_type.get(therapy_type, 0) + 1
        
        # Count disorders by category
        disorders_by_category = {}
        for disorder_id, guidelines in self.disorder_guidelines.items():
            # Map disorder to category (simplified mapping)
            if disorder_id in ["MDD", "BIPOLAR"]:
                category = "Mood Disorders"
            elif disorder_id in ["GAD", "PANIC", "PTSD"]:
                category = "Anxiety Disorders"
            elif disorder_id in ["OCD"]:
                category = "Obsessive-Compulsive Disorders"
            elif disorder_id in ["ADHD"]:
                category = "Neurodevelopmental Disorders"
            elif disorder_id in ["EATING_DISORDERS"]:
                category = "Eating Disorders"
            elif disorder_id in ["SUBSTANCE_USE"]:
                category = "Substance Use Disorders"
            elif disorder_id in ["PERSONALITY_DISORDERS"]:
                category = "Personality Disorders"
            else:
                category = "Other Disorders"
            
            disorders_by_category[category] = disorders_by_category.get(category, 0) + 1
        
        return {
            "total_disorders": total_disorders,
            "total_interventions": total_interventions,
            "total_dsm_references": total_dsm_references,
            "interventions_by_type": interventions_by_type,
            "disorders_by_category": disorders_by_category,
            "coverage": {
                "mood_disorders": "Complete",
                "anxiety_disorders": "Complete",
                "trauma_disorders": "Complete",
                "ocd": "Complete",
                "adhd": "Complete",
                "eating_disorders": "Complete",
                "substance_use": "Complete",
                "personality_disorders": "Complete"
            }
        }


# Utility functions for easy access
def get_treatment_guidelines() -> TreatmentGuidelines:
    """Get a global instance of treatment guidelines"""
    return TreatmentGuidelines()

def get_disorder_guidelines(disorder_id: str) -> Optional[DisorderSpecificGuidelines]:
    """Get guidelines for a specific disorder"""
    guidelines = get_treatment_guidelines()
    return guidelines.get_disorder_guidelines(disorder_id)

def get_treatment_plan(disorder_id: str, severity: SymptomSeverity) -> Dict[str, Any]:
    """Get a comprehensive treatment plan for a disorder"""
    guidelines = get_treatment_guidelines()
    return guidelines.get_comprehensive_treatment_plan(disorder_id, severity)

def validate_interventions(interventions: List[Intervention]) -> Dict[str, Any]:
    """Validate a combination of interventions"""
    guidelines = get_treatment_guidelines()
    return guidelines.validate_intervention_combination(interventions)


# Example usage and testing
if __name__ == "__main__":
    # Initialize guidelines
    guidelines = TreatmentGuidelines()
    
    # Test getting guidelines for a specific disorder
    mdd_guidelines = guidelines.get_disorder_guidelines("MDD")
    if mdd_guidelines:
        print(f"MDD Guidelines: {mdd_guidelines.disorder_name}")
        print(f"First-line interventions: {mdd_guidelines.first_line_interventions}")
    
    # Test getting treatment plan
    treatment_plan = guidelines.get_comprehensive_treatment_plan("GAD", SymptomSeverity.MODERATE)
    print(f"GAD Treatment Plan: {len(treatment_plan.get('treatment_approach', {}).get('first_line', []))} first-line interventions")
    
    # Test statistics
    stats = guidelines.get_statistics()
    print(f"Total disorders covered: {stats['total_disorders']}")
    print(f"Total interventions available: {stats['total_interventions']}")
    
    # Test export
    json_export = guidelines.export_guidelines_as_json("MDD")
    print(f"JSON export length: {len(json_export)} characters")


# Utility functions for easy access
def get_treatment_guidelines() -> TreatmentGuidelines:
    """Get a global instance of treatment guidelines"""
    return TreatmentGuidelines()

def get_disorder_guidelines(disorder_id: str) -> Optional[DisorderSpecificGuidelines]:
    """Get guidelines for a specific disorder"""
    guidelines = get_treatment_guidelines()
    return guidelines.get_disorder_guidelines(disorder_id)

def get_treatment_plan(disorder_id: str, severity: SymptomSeverity) -> Dict[str, Any]:
    """Get a comprehensive treatment plan for a disorder"""
    guidelines = get_treatment_guidelines()
    return guidelines.get_comprehensive_treatment_plan(disorder_id, severity)

def validate_interventions(interventions: List[Intervention]) -> Dict[str, Any]:
    """Validate a combination of interventions"""
    guidelines = get_treatment_guidelines()
    return guidelines.validate_intervention_combination(interventions)


# Example usage and testing
if __name__ == "__main__":
    # Initialize guidelines
    guidelines = TreatmentGuidelines()
    
    # Test getting guidelines for a specific disorder
    mdd_guidelines = guidelines.get_disorder_guidelines("MDD")
    if mdd_guidelines:
        print(f"MDD Guidelines: {mdd_guidelines.disorder_name}")
        print(f"First-line interventions: {mdd_guidelines.first_line_interventions}")
    
    # Test getting treatment plan
    treatment_plan = guidelines.get_comprehensive_treatment_plan("GAD", SymptomSeverity.MODERATE)
    print(f"GAD Treatment Plan: {len(treatment_plan.get('treatment_approach', {}).get('first_line', []))} first-line interventions")
    
    # Test statistics
    stats = guidelines.get_statistics()
    print(f"Total disorders covered: {stats['total_disorders']}")
    print(f"Total interventions available: {stats['total_interventions']}")
    
    # Test export
    json_export = guidelines.export_guidelines_as_json("MDD")
    print(f"JSON export length: {len(json_export)} characters")
      
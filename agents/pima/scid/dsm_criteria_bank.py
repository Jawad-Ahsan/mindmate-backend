# dsm_criteria_bank.py
"""
DSM-5 Criteria Bank
Centralized repository of DSM-5 diagnostic criteria for all SCID modules
Eliminates redundancy by centralizing criteria definitions
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

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
class DSMCriterion:
    """Individual DSM-5 criterion"""
    criterion_id: str
    text: str
    category: str
    required: bool = True
    notes: Optional[str] = None

@dataclass
class DisorderCriteria:
    """Complete DSM-5 criteria for a disorder"""
    disorder_id: str
    disorder_name: str
    category: DisorderCategory
    criteria: List[DSMCriterion] = field(default_factory=list)
    minimum_criteria_count: int = 0
    duration_requirement: Optional[str] = None
    exclusion_criteria: List[str] = field(default_factory=list)
    specifiers: List[str] = field(default_factory=list)
    severity_levels: Dict[str, str] = field(default_factory=dict)
    clinical_notes: str = ""

class DSMCriteriaBank:
    """Centralized DSM-5 criteria bank"""
    
    def __init__(self):
        self.disorders: Dict[str, DisorderCriteria] = {}
        self._initialize_criteria()
    
    def _initialize_criteria(self):
        """Initialize all DSM-5 criteria from modules"""
        
        # Major Depressive Disorder
        self.disorders["MDD"] = DisorderCriteria(
            disorder_id="MDD",
            disorder_name="Major Depressive Disorder",
            category=DisorderCategory.MOOD_DISORDERS,
            minimum_criteria_count=5,
            duration_requirement="At least 2 weeks",
            criteria=[
                DSMCriterion("MDD_A1", "Depressed mood most of the day, nearly every day", "core_mood"),
                DSMCriterion("MDD_A2", "Markedly diminished interest or pleasure in activities", "core_mood"),
                DSMCriterion("MDD_B1", "Significant weight loss/gain or appetite changes", "neurovegetative"),
                DSMCriterion("MDD_B2", "Insomnia or hypersomnia nearly every day", "neurovegetative"),
                DSMCriterion("MDD_B3", "Psychomotor agitation or retardation", "neurovegetative"),
                DSMCriterion("MDD_B4", "Fatigue or loss of energy nearly every day", "neurovegetative"),
                DSMCriterion("MDD_C1", "Feelings of worthlessness or inappropriate guilt", "cognitive"),
                DSMCriterion("MDD_C2", "Diminished ability to think or concentrate", "cognitive"),
                DSMCriterion("MDD_C3", "Recurrent thoughts of death or suicidal ideation", "cognitive")
            ],
            severity_levels={
                "mild": "2-3 symptoms beyond required 5",
                "moderate": "4-5 symptoms beyond required 5", 
                "severe": "6+ symptoms beyond required 5"
            },
            clinical_notes="Requires at least 5 symptoms for at least 2 weeks, with at least one being depressed mood or anhedonia."
        )
        
        # Generalized Anxiety Disorder
        self.disorders["GAD"] = DisorderCriteria(
            disorder_id="GAD",
            disorder_name="Generalized Anxiety Disorder",
            category=DisorderCategory.ANXIETY_DISORDERS,
            minimum_criteria_count=3,
            duration_requirement="At least 6 months",
            criteria=[
                DSMCriterion("GAD_A1", "Excessive anxiety and worry occurring more days than not for at least 6 months", "core_worry"),
                DSMCriterion("GAD_A2", "Difficult to control the worry", "core_worry"),
                DSMCriterion("GAD_B1", "Restlessness or feeling keyed up or on edge", "associated_symptoms"),
                DSMCriterion("GAD_B2", "Easily fatigued", "associated_symptoms"),
                DSMCriterion("GAD_B3", "Difficulty concentrating or mind going blank", "associated_symptoms"),
                DSMCriterion("GAD_B4", "Irritability", "associated_symptoms"),
                DSMCriterion("GAD_B5", "Muscle tension", "associated_symptoms"),
                DSMCriterion("GAD_B6", "Sleep disturbance", "associated_symptoms")
            ],
            severity_levels={
                "mild": "Minimal symptoms beyond required criteria",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires excessive worry occurring more days than not for at least 6 months."
        )
        
        # Panic Disorder
        self.disorders["PANIC"] = DisorderCriteria(
            disorder_id="PANIC",
            disorder_name="Panic Disorder",
            category=DisorderCategory.ANXIETY_DISORDERS,
            minimum_criteria_count=4,
            duration_requirement="At least 1 month of concern about attacks",
            criteria=[
                DSMCriterion("PAN_A1", "Recurrent unexpected panic attacks", "core_symptom"),
                DSMCriterion("PAN_B1", "Palpitations or accelerated heart rate", "physical_symptoms"),
                DSMCriterion("PAN_B2", "Sweating", "physical_symptoms"),
                DSMCriterion("PAN_B3", "Trembling or shaking", "physical_symptoms"),
                DSMCriterion("PAN_B4", "Shortness of breath or smothering", "physical_symptoms"),
                DSMCriterion("PAN_B5", "Feeling of choking", "physical_symptoms"),
                DSMCriterion("PAN_B6", "Chest pain or discomfort", "physical_symptoms"),
                DSMCriterion("PAN_B7", "Nausea or abdominal distress", "physical_symptoms"),
                DSMCriterion("PAN_B8", "Dizziness or lightheadedness", "physical_symptoms"),
                DSMCriterion("PAN_B9", "Derealization or depersonalization", "cognitive_symptoms"),
                DSMCriterion("PAN_B10", "Fear of losing control or going crazy", "cognitive_symptoms"),
                DSMCriterion("PAN_B11", "Fear of dying", "cognitive_symptoms"),
                DSMCriterion("PAN_B12", "Numbness or tingling", "physical_symptoms"),
                DSMCriterion("PAN_B13", "Chills or hot flushes", "physical_symptoms")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required 4",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires recurrent unexpected panic attacks with at least 1 month of concern about attacks."
        )
        
        # Substance Use Disorder
        self.disorders["SUBSTANCE_USE"] = DisorderCriteria(
            disorder_id="SUBSTANCE_USE",
            disorder_name="Substance Use Disorder",
            category=DisorderCategory.SUBSTANCE_USE_DISORDERS,
            minimum_criteria_count=2,
            duration_requirement="Within a 12-month period",
            criteria=[
                DSMCriterion("SUD_1", "Substance taken in larger amounts or over longer period than intended", "impaired_control"),
                DSMCriterion("SUD_2", "Persistent desire or unsuccessful efforts to cut down or control use", "impaired_control"),
                DSMCriterion("SUD_3", "Great deal of time spent obtaining, using, or recovering from substance", "impaired_control"),
                DSMCriterion("SUD_4", "Craving or strong desire/urge to use substance", "impaired_control"),
                DSMCriterion("SUD_5", "Recurrent use resulting in failure to fulfill major obligations", "social_impairment"),
                DSMCriterion("SUD_6", "Continued use despite persistent social or interpersonal problems", "social_impairment"),
                DSMCriterion("SUD_7", "Important activities given up or reduced because of substance use", "social_impairment"),
                DSMCriterion("SUD_8", "Recurrent use in physically hazardous situations", "risky_use"),
                DSMCriterion("SUD_9", "Continued use despite knowledge of physical or psychological problems", "risky_use"),
                DSMCriterion("SUD_10", "Tolerance (need for increased amounts or diminished effect)", "pharmacological"),
                DSMCriterion("SUD_11", "Withdrawal (characteristic syndrome or substance used to relieve symptoms)", "pharmacological")
            ],
            severity_levels={
                "mild": "2-3 criteria",
                "moderate": "4-5 criteria",
                "severe": "6+ criteria"
            },
            clinical_notes="Requires problematic pattern of substance use leading to clinically significant impairment or distress."
        )
        
        # ADHD
        self.disorders["ADHD"] = DisorderCriteria(
            disorder_id="ADHD",
            disorder_name="Attention-Deficit/Hyperactivity Disorder",
            category=DisorderCategory.NEURODEVELOPMENTAL_DISORDERS,
            minimum_criteria_count=6,
            duration_requirement="At least 6 months",
            criteria=[
                DSMCriterion("ADHD_IN1", "Fails to give close attention to details/makes careless mistakes", "inattention"),
                DSMCriterion("ADHD_IN2", "Has trouble sustaining attention in tasks or activities", "inattention"),
                DSMCriterion("ADHD_IN3", "Does not seem to listen when spoken to directly", "inattention"),
                DSMCriterion("ADHD_IN4", "Does not follow through on instructions/fails to finish tasks", "inattention"),
                DSMCriterion("ADHD_IN5", "Has trouble organizing tasks and activities", "inattention"),
                DSMCriterion("ADHD_IN6", "Avoids/dislikes tasks requiring sustained mental effort", "inattention"),
                DSMCriterion("ADHD_IN7", "Loses things necessary for tasks/activities", "inattention"),
                DSMCriterion("ADHD_IN8", "Easily distracted by extraneous stimuli", "inattention"),
                DSMCriterion("ADHD_IN9", "Forgetful in daily activities", "inattention"),
                DSMCriterion("ADHD_HI1", "Fidgets/taps hands or feet/squirms in seat", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI2", "Leaves seat when expected to remain seated", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI3", "Feels restless", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI4", "Unable to engage in leisure activities quietly", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI5", "On the go/acts as if driven by a motor", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI6", "Talks excessively", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI7", "Blurts out answers before questions completed", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI8", "Has trouble waiting turn", "hyperactivity_impulsivity"),
                DSMCriterion("ADHD_HI9", "Interrupts or intrudes on others", "hyperactivity_impulsivity")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required 6",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires persistent pattern of inattention and/or hyperactivity-impulsivity that interferes with functioning."
        )
        
        # Adjustment Disorder
        self.disorders["ADJUSTMENT"] = DisorderCriteria(
            disorder_id="ADJUSTMENT",
            disorder_name="Adjustment Disorder",
            category=DisorderCategory.OTHER_DISORDERS,
            minimum_criteria_count=1,
            duration_requirement="Within 3 months of stressor onset",
            criteria=[
                DSMCriterion("ADJ_A1", "Development of emotional or behavioral symptoms in response to identifiable stressor", "core_symptom"),
                DSMCriterion("ADJ_B1", "Marked distress out of proportion to severity of stressor", "distress"),
                DSMCriterion("ADJ_B2", "Significant impairment in social, occupational, or other areas", "impairment"),
                DSMCriterion("ADJ_C1", "Stress-related disturbance does not meet criteria for another mental disorder", "exclusion"),
                DSMCriterion("ADJ_C2", "Symptoms do not represent normal bereavement", "exclusion"),
                DSMCriterion("ADJ_D1", "Symptoms do not persist for more than 6 months after stressor termination", "duration")
            ],
            severity_levels={
                "mild": "Minimal impairment, symptoms manageable",
                "moderate": "Moderate impairment and distress",
                "severe": "Significant impairment and distress"
            },
            clinical_notes="Requires development of emotional or behavioral symptoms in response to identifiable stressor."
        )
        
        # Bipolar Disorder
        self.disorders["BIPOLAR"] = DisorderCriteria(
            disorder_id="BIPOLAR",
            disorder_name="Bipolar Disorder",
            category=DisorderCategory.MOOD_DISORDERS,
            minimum_criteria_count=3,
            duration_requirement="At least 1 week for mania, 4 days for hypomania",
            criteria=[
                DSMCriterion("BIP_A1", "Inflated self-esteem or grandiosity", "manic_symptoms"),
                DSMCriterion("BIP_A2", "Decreased need for sleep", "manic_symptoms"),
                DSMCriterion("BIP_A3", "More talkative than usual or pressure to keep talking", "manic_symptoms"),
                DSMCriterion("BIP_A4", "Flight of ideas or racing thoughts", "manic_symptoms"),
                DSMCriterion("BIP_A5", "Distractibility", "manic_symptoms"),
                DSMCriterion("BIP_A6", "Increase in goal-directed activity or psychomotor agitation", "manic_symptoms"),
                DSMCriterion("BIP_A7", "Excessive involvement in pleasurable activities with high potential for painful consequences", "manic_symptoms")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required 3",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires distinct period of abnormally elevated mood with at least 3 manic symptoms."
        )
        
        # Social Anxiety Disorder
        self.disorders["SOCIAL_ANXIETY"] = DisorderCriteria(
            disorder_id="SOCIAL_ANXIETY",
            disorder_name="Social Anxiety Disorder",
            category=DisorderCategory.ANXIETY_DISORDERS,
            minimum_criteria_count=6,
            duration_requirement="At least 6 months",
            criteria=[
                DSMCriterion("SOC_A1", "Marked fear or anxiety about social situations", "core_fear"),
                DSMCriterion("SOC_A2", "Fear of negative evaluation by others", "core_fear"),
                DSMCriterion("SOC_B1", "Social situations almost always provoke fear or anxiety", "avoidance"),
                DSMCriterion("SOC_B2", "Social situations are avoided or endured with intense fear", "avoidance"),
                DSMCriterion("SOC_C1", "Fear or anxiety is out of proportion to actual threat", "proportionality"),
                DSMCriterion("SOC_C2", "Fear or anxiety is persistent", "persistence"),
                DSMCriterion("SOC_D1", "Significant distress or impairment in functioning", "impairment"),
                DSMCriterion("SOC_D2", "Fear or anxiety is not attributable to substance use", "exclusion"),
                DSMCriterion("SOC_D3", "Fear or anxiety is not better explained by another mental disorder", "exclusion")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required criteria",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires marked fear or anxiety about social situations where individual may be scrutinized by others."
        )
        
        # Specific Phobia
        self.disorders["SPECIFIC_PHOBIA"] = DisorderCriteria(
            disorder_id="SPECIFIC_PHOBIA",
            disorder_name="Specific Phobia",
            category=DisorderCategory.ANXIETY_DISORDERS,
            minimum_criteria_count=4,
            duration_requirement="At least 6 months",
            criteria=[
                DSMCriterion("SPH_A1", "Marked fear or anxiety about specific object or situation", "core_fear"),
                DSMCriterion("SPH_A2", "Phobic object or situation almost always provokes immediate fear or anxiety", "provocation"),
                DSMCriterion("SPH_B1", "Phobic object or situation is actively avoided or endured with intense fear", "avoidance"),
                DSMCriterion("SPH_C1", "Fear or anxiety is out of proportion to actual danger", "proportionality"),
                DSMCriterion("SPH_C2", "Fear or anxiety is persistent", "persistence"),
                DSMCriterion("SPH_D1", "Significant distress or impairment in functioning", "impairment"),
                DSMCriterion("SPH_D2", "Fear or anxiety is not attributable to substance use", "exclusion"),
                DSMCriterion("SPH_D3", "Fear or anxiety is not better explained by another mental disorder", "exclusion")
            ],
            severity_levels={
                "mild": "Minimal impairment",
                "moderate": "Moderate impairment",
                "severe": "Significant impairment"
            },
            clinical_notes="Requires marked fear or anxiety about specific object or situation, with immediate fear response."
        )
        
        # Agoraphobia
        self.disorders["AGORAPHOBIA"] = DisorderCriteria(
            disorder_id="AGORAPHOBIA",
            disorder_name="Agoraphobia",
            category=DisorderCategory.ANXIETY_DISORDERS,
            minimum_criteria_count=2,
            duration_requirement="At least 6 months",
            criteria=[
                DSMCriterion("AGO_A1", "Marked fear or anxiety about two or more situations", "core_fear"),
                DSMCriterion("AGO_A2", "Fear of using public transportation", "specific_situations"),
                DSMCriterion("AGO_A3", "Fear of being in open spaces", "specific_situations"),
                DSMCriterion("AGO_A4", "Fear of being in enclosed places", "specific_situations"),
                DSMCriterion("AGO_A5", "Fear of standing in line or being in crowds", "specific_situations"),
                DSMCriterion("AGO_A6", "Fear of being outside of home alone", "specific_situations"),
                DSMCriterion("AGO_B1", "Situations are avoided or endured with intense fear", "avoidance"),
                DSMCriterion("AGO_C1", "Fear or anxiety is out of proportion to actual danger", "proportionality"),
                DSMCriterion("AGO_C2", "Fear or anxiety is persistent", "persistence"),
                DSMCriterion("AGO_D1", "Significant distress or impairment in functioning", "impairment")
            ],
            severity_levels={
                "mild": "Minimal impairment",
                "moderate": "Moderate impairment", 
                "severe": "Significant impairment"
            },
            clinical_notes="Requires marked fear or anxiety about two or more situations where escape might be difficult."
        )
        
        # Posttraumatic Stress Disorder
        self.disorders["PTSD"] = DisorderCriteria(
            disorder_id="PTSD",
            disorder_name="Posttraumatic Stress Disorder",
            category=DisorderCategory.TRAUMA_STRESSOR_DISORDERS,
            minimum_criteria_count=6,
            duration_requirement="More than 1 month",
            criteria=[
                DSMCriterion("PTSD_A1", "Exposure to actual or threatened death, serious injury, or sexual violence", "exposure"),
                DSMCriterion("PTSD_B1", "Intrusive memories of traumatic event", "intrusion"),
                DSMCriterion("PTSD_B2", "Recurrent distressing dreams", "intrusion"),
                DSMCriterion("PTSD_B3", "Dissociative reactions (flashbacks)", "intrusion"),
                DSMCriterion("PTSD_B4", "Intense psychological distress at exposure to cues", "intrusion"),
                DSMCriterion("PTSD_B5", "Marked physiological reactions to cues", "intrusion"),
                DSMCriterion("PTSD_C1", "Avoidance of memories, thoughts, or feelings", "avoidance"),
                DSMCriterion("PTSD_C2", "Avoidance of external reminders", "avoidance"),
                DSMCriterion("PTSD_D1", "Inability to remember important aspects of trauma", "negative_alterations"),
                DSMCriterion("PTSD_D2", "Persistent negative beliefs about self, others, or world", "negative_alterations"),
                DSMCriterion("PTSD_D3", "Persistent distorted cognitions about cause or consequences", "negative_alterations"),
                DSMCriterion("PTSD_D4", "Persistent negative emotional state", "negative_alterations"),
                DSMCriterion("PTSD_D5", "Markedly diminished interest in activities", "negative_alterations"),
                DSMCriterion("PTSD_D6", "Feelings of detachment from others", "negative_alterations"),
                DSMCriterion("PTSD_D7", "Persistent inability to experience positive emotions", "negative_alterations"),
                DSMCriterion("PTSD_E1", "Irritable behavior and angry outbursts", "arousal"),
                DSMCriterion("PTSD_E2", "Reckless or self-destructive behavior", "arousal"),
                DSMCriterion("PTSD_E3", "Hypervigilance", "arousal"),
                DSMCriterion("PTSD_E4", "Exaggerated startle response", "arousal"),
                DSMCriterion("PTSD_E5", "Problems with concentration", "arousal"),
                DSMCriterion("PTSD_E6", "Sleep disturbance", "arousal")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required criteria",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Requires exposure to trauma plus symptoms from intrusion, avoidance, negative alterations, and arousal clusters."
        )
        
        # Obsessive-Compulsive Disorder
        self.disorders["OCD"] = DisorderCriteria(
            disorder_id="OCD",
            disorder_name="Obsessive-Compulsive Disorder",
            category=DisorderCategory.OBSESSIVE_COMPULSIVE_DISORDERS,
            minimum_criteria_count=1,
            duration_requirement="At least 1 hour per day",
            criteria=[
                DSMCriterion("OCD_A1", "Presence of obsessions, compulsions, or both", "core_symptoms"),
                DSMCriterion("OCD_B1", "Obsessions are recurrent and persistent thoughts, urges, or images", "obsessions"),
                DSMCriterion("OCD_B2", "Obsessions are intrusive and unwanted", "obsessions"),
                DSMCriterion("OCD_B3", "Individual attempts to ignore or suppress obsessions", "obsessions"),
                DSMCriterion("OCD_B4", "Individual attempts to neutralize obsessions with compulsions", "obsessions"),
                DSMCriterion("OCD_C1", "Compulsions are repetitive behaviors or mental acts", "compulsions"),
                DSMCriterion("OCD_C2", "Compulsions are performed in response to obsessions", "compulsions"),
                DSMCriterion("OCD_C3", "Compulsions are aimed at preventing or reducing anxiety", "compulsions"),
                DSMCriterion("OCD_C4", "Compulsions are not connected in a realistic way", "compulsions"),
                DSMCriterion("OCD_D1", "Obsessions or compulsions are time-consuming", "impairment"),
                DSMCriterion("OCD_D2", "Obsessions or compulsions cause significant distress", "impairment"),
                DSMCriterion("OCD_D3", "Obsessions or compulsions cause impairment in functioning", "impairment")
            ],
            severity_levels={
                "mild": "1-3 hours per day",
                "moderate": "3-8 hours per day",
                "severe": "More than 8 hours per day"
            },
            clinical_notes="Requires presence of obsessions, compulsions, or both that are time-consuming or cause significant distress."
        )
        
        # Alcohol Use Disorder
        self.disorders["ALCOHOL_USE"] = DisorderCriteria(
            disorder_id="ALCOHOL_USE",
            disorder_name="Alcohol Use Disorder",
            category=DisorderCategory.SUBSTANCE_USE_DISORDERS,
            minimum_criteria_count=2,
            duration_requirement="Within a 12-month period",
            criteria=[
                DSMCriterion("AUD_1", "Alcohol taken in larger amounts or over longer period than intended", "impaired_control"),
                DSMCriterion("AUD_2", "Persistent desire or unsuccessful efforts to cut down or control use", "impaired_control"),
                DSMCriterion("AUD_3", "Great deal of time spent obtaining, using, or recovering from alcohol", "impaired_control"),
                DSMCriterion("AUD_4", "Craving or strong desire/urge to use alcohol", "impaired_control"),
                DSMCriterion("AUD_5", "Recurrent use resulting in failure to fulfill major obligations", "social_impairment"),
                DSMCriterion("AUD_6", "Continued use despite persistent social or interpersonal problems", "social_impairment"),
                DSMCriterion("AUD_7", "Important activities given up or reduced because of alcohol use", "social_impairment"),
                DSMCriterion("AUD_8", "Recurrent use in physically hazardous situations", "risky_use"),
                DSMCriterion("AUD_9", "Continued use despite knowledge of physical or psychological problems", "risky_use"),
                DSMCriterion("AUD_10", "Tolerance (need for increased amounts or diminished effect)", "pharmacological"),
                DSMCriterion("AUD_11", "Withdrawal (characteristic syndrome or alcohol used to relieve symptoms)", "pharmacological")
            ],
            severity_levels={
                "mild": "2-3 criteria",
                "moderate": "4-5 criteria",
                "severe": "6+ criteria"
            },
            clinical_notes="Requires problematic pattern of alcohol use leading to clinically significant impairment or distress."
        )
        
        # Eating Disorders
        self.disorders["EATING_DISORDERS"] = DisorderCriteria(
            disorder_id="EATING_DISORDERS",
            disorder_name="Eating Disorders",
            category=DisorderCategory.EATING_DISORDERS,
            minimum_criteria_count=3,
            duration_requirement="At least 3 months",
            criteria=[
                DSMCriterion("ED_1", "Restriction of energy intake relative to requirements", "restriction"),
                DSMCriterion("ED_2", "Intense fear of gaining weight or becoming fat", "body_image"),
                DSMCriterion("ED_3", "Disturbance in way body weight or shape is experienced", "body_image"),
                DSMCriterion("ED_4", "Recurrent episodes of binge eating", "binge_eating"),
                DSMCriterion("ED_5", "Recurrent inappropriate compensatory behaviors", "compensatory"),
                DSMCriterion("ED_6", "Self-evaluation unduly influenced by body shape and weight", "body_image"),
                DSMCriterion("ED_7", "Absence of regular menstrual periods (in females)", "physiological")
            ],
            severity_levels={
                "mild": "Few symptoms beyond required criteria",
                "moderate": "Moderate symptoms and impairment",
                "severe": "Many symptoms, severe functional impairment"
            },
            clinical_notes="Includes anorexia nervosa, bulimia nervosa, and binge-eating disorder."
        )
    
    def get_disorder_criteria(self, disorder_id: str) -> Optional[DisorderCriteria]:
        """Get criteria for a specific disorder"""
        return self.disorders.get(disorder_id.upper())
    
    def get_all_disorders(self) -> Dict[str, DisorderCriteria]:
        """Get all disorder criteria"""
        return self.disorders.copy()
    
    def get_disorders_by_category(self, category: DisorderCategory) -> Dict[str, DisorderCriteria]:
        """Get all disorders in a specific category"""
        return {
            disorder_id: criteria 
            for disorder_id, criteria in self.disorders.items() 
            if criteria.category == category
        }
    
    def search_criteria(self, search_term: str) -> List[DSMCriterion]:
        """Search criteria by text"""
        results = []
        search_term_lower = search_term.lower()
        
        for disorder in self.disorders.values():
            for criterion in disorder.criteria:
                if (search_term_lower in criterion.text.lower() or 
                    search_term_lower in criterion.criterion_id.lower()):
                    results.append(criterion)
        
        return results
    
    def get_criteria_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all criteria"""
        total_disorders = len(self.disorders)
        total_criteria = sum(len(disorder.criteria) for disorder in self.disorders.values())
        
        category_counts = {}
        for disorder in self.disorders.values():
            category = disorder.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "total_disorders": total_disorders,
            "total_criteria": total_criteria,
            "category_distribution": category_counts
        }
    
    def get_dsm_criteria_for_module(self, disorder_id: str) -> List[str]:
        """Get DSM criteria text list for a module (backward compatibility)"""
        disorder = self.get_disorder_criteria(disorder_id)
        if not disorder:
            return []
        return [criterion.text for criterion in disorder.criteria]
    
    def get_severity_thresholds_for_module(self, disorder_id: str) -> Dict[str, float]:
        """Get severity thresholds for a module (backward compatibility)"""
        disorder = self.get_disorder_criteria(disorder_id)
        if not disorder:
            return {}
        
        # Convert severity descriptions to numeric thresholds
        thresholds = {}
        if "mild" in disorder.severity_levels:
            thresholds["mild"] = 0.4
        if "moderate" in disorder.severity_levels:
            thresholds["moderate"] = 0.6
        if "severe" in disorder.severity_levels:
            thresholds["severe"] = 0.8
        
        return thresholds
    
    def get_clinical_notes_for_module(self, disorder_id: str) -> str:
        """Get clinical notes for a module (backward compatibility)"""
        disorder = self.get_disorder_criteria(disorder_id)
        return disorder.clinical_notes if disorder else ""
    
    def validate_module_criteria(self, disorder_id: str, module_criteria: List[str]) -> Dict[str, Any]:
        """Validate that a module's criteria match the centralized bank"""
        bank_disorder = self.get_disorder_criteria(disorder_id)
        if not bank_disorder:
            return {"valid": False, "error": f"Disorder {disorder_id} not found in criteria bank"}
        
        bank_criteria_texts = [criterion.text for criterion in bank_disorder.criteria]
        module_criteria_lower = [c.lower().strip() for c in module_criteria]
        bank_criteria_lower = [c.lower().strip() for c in bank_criteria_texts]
        
        missing_criteria = []
        extra_criteria = []
        
        for bank_criterion in bank_criteria_lower:
            if not any(bank_criterion in module_criterion or module_criterion in bank_criterion 
                      for module_criterion in module_criteria_lower):
                missing_criteria.append(bank_criterion)
        
        for module_criterion in module_criteria_lower:
            if not any(module_criterion in bank_criterion or bank_criterion in module_criterion 
                      for bank_criterion in bank_criteria_lower):
                extra_criteria.append(module_criterion)
        
        return {
            "valid": len(missing_criteria) == 0,
            "missing_criteria": missing_criteria,
            "extra_criteria": extra_criteria,
            "total_bank_criteria": len(bank_criteria_texts),
            "total_module_criteria": len(module_criteria)
        }
    
    def generate_module_criteria_dict(self, disorder_id: str) -> Dict[str, Any]:
        """Generate a criteria dictionary for use in module creation"""
        disorder = self.get_disorder_criteria(disorder_id)
        if not disorder:
            return {}
        
        return {
            "dsm_criteria": [criterion.text for criterion in disorder.criteria],
            "severity_thresholds": self.get_severity_thresholds_for_module(disorder_id),
            "clinical_notes": disorder.clinical_notes,
            "minimum_criteria_count": disorder.minimum_criteria_count,
            "duration_requirement": disorder.duration_requirement
        }


# Global instance for easy access
dsm_criteria_bank = DSMCriteriaBank()

# Utility functions for backward compatibility
def get_dsm_criteria(disorder_id: str) -> Optional[DisorderCriteria]:
    """Get DSM criteria for a disorder (backward compatibility)"""
    return dsm_criteria_bank.get_disorder_criteria(disorder_id)

def get_all_dsm_criteria() -> Dict[str, DisorderCriteria]:
    """Get all DSM criteria (backward compatibility)"""
    return dsm_criteria_bank.get_all_disorders()

def search_dsm_criteria(search_term: str) -> List[DSMCriterion]:
    """Search DSM criteria (backward compatibility)"""
    return dsm_criteria_bank.search_criteria(search_term)

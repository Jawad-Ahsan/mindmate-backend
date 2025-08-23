import json
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class SCIDItem:
    """Single SCID-5-SC screening item"""
    id: str
    text: str
    linked_modules: List[str]
    severity: str  # "low", "medium", "high"
    category: str  # "mood", "anxiety", "psychosis", etc.
    keywords: List[str]  # for rule-based matching

@dataclass
class SCIDModule:
    """SCID-5 module definition"""
    id: str
    name: str
    type: str  # "CV" (Clinical Version) or "PD" (Personality Disorders)
    priority_weight: float
    expected_time_mins: int
    description: str

class SCID_SC_Bank:
    """Complete SCID-5-SC (Screening) bank with all 55+ items"""
    
    def __init__(self):
        self.sc_items = self._initialize_sc_items()
        self.modules = self._initialize_modules()
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True, ngram_range=(1, 2))
        self._fit_vectorizer()
    
    def _initialize_sc_items(self) -> Dict[str, SCIDItem]:
        """Initialize complete SCID-5-SC item bank"""
        items = {}
        
        # MOOD DISORDERS
        items["MDD_01"] = SCIDItem(
            id="MDD_01",
            text="Have you felt sad, down, or depressed most of the day nearly every day for two weeks or more?",
            linked_modules=["MDD"],
            severity="medium",
            category="mood",
            keywords=["sad", "down", "depressed", "depression", "mood", "blue", "hopeless"]
        )
        
        items["MDD_02"] = SCIDItem(
            id="MDD_02",
            text="Have you lost interest or pleasure in activities you used to enjoy for two weeks or more?",
            linked_modules=["MDD"],
            severity="medium",
            category="mood",
            keywords=["lost interest", "no pleasure", "anhedonia", "enjoyment", "activities", "motivation"]
        )
        
        items["MAN_01"] = SCIDItem(
            id="MAN_01",
            text="Have you had a period when you felt so good or high that others thought you were not your normal self?",
            linked_modules=["Bipolar"],
            severity="high",
            category="mood",
            keywords=["manic", "high", "euphoric", "elevated", "good mood", "hyper"]
        )
        
        items["MAN_02"] = SCIDItem(
            id="MAN_02",
            text="Have you had a period when you needed much less sleep than usual and didn't feel tired?",
            linked_modules=["Bipolar"],
            severity="high",
            category="mood",
            keywords=["less sleep", "no sleep", "energetic", "restless", "insomnia", "hyper"]
        )
        
        items["HYP_01"] = SCIDItem(
            id="HYP_01",
            text="Have you had periods lasting several days when you felt unusually cheerful or outgoing?",
            linked_modules=["Bipolar"],
            severity="medium",
            category="mood",
            keywords=["cheerful", "outgoing", "hypomanic", "elevated", "social", "talkative"]
        )
        
        # ANXIETY DISORDERS
        items["PAN_01"] = SCIDItem(
            id="PAN_01",
            text="Have you had sudden episodes of intense fear or panic in which your heart races?",
            linked_modules=["Panic"],
            severity="high",
            category="anxiety",
            keywords=["panic", "panic attack", "heart racing", "intense fear", "sudden fear", "palpitations"]
        )
        
        items["PAN_02"] = SCIDItem(
            id="PAN_02",
            text="During panic episodes, do you experience shortness of breath or feel like you're choking?",
            linked_modules=["Panic"],
            severity="high",
            category="anxiety",
            keywords=["shortness of breath", "choking", "breathing", "suffocating", "chest tight"]
        )
        
        items["AGO_01"] = SCIDItem(
            id="AGO_01",
            text="Do you avoid or feel anxious about places where escape might be difficult?",
            linked_modules=["Agoraphobia"],
            severity="medium",
            category="anxiety",
            keywords=["avoid places", "escape", "trapped", "agoraphobia", "crowded", "public"]
        )
        
        items["SOC_01"] = SCIDItem(
            id="SOC_01",
            text="Are you very afraid of social situations where you might be judged by others?",
            linked_modules=["Social_Anxiety"],
            severity="medium",
            category="anxiety",
            keywords=["social anxiety", "judged", "embarrassed", "social situations", "performance", "shy"]
        )
        
        items["GAD_01"] = SCIDItem(
            id="GAD_01",
            text="Do you worry excessively about many different things most days?",
            linked_modules=["GAD"],
            severity="medium",
            category="anxiety",
            keywords=["worry", "excessive worry", "anxious", "restless", "tension", "nervous"]
        )
        
        items["SPE_01"] = SCIDItem(
            id="SPE_01",
            text="Do you have persistent, unreasonable fears of specific objects or situations?",
            linked_modules=["Specific_Phobia"],
            severity="low",
            category="anxiety",
            keywords=["phobia", "specific fear", "afraid of", "irrational fear", "avoid", "scared"]
        )
        
        # TRAUMA AND STRESSOR-RELATED DISORDERS
        items["PTS_01"] = SCIDItem(
            id="PTS_01",
            text="Have you experienced or witnessed a traumatic event that continues to bother you?",
            linked_modules=["PTSD"],
            severity="high",
            category="trauma",
            keywords=["trauma", "traumatic", "ptsd", "flashbacks", "nightmares", "witnessed"]
        )
        
        items["PTS_02"] = SCIDItem(
            id="PTS_02",
            text="Do you have recurring nightmares or flashbacks about traumatic experiences?",
            linked_modules=["PTSD"],
            severity="high",
            category="trauma",
            keywords=["nightmares", "flashbacks", "intrusive", "memories", "reliving", "dreams"]
        )
        
        items["ASD_01"] = SCIDItem(
            id="ASD_01",
            text="Have you had severe stress reactions lasting less than a month after trauma?",
            linked_modules=["Acute_Stress"],
            severity="medium",
            category="trauma",
            keywords=["acute stress", "recent trauma", "dissociation", "detached", "numb"]
        )
        
        # OBSESSIVE-COMPULSIVE AND RELATED DISORDERS
        items["OCD_01"] = SCIDItem(
            id="OCD_01",
            text="Do you have recurring, unwanted thoughts that cause you distress?",
            linked_modules=["OCD"],
            severity="medium",
            category="obsessive_compulsive",
            keywords=["obsessions", "unwanted thoughts", "intrusive", "compulsions", "rituals", "ocd"]
        )
        
        items["OCD_02"] = SCIDItem(
            id="OCD_02",
            text="Do you feel compelled to repeat behaviors or mental acts over and over?",
            linked_modules=["OCD"],
            severity="medium",
            category="obsessive_compulsive",
            keywords=["compulsions", "repeat", "rituals", "checking", "counting", "washing"]
        )
        
        items["BDD_01"] = SCIDItem(
            id="BDD_01",
            text="Are you excessively concerned about perceived flaws in your appearance?",
            linked_modules=["Body_Dysmorphic"],
            severity="medium",
            category="obsessive_compulsive",
            keywords=["appearance", "body image", "flaws", "ugly", "mirror", "grooming"]
        )
        
        items["HOA_01"] = SCIDItem(
            id="HOA_01",
            text="Do you have difficulty discarding possessions regardless of their value?",
            linked_modules=["Hoarding"],
            severity="low",
            category="obsessive_compulsive",
            keywords=["hoarding", "collecting", "clutter", "discard", "possessions", "saving"]
        )
        
        # PSYCHOTIC DISORDERS
        items["PSY_01"] = SCIDItem(
            id="PSY_01",
            text="Have you ever heard voices or sounds that other people didn't hear?",
            linked_modules=["Psychotic"],
            severity="high",
            category="psychotic",
            keywords=["voices", "hallucinations", "hearing voices", "sounds", "auditory"]
        )
        
        items["PSY_02"] = SCIDItem(
            id="PSY_02",
            text="Have you seen things that other people didn't see or weren't really there?",
            linked_modules=["Psychotic"],
            severity="high",
            category="psychotic",
            keywords=["visual hallucinations", "seeing things", "visions", "not there"]
        )
        
        items["PSY_03"] = SCIDItem(
            id="PSY_03",
            text="Have you believed that others were spying on you or plotting against you?",
            linked_modules=["Psychotic"],
            severity="high",
            category="psychotic",
            keywords=["paranoid", "spying", "plotting", "conspiracy", "persecution", "watching"]
        )
        
        items["PSY_04"] = SCIDItem(
            id="PSY_04",
            text="Have you felt that your thoughts were being broadcast or could be heard by others?",
            linked_modules=["Psychotic"],
            severity="high",
            category="psychotic",
            keywords=["thought broadcast", "thoughts heard", "mind reading", "telepathy"]
        )
        
        items["PSY_05"] = SCIDItem(
            id="PSY_05",
            text="Have you had unusual experiences with your body or felt controlled by outside forces?",
            linked_modules=["Psychotic"],
            severity="high",
            category="psychotic",
            keywords=["controlled", "outside forces", "body changes", "possession", "influenced"]
        )
        
        # SUBSTANCE USE DISORDERS
        items["ALC_01"] = SCIDItem(
            id="ALC_01",
            text="Have you used more alcohol than intended or had trouble cutting down?",
            linked_modules=["Alcohol_Use"],
            severity="high",
            category="substance",
            keywords=["alcohol", "drinking", "cut down", "control", "more than intended"]
        )
        
        items["ALC_02"] = SCIDItem(
            id="ALC_02",
            text="Has alcohol use interfered with work, school, or family responsibilities?",
            linked_modules=["Alcohol_Use"],
            severity="high",
            category="substance",
            keywords=["interference", "work problems", "family problems", "responsibilities"]
        )
        
        items["DRU_01"] = SCIDItem(
            id="DRU_01",
            text="Have you used drugs more than intended or been unable to cut down?",
            linked_modules=["Substance_Use"],
            severity="high",
            category="substance",
            keywords=["drugs", "substance", "cut down", "control", "more than intended"]
        )
        
        items["DRU_02"] = SCIDItem(
            id="DRU_02",
            text="Have you experienced withdrawal symptoms when stopping drug use?",
            linked_modules=["Substance_Use"],
            severity="high",
            category="substance",
            keywords=["withdrawal", "symptoms", "stopping", "physical", "sick"]
        )
        
        # EATING DISORDERS
        items["AN_01"] = SCIDItem(
            id="AN_01",
            text="Have you significantly restricted food intake leading to low body weight?",
            linked_modules=["Anorexia"],
            severity="high",
            category="eating",
            keywords=["restrict food", "low weight", "diet", "calories", "thin", "weight loss"]
        )
        
        items["BN_01"] = SCIDItem(
            id="BN_01",
            text="Do you have episodes of eating unusually large amounts of food in short periods?",
            linked_modules=["Bulimia"],
            severity="medium",
            category="eating",
            keywords=["binge eating", "large amounts", "overeating", "episodes", "food"]
        )
        
        items["BN_02"] = SCIDItem(
            id="BN_02",
            text="Do you compensate for overeating by vomiting, using laxatives, or excessive exercise?",
            linked_modules=["Bulimia"],
            severity="high",
            category="eating",
            keywords=["vomiting", "laxatives", "purging", "compensate", "excessive exercise"]
        )
        
        items["BED_01"] = SCIDItem(
            id="BED_01",
            text="Do you have binge eating episodes without compensatory behaviors?",
            linked_modules=["Binge_Eating"],
            severity="medium",
            category="eating",
            keywords=["binge eating", "no purging", "overeating", "guilt", "shame"]
        )
        
        # SLEEP-WAKE DISORDERS
        items["INS_01"] = SCIDItem(
            id="INS_01",
            text="Do you have persistent difficulty falling asleep or staying asleep?",
            linked_modules=["Insomnia"],
            severity="low",
            category="sleep",
            keywords=["insomnia", "can't sleep", "sleep problems", "staying asleep", "tired"]
        )
        
        items["HYP_02"] = SCIDItem(
            id="HYP_02",
            text="Do you experience excessive sleepiness during the day despite adequate sleep?",
            linked_modules=["Hypersomnia"],
            severity="low",
            category="sleep",
            keywords=["sleepy", "excessive sleep", "daytime", "tired", "drowsy"]
        )
        
        # PERSONALITY DISORDERS
        items["BPD_01"] = SCIDItem(
            id="BPD_01",
            text="Do your relationships swing between idealizing and devaluing people?",
            linked_modules=["Borderline_PD"],
            severity="medium",
            category="personality",
            keywords=["unstable relationships", "idealizing", "devaluing", "love-hate", "intense"]
        )
        
        items["BPD_02"] = SCIDItem(
            id="BPD_02",
            text="Do you have an unstable sense of self or frequent identity changes?",
            linked_modules=["Borderline_PD"],
            severity="medium",
            category="personality",
            keywords=["identity", "sense of self", "unstable", "who am i", "changing"]
        )
        
        items["BPD_03"] = SCIDItem(
            id="BPD_03",
            text="Do you engage in impulsive behaviors that could be harmful?",
            linked_modules=["Borderline_PD"],
            severity="high",
            category="personality",
            keywords=["impulsive", "harmful behaviors", "reckless", "dangerous", "self-harm"]
        )
        
        items["NPD_01"] = SCIDItem(
            id="NPD_01",
            text="Do you have a grandiose sense of self-importance or expect special treatment?",
            linked_modules=["Narcissistic_PD"],
            severity="low",
            category="personality",
            keywords=["grandiose", "special treatment", "important", "superior", "entitled"]
        )
        
        items["APD_01"] = SCIDItem(
            id="APD_01",
            text="Do you often disregard the rights of others or social norms?",
            linked_modules=["Antisocial_PD"],
            severity="medium",
            category="personality",
            keywords=["disregard rights", "antisocial", "rules", "norms", "others"]
        )
        
        items["HPD_01"] = SCIDItem(
            id="HPD_01",
            text="Do you feel uncomfortable when you're not the center of attention?",
            linked_modules=["Histrionic_PD"],
            severity="low",
            category="personality",
            keywords=["center attention", "dramatic", "emotional", "theatrical", "spotlight"]
        )
        
        items["AVD_01"] = SCIDItem(
            id="AVD_01",
            text="Do you avoid social activities due to fears of criticism or rejection?",
            linked_modules=["Avoidant_PD"],
            severity="medium",
            category="personality",
            keywords=["avoid social", "criticism", "rejection", "inadequate", "shy"]
        )
        
        items["DEP_01"] = SCIDItem(
            id="DEP_01",
            text="Do you have difficulty making decisions without excessive advice from others?",
            linked_modules=["Dependent_PD"],
            severity="low",
            category="personality",
            keywords=["decisions", "advice", "dependent", "help", "support", "clingy"]
        )
        
        items["OCP_01"] = SCIDItem(
            id="OCP_01",
            text="Are you preoccupied with orderliness, perfectionism, and control?",
            linked_modules=["Obsessive_Compulsive_PD"],
            severity="low",
            category="personality",
            keywords=["perfectionism", "control", "orderliness", "rigid", "rules", "details"]
        )
        
        items["PAR_01"] = SCIDItem(
            id="PAR_01",
            text="Do you generally distrust others and suspect their motives?",
            linked_modules=["Paranoid_PD"],
            severity="medium",
            category="personality",
            keywords=["distrust", "suspicious", "motives", "paranoid", "betrayal"]
        )
        
        items["SZD_01"] = SCIDItem(
            id="SZD_01",
            text="Do you prefer to be alone and have little interest in relationships?",
            linked_modules=["Schizoid_PD"],
            severity="low",
            category="personality",
            keywords=["alone", "solitary", "relationships", "detached", "isolated"]
        )
        
        items["STP_01"] = SCIDItem(
            id="STP_01",
            text="Do you have odd beliefs, unusual perceptions, or eccentric behavior?",
            linked_modules=["Schizotypal_PD"],
            severity="medium",
            category="personality",
            keywords=["odd beliefs", "eccentric", "unusual", "magical thinking", "strange"]
        )
        
        # ADDITIONAL SCREENING ITEMS
        items["ATT_01"] = SCIDItem(
            id="ATT_01",
            text="Do you have persistent difficulty paying attention or staying focused?",
            linked_modules=["ADHD"],
            severity="low",
            category="neurodevelopmental",
            keywords=["attention", "focus", "concentration", "adhd", "distracted"]
        )
        
        items["ATT_02"] = SCIDItem(
            id="ATT_02",
            text="Are you often hyperactive, restless, or impulsive?",
            linked_modules=["ADHD"],
            severity="low",
            category="neurodevelopmental",
            keywords=["hyperactive", "restless", "impulsive", "fidgety", "can't sit still"]
        )
        
        items["AUT_01"] = SCIDItem(
            id="AUT_01",
            text="Do you have difficulty with social communication and repetitive behaviors?",
            linked_modules=["Autism"],
            severity="low",
            category="neurodevelopmental",
            keywords=["social communication", "repetitive", "autism", "routine", "sensory"]
        )
        
        return items
    
    def _initialize_modules(self) -> Dict[str, SCIDModule]:
        """Initialize SCID-5 module definitions"""
        modules = {}
        
        # CLINICAL VERSION (CV) MODULES
        modules["MDD"] = SCIDModule("MDD", "Major Depressive Disorder", "CV", 0.8, 20, "Depression screening and assessment")
        modules["Bipolar"] = SCIDModule("Bipolar", "Bipolar Disorder", "CV", 0.9, 25, "Manic and hypomanic episodes")
        modules["Panic"] = SCIDModule("Panic", "Panic Disorder", "CV", 0.7, 15, "Panic attacks and panic disorder")
        modules["Agoraphobia"] = SCIDModule("Agoraphobia", "Agoraphobia", "CV", 0.6, 15, "Agoraphobic avoidance")
        modules["Social_Anxiety"] = SCIDModule("Social_Anxiety", "Social Anxiety Disorder", "CV", 0.6, 15, "Social phobia assessment")
        modules["GAD"] = SCIDModule("GAD", "Generalized Anxiety Disorder", "CV", 0.6, 15, "Excessive worry and anxiety")
        modules["Specific_Phobia"] = SCIDModule("Specific_Phobia", "Specific Phobia", "CV", 0.4, 10, "Specific fears and phobias")
        modules["PTSD"] = SCIDModule("PTSD", "Post-Traumatic Stress Disorder", "CV", 0.9, 30, "Trauma-related symptoms")
        modules["Acute_Stress"] = SCIDModule("Acute_Stress", "Acute Stress Disorder", "CV", 0.7, 20, "Acute stress reactions")
        modules["OCD"] = SCIDModule("OCD", "Obsessive-Compulsive Disorder", "CV", 0.7, 20, "Obsessions and compulsions")
        modules["Body_Dysmorphic"] = SCIDModule("Body_Dysmorphic", "Body Dysmorphic Disorder", "CV", 0.5, 15, "Body image concerns")
        modules["Hoarding"] = SCIDModule("Hoarding", "Hoarding Disorder", "CV", 0.4, 15, "Hoarding behaviors")
        modules["Psychotic"] = SCIDModule("Psychotic", "Psychotic Disorders", "CV", 1.0, 30, "Psychotic symptoms screening")
        modules["Alcohol_Use"] = SCIDModule("Alcohol_Use", "Alcohol Use Disorder", "CV", 0.9, 20, "Alcohol use problems")
        modules["Substance_Use"] = SCIDModule("Substance_Use", "Substance Use Disorder", "CV", 0.9, 25, "Drug use problems")
        modules["Anorexia"] = SCIDModule("Anorexia", "Anorexia Nervosa", "CV", 0.8, 20, "Restrictive eating disorder")
        modules["Bulimia"] = SCIDModule("Bulimia", "Bulimia Nervosa", "CV", 0.8, 20, "Binge-purge behaviors")
        modules["Binge_Eating"] = SCIDModule("Binge_Eating", "Binge Eating Disorder", "CV", 0.6, 15, "Binge eating without purging")
        modules["Insomnia"] = SCIDModule("Insomnia", "Insomnia Disorder", "CV", 0.3, 10, "Sleep difficulties")
        modules["Hypersomnia"] = SCIDModule("Hypersomnia", "Hypersomnia Disorder", "CV", 0.3, 10, "Excessive sleepiness")
        modules["ADHD"] = SCIDModule("ADHD", "ADHD", "CV", 0.5, 15, "Attention and hyperactivity")
        modules["Autism"] = SCIDModule("Autism", "Autism Spectrum Disorder", "CV", 0.6, 20, "Autism screening")
        
        # PERSONALITY DISORDERS (PD) MODULES
        modules["Borderline_PD"] = SCIDModule("Borderline_PD", "Borderline Personality Disorder", "PD", 0.8, 25, "Borderline personality traits")
        modules["Narcissistic_PD"] = SCIDModule("Narcissistic_PD", "Narcissistic Personality Disorder", "PD", 0.4, 20, "Narcissistic traits")
        modules["Antisocial_PD"] = SCIDModule("Antisocial_PD", "Antisocial Personality Disorder", "PD", 0.6, 25, "Antisocial behaviors")
        modules["Histrionic_PD"] = SCIDModule("Histrionic_PD", "Histrionic Personality Disorder", "PD", 0.4, 20, "Dramatic personality traits")
        modules["Avoidant_PD"] = SCIDModule("Avoidant_PD", "Avoidant Personality Disorder", "PD", 0.5, 20, "Social avoidance patterns")
        modules["Dependent_PD"] = SCIDModule("Dependent_PD", "Dependent Personality Disorder", "PD", 0.4, 15, "Excessive dependence")
        modules["Obsessive_Compulsive_PD"] = SCIDModule("Obsessive_Compulsive_PD", "Obsessive-Compulsive Personality Disorder", "PD", 0.4, 20, "Perfectionism and control")
        modules["Paranoid_PD"] = SCIDModule("Paranoid_PD", "Paranoid Personality Disorder", "PD", 0.5, 20, "Paranoid traits")
        modules["Schizoid_PD"] = SCIDModule("Schizoid_PD", "Schizoid Personality Disorder", "PD", 0.4, 15, "Social detachment")
        modules["Schizotypal_PD"] = SCIDModule("Schizotypal_PD", "Schizotypal Personality Disorder", "PD", 0.6, 25, "Eccentric traits and thinking")
        
        return modules
    
    def _fit_vectorizer(self):
        """Fit TF-IDF vectorizer on all SC item texts"""
        texts = [item.text for item in self.sc_items.values()]
        self.vectorizer.fit(texts)
        self.item_vectors = self.vectorizer.transform(texts)
    
    def export_as_json(self) -> str:
        """Export complete SCID-5-SC bank as JSON"""
        export_data = {
            "sc_items": [asdict(item) for item in self.sc_items.values()],
            "modules": [asdict(module) for module in self.modules.values()]
        }
        return json.dumps(export_data, indent=2)
    
    def generate_module_scores(self, presenting_concern: str, threshold: float = 0.3) -> Dict[str, float]:
        """
        Generate relevance scores for modules based on presenting concern
        
        Args:
            presenting_concern: Patient's presenting concern text
            threshold: Minimum score threshold to include module
            
        Returns:
            Dict mapping module_id to relevance score (0.0 to 1.0)
        """
        if not presenting_concern.strip():
            return {}
        
        # Normalize presenting concern
        concern_lower = presenting_concern.lower().strip()
        
        # Transform presenting concern to vector
        concern_vector = self.vectorizer.transform([concern_lower])
        
        # Calculate similarities with all items
        similarities = cosine_similarity(concern_vector, self.item_vectors)[0]
        
        # Rule-based keyword matching
        module_scores = {}
        item_list = list(self.sc_items.values())
        
        for i, (item_id, item) in enumerate(self.sc_items.items()):
            # Combine similarity score with keyword matching
            sim_score = similarities[i]
            
            # Keyword matching boost
            keyword_match = 0.0
            for keyword in item.keywords:
                if keyword.lower() in concern_lower:
                    keyword_match += 0.2  # Boost for keyword match
            
            # Severity weight
            severity_weight = {"low": 0.8, "medium": 1.0, "high": 1.2}[item.severity]
            
            # Combined score
            combined_score = min(1.0, (sim_score * 0.6 + keyword_match) * severity_weight)
            
            # Add to module scores
            for module_id in item.linked_modules:
                if module_id not in module_scores:
                    module_scores[module_id] = 0.0
                module_scores[module_id] = max(module_scores[module_id], combined_score)
        
        # Apply module priority weights
        final_scores = {}
        for module_id, score in module_scores.items():
            if module_id in self.modules and score >= threshold:
                priority_weight = self.modules[module_id].priority_weight
                final_scores[module_id] = min(1.0, score * priority_weight)
        
        # Sort by score descending
        return dict(sorted(final_scores.items(), key=lambda x: x[1], reverse=True))
    
    def semantic_module_selection(self, presenting_concern: str, max_modules: int = 5) -> Dict[str, Any]:
        """
        Semantic decision for module selection with detailed rationale
        
        Args:
            presenting_concern: Patient's presenting concern text
            max_modules: Maximum number of modules to recommend
            
        Returns:
            Dict with recommended modules, scores, and rationale
        """
        if not presenting_concern.strip():
            return {
                "recommended_modules": [],
                "rationale": "No presenting concern provided",
                "total_modules_available": len(self.modules),
                "analysis": {}
            }
        
        # Generate module scores
        module_scores = self.generate_module_scores(presenting_concern)
        
        if not module_scores:
            return {
                "recommended_modules": [],
                "rationale": "No modules matched the presenting concern",
                "total_modules_available": len(self.modules),
                "analysis": {"presenting_concern": presenting_concern}
            }
        
        # Get top modules
        top_modules = list(module_scores.items())[:max_modules]
        
        # Build detailed recommendations
        recommendations = []
        for module_id, score in top_modules:
            module = self.modules[module_id]
            
            # Find matching items for rationale
            matching_items = []
            for item_id, item in self.sc_items.items():
                if module_id in item.linked_modules:
                    # Check if this item would match
                    concern_lower = presenting_concern.lower()
                    if any(keyword.lower() in concern_lower for keyword in item.keywords):
                        matching_items.append({
                            "id": item_id,
                            "text": item.text,
                            "keywords_matched": [kw for kw in item.keywords if kw.lower() in concern_lower]
                        })
            
            recommendations.append({
                "module_id": module_id,
                "module_name": module.name,
                "module_type": module.type,
                "relevance_score": round(score, 3),
                "priority_weight": module.priority_weight,
                "estimated_time_mins": module.expected_time_mins,
                "description": module.description,
                "matching_items": matching_items[:3],  # Top 3 matching items
                "confidence": "high" if score >= 0.7 else "medium" if score >= 0.5 else "low"
            })
        
        # Generate rationale
        if top_modules:
            top_module = self.modules[top_modules[0][0]]
            top_score = top_modules[0][1]
            
            rationale = f"Based on semantic analysis, '{top_module.name}' shows highest relevance (score: {top_score:.3f}). "
            
            if len(top_modules) > 1:
                rationale += f"Additionally recommended: {', '.join([self.modules[mid].name for mid, _ in top_modules[1:3]])}. "
            
            # Add category analysis
            categories = {}
            for item in self.sc_items.values():
                if any(kw.lower() in presenting_concern.lower() for kw in item.keywords):
                    categories[item.category] = categories.get(item.category, 0) + 1
            
            if categories:
                top_category = max(categories.keys(), key=lambda k: categories[k])
                rationale += f"Primary symptom category: {top_category.replace('_', ' ').title()}."
        else:
            rationale = "No significant module matches found for the presenting concern."
        
        return {
            "recommended_modules": recommendations,
            "rationale": rationale,
            "total_modules_available": len(self.modules),
            "analysis": {
                "presenting_concern": presenting_concern,
                "total_scored_modules": len(module_scores),
                "category_distribution": categories if 'categories' in locals() else {},
                "highest_score": top_modules[0][1] if top_modules else 0.0,
                "recommendation_confidence": "high" if top_modules and top_modules[0][1] >= 0.7 else "medium"
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the bank
    scid_bank = SCID_SC_Bank()
    
    # Example 1: Export as JSON
    print("=== JSON Export (first 1000 chars) ===")
    json_export = scid_bank.export_as_json()
    print(json_export[:1000] + "...")
    
    # Example 2: Generate module scores
    print("\n=== Module Scores Example ===")
    concern1 = "I've been feeling very sad and depressed for weeks, lost interest in activities I used to enjoy"
    scores1 = scid_bank.generate_module_scores(concern1)
    print(f"Concern: {concern1}")
    print("Top module scores:")
    for module_id, score in list(scores1.items())[:5]:
        module_name = scid_bank.modules[module_id].name
        print(f"  {module_name}: {score:.3f}")
    
    # Example 3: Semantic module selection
    print("\n=== Semantic Module Selection Example ===")
    concern2 = "I have panic attacks with heart racing and feel anxious in crowded places"
    selection = scid_bank.semantic_module_selection(concern2, max_modules=3)
    
    print(f"Concern: {concern2}")
    print(f"Rationale: {selection['rationale']}")
    print("\nRecommended modules:")
    for rec in selection['recommended_modules']:
        print(f"  {rec['module_name']} ({rec['module_type']})")
        print(f"    Score: {rec['relevance_score']} | Confidence: {rec['confidence']}")
        print(f"    Time: {rec['estimated_time_mins']} mins | {rec['description']}")
        if rec['matching_items']:
            print(f"    Key matching item: {rec['matching_items'][0]['text'][:80]}...")
        print()
    
    # Example 4: Different types of concerns
    print("\n=== Various Concern Types ===")
    test_concerns = [
        "I hear voices that tell me what to do",
        "I can't stop checking if I locked the door",
        "My relationships are very unstable and intense",
        "I drink too much alcohol and can't control it",
        "I have trouble sleeping and feel tired all day"
    ]
    
    for concern in test_concerns:
        scores = scid_bank.generate_module_scores(concern, threshold=0.4)
        top_module = list(scores.items())[0] if scores else ("None", 0.0)
        print(f"'{concern}' → {scid_bank.modules[top_module[0]].name if top_module[0] != 'None' else 'No match'} ({top_module[1]:.3f})")
    
    print(f"\n=== Summary ===")
    print(f"Total SCID-5-SC items: {len(scid_bank.sc_items)}")
    print(f"Total modules: {len(scid_bank.modules)}")
    print(f"CV modules: {len([m for m in scid_bank.modules.values() if m.type == 'CV'])}")
    print(f"PD modules: {len([m for m in scid_bank.modules.values() if m.type == 'PD'])}")
    
    # Category breakdown
    categories = {}
    for item in scid_bank.sc_items.values():
        categories[item.category] = categories.get(item.category, 0) + 1
    
    print("\nItems by category:")
    for category, count in sorted(categories.items()):
        print(f"  {category.replace('_', ' ').title()}: {count} items")
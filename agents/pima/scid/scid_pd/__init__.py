# scid_pd/__init__.py
"""
SCID-PD (Personality Disorders) Implementation
A comprehensive structured clinical interview tool for DSM-5 personality disorders
"""

from .base_types import (
    ResponseType,
    PersonalityDimensionType,
    PervasivenessCriteria, 
    OnsetCriteria,
    Severity,
    DSMCluster,
    SCIDPDResponse,
    SCIDPDQuestion,
    PersonalityPatternExtraction,
    PersonalityModuleResult,
    SCIDPDModule,
    PersonalityProfile
)

from .utils import SCIDPDAdministrator

# Import all personality disorder modules
from .modules.borderline_pd import create_borderline_pd_module
# Additional modules would be imported here:
from .modules.narcissistic_pd import create_narcissistic_pd_module
from .modules.antisocial_pd import create_antisocial_pd_module
# from .modules.histrionic_pd import create_histrionic_pd_module
from .modules.avoidant_pd import create_avoidant_pd_module
from .modules.dependent_pd import create_dependent_pd_module
# from .modules.obsessive_compulsive_pd import create_obsessive_compulsive_pd_module
# from .modules.paranoid_pd import create_paranoid_pd_module
# from .modules.schizoid_pd import create_schizoid_pd_module
# from .modules.schizotypal_pd import create_schizotypal_pd_module

__version__ = "1.0.0"
__author__ = "SCID-PD Implementation Team"

# Registry of all available personality disorder modules
PD_MODULE_REGISTRY = {
    "BPD": create_borderline_pd_module,
    # Additional modules would be registered here:
    "NPD": create_narcissistic_pd_module,
    "ASPD": create_antisocial_pd_module,
    # "HPD": create_histrionic_pd_module,
    "AVPD": create_avoidant_pd_module,
    "DPD": create_dependent_pd_module,
    # "OCPD": create_obsessive_compulsive_pd_module,
    # "PPD": create_paranoid_pd_module,
    # "SPD": create_schizoid_pd_module,
    # "STPD": create_schizotypal_pd_module,
}

# Cluster organization for easier access
CLUSTER_A_MODULES = {
    # "PPD": create_paranoid_pd_module,
    # "SPD": create_schizoid_pd_module, 
    # "STPD": create_schizotypal_pd_module,
}

CLUSTER_B_MODULES = {
    "BPD": create_borderline_pd_module,
    # "NPD": create_narcissistic_pd_module,
    # "ASPD": create_antisocial_pd_module,
    # "HPD": create_histrionic_pd_module,
}

CLUSTER_C_MODULES = {
    # "AVPD": create_avoidant_pd_module,
    # "DPD": create_dependent_pd_module,
    # "OCPD": create_obsessive_compulsive_pd_module,
}

def get_all_pd_modules():
    """Get all available SCID-PD modules"""
    return {module_id: creator() for module_id, creator in PD_MODULE_REGISTRY.items()}

def get_pd_module(module_id: str):
    """Get a specific SCID-PD module"""
    if module_id not in PD_MODULE_REGISTRY:
        raise ValueError(f"Personality disorder module {module_id} not found. Available: {list(PD_MODULE_REGISTRY.keys())}")
    return PD_MODULE_REGISTRY[module_id]()

def get_cluster_modules(cluster: DSMCluster):
    """Get all modules for a specific DSM cluster"""
    if cluster == DSMCluster.CLUSTER_A:
        return {module_id: creator() for module_id, creator in CLUSTER_A_MODULES.items()}
    elif cluster == DSMCluster.CLUSTER_B:
        return {module_id: creator() for module_id, creator in CLUSTER_B_MODULES.items()}
    elif cluster == DSMCluster.CLUSTER_C:
        return {module_id: creator() for module_id, creator in CLUSTER_C_MODULES.items()}
    else:
        raise ValueError(f"Unknown cluster: {cluster}")

def list_available_pd_modules():
    """List all available personality disorder module IDs and names"""
    modules_info = []
    for module_id, creator in PD_MODULE_REGISTRY.items():
        module = creator()
        modules_info.append({
            "id": module_id,
            "name": module.name,
            "description": module.description,
            "dsm_cluster": module.dsm_cluster.value,
            "estimated_time_mins": module.estimated_time_mins,
            "total_questions": len(module.questions),
            "core_features": module.core_features,
            "minimum_criteria": module.minimum_criteria_count
        })
    return modules_info

def create_comprehensive_pd_assessment():
    """Create a comprehensive personality disorder assessment with all available modules"""
    administrator = SCIDPDAdministrator()
    profile = administrator.start_personality_assessment()
    
    # Add metadata about the comprehensive assessment
    profile.clinician_notes = "Comprehensive personality disorder assessment using all available SCID-PD modules"
    
    return administrator, profile

def create_cluster_assessment(cluster: DSMCluster):
    """Create a targeted assessment for a specific DSM cluster"""
    administrator = SCIDPDAdministrator()
    profile = administrator.start_personality_assessment()
    
    cluster_name = cluster.value.replace("_", " ").title()
    profile.clinician_notes = f"Targeted {cluster_name} personality disorder assessment"
    
    return administrator, profile, get_cluster_modules(cluster)

def create_screening_assessment():
    """Create a brief screening assessment with key personality disorder modules"""
    # For screening, focus on most common/important personality disorders
    screening_modules = {
        "BPD": create_borderline_pd_module,
        # Add other common PDs when implemented:
        # "NPD": create_narcissistic_pd_module,
        # "ASPD": create_antisocial_pd_module,
        # "AVPD": create_avoidant_pd_module,
    }
    
    administrator = SCIDPDAdministrator()
    profile = administrator.start_personality_assessment()
    profile.clinician_notes = "Screening assessment for common personality disorders"
    
    modules = {module_id: creator() for module_id, creator in screening_modules.items()}
    return administrator, profile, modules

# Utility functions for working with personality disorder data
def analyze_cluster_distribution(profile: PersonalityProfile):
    """Analyze the distribution of personality disorders across DSM clusters"""
    cluster_dist = profile.get_cluster_distribution()
    
    analysis = {
        "total_positive_diagnoses": len(profile.get_positive_diagnoses()),
        "cluster_breakdown": {},
        "predominant_cluster": None,
        "mixed_cluster_presentation": False
    }
    
    for cluster, diagnoses in cluster_dist.items():
        cluster_name = cluster.value.replace("_", " ").title()
        analysis["cluster_breakdown"][cluster_name] = {
            "count": len(diagnoses),
            "diagnoses": diagnoses
        }
    
    # Determine predominant cluster
    max_count = max(len(diagnoses) for diagnoses in cluster_dist.values())
    if max_count > 0:
        predominant_clusters = [
            cluster for cluster, diagnoses in cluster_dist.items() 
            if len(diagnoses) == max_count
        ]
        
        if len(predominant_clusters) == 1:
            analysis["predominant_cluster"] = predominant_clusters[0].value.replace("_", " ").title()
        else:
            analysis["mixed_cluster_presentation"] = True
    
    return analysis

def generate_treatment_recommendations(profile: PersonalityProfile):
    """Generate evidence-based treatment recommendations based on personality profile"""
    recommendations = []
    positive_diagnoses = profile.get_positive_diagnoses()
    
    if not positive_diagnoses:
        return ["No personality disorder criteria met - consider supportive therapy if distress present"]
    
    # General recommendations for any personality disorder
    recommendations.extend([
        "Consider long-term psychotherapy as primary treatment modality",
        "Assess for comorbid Axis I disorders (depression, anxiety, substance use)",
        "Evaluate current psychosocial stressors and support systems"
    ])
    
    # Specific recommendations based on diagnoses
    diagnosis_names = [result.module_name for result in positive_diagnoses]
    
    if "Borderline Personality Disorder" in diagnosis_names:
        recommendations.extend([
            "Consider Dialectical Behavior Therapy (DBT) as evidence-based treatment",
            "Assess suicide risk regularly and develop safety planning",
            "Consider medication for comorbid mood/anxiety symptoms",
            "Family therapy or education may be beneficial"
        ])
    
    # Cluster-specific recommendations
    cluster_dist = profile.get_cluster_distribution()
    
    if cluster_dist[DSMCluster.CLUSTER_A]:
        recommendations.extend([
            "Consider cognitive-behavioral approaches for paranoid/suspicious thinking",
            "Assess for psychotic symptoms and need for antipsychotic medication",
            "Social skills training may be beneficial"
        ])
    
    if cluster_dist[DSMCluster.CLUSTER_B]:
        recommendations.extend([
            "Emotion regulation skills training is essential",
            "Consider trauma-informed approaches if trauma history present",
            "Address impulsivity and self-harm behaviors as priorities"
        ])
    
    if cluster_dist[DSMCluster.CLUSTER_C]:
        recommendations.extend([
            "Exposure-based treatments for avoidance behaviors",
            "Assertiveness training and gradual independence building",
            "Address perfectionism and rigidity in thinking"
        ])
    
    # Severity-based recommendations
    severe_cases = [r for r in positive_diagnoses if r.severity_level == Severity.SEVERE]
    if severe_cases:
        recommendations.extend([
            "Consider intensive outpatient or partial hospitalization programs",
            "Coordinate care with psychiatrist for medication management",
            "Monitor for need for higher level of care"
        ])
    
    # Multiple personality disorders
    if len(positive_diagnoses) > 1:
        recommendations.extend([
            "Complex personality pathology - consider specialist consultation",
            "Prioritize treatment targets based on safety and functional impairment",
            "Longer-term treatment planning likely necessary"
        ])
    
    return list(set(recommendations))  # Remove duplicates

def export_pd_profile_summary(profile: PersonalityProfile) -> dict:
    """Export a concise summary of the personality disorder profile"""
    positive_diagnoses = profile.get_positive_diagnoses()
    cluster_analysis = analyze_cluster_distribution(profile)
    
    return {
        "assessment_summary": {
            "assessment_date": profile.assessment_date.isoformat(),
            "total_modules_administered": len(profile.module_results),
            "total_assessment_time_minutes": profile.total_assessment_time,
            "overall_severity": profile.overall_severity.value if profile.overall_severity else None
        },
        "diagnostic_findings": {
            "personality_disorders_diagnosed": len(positive_diagnoses),
            "primary_diagnoses": [result.module_name for result in positive_diagnoses],
            "dimensional_scores": profile.dimensional_scores,
            "cluster_analysis": cluster_analysis
        },
        "clinical_indicators": {
            "safety_concerns": any(
                "self_harm" in str(pattern.pattern_name).lower() or 
                "suicidal" in str(pattern.pattern_name).lower()
                for result in positive_diagnoses 
                for pattern in result.patterns_present
            ),
            "functional_impairment_severe": any(
                result.severity_level == Severity.SEVERE 
                for result in positive_diagnoses
            ),
            "multiple_pd_diagnoses": len(positive_diagnoses) > 1
        },
        "recommendations": {
            "treatment_recommendations": generate_treatment_recommendations(profile),
            "follow_up_needed": len(positive_diagnoses) > 0,
            "specialist_referral_indicated": len(positive_diagnoses) > 1 or any(
                result.severity_level == Severity.SEVERE for result in positive_diagnoses
            )
        }
    }
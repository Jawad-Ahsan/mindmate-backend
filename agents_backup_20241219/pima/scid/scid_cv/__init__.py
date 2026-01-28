# scid_cv/__init__.py
"""
SCID-5 Clinical Version (SCID-CV) Implementation
A comprehensive structured clinical interview tool for DSM-5 disorders
"""

from .base_types import (
    ResponseType, 
    Severity, 
    SCIDResponse, 
    SCIDQuestion, 
    SymptomExtraction, 
    ModuleResult, 
    SCIDModule
)

from .utils import SCIDAdministrator

# Import all modules
from .modules.mdd import create_mdd_module
from .modules.bipolar_disorder import create_bipolar_module
from .modules.panic_disorder import create_panic_module
from .modules.agoraphobia import create_agoraphobia_module
from .modules.social_anxiety import create_social_anxiety_module
from .modules.gad import create_gad_module
from .modules.specific_phobia import create_specific_phobia_module
from .modules.ptsd import create_ptsd_module
from .modules.ocd import create_ocd_module
# from .modules.psychotic_disorders import create_psychotic_module
from .modules.alcohal_use import create_alcohol_use_module
from .modules.substance_use import create_substance_use_module
from .modules.eating_disorder import create_eating_disorders_module
from .modules.adhd import create_adhd_module
from .modules.adjustment_disorder import create_adjustment_disorder_module

__version__ = "1.0.0"
__author__ = "SCID-CV Implementation Team"

# Registry of all available modules
MODULE_REGISTRY = {
    "MDD": create_mdd_module,
    "BIPOLAR": create_bipolar_module,
    "PANIC": create_panic_module,
    "AGORAPHOBIA": create_agoraphobia_module,
    "SOCIAL_ANXIETY": create_social_anxiety_module,
    "GAD": create_gad_module,
    "SPECIFIC_PHOBIA": create_specific_phobia_module,
    "PTSD": create_ptsd_module,
    "OCD": create_ocd_module,
    # "PSYCHOTIC": create_psychotic_module,
    "ALCOHOL_USE": create_alcohol_use_module,
    "SUBSTANCE_USE": create_substance_use_module,
    "EATING_DISORDERS": create_eating_disorders_module,
    "ADHD": create_adhd_module,
    "ADJUSTMENT": create_adjustment_disorder_module,
}

def get_all_modules():
    """Get all available SCID-CV modules"""
    return {module_id: creator() for module_id, creator in MODULE_REGISTRY.items()}

def get_module(module_id: str):
    """Get a specific SCID-CV module"""
    if module_id not in MODULE_REGISTRY:
        raise ValueError(f"Module {module_id} not found. Available: {list(MODULE_REGISTRY.keys())}")
    return MODULE_REGISTRY[module_id]()

def list_available_modules():
    """List all available module IDs and names"""
    modules_info = []
    for module_id, creator in MODULE_REGISTRY.items():
        module = creator()
        modules_info.append({
            "id": module_id,
            "name": module.name,
            "description": module.description,
            "estimated_time_mins": module.estimated_time_mins,
            "total_questions": len(module.questions)
        })
    return modules_info
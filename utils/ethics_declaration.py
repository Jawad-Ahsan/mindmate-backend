"""
MindMate Specialist Ethics Declaration Utilities
==============================================
Contains the ethics declaration text and helper functions for specialist onboarding
"""

from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================================
# ETHICS DECLARATION TEXT
# ============================================================================

MINDMATE_ETHICS_DECLARATION_TEXT = """
MindMate Specialist Ethics Declaration

I, [Name], hereby declare that:

1. I will maintain strict confidentiality of patient information and uphold the highest standards of privacy protection in accordance with applicable laws and professional ethics.

2. I will uphold professional boundaries and avoid any conflict of interest that could compromise the quality of care provided to patients.

3. I will only practice within the scope of my qualifications and registration, ensuring that I provide services that align with my professional competence and expertise.

4. I will treat all patients with dignity, respect, and without discrimination based on race, ethnicity, gender, sexual orientation, religion, age, disability, or any other personal characteristics.

5. I affirm that all documents and credentials submitted during the application process are authentic, accurate, and represent my true qualifications and experience.

6. I accept that violation of this declaration can result in immediate termination of my account, reporting to relevant authorities, and potential legal consequences.

7. I commit to ongoing professional development and staying updated with best practices in mental health care.

8. I will maintain appropriate professional liability insurance as required by my jurisdiction.

9. I will report any suspected abuse, neglect, or harm to vulnerable individuals in accordance with legal and ethical obligations.

10. I will engage in regular supervision and consultation as appropriate for my practice and professional development.

Name: ____________________
Date: ___________________
Signature: ________________

By signing this declaration, I acknowledge that I have read, understood, and agree to abide by all the terms and conditions outlined above.
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ethics_declaration_text(specialist_name: str) -> str:
    """
    Get the ethics declaration text with the specialist's name filled in
    
    Args:
        specialist_name: Full name of the specialist
        
    Returns:
        Formatted ethics declaration text
    """
    return MINDMATE_ETHICS_DECLARATION_TEXT.replace("[Name]", specialist_name)

def validate_ethics_declaration(declaration_text: str, signed_name: str) -> Dict[str, Any]:
    """
    Validate the ethics declaration submission
    
    Args:
        declaration_text: The submitted declaration text
        signed_name: The name signed on the declaration
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Check if declaration text contains required elements
    required_phrases = [
        "maintain strict confidentiality",
        "professional boundaries",
        "scope of my qualifications",
        "treat all patients with dignity",
        "documents and credentials submitted are authentic",
        "violation of this declaration can result in termination"
    ]
    
    for phrase in required_phrases:
        if phrase.lower() not in declaration_text.lower():
            validation_result["errors"].append(f"Missing required phrase: '{phrase}'")
            validation_result["is_valid"] = False
    
    # Check if signed name is reasonable length
    if len(signed_name.strip()) < 2:
        validation_result["errors"].append("Signed name is too short")
        validation_result["is_valid"] = False
    
    if len(signed_name.strip()) > 200:
        validation_result["errors"].append("Signed name is too long")
        validation_result["is_valid"] = False
    
    # Check if declaration text is reasonable length
    if len(declaration_text.strip()) < 500:
        validation_result["warnings"].append("Declaration text seems too short")
    
    if len(declaration_text.strip()) > 10000:
        validation_result["warnings"].append("Declaration text seems too long")
    
    return validation_result

def format_ethics_declaration_for_display(specialist_name: str, signed_date: Optional[datetime] = None) -> str:
    """
    Format the ethics declaration for display purposes
    
    Args:
        specialist_name: Full name of the specialist
        signed_date: Date when declaration was signed
        
    Returns:
        Formatted declaration text for display
    """
    declaration = get_ethics_declaration_text(specialist_name)
    
    if signed_date:
        date_str = signed_date.strftime("%B %d, %Y")
        declaration = declaration.replace("Date: ___________________", f"Date: {date_str}")
    
    return declaration

def get_mandatory_documents_list() -> Dict[str, Any]:
    """
    Get the list of mandatory documents for specialist induction
    
    Returns:
        Dictionary containing mandatory and optional document lists
    """
    return {
        "mandatory_documents": [
            {
                "type": "cnic_front",
                "name": "CNIC (Front)",
                "description": "Front side of Pakistani National Identity Card",
                "required": True
            },
            {
                "type": "cnic_back", 
                "name": "CNIC (Back)",
                "description": "Back side of Pakistani National Identity Card",
                "required": True
            },
            {
                "type": "degree_certificate",
                "name": "Degree Certificate",
                "description": "MBBS/BS/MS/PhD degree certificate",
                "required": True
            },
            {
                "type": "license_registration",
                "name": "License/Registration",
                "description": "PMC, Health Authority, PAP, or other relevant registration",
                "required": True
            },
            {
                "type": "experience_certificate",
                "name": "Experience Certificate",
                "description": "Internship/clinic/hospital experience certificate",
                "required": True
            },
            {
                "type": "recent_photograph",
                "name": "Recent Photograph",
                "description": "Recent professional photograph",
                "required": True
            },
            {
                "type": "ethics_declaration",
                "name": "Ethics Declaration",
                "description": "Signed MindMate Specialist Ethics Declaration",
                "required": True
            }
        ],
        "optional_documents": [
            {
                "type": "diploma_certification",
                "name": "Diplomas & Certifications",
                "description": "CBT, DBT, trauma-focused therapy, etc.",
                "required": False
            },
            {
                "type": "international_membership",
                "name": "International Memberships",
                "description": "APA, HCPC, or other international professional memberships",
                "required": False
            },
            {
                "type": "research_publication",
                "name": "Research Publications",
                "description": "Published research papers or articles",
                "required": False
            },
            {
                "type": "reference_letter",
                "name": "Reference Letters",
                "description": "Professional reference letters",
                "required": False
            }
        ]
    }

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MINDMATE_ETHICS_DECLARATION_TEXT",
    "get_ethics_declaration_text",
    "validate_ethics_declaration", 
    "format_ethics_declaration_for_display",
    "get_mandatory_documents_list"
]

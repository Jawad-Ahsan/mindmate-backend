# MindMate Specialist Induction Process

## Overview

The MindMate Specialist Induction Process is designed to ensure that all mental health professionals joining the platform meet the highest standards of qualification, ethics, and professional conduct. This document outlines the complete process, required documents, and API endpoints.

## Mandatory Documents

All specialists must submit the following mandatory documents during the induction process:

### 1. CNIC (Front + Back)
- **Type**: `cnic_front`, `cnic_back`
- **Description**: Pakistani National Identity Card (both sides)
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB per file

### 2. Degree Certificate
- **Type**: `degree_certificate`
- **Description**: MBBS/MSc/MS/PhD degree certificate
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

### 3. License/Registration
- **Type**: `license_registration`
- **Description**: PMC, Health Authority, PAP, or other relevant registration
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

### 4. Experience Certificate
- **Type**: `experience_certificate`
- **Description**: Internship/clinic/hospital experience certificate
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

### 5. Recent Photograph
- **Type**: `recent_photograph`
- **Description**: Recent professional photograph
- **Format**: JPG, PNG
- **Max Size**: 5MB

### 6. Ethics Declaration
- **Type**: `ethics_declaration`
- **Description**: Signed MindMate Specialist Ethics Declaration
- **Format**: PDF
- **Max Size**: 5MB

## Optional Documents

Specialists may also submit the following optional documents to enhance their profile:

### 1. Diplomas & Certifications
- **Type**: `diploma_certification`
- **Description**: CBT, DBT, trauma-focused therapy, etc.
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

### 2. International Memberships
- **Type**: `international_membership`
- **Description**: APA, HCPC, or other international professional memberships
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

### 3. Research Publications
- **Type**: `research_publication`
- **Description**: Published research papers or articles
- **Format**: PDF
- **Max Size**: 15MB

### 4. Reference Letters
- **Type**: `reference_letter`
- **Description**: Professional reference letters
- **Format**: PDF, JPG, PNG
- **Max Size**: 10MB

## MindMate Specialist Ethics Declaration

### Declaration Text

```
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
```

## API Endpoints

### 1. Get Ethics Declaration Text
```
GET /specialist/ethics-declaration-text
```
Returns the ethics declaration text with the specialist's name filled in.

### 2. Get Mandatory Documents List
```
GET /specialist/mandatory-documents
```
Returns the complete list of mandatory and optional documents required for induction.

### 3. Sign Ethics Declaration
```
POST /specialist/sign-ethics-declaration
```
Allows specialists to sign the ethics declaration electronically.

**Request Body:**
```json
{
  "signed_name": "Dr. John Doe",
  "declaration_text": "Full declaration text...",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

### 4. Complete Profile
```
POST /specialist/complete-profile
```
Complete the specialist's professional profile with basic information.

### 5. Submit Documents
```
POST /specialist/submit-documents
```
Submit all required documents for admin review.

## Database Schema Updates

### New Document Types
The `DocumentTypeEnum` has been updated to include:

```python
# Mandatory Documents
CNIC_FRONT = "cnic_front"
CNIC_BACK = "cnic_back"
DEGREE_CERTIFICATE = "degree_certificate"
LICENSE_REGISTRATION = "license_registration"
EXPERIENCE_CERTIFICATE = "experience_certificate"
RECENT_PHOTOGRAPH = "recent_photograph"
ETHICS_DECLARATION = "ethics_declaration"

# Optional Documents
DIPLOMA_CERTIFICATION = "diploma_certification"
INTERNATIONAL_MEMBERSHIP = "international_membership"
RESEARCH_PUBLICATION = "research_publication"
REFERENCE_LETTER = "reference_letter"
```

### New Tables

#### SpecialistEthicsDeclaration
Stores the signed ethics declaration information:
- `specialist_id`: Foreign key to specialists table
- `declaration_text`: Full text of the declaration
- `signed_name`: Name as signed on declaration
- `signed_date`: Date when signed
- `ip_address`: IP address when signed
- `user_agent`: Browser/device information
- `is_active`: Whether declaration is currently active
- `version`: Version of the declaration

#### Updated SpecialistsApprovalData
Added ethics declaration fields:
- `ethics_declaration_signed`: Boolean flag
- `ethics_declaration_date`: Date when signed
- `ethics_declaration_ip`: IP address when signed

## Validation Rules

### Document Validation
- All mandatory documents must be submitted
- No duplicate document types allowed
- File size limits enforced
- Supported file formats validated

### Ethics Declaration Validation
- Must contain all required phrases
- Signed name must be reasonable length
- Declaration text must be complete
- IP address and user agent captured for audit

## Admin Review Process

1. **Document Submission**: Specialist submits all mandatory documents
2. **Admin Notification**: System notifies admins of new submission
3. **Document Review**: Admins review each document individually
4. **Background Check**: System tracks background check status
5. **Approval Decision**: Admin approves or rejects with notes
6. **Specialist Notification**: Specialist notified of decision

## Timeline

- **Document Review**: 2-3 business days
- **Background Check**: 3-5 business days
- **Total Process**: 5-8 business days

## Compliance

This induction process ensures compliance with:
- Pakistani Medical Council (PMC) requirements
- Data protection regulations
- Professional ethics standards
- Mental health care best practices

## Support

For questions about the induction process, contact:
- Email: support@mindmate.com
- Phone: +92-XXX-XXXXXXX
- Hours: Monday-Friday, 9 AM - 6 PM PKT

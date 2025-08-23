# Users Management System

## Overview

The Users Management System provides comprehensive administrative control over specialists and patients in the platform. It includes functionality for approving, rejecting, suspending, activating, and deactivating users with detailed audit trails and reason tracking.

## Features

### Specialist Management
- **Get Specialist Profile with Documents**: Retrieve complete specialist information including all uploaded documents for approval/rejection
- **Approve Specialist**: Approve specialists for practice after document verification
- **Reject Specialist**: Reject specialist applications with detailed reasons
- **Suspend Specialist**: Temporarily suspend specialists pending investigation

### Patient Management
- **Activate Patient**: Activate patient accounts for full platform access
- **Deactivate Patient**: Deactivate patient accounts with reason tracking
- **Suspend Patient**: Temporarily suspend patient accounts
- **Unsuspend Patient**: Reactivate suspended patient accounts

### Key Features
- **Reason Tracking**: Every action requires a detailed reason (minimum 10 characters)
- **Admin Notes**: Optional additional notes for internal reference
- **Audit Trail**: All actions are logged with timestamps and admin information
- **Status Management**: Comprehensive status tracking for all user types
- **Document Verification**: Complete document management for specialist approval

## API Endpoints

### Base URL
```
/admin/users
```

### 1. Get Specialist Profile with Documents

**Endpoint**: `GET /admin/users/specialists/{specialist_id}/profile`

**Description**: Retrieve complete specialist profile including all documents for approval/rejection

**Response**: Complete specialist profile with:
- Basic information (name, email, phone, etc.)
- Authentication status
- Approval data and documents
- Specializations
- All uploaded documents with verification status

**Example Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "first_name": "Dr. Sarah",
  "last_name": "Johnson",
  "email": "sarah.johnson@example.com",
  "phone": "+923001234567",
  "specialist_type": "psychologist",
  "years_experience": 8,
  "city": "Karachi",
  "approval_status": "pending",
  "is_email_verified": true,
  "approval_data": {
    "license_number": "PSY-2023-001",
    "highest_degree": "Ph.D. in Clinical Psychology",
    "university_name": "University of Karachi",
    "documents": [
      {
        "document_type": "license",
        "document_name": "Professional License.pdf",
        "verification_status": "pending",
        "upload_date": "2024-01-15T10:30:00Z"
      }
    ]
  },
  "specializations": [
    {
      "specialization": "anxiety_disorders",
      "years_of_experience_in_specialization": 5,
      "is_primary_specialization": true
    }
  ]
}
```

### 2. Approve/Reject/Suspend Specialist

**Endpoint**: `POST /admin/users/specialists/{specialist_id}/action`

**Description**: Approve, reject, or suspend a specialist with reason and admin notes

**Request Body**:
```json
{
  "specialist_id": "123e4567-e89b-12d3-a456-426614174000",
  "action": "approve",
  "reason": "All documents verified and qualifications meet requirements. Specialist has valid license and appropriate experience.",
  "admin_notes": "Background check completed successfully. Ready for practice."
}
```

**Available Actions**:
- `approve`: Approve specialist for practice
- `reject`: Reject specialist application
- `suspend`: Suspend specialist temporarily

**Response**:
```json
{
  "specialist_id": "123e4567-e89b-12d3-a456-426614174000",
  "action": "approve",
  "previous_status": "pending",
  "new_status": "approved",
  "reason": "All documents verified and qualifications meet requirements...",
  "admin_notes": "Background check completed successfully. Ready for practice.",
  "action_performed_by": "admin-uuid",
  "action_performed_at": "2024-01-15T14:30:00Z",
  "success": true,
  "message": "Specialist approved successfully"
}
```

### 3. Activate/Deactivate Patient

**Endpoint**: `POST /admin/users/patients/{patient_id}/action`

**Description**: Activate, deactivate, or suspend a patient with reason and admin notes

**Request Body**:
```json
{
  "patient_id": "456e7890-e89b-12d3-a456-426614174000",
  "action": "activate",
  "reason": "Patient account verification completed. All required information provided and verified.",
  "admin_notes": "Patient can now access full platform features."
}
```

**Available Actions**:
- `activate`: Activate patient account
- `deactivate`: Deactivate patient account
- `suspend`: Suspend patient account temporarily
- `unsuspend`: Unsuspend patient account

**Response**:
```json
{
  "patient_id": "456e7890-e89b-12d3-a456-426614174000",
  "action": "activate",
  "previous_status": "inactive",
  "new_status": "active",
  "reason": "Patient account verification completed...",
  "admin_notes": "Patient can now access full platform features.",
  "action_performed_by": "admin-uuid",
  "action_performed_at": "2024-01-15T14:30:00Z",
  "success": true,
  "message": "Patient activated successfully"
}
```

## Usage Examples

### Python Requests

```python
import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/admin/users"

# Get specialist profile
specialist_id = "123e4567-e89b-12d3-a456-426614174000"
response = requests.get(f"{API_BASE}/specialists/{specialist_id}/profile")
specialist_data = response.json()

# Approve specialist
approve_payload = {
    "specialist_id": specialist_id,
    "action": "approve",
    "reason": "All documents verified and qualifications meet requirements.",
    "admin_notes": "Background check completed successfully."
}

response = requests.post(
    f"{API_BASE}/specialists/{specialist_id}/action",
    json=approve_payload
)

# Activate patient
patient_id = "456e7890-e89b-12d3-a456-426614174000"
activate_payload = {
    "patient_id": patient_id,
    "action": "activate",
    "reason": "Patient account verification completed.",
    "admin_notes": "Patient can now access full platform features."
}

response = requests.post(
    f"{API_BASE}/patients/{patient_id}/action",
    json=activate_payload
)
```

### cURL Examples

```bash
# Get specialist profile
curl -X GET "http://localhost:8000/admin/users/specialists/123e4567-e89b-12d3-a456-426614174000/profile"

# Approve specialist
curl -X POST "http://localhost:8000/admin/users/specialists/123e4567-e89b-12d3-a456-426614174000/action" \
  -H "Content-Type: application/json" \
  -d '{
    "specialist_id": "123e4567-e89b-12d3-a456-426614174000",
    "action": "approve",
    "reason": "All documents verified and qualifications meet requirements.",
    "admin_notes": "Background check completed successfully."
  }'

# Activate patient
curl -X POST "http://localhost:8000/admin/users/patients/456e7890-e89b-12d3-a456-426614174000/action" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "456e7890-e89b-12d3-a456-426614174000",
    "action": "activate",
    "reason": "Patient account verification completed.",
    "admin_notes": "Patient can now access full platform features."
  }'
```

## Implementation Details

### Service Layer

The `UsersManagementService` class provides the core business logic:

```python
class UsersManagementService:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_specialist_profile_with_documents(self, specialist_id: uuid.UUID) -> Optional[SpecialistProfileResponse]:
        # Retrieves complete specialist profile with documents
    
    def approve_reject_specialist(self, request: SpecialistActionRequest, admin_id: uuid.UUID) -> SpecialistActionResponse:
        # Handles specialist approval/rejection/suspension
    
    def activate_deactivate_patient(self, request: PatientActionRequest, admin_id: uuid.UUID) -> PatientActionResponse:
        # Handles patient activation/deactivation/suspension
```

### Data Models

The system uses comprehensive Pydantic schemas for request/response validation:

- `SpecialistProfileResponse`: Complete specialist profile with documents
- `SpecialistActionRequest/Response`: Specialist action handling
- `PatientActionRequest/Response`: Patient action handling
- `ActionTypeEnum`: Available action types
- `UserTypeEnum`: User type classification

### Database Integration

The service integrates with existing SQLAlchemy models:

- `Specialists`: Core specialist information
- `SpecialistsAuthInfo`: Authentication data
- `SpecialistsApprovalData`: Approval process data
- `SpecialistDocuments`: Document storage
- `Patient`: Core patient information
- `PatientAuthInfo`: Patient authentication data

### Audit Trail

All actions are logged with:
- User ID and type
- Action performed
- Previous and new status
- Reason and admin notes
- Timestamp and admin ID
- IP address and user agent (when available)

## Error Handling

The system provides comprehensive error handling:

- **400 Bad Request**: Invalid request data or validation errors
- **404 Not Found**: User not found
- **500 Internal Server Error**: Server-side errors

All errors include detailed messages for debugging.

## Security Considerations

1. **Authentication**: Admin authentication is required (to be implemented)
2. **Authorization**: Role-based access control for admin actions
3. **Input Validation**: Comprehensive request validation
4. **Audit Logging**: All actions are logged for security and compliance
5. **Reason Tracking**: Mandatory reason for all actions ensures accountability

## Testing

Run the test script to verify functionality:

```bash
python test_users_management.py
```

The test script includes examples for all endpoints and demonstrates proper usage patterns.

## Future Enhancements

1. **Admin Authentication**: Implement proper admin authentication middleware
2. **Bulk Operations**: Support for bulk user management actions
3. **Advanced Filtering**: Enhanced search and filter capabilities
4. **Notification System**: Email/SMS notifications for status changes
5. **Dashboard Integration**: Admin dashboard for user management
6. **Export Functionality**: Export user data and audit logs
7. **Advanced Analytics**: User management analytics and reporting

## Dependencies

- FastAPI
- SQLAlchemy
- Pydantic
- Python 3.8+
- PostgreSQL (recommended)

## Installation

1. Ensure all dependencies are installed
2. Import the admin router in your main FastAPI app
3. Configure database connections
4. Set up logging configuration
5. Run the application

```python
from routers.admin_routes import admin_router

app.include_router(admin_router)
```

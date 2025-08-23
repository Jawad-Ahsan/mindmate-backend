# Specialist Matching Agent (SMA) - Complete System

## Overview

The **Specialist Matching Agent (SMA)** is a comprehensive system that connects patients with mental health specialists. It serves as the "marketplace engine" that handles specialist search, matching, ranking, and appointment booking.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Patient Side  │    │   SMA Core      │    │ Specialist Side │
│                 │    │                 │    │                 │
│ • Search        │◄──►│ • Matcher       │◄──►│ • Appointments  │
│ • Book          │    │ • Appointments  │    │ • Confirm       │
│ • Manage        │    │ • Profiles      │    │ • Complete      │
│ • Recommendations│   │ • Reports       │    │ • Statistics    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🎯 Core Features

### 1. **Specialist Search & Matching**
- **Filtering**: Location, specialization, budget, languages, availability
- **Ranking**: AI-powered scoring based on patient preferences
- **Fallbacks**: Default preferences when user doesn't specify
- **Pagination**: Efficient browsing of large result sets

### 2. **Appointment Management**
- **Two-Step Booking**: Hold → Confirm flow for reliability
- **Slot Management**: Real-time availability tracking
- **Lifecycle Management**: Schedule, confirm, complete, cancel, reschedule
- **Notifications**: Email/SMS notifications for all events

### 3. **Profile Management**
- **Public Profiles**: Patient-accessible specialist information
- **Protected Profiles**: Admin-only detailed information
- **Private Profiles**: Specialist-only personal information

### 4. **Patient Reports**
- **Assessment Reports**: Comprehensive patient evaluations
- **Risk Assessment**: Safety and risk level analysis
- **Recommendations**: Treatment and specialist recommendations

## 📁 File Structure

```
agents/sma/
├── __init__.py                 # Package initialization
├── sma.py                     # Main SMA orchestrator
├── specialits_matcher.py      # Core matching logic
├── appointments_manager.py    # Appointment lifecycle management
├── sma_schemas.py            # Pydantic models and schemas
├── geo_locater.py            # Location-based services
├── README.md                 # This documentation
└── test_sma.py              # Unit tests
```

## 🚀 Quick Start

### 1. **Initialize SMA**
```python
from agents.sma.sma import SMA
from database.database import get_db

db = next(get_db())
sma = SMA(db)
```

### 2. **Search for Specialists**
```python
from agents.sma.sma_schemas import SpecialistSearchRequest, ConsultationMode

request = SpecialistSearchRequest(
    consultation_mode=ConsultationMode.ONLINE,
    languages=["English", "Urdu"],
    specializations=["anxiety_disorders"],
    budget_max=5000.0,
    page=1,
    size=10
)

result = sma.search_specialists(request)
print(f"Found {result['total_count']} specialists")
```

### 3. **Book an Appointment**
```python
# Step 1: Hold a slot
hold_request = SlotHoldRequest(
    slot_id=slot_uuid,
    patient_id=patient_uuid,
    hold_duration_minutes=10
)
hold_result = sma.hold_slot(hold_request)

# Step 2: Confirm appointment
confirm_request = AppointmentConfirmRequest(
    patient_id=patient_uuid,
    hold_token=hold_result['hold_token'],
    consultation_mode=ConsultationMode.ONLINE
)
appointment = sma.confirm_appointment(confirm_request)
```

## 🔌 API Endpoints

### Patient Endpoints (`/patient-sma`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search-specialists` | GET | Search specialists with filters |
| `/top-specialists` | GET | Get top N specialists |
| `/specialist/{id}` | GET | Get specialist details |
| `/specialist/{id}/slots` | GET | Get available slots |
| `/hold-slot` | POST | Hold a slot for booking |
| `/confirm-appointment` | POST | Confirm appointment |
| `/my-appointments` | GET | Get patient appointments |
| `/appointments/{id}/cancel` | POST | Cancel appointment |
| `/appointments/{id}/reschedule` | POST | Reschedule appointment |
| `/recommendations` | GET | Get personalized recommendations |

### Specialist Endpoints (`/specialist-sma`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/my-appointments` | GET | Get specialist appointments |
| `/appointments/{id}` | GET | Get appointment details |
| `/appointments/{id}/confirm` | POST | Confirm appointment |
| `/appointments/{id}/cancel` | POST | Cancel appointment |
| `/appointments/{id}/reschedule` | POST | Reschedule appointment |
| `/appointments/{id}/complete` | POST | Complete appointment |
| `/my-profile` | GET | Get public profile |
| `/my-slots` | GET | Get available slots |
| `/patients/{id}/report` | GET | Get patient report |
| `/statistics` | GET | Get specialist statistics |

## 🧠 Matching Algorithm

### Scoring Weights
```python
weights = {
    'specialization_match': 3.0,    # Highest priority
    'language_overlap': 2.0,        # Communication
    'rating_score': 1.5,           # Quality indicator
    'availability_soonness': 1.5,   # Timeliness
    'experience_score': 1.0,       # Expertise
    'budget_closeness': 1.0,       # Affordability
    'location_match': 0.5          # Geographic proximity
}
```

### Scoring Process
1. **Hard Filters**: Apply non-negotiable constraints
2. **Soft Scoring**: Calculate weighted scores for each specialist
3. **Ranking**: Sort by total score
4. **Fallbacks**: Apply defaults if no preferences specified

## 📊 Data Models

### Core Entities
- **Specialists**: Professional information and credentials
- **Patients**: Demographics and preferences
- **Appointments**: Booking and session management
- **Slots**: Availability and scheduling
- **Reports**: Patient assessments and recommendations

### Key Relationships
```
Patient ──► Appointments ──► Specialist
Patient ──► Preferences ──► Matching Criteria
Specialist ──► Specializations ──► Expertise Areas
Appointment ──► Slot ──► Availability
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mindmate

# SMA Settings
SMA_HOLD_DURATION_MINUTES=10
SMA_MAX_CONCURRENT_HOLDS=3
SMA_DEFAULT_BUDGET=5000.0
SMA_DEFAULT_LANGUAGES=["English", "Urdu"]
```

### Default Preferences
```python
default_prefs = {
    "consultation_mode": "online",
    "languages": ["English", "Urdu"],
    "budget_max": 5000.0,
    "specialist_type": "psychologist",
    "specializations": ["general"]
}
```

## 🧪 Testing

### Run Integration Tests
```bash
cd App/backend-1
python test_sma_integration.py
```

### Test Coverage
- ✅ Basic functionality
- ✅ Advanced search and filtering
- ✅ Appointment booking flow
- ✅ Error handling
- ✅ Health checks

## 🔒 Security & Privacy

### Access Control
- **Patient Routes**: Require patient authentication
- **Specialist Routes**: Require specialist authentication
- **Admin Routes**: Require admin authentication

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **Audit Logs**: All actions logged for compliance
- **GDPR Compliance**: Patient data handling compliant

## 📈 Performance

### Optimization Strategies
- **Database Indexing**: Optimized queries for fast searches
- **Caching**: Redis caching for frequently accessed data
- **Pagination**: Efficient handling of large result sets
- **Async Processing**: Background tasks for notifications

### Monitoring
- **Health Checks**: `/health` endpoint for system status
- **Metrics**: Performance and usage statistics
- **Logging**: Comprehensive logging for debugging

## 🚀 Deployment

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (optional, for caching)
- FastAPI

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the application
uvicorn main:app --reload
```

## 🔮 Future Enhancements

### Planned Features
- **AI-Powered Matching**: Machine learning for better recommendations
- **Video Integration**: Built-in video consultation platform
- **Payment Processing**: Integrated payment gateway
- **Analytics Dashboard**: Advanced reporting and insights
- **Mobile App**: Native mobile applications

### Scalability Improvements
- **Microservices**: Break down into smaller services
- **Load Balancing**: Distribute traffic across instances
- **Database Sharding**: Horizontal scaling for large datasets
- **CDN Integration**: Global content delivery

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Standards
- **Type Hints**: All functions must have type annotations
- **Documentation**: Comprehensive docstrings
- **Testing**: Minimum 80% test coverage
- **Linting**: Follow PEP 8 standards

## 📞 Support

### Documentation
- **API Docs**: Available at `/docs` when running
- **Code Comments**: Inline documentation
- **Examples**: Test files with usage examples

### Contact
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Email**: Support email for urgent issues

---

**SMA System** - Connecting patients with the right mental health specialists, one match at a time. 🧠💙

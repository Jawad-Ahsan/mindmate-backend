# TPA Utility - Simplified Treatment Planning Agent

A simplified interface for creating and exporting treatment plans without the complexity of tracking mechanisms.

## Quick Start

```python
from utilize_tpa import TPAUtil, PatientData

# Simple dictionary approach
patient_data = {
    "age": 30,
    "gender": "female",
    "primary_diagnosis": "Generalized Anxiety Disorder",
    "severity": "moderate",
    "symptoms": ["panic attacks", "constant worry", "sleep issues"],
    "primary_goals": ["Reduce anxiety", "Improve sleep"]
}

tpa = TPAUtil()
plan = tpa.get_treatment_plan(patient_data)

# Export to different formats
tpa.export_plan(plan, 'json', 'plan.json')
tpa.export_plan(plan, 'markdown', 'plan.md')
```

## Features

- ✅ **Simple Interface**: Single `get_treatment_plan(data)` method
- ✅ **Multiple Export Formats**: JSON, text, markdown, HTML
- ✅ **Type Safety**: Optional `PatientData` class for validation
- ✅ **No Tracking Complexity**: Focused on plan creation and export
- ✅ **Evidence-Based**: Uses TPA's comprehensive treatment guidelines

## Installation & Usage

### Basic Usage

```python
from utilize_tpa import get_treatment_plan

# Minimal patient data
data = {
    "age": 28,
    "gender": "female",
    "primary_diagnosis": "Major Depressive Disorder",
    "severity": "moderate",
    "symptoms": ["low mood", "fatigue", "loss of interest"],
    "primary_goals": ["Improve mood", "Increase energy"]
}

plan = get_treatment_plan(data)
print(f"Plan: {plan.title}")
print(f"Goal: {plan.goal}")
```

### Using PatientData Class

```python
from utilize_tpa import TPAUtil, PatientData

patient = PatientData(
    age=35,
    gender="male",
    occupation="engineer",
    primary_diagnosis="Generalized Anxiety Disorder",
    severity="moderate",
    symptoms=["panic attacks", "worry", "tension"],
    primary_goals=["Reduce anxiety", "Better coping"],
    weekly_time_commitment=10,
    preferred_approach="self_help"
)

tpa = TPAUtil()
plan = tpa.get_treatment_plan(patient)
```

### Export Options

```python
# Export to different formats
tpa.export_plan(plan, 'json')        # Returns JSON string
tpa.export_plan(plan, 'text')        # Returns formatted text
tpa.export_plan(plan, 'markdown')    # Returns markdown
tpa.export_plan(plan, 'html')        # Returns HTML

# Save to file
tpa.export_plan(plan, 'json', 'treatment_plan.json')
tpa.export_plan(plan, 'markdown', 'plan.md')
```

## Patient Data Format

### Required Fields
- `age`: Patient age (integer)
- `gender`: Patient gender (string)
- `primary_diagnosis`: Mental health diagnosis (string)
- `severity`: Symptom severity ("mild", "moderate", "severe")
- `symptoms`: List of symptoms (array of strings)

### Optional Fields
- `occupation`: Patient's job/occupation
- `primary_goals`: List of treatment goals
- `treatment_preferences`: Preferred treatment types
- `weekly_time_commitment`: Hours per week for treatment (1-20)
- `preferred_approach`: "self_help", "therapy", or "hybrid"
- `mode_preference`: "online", "in_person", or "hybrid"
- `budget_level`: "free", "low_cost", or "premium"
- `red_flags`: Safety concerns or risk factors

## Output Format

The treatment plan includes:

```python
{
    "patient_id": "unique_identifier",
    "title": "8-week plan to reduce anxiety & improve daily life",
    "goal": "Feel calmer and more in control of daily life",
    "top_actions": [
        "Weekly CBT sessions (50 min) — focus on thought challenging",
        "Daily mindfulness practice (10 min) — reduce racing thoughts",
        "Regular sleep routine — improve sleep quality"
    ],
    "step_by_step": [
        {
            "step_number": 1,
            "title": "Learn Thought Challenging",
            "description": "Practice identifying and challenging negative thoughts",
            "when": "Daily",
            "how_long": "15 minutes",
            "why": "Helps break the cycle of anxious thinking",
            "how_to_track": "Rate anxiety before/after (0-10 scale)"
        }
    ],
    "weekly_plan": {
        "Week 1": ["Onboarding + first steps + start daily routine"],
        "Weeks 2-7": ["Continue skills + weekly check-ins + homework"],
        "Week 8": ["Review & plan next steps"]
    },
    "safety_note": "If your mood drops quickly or you have thoughts of self-harm...",
    "plan_metadata": {
        "total_duration": "8 weeks",
        "total_steps": 12,
        "estimated_time_per_day": "25 minutes",
        "frequency": "Daily"
    },
    "reminder_schedule": "Daily reminders at 9 AM"
}
```

## Supported Conditions

The TPA utility supports evidence-based treatment plans for:

- **Mood Disorders**: Major Depressive Disorder, Bipolar Disorder
- **Anxiety Disorders**: Generalized Anxiety Disorder, Panic Disorder, Social Anxiety
- **Trauma Disorders**: PTSD, Adjustment Disorder
- **OCD**: Obsessive-Compulsive Disorder
- **Sleep Disorders**: Insomnia Disorder
- **Other**: ADHD, Eating Disorders, Substance Use Disorders

## Examples

See `example_usage.py` for comprehensive examples including:

- Basic usage with dictionary data
- Type-safe usage with PatientData class
- Different mental health conditions
- Quick plan creation
- Export to multiple formats

## Running Examples

```bash
cd /path/to/mindmate/backend/agents/tpa
python example_usage.py
```

This will create sample treatment plans and export them to different formats.

## API Reference

### TPAUtil Class

#### Methods
- `get_treatment_plan(data)`: Create treatment plan
- `export_plan(plan, format, filepath)`: Export plan to different formats
- `quick_plan_from_dict(data)`: Create and return plan as dictionary

### Convenience Functions
- `get_treatment_plan(data)`: Direct access to plan creation
- `export_plan(plan, format, filepath)`: Direct access to export

### PatientData Class
Type-safe class for patient information with validation.

## Integration

This utility is designed to be easily integrated into existing systems:

```python
# From a web API
@app.post("/treatment-plan")
def create_plan(patient_data: dict):
    tpa = TPAUtil()
    plan = tpa.get_treatment_plan(patient_data)
    return tpa.export_plan(plan, 'json')

# From a data pipeline
def process_patient_records(records):
    tpa = TPAUtil()
    plans = []
    for record in records:
        plan = tpa.get_treatment_plan(record)
        plans.append(plan)
    return plans
```

## Performance

- Plan creation: ~2-5 seconds depending on complexity
- Export: Near instantaneous
- Memory usage: Minimal (no tracking overhead)

## Error Handling

The utility includes comprehensive error handling:

```python
try:
    plan = tpa.get_treatment_plan(patient_data)
except Exception as e:
    print(f"Error creating plan: {e}")
    # Handle error appropriately
```

## Dependencies

- Python 3.7+
- TPA core modules (tpa_, tpa_schemas, tpa_tools, treatment_guidelines)
- Standard library modules (json, pathlib, datetime)

No external dependencies required for basic functionality.

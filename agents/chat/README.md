# MindMate - Mental Health Assessment Chatbot

🧠 **A ReAct-based chatbot for mental health concern assessment**

MindMate is a compassionate AI companion that conducts structured mental health assessments through natural conversation. It collects patient information across 10 key areas and generates comprehensive assessment reports.

## 🎯 Features

- **ReAct Architecture**: Reason → Act → Collect structured data
- **10-Question Flow**: Complete mental health assessment protocol
- **Natural Language Processing**: Maps free text to structured categories
- **Follow-up Handling**: One gentle clarification per question (max)
- **Error Resilience**: Never breaks, always responds empathetically
- **Report Generation**: Creates clinical-ready assessment summaries

## 📋 The 10 Assessment Questions

1. **Presenting Concern** - "What brings you here today?"
2. **Onset** - "When did you first start noticing these feelings?"
3. **Severity** - "On a scale of 1-10, how would you rate the intensity?"
4. **Frequency** - "How often do you experience these feelings?"
5. **Triggers** - "What situations make these feelings worse?"
6. **Work Impact** - "How have these feelings affected your work?"
7. **Prior Episodes** - "Have you experienced similar feelings before?"
8. **ADL Impact** - "How are these feelings affecting your daily activities?"
9. **Social Impact** - "How have these feelings affected your relationships?"
10. **Report Generation** - Comprehensive assessment summary

## 🚀 Quick Start

### Option 1: Simple Demonstration
```bash
python chatbot.py simple
```
Shows the complete 10-question flow with example responses.

### Option 2: Interactive Demo
```bash
python chatbot.py demo
```
Run through a complete assessment with pre-defined responses.

### Option 3: Full Interactive Chat
```bash
python chatbot.py
```
Start a real conversation with MindMate.

## 📊 Structured Data Output

Each assessment captures these structured fields:

```python
{
    "presenting_concern": "Anxiety",  # Primary concern category
    "hpi_onset": "Recently (past week)",  # When symptoms started
    "hpi_severity": 7,  # 1-10 severity rating
    "hpi_frequency": "Daily",  # How often symptoms occur
    "hpi_triggers": "Work stress",  # What worsens symptoms
    "hpi_impact_work": "Significant impact",  # Work/responsibility impact
    "hpi_prior_episodes": "Never before",  # Previous similar episodes
    "function_ADL": "Moderate difficulty",  # Daily living impact
    "social_activities": "Avoiding some activities",  # Social relationship impact
    "assessment_timestamp": "2024-01-01T12:00:00Z",
    "assessment_complete": true
}
```

## 🛠️ Technical Architecture

### Assessment Tools
Each question is handled by a specialized tool:

- **ConcernCollectorTool** - Maps natural language to concern categories
- **OnsetTool** - Temporal analysis of symptom onset
- **SeverityTool** - Numeric rating extraction and mapping
- **FrequencyTool** - Frequency pattern recognition
- **TriggersTool** - Trigger identification and categorization
- **ImpactWorkTool** - Work/responsibility impact assessment
- **PriorEpisodesTool** - Episode history analysis
- **ADLTool** - Activities of Daily Living impact
- **SocialActivitiesTool** - Social functioning assessment
- **ReportCreatorTool** - Final report generation

### State Management
- **LangGraph Integration**: Workflow orchestration (with fallback)
- **Session Persistence**: Maintains conversation context
- **Error Recovery**: Graceful handling of tool failures
- **Follow-up Logic**: Max one clarification per question

### NLP Mapping Examples

#### Concern Mapping
```
"feeling anxious" → "Anxiety"
"depressed and sad" → "Depression"
"work stress" → "Work-related stress"
"sleep issues" → "Sleep issues"
```

#### Severity Mapping
```
"very mild" → 2
"moderate" → 5
"severe" → 7
"unbearable" → 9
```

## 💬 Usage Examples

### Basic Interaction
```
🧠 MindMate: What brings you here today?
💭 You: I've been feeling really anxious lately

🧠 MindMate: Thank you for sharing what's been troubling you...
🧠 MindMate: When did you first start noticing these feelings?
💭 You: About two weeks ago
```

### Ambiguity Handling
```
🧠 MindMate: On a scale of 1-10, how would you rate the intensity?
💭 You: Pretty bad

🧠 MindMate: On that scale of 1 to 10, what number feels right to you for how intense these feelings are?
💭 You: I'd say about 7
```

## 📝 Commands

During interactive chat:
- `help` - Show available commands
- `reset` - Start a new assessment
- `report` - View current assessment data
- `quit` - Exit the conversation

## 🔧 Configuration

### Dependencies
- Python 3.8+
- LangGraph (optional - includes fallback implementation)
- Standard library modules (json, datetime, typing, etc.)

### Environment Variables
```bash
# Optional: For LLM integration (future enhancement)
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=llama3-8b-8192
```

## 🎨 Patient Experience

- **Empathetic Communication**: Each question includes context-aware empathy
- **Natural Flow**: Feels like talking to a compassionate professional
- **Clarification Support**: Gentle follow-ups when responses are unclear
- **Privacy Conscious**: All interactions are confidential
- **Pace Respectful**: Patients can take breaks anytime

## 📋 Clinical Integration

The structured output is designed for integration with:
- Electronic Health Records (EHR) systems
- Clinical decision support tools
- Risk assessment algorithms
- Treatment planning workflows
- Progress tracking systems

## 🚨 Important Notes

- **Not a Replacement**: This tool augments clinical assessment, doesn't replace it
- **Confidentiality**: All patient data should be handled according to HIPAA/privacy regulations
- **Cultural Sensitivity**: NLP mappings are English-focused; localization needed for other languages
- **Clinical Validation**: Assessment categories should be validated by mental health professionals

## 🤝 Contributing

This is a demonstration implementation. For production use:
1. Add comprehensive validation of NLP mappings
2. Implement proper data encryption and privacy controls
3. Add integration with clinical workflows
4. Include cultural and linguistic adaptations
5. Add comprehensive error logging and monitoring

## 📄 License

This implementation is provided for educational and demonstration purposes.

---

**Remember**: Mental health assessment requires clinical expertise. This tool demonstrates the technical architecture for structured data collection through conversational AI.</content>
</xai:function_call">README.md

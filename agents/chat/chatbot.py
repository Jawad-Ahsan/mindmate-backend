import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from dataclasses import dataclass
import re
import threading
from collections import deque

# Import your LLM client
from agents.llm_client import AgentLLMClient

# Import database models and utilities
from models import ChatSession, ChatMessage, ChatConversationSummary
from database.database import get_db
from sqlalchemy.orm import Session
from typing import Optional
import uuid

# Import appointment tool
from .appointment_tool import AppointmentTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mindmate.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define the state
class MindMateState(TypedDict):
    messages: Annotated[List[str], operator.add]
    reasoning: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    current_step: str
    user_input: str
    final_response: str
    conversation_context: Dict[str, Any]
    followup_count: int
    severity_assessment: Optional[str]
    requires_specialist: bool

class ConversationMemory:
    """Enhanced memory for WhatsApp-style conversations with database persistence"""

    def __init__(self, llm_client, max_messages=15, summary_threshold=10, db_session: Optional[Session] = None, patient_id: Optional[str] = None):
        self.llm_client = llm_client
        self.max_messages = max_messages
        self.summary_threshold = summary_threshold
        self.db_session = db_session
        self.patient_id = patient_id
        self.messages = deque(maxlen=max_messages)
        self.conversation_summary = ""
        self.key_points = {}
        self.session_data = {
            "start_time": datetime.now(),
            "message_count": 0,
            "main_concern": None,
            "mood_trend": "neutral"
        }
        self._lock = threading.Lock()

        # Database session tracking
        self.chat_session = None
        if self.db_session and self.patient_id:
            self._initialize_db_session()

    def _initialize_db_session(self):
        """Initialize database chat session"""
        try:
            # Create new chat session
            session_id = str(uuid.uuid4())
            self.chat_session = ChatSession(
                session_id=session_id,
                patient_id=self.patient_id,
                status="active"
                # created_at and updated_at are handled by server_default
            )
            self.db_session.add(self.chat_session)
            self.db_session.commit()
            logger.info(f"Chat session initialized: {session_id}")
        except Exception as e:
            logger.error(f"Failed to initialize chat session: {e}")
            self.chat_session = None

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message with quick summarization and database persistence"""
        with self._lock:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            self.messages.append(message)
            self.session_data["message_count"] += 1

            # Quick mood detection
            if role == "user":
                self._quick_mood_check(content)

            # Save to database if available
            if self.db_session and self.chat_session:
                self._save_message_to_db(role, content, metadata)

            # Light summarization when needed
            if len(self.messages) >= self.summary_threshold:
                self._quick_summary()

    def _save_message_to_db(self, role: str, content: str, metadata: Dict = None):
        """Save message to database"""
        # Skip database operations if session management is disabled
        if not self.db_session or not self.chat_session:
            return

        try:
            # Create ChatMessage record with only valid columns
            chat_message = ChatMessage(
                session_id=self.chat_session.session_id,
                role=role,
                content=content,
                metadata_json=metadata  # Store all metadata as JSON
            )

            self.db_session.add(chat_message)
            self.db_session.commit()
            logger.debug(f"Saved {role} message to database")

        except Exception as e:
            logger.error(f"❌ Failed to save message to database: {e}")
            if self.db_session:
                self.db_session.rollback()
    
    def _quick_mood_check(self, content: str):
        """Quick mood detection for better responses"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["great", "good", "better", "happy", "thanks"]):
            self.session_data["mood_trend"] = "positive"
        elif any(word in content_lower for word in ["bad", "worse", "terrible", "awful", "sad", "anxious"]):
            self.session_data["mood_trend"] = "negative"
        elif any(word in content_lower for word in ["okay", "fine", "same", "alright"]):
            self.session_data["mood_trend"] = "neutral"
    
    def _quick_summary(self):
        """Create brief conversation summary"""
        try:
            recent_messages = list(self.messages)[-6:]
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_messages
            ])
            
            summary_prompt = f"""Summarize this chat in 2-3 short sentences:
            
            {conversation_text}
            
            Focus on: main concern, current mood, what help was offered.
            Keep it brief like a WhatsApp summary."""
            
            new_summary = self.llm_client.generate(
                summary_prompt,
                temperature=0.3,
                max_tokens=100
            )
            
            if not new_summary.startswith("Error:"):
                self.conversation_summary = new_summary
                
        except Exception as e:
            logger.error(f"Error creating summary: {e}")
    
    def get_quick_context(self) -> str:
        """Get relevant context for responses"""
        context_parts = []
        
        # Add summary if available
        if self.conversation_summary:
            context_parts.append(f"Previous chat: {self.conversation_summary}")
        
        # Add recent messages (last 3)
        recent_messages = list(self.messages)[-3:]
        if recent_messages:
            recent_text = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent_messages
            ])
            context_parts.append(f"Recent:\n{recent_text}")
        
        return "\n\n".join(context_parts)
    
    def clear_memory(self):
        """Clear memory for new conversation"""
        with self._lock:
            self.messages.clear()
            self.conversation_summary = ""
            self.key_points = {}
            self.session_data = {
                "start_time": datetime.now(),
                "message_count": 0,
                "main_concern": None,
                "mood_trend": "neutral"
            }

class QuickFollowUpTool:
    name = "ask_followup"
    description = "Ask one quick follow-up question"
    
    def __init__(self):
        self.questions = {
            "anxiety": [
                "How long have you been feeling this way?",
                "What usually triggers it?",
                "How's it affecting your daily routine?",
                "Have you tried anything that helps?"
            ],
            "depression": [
                "When did this start?",
                "How are you sleeping?",
                "Are you eating okay?",
                "Who do you usually talk to?"
            ],
            "stress": [
                "What's causing the most stress right now?",
                "How's your sleep been?",
                "When do you feel it most?",
                "What usually helps you relax?"
            ],
            "general": [
                "Can you tell me more about that?",
                "How long has this been going on?",
                "How's it affecting you day to day?",
                "What would help most right now?"
            ]
        }
    
    def run(self, context: str) -> str:
        """Generate one appropriate follow-up question"""
        try:
            context_lower = context.lower()
            
            if any(word in context_lower for word in ["anxious", "worry", "panic"]):
                category = "anxiety"
            elif any(word in context_lower for word in ["sad", "depressed", "down"]):
                category = "depression"
            elif any(word in context_lower for word in ["stress", "overwhelmed", "pressure"]):
                category = "stress"
            else:
                category = "general"
            
            question = random.choice(self.questions[category])
            
            return json.dumps({
                "question": question,
                "category": category
            })
            
        except Exception as e:
            logger.error(f"Follow-up error: {e}")
            return json.dumps({
                "question": "Tell me more about how you're feeling?",
                "category": "general"
            })

class QuickSolutionTool:
    name = "give_solution"
    description = "Give detailed, actionable step-by-step solutions"
    
    def __init__(self):
        self.solutions = {
            "anxiety": {
                "title": "Anxiety Relief Action Plan",
                "steps": [
                    "Step 1: Find a quiet, comfortable place where you won't be disturbed for the next 10 minutes",
                    "Step 2: Sit or lie down in a comfortable position and close your eyes if it feels safe",
                    "Step 3: Place one hand on your chest and one on your belly to feel your breathing",
                    "Step 4: Try the 4-7-8 breathing technique: Inhale quietly through your nose for 4 seconds",
                    "Step 5: Hold your breath for 7 seconds - this may feel uncomfortable at first but gets easier",
                    "Step 6: Exhale slowly through your mouth for 8 seconds, making a gentle whooshing sound",
                    "Step 7: Repeat this cycle 4 times - focus only on the counting and your breath",
                    "Step 8: Notice how your body feels after these breathing cycles - you may feel calmer",
                    "Step 9: Try a quick grounding exercise: Name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste",
                    "Step 10: Do something small and positive - make yourself a cup of tea, listen to your favorite song, or call a friend",
                    "Step 11: If anxiety persists, try a short 10-minute walk outside in nature or around your home",
                    "Step 12: Write down three things you're grateful for today, no matter how small",
                    "Step 13: Practice progressive muscle relaxation: Tense and release each muscle group from your toes to your head",
                    "Step 14: Limit caffeine and sugar intake today as they can worsen anxiety symptoms",
                    "Step 15: Set a small, achievable goal for today and celebrate completing it"
                ],
                "emergency_note": "If your anxiety feels overwhelming or you have thoughts of harming yourself, please contact emergency services (112) or a mental health professional immediately."
            },
            "depression": {
                "title": "Depression Management Action Plan",
                "steps": [
                    "Step 1: Start your day with a simple routine - make your bed, brush your teeth, get dressed",
                    "Step 2: Open your curtains or blinds to let in natural sunlight, even if just for 10 minutes",
                    "Step 3: Eat something nourishing - prepare a simple meal or snack that you enjoy",
                    "Step 4: Do one small physical activity - stretch for 5 minutes, dance to a song, or walk around your room",
                    "Step 5: Connect with someone - send a text, make a phone call, or interact with a pet",
                    "Step 6: Practice self-compassion - say kind words to yourself like you would to a friend",
                    "Step 7: Set one tiny goal for today - something as small as 'drink a glass of water'",
                    "Step 8: Listen to uplifting music or a podcast that makes you feel good",
                    "Step 9: Try a creative activity - draw, color, write, or work on a hobby for 15 minutes",
                    "Step 10: Practice deep breathing - inhale for 4 counts, hold for 4, exhale for 6",
                    "Step 11: Spend time in nature - step outside, look at the sky, feel the air on your skin",
                    "Step 12: Write down three things you appreciate about yourself or your life",
                    "Step 13: Do something kind for someone else - a small act of kindness can boost your mood",
                    "Step 14: Limit social media time and focus on real-world connections instead",
                    "Step 15: End your day by writing what went well today, no matter how small"
                ],
                "emergency_note": "If depression is severe and you feel unable to function, please seek immediate professional help."
            },
            "stress": {
                "title": "Stress Reduction Action Plan",
                "steps": [
                    "Step 1: Identify your main stressors - write down what's causing you the most stress right now",
                    "Step 2: Prioritize what you can control - focus on one thing you can actually change today",
                    "Step 3: Take a 5-minute break - step away from your stressors and breathe deeply",
                    "Step 4: Try progressive muscle relaxation - tense and release muscle groups throughout your body",
                    "Step 5: Listen to calming music or nature sounds for 10 minutes",
                    "Step 6: Do a quick body scan meditation - focus attention on different parts of your body",
                    "Step 7: Write down your worries - getting them out of your head can reduce their power",
                    "Step 8: Practice positive self-talk - replace negative thoughts with kinder, more realistic ones",
                    "Step 9: Do something enjoyable for 15 minutes - read, watch a funny video, or call a friend",
                    "Step 10: Exercise or move your body - even 10 minutes of stretching or walking can help",
                    "Step 11: Practice time management - break overwhelming tasks into smaller, manageable steps",
                    "Step 12: Set boundaries - learn to say no to additional commitments when you're already stressed",
                    "Step 13: Connect with others - talk to someone you trust about what's stressing you",
                    "Step 14: Practice mindfulness - focus on the present moment without judgment",
                    "Step 15: Prepare for tomorrow - lay out clothes, prepare lunch, or make a to-do list to reduce morning stress"
                ],
                "emergency_note": "If stress is causing physical symptoms or interfering with daily life, consider speaking with a healthcare professional."
            },
            "general": {
                "title": "Mental Wellness Action Plan",
                "steps": [
                    "Step 1: Start with deep breathing - inhale for 4 counts, hold for 4, exhale for 6",
                    "Step 2: Ground yourself in the present - name 5 things you see, 4 you can touch, 3 you can hear",
                    "Step 3: Do one small act of self-care - take a warm shower, drink water, or eat something nourishing",
                    "Step 4: Move your body gently - stretch, walk, or dance for 10 minutes",
                    "Step 5: Connect with someone - text a friend, call family, or pet your animal companion",
                    "Step 6: Practice gratitude - write down 3 things you're thankful for today",
                    "Step 7: Limit screen time - take a break from social media and news for at least 30 minutes",
                    "Step 8: Try a creative outlet - draw, write, play music, or work on a hobby",
                    "Step 9: Spend time in nature - step outside, look at the sky, listen to birds",
                    "Step 10: Practice positive affirmations - repeat kind words about yourself",
                    "Step 11: Set a small goal - something achievable that will make you feel accomplished",
                    "Step 12: Do something kind for yourself or others - small acts of kindness boost mood",
                    "Step 13: Practice good sleep hygiene - dim lights, avoid screens before bed",
                    "Step 14: Learn something new - read an article, watch an educational video, or try a new recipe",
                    "Step 15: End the day with reflection - what went well today, what can you improve tomorrow"
                ],
                "emergency_note": "Remember that seeking help is a sign of strength, not weakness."
            }
        }
    
    def run(self, context: str) -> str:
        """Give detailed, actionable step-by-step solutions"""
        try:
            context_lower = context.lower()
            
            # Determine category based on context
            if any(word in context_lower for word in ["anxious", "worry", "panic", "nervous", "fear"]):
                category = "anxiety"
            elif any(word in context_lower for word in ["sad", "depressed", "down", "hopeless", "empty"]):
                category = "depression"
            elif any(word in context_lower for word in ["stress", "overwhelmed", "pressure", "busy", "tired"]):
                category = "stress"
            else:
                category = "general"
            
            solution_data = self.solutions[category]

            # Create detailed response with all steps
            response_parts = [
                f"💙 **{solution_data['title']}** 💙",
                "",
                "Here's a comprehensive step-by-step plan to help you feel better:"
            ]

            # Add all 15 steps
            for step in solution_data['steps']:
                response_parts.append(f"• {step}")

            response_parts.extend([
                "",
                f"💡 **{solution_data['emergency_note']}**",
                "",
                "🌟 You're taking an important step by being proactive about your mental health. Remember, small consistent actions create big changes over time!"
            ])

            detailed_solution = "\n".join(response_parts)
            
            return json.dumps({
                "solution": detailed_solution,
                "category": category,
                "step_count": len(solution_data['steps']),
                "note": "Take it one step at a time 💙"
            })
            
        except Exception as e:
            logger.error(f"Solution error: {e}")
            return json.dumps({
                "solution": "Here are some immediate steps you can take:\n\n• Take 5 deep breaths\n• Drink a glass of water\n• Step outside for fresh air\n• Call or text someone you trust\n• Do one small thing that brings you comfort\n\nYou're not alone in this 💙",
                "category": "general",
                "note": "I'm here to support you through this 💙"
            })

class QuickInfoTool:
    name = "share_info"
    description = "Share brief mental health info"
    
    def __init__(self):
        self.info = {
            "anxiety": "Anxiety is your mind trying to protect you, but sometimes it gets a bit overzealous. Very treatable with the right support.",
            "depression": "Depression is like a filter that makes everything seem harder. It's not your fault, and it can get better with help.",
            "stress": "Stress is normal, but chronic stress needs attention. Your body and mind need breaks to reset.",
            "panic": "Panic attacks feel scary but aren't dangerous. They usually peak in 10 minutes and always pass.",
            "help": "Professional support can make a huge difference. In Pakistan: Mental Health Helpline 0800-00-786"
        }
    
    def run(self, topic: str) -> str:
        """Get brief info about mental health topics"""
        try:
            topic_lower = topic.lower()
            
            info_text = None
            for key, value in self.info.items():
                if key in topic_lower:
                    info_text = value
                    break
            
            if not info_text:
                info_text = "Mental health matters just like physical health. It's okay to need support sometimes."
            
            return json.dumps({
                "info": info_text,
                "topic": topic
            })
            
        except Exception as e:
            logger.error(f"Info error: {e}")
            return json.dumps({
                "info": "Taking care of your mental health is important. Professional help is available when you need it.",
                "topic": topic
            })

# Initialize tools
MINDMATE_TOOLS = {
    "ask_followup": QuickFollowUpTool(),
    "give_solution": QuickSolutionTool(),
    "share_info": QuickInfoTool(),
    "book_appointment": None  # Will be initialized per instance
}

class MindMate:
    """
    MindMate: WhatsApp-Style Mental Health Companion
    Brief, friendly, supportive conversations
    
    Created by Hammad Munir & Jawad Ahsan
    """
    
    def __init__(self, db_session: Optional[Session] = None, patient_id: Optional[str] = None):
        """Initialize MindMate for WhatsApp-style conversations with database integration"""
        self.llm_client = AgentLLMClient(
            agent_name="MindMate",
            system_prompt="""You are MindMate, a supportive friend for mental health chats. Keep conversations like WhatsApp - brief, friendly, natural.

CONVERSATION STYLE:
- Keep responses SHORT (1-3 sentences max)
- Be warm and conversational like texting a friend
- Use simple, clear language
- No long paragraphs or formal tone
- Be supportive but not overwhelming

RESPONSE PATTERNS:
- For concerns: Listen, then ask ONE follow-up question
- After 2-3 questions: Give 2-3 practical tips
- For info requests: Brief, helpful explanation
- For casual chat: Friendly, encouraging response

WHEN TO USE TOOLS:
- book_appointment: When they want to book/schedule/see a specialist
- ask_followup: When someone shares a problem (max 3 questions)
- give_solution: After understanding the issue (2-3 practical tips)
- share_info: When they ask about mental health topics

KEEP IT SIMPLE:
- One main point per message
- Ask one question at a time
- Give solutions as brief bullet points
- Always end with encouragement

CRISIS SITUATIONS:
- For serious concerns: Recommend professional help
- Pakistan resources: Mental Health Helpline 0800-00-786
- Emergency: Always suggest calling 1122

Remember: You're a supportive friend, not a therapist. Keep it conversational, brief, and caring."""
            # Model is now inherited from environment config (CEREBRAS_MODEL)
        )

        self.db_session = db_session
        self.patient_id = patient_id
        self.memory = ConversationMemory(self.llm_client, db_session=db_session, patient_id=patient_id)

        # Initialize appointment tool with database session and LLM client
        self.appointment_tool = AppointmentTool(
            db_session=db_session,
            patient_id=patient_id,
            llm_client=self.llm_client  # Pass LLM client for natural responses
        )

        # Update tools dictionary for this instance
        self.mindmate_tools = MINDMATE_TOOLS.copy()
        self.mindmate_tools["book_appointment"] = self.appointment_tool

        self.setup_graph()
        self.session_data = {
            "followup_count": 0,
            "questions_asked": 0,
            "solutions_given": 0,
            "appointment_stage": None  # Track appointment booking stage
        }

    def end_conversation(self) -> Optional[ChatConversationSummary]:
        """End the current conversation and generate summary"""
        if not self.db_session or not self.memory.chat_session:
            logger.warning("⚠️  No database session or chat session available")
            return None

        try:
            # End the chat session
            self.memory.chat_session.end_session()

            # Generate conversation summary
            summary = self._generate_conversation_summary()
            if summary:
                self.db_session.add(summary)
                self.db_session.commit()
                logger.info(f"✅ Conversation ended and summary generated: {summary.id}")
                return summary

        except Exception as e:
            logger.error(f"❌ Failed to end conversation: {e}")
            self.db_session.rollback()
            return None

        return None

    def _generate_conversation_summary(self) -> Optional[ChatConversationSummary]:
        """Generate conversation summary for database storage"""
        if not self.memory.chat_session:
            return None

        try:
            # Get conversation messages
            messages = list(self.memory.messages)

            # Generate summary text using LLM
            summary_text = self._create_summary_text(messages)

            # Extract key points
            key_points = self._extract_key_points(messages)

            # Determine conversation topics
            topic_categories = self._categorize_topics(messages)

            # Assess sentiment trend
            sentiment_trend = self._assess_sentiment_trend()

            # Create summary record
            summary = ChatConversationSummary(
                session_id=self.memory.chat_session.id,
                summary_text=summary_text,
                key_points=json.dumps(key_points),
                topic_categories=json.dumps(topic_categories),
                sentiment_trend=sentiment_trend,
                engagement_level=self._assess_engagement_level()
            )

            return summary

        except Exception as e:
            logger.error(f"❌ Failed to generate conversation summary: {e}")
            return None

    def _create_summary_text(self, messages) -> str:
        """Create conversation summary text"""
        if not messages:
            return "No conversation messages available"

        try:
            # Use LLM to generate summary
            conversation_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages[-10:]  # Last 10 messages
            ])

            prompt = f"""Summarize this mental health conversation in 2-3 sentences:

{conversation_text}

Focus on:
- Main concerns discussed
- Key insights or advice given
- Overall tone and progress"""

            response = self.llm_client.generate_response(prompt, max_tokens=150)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception:
            # Fallback summary
            user_messages = [msg for msg in messages if msg['role'] == 'user']
            return f"Conversation with {len(user_messages)} user messages covering mental health topics."

    def _extract_key_points(self, messages) -> List[str]:
        """Extract key points from conversation"""
        key_points = []
        for msg in messages:
            if msg['role'] == 'user' and len(msg['content']) > 20:
                # Extract potential key concerns
                content_lower = msg['content'].lower()
                if any(word in content_lower for word in ['depression', 'anxiety', 'stress', 'sad', 'worried', 'help']):
                    key_points.append(msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content'])

        return key_points[:5]  # Limit to 5 key points

    def _categorize_topics(self, messages) -> Dict[str, int]:
        """Categorize conversation topics"""
        categories = {
            "depression": 0,
            "anxiety": 0,
            "stress": 0,
            "relationships": 0,
            "work": 0,
            "general": 0
        }

        for msg in messages:
            content_lower = msg['content'].lower()

            if any(word in content_lower for word in ['depress', 'sad', 'hopeless']):
                categories["depression"] += 1
            elif any(word in content_lower for word in ['anxious', 'worry', 'fear', 'panic']):
                categories["anxiety"] += 1
            elif any(word in content_lower for word in ['stress', 'pressure', 'overwhelm']):
                categories["stress"] += 1
            elif any(word in content_lower for word in ['relationship', 'partner', 'family', 'friend']):
                categories["relationships"] += 1
            elif any(word in content_lower for word in ['work', 'job', 'career', 'office']):
                categories["work"] += 1
            else:
                categories["general"] += 1

        return categories

    def _assess_sentiment_trend(self) -> str:
        """Assess sentiment trend from conversation"""
        if hasattr(self.memory, 'session_data'):
            mood_trend = self.memory.session_data.get('mood_trend', 'neutral')

            if mood_trend == 'positive':
                return 'improving'
            elif mood_trend == 'negative':
                return 'concerning'
            else:
                return 'stable'

        return 'stable'

    def _assess_engagement_level(self) -> str:
        """Assess user engagement level"""
        if not self.memory.chat_session:
            return 'low'

        message_ratio = self.memory.chat_session.message_ratio

        if message_ratio > 0.8:
            return 'high'
        elif message_ratio > 0.5:
            return 'medium'
        else:
            return 'low'

    def setup_graph(self):
        """Set up conversation flow"""
        workflow = StateGraph(MindMateState)
        
        workflow.add_node("analyze", self.analyze_message)
        workflow.add_node("use_tools", self.use_tools)
        workflow.add_node("respond", self.create_response)
        
        workflow.set_entry_point("analyze")
        
        workflow.add_conditional_edges(
            "analyze",
            self.should_use_tools,
            {
                "use_tools": "use_tools",
                "respond_directly": "respond"
            }
        )
        
        workflow.add_edge("use_tools", "respond")
        workflow.add_edge("respond", END)
        
        self.app = workflow.compile()
    
    def analyze_message(self, state: MindMateState) -> Dict[str, Any]:
        """Quick analysis of what user needs"""
        user_message = state.get("user_input", "")
        context = self.memory.get_quick_context()
        questions_asked = self.session_data.get("questions_asked", 0)
        
        # Check if we're in appointment flow
        appointment_context = ""
        if self.is_in_appointment_flow():
            appointment_context = f"Current appointment stage: {self.get_appointment_context()}"
        
        analysis_prompt = f"""User said: "{user_message}"

Chat history: {context}
Questions asked so far: {questions_asked}
{appointment_context}

Quick analysis - what does the user need?
1. Appointment booking (if they want to book/schedule/see specialist)
2. Follow-up question (if they shared a concern and we've asked <3 questions)
3. Solution/tips (if we understand their issue)
4. Information (if they're asking about mental health)
5. Just friendly chat (for casual messages)

Respond with just one word: "appointment", "followup", "solution", "info", or "chat"
"""
        
        analysis = self.llm_client.generate(
            analysis_prompt,
            temperature=0.2,
            max_tokens=10
        )
        
        logger.info(f"Analysis: {analysis}")
        
        # Determine action based on analysis
        analysis_lower = analysis.lower()
        tool_needed = None
        
        # If we're in appointment flow, prioritize appointment tool
        if self.is_in_appointment_flow():
            tool_needed = "book_appointment"
        elif "appointment" in analysis_lower:
            tool_needed = "book_appointment"
        elif "followup" in analysis_lower and questions_asked < 3:
            tool_needed = "ask_followup"
        elif "solution" in analysis_lower:
            tool_needed = "give_solution"
        elif "info" in analysis_lower:
            tool_needed = "share_info"
        
        tool_calls = []
        if tool_needed:
            tool_calls.append({
                "tool": tool_needed,
                "input": user_message
            })
        
        return {
            "reasoning": analysis,
            "tool_calls": tool_calls,
            "current_step": "analyzed"
        }
    
    def should_use_tools(self, state: MindMateState) -> str:
        """Decide if we need tools or can respond directly"""
        has_tools = len(state.get("tool_calls", [])) > 0
        return "use_tools" if has_tools else "respond_directly"
    
    def use_tools(self, state: MindMateState) -> Dict[str, Any]:
        """Execute required tools"""
        tool_results = []
        
        for tool_call in state.get("tool_calls", []):
            tool_name = tool_call.get("tool", "")
            tool_input = tool_call.get("input", "")
            
            if tool_name in self.mindmate_tools and self.mindmate_tools[tool_name] is not None:
                try:
                    result = self.mindmate_tools[tool_name].run(tool_input)
                    tool_results.append({
                        "tool": tool_name,
                        "result": result
                    })
                    
                    # Update session tracking
                    if tool_name == "ask_followup":
                        self.session_data["questions_asked"] += 1
                    elif tool_name == "give_solution":
                        self.session_data["solutions_given"] += 1
                        
                except Exception as e:
                    logger.error(f"Tool error: {e}")
                    tool_results.append({
                        "tool": tool_name,
                        "result": json.dumps({"error": str(e)})
                    })
        
        return {
            "tool_results": tool_results,
            "current_step": "tools_used"
        }
    
    def create_response(self, state: MindMateState) -> Dict[str, Any]:
        """Create final WhatsApp-style response"""
        user_input = state.get("user_input", "")
        tool_results = state.get("tool_results", [])
        context = self.memory.get_quick_context()
        
        if tool_results:
            # Use tool results
            tool_data = tool_results[0].get("result", "{}")
            tool_name = tool_results[0].get("tool", "")
            
            try:
                tool_info = json.loads(tool_data)
                # Track appointment stage for conversation context
                if tool_name == "book_appointment" and "stage" in tool_info:
                    self.session_data["appointment_stage"] = tool_info["stage"]
            except:
                tool_info = {"error": "Tool error"}
            
            if "question" in tool_info:
                # Follow-up question
                response_prompt = f"""User said: "{user_input}"
Context: {context}

Tool suggested question: "{tool_info['question']}"

Turn this into a natural, caring response. Be brief like WhatsApp:
- Acknowledge what they said
- Ask the follow-up question naturally
- Keep it short (2-3 sentences max)

Example: "That sounds really tough. {tool_info['question']} I'm here to listen."
"""
                
            elif "tips" in tool_info:
                # Solutions
                tips = tool_info.get("tips", [])
                note = tool_info.get("note", "")
                
                response_prompt = f"""User shared: "{user_input}"

Give these tips in a WhatsApp-friendly way:
{tips}

Make it:
- Brief and encouraging
- Like advice from a caring friend  
- End with: "{note}"

Keep it conversational, not like a manual."""
                
            elif "info" in tool_info:
                # Information
                info_text = tool_info.get("info", "")
                
                response_prompt = f"""User asked about: "{user_input}"

Share this info in a friendly way: "{info_text}"

Make it:
- Conversational like WhatsApp
- Supportive and reassuring
- Brief (2-3 sentences)"""

            elif "response" in tool_info:
                # Appointment booking response - use it directly
                final_response = tool_info["response"]
                return {
                    "final_response": final_response,
                    "current_step": "completed"
                }
                
            else:
                # Fallback
                response_prompt = f"""User said: "{user_input}"

Respond supportively and briefly like a caring friend texting. Keep it natural and encouraging."""
        
        else:
            # Direct response without tools
            response_prompt = f"""User said: "{user_input}"

Chat context: {context}

Respond naturally like a supportive friend on WhatsApp:
- Be warm and encouraging
- Keep it brief (1-3 sentences)
- Match their energy level
- If they seem to be struggling, gently ask if they want to talk about it"""
        
        final_response = self.llm_client.generate(
            response_prompt,
            temperature=0.7,
            max_tokens=150
        )
        
        # Debug logging to understand what LLM returns
        logger.info(f"LLM Raw Response: {final_response[:200] if final_response else 'EMPTY'}")
        
        # Clean up response - remove unwanted meta-text
        if final_response.startswith("Error:"):
            logger.warning(f"LLM returned error: {final_response}")
            final_response = "I'm here for you. What's on your mind?"
        
        # Remove common LLM meta-text patterns (but NOT the whole response)
        unwanted_patterns = [
            r"^Here's a revised response:\s*",
            r"^Here's a better response:\s*",
            r"^Let me try again:\s*",
            r"^Revised response:\s*",
            r"^Better response:\s*",
            # Removed overly aggressive pattern that was stripping valid responses
        ]

        import re
        for pattern in unwanted_patterns:
            final_response = re.sub(pattern, "", final_response, flags=re.MULTILINE | re.IGNORECASE)

        # Clean up extra whitespace
        final_response = re.sub(r'\n\s*\n', '\n', final_response.strip())
        
        # Final safety check - if response is empty after cleanup, use fallback
        if not final_response or len(final_response) < 5:
            logger.warning(f"Response too short after cleanup, using fallback")
            final_response = "I hear you. Tell me more about what's going on?"

        return {
            "final_response": final_response,
            "current_step": "completed"
        }
    
    def chat(self, message: str) -> str:
        """Main chat function - returns brief, supportive responses"""
        
        # Add to memory
        self.memory.add_message("user", message)
        
        logger.info(f"User: {message}")
        
        initial_state = {
            "messages": [],
            "reasoning": "",
            "tool_calls": [],
            "tool_results": [],
            "current_step": "start",
            "user_input": message,
            "final_response": "",
            "conversation_context": self.session_data,
            "followup_count": self.session_data.get("questions_asked", 0),
            "severity_assessment": None,
            "requires_specialist": False
        }
        
        try:
            final_state = self.app.invoke(initial_state)
            response = final_state.get("final_response", "")
            
            if not response or response.startswith("Error:"):
                response = "I'm here to listen. What's going on?"
            
            # Add to memory
            self.memory.add_message("assistant", response)
            
            logger.info(f"MindMate: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            fallback = "Hey, I'm having some trouble but I'm still here for you. What's up?"
            self.memory.add_message("assistant", fallback)
            return fallback
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "session_data": self.session_data,
            "mood_trend": self.memory.session_data.get("mood_trend", "neutral"),
            "total_messages": self.memory.session_data["message_count"],
            "conversation_time": str(datetime.now() - self.memory.session_data["start_time"]),
            "created_by": "Hammad Munir & Jawad Ahsan"
        }
    
    def reset_session(self):
        """Start fresh conversation"""
        self.session_data = {
            "followup_count": 0,
            "questions_asked": 0,
            "solutions_given": 0,
            "appointment_stage": None
        }
        self.memory.clear_memory()
        # Reset appointment tool conversation state
        if hasattr(self, 'appointment_tool'):
            self.appointment_tool._reset_conversation()
        logger.info("New conversation started")

    def is_in_appointment_flow(self) -> bool:
        """Check if we're currently in an appointment booking conversation"""
        return self.session_data.get("appointment_stage") is not None

    def get_appointment_context(self) -> str:
        """Get context about current appointment booking state"""
        stage = self.session_data.get("appointment_stage")
        if not stage:
            return ""

        stage_messages = {
            "specialist_selected": "We're in the process of booking an appointment with a specialist.",
            "slot_selected": "We're selecting a time slot for the appointment.",
            "confirmed": "The appointment has been booked successfully.",
            "initial": "We're starting the appointment booking process."
        }

        return stage_messages.get(stage, f"We're in the {stage} stage of appointment booking.")

# Quick API for React integration
class MindMateAPI:
    """Simple API for React frontend"""
    
    def __init__(self):
        self.mindmate = MindMate()
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send message and get response"""
        try:
            response = self.mindmate.chat(message)
            return {
                "success": True,
                "message": response,
                "timestamp": datetime.now().isoformat(),
                "mood": self.mindmate.memory.session_data.get("mood_trend", "neutral")
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Having some trouble, but I'm still here for you",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_chat_history(self) -> List[Dict]:
        """Get recent chat messages"""
        messages = []
        for msg in list(self.mindmate.memory.messages)[-10:]:  # Last 10
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"]
            })
        return messages
    
    def reset_chat(self) -> Dict[str, Any]:
        """Reset conversation"""
        self.mindmate.reset_session()
        return {"success": True, "message": "Fresh start!"}

def main():
    """WhatsApp-style MindMate interface"""
    print("💙 MindMate - Your Mental Health Friend")
    print("="*40)
    print("Chat with me like you would on WhatsApp!")
    print("I'm here to listen and support you.")
    print("="*40)
    print("Quick help: 'reset' for new chat, 'quit' to exit")
    print("="*40)
    
    try:
        mindmate = MindMate()
        print("\n💬 Hey! How are you feeling today?")
    except Exception as e:
        print(f"Error starting MindMate: {e}")
        return
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nTake care of yourself! 💙")
                print("Remember: you're stronger than you know.")
                break
                
            elif user_input.lower() == 'reset':
                mindmate.reset_session()
                print("\n💬 Fresh start! What's on your mind?")
                continue
                
            elif user_input.lower() == 'help':
                print("\n💡 Just chat with me naturally!")
                print("• Share what's bothering you")
                print("• Ask for tips or advice") 
                print("• Get info about mental health")
                print("• Type 'reset' for new conversation")
                continue
                
            elif not user_input:
                print("💬 I'm here when you're ready to talk.")
                continue
            
            # Get response
            response = mindmate.chat(user_input)
            print(f"\n💙 MindMate: {response}")
            
        except KeyboardInterrupt:
            print(f"\n\nTake care! You've got this 💙")
            break
            
        except Exception as e:
            print(f"\n💙 Something went wrong, but I'm still here. What's up?")
            logger.error(f"Main loop error: {e}")
            continue

if __name__ == "__main__":
    main()
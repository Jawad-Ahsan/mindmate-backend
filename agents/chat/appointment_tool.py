"""
Appointment Tool - Natural Language Appointment Booking for MindMate
==================================================================
Handles appointment booking through natural conversation with patients.
Integrates with existing SMA (Specialist Matching Agent) and appointment booking systems.
"""

import json
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

# Import existing systems
from agents.sma.specialits_matcher import SpecialistMatcher
from agents.sma.appointments_manager import AppointmentsManager
from models.sql_models.specialist_models import Specialists
from models.sql_models.appointments_model import Appointment, AppointmentStatusEnum, AppointmentTypeEnum
from models.sql_models.patient_models import Patient
from agents.sma.sma_schemas import SpecialistSearchRequest, ConsultationMode, SortOption

logger = logging.getLogger(__name__)


class AppointmentTool:
    """
    Natural language appointment booking tool for MindMate chatbot.

    Features:
    - LLM-powered conversational specialist matching
    - Natural slot selection with LLM understanding
    - Automatic booking confirmation
    - Context-aware responses using LLM
    - Integration with existing SMA system
    """

    name = "book_appointment"
    description = "Handle appointment booking through natural conversation"

    def __init__(self, db_session: Session, patient_id: Optional[str] = None, llm_client=None):
        """Initialize appointment tool with database session and optional LLM client"""
        self.db = db_session
        self.patient_id = patient_id
        self.llm_client = llm_client  # Can use LLM for better conversation flow
        self.specialist_matcher = SpecialistMatcher(db_session)
        self.appointments_manager = AppointmentsManager(db_session)
        self.conversation_state = {
            "stage": "initial",  # initial, specialist_selected, slot_selected, confirmed
            "selected_specialist": None,
            "available_slots": [],
            "selected_slot": None,
            "specialist_details": {},
            "booking_attempts": 0,
            "conversation_history": []  # Track conversation for LLM context
        }

    def run(self, user_input: str) -> str:
        """
        Main entry point for appointment booking conversation

        Args:
            user_input: User's natural language message

        Returns:
            Natural language response with next steps or booking result
        """
        try:
            user_input_lower = user_input.lower()

            # Check if user wants to book appointment
            if self._is_appointment_request(user_input_lower):
                return self._handle_appointment_request(user_input)

            # Handle different conversation stages
            if self.conversation_state["stage"] == "specialist_selected":
                return self._handle_slot_selection(user_input)

            elif self.conversation_state["stage"] == "slot_selected":
                return self._handle_booking_confirmation(user_input)

            elif self.conversation_state["stage"] == "confirmed":
                return self._handle_post_booking(user_input)

            # Default: start appointment booking process
            return self._handle_appointment_request(user_input)

        except Exception as e:
            logger.error(f"Appointment tool error: {e}")
            self._reset_conversation()
            return json.dumps({
                "response": "I'm having trouble with the appointment booking right now. Let me start fresh - would you like to book an appointment with a specialist?",
                "stage": "initial",
                "error": str(e)
            })

    def _is_appointment_request(self, user_input: str) -> bool:
        """Check if user is requesting appointment booking"""
        appointment_keywords = [
            "book appointment", "make appointment", "schedule appointment",
            "see specialist", "talk to doctor", "consultation",
            "appointment with", "meet with", "see someone",
            "help me book", "want to book", "need appointment"
        ]

        return any(keyword in user_input for keyword in appointment_keywords)

    def _handle_appointment_request(self, user_input: str) -> str:
        """Handle initial appointment request"""
        try:
            # Extract preferences from user input
            preferences = self._extract_appointment_preferences(user_input)

            # Find matching specialists
            specialists = self._find_matching_specialists(preferences)

            if not specialists:
                return json.dumps({
                    "response": "I couldn't find any specialists matching your preferences right now. Would you like me to search more broadly?",
                    "stage": "initial",
                    "needs_more_info": True
                })

            # Select best specialist
            best_specialist = specialists[0]
            specialist_info = self._get_specialist_details(best_specialist)

            # Update conversation state
            self.conversation_state["stage"] = "specialist_selected"
            self.conversation_state["selected_specialist"] = best_specialist
            self.conversation_state["specialist_details"] = specialist_info

            # Create natural response
            response = self._create_specialist_suggestion_response(specialist_info)

            return json.dumps({
                "response": response,
                "stage": "specialist_selected",
                "specialist": specialist_info,
                "follow_up": "Would you like to book with this specialist?"
            })

        except Exception as e:
            logger.error(f"Error handling appointment request: {e}")
            return json.dumps({
                "response": "I'd be happy to help you book an appointment. Could you tell me what type of specialist you're looking for?",
                "stage": "initial",
                "error": str(e)
            })

    def _handle_slot_selection(self, user_input: str) -> str:
        """Handle slot selection after specialist is chosen"""
        try:
            user_input_lower = user_input.lower()

            # Check if user agrees to proceed with selected specialist
            if self._is_positive_response(user_input_lower):
                # Get available slots for selected specialist
                specialist = self.conversation_state["selected_specialist"]
                slots = self._get_available_slots(specialist.id)

                if not slots:
                    return json.dumps({
                        "response": f"Sorry, {self.conversation_state['specialist_details']['name']} doesn't have any available slots in the near future. Would you like me to find another specialist?",
                        "stage": "initial",
                        "no_slots_available": True
                    })

                # Update state and create slot selection response
                self.conversation_state["stage"] = "slot_selected"
                self.conversation_state["available_slots"] = slots

                response = self._create_slot_selection_response(slots)

                # Convert UUIDs to strings for JSON serialization
                serializable_slots = []
                for slot in slots:
                    serializable_slot = {
                        "id": str(slot.get("id", "")),
                        "specialist_id": str(slot.get("specialist_id", "")),
                        "start_time": slot.get("start_time"),
                        "end_time": slot.get("end_time"),
                        "status": slot.get("status"),
                        "duration_minutes": slot.get("duration_minutes")
                    }
                    serializable_slots.append(serializable_slot)

                return json.dumps({
                    "response": response,
                    "stage": "slot_selected",
                    "available_slots": serializable_slots,
                    "follow_up": "Which time slot works best for you?"
                })

            elif self._is_negative_response(user_input_lower):
                # User doesn't want this specialist, find another
                return self._find_alternative_specialist()

            else:
                # Ask for clarification
                return json.dumps({
                    "response": f"I understand you're considering booking with {self.conversation_state['specialist_details']['name']}. Would you like to proceed with this specialist, or would you prefer someone else?",
                    "stage": "specialist_selected",
                    "needs_clarification": True
                })

        except Exception as e:
            logger.error(f"Error handling slot selection: {e}")
            return json.dumps({
                "response": "Let me try to find some available time slots for you. Which day works best?",
                "stage": "slot_selected",
                "error": str(e)
            })

    def _handle_booking_confirmation(self, user_input: str) -> str:
        """Handle booking confirmation"""
        try:
            user_input_lower = user_input.lower()

            # Check if user is confirming booking
            if self._is_positive_response(user_input_lower):
                # Book the appointment
                result = self._book_appointment()

                if result["success"]:
                    self.conversation_state["stage"] = "confirmed"
                    response = self._create_booking_success_response(result["appointment"])
                else:
                    response = f"Sorry, I couldn't book that appointment. {result.get('message', 'Please try again or select a different time slot.')}"

                return json.dumps({
                    "response": response,
                    "stage": "confirmed" if result["success"] else "slot_selected",
                    "booking_result": result
                })

            elif self._is_negative_response(user_input_lower):
                # User changed mind, go back to slot selection
                self.conversation_state["stage"] = "specialist_selected"
                return json.dumps({
                    "response": "No problem! Let's go back to the time slots. Which one would work better for you?",
                    "stage": "specialist_selected",
                    "changed_mind": True
                })

            else:
                # Try to extract slot preference from user input
                logger.info(f"Extracting slot preference from: '{user_input}'")
                logger.info(f"Available slots: {len(self.conversation_state['available_slots'])} slots")

                slot_index = self._extract_slot_preference(user_input)
                logger.info(f"Extracted slot index: {slot_index}")

                if slot_index is not None and slot_index < len(self.conversation_state["available_slots"]):
                    selected_slot = self.conversation_state["available_slots"][slot_index]
                    self.conversation_state["selected_slot"] = selected_slot

                    # Check if this was a specific time request
                    time_match = self._parse_specific_time(user_input_lower)
                    if time_match:
                        requested_hour, requested_minute, is_pm = time_match
                        # This was a specific time request, mention it's the closest available
                        return json.dumps({
                            "response": f"I found {self._format_slot_time(selected_slot)} as the closest available time to your requested {user_input}. Should I proceed with the booking?",
                            "stage": "slot_selected",
                            "slot_selected": True,
                            "follow_up": "Confirm booking?"
                        })
                    else:
                        # Regular slot selection
                        return json.dumps({
                            "response": f"Great choice! I'll book you for {self._format_slot_time(selected_slot)}. Should I proceed with the booking?",
                            "stage": "slot_selected",
                            "slot_selected": True,
                            "follow_up": "Confirm booking?"
                        })

                # Provide more helpful clarification with better time matching
                available_times = []
                monday_slots = []
                noonish_slots = []  # Slots around noon (11 AM - 1 PM)

                for slot in self.conversation_state["available_slots"]:
                    start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                    time_str = start_time.strftime("%A at %I:%M %p")
                    available_times.append(time_str)

                    # Check for Monday slots
                    if start_time.strftime('%A').lower() == 'monday':
                        monday_slots.append(time_str)

                    # Check for noon-ish slots (11 AM - 1 PM)
                    if 11 <= start_time.hour <= 13:
                        noonish_slots.append(time_str)

                # Create a more helpful response based on what the user asked for
                if "monday" in user_input_lower and ("12" in user_input_lower or "noon" in user_input_lower):
                    if monday_slots:
                        clarification_msg = f"I don't have Monday at 12 PM available, but I do have these Monday slots: {', '.join(monday_slots)}. Would one of these work instead?"
                    elif noonish_slots:
                        clarification_msg = f"Monday at 12 PM isn't available, but I have these noon-ish times: {', '.join(noonish_slots)}. Would any of these work?"
                    else:
                        clarification_msg = f"Monday slots aren't available right now. Here are my available times: {', '.join(available_times[:5])}. Which one works for you?"
                elif "12" in user_input_lower or "noon" in user_input_lower:
                    if noonish_slots:
                        clarification_msg = f"I don't have exactly 12 PM available, but here are my noon-ish times: {', '.join(noonish_slots)}. Would one of these work?"
                    else:
                        clarification_msg = f"12 PM isn't available right now. Here are my available times: {', '.join(available_times[:5])}. Which one works for you?"
                elif available_times:
                    times_text = ", ".join(available_times[:5])
                    clarification_msg = f"I have these times available: {times_text}. You can say the number (1, 2, 3), the day and time (like 'monday 2 pm'), or just a time (like '3 pm'). Which one works best?"
                else:
                    clarification_msg = "Could you please specify which time works best for you from the options above?"

                return json.dumps({
                    "response": clarification_msg,
                    "stage": "slot_selected",
                    "needs_clarification": True,
                    "available_slots_preview": available_times,
                    "suggested_alternatives": monday_slots + noonish_slots
                })

        except Exception as e:
            logger.error(f"Error handling booking confirmation: {e}")
            return json.dumps({
                "response": "There was an issue with the booking. Would you like to try again or select a different time?",
                "stage": "slot_selected",
                "error": str(e)
            })

    def _handle_post_booking(self, user_input: str) -> str:
        """Handle conversation after successful booking"""
        try:
            user_input_lower = user_input.lower()

            if "cancel" in user_input_lower or "change" in user_input_lower:
                return json.dumps({
                    "response": "If you'd like to cancel or change your appointment, I can help with that too. Would you like me to proceed?",
                    "stage": "post_booking",
                    "action_requested": "cancellation"
                })

            elif "reminder" in user_input_lower or "remind" in user_input_lower:
                return json.dumps({
                    "response": "I'll make sure you get a reminder before your appointment. Is there anything else you'd like to know about preparing for your session?",
                    "stage": "post_booking",
                    "reminder_set": True
                })

            else:
                return json.dumps({
                    "response": "Great! Your appointment is all set. Remember, it's completely normal to feel nervous before your first session. Is there anything specific you'd like to know before then?",
                    "stage": "post_booking",
                    "follow_up": "Any questions about the appointment?"
                })

        except Exception as e:
            logger.error(f"Error handling post-booking: {e}")
            return json.dumps({
                "response": "Your appointment is booked successfully! I'm here if you need any help or have questions.",
                "stage": "post_booking",
                "error": str(e)
            })

    def _extract_appointment_preferences(self, user_input: str) -> Dict[str, Any]:
        """Extract appointment preferences from user input"""
        preferences = {
            "specializations": [],
            "specialist_type": None,
            "consultation_mode": ConsultationMode.ONLINE,  # Default to online
            "budget_max": None,
            "urgency": "normal"
        }

        user_input_lower = user_input.lower()

        # Extract specializations
        if "depression" in user_input_lower or "depressed" in user_input_lower:
            preferences["specializations"].append("depression")
        if "anxiety" in user_input_lower or "anxious" in user_input_lower:
            preferences["specializations"].append("anxiety")
        if "stress" in user_input_lower or "stressed" in user_input_lower:
            preferences["specializations"].append("stress")
        if "therapy" in user_input_lower or "therapist" in user_input_lower:
            preferences["specialist_type"] = "psychologist"
        if "psychiatrist" in user_input_lower:
            preferences["specialist_type"] = "psychiatrist"
        if "counselor" in user_input_lower:
            preferences["specialist_type"] = "counselor"

        # Check urgency
        if "urgent" in user_input_lower or "emergency" in user_input_lower or "asap" in user_input_lower:
            preferences["urgency"] = "urgent"
        elif "soon" in user_input_lower or "quick" in user_input_lower:
            preferences["urgency"] = "soon"

        # Check consultation mode preference
        if "in person" in user_input_lower or "face to face" in user_input_lower:
            preferences["consultation_mode"] = ConsultationMode.IN_PERSON

        return preferences

    def _find_matching_specialists(self, preferences: Dict[str, Any]) -> List[Specialists]:
        """Find specialists matching user preferences"""
        try:
            # Create search request
            search_request = SpecialistSearchRequest(
                specializations=preferences.get("specializations", []),
                specialist_type=preferences.get("specialist_type"),
                consultation_mode=preferences.get("consultation_mode", ConsultationMode.ONLINE),
                budget_max=preferences.get("budget_max"),
                limit=5,
                sort_by=SortOption.BEST_MATCH
            )

            # Search for specialists
            result = self.specialist_matcher.search_specialists(search_request)

            if result and result.get("specialists"):
                # Get full specialist objects
                specialist_ids = [spec["id"] for spec in result["specialists"]]
                specialists = self.db.query(Specialists).filter(
                    Specialists.id.in_(specialist_ids)
                ).all()

                # Sort by search result order
                specialist_order = {str(sid): i for i, sid in enumerate(specialist_ids)}
                specialists.sort(key=lambda x: specialist_order.get(str(x.id), 999))

                return specialists

            return []

        except Exception as e:
            logger.error(f"Error finding matching specialists: {e}")
            return []

    def _get_specialist_details(self, specialist: Specialists) -> Dict[str, Any]:
        """Get detailed information about a specialist"""
        return {
            "id": str(specialist.id),
            "name": specialist.full_name,
            "type": specialist.specialist_type.value if specialist.specialist_type else "Specialist",
            "specializations": [spec.specialization.value for spec in specialist.specializations] if specialist.specializations else [],
            "experience": f"{specialist.years_experience} years" if specialist.years_experience else "Experienced",
            "fee": f"PKR {specialist.consultation_fee}" if specialist.consultation_fee else "Fee not specified",
            "rating": f"{specialist.average_rating}/5" if specialist.average_rating else "Not rated yet",
            "bio": specialist.bio[:200] + "..." if specialist.bio and len(specialist.bio) > 200 else specialist.bio or "Professional mental health specialist"
        }

    def _get_available_slots(self, specialist_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get available time slots for a specialist"""
        try:
            # Get slots for next 7 days
            from_date = datetime.now(timezone.utc) + timedelta(hours=1)
            to_date = from_date + timedelta(days=7)

            logger.info(f"Getting slots for specialist {specialist_id} from {from_date} to {to_date}")

            slots = self.appointments_manager.get_specialist_slots(
                specialist_id=specialist_id,
                from_date=from_date,
                to_date=to_date
            )

            logger.info(f"Total slots generated: {len(slots)}")

            # Log all slots with their details
            for i, slot in enumerate(slots[:10]):  # Log first 10 slots
                start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                logger.info(f"Slot {i}: {start_time.strftime('%A %I:%M %p')} - Status: {slot.get('status')}")

            # Filter to first 5 available slots
            available_slots = [slot for slot in slots if slot.get("status") == "free"][:5]

            logger.info(f"Available slots after filtering: {len(available_slots)}")
            for i, slot in enumerate(available_slots):
                start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                logger.info(f"Available slot {i}: {start_time.strftime('%A %I:%M %p')}")

            return available_slots

        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return []

    def _book_appointment(self) -> Dict[str, Any]:
        """Book the selected appointment"""
        try:
            if not self.patient_id:
                return {"success": False, "message": "Patient ID not available"}

            if not self.conversation_state.get("selected_specialist"):
                return {"success": False, "message": "No specialist selected"}

            if not self.conversation_state.get("selected_slot"):
                return {"success": False, "message": "No time slot selected"}

            specialist = self.conversation_state["selected_specialist"]
            slot = self.conversation_state["selected_slot"]

            # Parse slot times - ensure they are offset-aware
            start_time_str = slot["start_time"]
            end_time_str = slot["end_time"]

            # Handle different ISO format variations
            if start_time_str.endswith('Z'):
                start_time_str = start_time_str[:-1] + '+00:00'
            if end_time_str.endswith('Z'):
                end_time_str = end_time_str[:-1] + '+00:00'

            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)

            # Ensure both times are offset-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            # Create appointment
            appointment = Appointment(
                specialist_id=specialist.id,
                patient_id=uuid.UUID(self.patient_id),
                scheduled_start=start_time,
                scheduled_end=end_time,
                appointment_type=AppointmentTypeEnum.VIRTUAL,
                status=AppointmentStatusEnum.SCHEDULED,
                fee=specialist.consultation_fee or 0,
                notes="Booked through MindMate chatbot"
            )

            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)

            return {
                "success": True,
                "appointment": {
                    "id": str(appointment.id),
                    "specialist_name": specialist.full_name,
                    "start_time": appointment.scheduled_start.isoformat(),
                    "end_time": appointment.scheduled_end.isoformat(),
                    "fee": float(appointment.fee)
                }
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            self.db.rollback()
            return {"success": False, "message": f"Booking failed: {str(e)}"}

    def _create_specialist_suggestion_response(self, specialist_info: Dict[str, Any]) -> str:
        """Create natural language response suggesting a specialist"""
        if self.llm_client:
            # Use LLM for more natural response
            prompt = f"""Create a natural, friendly response suggesting this specialist for an appointment:

Specialist Details:
- Name: {specialist_info['name']}
- Type: {specialist_info['type']}
- Experience: {specialist_info['experience']}
- Specializations: {', '.join(specialist_info['specializations'][:3])}
- Rating: {specialist_info.get('rating', 'Not rated yet')}
- Fee: {specialist_info['fee']}
- Bio: {specialist_info['bio'][:150]}...

Make it conversational like you're recommending a friend. Keep it brief (2-3 sentences) and end with asking if they want to book.
"""

            llm_response = self.llm_client.generate(prompt, temperature=0.7, max_tokens=150)
            if llm_response and not llm_response.startswith("Error:"):
                return llm_response

        # Fallback to structured response
        response = f"I found {specialist_info['name']}, a {specialist_info['experience']} {specialist_info['type'].lower()} who specializes in {', '.join(specialist_info['specializations'][:2])}."

        if specialist_info.get('rating') != "Not rated yet":
            response += f" They have a {specialist_info['rating']} rating."

        response += f" The consultation fee is {specialist_info['fee']}."

        response += f"\n\n{specialist_info['bio']}\n\nWould you like to book an appointment with {specialist_info['name']}?"

        return response

    def _create_slot_selection_response(self, slots: List[Dict[str, Any]]) -> str:
        """Create natural language response for slot selection"""
        if not slots:
            return "Sorry, there are no available slots at the moment."

        response = "Here are the available time slots:\n\n"

        for i, slot in enumerate(slots, 1):
            start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
            formatted_time = start_time.strftime("%A, %B %d at %I:%M %p")
            response += f"{i}. {formatted_time}\n"

        response += "\nWhich time slot works best for you? Just tell me the number or describe what you're looking for."

        return response

    def _create_booking_success_response(self, appointment: Dict[str, Any]) -> str:
        """Create natural language response for successful booking"""
        start_time = datetime.fromisoformat(appointment["start_time"])
        formatted_time = start_time.strftime("%A, %B %d at %I:%M %p")

        response = f"Perfect! Your appointment with {appointment['specialist_name']} is now booked for {formatted_time}.\n\n"
        response += f"💙 Remember: Taking this step shows how strong you are. It's completely normal to feel a mix of emotions before your first session.\n\n"
        response += f"If you need to make any changes or have questions before then, just let me know!"

        return response

    def _find_alternative_specialist(self) -> str:
        """Find an alternative specialist"""
        self._reset_conversation()
        return json.dumps({
            "response": "No problem! Let me find another specialist for you. What type of specialist are you looking for?",
            "stage": "initial",
            "finding_alternative": True
        })

    def _is_positive_response(self, user_input: str) -> bool:
        """Check if user response is positive/affirmative"""
        positive_words = ["yes", "sure", "okay", "fine", "good", "great", "perfect", "yes please", "that works", "book it"]
        return any(word in user_input for word in positive_words)

    def _is_negative_response(self, user_input: str) -> bool:
        """Check if user response is negative"""
        negative_words = ["no", "not", "don't", "won't", "never", "bad", "wrong", "different", "other"]
        return any(word in user_input for word in negative_words)

    def _extract_slot_preference(self, user_input: str) -> Optional[int]:
        """Extract slot preference from user input"""
        user_input_lower = user_input.lower()
        logger.info(f"_extract_slot_preference called with: '{user_input_lower}'")

        # First try LLM-powered understanding for complex queries
        if self.llm_client and len(user_input.split()) > 2:  # Only for longer queries
            llm_slot_index = self._llm_extract_slot_preference(user_input)
            if llm_slot_index is not None:
                logger.info(f"LLM extracted slot index: {llm_slot_index}")
                return llm_slot_index

        # Check for numbers first (highest priority)
        import re
        numbers = re.findall(r'\d+', user_input)
        logger.info(f"Found numbers: {numbers}")

        if numbers:
            slot_index = int(numbers[0]) - 1  # Convert to 0-based index
            logger.info(f"Calculated slot index: {slot_index}, available slots: {len(self.conversation_state['available_slots'])}")
            if 0 <= slot_index < len(self.conversation_state["available_slots"]):
                logger.info(f"Returning valid slot index: {slot_index}")
                return slot_index

        # Check for ordinals
        if "first" in user_input_lower:
            return 0
        elif "second" in user_input_lower:
            return 1
        elif "third" in user_input_lower:
            return 2
        elif "fourth" in user_input_lower:
            return 3
        elif "fifth" in user_input_lower:
            return 4

        # Parse specific times (like "12 pm", "3 pm", "2:00 pm", etc.)
        time_match = self._parse_specific_time(user_input_lower)
        logger.info(f"Time match result: {time_match}")
        if time_match:
            requested_hour, requested_minute, is_pm = time_match
            logger.info(f"Looking for closest slot to {requested_hour}:{requested_minute:02d} {'PM' if is_pm else 'AM'}")
            closest_slot = self._find_closest_slot_by_time(requested_hour, requested_minute, is_pm)
            logger.info(f"Closest slot found: {closest_slot}")
            return closest_slot

        # Check for general time preferences
        if "morning" in user_input_lower:
            # Find first morning slot (before 12 PM)
            for i, slot in enumerate(self.conversation_state["available_slots"]):
                start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                if start_time.hour < 12:
                    return i
        elif "afternoon" in user_input_lower:
            # Find first afternoon slot (12 PM and after)
            for i, slot in enumerate(self.conversation_state["available_slots"]):
                start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                if start_time.hour >= 12:
                    return i
        elif "evening" in user_input_lower:
            # Find first evening slot (after 5 PM)
            for i, slot in enumerate(self.conversation_state["available_slots"]):
                start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                if start_time.hour >= 17:
                    return i

        # Check for day preferences combined with time
        day_slot = self._find_slot_by_day_and_time(user_input_lower)
        if day_slot is not None:
            return day_slot

        return None

    def _llm_extract_slot_preference(self, user_input: str) -> Optional[int]:
        """Use LLM to understand complex slot preferences"""
        if not self.llm_client or not self.conversation_state["available_slots"]:
            return None

        # Create a list of available slots for the LLM to understand
        slot_options = []
        for i, slot in enumerate(self.conversation_state["available_slots"]):
            start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
            slot_description = f"Option {i+1}: {start_time.strftime('%A at %I:%M %p')}"
            slot_options.append(slot_description)

        prompt = f"""Given these available appointment slots:

{chr(10).join(slot_options)}

And the user's preference: "{user_input}"

Which slot number (1, 2, 3, etc.) would best match their preference?
Consider factors like:
- Day preferences (Monday, Tuesday, etc.)
- Time preferences (morning, afternoon, specific times)
- Flexibility ("any day", "whatever works")
- Urgency ("soon", "ASAP")

Respond with ONLY the slot number (1, 2, 3, etc.) that best matches, or "none" if no good match.
"""

        try:
            llm_response = self.llm_client.generate(prompt, temperature=0.1, max_tokens=10)
            if llm_response and not llm_response.startswith("Error:"):
                response_clean = llm_response.strip().lower()
                if response_clean.isdigit():
                    slot_index = int(response_clean) - 1
                    if 0 <= slot_index < len(self.conversation_state["available_slots"]):
                        return slot_index
                elif response_clean == "none":
                    return None
        except Exception as e:
            logger.error(f"LLM slot extraction failed: {e}")

        return None

    def _parse_specific_time(self, user_input: str) -> Optional[tuple]:
        """Parse specific time from user input like '12 pm', '3 pm', '2:30 pm'"""
        import re
        logger.info(f"_parse_specific_time called with: '{user_input}'")

        # Match patterns like: 12 pm, 3 pm, 2:30 pm, 9 am, etc.
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 2:30 pm
            r'(\d{1,2})\s*(am|pm)',           # 12 pm
            r'(\d{1,2})(am|pm)',              # 12pm (no space)
            r'(\d{1,2}):(\d{2})',             # 2:30 (assume current day period)
            r'(\d{1,2})\s*o\'clock',          # 3 o'clock
        ]

        for i, pattern in enumerate(time_patterns):
            logger.info(f"Trying pattern {i+1}: {pattern}")
            match = re.search(pattern, user_input)
            logger.info(f"Match result: {match}")
            if match:
                logger.info(f"Match groups: {match.groups()}")
                if len(match.groups()) == 3:  # hour:minute am/pm
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    period = match.group(3).lower()
                elif len(match.groups()) == 2:  # hour am/pm
                    hour = int(match.group(1))
                    minute = 0
                    period = match.group(2).lower()
                else:  # hour:minute or hour o'clock (assume am/pm based on context)
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if len(match.groups()) > 1 else 0
                    # Try to determine AM/PM from context or assume reasonable default
                    period = self._guess_time_period(hour, user_input)

                # Convert to 24-hour format
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0

                return (hour, minute, period == 'pm')

        return None

    def _guess_time_period(self, hour: int, context: str) -> str:
        """Guess AM/PM based on context and common sense"""
        # Morning hours typically AM
        if hour >= 6 and hour <= 11:
            return 'am'
        # Afternoon/evening hours typically PM
        elif hour >= 12 and hour <= 23:
            return 'pm'
        # Ambiguous hours - check context
        elif hour >= 1 and hour <= 5:
            if any(word in context for word in ['morning', 'early', 'wake']):
                return 'am'
            else:
                return 'pm'  # Default to PM for ambiguous hours
        else:
            return 'am'  # Default to AM

    def _find_closest_slot_by_time(self, requested_hour: int, requested_minute: int, is_pm: bool) -> Optional[int]:
        """Find the closest available slot to the requested time"""
        if not self.conversation_state["available_slots"]:
            logger.info("No available slots to search through")
            return None

        logger.info(f"Looking for closest slot to {requested_hour}:{requested_minute:02d} {'PM' if is_pm else 'AM'}")
        logger.info(f"Available slots: {len(self.conversation_state['available_slots'])}")

        closest_slot_index = None
        smallest_diff = float('inf')

        for i, slot in enumerate(self.conversation_state["available_slots"]):
            start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
            slot_hour = start_time.hour
            slot_minute = start_time.minute

            logger.info(f"Slot {i}: {start_time.strftime('%A %I:%M %p')} (hour: {slot_hour}, minute: {slot_minute})")

            # Calculate time difference in minutes
            requested_total_minutes = requested_hour * 60 + requested_minute
            slot_total_minutes = slot_hour * 60 + slot_minute

            time_diff = abs(requested_total_minutes - slot_total_minutes)
            logger.info(f"Time difference: {time_diff} minutes")

            if time_diff < smallest_diff:
                smallest_diff = time_diff
                closest_slot_index = i
                logger.info(f"New closest slot: {i}, diff: {smallest_diff}")

        logger.info(f"Returning closest slot index: {closest_slot_index}, diff: {smallest_diff}")
        return closest_slot_index

    def _find_slot_by_day_and_time(self, user_input: str) -> Optional[int]:
        """Find slot by day and time combination like 'monday 12 pm'"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for day in days:
            if day in user_input:
                # Found a day, now look for time in the same input
                time_match = self._parse_specific_time(user_input)
                if time_match:
                    requested_hour, requested_minute, is_pm = time_match

                    # Find slots on the specified day
                    for i, slot in enumerate(self.conversation_state["available_slots"]):
                        start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                        if start_time.strftime('%A').lower() == day:
                            # Check if this slot is close to requested time
                            slot_hour = start_time.hour
                            slot_minute = start_time.minute

                            # Allow 1-2 hour window around requested time
                            time_diff = abs((requested_hour * 60 + requested_minute) -
                                          (slot_hour * 60 + slot_minute))

                            if time_diff <= 120:  # Within 2 hours
                                return i

                    # If no exact match on that day, return first slot on that day
                    for i, slot in enumerate(self.conversation_state["available_slots"]):
                        start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
                        if start_time.strftime('%A').lower() == day:
                            return i

        return None

    def _format_slot_time(self, slot: Dict[str, Any]) -> str:
        """Format slot time for display"""
        start_time = datetime.fromisoformat(slot["start_time"].replace('Z', '+00:00'))
        return start_time.strftime("%A, %B %d at %I:%M %p")

    def _reset_conversation(self):
        """Reset conversation state"""
        self.conversation_state = {
            "stage": "initial",
            "selected_specialist": None,
            "available_slots": [],
            "selected_slot": None,
            "specialist_details": {},
            "booking_attempts": 0
        }


# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of the AppointmentTool:

    # Initialize with database session and patient ID
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Mock database session for testing
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    patient_id = "test_patient_123"

    # Create appointment tool
    appointment_tool = AppointmentTool(db_session=db, patient_id=patient_id)

    # Example conversation flow:
    # 1. User: "I want to book an appointment"
    response1 = appointment_tool.run("I want to book an appointment")
    print("Bot:", response1)

    # 2. User: "Yes, that sounds good"
    response2 = appointment_tool.run("Yes, that sounds good")
    print("Bot:", response2)

    # 3. User: "I'll take the first slot"
    response3 = appointment_tool.run("I'll take the first slot")
    print("Bot:", response3)

    # 4. User: "Yes, please book it"
    response4 = appointment_tool.run("Yes, please book it")
    print("Bot:", response4)
    """

    print("AppointmentTool created successfully!")
    print("To use this tool, initialize it with a database session and patient ID.")
    print("See the docstring above for example usage.")

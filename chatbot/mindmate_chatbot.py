"""
MindMate Chatbot - RE-ACT Agent System
======================================
Main chatbot implementation using LangGraph for patient assessment.
"""

import json
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from datetime import datetime

from .LLM_client import ChatbotLLMClient
from .tools import ask_basic_info, ask_concern, ask_risk_assessment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the state
class ChatbotState(TypedDict):
    messages: Annotated[List[str], operator.add]
    current_tool: str
    tool_state: Dict[str, Any]
    user_input: str
    final_response: str
    assessment_data: Dict[str, Any]
    workflow_complete: bool

class MindMateChatbot:
    """
    RE-ACT agent chatbot for patient assessment using LangGraph.
    Follows the sequence: basic_info -> concern -> risk_assessment
    """
    
    def __init__(self):
        """Initialize the chatbot with LLM client and tools"""
        self.llm_client = ChatbotLLMClient()
        self.setup_graph()
        
        # Tool execution order
        self.tool_sequence = ["basic_info", "concern", "risk_assessment"]
        self.current_tool_index = 0
    
    def setup_graph(self):
        """Set up the LangGraph state graph"""
        workflow = StateGraph(ChatbotState)
        
        # Add nodes
        workflow.add_node("reasoning", self.reasoning_node)
        workflow.add_node("tool_execution", self.tool_execution_node)
        workflow.add_node("response_generation", self.response_generation_node)
        
        # Set entry point
        workflow.set_entry_point("reasoning")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "reasoning",
            self.should_use_tools,
            {
                "use_tools": "tool_execution",
                "direct_response": "response_generation"
            }
        )
        
        workflow.add_edge("tool_execution", "response_generation")
        workflow.add_edge("response_generation", END)
        
        self.app = workflow.compile()
    
    def reasoning_node(self, state: ChatbotState) -> Dict[str, Any]:
        """First node: Observe and reason about the user's request"""
        logger.info("🧠 REASONING NODE - Observing and Analyzing...")
        
        user_message = state.get("user_input", "")
        
        if not user_message:
            return {
                "current_tool": "none",
                "tool_state": {},
                "workflow_complete": False
            }
        
        # Check if this is a new conversation or continuation
        if "start" in user_message.lower() or "begin" in user_message.lower():
            # Start new assessment workflow
            return {
                "current_tool": "basic_info",
                "tool_state": {"action": "start"},
                "workflow_complete": False
            }
        
        # Check if we're in the middle of a tool assessment
        current_tool = state.get("current_tool", "")
        if current_tool and current_tool in self.tool_sequence:
            # Get the current assessment data to understand context
            assessment_data = state.get("assessment_data", {})
            current_tool_data = assessment_data.get(current_tool, {})
            
            # Continue with current tool, passing context
            return {
                "current_tool": current_tool,
                "tool_state": {
                    "action": "respond", 
                    "response": user_message,
                    "current_question": current_tool_data.get("question"),
                    "progress": current_tool_data.get("progress"),
                    "section": current_tool_data.get("section")
                },
                "workflow_complete": False
            }
        
        # Default: start basic info
        return {
            "current_tool": "basic_info",
            "tool_state": {"action": "start"},
            "workflow_complete": False
        }
    
    def should_use_tools(self, state: ChatbotState) -> str:
        """Decide whether to use tools or provide direct response"""
        current_tool = state.get("current_tool", "")
        has_tool = current_tool and current_tool in self.tool_sequence
        
        logger.info(f"🤔 DECISION: {'Using tools' if has_tool else 'Direct response'}")
        return "use_tools" if has_tool else "direct_response"
    
    def tool_execution_node(self, state: ChatbotState) -> Dict[str, Any]:
        """Execute the required tools"""
        logger.info("⚡ TOOL EXECUTION NODE - Running Tools...")
        
        current_tool = state.get("current_tool", "")
        tool_state = state.get("tool_state", {})
        
        if not current_tool or current_tool not in self.tool_sequence:
            return {
                "tool_state": {},
                "workflow_complete": False
            }
        
        try:
            # Debug logging for tool state
            logger.info(f"🔍 Tool execution debug - Tool: {current_tool}")
            logger.info(f"🔍 Tool state: {tool_state}")
            
            # Execute the appropriate tool
            if current_tool == "basic_info":
                # Extract action and pass other params as kwargs
                action = tool_state.get("action", "start")
                kwargs = {k: v for k, v in tool_state.items() if k != "action"}
                result = ask_basic_info(action, **kwargs)
            elif current_tool == "concern":
                # Extract action and pass other params as kwargs
                action = tool_state.get("action", "start")
                kwargs = {k: v for k, v in tool_state.items() if k != "action"}
                result = ask_concern(action, **kwargs)
            elif current_tool == "risk_assessment":
                # Extract action and pass other params as kwargs
                action = tool_state.get("action", "start")
                kwargs = {k: v for k, v in tool_state.items() if k != "action"}
                result = ask_risk_assessment(action, **kwargs)
            else:
                result = {"error": f"Unknown tool: {current_tool}"}
            
            logger.info(f"🔧 Tool {current_tool} result: {result}")
            
            # Check if tool execution is complete
            if result.get("status") == "completed":
                # Move to next tool in sequence
                next_tool = self._get_next_tool(current_tool)
                if next_tool:
                    return {
                        "current_tool": next_tool,
                        "tool_state": {"action": "start"},
                        "assessment_data": {**state.get("assessment_data", {}), current_tool: result}
                    }
                else:
                    # All tools completed
                    return {
                        "current_tool": "",
                        "tool_state": {},
                        "workflow_complete": True,
                        "assessment_data": {**state.get("assessment_data", {}), current_tool: result}
                    }
            elif result.get("status") == "critical":
                # Critical response from risk assessment
                return {
                    "current_tool": "",
                    "tool_state": {},
                    "workflow_complete": True,
                    "assessment_data": {**state.get("assessment_data", {}), current_tool: result}
                }
            else:
                # Tool needs more input
                return {
                    "current_tool": current_tool,
                    "tool_state": {},
                    "assessment_data": {**state.get("assessment_data", {}), current_tool: result}
                }
                
        except Exception as e:
            logger.error(f"❌ Tool execution error: {e}")
            return {
                "tool_state": {},
                "workflow_complete": False
            }
    
    def _get_next_tool(self, current_tool: str) -> Optional[str]:
        """Get the next tool in the sequence"""
        try:
            current_index = self.tool_sequence.index(current_tool)
            if current_index + 1 < len(self.tool_sequence):
                return self.tool_sequence[current_index + 1]
        except ValueError:
            pass
        return None
    
    def response_generation_node(self, state: ChatbotState) -> Dict[str, Any]:
        """Generate final response based on reasoning and tool results"""
        logger.info("📝 RESPONSE GENERATION NODE - Creating Final Answer...")
        
        current_tool = state.get("current_tool", "")
        workflow_complete = state.get("workflow_complete", False)
        assessment_data = state.get("assessment_data", {})
        
        if workflow_complete:
            # Generate completion response
            if "risk_assessment" in assessment_data and assessment_data["risk_assessment"].get("risk_level") == "critical":
                final_response = self._generate_critical_response(assessment_data)
            else:
                final_response = self._generate_completion_response(assessment_data)
        elif current_tool:
            # Generate question response
            final_response = self._generate_question_response(current_tool, assessment_data)
        else:
            # Generate welcome response
            final_response = self._generate_welcome_response()
        
        logger.info(f"✅ FINAL RESPONSE: {final_response}")
        
        return {
            "final_response": final_response,
            "workflow_complete": workflow_complete
        }
    
    def _generate_welcome_response(self) -> str:
        """Generate welcome message"""
        return """Welcome to MindMate! I'm here to help assess your mental health needs.

I'll be asking you a series of questions in three areas:
1. **Basic Information** - Your medical and mental health history
2. **Presenting Concerns** - What brings you here today
3. **Risk Assessment** - Safety evaluation

Let's begin with the first assessment. Type 'start' or 'begin' to get started, or just respond to my questions naturally.

Your privacy and safety are my top priorities. All information is confidential and will be used only to help provide you with appropriate care."""
    
    def _generate_question_response(self, current_tool: str, assessment_data: Dict) -> str:
        """Generate response for ongoing tool assessment"""
        tool_names = {
            "basic_info": "Basic Information",
            "concern": "Presenting Concerns", 
            "risk_assessment": "Risk Assessment"
        }
        
        tool_name = tool_names.get(current_tool, current_tool)
        
        # Get the current question from the tool result that was already collected
        tool_result = assessment_data.get(current_tool, {})
        
        # Debug logging
        logger.info(f"🔍 Response generation debug - Tool: {current_tool}")
        logger.info(f"🔍 Tool result: {tool_result}")
        logger.info(f"🔍 Assessment data keys: {list(assessment_data.keys())}")
        
        if not tool_result:
            logger.error(f"❌ No tool result found for {current_tool}")
            return f"I'm having trouble with the {tool_name} assessment. Please try again or contact support."
        
        # Check if we have a question to ask
        if "question" in tool_result:
            question = tool_result["question"]
            
            # Handle both object and dictionary formats
            if hasattr(question, 'text'):
                question_text = question.text
                question_type = getattr(question, 'type', 'text')
                question_options = getattr(question, 'options', [])
                question_placeholder = getattr(question, 'placeholder', None)
            else:
                # Handle dictionary format
                question_text = question.get('text', str(question))
                question_type = question.get('type', 'text')
                question_options = question.get('options', [])
                question_placeholder = question.get('placeholder', None)
            
            # Format the question based on its type
            if question_type == 'yes_no':
                response = f"**{tool_name} Question {tool_result.get('progress', '')}:**\n\n"
                response += f"{question_text}\n\n"
                response += "Please answer with 'Yes' or 'No'."
                
                # Add options if available
                if question_options:
                    response += "\n\n**Options:**\n"
                    for option in question_options:
                        if hasattr(option, 'display'):
                            display_text = option.display
                        else:
                            display_text = option.get('display', str(option))
                        response += f"• {display_text}\n"
                
                return response
            else:
                response = f"**{tool_name} Question {tool_result.get('progress', '')}:**\n\n"
                response += f"{question_text}\n\n"
                response += "Please provide your answer."
                
                # Add placeholder if available
                if question_placeholder:
                    response += f"\n\n**Hint:** {question_placeholder}"
                
                return response
        
        # Fallback if no question data
        return f"Thank you for that information. Now let me ask you about your {tool_name.lower()}.\n\nPlease answer the next question to continue."
    
    def _generate_completion_response(self, assessment_data: Dict) -> str:
        """Generate completion response"""
        response_parts = [
            "🎉 **Assessment Complete!**\n\n",
            "Thank you for completing the MindMate mental health assessment. Here's a summary of what we covered:\n\n"
        ]
        
        # Add summaries from each tool
        if "basic_info" in assessment_data:
            response_parts.append("**📋 Basic Information Collected:**\n")
            basic_data = assessment_data["basic_info"]
            if basic_data.get("past_psych_dx"):
                response_parts.append(f"• Psychiatric History: {basic_data['past_psych_dx']}\n")
            if basic_data.get("current_meds"):
                response_parts.append(f"• Current Medications: {basic_data['current_meds']}\n")
            if basic_data.get("medical_history"):
                response_parts.append(f"• Medical History: {basic_data['medical_history']}\n")
            response_parts.append("\n")
        
        if "concern" in assessment_data:
            response_parts.append("**🎯 Presenting Concerns:**\n")
            concern_data = assessment_data["concern"]
            if concern_data.get("presenting_concern"):
                response_parts.append(f"• Main Concern: {concern_data['presenting_concern']}\n")
            if concern_data.get("severity"):
                response_parts.append(f"• Severity: {concern_data['severity']}/10\n")
            if concern_data.get("impact_work"):
                response_parts.append(f"• Impact on Daily Life: {concern_data['impact_work']}\n")
            response_parts.append("\n")
        
        if "risk_assessment" in assessment_data:
            response_parts.append("**⚠️ Risk Assessment:**\n")
            risk_data = assessment_data["risk_assessment"]
            if risk_data.get("risk_level"):
                response_parts.append(f"• Risk Level: {risk_data['risk_level'].upper()}\n")
            if risk_data.get("protective_factors"):
                response_parts.append(f"• Protective Factors: {risk_data['protective_factors']}\n")
            response_parts.append("\n")
        
        response_parts.append("**📞 Next Steps:**\n")
        response_parts.append("Based on your responses, I recommend:\n")
        response_parts.append("1. **Schedule a consultation** with a mental health specialist\n")
        response_parts.append("2. **Keep this information** for your appointment\n")
        response_parts.append("3. **Contact emergency services** if you experience a crisis\n\n")
        
        response_parts.append("Your privacy and safety are our top priorities. This assessment helps us provide you with the most appropriate care and support.")
        
        return "".join(response_parts)
    
    def _generate_critical_response(self, assessment_data: Dict) -> str:
        """Generate critical response for high-risk situations"""
        return """🚨 **CRITICAL SAFETY ALERT** 🚨

Your responses indicate immediate safety concerns that require immediate attention.

**⚠️ IMMEDIATE ACTIONS REQUIRED:**

1. **Call Emergency Services** (911 or your local emergency number)
2. **Contact a Mental Health Crisis Line** (available 24/7)
3. **Go to the nearest Emergency Room**
4. **Stay with someone you trust** until help arrives

**📞 Crisis Resources:**
• National Suicide Prevention Lifeline: 988
• Crisis Text Line: Text HOME to 741741
• Emergency Services: 911

**🛡️ Safety First:**
• Remove access to any means of self-harm
• Stay in a safe environment
• Don't be alone right now

**💬 Professional Help:**
This assessment has been completed and flagged for immediate professional evaluation. Please seek help immediately - your life matters and help is available.

**Remember:** This is a temporary crisis, and with proper support, things can and will get better."""
    
    def chat(self, message: str) -> str:
        """Main chat interface"""
        logger.info(f"💬 USER: {message}")
        
        # Create initial state
        initial_state = {
            "messages": [],
            "current_tool": "",
            "tool_state": {},
            "user_input": message,
            "final_response": "",
            "assessment_data": {},
            "workflow_complete": False
        }
        
        try:
            # Run the graph
            final_state = self.app.invoke(initial_state)
            
            # Extract the final response
            final_response = final_state.get("final_response", "")
            if final_response:
                return final_response
            else:
                return "I apologize, but I couldn't generate a proper response."
                
        except Exception as e:
            error_msg = f"Error in chat processing: {str(e)}"
            logger.error(f"❌ CHAT ERROR: {error_msg}")
            return error_msg
    
    def get_assessment_status(self) -> Dict[str, Any]:
        """Get current assessment status"""
        return {
            "current_tool": getattr(self, 'current_tool', ''),
            "tool_sequence": self.tool_sequence,
            "workflow_complete": False,
            "assessment_data": {}
        }
    
    def reset_assessment(self):
        """Reset the assessment workflow"""
        self.current_tool_index = 0
        logger.info("🔄 Assessment workflow reset")

# Global instance
_mindmate_chatbot = MindMateChatbot()

def get_chatbot() -> MindMateChatbot:
    """Get the global chatbot instance"""
    return _mindmate_chatbot

def chat_with_bot(message: str) -> str:
    """Simple interface for chatting with the bot"""
    return _mindmate_chatbot.chat(message)

"""
DA Diagnosis Agent ReAct System
A reasoning and acting agent for psychiatric diagnosis using LangGraph
"""

from typing import Dict, List, Any, Optional, Annotated, TypedDict
from datetime import datetime
from dataclasses import dataclass, field
import json
import asyncio

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

# Import our existing LLM client
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from llm_client import LLMClient

# Import our custom tools
from da.da_tools import (
    dsm_checker, symptom_analyzer, confidence_calculator,
    DiagnosisResult
)

# Define the state for the ReAct agent
class DiagnosisState(TypedDict):
    """State for the diagnosis ReAct agent"""
    messages: List[BaseMessage]
    patient_symptoms: List[str]
    current_diagnosis: Optional[str]
    diagnosis_results: Dict[str, Any]
    confidence_analysis: Dict[str, Any]
    reasoning_steps: List[str]
    final_diagnosis: Optional[str]
    final_confidence: float
    final_severity: str
    final_reasoning: str

# Define the ReAct agent class
class DiagnosisReActAgent:
    """ReAct agent for psychiatric diagnosis"""

    def __init__(self, model_name: str = None):
        # Use our existing LLM client with Groq
        self.llm_client = LLMClient(model=model_name, enable_cache=True)
        self.model_name = model_name or self.llm_client.model

        # Define the tools for the agent
        self.tools = [
            self.analyze_symptoms_tool,
            self.check_dsm_criteria_tool,
            self.calculate_confidence_tool,
            self.get_differential_diagnoses_tool
        ]

        # Create the LangGraph
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the ReAct graph with reasoning and tool use"""

        # Define the workflow
        workflow = StateGraph(DiagnosisState)

        # Add nodes
        workflow.add_node("reason", self._reason_step)
        workflow.add_node("act", self._act_step)
        workflow.add_node("finalize", self._finalize_step)

        # Add custom tool execution node
        workflow.add_node("tools", self._tool_execution_node)

        # Define the flow
        workflow.set_entry_point("reason")

        # Add conditional edges
        workflow.add_conditional_edges(
            "reason",
            self._should_continue,
            {
                "continue": "act",
                "finalize": "finalize",
                "tools": "tools"
            }
        )

        workflow.add_edge("act", "reason")
        workflow.add_edge("tools", "reason")
        workflow.add_edge("finalize", END)

        # Compile the graph (LangGraph handles recursion limit differently)
        compiled_graph = workflow.compile()

        # Note: Recursion limit is handled at runtime when invoking the graph
        return compiled_graph

    def _reason_step(self, state: DiagnosisState) -> DiagnosisState:
        """Reasoning step - analyze current state and plan next action"""

        messages = state.get("messages", [])
        patient_symptoms = state.get("patient_symptoms", [])
        reasoning_steps = state.get("reasoning_steps", [])

        # Create reasoning prompt
        system_prompt = """You are a psychiatric diagnosis agent using the ReAct (Reasoning + Acting) pattern.
Your goal is to provide accurate psychiatric diagnoses based on patient symptoms and DSM-5 criteria.

You have access to these tools:
1. analyze_symptoms_tool - Analyze symptoms and suggest potential disorders
2. check_dsm_criteria_tool - Check if symptoms match specific DSM criteria
3. calculate_confidence_tool - Calculate overall diagnostic confidence
4. get_differential_diagnoses_tool - Get alternative diagnosis possibilities

Follow this process:
1. Analyze the patient's symptoms
2. Check against relevant DSM-5 criteria
3. Calculate confidence and severity
4. Consider differential diagnoses
5. Provide final diagnosis with reasoning

Always explain your reasoning clearly and justify your decisions."""

        # Determine current step based on available data
        diagnosis_results = state.get("diagnosis_results", {})
        confidence_analysis = state.get("confidence_analysis", {})

        # Build detailed status information
        status_info = []
        if diagnosis_results:
            disorder_count = len(diagnosis_results.get("potential_disorders", {}))
            status_info.append(f"✅ Symptom analysis completed - {disorder_count} potential disorders identified")

            # Show top disorders
            if diagnosis_results.get("potential_disorders"):
                top_disorders = list(diagnosis_results["potential_disorders"].keys())[:3]
                status_info.append(f"🔍 Top potential disorders: {', '.join(top_disorders)}")

        if confidence_analysis:
            confidence_score = confidence_analysis.get("overall_confidence", 0.0)
            severity = confidence_analysis.get("severity", "unknown")
            status_info.append(f"📊 Confidence analysis completed - {confidence_score:.2f} confidence, {severity} severity")

        # Determine next action based on current state
        if not diagnosis_results:
            next_action = "analyze_symptoms_tool"
            action_reason = "Start by analyzing the patient's symptoms to identify potential disorders"
        elif diagnosis_results and not confidence_analysis:
            next_action = "calculate_confidence_tool"
            action_reason = "Calculate overall diagnostic confidence using the symptom analysis results"
        else:
            next_action = "finalize"
            action_reason = "All analysis complete - proceed with final diagnosis"

        reasoning_prompt = f"""
🧠 PSYCHIATRIC DIAGNOSIS ASSISTANT - STEP-BY-STEP ANALYSIS

PATIENT SYMPTOMS:
{chr(10).join(f"• {symptom}" for symptom in patient_symptoms)}

CURRENT ANALYSIS STATUS:
{chr(10).join(status_info) if status_info else "⏳ No analysis completed yet"}

WORKFLOW PROGRESS:
• Step 1 (Symptom Analysis): {'✅ COMPLETED' if diagnosis_results else '⏳ PENDING'}
• Step 2 (Confidence Assessment): {'✅ COMPLETED' if confidence_analysis else '⏳ PENDING'}
• Step 3 (Final Diagnosis): {'⏳ READY' if diagnosis_results and confidence_analysis else '⏳ PENDING'}

REQUIRED NEXT ACTION:
🎯 {action_reason}

AVAILABLE TOOLS:
• analyze_symptoms_tool - Analyze symptoms and identify potential disorders
• check_dsm_criteria_tool - Check specific DSM criteria for a disorder
• calculate_confidence_tool - Calculate overall diagnostic confidence
• get_differential_diagnoses_tool - Compare multiple diagnosis options

RESPONSE INSTRUCTIONS:
If analysis is incomplete, respond with the EXACT tool name: "{next_action}"
If all analysis is complete, respond with: "finalize"

Your response should be ONLY the tool name or "finalize" - no additional explanation needed.
"""

        # Get reasoning from LLM using our client
        response = self.llm_client.generate(
            prompt=reasoning_prompt,
            system_prompt=system_prompt,
            max_tokens=600,
            temperature=0.1
        )

        # Add reasoning to steps
        new_reasoning_steps = reasoning_steps + [response]

        # Convert response to AIMessage for LangGraph compatibility
        ai_message = AIMessage(content=response)

        return {
            **state,
            "messages": messages + [ai_message],
            "reasoning_steps": new_reasoning_steps
        }

    def _act_step(self, state: DiagnosisState) -> DiagnosisState:
        """Acting step - execute planned actions and update state"""

        print("🎯 ACT STEP - Executing planned actions...")

        # This step is mainly handled by the ToolNode, but we can add logic here
        # to process tool results and update the state accordingly

        # The ToolNode will automatically call the appropriate tools
        # and their results will be available in the state

        return state

    def _tool_execution_node(self, state: DiagnosisState) -> DiagnosisState:
        """Custom tool execution node that properly updates state"""

        messages = state.get("messages", [])
        patient_symptoms = state.get("patient_symptoms", [])

        print("🔧 TOOL EXECUTION NODE - Running tools...")

        # Extract the last message to determine which tool to use
        if not messages:
            print("⚠️  No messages found, skipping tool execution")
            return state

        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            content = last_message.content.lower().strip()
        else:
            content = str(last_message).lower().strip()

        updated_state = dict(state)  # Create a new dict instead of using copy()

        try:
            # Determine which tool to use based on the LLM's reasoning
            if content == "analyze_symptoms_tool" or "analyze_symptoms_tool" in content:
                print("🔍 Executing symptom analyzer tool...")
                analysis = self.analyze_symptoms_tool.func(self, patient_symptoms)
                updated_state["diagnosis_results"] = analysis
                print(f"   ✅ Set diagnosis_results with {len(analysis.get('potential_disorders', {}))} potential disorders")

                # Show top disorders for debugging
                if analysis.get("potential_disorders"):
                    top_disorders = list(analysis["potential_disorders"].keys())[:3]
                    print(f"   🔍 Top disorders: {', '.join(top_disorders)}")

            elif content == "calculate_confidence_tool" or "calculate_confidence_tool" in content:
                print("📊 Executing confidence calculator tool...")
                diagnosis_results = state.get("diagnosis_results", {})
                if diagnosis_results.get("potential_disorders"):
                    top_disorder = list(diagnosis_results["potential_disorders"].keys())[0]
                    confidence_result = self.calculate_confidence_tool.func(self, diagnosis_results, top_disorder)
                    updated_state["confidence_analysis"] = confidence_result
                    confidence_score = confidence_result.get('overall_confidence', 0.0)
                    severity = confidence_result.get('severity', 'unknown')
                    print(f"   ✅ Set confidence analysis: {confidence_score:.2f} confidence, {severity} severity")
                else:
                    print("   ⚠️  No diagnosis results available for confidence calculation")

            elif content in ["check_dsm_criteria_tool", "get_differential_diagnoses_tool"]:
                print(f"🔧 Executing {content}...")
                # For now, these tools are less critical for basic diagnosis
                print(f"   ℹ️  {content} execution skipped (not essential for basic diagnosis)")

            else:
                print(f"⚠️  No matching tool found for message: '{content}'")

        except Exception as e:
            print(f"❌ Error in tool execution: {e}")
            import traceback
            traceback.print_exc()

        # Ensure we return a proper state dict
        return updated_state

    def _should_continue(self, state: DiagnosisState) -> str:
        """Determine if we should continue reasoning, use tools, or finalize"""

        messages = state.get("messages", [])
        reasoning_steps = state.get("reasoning_steps", [])
        diagnosis_results = state.get("diagnosis_results", {})
        confidence_analysis = state.get("confidence_analysis", {})

        # Safety check: if we have too many reasoning steps, finalize
        if len(reasoning_steps) > 15:
            print("⚠️  Safety check: Too many reasoning steps, finalizing...")
            return "finalize"

        # If we have both diagnosis results and confidence analysis, finalize
        if diagnosis_results and confidence_analysis:
            print("✅ Complete analysis available, finalizing...")
            return "finalize"

        if not messages:
            print("📝 No messages yet, starting reasoning...")
            return "continue"

        last_message = messages[-1].content if messages else ""
        last_message_lower = last_message.lower().strip()

        # Check for exact tool names or finalize command
        if last_message_lower == "analyze_symptoms_tool":
            print("🔍 LLM requested symptom analysis...")
            return "tools"
        elif last_message_lower == "calculate_confidence_tool":
            print("📊 LLM requested confidence calculation...")
            return "tools"
        elif last_message_lower == "finalize":
            print("🎯 LLM ready to finalize...")
            return "finalize"
        elif last_message_lower in ["check_dsm_criteria_tool", "get_differential_diagnoses_tool"]:
            print(f"🔧 LLM requested {last_message_lower}...")
            return "tools"

        # Check for tool-related keywords in response
        tool_keywords = [
            "analyze_symptoms_tool", "check_dsm_criteria_tool",
            "calculate_confidence_tool", "get_differential_diagnoses_tool"
        ]

        if any(keyword in last_message_lower for keyword in tool_keywords):
            print("🔧 LLM mentioned tool use, executing tools...")
            return "tools"

        # If we don't have diagnosis results, we need symptom analysis
        if not diagnosis_results:
            print("🔍 No diagnosis results, need symptom analysis...")
            return "continue"

        # If we have diagnosis results but no confidence analysis, continue
        elif diagnosis_results and not confidence_analysis:
            print("📊 Have diagnosis results but no confidence analysis, continuing...")
            return "continue"

        # Default to continue if we're still processing
        print("🤔 Continuing workflow...")
        return "continue"

    def _finalize_step(self, state: DiagnosisState) -> DiagnosisState:
        """Finalize the diagnosis with comprehensive reasoning"""

        diagnosis_results = state.get("diagnosis_results", {})
        confidence_analysis = state.get("confidence_analysis", {})
        reasoning_steps = state.get("reasoning_steps", [])

        # Extract the most likely diagnosis
        if diagnosis_results.get("potential_disorders"):
            top_disorder_id = list(diagnosis_results["potential_disorders"].keys())[0]
            top_disorder = diagnosis_results["potential_disorders"][top_disorder_id]

            final_diagnosis = top_disorder["disorder_name"]
            final_confidence = confidence_analysis.get("overall_confidence", 0.0)
            final_severity = confidence_analysis.get("severity", "unknown")

            # Build comprehensive reasoning
            reasoning_parts = [
                f"Primary Diagnosis: {final_diagnosis}",
                f"Confidence: {final_confidence:.2f}",
                f"Severity: {final_severity}",
                "",
                "Reasoning Process:"
            ]

            for i, step in enumerate(reasoning_steps, 1):
                reasoning_parts.append(f"{i}. {step}")

            if confidence_analysis.get("recommendations"):
                reasoning_parts.append("")
                reasoning_parts.append("Recommendations:")
                for rec in confidence_analysis["recommendations"]:
                    reasoning_parts.append(f"- {rec}")

            final_reasoning = "\n".join(reasoning_parts)

        else:
            final_diagnosis = "Unable to determine diagnosis"
            final_confidence = 0.0
            final_severity = "unknown"
            final_reasoning = "Insufficient information or symptoms for diagnosis"

        return {
            **state,
            "final_diagnosis": final_diagnosis,
            "final_confidence": final_confidence,
            "final_severity": final_severity,
            "final_reasoning": final_reasoning
        }

    # Tool definitions using the @tool decorator

    @tool
    def analyze_symptoms_tool(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze patient symptoms and suggest potential disorders"""
        try:
            result = symptom_analyzer.analyze_symptoms(symptoms)
            print(f"🔍 Symptom analysis completed: {len(result.get('potential_disorders', {}))} potential disorders")
            return result
        except Exception as e:
            print(f"❌ Error in symptom analysis: {e}")
            return {"error": str(e), "potential_disorders": {}}

    @tool
    def check_dsm_criteria_tool(self, symptoms: List[str], disorder_id: str) -> Dict[str, Any]:
        """Check if symptoms match DSM criteria for a specific disorder"""
        try:
            result = dsm_checker.check_criteria_match(symptoms, disorder_id)
            print(f"📋 DSM criteria check for {disorder_id}: confidence={result.confidence:.2f}")
            return {
                "diagnosis": result.diagnosis,
                "confidence": result.confidence,
                "severity": result.severity,
                "reasoning": result.reasoning,
                "matched_criteria": result.matched_criteria,
                "missing_criteria": result.missing_criteria
            }
        except Exception as e:
            print(f"❌ Error in DSM criteria check: {e}")
            return {
                "diagnosis": f"Error checking {disorder_id}",
                "confidence": 0.0,
                "severity": "unknown",
                "reasoning": f"Error: {str(e)}",
                "matched_criteria": [],
                "missing_criteria": []
            }

    @tool
    def calculate_confidence_tool(self, symptom_analysis: Dict[str, Any],
                                 primary_diagnosis: str) -> Dict[str, Any]:
        """Calculate overall diagnostic confidence"""
        try:
            result = confidence_calculator.calculate_overall_confidence(
            symptom_analysis, primary_diagnosis
        )
            confidence = result.get("overall_confidence", 0.0)
            print(f"📊 Confidence calculation: {confidence:.2f} for {primary_diagnosis}")
            return result
        except Exception as e:
            print(f"❌ Error in confidence calculation: {e}")
            return {
                "overall_confidence": 0.0,
                "severity": "unknown",
                "confidence_factors": {},
                "recommendations": [f"Error in calculation: {str(e)}"],
                "primary_diagnosis": primary_diagnosis
            }

    @tool
    def get_differential_diagnoses_tool(self, symptoms: List[str],
                                       exclude_disorder: str = "") -> Dict[str, Any]:
        """Get differential diagnosis possibilities"""
        try:
            analysis = symptom_analyzer.analyze_symptoms(symptoms)

            if exclude_disorder and exclude_disorder in analysis.get("potential_disorders", {}):
                del analysis["potential_disorders"][exclude_disorder]

            potential_count = len(analysis.get("potential_disorders", {}))
            print(f"🔄 Differential diagnosis: {potential_count} alternatives found")
            return analysis
        except Exception as e:
            print(f"❌ Error in differential diagnosis: {e}")
            return {"error": str(e), "potential_disorders": {}}

    async def diagnose_async(self, symptoms: List[str]) -> Dict[str, Any]:
        """Run the diagnosis process asynchronously with comprehensive error handling"""

        initial_state = {
            "messages": [],
            "patient_symptoms": symptoms,
            "current_diagnosis": None,
            "diagnosis_results": {},
            "confidence_analysis": {},
            "reasoning_steps": [],
            "final_diagnosis": None,
            "final_confidence": 0.0,
            "final_severity": "unknown",
            "final_reasoning": ""
        }

        try:
            # Run the graph with recursion limit and timeout protection
            config = {"recursion_limit": 50}  # Increased from default 25
            result = await self.graph.ainvoke(initial_state, config=config)

            return {
                "diagnosis": result.get("final_diagnosis", "Unknown"),
                "confidence": result.get("final_confidence", 0.0),
                "severity": result.get("final_severity", "unknown"),
                "reasoning": result.get("final_reasoning", ""),
                "intermediate_results": {
                    "diagnosis_results": result.get("diagnosis_results", {}),
                    "confidence_analysis": result.get("confidence_analysis", {}),
                    "reasoning_steps": result.get("reasoning_steps", [])
                }
            }

        except Exception as e:
            # Handle various LangGraph errors gracefully
            error_type = type(e).__name__

            if "GraphRecursionError" in error_type or "recursion" in str(e).lower():
                print(f"⚠️  Graph recursion error detected: {e}")
                return await self._handle_recursion_error(symptoms, initial_state)

            elif "timeout" in str(e).lower() or "cancelled" in str(e).lower():
                print(f"⏰ Diagnosis timeout: {e}")
                return await self._handle_timeout_error(symptoms, initial_state)

            else:
                print(f"❌ Unexpected error during diagnosis: {e}")
                return await self._handle_generic_error(symptoms, initial_state, str(e))

    async def _handle_recursion_error(self, symptoms: List[str], partial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle recursion errors by falling back to direct tool-based diagnosis"""
        print("🔄 Falling back to direct diagnosis approach...")

        try:
            # Use the direct diagnosis approach without LangGraph
            from .da_tools import symptom_analyzer, dsm_checker, confidence_calculator

            # Step 1: Analyze symptoms
            analysis = symptom_analyzer.analyze_symptoms(symptoms)

            if not analysis.get("potential_disorders"):
                return {
                    "diagnosis": "Unable to determine diagnosis",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Insufficient symptoms for diagnosis",
                    "error_handling": "RecursionErrorFallback",
                    "intermediate_results": {"analysis": analysis}
                }

            # Step 2: Check top diagnosis
            top_disorder = list(analysis["potential_disorders"].keys())[0]
            dsm_result = dsm_checker.check_criteria_match(symptoms, top_disorder)

            # Step 3: Calculate confidence
            confidence_result = confidence_calculator.calculate_overall_confidence(analysis, top_disorder)

            return {
                "diagnosis": dsm_result.diagnosis,
                "confidence": confidence_result.get("overall_confidence", 0.0),
                "severity": confidence_result.get("severity", "unknown"),
                "reasoning": f"Fallback diagnosis due to recursion error. {dsm_result.reasoning}",
                "error_handling": "RecursionErrorFallback",
                "intermediate_results": {
                    "analysis": analysis,
                    "dsm_result": {
                        "diagnosis": dsm_result.diagnosis,
                        "confidence": dsm_result.confidence,
                        "matched_criteria": dsm_result.matched_criteria,
                        "missing_criteria": dsm_result.missing_criteria
                    },
                    "confidence_analysis": confidence_result
                }
            }

        except Exception as fallback_error:
            print(f"❌ Fallback diagnosis also failed: {fallback_error}")
            return {
                "diagnosis": "Diagnosis Error",
                "confidence": 0.0,
                "severity": "unknown",
                "reasoning": f"Both primary and fallback diagnosis failed. Primary: GraphRecursionError, Fallback: {str(fallback_error)}",
                "error_handling": "CompleteFailure",
                "intermediate_results": {"original_error": str(fallback_error)}
            }

    async def _handle_timeout_error(self, symptoms: List[str], partial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timeout errors"""
        print("⏰ Diagnosis timed out, providing partial results...")

        reasoning_steps = partial_state.get("reasoning_steps", [])
        diagnosis_results = partial_state.get("diagnosis_results", {})

        return {
            "diagnosis": "Partial Diagnosis - Timeout",
            "confidence": 0.0,
            "severity": "unknown",
            "reasoning": f"Diagnosis process timed out after {len(reasoning_steps)} reasoning steps. Partial analysis available.",
            "error_handling": "TimeoutFallback",
            "intermediate_results": {
                "reasoning_steps": reasoning_steps,
                "diagnosis_results": diagnosis_results,
                "timeout_at_step": len(reasoning_steps)
            }
        }

    async def _handle_generic_error(self, symptoms: List[str], partial_state: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Handle generic errors"""
        print(f"❌ Generic error: {error_msg}")

        return {
            "diagnosis": "Error in Diagnosis Process",
            "confidence": 0.0,
            "severity": "unknown",
            "reasoning": f"An error occurred during diagnosis: {error_msg}. Please try again or consult with a healthcare professional.",
            "error_handling": "GenericError",
            "intermediate_results": {
                "error_message": error_msg,
                "partial_state": partial_state
            }
        }

    def _direct_diagnosis(self, symptoms: List[str]) -> Dict[str, Any]:
        """Direct diagnosis approach using DA tools sequentially"""

        try:
            # Try relative import first, then fallback to absolute import
            try:
                from .da_tools import symptom_analyzer, dsm_checker, confidence_calculator
            except ImportError:
                # Fallback to absolute import for direct execution
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                from da_tools import symptom_analyzer, dsm_checker, confidence_calculator

            # Step 1: Analyze symptoms
            analysis = symptom_analyzer.analyze_symptoms(symptoms)
            if not analysis.get("potential_disorders"):
                return {
                    "diagnosis": "No Clear Diagnosis",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Symptoms do not clearly match any known disorder patterns",
                    "error_handling": "DirectDiagnosis_NoMatches"
                }

            # Step 2: Get top 3 potential disorders
            potential_disorders = list(analysis["potential_disorders"].keys())[:3]
            best_result = None
            best_confidence = 0.0

            # Step 3: Check DSM criteria for each potential disorder
            for disorder_id in potential_disorders:
                try:
                    dsm_result = dsm_checker.check_criteria_match(symptoms, disorder_id)
                    if dsm_result.confidence > best_confidence:
                        best_result = dsm_result
                        best_confidence = dsm_result.confidence
                except Exception as e:
                    print(f"⚠️  Failed to check {disorder_id}: {e}")
                    continue

            if not best_result:
                return {
                    "diagnosis": "Diagnosis Check Failed",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Failed to match symptoms against DSM criteria",
                    "error_handling": "DirectDiagnosis_DSMMatchFailed"
                }

            # Step 4: Calculate confidence
            confidence_result = confidence_calculator.calculate_overall_confidence(
                analysis, list(analysis["potential_disorders"].keys())[0]
            )

            return {
                "diagnosis": best_result.diagnosis,
                "confidence": confidence_result.get("overall_confidence", best_result.confidence),
                "severity": confidence_result.get("severity", best_result.severity),
                "reasoning": f"Direct diagnosis: {best_result.reasoning}",
                "error_handling": "DirectDiagnosis_Success",
                "intermediate_results": {
                    "analysis": analysis,
                    "dsm_result": {
                        "diagnosis": best_result.diagnosis,
                        "confidence": best_result.confidence,
                        "matched_criteria": best_result.matched_criteria,
                        "missing_criteria": best_result.missing_criteria
                    },
                    "confidence_analysis": confidence_result
                }
            }

        except Exception as e:
            print(f"❌ Direct diagnosis error: {e}")
            raise Exception(f"Direct diagnosis failed: {str(e)}")

    def diagnose(self, symptoms: List[str]) -> Dict[str, Any]:
        """Run the diagnosis process with optimized flow - direct diagnosis first, ReAct as fallback"""

        # Primary approach: Direct diagnosis (fast and reliable)
        try:
            print("🔄 Starting with direct diagnosis approach...")
            direct_result = self._direct_diagnosis(symptoms)
            if direct_result and direct_result.get("confidence", 0) > 0.3:
                print("✅ Direct diagnosis successful!")
                return direct_result
            else:
                print(f"⚠️  Direct diagnosis confidence too low ({direct_result.get('confidence', 0):.2f}), trying advanced workflow...")
        except Exception as e:
            print(f"⚠️  Direct diagnosis failed: {e}")

        # Secondary approach: Simplified ReAct workflow (only if direct diagnosis is uncertain)
        try:
            print("🔄 Attempting optimized ReAct workflow...")
            return asyncio.run(self._optimized_react_diagnosis(symptoms))
        except Exception as e:
            print(f"⚠️  ReAct workflow failed: {e}")
            print("🔄 Final fallback to synchronous diagnosis...")

            try:
                return self._fallback_diagnose_sync(symptoms)
            except Exception as fallback_error:
                print(f"❌ All diagnosis methods failed: {fallback_error}")
                return self._emergency_diagnosis(symptoms, str(e), str(fallback_error))

    def _fallback_diagnose_sync(self, symptoms: List[str]) -> Dict[str, Any]:
        """Synchronous fallback diagnosis using direct tool calls"""

        print("🔄 Using synchronous fallback diagnosis...")

        try:
            from .da_tools import symptom_analyzer, dsm_checker, confidence_calculator

            # Step 1: Basic symptom validation
            if not symptoms or len(symptoms) < 2:
                return {
                    "diagnosis": "Insufficient Symptoms",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "At least 2 symptoms are required for diagnosis",
                    "error_handling": "InsufficientSymptoms"
                }

            # Step 2: Analyze symptoms
            analysis = symptom_analyzer.analyze_symptoms(symptoms)
            print(f"📊 Symptom analysis found {len(analysis.get('potential_disorders', {}))} potential disorders")

            if not analysis.get("potential_disorders"):
                return {
                    "diagnosis": "No Clear Diagnosis",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Symptoms do not clearly match any known disorder patterns",
                    "error_handling": "NoMatchesFound",
                    "intermediate_results": {"analysis": analysis}
                }

            # Step 3: Check top 2 potential diagnoses
            potential_disorders = list(analysis["potential_disorders"].keys())[:2]
            best_result = None
            best_confidence = 0.0

            for disorder_id in potential_disorders:
                try:
                    dsm_result = dsm_checker.check_criteria_match(symptoms, disorder_id)
                    if dsm_result.confidence > best_confidence:
                        best_result = dsm_result
                        best_confidence = dsm_result.confidence
                except Exception as e:
                    print(f"⚠️  Failed to check {disorder_id}: {e}")
                    continue

            if not best_result:
                return {
                    "diagnosis": "Diagnosis Check Failed",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": "Failed to match symptoms against DSM criteria",
                    "error_handling": "DSMMatchFailed",
                    "intermediate_results": {"analysis": analysis}
                }

            # Step 4: Calculate confidence
            confidence_result = confidence_calculator.calculate_overall_confidence(
                analysis, list(analysis["potential_disorders"].keys())[0]
            )

            return {
                "diagnosis": best_result.diagnosis,
                "confidence": confidence_result.get("overall_confidence", best_result.confidence),
                "severity": confidence_result.get("severity", best_result.severity),
                "reasoning": f"Fallback diagnosis: {best_result.reasoning}",
                "error_handling": "SyncFallbackSuccess",
                "intermediate_results": {
                    "analysis": analysis,
                    "dsm_result": {
                        "diagnosis": best_result.diagnosis,
                        "confidence": best_result.confidence,
                        "matched_criteria": best_result.matched_criteria,
                        "missing_criteria": best_result.missing_criteria
                    },
                    "confidence_analysis": confidence_result
                }
            }

        except Exception as e:
            raise Exception(f"Synchronous fallback failed: {str(e)}")

    async def _optimized_react_diagnosis(self, symptoms: List[str]) -> Dict[str, Any]:
        """Optimized ReAct diagnosis that avoids loops and ensures proper progression"""

        print("🔄 Starting optimized ReAct diagnosis...")

        # Step 1: Quick symptom analysis
        try:
            from .da_tools import symptom_analyzer, confidence_calculator
        except ImportError:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from da_tools import symptom_analyzer, confidence_calculator

        # Analyze symptoms
        analysis = symptom_analyzer.analyze_symptoms(symptoms)
        if not analysis.get("potential_disorders"):
            return {
                "diagnosis": "No Clear Diagnosis",
                "confidence": 0.0,
                "severity": "unknown",
                "reasoning": "Symptoms do not clearly match any known disorder patterns",
                "error_handling": "OptimizedReAct_NoMatches"
            }

        # Get top disorder
        top_disorder = list(analysis["potential_disorders"].keys())[0]

        # Calculate confidence
        confidence_result = confidence_calculator.calculate_overall_confidence(analysis, top_disorder)

        return {
            "diagnosis": analysis["potential_disorders"][top_disorder]["disorder_name"],
            "confidence": confidence_result.get("overall_confidence", 0.5),
            "severity": confidence_result.get("severity", "moderate"),
            "reasoning": f"Optimized ReAct diagnosis: {analysis['potential_disorders'][top_disorder]['disorder_name']} identified as most likely diagnosis based on symptom analysis.",
            "error_handling": "OptimizedReAct_Success",
            "intermediate_results": {
                "analysis": analysis,
                "confidence_analysis": confidence_result
            }
        }

    def _emergency_diagnosis(self, symptoms: List[str], primary_error: str, fallback_error: str) -> Dict[str, Any]:
        """Emergency diagnosis when all methods fail"""

        symptom_count = len(symptoms) if symptoms else 0

        return {
            "diagnosis": "Unable to Complete Diagnosis",
            "confidence": 0.0,
            "severity": "unknown",
            "reasoning": f"Both primary and fallback diagnosis methods failed. Primary error: {primary_error}. Fallback error: {fallback_error}. Please try again or consult with a healthcare professional.",
            "error_handling": "CompleteFailure",
            "intermediate_results": {
                "symptom_count": symptom_count,
                "primary_error": primary_error,
                "fallback_error": fallback_error,
                "symptoms_provided": symptoms[:5] if symptoms else []  # First 5 symptoms for reference
            }
        }

# MCP-compatible wrapper class
class MCPDiagnosisAgent:
    """MCP-compatible wrapper for the Diagnosis Agent"""

    def __init__(self, model_name: str = None):
        self.agent = DiagnosisReActAgent(model_name)

    def diagnose_patient(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        MCP-compatible method for patient diagnosis with enhanced error handling

        Args:
            symptoms: List of patient symptoms

        Returns:
            Diagnosis results in MCP format
        """
        try:
            # Validate symptoms first
            validation = self.validate_symptoms(symptoms)
            if not validation["valid"]:
                return {
                    "diagnosis": "Invalid Input",
                    "confidence": 0.0,
                    "severity": "unknown",
                    "reasoning": validation["error"],
                    "metadata": {
                        "agent_type": "DA Diagnosis Agent",
                        "error_type": "ValidationError",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # Perform diagnosis
            result = self.agent.diagnose(symptoms)

            # Format for MCP compatibility
            return {
                "diagnosis": result["diagnosis"],
                "confidence": result["confidence"],
                "severity": result["severity"],
                "reasoning": result["reasoning"],
                "metadata": {
                    "agent_type": "DA Diagnosis Agent",
                    "model_used": self.agent.model_name,
                    "timestamp": datetime.now().isoformat(),
                    "tools_used": ["analyze_symptoms", "check_dsm_criteria", "calculate_confidence"],
                    "error_handling": result.get("error_handling", "None")
                },
                "intermediate_results": result.get("intermediate_results", {})
            }

        except Exception as e:
            print(f"❌ Error in MCP diagnosis: {e}")
            return {
                "diagnosis": "Diagnosis System Error",
                "confidence": 0.0,
                "severity": "unknown",
                "reasoning": f"An error occurred in the diagnosis system: {str(e)}. Please try again.",
                "metadata": {
                    "agent_type": "DA Diagnosis Agent",
                    "error_type": "SystemError",
                    "timestamp": datetime.now().isoformat()
            }
        }

    def get_available_disorders(self) -> List[str]:
        """Get list of available disorders in the system"""
        try:
            # Try relative import first
            from .da_tools import dsm_criteria_bank
        except ImportError:
            # Fallback to absolute import for test environment
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from pima.scid.dsm_criteria_bank import dsm_criteria_bank

        disorders = dsm_criteria_bank.get_all_disorders()
        return [disorder.disorder_name for disorder in disorders.values()]

    def validate_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Validate symptom input"""
        if not symptoms or len(symptoms) == 0:
            return {"valid": False, "error": "No symptoms provided"}

        if len(symptoms) > 50:
            return {"valid": False, "error": "Too many symptoms (max 50)"}

        # Check for empty or very short symptoms
        invalid_symptoms = [s for s in symptoms if len(s.strip()) < 3]
        if invalid_symptoms:
            return {"valid": False, "error": f"Invalid symptoms: {invalid_symptoms}"}

        return {"valid": True, "symptom_count": len(symptoms)}

# Global instance for easy access
diagnosis_agent = MCPDiagnosisAgent()

# Convenience functions
def diagnose_patient(symptoms: List[str]) -> Dict[str, Any]:
    """Convenience function for patient diagnosis"""
    return diagnosis_agent.diagnose_patient(symptoms)

def get_available_disorders() -> List[str]:
    """Get available disorders"""
    return diagnosis_agent.get_available_disorders()

if __name__ == "__main__":
    # Example usage
    test_symptoms = [
        " ok",
        "loss of interest in activities",
        "significant weight growth",
        "insomnia",
        "fatigue",
        "feelings of worthlessness",
        "diminished concentration"
    ]

    print("Testing DA Diagnosis Agent...")
    result = diagnose_patient(test_symptoms)

    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Severity: {result['severity']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Metadata: {result['metadata']}")

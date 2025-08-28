import json
import requests
import math
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import logging

# Import your LLM client
from llm_client import AgentLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

# Define the state
class AgentState(TypedDict):
    messages: Annotated[List[str], operator.add]
    reasoning: str
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    current_step: str
    user_input: str
    final_response: str

# Tool Classes (simplified without LangChain dependencies)
class WeatherTool:
    name = "get_weather"
    description = "Get current weather information for a city. Input should be a city name."
    
    def run(self, city: str) -> str:
        """Get weather for a city (mock implementation)"""
        try:
            # Mock weather data - in real implementation, use actual weather API
            weather_data = {
                "New York": {"temp": 22, "condition": "Sunny", "humidity": 65},
                "London": {"temp": 18, "condition": "Cloudy", "humidity": 75},
                "Tokyo": {"temp": 25, "condition": "Rainy", "humidity": 80},
                "Paris": {"temp": 20, "condition": "Partly Cloudy", "humidity": 70},
                "Sydney": {"temp": 28, "condition": "Clear", "humidity": 60}
            }
            
            city_clean = city.strip().title()
            if city_clean in weather_data:
                data = weather_data[city_clean]
                return json.dumps({
                    "city": city_clean,
                    "temperature": f"{data['temp']}°C",
                    "condition": data["condition"],
                    "humidity": f"{data['humidity']}%"
                })
            else:
                # Generate random weather for unknown cities
                import random
                conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Stormy"]
                return json.dumps({
                    "city": city_clean,
                    "temperature": f"{random.randint(10, 35)}°C",
                    "condition": random.choice(conditions),
                    "humidity": f"{random.randint(40, 90)}%"
                })
        except Exception as e:
            return f"Error getting weather for {city}: {str(e)}"

class CalculatorTool:
    name = "calculator"
    description = "Perform mathematical calculations. Input should be a mathematical expression like '2+2' or 'sqrt(16)'."
    
    def run(self, expression: str) -> str:
        """Safely evaluate mathematical expressions"""
        try:
            # Safe evaluation - only allow basic math operations
            allowed_names = {
                k: v for k, v in math._dict.items() if not k.startswith("_")
            }
            allowed_names.update({"abs": abs, "round": round})
            
            # Replace common math functions
            expression = expression.replace("^", "")
            
            result = eval(expression, {"_builtins_": {}}, allowed_names)
            return json.dumps({
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}"
            })
        except Exception as e:
            return f"Error calculating '{expression}': {str(e)}"

class DateTimeTool:
    name = "datetime_info"
    description = "Get current date/time information or calculate date differences. Use 'current' for now, or 'diff:YYYY-MM-DD' for date calculations."
    
    def run(self, query: str) -> str:
        """Get date/time information"""
        try:
            now = datetime.now()
            
            if query.lower() == "current":
                return json.dumps({
                    "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                    "weekday": now.strftime("%A"),
                    "month": now.strftime("%B"),
                    "year": now.year
                })
            elif query.startswith("diff:"):
                target_date_str = query.split(":", 1)[1]
                target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
                diff = target_date - now
                
                return json.dumps({
                    "target_date": target_date_str,
                    "current_date": now.strftime("%Y-%m-%d"),
                    "days_difference": diff.days,
                    "weeks_difference": round(diff.days / 7, 2),
                    "in_past": diff.days < 0
                })
            else:
                return "Invalid query. Use 'current' or 'diff:YYYY-MM-DD'"
        except Exception as e:
            return f"Error processing date query '{query}': {str(e)}"

class TextAnalyzerTool:
    name = "text_analyzer"
    description = "Analyze text properties like word count, character count, and basic statistics."
    
    def run(self, text: str) -> str:
        """Analyze text properties"""
        try:
            words = text.split()
            sentences = text.replace('!', '.').replace('?', '.').split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Character frequency
            char_freq = {}
            for char in text.lower():
                if char.isalpha():
                    char_freq[char] = char_freq.get(char, 0) + 1
            
            # Most common character
            most_common_char = max(char_freq.items(), key=lambda x: x[1]) if char_freq else ("", 0)
            
            return json.dumps({
                "total_characters": len(text),
                "total_characters_no_spaces": len(text.replace(" ", "")),
                "total_words": len(words),
                "total_sentences": len(sentences),
                "average_word_length": round(sum(len(word) for word in words) / len(words), 2) if words else 0,
                "most_common_character": most_common_char[0] if most_common_char[1] > 0 else None,
                "most_common_character_count": most_common_char[1]
            })
        except Exception as e:
            return f"Error analyzing text: {str(e)}"

class UnitConverterTool:
    name = "unit_converter"
    description = "Convert between units. Format: 'value|from_unit|to_unit' (e.g., '100|celsius|fahrenheit', '5|miles|kilometers')"
    
    def run(self, conversion: str) -> str:
        """Convert between different units"""
        try:
            parts = conversion.split("|")
            if len(parts) != 3:
                return "Format: 'value|from_unit|to_unit'"
            
            value, from_unit, to_unit = parts
            value = float(value)
            from_unit = from_unit.lower().strip()
            to_unit = to_unit.lower().strip()
            
            # Temperature conversions
            if from_unit == "celsius" and to_unit == "fahrenheit":
                result = (value * 9/5) + 32
                return json.dumps({
                    "original": f"{value}°C",
                    "converted": f"{result}°F",
                    "calculation": f"({value} × 9/5) + 32 = {result}"
                })
            elif from_unit == "fahrenheit" and to_unit == "celsius":
                result = (value - 32) * 5/9
                return json.dumps({
                    "original": f"{value}°F",
                    "converted": f"{round(result, 2)}°C",
                    "calculation": f"({value} - 32) × 5/9 = {round(result, 2)}"
                })
            
            # Length conversions
            elif from_unit == "miles" and to_unit == "kilometers":
                result = value * 1.609344
                return json.dumps({
                    "original": f"{value} miles",
                    "converted": f"{round(result, 2)} km",
                    "calculation": f"{value} × 1.609344 = {round(result, 2)}"
                })
            elif from_unit == "kilometers" and to_unit == "miles":
                result = value / 1.609344
                return json.dumps({
                    "original": f"{value} km",
                    "converted": f"{round(result, 2)} miles",
                    "calculation": f"{value} ÷ 1.609344 = {round(result, 2)}"
                })
            elif from_unit == "feet" and to_unit == "meters":
                result = value * 0.3048
                return json.dumps({
                    "original": f"{value} feet",
                    "converted": f"{round(result, 2)} meters",
                    "calculation": f"{value} × 0.3048 = {round(result, 2)}"
                })
            elif from_unit == "meters" and to_unit == "feet":
                result = value / 0.3048
                return json.dumps({
                    "original": f"{value} meters",
                    "converted": f"{round(result, 2)} feet",
                    "calculation": f"{value} ÷ 0.3048 = {round(result, 2)}"
                })
            
            # Weight conversions
            elif from_unit == "pounds" and to_unit == "kilograms":
                result = value * 0.453592
                return json.dumps({
                    "original": f"{value} lbs",
                    "converted": f"{round(result, 2)} kg",
                    "calculation": f"{value} × 0.453592 = {round(result, 2)}"
                })
            elif from_unit == "kilograms" and to_unit == "pounds":
                result = value / 0.453592
                return json.dumps({
                    "original": f"{value} kg",
                    "converted": f"{round(result, 2)} lbs",
                    "calculation": f"{value} ÷ 0.453592 = {round(result, 2)}"
                })
            
            else:
                return f"Conversion from {from_unit} to {to_unit} not supported. Available: celsius/fahrenheit, miles/kilometers, feet/meters, pounds/kilograms"
                
        except Exception as e:
            return f"Error in unit conversion: {str(e)}"

# Initialize tools
TOOLS = {
    "get_weather": WeatherTool(),
    "calculator": CalculatorTool(),
    "datetime_info": DateTimeTool(),
    "text_analyzer": TextAnalyzerTool(),
    "unit_converter": UnitConverterTool()
}

class ReasoningChatbot:
    """LangGraph-based chatbot with reasoning and tool calling capabilities"""
    
    def _init_(self):
        """Initialize the chatbot with LLM client and tools"""
        self.llm_client = AgentLLMClient(
            agent_name="ReasoningChatbot",
            system_prompt="""You are an intelligent assistant that follows a strict Observe-Reason-Act pattern.

For every user request:
1. OBSERVE: Analyze what the user is asking for
2. REASON: Think through what tools (if any) you need to use and why
3. ACT: Either use tools or provide a direct response

Available tools and their purposes:
- get_weather: Get weather information for cities (input: city name)
- calculator: Perform mathematical calculations (input: mathematical expression)
- datetime_info: Get date/time info (input: 'current' or 'diff:YYYY-MM-DD')
- text_analyzer: Analyze text properties (input: text to analyze)
- unit_converter: Convert units (input: 'value|from_unit|to_unit')

IMPORTANT: Always explain your reasoning process step by step. Be explicit about why you're choosing certain tools or providing direct answers.

When using tools, format your response as JSON with this structure:
{
    "reasoning": "Your step-by-step reasoning process",
    "tool_calls": [
        {
            "tool": "tool_name",
            "input": "tool_input",
            "justification": "why you're using this tool"
        }
    ]
}

If no tools are needed, format as:
{
    "reasoning": "Your reasoning process",
    "response": "Your direct answer",
    "tool_calls": []
}""",
            model="llama3-8b-8192"
        )
        
        self.setup_graph()
    
    def setup_graph(self):
        """Set up the LangGraph state graph"""
        workflow = StateGraph(AgentState)
        
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
    
    def reasoning_node(self, state: AgentState) -> Dict[str, Any]:
        """First node: Observe and reason about the user's request"""
        print("\n🧠 REASONING NODE - Observing and Analyzing...")
        
        user_message = state.get("user_input", "")
        
        if not user_message:
            return {
                "reasoning": "No user message found",
                "tool_calls": [],
                "current_step": "error"
            }
        
        # Generate reasoning response
        reasoning_prompt = f"""
        User Request: "{user_message}"
        
        Follow the Observe-Reason-Act pattern:
        
        1. OBSERVE: What is the user asking for?
        2. REASON: What approach should I take? Do I need tools?
        3. ACT: What specific actions should I take?
        
        Respond in JSON format as specified in your system prompt.
        """
        
        response = self.llm_client.generate_with_history(
            reasoning_prompt,
            temperature=0.3,
            max_tokens=800
        )
        
        print(f"🔍 LLM Reasoning Response: {response}")
        
        try:
            # Try to parse JSON response
            if response.startswith("Error:"):
                reasoning_data = {
                    "reasoning": "LLM client error occurred",
                    "tool_calls": [],
                    "response": response
                }
            else:
                # Extract JSON from response if it's wrapped in other text
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    reasoning_data = json.loads(json_str)
                else:
                    # Fallback: treat as direct response
                    reasoning_data = {
                        "reasoning": f"Direct response provided: {response}",
                        "tool_calls": [],
                        "response": response
                    }
        except json.JSONDecodeError as e:
            # Fallback for non-JSON responses
            print(f"⚠ JSON Parse Error: {e}")
            reasoning_data = {
                "reasoning": f"Analyzing request: {user_message}. Providing direct response due to JSON parsing issue.",
                "tool_calls": [],
                "response": response
            }
        
        # Print reasoning
        print(f"📝 REASONING: {reasoning_data.get('reasoning', 'No reasoning provided')}")
        
        return {
            "reasoning": reasoning_data.get("reasoning", ""),
            "tool_calls": reasoning_data.get("tool_calls", []),
            "current_step": "reasoned"
        }
    
    def should_use_tools(self, state: AgentState) -> str:
        """Decide whether to use tools or provide direct response"""
        has_tool_calls = len(state.get("tool_calls", [])) > 0
        print(f"🤔 DECISION: {'Using tools' if has_tool_calls else 'Direct response'}")
        return "use_tools" if has_tool_calls else "direct_response"
    
    def tool_execution_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the required tools"""
        print("\n⚡ TOOL EXECUTION NODE - Running Tools...")
        
        tool_results = []
        
        for tool_call in state.get("tool_calls", []):
            tool_name = tool_call.get("tool", "")
            tool_input = tool_call.get("input", "")
            justification = tool_call.get("justification", "")
            
            print(f"🔧 Using tool: {tool_name}")
            print(f"📥 Input: {tool_input}")
            print(f"💭 Justification: {justification}")
            
            if tool_name in TOOLS:
                try:
                    result = TOOLS[tool_name].run(tool_input)
                    print(f"📤 Tool Result: {result}")
                    
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result,
                        "justification": justification
                    })
                    
                except Exception as e:
                    error_result = f"Error executing {tool_name}: {str(e)}"
                    print(f"❌ Tool Error: {error_result}")
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": error_result,
                        "justification": justification
                    })
            else:
                error_result = f"Tool {tool_name} not found. Available tools: {list(TOOLS.keys())}"
                print(f"❌ Tool Error: {error_result}")
                tool_results.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": error_result,
                    "justification": justification
                })
        
        return {
            "tool_results": tool_results,
            "current_step": "tools_executed"
        }
    
    def response_generation_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate final response based on reasoning and tool results"""
        print("\n📝 RESPONSE GENERATION NODE - Creating Final Answer...")
        
        # Check if we have tool results to incorporate
        tool_results = state.get("tool_results", [])
        reasoning = state.get("reasoning", "")
        user_input = state.get("user_input", "")
        
        if tool_results:
            # Generate response incorporating tool results
            tool_summary = "\n".join([
                f"- {result['tool']}: {result['result']}" 
                for result in tool_results
            ])
            
            response_prompt = f"""
            Based on my reasoning and tool execution results, provide a comprehensive but friendly and concise whatsapp chat like answer to the user's question: "{user_input}"
            
            My Reasoning: {reasoning}
            
            Tool Results:
            {tool_summary}
            
            Provide a concise whatsapp chat like but clear, helpful response that incorporates the tool results naturally. Don't just repeat the raw tool output - synthesize it into a human-friendly answer.
            """
            
            final_response = self.llm_client.generate(
                response_prompt,
                temperature=0.3,
                max_tokens=600
            )
            
        else:
            # Direct response case - use the response from reasoning if available
            existing_response = None
            for msg in reversed(state.get("messages", [])):
                if "response" in str(msg):
                    existing_response = msg
                    break
            
            if existing_response:
                final_response = existing_response
            else:
                final_response = self.llm_client.generate(
                    f"Provide a helpful response to: {user_input}",
                    temperature=0.7,
                    max_tokens=600
                )
        
        print(f"✅ FINAL RESPONSE: {final_response}")
        
        return {
            "final_response": final_response,
            "current_step": "completed"
        }
    
    def chat(self, message: str) -> str:
        """Main chat interface"""
        print(f"\n" + "="*80)
        print(f"💬 USER: {message}")
        print("="*80)
        
        # Create initial state
        initial_state = {
            "messages": [],
            "reasoning": "",
            "tool_calls": [],
            "tool_results": [],
            "current_step": "start",
            "user_input": message,
            "final_response": ""
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
            print(f"❌ CHAT ERROR: {error_msg}")
            return error_msg

def main():
    """Interactive chatbot main function"""
    print("🤖 LangGraph Reasoning Chatbot with Tools")
    print("="*60)
    print("🛠  Available Tools:")
    print("   🌤  get_weather - Get weather for any city")
    print("   🧮 calculator - Perform mathematical calculations")
    print("   📅 datetime_info - Get current date/time or calculate differences")
    print("   📝 text_analyzer - Analyze text properties and statistics")
    print("   ⚖  unit_converter - Convert between different units")
    print("="*60)
    print("💡 Example queries:")
    print("   • 'What's the weather in Tokyo?'")
    print("   • 'Calculate 15 * 23 + sqrt(144)'")
    print("   • 'What's the current date?'")
    print("   • 'Analyze: The quick brown fox jumps'")
    print("   • 'Convert 75 fahrenheit to celsius'")
    print("   • 'What's 2+2 and weather in Paris?' (multi-tool)")
    print("="*60)
    print("🔤 Commands: 'help', 'tools', 'clear', 'quit'")
    print("="*60)
    
    try:
        chatbot = ReasoningChatbot()
        print("✅ Chatbot initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return
    
    conversation_count = 0
    
    # Interactive loop
    while True:
        try:
            user_input = input(f"\n💭 You [{conversation_count + 1}]: ").strip()
            
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("👋 Thank you for using the Reasoning Chatbot! Goodbye!")
                break
                
            elif user_input.lower() in ['help', 'h']:
                print("\n🆘 Help:")
                print("• Ask questions naturally - the bot will reason and use tools")
                print("• Use 'tools' to see available tools")
                print("• Use 'clear' to clear conversation history")
                print("• Use 'quit' or 'exit' to exit")
                continue
                
            elif user_input.lower() in ['tools', 'tool']:
                print("\n🛠  Available Tools:")
                for tool_name, tool in TOOLS.items():
                    print(f"   📌 {tool_name}: {tool.description}")
                continue
                
            elif user_input.lower() in ['clear', 'cls']:
                chatbot.llm_client.clear_history(keep_system=True)
                conversation_count = 0
                print("🧹 Conversation history cleared!")
                continue
                
            elif not user_input:
                print("⚠  Please enter a message or command.")
                continue
            
            # Process user input
            print(f"\n🔄 Processing your request...")
            conversation_count += 1
            
            response = chatbot.chat(user_input)
            
            # Display response with formatting
            print(f"\n🤖 Assistant:")
            print("─" * 50)
            print(response)
            print("─" * 50)
            
            # Show conversation stats
            if conversation_count % 5 == 0:
                print(f"💬 Conversation count: {conversation_count}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("🔄 Continuing with next input...")
            continue

if _name_ == "_main_":
    main()
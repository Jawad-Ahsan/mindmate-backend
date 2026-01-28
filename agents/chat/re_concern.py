import requests
import os
import json
import time
import asyncio
from typing import List, Dict, Optional, Union, Any, Callable
from dataclasses import dataclass
import logging
import hashlib
from functools import wraps
import threading
from collections import deque
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class Message:
    """Represents a chat message"""
    role: str  # "system", "user", "assistant"
    content: str

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == 'OPEN':
                if self.last_failure_time and \
                   datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                    self.state = 'HALF_OPEN'
                    logger.info("Circuit breaker moving to HALF_OPEN state")
                else:
                    raise Exception("Circuit breaker is OPEN - service unavailable")
            
            try:
                result = func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                    logger.info("Circuit breaker reset to CLOSED state")
                return result
                
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.now()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'
                    logger.error(f"Circuit breaker opened after {self.failure_count} failures")
                
                raise e

class RequestQueue:
    """Thread-safe request queue with rate limiting"""
    
    def __init__(self, max_requests_per_minute: int = 8, max_concurrent: int = 2):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_concurrent = max_concurrent
        self.request_times = deque()
        self.active_requests = 0
        self._lock = threading.Lock()
    
    def can_make_request(self) -> bool:
        """Check if we can make a request without hitting rate limits"""
        now = datetime.now()
        
        # Clean old requests
        while self.request_times and (now - self.request_times[0]) > timedelta(minutes=1):
            self.request_times.popleft()
        
        return (len(self.request_times) < self.max_requests_per_minute and 
                self.active_requests < self.max_concurrent)
    
    def wait_for_slot(self, timeout: int = 120):
        """Wait for an available request slot"""
        start_time = time.time()
        
        while not self.can_make_request():
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for request slot")
            
            sleep_time = max(1.0, 60.0 / self.max_requests_per_minute)
            time.sleep(sleep_time)
    
    def acquire_slot(self):
        """Acquire a request slot"""
        with self._lock:
            self.wait_for_slot()
            self.request_times.append(datetime.now())
            self.active_requests += 1
    
    def release_slot(self):
        """Release a request slot"""
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)

class ResponseCache:
    """Simple in-memory cache for responses"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self._lock = threading.Lock()
    
    def _generate_key(self, prompt: str, model: str = None, **kwargs) -> str:
        """Generate cache key with timestamp to prevent stale caching"""
        timestamp = int(time.time() / 60)  # Change key every minute
        cache_data = {
            'prompt': prompt[:500],  # Only use first 500 chars
            'model': model or 'default',
            'timestamp': timestamp,
            'kwargs': {k: v for k, v in kwargs.items() if k in ['temperature', 'max_tokens']}
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
        
    def get(self, key: str) -> Optional[str]:
        """Get cached response if valid"""
        with self._lock:
            if key in self.cache:
                response, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    return response
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, response: str):
        """Cache response"""
        with self._lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (response, time.time())

class LLMClient:
    """
    Enhanced LLM client with circuit breaker, rate limiting, caching, and robust error handling.
    """
    
    def __init__(self, model: str = None, enable_cache: bool = True):
        """
        Initialize the enhanced LLM client.
        
        Args:
            model: The model to use (if None, will use GROQ_MODEL from .env or default)
            enable_cache: Whether to enable response caching
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        # Get model from environment variable or use provided model or default
        if model is None:
            self.model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        else:
            self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize components
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
        self.request_queue = RequestQueue(max_requests_per_minute=6, max_concurrent=1)
        self.cache = ResponseCache(max_size=50, ttl_seconds=1800) if enable_cache else None
        
        # Model configuration
        self.max_context_length = self._get_model_context_limit()
        
        # Verify connection
        self._verify_connection()
    
    def _get_model_context_limit(self) -> int:
        """Get context limit for the model"""
        context_limits = {
            "mixtral-8x7b-32768": 32768,
            "llama2-70b-4096": 4096,
            "gemma-7b-it": 8192,
            "mistral-saba-24b": 8192,
            "qwen/qwen3-32b": 32768,
            "qwen/qwen-2.5-72b-instruct": 32768,
            "qwen/qwen-2.5-coder-32b-instruct": 32768,
            "llama3-8b-8192": 8192,
            "llama3-70b-8192": 8192,
            "llama-3.3-70b-versatile": 32768,
            "moonshotai/kimi-k2-instruct": 32768,
            "whisper-large-v3": 8192
        }
        return context_limits.get(self.model, 8192)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return max(1, len(text) // 4)
    
    def _verify_connection(self) -> bool:
        """Verify API connection with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
                response.raise_for_status()
                
                models = response.json()
                available_models = [model['id'] for model in models.get('data', [])]
                
                if self.model not in available_models:
                    logger.warning(f"Model {self.model} not found in available models.")
                    logger.info(f"Available models: {available_models}")
                    
                    # Try to find a suitable alternative
                    qwen_alternatives = [m for m in available_models if 'qwen' in m.lower()]
                    llama_alternatives = [m for m in available_models if 'llama' in m.lower()]
                    
                    if qwen_alternatives:
                        self.model = qwen_alternatives[0]
                        logger.info(f"Switched to Qwen alternative: {self.model}")
                    elif llama_alternatives:
                        self.model = llama_alternatives[0]
                        logger.info(f"Switched to Llama alternative: {self.model}")
                    elif available_models:
                        self.model = available_models[0]
                        logger.info(f"Switched to first available model: {self.model}")
                    else:
                        raise ValueError("No models available from API")
                
                logger.info(f"Connected to Groq API successfully. Using model: {self.model}")
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect to Groq API after {max_retries} attempts: {e}")
                    raise
    
    def _truncate_payload(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        """Intelligently truncate payload to fit within limits"""
        # Calculate total tokens
        total_tokens = sum(self._estimate_tokens(msg['content']) for msg in messages)
        
        # Reserve tokens for response
        available_tokens = self.max_context_length - max_tokens - 500  # Buffer
        
        if total_tokens <= available_tokens:
            return messages
        
        logger.warning(f"Payload too large ({total_tokens} tokens), truncating...")
        
        # Keep system message and recent messages
        truncated = []
        remaining_tokens = available_tokens
        
        # Always keep system message if present
        if messages and messages[0]['role'] == 'system':
            sys_msg = messages[0]
            sys_tokens = self._estimate_tokens(sys_msg['content'])
            if sys_tokens < remaining_tokens:
                truncated.append(sys_msg)
                remaining_tokens -= sys_tokens
                messages = messages[1:]
        
        # Add messages from the end (most recent first)
        for msg in reversed(messages):
            msg_tokens = self._estimate_tokens(msg['content'])
            if msg_tokens < remaining_tokens:
                truncated.insert(-len([m for m in truncated if m['role'] != 'system']), msg)
                remaining_tokens -= msg_tokens
            else:
                # Truncate this message content
                if remaining_tokens > 100:  # Only if we have significant space left
                    max_chars = (remaining_tokens - 50) * 4  # Convert tokens back to chars
                    truncated_content = msg['content'][:max_chars] + "... [truncated]"
                    truncated_msg = {**msg, 'content': truncated_content}
                    truncated.insert(-len([m for m in truncated if m['role'] != 'system']), truncated_msg)
                break
        
        logger.info(f"Truncated to {len(truncated)} messages")
        return truncated
    
    def _make_request_with_protection(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 800,
        temperature: float = 0.7,
        top_p: float = 0.9,
        timeout: int = 120,
        **kwargs
    ) -> str:
        """Make protected API request with all safety measures"""
        
        # Truncate payload if necessary
        messages = self._truncate_payload(messages, max_tokens)
        
        # Check cache first
        cache_key = None
        if self.cache:
            messages_str = json.dumps(messages)
            cache_key = self.cache._generate_key(
                messages_str,
                model=self.model,
                temperature=temperature, 
                max_tokens=max_tokens
            )
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info("Returning cached response")
                return cached_response
        
        # Acquire request slot
        self.request_queue.acquire_slot()
        
        try:
            # Prepare payload
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
                **kwargs
            }
            
            # Make request through circuit breaker
            def api_call():
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                return response.json()
            
            result = self.circuit_breaker.call(api_call)
            
            # Extract response
            if 'choices' not in result or not result['choices']:
                raise ValueError("No response choices returned from API")
            
            response_text = result['choices'][0]['message']['content']
            
            # Cache successful response
            if self.cache and cache_key:
                self.cache.set(cache_key, response_text)
            
            return response_text
            
        finally:
            self.request_queue.release_slot()
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.7,
        max_retries: int = 3,
        **kwargs
    ) -> str:
        """Generate response with comprehensive error handling"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return self._make_request_with_protection(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                if "429" in str(e) or "rate limit" in error_str:
                    wait_time = (attempt + 1) * 30 + 60  # Longer waits for rate limits
                    logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                elif "413" in str(e) or "payload too large" in error_str:
                    # Reduce max_tokens and try again
                    max_tokens = max(200, max_tokens // 2)
                    logger.warning(f"Payload too large, reducing max_tokens to {max_tokens}")
                    continue
                elif "timeout" in error_str:
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"Timeout error, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"API error, retrying in {wait_time}s: {str(e)[:100]}")
                    time.sleep(wait_time)
        
        # Return fallback response instead of raising
        logger.error(f"Failed to generate response after {max_retries} attempts: {last_exception}")
        return f"Error: Unable to generate response due to API limitations. Last error: {str(last_exception)[:100]}"
    
    def chat(
        self,
        messages: List[Union[Message, Dict[str, str]]],
        max_tokens: int = 800,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Chat with conversation history"""
        # Convert Message objects to dicts
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, Message):
                formatted_messages.append({"role": msg.role, "content": msg.content})
            else:
                formatted_messages.append(msg)
        
        try:
            return self._make_request_with_protection(
                messages=formatted_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return f"Error: Chat generation failed due to API limitations."
    
    def get_json_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 800,
        temperature: float = 0.1,
        max_retries: int = 3,
        **kwargs
    ) -> dict:
        """Generate response and ensure it returns valid JSON"""
        json_instruction = " IMPORTANT: Return your response as valid JSON only, no additional text before or after."
        enhanced_prompt = prompt + json_instruction
        
        if system_prompt:
            enhanced_system = system_prompt + " You must return all responses in valid JSON format."
        else:
            enhanced_system = "You must return all responses in valid JSON format."
        
        for attempt in range(max_retries):
            try:
                response = self.generate(
                    prompt=enhanced_prompt,
                    system_prompt=enhanced_system,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                
                # Clean the response
                response = response.strip()
                
                # Try to extract JSON if wrapped in markdown or other text
                if '```json' in response:
                    start = response.find('```json') + 7
                    end = response.find('```', start)
                    if end != -1:
                        response = response[start:end].strip()
                elif '```' in response:
                    start = response.find('```') + 3
                    end = response.find('```', start)
                    if end != -1:
                        response = response[start:end].strip()
                
                # Find JSON content between braces
                if '{' in response and '}' in response:
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    response = response[start:end]
                
                # Parse JSON
                parsed = json.loads(response)
                return parsed
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {e}")
                logger.warning(f"Response was: {response[:200]}...")
                
                if attempt == max_retries - 1:
                    # Return a structured error response
                    return {
                        "error": "Failed to parse JSON response",
                        "raw_response": response[:500],
                        "attempt": attempt + 1
                    }
                
                # Wait before retry
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return {
                        "error": str(e),
                        "attempt": attempt + 1
                    }
                time.sleep(1)
        
        return {"error": "Maximum retries exceeded"}

class AgentLLMClient(LLMClient):
    """
    Agent-specific LLM client with enhanced conversation management
    """ 
    
    def __init__(self, agent_name: str, system_prompt: str = None, **kwargs):
        """Initialize agent-specific client"""
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.conversation_history: List[Message] = []
        self.max_history_tokens = 4000
        self._history_lock = threading.Lock()
        
        if system_prompt:
            self.conversation_history.append(Message("system", system_prompt))
    
    def add_message(self, role: str, content: str) -> None:
        """Add message with history management"""
        with self._history_lock:
            self.conversation_history.append(Message(role, content))
            self._manage_history_size()
    
    def _manage_history_size(self):
        """Keep conversation history within token limits"""
        total_tokens = sum(self._estimate_tokens(msg.content) for msg in self.conversation_history)
        
        if total_tokens > self.max_history_tokens:
            # Keep system message and recent messages
            system_msgs = [msg for msg in self.conversation_history if msg.role == "system"]
            other_msgs = [msg for msg in self.conversation_history if msg.role != "system"]
            
            # Keep recent messages that fit in budget
            remaining_tokens = self.max_history_tokens - sum(self._estimate_tokens(msg.content) for msg in system_msgs)
            kept_msgs = []
            
            # Add system messages first
            kept_msgs.extend(system_msgs)
            
            # Add recent messages from the end
            for msg in reversed(other_msgs):
                msg_tokens = self._estimate_tokens(msg.content)
                if msg_tokens < remaining_tokens:
                    kept_msgs.insert(len(system_msgs), msg)  # Insert after system messages
                    remaining_tokens -= msg_tokens
                else:
                    break
            
            if len(kept_msgs) < len(self.conversation_history):
                logger.info(f"Trimmed conversation history from {len(self.conversation_history)} to {len(kept_msgs)} messages")
                self.conversation_history = kept_msgs
    
    def generate_with_history(
        self,
        prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.7,
        remember_response: bool = True,
        **kwargs
    ) -> str:
        """Generate response using conversation history"""
        self.add_message("user", prompt)
        
        try:
            response = self.chat(
                messages=self.conversation_history,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            if remember_response and not response.startswith("Error:"):
                self.add_message("assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"History-based generation failed: {e}")
            # Try without history as fallback
            try:
                fallback_response = self.generate(
                    prompt=prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                if remember_response and not fallback_response.startswith("Error:"):
                    self.add_message("assistant", fallback_response)
                return fallback_response
            except Exception as fallback_error:
                error_msg = f"Both history and fallback generation failed: {fallback_error}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
    
    def clear_history(self, keep_system: bool = True) -> None:
        """Clear conversation history"""
        with self._history_lock:
            if keep_system and self.system_prompt:
                self.conversation_history = [Message("system", self.system_prompt)]
            else:
                self.conversation_history = []
        logger.info(f"Conversation history cleared for agent: {self.agent_name}")
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get comprehensive history summary"""
        with self._history_lock:
            return {
                "agent_name": self.agent_name,
                "total_messages": len(self.conversation_history),
                "system_prompt": self.system_prompt,
                "last_message": self.conversation_history[-1].content[:100] if self.conversation_history else None,
                "estimated_tokens": sum(self._estimate_tokens(msg.content) for msg in self.conversation_history),
                "max_history_tokens": self.max_history_tokens
            }


# Enhanced Mental Health Assessment System

class MentalHealthAssessment:
    def __init__(self, client: LLMClient):
        self.client = client
        self.assessment_goals = {
            'primary_concern': False,
            'onset_timeline': False,
            'severity_level': False,
            'triggers': False,
            'suicidal_ideation': False,
            'functional_impact': False
        }
        self.collected_info = {}
        self.conversation_log = []
    
    def get_progress(self) -> float:
        """Calculate assessment completion percentage"""
        completed = sum(1 for goal in self.assessment_goals.values() if goal)
        return (completed / len(self.assessment_goals)) * 100
    
    def get_missing_goals(self) -> List[str]:
        """Get list of incomplete assessment goals"""
        return [goal for goal, completed in self.assessment_goals.items() if not completed]
    
    def analyze_patient_response(self, patient_response: str, conversation_context: str) -> dict:
        """Analyze patient response using LLM with strict JSON format"""
        
        analysis_prompt = f"""
You are a mental health professional analyzing a patient's response. 

CONVERSATION CONTEXT:
{conversation_context}

PATIENT'S CURRENT RESPONSE: "{patient_response}"

ASSESSMENT GOALS (mark as complete only if explicitly mentioned):
- primary_concern: Main mental health issue/problem
- onset_timeline: When symptoms started, duration
- severity_level: Severity rating (1-10) or descriptive terms (mild/moderate/severe)
- triggers: Specific triggers that worsen symptoms (not "none" or "unsure")
- suicidal_ideation: Explicit yes/no about self-harm thoughts
- functional_impact: Specific impact on work, relationships, or daily activities

Analyze the patient's response and return ONLY a JSON object with these fields:
{{
    "patient_emotional_state": "calm/anxious/distressed/confused/withdrawn/agitated",
    "information_extracted": "brief summary of medical/psychological information found",
    "goals_completed": ["list of goals from above that are NOW complete based on this response"],
    "next_priority": "most important question to ask next",
    "safety_flags": "immediate/moderate/low/none",
    "readiness_to_conclude": "ready/needs_more_info/requires_safety_intervention"
}}

CRITICAL: Return ONLY the JSON object, no other text.
"""
        
        try:
            response = self.client.get_json_response(
                prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=500
            )
            
            # Validate response structure
            required_fields = ['patient_emotional_state', 'information_extracted', 'goals_completed', 'next_priority', 'safety_flags', 'readiness_to_conclude']
            
            if not all(field in response for field in required_fields):
                logger.error(f"Missing required fields in response: {response}")
                return self._get_fallback_analysis()
            
            return response
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> dict:
        """Provide fallback analysis when LLM fails"""
        return {
            "patient_emotional_state": "unknown",
            "information_extracted": "Unable to analyze response due to technical error",
            "goals_completed": [],
            "next_priority": "Can you tell me more about what's been troubling you?",
            "safety_flags": "none",
            "readiness_to_conclude": "needs_more_info"
        }
    
    def extract_medical_info(self, patient_response: str) -> dict:
        """Extract specific medical information with strict requirements"""
        
        extraction_prompt = f"""
Extract specific medical/psychological information from this patient response: "{patient_response}"

Return ONLY a JSON object with these fields (use "not_mentioned" if information is not provided):
{{
    "primary_concern": "specific mental health issue mentioned or not_mentioned",
    "onset_timeline": "when symptoms started and duration or not_mentioned", 
    "severity_level": "exact severity rating (1-10) or terms like mild/moderate/severe or not_mentioned",
    "triggers": "specific triggers mentioned (NOT general terms like 'stress') or not_mentioned",
    "suicidal_ideation": "yes/no/not_mentioned - only yes if explicitly mentions self-harm thoughts",
    "functional_impact": "specific impacts on work/relationships/daily activities or not_mentioned"
}}

CRITICAL: Be very strict - only extract information that is explicitly stated. Return ONLY JSON.
"""
        
        try:
            response = self.client.get_json_response(
                prompt=extraction_prompt,
                temperature=0.0,
                max_tokens=400
            )
            
            # Update collected info with non-"not_mentioned" values
            for key, value in response.items():
                if key in self.assessment_goals and value != "not_mentioned":
                    self.collected_info[key] = value
                    self.assessment_goals[key] = True
            
            return response
            
        except Exception as e:
            logger.error(f"Medical info extraction failed: {e}")
            return {key: "not_mentioned" for key in self.assessment_goals.keys()}
    
    def generate_next_question(self, analysis: dict) -> str:
        """Generate the next appropriate question"""

        missing_goals = self.get_missing_goals()
        safety_flags = analysis.get('safety_flags', 'none')
        emotional_state = analysis.get('patient_emotional_state', 'unknown')

        # Handle safety concerns first
        if safety_flags == 'immediate':
            return "I'm concerned about your safety. Are you in immediate danger or thinking about harming yourself right now?"

        if safety_flags == 'moderate':
            return "I notice you mentioned some difficult thoughts. Can you tell me more about what's been troubling you lately?"

        # Generate question based on missing goals and emotional state
        if 'primary_concern' in missing_goals:
            if emotional_state in ['anxious', 'distressed', 'agitated']:
                return "I can sense you're feeling quite distressed right now. What's been weighing on your mind most heavily?"
            else:
                return "Can you tell me what's been troubling you most lately?"

        if 'onset_timeline' in missing_goals:
            return "When did you first notice these feelings or changes? Has this been going on for days, weeks, or longer?"

        if 'severity_level' in missing_goals:
            return "On a scale of 1-10, with 1 being mild and 10 being the most severe you've ever felt, how would you rate your current distress?"

        if 'triggers' in missing_goals:
            return "Are there specific situations, people, or events that tend to make your symptoms worse?"

        if 'suicidal_ideation' in missing_goals:
            return "Have you had any thoughts of harming yourself or ending your life recently?"

        if 'functional_impact' in missing_goals:
            return "How have these feelings been affecting your daily life, work, relationships, or ability to function?"

        # If all goals are complete but assessment not ready to conclude
        if analysis.get('readiness_to_conclude') == 'needs_more_info':
            return "Can you tell me more about how you've been coping or what kind of support you've been receiving?"

        return "Thank you for sharing that with me. How are you feeling about the conversation so far?"

    def update_assessment_status(self, analysis: dict) -> None:
        """Update assessment goals based on analysis results"""
        goals_completed = analysis.get('goals_completed', [])

        for goal in goals_completed:
            if goal in self.assessment_goals:
                self.assessment_goals[goal] = True
                logger.info(f"Assessment goal completed: {goal}")

    def generate_assessment_report(self) -> str:
        """Generate comprehensive assessment report"""

        report_prompt = f"""
Based on the collected information, generate a comprehensive mental health assessment report:

COLLECTED INFORMATION:
{json.dumps(self.collected_info, indent=2)}

ASSESSMENT GOALS STATUS:
{json.dumps(self.assessment_goals, indent=2)}

CONVERSATION LOG SUMMARY:
{chr(10).join([f"{i+1}. {entry[:100]}..." for i, entry in enumerate(self.conversation_log)])}

Generate a professional assessment report that includes:
1. Summary of primary concerns
2. Timeline and onset information
3. Severity assessment
4. Identified triggers and risk factors
5. Impact on daily functioning
6. Recommendations for next steps
7. Safety considerations (if applicable)

Format as a structured report with clear sections.
"""

        try:
            report = self.client.generate(
                prompt=report_prompt,
                system_prompt="You are a professional mental health assessment specialist. Generate clear, compassionate, and clinically relevant reports.",
                max_tokens=1000,
                temperature=0.3
            )
            return report
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self._generate_fallback_report()

    def _generate_fallback_report(self) -> str:
        """Generate a basic fallback report when LLM fails"""
        report_lines = [
            "# Mental Health Assessment Report",
            "",
            "## Patient Information",
            "- Assessment Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "",
            "## Collected Information",
        ]

        for key, value in self.collected_info.items():
            report_lines.append(f"- {key.replace('_', ' ').title()}: {value}")

        report_lines.extend([
            "",
            "## Assessment Status",
            "- Completed Goals: " + ", ".join([k for k, v in self.assessment_goals.items() if v]),
            "- Missing Information: " + ", ".join([k for k, v in self.assessment_goals.items() if not v]),
            "",
            "## Recommendations",
            "- Continue assessment to gather missing information",
            "- Consider follow-up evaluation",
            "",
            "*Note: This is a preliminary assessment. Professional clinical evaluation recommended.*"
        ])

        return chr(10).join(report_lines)

    def complete_workflow(self, initial_patient_input: str = None) -> Dict[str, Any]:
        """
        Complete workflow from welcoming to report generation

        Args:
            initial_patient_input: Optional initial patient message to start with

        Returns:
            Dictionary containing assessment results and report
        """
        logger.info("Starting complete mental health assessment workflow")

        # Initialize workflow state
        workflow_state = {
            'stage': 'welcome',
            'conversation_history': [],
            'assessment_complete': False,
            'safety_intervention_needed': False,
            'report_generated': False
        }

        try:
            # Stage 1: Welcome and initial engagement
            welcome_message = self._generate_welcome_message()
            workflow_state['conversation_history'].append({
                'role': 'assistant',
                'content': welcome_message,
                'timestamp': datetime.now().isoformat()
            })

            # Stage 2: Initial assessment questions
            if initial_patient_input:
                workflow_state['conversation_history'].append({
                    'role': 'user',
                    'content': initial_patient_input,
                    'timestamp': datetime.now().isoformat()
                })

                # Analyze initial input
                analysis = self.analyze_patient_response(initial_patient_input, welcome_message)
                self.update_assessment_status(analysis)

            # Stage 3: Interactive assessment loop
            max_iterations = 10  # Prevent infinite loops
            iteration = 0

            while not self._should_conclude_assessment() and iteration < max_iterations:
                iteration += 1
                logger.info(f"Assessment iteration {iteration}")

                # Generate next question based on current state
                last_analysis = analysis if 'analysis' in locals() else None
                next_question = self.generate_next_question(last_analysis or {})

                workflow_state['conversation_history'].append({
                    'role': 'assistant',
                    'content': next_question,
                    'timestamp': datetime.now().isoformat()
                })

                # In a real implementation, you would wait for patient response here
                # For this simulation, we'll generate a simulated response
                simulated_response = self._simulate_patient_response(next_question, iteration)

                workflow_state['conversation_history'].append({
                    'role': 'user',
                    'content': simulated_response,
                    'timestamp': datetime.now().isoformat()
                })

                # Analyze response
                conversation_context = chr(10).join([
                    msg['content'] for msg in workflow_state['conversation_history'][-5:]  # Last 5 messages
                ])

                analysis = self.analyze_patient_response(simulated_response, conversation_context)
                self.update_assessment_status(analysis)

                # Check for safety concerns
                if analysis.get('safety_flags') in ['immediate', 'moderate']:
                    workflow_state['safety_intervention_needed'] = True
                    logger.warning(f"Safety flag raised: {analysis.get('safety_flags')}")

                # Update workflow state
                workflow_state['stage'] = 'assessment_ongoing'

            # Stage 4: Generate final report
            workflow_state['stage'] = 'report_generation'
            logger.info("Generating assessment report")

            report = self.generate_assessment_report()

            workflow_state['report_generated'] = True
            workflow_state['final_report'] = report
            workflow_state['assessment_complete'] = True
            workflow_state['completion_time'] = datetime.now().isoformat()

            # Stage 5: Generate summary and recommendations
            summary = self._generate_workflow_summary(workflow_state)

            return {
                'success': True,
                'workflow_state': workflow_state,
                'assessment_summary': summary,
                'collected_info': self.collected_info,
                'goals_status': self.assessment_goals,
                'conversation_count': len(workflow_state['conversation_history']),
                'safety_concerns': workflow_state['safety_intervention_needed']
            }

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            workflow_state['error'] = str(e)
            workflow_state['stage'] = 'error'

            return {
                'success': False,
                'error': str(e),
                'workflow_state': workflow_state,
                'partial_info': self.collected_info
            }

    def _generate_welcome_message(self) -> str:
        """Generate personalized welcome message"""
        welcome_prompt = """
Generate a warm, professional welcome message for a mental health assessment chat.
The message should:
1. Introduce yourself as a mental health assessment assistant
2. Explain the purpose of the assessment
3. Assure confidentiality and safety
4. Invite the patient to share what's on their mind
5. Keep it concise but compassionate

Return only the welcome message, no additional text.
"""

        try:
            return self.client.generate(
                prompt=welcome_prompt,
                system_prompt="You are a compassionate mental health professional.",
                max_tokens=200,
                temperature=0.7
            )
        except Exception as e:
            logger.error(f"Welcome message generation failed: {e}")
            return """Hello! I'm here to help you with a mental health assessment. I'm not a replacement for professional therapy, but I can help gather information about how you're feeling. Everything you share here is confidential. What's been on your mind lately that you'd like to talk about?"""

    def _should_conclude_assessment(self) -> bool:
        """Determine if assessment should conclude"""
        progress = self.get_progress()

        # Conclude if most goals are complete or high safety risk
        if progress >= 80:
            return True

        # Check if critical information is missing
        critical_goals = ['primary_concern', 'severity_level']
        critical_missing = any(not self.assessment_goals[goal] for goal in critical_goals)

        return not critical_missing

    def _simulate_patient_response(self, question: str, iteration: int) -> str:
        """Simulate patient response for demonstration purposes"""
        # This is a simulation - in real implementation, this would come from user input
        responses = [
            "I've been feeling really anxious and stressed lately. It's hard to sleep and I feel overwhelmed most days.",
            "This started about 3 weeks ago when I had a big project at work. I used to feel more in control.",
            "I'd say it's about a 7 or 8 on a scale of 1-10. Some days are better than others.",
            "Work deadlines and social situations seem to trigger it the most. I get nervous before meetings.",
            "No, I haven't had thoughts of harming myself, but I do feel very down sometimes.",
            "It's affecting my concentration at work and I'm not enjoying time with friends like I used to."
        ]

        if iteration <= len(responses):
            return responses[iteration - 1]
        else:
            return "I'm not sure what else to say right now. I think that covers the main things."

    def _generate_workflow_summary(self, workflow_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive workflow summary"""
        return {
            'total_messages': len(workflow_state['conversation_history']),
            'assessment_completion': self.get_progress(),
            'goals_completed': [k for k, v in self.assessment_goals.items() if v],
            'goals_missing': [k for k, v in self.assessment_goals.items() if not v],
            'safety_flags': workflow_state.get('safety_intervention_needed', False),
            'report_generated': workflow_state.get('report_generated', False),
            'duration': 'Simulated assessment completed',
            'recommendations': self._generate_recommendations()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate personalized recommendations based on assessment"""
        recommendations = []

        if self.get_progress() < 100:
            recommendations.append("Complete assessment with mental health professional")

        if self.collected_info.get('severity_level', '').lower() in ['severe', '8', '9', '10']:
            recommendations.append("Urgent consultation with mental health professional recommended")

        if self.collected_info.get('suicidal_ideation') == 'yes':
            recommendations.append("Immediate safety assessment required")

        recommendations.extend([
            "Consider stress management techniques",
            "Maintain regular sleep and exercise routine",
            "Connect with trusted friends or family",
            "Schedule follow-up assessment in 1-2 weeks"
        ])

        return recommendations[:5]  # Limit to top 5 recommendations

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            'assessment_progress': self.get_progress(),
            'completed_goals': [k for k, v in self.assessment_goals.items() if v],
            'missing_goals': [k for k, v in self.assessment_goals.items() if not v],
            'collected_info_count': len(self.collected_info),
            'conversation_length': len(self.conversation_log),
            'ready_to_conclude': self._should_conclude_assessment()
        }


# Example usage and testing functions
def demo_assessment_workflow(initial_input: str = None):
    """Demonstrate the complete assessment workflow

    Args:
        initial_input: Optional initial patient input to start the assessment
    """
    try:
        # Initialize client
        client = LLMClient()

        # Create assessment instance
        assessment = MentalHealthAssessment(client)

        # Run complete workflow
        print("🤖 Starting Mental Health Assessment Demo...")
        print("=" * 60)

        if initial_input:
            print(f"Initial patient input: '{initial_input}'")
            print()

        result = assessment.complete_workflow(initial_patient_input=initial_input)

        if result['success']:
            print("\n✅ Assessment completed successfully!")
            print(f"📊 Progress: {result['assessment_summary']['assessment_completion']:.1f}%")
            print(f"🎯 Goals completed: {len(result['assessment_summary']['goals_completed'])}")
            print(f"💬 Total conversation: {result['conversation_count']} messages")

            if result.get('safety_concerns'):
                print("⚠️  Safety concerns were identified during assessment")

            print("\n📋 Final Report Preview:")
            print("-" * 40)
            report_preview = result['workflow_state']['final_report'][:400] + "..."
            print(report_preview)

            # Show recommendations
            if result['assessment_summary'].get('recommendations'):
                print("\n💡 Recommendations:")
                for i, rec in enumerate(result['assessment_summary']['recommendations'][:3], 1):
                    print(f"   {i}. {rec}")

        else:
            print(f"\n❌ Assessment failed: {result['error']}")

        return result

    except Exception as e:
        print(f"Demo failed: {e}")
        return None


def interactive_assessment_demo():
    """Interactive demo that shows step-by-step workflow"""
    try:
        client = LLMClient()
        assessment = MentalHealthAssessment(client)

        print("🔄 Interactive Mental Health Assessment")
        print("=" * 50)
        print("This demo shows the complete workflow step by step.")
        print()

        # Show initial status
        status = assessment.get_workflow_status()
        print(f"Initial progress: {status['assessment_progress']:.1f}%")
        print(f"Goals to complete: {status['missing_goals']}")
        print()

        # Run workflow
        result = assessment.complete_workflow()

        if result['success']:
            print("\n✅ Workflow completed!")
            print("\n📈 Final Statistics:")
            print(f"   • Total messages: {result['conversation_count']}")
            print(f"   • Goals completed: {len(result['assessment_summary']['goals_completed'])}")
            print(f"   • Safety concerns: {'Yes' if result['safety_concerns'] else 'None'}")

            print("\n📝 Conversation Flow:")
            for i, msg in enumerate(result['workflow_state']['conversation_history'], 1):
                role = "🤖 Assistant" if msg['role'] == 'assistant' else "👤 User"
                print(f"   {i}. {role}: {msg['content'][:80]}...")

        return result

    except Exception as e:
        print(f"Interactive demo failed: {e}")
        return None


if __name__ == "__main__":
    # Run demo when script is executed directly
    import sys

    if len(sys.argv) > 1:
        initial_input = " ".join(sys.argv[1:])
        print(f"Running with custom input: {initial_input}")
        demo_result = demo_assessment_workflow(initial_input)
    else:
        demo_result = demo_assessment_workflow()

    if demo_result and demo_result['success']:
        print("\n" + "=" * 60)
        print("🎉 Demo completed successfully!")
        print("\n🔍 The complete_workflow() method includes:")
        print("   1. 🤝 Welcome message generation")
        print("   2. 🔄 Interactive assessment questions")
        print("   3. 🧠 Response analysis and goal tracking")
        print("   4. 🛡️  Safety monitoring")
        print("   5. 📋 Comprehensive report generation")
        print("   6. 💡 Personalized recommendations")
        print("\n💡 Usage Tips:")
        print("   • Call complete_workflow() to run the full assessment")
        print("   • Use get_workflow_status() to check progress")
        print("   • Access collected_info for gathered data")
        print("   • Check goals_status for completion tracking")
        print("=" * 60)
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
            self.model = os.getenv("GROQ_MODEL")
        else:
            self.model = model
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initialize components
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
        self.request_queue = RequestQueue(max_requests_per_minute=6, max_concurrent=1)  # Very conservative
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
        return context_limits.get(self.model, 8192)  # Default to 8192
    
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
    
    def generate_multiple(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        max_tokens: int = 600,
        temperature: float = 0.7,
        batch_delay: float = 5.0,
        **kwargs
    ) -> List[str]:
        """Generate responses for multiple prompts with batch processing"""
        responses = []
        
        for i, prompt in enumerate(prompts):
            try:
                if i > 0:
                    logger.info(f"Batch delay: {batch_delay}s before request {i + 1}/{len(prompts)}")
                    time.sleep(batch_delay)
                
                logger.info(f"Processing batch request {i + 1}/{len(prompts)}")
                response = self.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                responses.append(response)
                
            except Exception as e:
                logger.error(f"Batch request {i + 1} failed: {e}")
                responses.append(f"Error in batch request {i + 1}: {str(e)[:100]}")
        
        return responses
    
    def get_available_models(self) -> List[str]:
        """Get list of available models with caching"""
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            response.raise_for_status()
            models = response.json()
            return [model['id'] for model in models.get('data', [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return ["mixtral-8x7b-32768", "llama2-70b-4096"]  # Fallback list
    
    def set_model(self, model: str) -> bool:
        """Change the model with validation"""
        available_models = self.get_available_models()
        
        if model in available_models:
            old_model = self.model
            self.model = model
            self.max_context_length = self._get_model_context_limit()
            logger.info(f"Model changed from {old_model} to {model}")
            return True
        else:
            logger.error(f"Model {model} not available. Available: {available_models[:5]}...")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "model": self.model,
            "max_context_length": self.max_context_length,
            "circuit_breaker_state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "active_requests": self.request_queue.active_requests,
            "cache_size": len(self.cache.cache) if self.cache else 0
        }


class AgentLLMClient(LLMClient):
    """
    Agent-specific LLM client with enhanced conversation management generate_with_history
    """ 
    
    def __init__(self, agent_name: str, system_prompt: str = None, **kwargs):
        """Initialize agent-specific client"""
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.conversation_history: List[Message] = []
        self.max_history_tokens = 4000  # Limit conversation history size
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


# Usage example
if __name__ == "__main__":
    try:
        # Will use GROQ_MODEL from .env if available, otherwise defaults to qwen/qwen-2.5-72b-instruct
        # client = LLMClient(enable_cache=True)
        
        client = LLMClient(model="llama3-8b-8192", enable_cache=True)
        
        print(f"Using model: {client.model}")
        
        # Test basic generation
        response = client.generate("What is the capital of France? reply in JSOn format. in this format  {\"answer\": \"\"}   ",)
        print("Response:", response)
        
        #Expected response format:
# INFO:__main__:Connected to Groq API successfully. Using model: qwen/qwen3-32b
# Using model: qwen/qwen3-32b
# Response: <think>
# Okay, so I need to figure out the capital of France. Let me start by recalling what I know. France is a country in Europe, right? I remember from school that the capital of France is Paris. Wait, is that correct? Let me think. I've heard Paris mentioned a lot in the context of France. There's the Eiffel Tower there, the Louvre Museum, and it's a major city. But maybe I should verify this.
# I think the capital is the city where the government is located. For France, the president and the government would be in the capital. I've heard of the French president holding meetings in Paris. Also, when I watch the news, they often mention Paris as the capital. But maybe there's another city? I'm not sure. Let me try to recall other cities in France. There's Lyon, Marseille, Bordeaux, Nice... none of these seem like capitals. Lyon is a big city, but I don't think it's the capital. Marseille is a port city. Bordeaux is known for wine. So Paris is the most likely answer.

# Wait, but I should check if there's any confusion with other countries. For example, sometimes people mix up countries. The capital of Germany is Berlin, the UK is London, Spain is Madrid. So France's capital being Paris fits with that pattern. Also, in movies and books, Paris is often referred to as the capital. Maybe I can think of some historical context. The French Revolution took place in Paris, right? The city has a lot of historical significance. The Palace of Versailles is just outside Paris, which was the seat of the French monarchy. So that supports Paris being the capital.

# Another angle: when you look at a map of France, Paris is centrally located in the north-central part of the country. That makes sense for a capital because it's a central location. Also, Paris is a major economic and cultural hub. It's one of the most visited cities in the world. So all these points lead me to believe that Paris is indeed the capital of France. I don't think I've ever heard any other city being mentioned as the capital, so I think that's the correct answer.
# </think>

# The capital of France is **Paris**. 

# Paris is not only the political and administrative center of France but also a global hub for art, culture, fashion, and gastronomy. Key landmarks such as the Eiffel Tower, the Louvre Museum, and the Palace of Versailles (located just outside Paris) underscore its historical and cultural significance. The city has been the capital since the 10th century and remains the seat of the French government, housing institutions like the Élysée Palace (residence of the President) and the National Assembly. 

# **Answer:** Paris, France.
        
        # # Test chat with history
        # agent_client = AgentLLMClient(agent_name="TestAgent", system_prompt="You are a helpful assistant.")
        # response = agent_client.generate_with_history("Hello, who are you?")
        # print("Agent Response 1:", response)
        
        # response2 = agent_client.generate_with_history("What can you do?")
        # print("Agent Response 2:", response2)
        
        # # Get stats
        # stats = client.get_stats()
        # print("Client Stats:", stats)
        
        # agent_stats = agent_client.get_history_summary()
        # print("Agent History Summary:", agent_stats)
        
        # # Test model change
        # available_models = client.get_available_models()
        # print("Available Models:", available_models[:3])
        
        # # Try to use qwen/qwen3-32b if not already using it
        # if client.model != "qwen/qwen3-32b" and "qwen/qwen3-32b" in available_models:
        #     if client.set_model("qwen/qwen3-32b"):
        #         print(f"Model changed successfully to {client.model}")
        #     else:
        #         print("Failed to change model")
        
        # # Generate multiple responses
        # prompts = ["What is AI?", "Explain quantum computing.", "What is the meaning of life?"]
        # batch_responses = client.generate_multiple(prompts, system_prompt="You are an expert in science.")
        # print("Batch Responses:", len(batch_responses), "responses generated")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error: {e}")
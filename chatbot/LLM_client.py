import requests
import os
import json
import time
import logging
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Represents a chat message"""
    role: str  # "system", "user", "assistant"
    content: str

class ChatbotLLMClient:
    """
    Simplified LLM client for the MindMate chatbot system.
    Handles GROQ API interactions with LLaMA models.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the chatbot LLM client.
        
        Args:
            model: The model to use (if None, will use GROQ_MODEL from .env or default)
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
        
        # Verify connection
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """Verify API connection"""
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            response.raise_for_status()
            
            models = response.json()
            available_models = [model['id'] for model in models.get('data', [])]
            
            if self.model not in available_models:
                logger.warning(f"Model {self.model} not found in available models.")
                logger.info(f"Available models: {available_models}")
                
                # Try to find a suitable alternative
                llama_alternatives = [m for m in available_models if 'llama' in m.lower()]
                qwen_alternatives = [m for m in available_models if 'qwen' in m.lower()]
                
                if llama_alternatives:
                    self.model = llama_alternatives[0]
                    logger.info(f"Switched to Llama alternative: {self.model}")
                elif qwen_alternatives:
                    self.model = qwen_alternatives[0]
                    logger.info(f"Switched to Qwen alternative: {self.model}")
                elif available_models:
                    self.model = available_models[0]
                    logger.info(f"Switched to first available model: {self.model}")
                else:
                    raise ValueError("No models available from API")
            
            logger.info(f"Connected to Groq API successfully. Using model: {self.model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Groq API: {e}")
            raise
    
    def generate_response(
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
                # Prepare payload
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": False,
                    **kwargs
                }
                
                # Make request
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract response
                if 'choices' not in result or not result['choices']:
                    raise ValueError("No response choices returned from API")
                
                response_text = result['choices'][0]['message']['content']
                return response_text
                
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                if "429" in str(e) or "rate limit" in error_str:
                    wait_time = (attempt + 1) * 30 + 60  # Longer waits for rate limits
                    logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
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
            # Prepare payload
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
                **kwargs
            }
            
            # Make request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response
            if 'choices' not in result or not result['choices']:
                raise ValueError("No response choices returned from API")
            
            response_text = result['choices'][0]['message']['content']
            return response_text
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return f"Error: Chat generation failed due to API limitations."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            response.raise_for_status()
            models = response.json()
            return [model['id'] for model in models.get('data', [])]
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return ["llama3-8b-8192", "qwen/qwen3-32b"]  # Fallback list
    
    def set_model(self, model: str) -> bool:
        """Change the model with validation"""
        available_models = self.get_available_models()
        
        if model in available_models:
            old_model = self.model
            self.model = model
            logger.info(f"Model changed from {old_model} to {model}")
            return True
        else:
            logger.error(f"Model {model} not available. Available: {available_models[:5]}...")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "model": self.model,
            "api_connected": True,
            "base_url": self.base_url
        }

from openai import OpenAI
from enum import Enum
import os
import re
import logging
import time
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import json

load_dotenv()

# Configure logging for this module
logger = logging.getLogger(__name__)

class ModelType(Enum):
    LOCAL_LM_STUDIO = "local_lm_studio"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class LLMClient:
    def __init__(self, model_type: ModelType, evaluator_client=None, **kwargs):
        self.model_type = model_type
        
        # Use environment variables with fallbacks
        default_base_url = 'http://localhost:1234/v1'
        
        # Check for Docker environment and use host.docker.internal
        if os.path.exists('/.dockerenv'):
            default_base_url = 'http://host.docker.internal:1234/v1'
            logger.info("Detected Docker environment, using host.docker.internal")
        
        self.base_url = kwargs.get('base_url', os.getenv('LLM_BASE_URL', default_base_url))
        self.api_key = kwargs.get('api_key', os.getenv('LLM_API_KEY', 'not-needed-for-local'))
        self.model_name = kwargs.get('model_name', os.getenv('LLM_MODEL_NAME', 'deepseek/deepseek-r1-0528-qwen3-8b'))
        
        # Option to skip connection test (useful for development)
        self.skip_connection_test = os.getenv('SKIP_LLM_CONNECTION_TEST', 'false').lower() == 'true'
        
        logger.info(f"Initializing LLMClient with model_type: {model_type.value}")
        logger.debug(f"Configuration - base_url: {self.base_url}, model_name: {self.model_name}")
        logger.debug(f"Skip connection test: {self.skip_connection_test}")
        
        if model_type == ModelType.LOCAL_LM_STUDIO:
            try:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                logger.info("Successfully initialized LOCAL_LM_STUDIO client")
                
                # Test the connection (unless skipped)
                if not self.skip_connection_test:
                    self._test_connection()
                else:
                    logger.info("Skipping connection test as requested")
                
            except Exception as e:
                logger.error(f"Failed to initialize LOCAL_LM_STUDIO client: {str(e)}", exc_info=True)
                raise
        elif model_type == ModelType.OPENAI:
            # TODO: Implement OpenAI client
            logger.warning("OpenAI client requested but not implemented yet")
            raise NotImplementedError("OpenAI client not implemented yet")
        elif model_type == ModelType.ANTHROPIC:
            # TODO: Implement Anthropic client
            logger.warning("Anthropic client requested but not implemented yet")
            raise NotImplementedError("Anthropic client not implemented yet")
        elif model_type == ModelType.GEMINI:
            # TODO: Implement Gemini client
            logger.warning("Gemini client requested but not implemented yet")
            raise NotImplementedError("Gemini client not implemented yet")
    
    def _test_connection(self):
        """Test the connection to the LLM service."""
        try:
            logger.info("Testing connection to LLM service...")
            
            if self.model_type == ModelType.LOCAL_LM_STUDIO:
                # First test with a simple HTTP request to check if server is reachable
                models_url = f"{self.base_url}/models"
                logger.debug(f"Testing connection to: {models_url}")
                
                response = requests.get(models_url, timeout=10)
                response.raise_for_status()
                
                models_data = response.json()
                available_models = [model['id'] for model in models_data.get('data', [])]
                logger.info(f"Available models: {available_models}")
                
                # Check if our configured model is available
                if self.model_name not in available_models:
                    logger.warning(f"Configured model '{self.model_name}' not found in available models: {available_models}")
                    logger.warning("This may cause issues during chat completion")
                else:
                    logger.info(f"Configured model '{self.model_name}' is available")
                
                # Test with a simple OpenAI client call
                logger.debug("Testing OpenAI client with a simple call...")
                models_response = self.client.models.list()
                logger.info("OpenAI client connection test successful")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP connection test failed: {str(e)}")
            logger.error(f"Cannot reach LLM service at {self.base_url}")
            logger.error("Possible solutions:")
            logger.error("1. Ensure LM Studio is running and accessible")
            logger.error("2. If running in Docker, set LLM_BASE_URL=http://host.docker.internal:1234/v1")
            logger.error("3. Set SKIP_LLM_CONNECTION_TEST=true to skip this test")
            raise ConnectionError(f"Cannot reach LLM service at {self.base_url}: {str(e)}")
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            raise
    
    def chat_completion_json(self, messages: List[Dict[str, str]], temperature: float = 0.0, 
                           response_schema: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a chat completion and extract JSON from the response.
        Handles model-specific quirks like DeepSeek R1 thinking tags.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            response_schema: Optional schema for structured output (not used for local models)
            
        Returns:
            Extracted JSON string
        """
        start_time = time.time()
        logger.info(f"Starting chat completion with {self.model_type.value}")
        logger.debug(f"Parameters - temperature: {temperature}, messages count: {len(messages)}")
        
        # Log message details (truncated for readability)
        for i, msg in enumerate(messages):
            content_preview = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            logger.debug(f"Message {i} ({msg['role']}): {content_preview}")
        
        try:
            if self.model_type == ModelType.LOCAL_LM_STUDIO:
                logger.info(f"Sending request to LOCAL_LM_STUDIO model: {self.model_name}")
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature
                )
                
                request_time = time.time() - start_time
                logger.info(f"Received response from LOCAL_LM_STUDIO in {request_time:.2f}s")
                
                content = response.choices[0].message.content
                logger.debug(f"Raw response length: {len(content)} characters")
                logger.debug(f"Raw response preview: {content[:500]}...")
                
                # Remove "thinking" tags and their content (e.g., <think> ... </think>)
                cleaned_content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE)
                return cleaned_content
                # Iterate through brace blocks and return the first valid JSON
                json_candidate = None
                for match in re.finditer(r'\{[\s\S]*?\}', cleaned_content):
                    candidate = match.group(0)
                    try:
                        json.loads(candidate)
                        json_candidate = candidate
                        break
                    except Exception:
                        continue

                if json_candidate:
                    logger.info("Successfully extracted JSON from response")
                    logger.debug(f"Extracted JSON length: {len(json_candidate)} characters")
                    logger.debug(f"Extracted JSON preview: {json_candidate[:300]}...")

                    total_time = time.time() - start_time
                    logger.info(f"Chat completion completed successfully in {total_time:.2f}s")
                    return json_candidate
                else:
                    logger.warning("No JSON found in response, returning full content")
                    logger.debug(f"Full content: {content}")
                    total_time = time.time() - start_time
                    logger.info(f"Chat completion completed (fallback) in {total_time:.2f}s")
                    return content
                    
            else:
                # For other model types, implement their specific logic
                logger.error(f"Chat completion not implemented for {self.model_type.value}")
                raise NotImplementedError(f"Chat completion not implemented for {self.model_type}")
                
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"Error during chat completion after {error_time:.2f}s: {str(e)}", exc_info=True)
            
            # Provide more specific error messages
            if "Connection error" in str(e) or "ConnectTimeout" in str(e):
                logger.error(f"Cannot connect to LLM service at {self.base_url}")
                logger.error("Please ensure LM Studio is running and accessible")
                logger.error("If running in Docker, check the LLM_BASE_URL configuration")
            
            raise
from enum import Enum
import os
import re
import logging
import time
import httpx
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# Configure logging for this module
logger = logging.getLogger(__name__)

class ModelType(Enum):
    LOCAL_LM_STUDIO = "local_lm_studio"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"

class LLMClient:
    def __init__(self, model_type: ModelType, **kwargs):
        self.model_type = model_type

        # Determine default base URL based on model type
        if model_type == ModelType.OPENROUTER:
            default_base_url = 'https://openrouter.ai/api/v1'
        else:
            default_base_url = 'http://localhost:1234/v1'
            if os.path.exists('/.dockerenv'):
                default_base_url = 'http://host.docker.internal:1234/v1'
                logger.info("Detected Docker environment, using host.docker.internal")

        self.base_url = kwargs.get('base_url', os.getenv('LLM_BASE_URL', default_base_url))
        self.api_key = kwargs.get('api_key', os.getenv('API_KEY', 'not-needed-for-local'))
        self.model_name = kwargs.get('model_name', os.getenv('LLM_MODEL_NAME', 'moonshotai/kimi-k2'))
        self.skip_connection_test = os.getenv('SKIP_LLM_CONNECTION_TEST', 'false').lower() == 'true'

        logger.info(f"Initializing LLMClient with model_type: {model_type.value}")

        if model_type == ModelType.LOCAL_LM_STUDIO:
            self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
            logger.info("Successfully initialized LOCAL_LM_STUDIO async client")
        elif model_type == ModelType.OPENROUTER:
            self.client = AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
            logger.info("Successfully initialized OPENROUTER async client")
        else:
            raise NotImplementedError(f"{model_type.value} client not implemented yet")

    async def test_connection(self):
        """Test the connection to the LLM service."""
        if self.skip_connection_test:
            logger.info("Skipping connection test as requested")
            return

        logger.info("Testing connection to LLM service...")
        try:
            # The OpenAI client now has the default headers, so we can use it directly
            # for a more reliable connection test.
            await self.client.models.list()
            logger.info("OpenAI async client connection test successful")

        except httpx.RequestError as e:
            logger.error(f"HTTP connection test failed: {str(e)}")
            raise ConnectionError(f"Cannot reach LLM service at {self.base_url}: {str(e)}")
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            raise

    async def chat_completion_json(self, messages: List[Dict[str, str]], temperature: float = 0.0,
                           response_schema: Optional[Dict[str, Any]] = None) -> str:
        start_time = time.time()
        logger.info(f"Starting chat completion with {self.model_type.value}")
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            if response.choices is None:
                logger.error(f"No choices in response: {response}")
                raise ValueError("No choices returned from the model")
            content = response.choices[0].message.content
            logger.info(f"Raw response content: {content}")  # Log raw content for debugging
            # Remove ```json and ``` if present
            if content.strip().startswith('```json'):
                content = content.strip()[7:]
            if content.strip().startswith('```'):
                content = content.strip()[3:]
            if content.strip().endswith('```'):
                content = content.strip()[:-3]
            cleaned_content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()

            total_time = time.time() - start_time
            logger.info(f"Chat completion completed successfully in {total_time:.2f}s")
            return cleaned_content
        except Exception as e:
            logger.error(f"Error during chat completion: {str(e)}", exc_info=True)
            raise

import asyncio
from services.client import LLMClient, ModelType
from services.prompt_builder import PromptBuilder
from settings import settings  # <-- new import

llm_client_instance: LLMClient = None
client_init_lock = asyncio.Lock()

async def get_llm_client() -> LLMClient:
    """
    Dependency injector for the LLMClient.
    
    Uses an async lock to ensure the client is initialized only once.
    """
    global llm_client_instance
    if llm_client_instance is None:
        async with client_init_lock:
            if llm_client_instance is None:
                # Determine model type from settings
                provider_name = settings.llm_provider.lower()
                provider_map = {
                    "local_lm_studio": ModelType.LOCAL_LM_STUDIO,
                    "openrouter": ModelType.OPENROUTER,
                    "openai": ModelType.OPENAI,
                    "anthropic": ModelType.ANTHROPIC,
                    "gemini": ModelType.GEMINI,
                }
                model_type = provider_map.get(provider_name, ModelType.LOCAL_LM_STUDIO)

                client = LLMClient(model_type)
                llm_client_instance = client
    return llm_client_instance

def get_prompt_builder() -> PromptBuilder:
    """Dependency injector for the PromptBuilder."""
    return PromptBuilder()

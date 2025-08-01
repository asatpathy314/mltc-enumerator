import asyncio
from services.client import LLMClient, ModelType
from services.prompt_builder import PromptBuilder, ModularQuestionGenerator
from services.threat_generator import ThreatChainGenerator
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

def get_modular_question_generator() -> ModularQuestionGenerator:
    """Dependency injector for the ModularQuestionGenerator."""
    prompt_builder = get_prompt_builder()
    return ModularQuestionGenerator(prompt_builder)

async def get_threat_generator() -> ThreatChainGenerator:
    """Dependency injector for the ThreatChainGenerator."""
    llm_client = await get_llm_client()
    return ThreatChainGenerator(llm_client)

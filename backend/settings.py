from pydantic_settings import BaseSettings
from typing import List
import logging

class Settings(BaseSettings):
    """
    Centralized application configuration.
    
    All values are loaded from environment variables or a .env file.
    """
    # FastAPI settings
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ]
    
    # Logging configuration
    log_level: str = "DEBUG"
    log_file: str = "mltc_api.log"

    # LLM configuration
    llm_provider: str = "openrouter"  # Options: local_lm_studio, openrouter, openai, anthropic, gemini
    llm_base_url: str | None = None  # Optional explicit override of the base URL used to reach the provider

    class Config:
        env_file = ".env"

# Instantiate settings
settings = Settings()

# Configure logging based on settings
def setup_logging():
    """Set up the root logger based on the application settings."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.log_file)
        ]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

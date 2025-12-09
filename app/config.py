from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    APP_PG_HOST: str = "host.docker.internal"
    APP_PG_USER: str = "postgres"
    APP_PG_PASSWORD: str = "postgres"
    APP_PG_DATABASE: str = "ultimate_advisor"
    APP_PG_PORT: int = 5432
    
    # Ollama Configuration
    OLLAMA_HOST: str = "http://host.docker.internal:11434"
    APP_CHAT_MODEL: str = "llama3.2:3b"
    APP_EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    
    # AI Studio API Key (for Gemini if needed)
    AI_STUDIO_API_KEY: Optional[str] = None
    
    # RAG Configuration
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"

settings = Settings()
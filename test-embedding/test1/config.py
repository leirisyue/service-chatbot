import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_EMBED_MODEL = os.getenv(
        "GEMINI_EMBED_MODEL",
        "models/text-embedding-004"
    )

    # Qwen
    QWEN_EMBED_MODEL = os.getenv(
        "QWEN_EMBED_MODEL",
        "qwen3-embedding:latest"
    )

settings = Settings()

from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar, Dict

load_dotenv()

class Settings(BaseSettings):
    My_GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"

    DB_CONFIG: ClassVar[Dict[str, str]] = {
        "dbname": "db_vector",
        "user": "postgres",
        "password": "postgres",
        "host": "localhost",
        "port": "5432"
    }

settings = Settings()
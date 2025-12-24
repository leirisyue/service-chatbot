from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar, Dict

load_dotenv()

class Settings(BaseSettings):
    My_GOOGLE_API_KEY: str
    
    # Database settings
    DB_NAME: str = "db_vector"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    class Config:
        env_file = ".env"

    @property
    def DB_CONFIG(self) -> Dict[str, str]:
        """Get database configuration as dict"""
        return {
            "dbname": self.DB_NAME,
            "user": self.DB_USER,
            "password": self.DB_PASSWORD,
            "host": self.DB_HOST,
            "port": self.DB_PORT
        }

settings = Settings()
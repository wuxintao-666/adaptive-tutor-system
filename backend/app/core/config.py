# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Settings(BaseSettings):
        """
        Loads all application settings from environment variables or a .env file.
        The validation is handled by Pydantic.
        """
        # Server
        BACKEND_PORT: int = 8000

        # OpenAI
        OPENAI_API_KEY: str
        OPENAI_MODEL: str = "gpt-4-turbo"
        OPENAI_API_BASE: str = "https://api.openai.com/v1"
  
        # Embedding
        EMBEDDING_MODEL: str = "text-embedding-3-small"

        # Database
        DATABASE_URL: str = "sqlite:///./learning_data.db"

        # Model configuration tells Pydantic where to find the .env file.
        # It will search from the current working directory upwards.
        model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

# Create a single, globally accessible instance of the settings.
# This will raise a validation error on startup if required settings are missing.
settings = Settings()

# Database setup
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models to ensure they are registered with the Base
from .models import Base, UserKnowledge, Tag, UserTime

# Create tables
Base.metadata.create_all(bind=engine)
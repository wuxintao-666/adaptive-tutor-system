from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import List

class Settings(BaseSettings):
    """
    Loads all application settings from environment variables or a .env file.
    The validation is handled by Pydantic.
    """
    # Server
    BACKEND_PORT: int = 8000

    # OpenAI (for chat completions)
    TUTOR_OPENAI_API_KEY: str
    TUTOR_OPENAI_MODEL: str = "gpt-4-turbo"
    TUTOR_OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Embedding API (can be different from OpenAI)
    TUTOR_EMBEDDING_API_KEY: str
    TUTOR_EMBEDDING_API_BASE: str = "https://ms-fc-1d889e1e-d2ad.api-inference.modelscope.cn/v1"
    TUTOR_EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-4B-GGUF"

    # Model configuration tells Pydantic where to find the .env file.
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra='ignore',
        case_sensitive=True
    )

    PROJECT_NAME: str = "Adaptive Tutor System"
    API_V1_STR: str = "/api/v1"

    # TODO: 到时候可能需要约束，不能放所有都进来
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    DATABASE_URL: str = "sqlite:///./database.db"
    
    # File paths
    DATA_DIR: str = "./backend/data"
    DOCUMENTS_DIR: str = "./backend/data/documents"
    VECTOR_STORE_DIR: str = "./backend/data/vector_store"
    KB_ANN_FILENAME: str = "kb.ann"
    KB_CHUNKS_FILENAME: str = "kb_chunks.json"

# Create a single, globally accessible instance of the settings.
# This will raise a validation error on startup if required settings are missing.
settings = Settings()
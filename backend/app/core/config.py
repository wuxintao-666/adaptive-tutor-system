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

    # OpenAI配置 (用于聊天完成)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    
    # 魔搭配置
    MODELSCOPE_API_KEY: str = ""
    MODELSCOPE_API_BASE: str = "https://api-inference.modelscope.cn/v1"
    MODELSCOPE_MODEL: str = "qwen-turbo"
    
    # 嵌入模型配置 (可以与OpenAI不同)
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_API_BASE: str = "https://ms-fc-1d889e1e-d2ad.api-inference.modelscope.cn/v1"
    EMBEDDING_MODEL: str = "Qwen/Qwen3-Embedding-4B-GGUF"
    
    # LLM服务选择 (openai 或 modelscope)
    LLM_PROVIDER: str = "modelscope"

    # Model configuration tells Pydantic where to find the .env file.
    # It will search from the current working directory upwards.
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env", "../../.env"],  # 尝试多个路径
        env_file_encoding='utf-8', 
        extra='ignore',
        case_sensitive=True
    )

    PROJECT_NAME: str = "Adaptive Tutor System"
    API_V1_STR: str = "/api/v1"

    # TODO: 到时候可能需要约束，不能放所有都进来
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    DATABASE_URL: str = "sqlite:///./database.db"

# Create a single, globally accessible instance of the settings.
# This will raise a validation error on startup if required settings are missing.
settings = Settings()
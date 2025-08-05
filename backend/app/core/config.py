from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import List, Dict, Any

class Settings(BaseSettings):
    """
    Loads all application settings from environment variables or a .env file.
    The validation is handled by Pydantic.
    """
    # Server
    BACKEND_PORT: int = 8000

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # Embedding
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # ModelScope
    MODELSCOPE_API_KEY: str = ""

    # Model configuration tells Pydantic where to find the .env file.
    # It will search from the current working directory upwards.
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
    
    # RAG基础路径配置 (从环境变量读取，符合TDD要求)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = None  # 将从环境变量或默认值获取
    DOCUMENTS_DIR: str = None  # 将从环境变量或默认值获取
    VECTOR_STORE_DIR: str = None  # 将从环境变量或默认值获取
    
    # RAG配置 (从环境变量读取，符合TDD要求)
    RAG_CONFIG: Dict[str, Any] = {
        # 向量存储配置
        "vector_store": {
            "index_file": "kb.ann",
            "chunks_file": "kb_chunks.json"
        },
        
        # 检索器配置
        "retriever": {
            "top_k": 3
        }
    }
    
    @property
    def _data_dir(self) -> str:
        """获取数据目录路径"""
        return os.environ.get("DATA_DIR", os.path.join(self.BASE_DIR, 'data'))
    
    @property
    def _documents_dir(self) -> str:
        """获取文档目录路径"""
        return os.environ.get("DOCUMENTS_DIR", os.path.join(self._data_dir, 'test_tasks'))
    
    @property
    def _vector_store_dir(self) -> str:
        """获取向量存储目录路径"""
        return os.environ.get("VECTOR_STORE_DIR", os.path.join(self._data_dir, 'vector_store'))

# Create a single, globally accessible instance of the settings.
# This will raise a validation error on startup if required settings are missing.
settings = Settings()
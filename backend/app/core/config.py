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

    # OpenAI / ModelScope
    # 这些值将从 .env 文件中加载
    OPENAI_API_KEY: str
    OPENAI_MODEL: str
    OPENAI_API_BASE: str
    EMBEDDING_MODEL: str
    MODELSCOPE_API_KEY: str = "" # 可选

    # Model configuration tells Pydantic where to find the .env file.
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra='ignore',
        case_sensitive=False # 改为不区分大小写，提高灵活性
    )

    PROJECT_NAME: str = "Adaptive Tutor System"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    DATABASE_URL: str = "sqlite:///./database.db"
    
    # RAG配置
    RAG_CONFIG: Dict[str, Any] = {
        "vector_store": {
            "index_file": "kb.ann",
            "chunks_file": "kb_chunks.json"
        },
        "retriever": {
            "top_k": 3
        }
    }
    
    @property
    def BASE_DIR(self) -> str:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @property
    def DATA_DIR(self) -> str:
        return os.environ.get("DATA_DIR", os.path.join(self.BASE_DIR, 'data'))
    
    @property
    def DOCUMENTS_DIR(self) -> str:
        return os.environ.get("DOCUMENTS_DIR", os.path.join(self.DATA_DIR, 'documents'))
    
    @property
    def VECTOR_STORE_DIR(self) -> str:
        return os.environ.get("VECTOR_STORE_DIR", os.path.join(self.DATA_DIR, 'vector_store'))

settings = Settings()
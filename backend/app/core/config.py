from pydantic_settings import BaseSettings, SettingsConfigDict 
from pydantic import AnyHttpUrl
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

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    DATABASE_URL: str = "sqlite:///./database.db"
    
    
    
    # 服务调用配置
    SERVICE_CONFIG: Dict[str, Any] = {
        "ollama_host": "http://localhost:11434",  # Ollama服务地址
        "embedding_timeout": 60,   # 嵌入生成超时时间（秒）
        "rerank_timeout": 120,     # 重排序超时时间（秒）
        "modelscope_base_url": "https://api-inference.modelscope.cn/v1/",  # ModelScope API基础URL
    }
    # RAG基础路径配置
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, 'data')
    DOCUMENTS_DIR: str = os.path.join(DATA_DIR, 'test_tasks')
    VECTOR_STORE_DIR: str = os.path.join(DATA_DIR, 'vector_store')
    
    # RAG配置（AI组件）
    RAG_CONFIG: Dict[str, Any] = {
        # 文档加载配置
        "document_loader": {
            "extensions": [".txt", ".pdf", ".docx", ".pptx", ".md", ".json", ".csv"]
        },
        
        # 文本分割配置 
        "text_splitter": {
            "chunk_size": 1500, 
            "chunk_overlap": 100  
        },
        
        # 嵌入模型配置 
        "embeddings": {
            "model_type": "ollama",  # ollama 或 huggingface 或 modelscope
            "model_name": "all-minilm", #ollama/all-minilm  modelscope/text-embedding-v1
            "dim": 384,             # 嵌入维度  ollama/384   modelscope/1024
            "batch_size": 32,        # 批量处理大小
            "modelscope": {
                "model": "text-embedding-v1",  # 默认嵌入模型
            }
        },
        
        # 向量存储配置
        "vector_store": {
            "type": "annoy",  
            "index_name": "document_index",
            "distance_metric": "angular",  # 距离度量方法
            "build_trees": 10              # Annoy索引树数量
        },
        
        # 检索器配置
        "retriever": {
            "top_k": 20,              # 检索返回的文档数量
            "score_threshold": 0.3,   # 相似度分数阈值
            "enable_rerank": False     # 是否默认启用重排序
        },
        
        # 摘要生成配置
        "summarizer": {
            "model_type": "modelscope",    # ollama 或 modelscope
            "ollama_model_name": "qwen:7b",   # Ollama模型名称
            "modelscope_model_name": "Qwen/Qwen2.5-7B-Instruct",  # ModelScope模型名称
            "max_summary_length": 15   # 摘要最大长度（字数）
        },
        
        # 修改后的重排序配置 - 二元组格式
        "reranker": {
            "enable": True,           # 是否启用重排序
            "model_type": "modelscope",    # ollama 或 modelscope
            "ollama_model_name": "qwen:7b",   # Ollama重排序模型
            "modelscope_model_name": "Qwen/Qwen2.5-7B-Instruct",  # ModelScope模型名称
            "top_n_for_rerank": 20,    # 参与重排序的文档数量
            "score_threshold": 0.3,    # 相关性阈值
            "prompt_template": (
                    "仅根据问题：'{query}'，对下列摘要按你认为与问题的相关性进行打分，认为不相关的不加入数组。\n"
                    "只返回一个JSON数组，格式为[[索引, 分数], [索引, 分数], ...]，对应什么摘要不用输出，按分数降序排列。\n"
                    "你是API不能输出任何解释、注释、说明、自然语言也不要对你的输出做任何的解释，只输出JSON数组本身，否则我手上的这只猫就会被我掐死。\n"
                    "摘要列表：\n{summaries}"
                )
        }
    }

# Create a single, globally accessible instance of the settings.
# This will raise a validation error on startup if required settings are missing.
settings = Settings()
import requests
import numpy as np
from typing import List
from core.config import RAG_CONFIG
import logging
import time
import os

# 添加openai库导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Install with 'pip install openai' for ModelScope support.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self):
        """
        @brief 初始化嵌入模型
        """
        config = RAG_CONFIG["embeddings"]
        self.model_type = config["model_type"]
        self.model_name = config["model_name"]
        self.dim = config.get("dim", 384)
        self.api_url = "http://localhost:11434/api/embeddings"
        self.modelscope_config = config.get("modelscope", {})
        self.modelscope_model = self.modelscope_config.get("model", "text-embedding-v1")
        self.modelscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.modelscope_base_url = "https://api-inference.modelscope.cn/v1/"
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        @brief 根据配置的模型类型，使用相应的方法将输入文本转换为向量表示
        
        @param texts (List[str]): 需要转换为向量的文本列表
        
        @return List[List[float]]: 对应的向量表示列表，每个向量是一个浮点数列表
        """
        if not texts:
            return []
            
        # 支持modelscope作为dashscope的别名
        model_type = self.model_type
        if model_type == "modelscope":
            model_type = "dashscope"
            
        if model_type == "ollama":
            return self._embed_with_ollama(texts)
        elif model_type == "huggingface":
            return self._embed_with_huggingface(texts)
        elif model_type == "dashscope":
            return self._embed_with_dashscope(texts)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def _embed_with_ollama(self, texts: List[str]) -> List[List[float]]:
        """
        @brief 通过HTTP请求调用Ollama的嵌入API，将文本转换为向量表示，并包含重试机制
        
        @param texts (List[str]): 需要生成嵌入的文本列表
        
        @return List[List[float]]: 文本对应的向量表示列表
        """
        embeddings = []
        for text in texts:
            if not text.strip():
                embeddings.append([])
                continue
                
            for attempt in range(3):  
                try:
                    response = requests.post(
                        self.api_url,
                        json={
                            "model": self.model_name,
                            "prompt": text
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "embedding" in data and data["embedding"]:
                            embedding = data["embedding"]
                            
                            if len(embedding) == self.dim:
                                embeddings.append(embedding)
                                break
                            else:
                                logger.warning(f"Embedding dimension mismatch: expected {self.dim}, got {len(embedding)}")
                                embeddings.append([])
                                break
                        else:
                            logger.warning(f"Empty embedding for text: {text[:50]}...")
                    else:
                        logger.error(f"Error embedding text: {response.status_code} - {response.text}")
                    
                   
                    if attempt == 2:
                        logger.error(f"Failed to generate embedding after 3 attempts for text: {text[:50]}...")
                        embeddings.append([])
                except Exception as e:
                    logger.error(f"Ollama embedding error: {str(e)}")
                    if attempt == 2:
                        embeddings.append([])
        return embeddings
    
    def _embed_with_huggingface(self, texts: List[str]) -> List[List[float]]:
        """
        @brief 占位方法，用于HuggingFace模型的嵌入生成（当前未实现）
        
        @param texts (List[str]): 需要生成嵌入的文本列表
        
        @return List[List[float]]: 空向量列表，每个元素都是空列表
        """
        return [[] for _ in texts]
    
    def _embed_with_dashscope(self, texts: List[str]) -> List[List[float]]:
        """
        @brief 通过OpenAI兼容方式调用ModelScope的嵌入API，将文本转换为向量表示
        
        @param texts (List[str]): 需要生成嵌入的文本列表
        
        @return List[List[float]]: 文本对应的向量表示列表
        """
        if not self.modelscope_api_key:
            raise ValueError("ModelScope API key is not set. Please set DASHSCOPE_API_KEY environment variable.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library is not installed. Please install with 'pip install openai'")
        
        # 使用OpenAI兼容方式调用ModelScope API
        client = OpenAI(
            api_key=self.modelscope_api_key,
            base_url=self.modelscope_base_url
        )
        
        embeddings = []
        for text in texts:
            if not text.strip():
                embeddings.append([])
                continue
                
            try:
                # 调用ModelScope嵌入API
                response = client.embeddings.create(
                    input=text,
                    model=self.modelscope_model
                )
                
                # 提取嵌入向量
                if response.data and len(response.data) > 0:
                    embedding = response.data[0].embedding
                    if len(embedding) == self.dim:
                        embeddings.append(embedding)
                    else:
                        logger.warning(f"Embedding dimension mismatch: expected {self.dim}, got {len(embedding)}")
                        embeddings.append([])
                else:
                    logger.warning(f"Empty embedding in ModelScope response for text: {text[:50]}...")
                    embeddings.append([])
            except Exception as e:
                logger.error(f"ModelScope embedding error: {str(e)}")
                embeddings.append([])
        
        return embeddings
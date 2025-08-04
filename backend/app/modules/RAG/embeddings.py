import requests
import numpy as np
from typing import List
from core.config import settings
import logging
import time
import os

# 添加openai库导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class EmbeddingModel:
    def __init__(self):
        """
        @brief 初始化嵌入模型，根据配置选择不同类型的嵌入模型
        """
        self.config = settings.RAG_CONFIG["embeddings"]
        self.model_type = self.config["model_type"]
        self.model_name = self.config["model_name"]
        self.dim = self.config["dim"]
        self.batch_size = self.config["batch_size"]
        
        # 从环境变量获取API密钥
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.modelscope_api_key = os.getenv("MODELSCOPE_API_KEY", "")
        self.ollama_host = settings.SERVICE_CONFIG.get("ollama_host", "http://localhost:11434")
        self.modelscope_base_url = settings.SERVICE_CONFIG.get("modelscope_base_url", "https://api-inference.modelscope.cn/v1/")
        
        # 初始化模型
        if self.model_type == "ollama":
            self._init_ollama()
        elif self.model_type == "openai":
            self._init_openai()
        elif self.model_type == "modelscope":
            self._init_modelscope()
        else:
            raise ValueError(f"Unsupported embedding model type: {self.model_type}")
    
    def _init_ollama(self):
        """初始化Ollama嵌入模型"""
        logger.info(f"Initializing Ollama embedding model: {self.model_name}")
    
    def _init_openai(self):
        """初始化OpenAI嵌入模型"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set. Please set OPENAI_API_KEY environment variable.")
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        logger.info(f"Initializing OpenAI embedding model: {self.model_name}")
    
    def _init_modelscope(self):
        """初始化ModelScope嵌入模型"""
        if not self.modelscope_api_key:
            raise ValueError("ModelScope API key is not set. Please set MODELSCOPE_API_KEY environment variable.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Please install openai package.")
            
        self.modelscope_client = OpenAI(
            api_key=self.modelscope_api_key,
            base_url=self.modelscope_base_url
        )
        logger.info(f"Initializing ModelScope embedding model: {self.config['modelscope']['model']}")
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        @brief 为文本列表生成嵌入向量
        
        @param texts (List[str]): 待处理的文本列表
        
        @return List[List[float]]: 对应的嵌入向量列表
        """
        if self.model_type == "ollama":
            return self._embed_with_ollama(texts)
        elif self.model_type == "openai":
            return self._embed_with_openai(texts)
        elif self.model_type == "modelscope":
            return self._embed_with_modelscope(texts)
        else:
            raise ValueError(f"Unsupported embedding model type: {self.model_type}")
    
    def _embed_with_ollama(self, texts: List[str]) -> List[List[float]]:
        """使用Ollama生成嵌入"""
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model_name,
                        "prompt": text
                    }
                )
                if response.status_code == 200:
                    embedding = response.json()["embedding"]
                    embeddings.append(embedding)
                else:
                    logger.error(f"Ollama embedding failed: {response.status_code} - {response.text}")
                    # 返回零向量作为后备
                    embeddings.append([0.0] * self.dim)
            except Exception as e:
                logger.error(f"Error generating embedding with Ollama: {str(e)}")
                # 返回零向量作为后备
                embeddings.append([0.0] * self.dim)
        return embeddings
    
    def _embed_with_openai(self, texts: List[str]) -> List[List[float]]:
        """使用OpenAI生成嵌入"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Please install openai package.")
        
        try:
            response = self.openai_client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embedding with OpenAI: {str(e)}")
            raise e
    
    def _embed_with_modelscope(self, texts: List[str]) -> List[List[float]]:
        """使用ModelScope生成嵌入"""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Please install openai package.")
        
        try:
            model_name = self.config["modelscope"]["model"]
            response = self.modelscope_client.embeddings.create(
                input=texts,
                model=model_name
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embedding with ModelScope: {str(e)}")
            # 返回零向量作为后备
            return [[0.0] * self.dim for _ in texts]
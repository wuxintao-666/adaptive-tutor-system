import re
import logging
from typing import List, Dict
from core.config import settings
import requests
import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from tqdm import tqdm  
import time

# 添加openai库导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Please install with 'pip install openai'")

logger = logging.getLogger(__name__)

class TextSplitter:
    def __init__(self, progress_callback=None):
        """
        @brief 初始化文本分割器
        
        @param progress_callback (function, optional): 进度回调函数
        """
        self.config = settings.RAG_CONFIG["text_splitter"]
        self.chunk_size = self.config["chunk_size"]
        self.chunk_overlap = self.config["chunk_overlap"]
        self.progress_callback = progress_callback or (lambda **kwargs: None)
        
        # 从配置中获取服务参数
        self.ollama_host = settings.SERVICE_CONFIG.get("ollama_host", "http://localhost:11434")
        self.modelscope_base_url = settings.SERVICE_CONFIG.get("modelscope_base_url", "https://api-inference.modelscope.cn/v1/")
        
        # 从环境变量获取API密钥
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.modelscope_api_key = os.getenv("MODELSCOPE_API_KEY", "")
        
        # 从配置中获取摘要参数
        self.summarizer_config = settings.RAG_CONFIG["summarizer"]
        self.summarizer_model_type = self.summarizer_config["model_type"]
        self.summarizer_ollama_model = self.summarizer_config["ollama_model_name"]
        self.summarizer_modelscope_model = self.summarizer_config["modelscope_model_name"]
        self.max_summary_length = self.summarizer_config["max_summary_length"]
    
    def split_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        @brief 将文档分割成文本块并生成摘要
        
        @param documents (List[Dict]): 待分割的文档列表，每个文档包含'text'和'source'字段
        
        @return List[Dict]: 分割后的文本块列表，每个块包含'text'、'source'和'summary'字段
        """
        chunks = []
        total_docs = len(documents)
        
        for doc_idx, document in enumerate(documents):
            self.progress_callback(
                stage="split", 
                total=total_docs, 
                current=doc_idx, 
                message=f"正在分割文档 {doc_idx+1}/{total_docs}"
            )
            
            text = document["content"]
            source = document["source"]
            
            # 分割文本
            doc_chunks = self._split_text(text)
            
            # 为每个文本块生成摘要
            for chunk_idx, chunk_text in enumerate(doc_chunks):
                try:
                    summary = self._generate_summary(chunk_text)
                except Exception as e:
                    logger.error(f"生成摘要失败: {str(e)}")
                    summary = "无法生成摘要"
                
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "summary": summary,
                    "chunk_id": f"{source}_{doc_idx}_{chunk_idx}"
                })
        
        self.progress_callback(
            stage="split", 
            total=total_docs, 
            current=total_docs, 
            message="文档分割完成", 
            status="completed"
        )
        
        return chunks
    
    def _split_text(self, text: str) -> List[str]:
        """
        @brief 使用固定大小窗口分割文本
        
        @param text (str): 待分割的文本
        
        @return List[str]: 分割后的文本块列表
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            
            start += self.chunk_size - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_summary(self, text: str) -> str:
        """
        @brief 为文本块生成摘要
        
        @param text (str): 待摘要的文本
        
        @return str: 生成的摘要
        """
        prompt = f"请用中文为以下文本生成一个{self.max_summary_length}字以内的摘要：\n\n{text}"
        
        try:
            if self.summarizer_model_type == "ollama":
                return self._summarize_with_ollama(prompt)
            elif self.summarizer_model_type == "modelscope":
                return self._summarize_with_modelscope(prompt)
            elif self.summarizer_model_type == "openai":
                return self._summarize_with_openai(prompt)
            else:
                logger.warning(f"Unsupported summarizer model type: {self.summarizer_model_type}")
                return "无法生成摘要：不支持的模型类型"
        except Exception as e:
            logger.error(f"生成摘要时出错: {str(e)}")
            return "无法生成摘要"
    
    def _summarize_with_ollama(self, prompt: str) -> str:
        """使用Ollama生成摘要"""
        response = requests.post(
            f"{self.ollama_host}/api/generate",
            json={
                "model": self.summarizer_ollama_model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"].strip()
        else:
            raise Exception(f"Ollama summarization failed: {response.status_code} - {response.text}")
    
    def _summarize_with_modelscope(self, prompt: str) -> str:
        """使用ModelScope生成摘要"""
        if not self.modelscope_api_key:
            raise ValueError("ModelScope API key is not set. Please set MODELSCOPE_API_KEY environment variable.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Please install openai package.")
        
        client = OpenAI(
            api_key=self.modelscope_api_key,
            base_url=self.modelscope_base_url
        )
        
        completion = client.chat.completions.create(
            model=self.summarizer_modelscope_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return completion.choices[0].message.content.strip()
    
    def _summarize_with_openai(self, prompt: str) -> str:
        """使用OpenAI生成摘要"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is not set. Please set OPENAI_API_KEY environment variable.")
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Please install openai package.")
        
        client = OpenAI(api_key=self.openai_api_key)
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # 或其他适当的模型
            messages=[{"role": "user", "content": prompt}]
        )
        
        return completion.choices[0].message.content.strip()
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.config import RAG_CONFIG, SERVICE_CONFIG
from pathlib import Path
import logging
import requests
import time
from tqdm import tqdm  
from typing import List
import os
import json

# 添加openai库导入
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not available. Install with 'pip install openai' for ModelScope support.")

logger = logging.getLogger(__name__)

class TextSplitter:
    def __init__(self, progress_callback=None):
        """
        @brief 初始化文本分割器
        
        @param progress_callback (function, optional): 进度回调函数
        """
        config = RAG_CONFIG["text_splitter"]
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            separators=["\n\n", "\n", "。", "？", "！", "；", " ", ""],
            keep_separator=True
        )
        self.summarizer_config = RAG_CONFIG.get("summarizer", {})
        self.progress_callback = progress_callback or (lambda **kw: None)
        self.ollama_host = SERVICE_CONFIG["ollama_host"]
        self.modelscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.modelscope_base_url = SERVICE_CONFIG.get("modelscope_base_url", "https://api-inference.modelscope.cn/v1/")
    
    def generate_summary(self, text: str) -> str:
        """
        @brief 调用大语言模型为输入文本生成简洁的短语级摘要
        
        @param text (str): 需要生成摘要的输入文本
        
        @return str: 生成的摘要文本，失败时返回前5个词的组合
        """
        try:
            model_type = self.summarizer_config.get("model_type", "ollama")
            prompt = f"请用5-10个字的短语总结以下文本的核心内容，不要解释，只输出短语：\n{text}"
            
            # 添加重试机制
            for attempt in range(3):
                try:
                    if model_type == "ollama":
                        response = requests.post(
                            f"{self.ollama_host}/api/generate",
                            json={
                                "model": self.summarizer_config.get("ollama_model_name", "qwen:7b"),
                                "prompt": prompt,
                                "stream": False
                            },
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result = response.json().get("response", "").strip().replace('"', '')
                            if result:
                                return result
                            else:
                                logger.warning(f"Empty summary response for text: {text[:50]}...")
                        else:
                            logger.warning(f"摘要生成失败: {response.status_code} - {response.text}")
                    
                    elif model_type == "modelscope":
                        if not self.modelscope_api_key:
                            raise ValueError("ModelScope API key is not set. Please set DASHSCOPE_API_KEY environment variable.")
                        
                        if not OPENAI_AVAILABLE:
                            raise ImportError("OpenAI library is not installed. Please install with 'pip install openai'")
                        
                        # 使用OpenAI兼容方式调用ModelScope API
                        client = OpenAI(
                            api_key=self.modelscope_api_key,
                            base_url=self.modelscope_base_url
                        )
                        
                        chat_completion = client.chat.completions.create(
                            model=self.summarizer_config.get("modelscope_model_name", "Qwen/Qwen2.5-7B-Instruct"),
                            messages=[
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            stream=False,
                            max_tokens=20,
                            temperature=0.1
                        )
                        
                        result = chat_completion.choices[0].message.content.strip().replace('"', '')
                        if result:
                            return result
                        else:
                            logger.warning(f"Empty summary response for text: {text[:50]}...")
                
                except requests.exceptions.Timeout:
                    logger.warning(f"摘要生成超时 (尝试 {attempt+1}/3): {text[:50]}...")
                    if attempt == 2:  # 最后一次尝试
                        logger.error(f"摘要生成最终超时: {text[:50]}...")
                
                except Exception as e:
                    logger.error(f"摘要生成错误 (尝试 {attempt+1}/3): {str(e)}")
                    if attempt == 2:  # 最后一次尝试
                        logger.error(f"摘要生成最终失败: {text[:50]}...")
                
                # 重试前等待
                if attempt < 2:
                    time.sleep(2 ** attempt)  # 指数退避
        
        except Exception as e:
            logger.error(f"摘要生成错误: {str(e)}")
        
        
        return " ".join(text.split()[:5])
    
    
    def _smart_split(self, text: str) -> List[str]:
        """
        @brief 将输入文本按配置的块大小进行分割，同时尽量保持句子完整性
        
        @param text (str): 需要分割的输入文本
        
        @return List[str]: 分割后的文本块列表
        """
        
        sentence_endings = {'。', '？', '！', '；', '.', '?', '!', ';'}
        
        chunks = []
        current_chunk = ""
        char_count = 0
        
        
        for char in text:
            current_chunk += char
            char_count += 1
            
            
            if char_count >= self.splitter._chunk_size * 0.7 and char in sentence_endings:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                char_count = 0
                
            
            elif char_count >= self.splitter._chunk_size:
                
                for i in range(len(current_chunk)-1, -1, -1):
                    if current_chunk[i] in sentence_endings:
                        chunks.append(current_chunk[:i+1].strip())
                        current_chunk = current_chunk[i+1:]
                        char_count = len(current_chunk)
                        break
                else:  
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    char_count = 0
        
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def split_documents(self, documents):
        """
        @brief 将加载的文档列表分割为较小的文本块，并为每个块生成摘要
        
        @param documents (list): 文档列表，每个元素包含文件路径和内容
        
        @return list: 分割后的文本块列表，每个元素包含文本、摘要等信息
        """
        chunks = []
        total_docs = len(documents)
        
        
        self.progress_callback(stage="split", total=total_docs, current=0, message="开始分割文档")
        
        for doc_idx, doc in enumerate(tqdm(documents, desc="分割文档")):
            content = doc["content"]
            
            content = re.sub(r'\s+', ' ', content).strip()
            
            split_texts = self._smart_split(content)
            
            
            self.progress_callback(
                stage="split",
                current=doc_idx + 1,
                total=total_docs,
                message=f"正在处理文档: {Path(doc['source']).name}",
                details=f"分割成 {len(split_texts)} 个片段"
            )
            
            for i, text in enumerate(split_texts):
                
                summary = self.generate_summary(text)
                
                chunks.append({
                    "text": text,
                    "summary": summary,
                    "source": doc["source"],
                    "chunk_id": f"{Path(doc['source']).stem}_{i}"
                })
        
        
        self.progress_callback(
            stage="split",
            current=total_docs,
            total=total_docs,
            message=f"文档分割完成",
            details=f"共生成 {len(chunks)} 个文本块"
        )
        
        return chunks
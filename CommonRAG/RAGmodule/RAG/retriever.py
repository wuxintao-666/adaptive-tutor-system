from .embeddings import EmbeddingModel
from .vector_store import VectorStore
from config import RAG_CONFIG, SERVICE_CONFIG
from pathlib import Path
import logging
import json
import requests
import re  
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

class Retriever:
    def __init__(self):
        """
        @brief 初始化检索器
        """
        self.embedding_model = EmbeddingModel()
        self.vector_store = VectorStore()
        self.vector_store.load_index()
        
        
        retriever_config = RAG_CONFIG["retriever"]
        self.top_k = retriever_config["top_k"]
        self.score_threshold = retriever_config["score_threshold"]
        self.enable_rerank = retriever_config["enable_rerank"]
        
        
        reranker_config = RAG_CONFIG.get("reranker", {})
        self.reranker_enable = reranker_config.get("enable", False)
        self.reranker_model_type = reranker_config.get("model_type", "ollama")
        self.reranker_ollama_model = reranker_config.get("ollama_model_name", "qwen:7b")
        self.reranker_modelscope_model = reranker_config.get("modelscope_model_name", "Qwen/Qwen2.5-7B-Instruct")
        self.top_n_for_rerank = reranker_config.get("top_n_for_rerank", 10)
        self.rerank_score_threshold = reranker_config.get("score_threshold", 0.3)
        self.reranker_prompt_template = reranker_config.get("prompt_template", "")
        self.ollama_host = SERVICE_CONFIG["ollama_host"]
        self.rerank_timeout = SERVICE_CONFIG["rerank_timeout"]
        self.modelscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.modelscope_base_url = SERVICE_CONFIG.get("modelscope_base_url", "https://api-inference.modelscope.cn/v1/")
    
    def retrieve(self, query: str, use_rerank: bool = None) -> str:
        """
        @brief 根据输入查询检索相关文档片段，可选择是否进行重排序，并返回格式化的上下文字符串
        
        @param query (str): 用户的查询字符串
        @param use_rerank (bool, optional): 是否启用重排序功能，默认为None时使用配置值
        
        @return str: 格式化的上下文信息字符串
        """
        
        if use_rerank is None:
            use_rerank = self.reranker_enable or self.enable_rerank
            
        
        query_embedding = self.embedding_model.embed_texts([query])
        if not query_embedding or not query_embedding[0]:
            logger.warning(f"Failed to generate embedding for query: '{query}'")
            return ""
        
        
        if not isinstance(query_embedding[0], list) or not all(isinstance(x, float) for x in query_embedding[0]):
            logger.error(f"Invalid embedding format for query: '{query}'")
            return ""
        
        
        results = self.vector_store.similarity_search(
            query_embedding[0], 
            top_k=self.top_k
        )
        
        
        if use_rerank and results:
            reranked_results = self._rerank_documents(query, results)
            if reranked_results:
                results = reranked_results
        
        
        context = []
        for score, chunk_id, chunk_data in results:
            if score >= self.score_threshold:
                context.append({
                    "text": chunk_data["text"],
                    "summary": chunk_data["summary"],
                    "source": chunk_data["source"],
                    "score": round(score, 3)
                })
        
        
        return self._format_context(context)
    
    def retrieve_raw(self, query: str, use_rerank: bool = None) -> list:
        """
        @brief 根据输入查询检索相关文档片段，返回原始数据结构
        
        @param query (str): 用户的查询字符串
        @param use_rerank (bool, optional): 是否启用重排序功能，默认为None时使用配置值
        
        @return list: 包含检索结果的列表，每个元素是包含文本、摘要等信息的字典
        """
        if use_rerank is None:
            use_rerank = self.reranker_enable or self.enable_rerank
        query_embedding = self.embedding_model.embed_texts([query])
        if not query_embedding or not query_embedding[0]:
            logger.warning(f"Failed to generate embedding for query: '{query}'")
            return []
        if not isinstance(query_embedding[0], list) or not all(isinstance(x, float) for x in query_embedding[0]):
            logger.error(f"Invalid embedding format for query: '{query}'")
            return []
        results = self.vector_store.similarity_search(
            query_embedding[0],
            top_k=self.top_k
        )
        if use_rerank and results:
            reranked_results = self._rerank_documents(query, results)
            if reranked_results:
                results = reranked_results
        context = []
        for score, chunk_id, chunk_data in results:
            if score >= self.score_threshold:
                context.append({
                    "text": chunk_data["text"],
                    "summary": chunk_data["summary"],
                    "source": chunk_data["source"],
                    "score": round(score, 3)
                })
        return context
    
    def _rerank_documents(self, query: str, results: list) -> list:
        """
        @brief 通过调用大语言模型对初步检索结果进行相关性重排序
        
        @param query (str): 用户的原始查询
        @param results (list): 初步检索结果列表
        
        @return list: 重排序后的结果列表，格式与输入相同
        """
        if len(results) < 2:  
            return None
        
        
        summaries = []
        for i, (score, _, chunk_data) in enumerate(results[:self.top_n_for_rerank]):
            summaries.append(f"[{i+1}] {chunk_data['summary']}")
        
        
        prompt = self.reranker_prompt_template.format(
            query=query,
            summaries="\n".join(summaries)
        )
        
        try:
            
            if self.reranker_model_type == "ollama":
                response = requests.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.reranker_ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=self.rerank_timeout
                )
                
                if response.status_code == 200:
                    response_text = response.json().get("response", "").strip()
                else:
                    logger.error(f"重排序失败: {response.status_code} - {response.text}")
                    return None
                    
            elif self.reranker_model_type == "modelscope":
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
                    model=self.reranker_modelscope_model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    stream=False,
                    temperature=0.1
                )
                
                response_text = chat_completion.choices[0].message.content.strip()
            
            logger.info(f"大模型原始返回: {response_text}")
            ranked_pairs = self._parse_rerank_response(response_text)
            
            if not ranked_pairs:
                logger.info("重排序未返回有效结果")
                return None
            
            
            reranked = []
            for idx, score in ranked_pairs:
                
                if 1 <= idx <= len(summaries):
                    
                    original_index = idx - 1  
                    reranked.append((
                        results[original_index][0],  
                        score,                      
                        results[original_index][1],  
                        results[original_index][2]   
                    ))
            
            
            reranked.sort(key=lambda x: x[1], reverse=True)
            
            
            final_results = []
            for item in reranked:
                
                final_results.append((item[0], item[2], item[3]))
            
            
            if self.top_n_for_rerank < len(results):
                final_results.extend(results[self.top_n_for_rerank:])
            
            return final_results
        except Exception as e:
            logger.error(f"重排序失败: {str(e)}")
        
        return None
    
    def _parse_rerank_response(self, response_text: str) -> list:
        """
        @brief 解析重排序模型的响应文本，提取索引和分数对
        
        @param response_text (str): 模型返回的原始响应文本
        
        @return list: 解析后的索引和分数对列表，格式为[(索引, 分数), ...]
        """
        try:
            
            match = re.search(r'\[.*\]', response_text)
            if match:
                json_str = match.group(0)
                parsed = json.loads(json_str)
                if isinstance(parsed, list) and all(isinstance(x, list) and len(x) == 2 for x in parsed):
                    return [(int(x[0]), float(x[1])) for x in parsed if isinstance(x[0], (int, float)) and isinstance(x[1], (int, float))]
            else:
                
                parsed = json.loads(response_text)
                if isinstance(parsed, list) and all(isinstance(x, list) and len(x) == 2 for x in parsed):
                    return [(int(x[0]), float(x[1])) for x in parsed if isinstance(x[0], (int, float)) and isinstance(x[1], (int, float))]
        except json.JSONDecodeError:
            logger.warning(f"JSON解析失败: {response_text}")
        except Exception as e:
            logger.error(f"解析重排序响应时出错: {str(e)}")
        
        return []
    
    def _format_context(self, context: list) -> str:
        """
        @brief 将检索到的上下文列表格式化为字符串
        
        @param context (list): 检索到的上下文列表
        
        @return str: 格式化后的上下文字符串
        """
        if not context:
            return ""
        
        formatted = []
        for i, item in enumerate(context, 1):
            formatted.append(
                f"[{i}][{item['summary']}][相关度:{item['score']}]\n"
                f"{item['text']}\n"
                f"来源: {item['source']}\n"
            )
        
        return "\n".join(formatted).strip()
# backend/app/services/rag_service.py
import json
import os
import time
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings

class RAGService:
	def __init__(self):
		# 在应用启动时加载索引和数据
		self.embedding_dimension = 2560 # for Qwen/Qwen3-Embedding-4B-GGUF
		self.index = AnnoyIndex(self.embedding_dimension, 'angular')
		
		# 获取当前文件的目录
		current_dir = os.path.dirname(os.path.abspath(__file__))
		# 构建数据文件的绝对路径 (正确计算到backend/data目录)
		backend_dir = os.path.dirname(os.path.dirname(current_dir))
		data_dir = os.path.join(backend_dir, 'data')
		kb_ann_path = os.path.join(data_dir, 'kb.ann')
		kb_chunks_path = os.path.join(data_dir, 'kb_chunks.json')
		
		# 使用内存映射加载索引，非常高效
		self.index.load(kb_ann_path, prefault=False) 
	  
		with open(kb_chunks_path, "r", encoding="utf-8") as f:
			self.chunks = json.load(f)
	  
		# 使用OpenAI客户端连接ModelScope API
		self.client = OpenAI(
			api_key=settings.EMBEDDING_API_KEY,
			base_url=settings.EMBEDDING_API_BASE,
			timeout=30.0  # 设置30秒超时
		)
		self.embedding_model = settings.EMBEDDING_MODEL

	def _get_embedding(self, text: str) -> list[float]:
		"""使用OpenAI客户端获取单个文本的embedding"""
		# 处理空查询
		if not text or not text.strip():
			# 对于空查询，返回零向量
			return [0.0] * self.embedding_dimension
			
		try:
			# 添加重试机制
			max_retries = 3
			for attempt in range(max_retries):
				try:
					response = self.client.embeddings.create(
						input=text,  # ModelScope API期望字符串而不是列表
						model=self.embedding_model
					)
					if response.data and len(response.data) > 0 and response.data[0].embedding:
						return response.data[0].embedding
					else:
						raise ValueError("Empty embedding received from API")
				except Exception as e:
					if attempt < max_retries - 1:
						# 等待后重试
						time.sleep(1 * (attempt + 1))  # 指数退避
						continue
					else:
						raise e
		except Exception as e:
			print(f"Error calling embedding API: {e}")
			raise ValueError(f"Failed to get embedding from API: {str(e)}")

	def retrieve(self, query_text: str, k: int = 3) -> list[str]:
		try:
			query_vector = self._get_embedding(query_text)
			
			if not query_vector:
				raise ValueError("Empty embedding vector received")
			
			# 在Annoy中搜索
			indices = self.index.get_nns_by_vector(query_vector, k)
	  
			return [self.chunks[i] for i in indices]
		except Exception as e:
			# 记录详细的错误信息
			print(f"Error in retrieve: {e}")
			raise

# rag_service = RAGService()

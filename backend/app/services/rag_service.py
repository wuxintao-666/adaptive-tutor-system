# backend/services/rag_service.py
import json
import os
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings

class RAGService:
    def __init__(self):
        # 在应用启动时加载索引和数据
        self.embedding_dimension = 1536 # for text-embedding-3-small
        self.index = AnnoyIndex(self.embedding_dimension, 'angular')
        # 使用内存映射加载索引，非常高效
        index_file = os.path.join(settings._vector_store_dir, settings.RAG_CONFIG["vector_store"]["index_file"])
        self.index.load(index_file, prefault=False) 
      
        chunks_file = os.path.join(settings._vector_store_dir, settings.RAG_CONFIG["vector_store"]["chunks_file"])
        with open(chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
      
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_model = settings.EMBEDDING_MODEL

    def retrieve(self, query_text: str, k: int = 3) -> list[str]:
        # 参数验证
        if not query_text or not isinstance(query_text, str):
            return []
        
        if k <= 0:
            return []
            
        response = self.client.embeddings.create(input=[query_text], model=self.embedding_model)
        query_vector = response.data[0].embedding
      
        # 在Annoy中搜索
        indices = self.index.get_nns_by_vector(query_vector, k)
      
        return [self.chunks[i] for i in indices]

rag_service = RAGService()
# backend/services/rag_service.py
import json
import os
import sys
from openai import OpenAI
from annoy import AnnoyIndex

# 将项目根目录添加到Python路径，以便导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings

class RAGService:
    def __init__(self):
        # 在应用启动时加载索引和数据
        # 首先从chunks文件中获取向量维度
        vector_store_dir = settings.VECTOR_STORE_DIR
        chunks_file = os.path.join(vector_store_dir, settings.RAG_CONFIG["vector_store"]["chunks_file"])
        
        try:
            with open(chunks_file, "r", encoding="utf-8") as f:
                self.chunks = json.load(f)
        except FileNotFoundError:
            print(f"Error: Chunks file not found at {chunks_file}. Please run the build script first.")
            self.chunks = []
        
        # 使用内存映射加载索引，非常高效
        # 注意: 必须先获取维度才能加载索引
        self.embedding_dimension = self._get_embedding_dimension()
        if self.embedding_dimension:
            self.index = AnnoyIndex(self.embedding_dimension, 'angular')
            index_file = os.path.join(vector_store_dir, settings.RAG_CONFIG["vector_store"]["index_file"])
            try:
                self.index.load(index_file, prefault=False)
            except Exception as e:
                print(f"Error loading Annoy index: {e}. It might not exist yet.")
                self.index = None
        else:
            self.index = None
      
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )
        self.embedding_model = settings.EMBEDDING_MODEL

    def _get_embedding_dimension(self) -> int:
        """从样本中获取嵌入维度"""
        if self.chunks:
            # 尝试通过向量化一小段文本来获取维度
            try:
                response = self.client.embeddings.create(
                    input=[self.chunks[0]], 
                    model=self.embedding_model,
                    encoding_format="float"
                )
                return len(response.data[0].embedding)
            except Exception as e:
                print(f"Could not determine embedding dimension: {e}")
        return 0

    def retrieve(self, query_text: str, k: int = 3) -> list[str]:
        if not query_text or not isinstance(query_text, str) or self.index is None:
            return []
        
        if k <= 0:
            return []
            
        try:
            response = self.client.embeddings.create(
                input=[query_text], 
                model=self.embedding_model,
                encoding_format="float"
            )
            query_vector = response.data[0].embedding
      
            indices = self.index.get_nns_by_vector(query_vector, k)
      
            return [self.chunks[i] for i in indices]
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []

rag_service = RAGService()
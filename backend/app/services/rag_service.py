# backend/services/rag_service.py
import sys
import os
from pathlib import Path

# 将新的RAG模块路径添加到Python路径中
rag_module_path = os.path.join(os.path.dirname(__file__), '..', 'modules')
if rag_module_path not in sys.path:
    sys.path.append(rag_module_path)

# 确保能正确导入core.config
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

from RAG.retriever import Retriever

class RAGService:
    def __init__(self):
        # 初始化RAG的检索器
        self.retriever = Retriever()

    def retrieve(self, query_text: str, k: int = 3) -> list[str]:
        """
        使用RAG模块进行检索
        根据TDD要求保持接口一致，返回字符串列表
        """
        # 参数验证
        if not query_text or not isinstance(query_text, str):
            return []
        
        if k <= 0:
            return []
            
        # 临时修改top_k值以获取指定数量的结果
        original_top_k = self.retriever.top_k
        self.retriever.top_k = k
        
        try:
            # 从RAG获取原始结果
            raw_results = self.retriever.retrieve_raw(query_text)
            
            # 处理边界情况
            if not raw_results:
                return []
            
            # 提取文本内容，确保返回的数量符合要求
            texts = [item["text"] for item in raw_results[:k]]
            return texts
        except Exception as e:
            # 记录错误但不中断程序
            print(f"Error retrieving documents: {e}")
            return []
        finally:
            # 恢复原始设置
            self.retriever.top_k = original_top_k

rag_service = RAGService()
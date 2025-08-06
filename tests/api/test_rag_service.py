import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add backend to path so we can import rag_service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.services.rag_service import RAGService


class TestRAGServiceIntegration:
    """RAG服务集成测试"""

    @pytest.fixture
    def mock_embedding_response(self):
        """模拟嵌入API响应"""
        mock_response = Mock()
        mock_data = Mock()
        mock_data.embedding = [0.1] * 4096  # 模拟4096维的嵌入向量
        mock_response.data = [mock_data]
        return mock_response

    @pytest.fixture
    def sample_chunks(self):
        """示例知识库片段"""
        return [
            "Python是一种高级编程语言，具有简洁易读的语法。",
            "机器学习是人工智能的一个分支，专注于算法和统计模型。",
            "数据库是结构化数据的集合，用于存储和检索信息。"
        ]

    @patch('app.services.rag_service.OpenAI')
    @patch('app.services.rag_service.AnnoyIndex')
    def test_rag_service_initialization(self, mock_annoy_index, mock_openai):
        """测试RAG服务是否能正确加载知识库"""
        # 准备模拟数据
        mock_index = Mock()
        mock_annoy_index.return_value = mock_index
        
        # 模拟知识库文件
        sample_chunks = ["测试内容1", "测试内容2", "测试内容3"]
        
        with patch('builtins.open', mock_open=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_chunks)
            
            # 创建RAG服务实例
            rag_service = RAGService()
            
            # 验证初始化过程
            assert rag_service.embedding_dimension == 4096
            mock_annoy_index.assert_called_once_with(4096, 'angular')
            mock_index.load.assert_called_once_with("backend/data/kb.ann", prefault=False)
            
            # 验证OpenAI客户端初始化
            mock_openai.assert_called_once_with(
                api_key="ms-0d9e9f84-5c9c-4d39-b760-a0a7458c3ecd",
                base_url="https://ms-fc-1d889e1e-d2ad.api-inference.modelscope.cn/v1"
            )

    @patch('app.services.rag_service.OpenAI')
    @patch('app.services.rag_service.AnnoyIndex')
    def test_retrieve_functionality(self, mock_annoy_index, mock_openai, mock_embedding_response):
        """测试向量检索功能是否正常工作"""
        # 准备模拟对象
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = mock_embedding_response
        
        mock_index = Mock()
        mock_annoy_index.return_value = mock_index
        
        # 模拟检索结果
        mock_index.get_nns_by_vector.return_value = [0, 1, 2]
        
        # 模拟知识库内容
        sample_chunks = ["相关内容1", "相关内容2", "相关内容3"]
        
        with patch('builtins.open', mock_open=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_chunks)
            
            # 创建RAG服务实例
            rag_service = RAGService()
            
            # 执行检索
            query = "测试查询"
            results = rag_service.retrieve(query, k=3)
            
            # 验证结果
            assert len(results) == 3
            assert results == sample_chunks
            
            # 验证调用过程
            mock_client.embeddings.create.assert_called_once_with(
                input=[query], 
                model="Qwen/Qwen3-Embedding-4B-GGUF"
            )
            mock_index.get_nns_by_vector.assert_called_once()

    @patch('app.services.rag_service.OpenAI')
    @patch('app.services.rag_service.AnnoyIndex')
    def test_retrieve_returns_expected_results(self, mock_annoy_index, mock_openai, mock_embedding_response):
        """验证返回的结果是否符合预期"""
        # 准备模拟对象
        mock_client = Mock()
        mock_openai.return_value = mock_client
        mock_client.embeddings.create.return_value = mock_embedding_response
        
        mock_index = Mock()
        mock_annoy_index.return_value = mock_index
        
        # 模拟检索结果
        mock_index.get_nns_by_vector.return_value = [1, 0, 2]
        
        # 模拟知识库内容
        sample_chunks = [
            "Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。",
            "Python由Guido van Rossum于1989年发明，第一个公开发行版发行于1991年。",
            "Python的设计哲学强调代码的可读性和简洁的语法。"
        ]
        
        with patch('builtins.open', mock_open=True) as mock_file:
            mock_file.return_value.__enter__.return_value.read.return_value = json.dumps(sample_chunks)
            
            # 创建RAG服务实例
            rag_service = RAGService()
            
            # 执行检索
            query = "Python的历史"
            results = rag_service.retrieve(query, k=2)
            
            # 验证结果数量和内容
            assert len(results) == 2
            assert results[0] == sample_chunks[1]  # 应该返回索引为1的内容（根据mock的返回）
            assert results[1] == sample_chunks[0]  # 应该返回索引为0的内容


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
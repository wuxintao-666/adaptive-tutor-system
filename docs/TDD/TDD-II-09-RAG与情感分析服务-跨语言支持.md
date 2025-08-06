### **详细技术设计文档 (TDD-II-09-1): RAG服务跨语言支持**

**版本:** 1.0
**关联的顶层TDD:** TDD-II-09 - RAG与情感分析服务
**作者:** Claude Code
**日期:** 2025-8-6

#### **1. 功能概述 (Feature Overview)**

**目标:** 扩展现有的RAG服务，使其能够支持跨语言查询，特别是中文查询英文文档的功能。

**核心原则:**
*   **向后兼容:** 新功能不应影响现有英文查询的功能。
*   **性能考量:** 翻译过程应尽可能高效，避免显著增加查询延迟。
*   **易于集成:** 翻译服务应简单明了，方便RAG服务进行调用。

**范围:**
1.  设计翻译服务的实现细节，包括API选择和错误处理。
2.  修改RAG服务以集成翻译功能。
3.  更新相关配置以支持翻译服务。

#### **2. 设计与实现**

##### **2.1. 翻译服务 (`TranslationService`)**

*   **服务实现 (`backend/services/translation_service.py`)**
```python
# backend/services/translation_service.py
from openai import OpenAI
from app.core.config import settings
import time

class TranslationService:
    def __init__(self):
        # 使用OpenAI客户端连接ModelScope API
        self.client = OpenAI(
            api_key=settings.TUTOR_OPENAI_API_KEY,
            base_url=settings.TUTOR_OPENAI_API_BASE,
            timeout=30.0  # 设置30秒超时
        )
        self.translation_model = settings.TUTOR_OPENAI_MODEL

    def translate(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """
        使用LLM将文本从源语言翻译成目标语言
        """
        # 处理空查询
        if not text or not text.strip():
            return ""
            
        try:
            # 添加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    prompt = f"请将以下{source_lang}文本翻译成{target_lang}，只返回翻译结果，不要添加任何其他内容：\n\n{text}"
                    
                    response = self.client.chat.completions.create(
                        model=self.translation_model,
                        messages=[
                            {"role": "system", "content": f"你是一个专业的翻译员，专门负责将{source_lang}翻译成{target_lang}。"},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.3
                    )
                    
                    if response.choices and len(response.choices) > 0 and response.choices[0].message.content:
                        return response.choices[0].message.content.strip()
                    else:
                        raise ValueError("Empty translation received from API")
                except Exception as e:
                    if attempt < max_retries - 1:
                        # 等待后重试
                        time.sleep(1 * (attempt + 1))  # 指数退避
                        continue
                    else:
                        raise e
        except Exception as e:
            print(f"Error calling translation API: {e}")
            raise ValueError(f"Failed to get translation from API: {str(e)}")

translation_service = TranslationService()
```

##### **2.2. 修改后的RAG服务 (`RAGService`)**
*   **在线检索时序图 (带翻译功能):**
    ```mermaid
    sequenceDiagram
        participant Controller as DynamicController
        participant RAG as RAGService
        participant Translation as TranslationService
        participant Embedding as Embedding API
        participant Annoy as Annoy Index (memory-mapped)

        Controller->>RAG: 1. retrieve(user_message)
        RAG->>Translation: 2. translate(user_message, 'zh', 'en')
        Translation-->>RAG: 3. 返回翻译后的英文查询
        RAG->>Embedding: 4. 将英文查询向量化
        Embedding-->>RAG: 5. 返回问题向量
        RAG->>Annoy: 6. get_nns_by_vector(问题向量, k=3)
        Annoy-->>RAG: 7. 返回Top-3最相似项的索引
        RAG->>RAG: 8. 从映射文件中根据索引查找原始文本块
        RAG-->>Controller: 9. 返回Top-3相关的文本片段
    ```

*   **修改后的服务实现 (`backend/services/rag_service.py`)**
```python
# backend/services/rag_service.py
import json
import os
import time
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings
# 导入翻译服务
from app.services.translation_service import translation_service

class RAGService:
    def __init__(self):
        # 在应用启动时加载索引和数据
        self.embedding_dimension = 2560 # for Qwen/Qwen3-Embedding-4B-GGUF
        self.index = AnnoyIndex(self.embedding_dimension, 'angular')
        
        # 使用配置中的路径
        kb_ann_path = os.path.join(settings.VECTOR_STORE_DIR, settings.KB_ANN_FILENAME)
        kb_chunks_path = os.path.join(settings.VECTOR_STORE_DIR, settings.KB_CHUNKS_FILENAME)
        
        # 使用内存映射加载索引，非常高效
        self.index.load(kb_ann_path, prefault=False) 
  
        with open(kb_chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
  
        # 使用OpenAI客户端连接ModelScope API
        self.client = OpenAI(
            api_key=settings.TUTOR_EMBEDDING_API_KEY,
            base_url=settings.TUTOR_EMBEDDING_API_BASE,
            timeout=30.0  # 设置30秒超时
        )
        self.embedding_model = settings.TUTOR_EMBEDDING_MODEL
        
        # 初始化翻译服务
        self.translation_service = translation_service

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
            # 检查查询是否为中文，如果是则翻译成英文
            if self._is_chinese(query_text):
                translated_query = self.translation_service.translate(query_text, "zh", "en")
                print(f"Translated query: {query_text} -> {translated_query}")
                query_text = translated_query
            
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
            
    def _is_chinese(self, text: str) -> bool:
        """
        简单判断文本是否包含中文字符
        """
        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                return True
        return False

# 后面使用DI，而非使用单例
# rag_service = RAGService()
```

##### **2.3. 配置更新 (`backend/core/config.py`)**
需要确保配置文件中包含翻译服务所需的配置项：

```python
# 在现有的配置类中添加以下配置项
# OpenAI (for chat completions - including translation)
TUTOR_OPENAI_API_KEY: str
TUTOR_OPENAI_MODEL: str = "gpt-4-turbo"
TUTOR_OPENAI_API_BASE: str = "https://api.openai.com/v1"
```

#### **3. 测试计划**

1.  **单元测试:**
    *   测试翻译服务的基本功能
    *   测试RAG服务的_is_chinese方法
    *   测试RAG服务在中英文查询下的表现

2.  **集成测试:**
    *   测试完整的跨语言查询流程
    *   测试错误处理和重试机制

3.  **性能测试:**
    *   测量添加翻译功能后的查询延迟
    *   测试在高并发情况下的表现

#### **4. 部署和监控**

1.  **部署:**
    *   确保新的翻译服务模块被正确部署
    *   更新配置文件以包含必要的API密钥和端点

2.  **监控:**
    *   添加翻译服务的调用日志
    *   监控翻译和检索的性能指标
    *   设置错误率和延迟的告警

***
**总结:**
通过添加翻译服务，RAG服务现在可以支持跨语言查询，特别是中文查询英文文档的功能。这个扩展保持了向后兼容性，同时为用户提供更灵活的查询方式。
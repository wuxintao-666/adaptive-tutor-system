### **详细技术设计文档 (TDD-II-09): RAG与情感分析服务**

**版本:** 1.2
**关联的顶层TDD:** V1.2 - 章节 2.1, 2.3
**作者:** 曹欣卓
**日期:** 2025-7-29

#### **1. 功能概述 (Feature Overview)**

**目标:** 设计并实现两个独立的、高性能的后端服务，用于增强AI对话的上下文理解能力：
1.  **RAGService:** 从一个权威的、预处理过的向量知识库中，快速检索与用户提问最相关的信息。
2.  **SentimentAnalysisService:** 使用一个预训练的深度学习模型（如BERT），对用户的聊天文本进行情感分析，输出如“困惑”、“沮丧”等情感标签。

**核心原则:**

*   **解耦与单一职责:** 每个服务只做一件事并把它做好。RAG负责信息检索，SentimentAnalysis负责情感判断。
*   **性能考量:** 这两个服务，特别是模型推理部分，可能是计算密集型的。设计时需考虑模型的加载、缓存和推理效率。
*   **易于集成:** 服务的接口应简单明了，方便`DynamicController`和`UserStateService`进行调用。

**范围:**

1.  设计`RAGService`的实现细节，包括知识库加载和检索方法。
2.  设计`SentimentAnalysisService`的实现细节，包括BERT模型的加载和推理方法。
3.  规划支持这些服务的离线脚本（如知识库构建、模型下载）。

#### **2. 设计与实现**

##### **2.1. RAG 服务 (`RAGService`)**

*   **离线构建流程图:**
    这个流程在项目开发前执行一次，用于创建向量知识库。

    ```mermaid
	graph TD
	    A[1.收集与切块] --> B[2.向量化];
	    B --> C{构建数据结构};
	    C --> D["**Annoy 索引文件** <br> (kb.ann)"];
	    C --> E["文本块映射文件 <br> (kb_chunks.json)"];

    ```

*   **离线构建脚本 (`scripts/build_knowledge_base.py`):**
这里可以看智尧你打算怎么做，这个是构建知识库的。能按我这里写的方式做一下最好，懒得改或者说你的方法更好你需要改动也没关系，这个可以改的，只需要保证下面的服务实现代码不要改变接口就好。

```python
# scripts/build_knowledge_base.py (使用Annoy)
import json
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings

# 1. 加载并切分文档...
text_chunks = [...] 

# 2. 向量化
client = OpenAI(api_key=settings.OPENAI_API_KEY)
response = client.embeddings.create(input=text_chunks, model=settings.EMBEDDING_MODEL)
embeddings = [item.embedding for item in response.data]
dimension = len(embeddings[0])

# 3. 构建Annoy索引
annoy_index = AnnoyIndex(dimension, 'angular') # 'angular' is recommended for cosine-based embeddings
for i, vector in enumerate(embeddings):
	annoy_index.add_item(i, vector)

annoy_index.build(10) # 10棵树，树越多精度越高，但索引越大

# 4. 保存索引和文本块
annoy_index.save("backend/data/kb.ann")
with open("backend/data/kb_chunks.json", "w", encoding="utf-8") as f:
	json.dump(text_chunks, f)
print("Annoy index and chunks saved.")
```

*   **在线检索时序图 (Annoy版):**
    ```mermaid
    sequenceDiagram
        participant Controller as DynamicController
        participant RAG as RAGService
        participant Embedding as Embedding API
        participant Annoy as Annoy Index (memory-mapped)

        Controller->>RAG: 1. retrieve(user_message)
        RAG->>Embedding: 2. 将user_message向量化
        Embedding-->>RAG: 3. 返回问题向量
        RAG->>Annoy: 4. get_nns_by_vector(问题向量, k=3)
        Annoy-->>RAG: 5. 返回Top-3最相似项的索引
        RAG->>RAG: 6. 从映射文件中根据索引查找原始文本块
        RAG-->>Controller: 7. 返回Top-3相关的文本片段
    ```

*   **服务实现 (`backend/services/rag_service.py`)**
	这里结构不能改了

```python
# backend/services/rag_service.py
import json
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings

class RAGService:
	def __init__(self):
		# 在应用启动时加载索引和数据
		self.embedding_dimension = 1536 # for text-embedding-3-small
		self.index = AnnoyIndex(self.embedding_dimension, 'angular')
		# 使用内存映射加载索引，非常高效
		self.index.load("backend/data/kb.ann", prefault=False) 
	  
		with open("backend/data/kb_chunks.json", "r", encoding="utf-8") as f:
			self.chunks = json.load(f)
	  
		self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
		self.embedding_model = settings.EMBEDDING_MODEL

	def retrieve(self, query_text: str, k: int = 3) -> list[str]:
		response = self.client.embeddings.create(input=[query_text], model=self.embedding_model)
		query_vector = response.data[0].embedding
	  
		# 在Annoy中搜索
		indices = self.index.get_nns_by_vector(query_vector, k)
	  
		return [self.chunks[i] for i in indices]

rag_service = RAGService()
```

##### **2.2. 情感分析服务 (`SentimentAnalysisService`)**

*   **模型准备:**
    *   **模型选择:** 用新涛之前搞的那个，或者从Hugging Face Hub选择一个适用于文本分类/情感分析的、轻量级的预训练模型，例如 `distilbert-base-uncased-finetuned-sst-2-english` 或一个专门为教学领域微调的模型。
    *   **离线下载:** 编写一个脚本 (`scripts/download_models.py`)，使用`transformers`库提前下载模型文件到本地，避免服务启动时才去下载。
        ```python
        # scripts/download_models.py
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
      
        MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
        SAVE_DIRECTORY = "backend/models/sentiment_bert"
      
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
      
        tokenizer.save_pretrained(SAVE_DIRECTORY)
        model.save_pretrained(SAVE_DIRECTORY)
        print(f"Model saved to {SAVE_DIRECTORY}")
        ```
	    新涛，到时候你就把这个module上传到抱抱脸或者阿里云的魔搭平台上，到时候我们不传到Git上，不然Git会很慢，有不懂的可以问我

*   **在线推理流程图:**
    ```mermaid
    graph TD
        A["analyze_sentiment(text)"] --> B["使用Tokenizer对文本进行预处理<br>(编码, 补齐, 转换为Tensor)"];
        B --> C["将Tensor输入到已加载的BERT模型中"];
        C --> D["模型进行前向传播 (Inference)"];
        D --> E["获取输出Logits"];
        E --> F["应用Softmax函数将Logits<br>转换为概率分布"];
        F --> G["找到概率最高的标签<br>(e.g., 'confused', 'frustrated')"];
        G --> H["返回情感标签和置信度"];
    ```

*   **实现 (`backend/services/sentiment_analysis_service.py`):**
	  这里的结构不能改，如果要改的话需要先跟我说一下
    ```python
    # backend/services/sentiment_analysis_service.py
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

    class SentimentAnalysisService:
        def __init__(self):
            # **设计决策:** 使用 pipeline 极大地简化了代码。
            # 它封装了从分词到模型推理再到后处理的整个流程。
            # 在应用启动时加载模型到内存。
            model_path = "backend/models/sentiment_bert"
            self.classifier = pipeline(
                "sentiment-analysis", # 或 "text-classification"
                model=model_path,
                tokenizer=model_path
            )
            # 假设我们的模型能输出 'CONFUSED', 'FRUSTRATED', 'NEUTRAL' 等标签
          
        def analyze_sentiment(self, text: str) -> Dict[str, Any]:
            """
            Analyzes the sentiment of a given text.
            Returns a dictionary like {'label': 'CONFUSED', 'score': 0.95}
            """
            if not text.strip():
                return {"label": "NEUTRAL", "score": 1.0}
          
            # pipeline 会处理所有复杂的步骤
            results = self.classifier(text)
            # 返回第一个结果，因为我们只输入了一段文本
            return results[0]

    sentiment_analysis_service = SentimentAnalysisService()
    ```
    **设计决策:** 采用Hugging Face的`pipeline`是最佳实践。它不仅代码简洁，而且经过高度优化，性能良好。

***

**总结:**
`RAGService`通过**向量检索**解决了LLM的幻觉问题。`SentimentAnalysisService`通过**深度学习模型**为AI提供了**情感洞察**，使其能够理解用户的言外之意。这两个服务的实现都遵循了**离线准备**和**在线高效服务**的原则，通过模型预加载和缓存等技术确保了性能。
# scripts/build_knowledge_base.py (使用Annoy)
import json
import os
import sys
from openai import OpenAI
from annoy import AnnoyIndex

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 确保能找到.env文件
import os
from pathlib import Path

# 找到项目根目录并设置环境变量
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

from app.core.config import settings

# 从配置中获取路径
DATA_DIR = settings.DATA_DIR
DOCUMENTS_DIR = settings.DOCUMENTS_DIR
VECTOR_STORE_DIR = settings.VECTOR_STORE_DIR
KB_ANN_PATH = os.path.join(VECTOR_STORE_DIR, settings.KB_ANN_FILENAME)
KB_CHUNKS_JSON_PATH = os.path.join(VECTOR_STORE_DIR, settings.KB_CHUNKS_FILENAME)

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """使用OpenAI客户端获取embeddings，ModelScope API期望字符串而非列表"""
    client = OpenAI(
        base_url=settings.TUTOR_EMBEDDING_API_BASE,
        api_key=settings.TUTOR_EMBEDDING_API_KEY,
    )
    
    embeddings = []
    for text in texts:
        try:
            response = client.embeddings.create(
                model=settings.TUTOR_EMBEDDING_MODEL,
                input=text,  # ModelScope期望单个字符串
                encoding_format="float"
            )
            embeddings.append(response.data[0].embedding)
            
        except Exception as e:
            print(f"API调用错误: '{text[:50]}...': {e}")
            embeddings.append([0.0] * 2560)
    
    return embeddings

def build_knowledge_base(text_chunks):
    # 2. 向量化
    batch_size = 10
    embeddings = []
    
    for i in range(0, len(text_chunks), batch_size):
        batch_texts = text_chunks[i:i+batch_size]
        batch_embeddings = get_embeddings_batch(batch_texts)
        
        # 检查是否有错误
        for j, emb in enumerate(batch_embeddings):
            if not emb:
                print(f"Warning: Failed to get embedding for chunk {i+j}, using zero vector.")
                batch_embeddings[j] = [0.0] * 2560
                
        embeddings.extend(batch_embeddings)
        print(f"Processed batch {i//batch_size + 1}/{(len(text_chunks)-1)//batch_size + 1}")
    
    if not embeddings or not any(embeddings):
        raise ValueError("Failed to get any embeddings from API")
        
    # 验证所有embedding维度一致
    expected_dim = 2560  # Qwen3-Embedding-4B-GGUF的维度
    for i, emb in enumerate(embeddings):
        if len(emb) != expected_dim:
            print(f"Warning: Embedding {i} has dimension {len(emb)}, padding/truncating to {expected_dim}")
            if len(emb) < expected_dim:
                emb.extend([0.0] * (expected_dim - len(emb)))
            else:
                embeddings[i] = emb[:expected_dim]
        
    dimension = len(embeddings[0])

    # 3. 构建Annoy索引
    annoy_index = AnnoyIndex(dimension, 'angular') # 'angular' is recommended for cosine-based embeddings
    for i, vector in enumerate(embeddings):
        annoy_index.add_item(i, vector)

    annoy_index.build(10) # 10棵树，树越多精度越高，但索引越大

    # 4. 保存索引和文本块
    # 确保目录存在
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    
    annoy_index.save(KB_ANN_PATH)
    with open(KB_CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f)
    print(f"Annoy index saved to {KB_ANN_PATH}")
    print(f"Chunks saved to {KB_CHUNKS_JSON_PATH}")

if __name__ == "__main__":
    # 1. 加载并切分文档...
    # 从测试数据文件加载实际的知识库内容
    source_chunks_path = os.path.join(DOCUMENTS_DIR, 'python_basics.json')
    print(f"Loading source chunks from {source_chunks_path}")
    with open(source_chunks_path, "r", encoding="utf-8") as f:
        doc_data = json.load(f)
    
    # 从文档中提取文本内容作为文本块
    text_chunks = [doc_data["text"]]
    
    # 构建知识库
    build_knowledge_base(text_chunks)
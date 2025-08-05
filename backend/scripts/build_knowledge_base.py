# scripts/build_knowledge_base.py (使用Annoy)
import json
import os
import sys
import requests
from annoy import AnnoyIndex

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings

# Define absolute paths based on the script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
KB_ANN_PATH = os.path.join(DATA_DIR, 'kb.ann')
KB_CHUNKS_JSON_PATH = os.path.join(DATA_DIR, 'kb_chunks.json')

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """使用requests批量获取embeddings"""
    embeddings = []
    for text in texts:
        url = f"{settings.EMBEDDING_API_BASE}/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.EMBEDDING_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.EMBEDDING_MODEL,
            "input": text,  # 每次只发送一个文本
            "encoding_format": "float"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            
            if not response_data or "data" not in response_data or not response_data["data"]:
                raise ValueError("No embedding data in response")
                
            embeddings.append(response_data["data"][0]["embedding"])
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling embedding API for text: '{text[:30]}...': {e}")
            embeddings.append([]) # 添加空列表作为占位符
        except (KeyError, IndexError) as e:
            print(f"Error parsing embedding response for text: '{text[:30]}...': {e}")
            embeddings.append([])
    
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
    os.makedirs(DATA_DIR, exist_ok=True)
    
    annoy_index.save(KB_ANN_PATH)
    with open(KB_CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f)
    print(f"Annoy index saved to {KB_ANN_PATH}")
    print(f"Chunks saved to {KB_CHUNKS_JSON_PATH}")

if __name__ == "__main__":
    # 1. 加载并切分文档...
    # 从测试数据文件加载实际的知识库内容
    source_chunks_path = os.path.join(BACKEND_DIR, 'tests', 'backend', 'data', 'kb_chunks.json')
    print(f"Loading source chunks from {source_chunks_path}")
    with open(source_chunks_path, "r", encoding="utf-8") as f:
        text_chunks = json.load(f)
    
    # 构建知识库
    build_knowledge_base(text_chunks)
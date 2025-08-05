# scripts/build_knowledge_base.py (使用Annoy)
import json
import os
import sys
import time
from openai import OpenAI, APITimeoutError
from annoy import AnnoyIndex

# 将项目根目录添加到Python路径，以便导入app模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings

def print_debug_settings():
    """打印用于调试的配置信息"""
    print("\n--- Debug: Current Settings ---")
    print(f"OPENAI_API_KEY (last 4 chars): ...{settings.OPENAI_API_KEY[-4:] if settings.OPENAI_API_KEY else 'Not Set'}")
    print(f"OPENAI_API_BASE: {settings.OPENAI_API_BASE}")
    print(f"EMBEDDING_MODEL: {settings.EMBEDDING_MODEL}")
    print("---------------------------------\n")

def load_and_split_documents():
    """加载并切分文档"""
    # ... (代码不变)
    text_chunks = []
    docs_dir = settings.DOCUMENTS_DIR
    
    if not os.path.isdir(docs_dir):
        print(f"Error: Documents directory not found at '{docs_dir}'")
        return []

    for filename in os.listdir(docs_dir):
        filepath = os.path.join(docs_dir, filename)
        if os.path.isfile(filepath):
            try:
                if filename.endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        paragraphs = content.split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                text_chunks.append(para.strip())
                elif filename.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'text' in data:
                            text_chunks.append(data['text'])
                        elif isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'text' in item:
                                    text_chunks.append(item['text'])
            except Exception as e:
                print(f"Error processing file {filename}: {e}")
    
    return text_chunks

def main():
    # 打印调试信息
    print_debug_settings()

    # 1. 加载并切分文档
    text_chunks = load_and_split_documents()
    if not text_chunks:
        print("No text chunks found. Please add documents to the documents directory.")
        return
    
    print(f"Loaded {len(text_chunks)} text chunks from documents.")

    # 2. 向量化
    print("Connecting to embedding service...")
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_API_BASE,
        timeout=60.0,
    )
    
    embeddings = []
    max_retries = 3
    retry_delay = 5

    for i in range(max_retries):
        try:
            print(f"Attempt {i+1}/{max_retries}: Requesting embeddings with model: {settings.EMBEDDING_MODEL}")
            response = client.embeddings.create(
                input=text_chunks, 
                model=settings.EMBEDDING_MODEL,
                encoding_format="float"
            )
            embeddings = [item.embedding for item in response.data]
            break
        except APITimeoutError:
            print(f"Request timed out. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    
    if not embeddings:
        print("Failed to generate embeddings after several retries.")
        return

    dimension = len(embeddings[0])
    print(f"Generated embeddings for {len(embeddings)} chunks. Dimension: {dimension}")

    # 3. 构建Annoy索引
    annoy_index = AnnoyIndex(dimension, 'angular')
    for i, vector in enumerate(embeddings):
        annoy_index.add_item(i, vector)

    annoy_index.build(10)
    print("Built Annoy index with 10 trees.")

    # 4. 保存索引和文本块
    vector_store_dir = settings.VECTOR_STORE_DIR
    os.makedirs(vector_store_dir, exist_ok=True)
    
    index_file = os.path.join(vector_store_dir, settings.RAG_CONFIG["vector_store"]["index_file"])
    chunks_file = os.path.join(vector_store_dir, settings.RAG_CONFIG["vector_store"]["chunks_file"])
    
    annoy_index.save(index_file)
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f, ensure_ascii=False, indent=4)
        
    print(f"Annoy index saved to {index_file}")
    print(f"Text chunks saved to {chunks_file}")
    print("Knowledge base built successfully.")

if __name__ == "__main__":
    main()

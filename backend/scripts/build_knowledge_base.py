# scripts/build_knowledge_base.py (使用Annoy)
import json
import os
from openai import OpenAI
from annoy import AnnoyIndex
from app.core.config import settings

def load_and_split_documents():
    """加载并切分文档"""
    # 这里简化实现，实际项目中需要根据具体需求实现文档加载和切分逻辑
    text_chunks = []
    
    # 遍历文档目录中的所有文件
    for filename in os.listdir(settings._documents_dir):
        filepath = os.path.join(settings._documents_dir, filename)
        if os.path.isfile(filepath):
            try:
                if filename.endswith('.txt'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 简单按段落切分，实际项目中需要更复杂的切分逻辑
                        paragraphs = content.split('\n\n')
                        for para in paragraphs:
                            if para.strip():
                                text_chunks.append(para.strip())
                elif filename.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 假设JSON文件中有text字段
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
    # 1. 加载并切分文档
    text_chunks = load_and_split_documents()
    if not text_chunks:
        print("No text chunks found. Please add documents to the test_tasks directory.")
        return
    
    print(f"Loaded {len(text_chunks)} text chunks from documents.")

    # 2. 向量化
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.embeddings.create(input=text_chunks, model=settings.EMBEDDING_MODEL)
    embeddings = [item.embedding for item in response.data]
    dimension = len(embeddings[0])
    
    print(f"Generated embeddings for {len(embeddings)} chunks.")

    # 3. 构建Annoy索引
    annoy_index = AnnoyIndex(dimension, 'angular')  # 'angular' is recommended for cosine-based embeddings
    for i, vector in enumerate(embeddings):
        annoy_index.add_item(i, vector)

    annoy_index.build(10)  # 10棵树，树越多精度越高，但索引越大
    
    print("Built Annoy index with 10 trees.")

    # 4. 保存索引和文本块
    index_file = os.path.join(settings._vector_store_dir, settings.RAG_CONFIG["vector_store"]["index_file"])
    chunks_file = os.path.join(settings._vector_store_dir, settings.RAG_CONFIG["vector_store"]["chunks_file"])
    
    # 确保向量存储目录存在
    os.makedirs(settings._vector_store_dir, exist_ok=True)
    
    annoy_index.save(index_file)
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(text_chunks, f)
        
    print(f"Annoy index saved to {index_file}")
    print(f"Text chunks saved to {chunks_file}")
    print("Knowledge base built successfully.")

if __name__ == "__main__":
    main()
# backend/app/services/content_loader.py
import json
from pathlib import Path
from fastapi import HTTPException
from functools import lru_cache

# 获取data目录的绝对路径
DATA_DIR = Path(__file__).parent.parent / "data"

# 使用LRU缓存来避免重复读取文件，提升性能
@lru_cache(maxsize=128)
def load_json_content(content_type: str, topic_id: str) -> dict:
    """
    一个带缓存的函数，用于从JSON文件中加载内容。 
    content_type 应该是 'learning_content' 或 'test_tasks'。
    """
    content_file = DATA_DIR / content_type / f"{topic_id}.json"
    if not content_file.exists():
        raise HTTPException(status_code=404, detail=f"{content_type} for topic '{topic_id}' not found.")

    with open(content_file, "r", encoding="utf-8") as f:
        return json.load(f)
# backend/app/api/endpoints/knowledge_graph.py

from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter()

GRAPH_FILE_PATH = os.path.join("backend", "data", "knowledge_graph.json")

_knowledge_graph_cache = None


@router.get("/knowledge-graph")
def get_knowledge_graph():
    global _knowledge_graph_cache

    if _knowledge_graph_cache is None:
        try:
            with open(GRAPH_FILE_PATH, "r", encoding="utf-8") as f:
                _knowledge_graph_cache = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="知识图谱数据文件未找到")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"知识图谱加载失败: {str(e)}")

    return {
        "code": 0,
        "message": "success",
        "data": _knowledge_graph_cache  # 保持原样返回前端期望结构
    }

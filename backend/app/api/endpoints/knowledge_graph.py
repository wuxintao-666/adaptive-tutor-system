from fastapi import APIRouter, HTTPException
import json
import os
from app.schemas.knowledge_graph import KnowledgeGraph
from app.core.config import settings
from app.schemas.response import StandardResponse

router = APIRouter()

# 使用配置中的DATA_DIR确保路径正确
GRAPH_FILE_PATH = os.path.join(settings.DATA_DIR, "knowledge_graph.json")

_knowledge_graph_cache = None # 全局缓存
_last_loaded_path = None   # 最后一次加载的缓存路径

@router.get("", response_model=StandardResponse[KnowledgeGraph])  # 空路径，因为路由前缀会在api.py中定义
def get_knowledge_graph():
    global _knowledge_graph_cache, _last_loaded_path

    # 如果缓存存在并且路径没变，直接用缓存
    if _knowledge_graph_cache is not None and _last_loaded_path == GRAPH_FILE_PATH:
        return StandardResponse(data=_knowledge_graph_cache)
        
    try:
        # 文件不存在情况
        if not os.path.exists(GRAPH_FILE_PATH):
            _knowledge_graph_cache = KnowledgeGraph(nodes=[], edges=[], dependent_edges=[], metadata=None)
            _last_loaded_path = GRAPH_FILE_PATH
            return StandardResponse(data=_knowledge_graph_cache)  # 返回空数据
            
        # 读取并解析文件
        with open(GRAPH_FILE_PATH) as f:
            try:
                data = json.load(f)
                validated_data = KnowledgeGraph(**data)
                _knowledge_graph_cache = validated_data
                _last_loaded_path = GRAPH_FILE_PATH
                return StandardResponse(data=validated_data)
            except json.JSONDecodeError:
                # JSON 无效时返回 default_node
                _knowledge_graph_cache = KnowledgeGraph(
                    nodes=[{"data": {
                        "id": "default_node",
                        "label": "默认节点",
                        "type": None,
                        "description": None,
                        "difficulty": None
                    }}],
                    edges=[],
                    dependent_edges=[],
                    metadata=None
                )
                _last_loaded_path = GRAPH_FILE_PATH
                return StandardResponse(data=_knowledge_graph_cache)
    except Exception as e:
        # 其他异常
        _knowledge_graph_cache = KnowledgeGraph(nodes=[], edges=[], dependent_edges=[], metadata=None)
        _last_loaded_path = GRAPH_FILE_PATH
        return StandardResponse(data=_knowledge_graph_cache)  # 返回空数据

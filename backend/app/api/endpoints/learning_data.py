# backend/app/api/endpoints/learning_data.py
import json
import logging
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request

# 使用前缀统一版本管理,可修改
router = APIRouter(prefix='/api/v1')

# 配置日志
logger = logging.getLogger(__name__)

# 定义路径
CATALOG_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_graph.json"

# 这个文件现在为空，因为所有API都已被删除

 
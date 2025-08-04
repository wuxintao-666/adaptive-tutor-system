# backend/app/api/endpoints/learing-content.py
import json
import html
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, BaseLoader

# 使用前缀统一版本管理,可修改
router = APIRouter(prefix='/api/v1')

# 学习内容数据目录
LEARNING_CONTENT_DIR = Path(__file__).parent.parent.parent / "data" / "learning_content"


@router.get("/learning-content/{topic_id}", response_model=StandardResponse[LearningContent])
def get_learning_content(topic_id: str):
    # TODO: 学习内容传传递
  """
  Retrieves learning materials for a specific topic.
  """
  content_data = load_json_content("learning_content", topic_id)
  return StandardResponse(data=content_data)


@router.get("/test-tasks/{topic_id}", response_model=StandardResponse[TestTask])
def get_test_task(topic_id: str):
    # TODO: 测试任务传递
  """
  Retrieves the test task for a specific topic.
  """
  content_data = load_json_content("test_tasks", topic_id)
  return StandardResponse(data=content_data)
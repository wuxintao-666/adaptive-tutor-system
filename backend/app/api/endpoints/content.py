import json
import html
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, BaseLoader
from app.schemas.response import StandardResponse
from app.schemas.content import LearningContent, TestTask
from app.services.content_loader import load_json_content

# 使用前缀统一版本管理,可修改
router = APIRouter()


@router.get("/learning-content/{topic_id}", response_model=StandardResponse[LearningContent])
def get_learning_content(topic_id: str):
    """
    Retrieves learning materials for a specific topic.
    """
    try:
        content_data = load_json_content("learning_content", topic_id)
        return StandardResponse(data=content_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/test-tasks/{topic_id}", response_model=StandardResponse[TestTask])
def get_test_task(topic_id: str):
    """
    Retrieves the test task for a specific topic.
    """
    try:
        content_data = load_json_content("test_tasks", topic_id)
        return StandardResponse(data=content_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
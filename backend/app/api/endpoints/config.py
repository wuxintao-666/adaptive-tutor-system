from fastapi import APIRouter
from typing import Dict, Any
from ...schemas.response import StandardResponse

router = APIRouter()


@router.get("/config")
async def get_config() -> StandardResponse[Dict[str, Any]]:
    """
    获取前端配置信息

    Returns:
        StandardResponse[Dict[str, Any]]: 前端配置
    """
    config = {
        "api_base_url": "/api/v1",
        "model_name_for_display": "Qwen-Turbo (魔搭)",
        "features": {
            "ai_chat": True,
            "knowledge_graph": True,
            "code_testing": True,
            "sentiment_analysis": True
        },
        "ui": {
            "theme": "light",
            "language": "zh-CN"
        }
    }
    
    return StandardResponse(
        code=200,
        message="Configuration retrieved successfully",
        data=config
    )
# backend/app/api/endpoints/config.py
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.config import FrontendConfig
from app.schemas.response import StandardResponse # 使用标准响应

# 使用前缀统一版本管理,可修改
router = APIRouter(prefix='/api/v1')

@router.get("/config", response_model=StandardResponse[FrontendConfig])
def get_frontend_config():
        """
        Provides a safe, non-sensitive set of configuration
        variables to the frontend application.
        """
        config_data = FrontendConfig(
                # model_name_for_display=settings.OPENAI_MODEL
        )
        return StandardResponse(data=config_data)
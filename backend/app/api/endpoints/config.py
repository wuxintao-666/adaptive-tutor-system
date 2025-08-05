from fastapi import APIRouter
from app.core.config import settings
from app.schemas.config import FrontendConfig
from app.schemas.response import StandardResponse # 使用标准响应格式

# 使用前缀统一版本管理,可修改
router = APIRouter(prefix='/api/v1')

@router.get("/config", response_model=StandardResponse[FrontendConfig])
def get_frontend_config():
        """
        为前端应用程序提供安全、非敏感的配置变量集合。
        """
        config_data = FrontendConfig(
                # 用于显示的模型名称=settings.OPENAI_MODEL
        )
        return StandardResponse(data=config_data)
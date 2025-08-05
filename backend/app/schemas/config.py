# backend/app/schemas/config.py
from pydantic import BaseModel

class FrontendConfig(BaseModel):
        """
        Defines the non-sensitive configuration variables
        that will be exposed to the frontend.
        """
        # API基础URL，供前端使用
        api_base_url: str
        
        # 示例: 如果前端需要知道当前实验使用的模型名（非敏感）
        # model_name_for_display: str
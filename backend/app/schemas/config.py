from pydantic import BaseModel

class FrontendConfig(BaseModel):
    """
    前端配置模型

    定义向前端暴露的非敏感配置变量，用于前端连接后端API和获取配置信息。

    Attributes:
        api_base_url: API基础URL，供前端使用，用于构建完整的API请求地址
    """
    # API基础URL，供前端使用
    api_base_url: str

    # 示例: 如果前端需要知道当前实验使用的模型名（非敏感）
    # model_name_for_display: str
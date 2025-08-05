# 依赖注入配置示例

from app.services.sandbox_service_improved import SandboxService, DefaultPlaywrightManager
from app.services.user_state_service import UserStateService
from app.services.sentiment_analysis_service import sentiment_analysis_service
from app.services.llm_gateway import llm_gateway
from app.services.prompt_generator import prompt_generator
from app.services.dynamic_controller import dynamic_controller
# from app.services.rag_service import rag_service  # 暂时注释，等待RAG模块修复


class ProductionConfig:
    """生产环境配置"""
    @staticmethod
    def create_sandbox_service():
        return SandboxService(
            playwright_manager=DefaultPlaywrightManager(),
            headless=True
        )


class DevelopmentConfig:
    """开发环境配置"""
    @staticmethod
    def create_sandbox_service():
        return SandboxService(
            playwright_manager=DefaultPlaywrightManager(),
            headless=False  # 开发环境使用有头模式便于调试
        )


class TestingConfig:
    """测试环境配置"""
    @staticmethod
    def create_sandbox_service(mock_playwright_manager):
        return SandboxService(
            playwright_manager=mock_playwright_manager,
            headless=True
        )


# 应用启动时根据环境选择配置
import os

def get_sandbox_service():
    """根据环境变量获取合适的沙箱服务实例"""
    env = os.getenv('APP_ENV', 'production')
    
    if env == 'development':
        return DevelopmentConfig.create_sandbox_service()
    elif env == 'testing':
        # 在测试环境中，会传入模拟的 Playwright 管理器
        return None  # 实际测试中会传入模拟对象
    else:
        return ProductionConfig.create_sandbox_service()


# 使用示例
if __name__ == "__main__":
    # 生产环境使用
    sandbox_service = get_sandbox_service()
    
    # 开发环境使用 (设置环境变量)
    # os.environ['APP_ENV'] = 'development'
    # sandbox_service = get_sandbox_service()

# --- UserStateService 依赖注入 ---


# 在应用启动时创建 UserStateService 的单例
# 这确保了所有用户的状态都保存在同一个内存缓存中
user_state_service_instance = UserStateService()

def get_user_state_service() -> UserStateService:
    """
    一个简单的依赖项，用于在整个应用中共享同一个UserStateService实例。
    """
    return user_state_service_instance


# --- AI服务依赖注入 ---

def get_sentiment_analysis_service():
    """
    获取情感分析服务实例
    """
    return sentiment_analysis_service


def get_llm_gateway():
    """
    获取LLM网关服务实例
    """
    return llm_gateway


def get_prompt_generator():
    """
    获取提示词生成器实例
    """
    return prompt_generator


def get_dynamic_controller():
    """
    获取动态控制器实例
    """
    return dynamic_controller


def get_rag_service():
    """
    获取RAG服务实例（暂时禁用）
    """
    return None  # 暂时返回None，等待RAG模块修复


# --- 服务验证函数 ---

def validate_all_services() -> dict:
    """
    验证所有服务的状态
    
    Returns:
        dict: 服务状态字典
    """
    return {
        'user_state_service': True,  # 本地服务，总是可用
        'sentiment_analysis_service': True,  # 本地服务，总是可用
        'llm_gateway': llm_gateway.validate_connection(),
        'prompt_generator': True,  # 本地服务，总是可用
        'dynamic_controller': True,  # 本地服务，总是可用
        'rag_service': False,  # 暂时禁用，等待RAG模块修复
        'sandbox_service': get_sandbox_service() is not None
    }

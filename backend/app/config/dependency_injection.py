# 依赖注入配置示例

from app.services.sandbox_service_improved import SandboxService, DefaultPlaywrightManager
from app.services.user_state_service import UserStateService


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

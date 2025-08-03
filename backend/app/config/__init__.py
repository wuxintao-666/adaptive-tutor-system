# 依赖注入配置示例

from backend.app.services.sandbox_service_improved import SandboxService, DefaultPlaywrightManager
import os


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


# 默认实例
sandbox_service = get_sandbox_service()
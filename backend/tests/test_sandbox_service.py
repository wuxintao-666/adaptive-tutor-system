import pytest
from unittest.mock import Mock, MagicMock
from backend.app.services.sandbox_service import SandboxService


# 模拟的 Playwright 管理器
class MockPlaywrightManager:
    def __init__(self):
        self.browser = Mock()
        self.page = Mock()
        self.playwright = Mock()
        self.playwright.chromium.launch.return_value = self.browser
        self.browser.new_page.return_value = self.page

    def __enter__(self):
        return self.playwright

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_sandbox_service_initialization():
    """测试沙箱服务初始化"""
    # 测试默认初始化
    service = SandboxService()
    assert service._headless == True

    # 测试带参数初始化
    service = SandboxService(headless=False)
    assert service._headless == False


def test_run_evaluation_success():
    """测试成功运行评估"""
    # 创建模拟的 Playwright 管理器
    mock_manager = MockPlaywrightManager()
    
    # 创建服务实例并注入模拟依赖
    service = SandboxService(playwright_manager=mock_manager, headless=False)
    
    # 准备测试数据
    user_code = {
        'html': '<div id="test">Hello</div>',
        'css': '#test { color: red; }',
        'js': 'console.log("test");'
    }
    
    checkpoints = [
        {
            'type': 'assert_text_content',
            'selector': '#test',
            'assertion_type': 'contains',
            'value': 'Hello'
        }
    ]
    
    # 运行评估
    result = service.run_evaluation(user_code, checkpoints)
    
    # 验证结果
    assert isinstance(result, dict)
    assert 'passed' in result
    assert 'message' in result
    assert 'details' in result
    
    # 验证 Playwright 调用
    mock_manager.playwright.chromium.launch.assert_called_once_with(headless=False)
    mock_manager.browser.new_page.assert_called_once()
    mock_manager.browser.close.assert_called_once()


def test_run_evaluation_with_interaction():
    """测试带有交互的评估"""
    mock_manager = MockPlaywrightManager()
    service = SandboxService(playwright_manager=mock_manager)
    
    user_code = {
        'html': '<button id="btn">Click me</button>',
        'css': '',
        'js': 'document.getElementById("btn").addEventListener("click", () => { document.getElementById("btn").textContent = "Clicked!"; });'
    }
    
    checkpoints = [
        {
            'type': 'interaction_and_assert',
            'action_type': 'click',
            'action_selector': '#btn',
            'assertion': {
                'type': 'assert_text_content',
                'selector': '#btn',
                'assertion_type': 'contains',
                'value': 'Clicked!'
            }
        }
    ]
    
    result = service.run_evaluation(user_code, checkpoints)
    
    # 验证按钮点击被调用
    mock_manager.page.locator.assert_called_with('#btn')
    mock_manager.page.locator.return_value.click.assert_called_once()


def test_run_evaluation_playwright_error():
    """测试 Playwright 错误处理"""
    mock_manager = MockPlaywrightManager()
    # 模拟 Playwright 错误
    mock_manager.playwright.chromium.launch.side_effect = Exception("Playwright error")
    
    service = SandboxService(playwright_manager=mock_manager)
    
    user_code = {'html': '', 'css': '', 'js': ''}
    checkpoints = []
    
    result = service.run_evaluation(user_code, checkpoints)
    
    assert result['passed'] == False
    assert "评测服务发生内部错误" in result['message']


# 模拟的断言评估器，用于测试私有方法
class MockAssertionEvaluator:
    @staticmethod
    def evaluate_assertion(page, assertion):
        if assertion.get('should_pass', True):
            return True, "通过"
        else:
            return False, "断言失败"


def test_evaluate_checkpoint_interaction():
    """测试检查点评估 - 交互类型"""
    service = SandboxService()
    
    # 使用魔术方法直接测试私有方法
    page = Mock()
    
    checkpoint = {
        'type': 'interaction_and_assert',
        'action_type': 'click',
        'action_selector': '#test-btn',
        'assertion': {
            'type': 'assert_text_content',
            'selector': '#result',
            'assertion_type': 'contains',
            'value': 'Success'
        }
    }
    
    # 由于 _evaluate_assertion 是私有方法且返回静态值，我们直接验证调用
    result = service._evaluate_checkpoint(page, checkpoint)
    
    # 验证页面元素被定位和点击
    page.locator.assert_called_with('#test-btn')
    page.locator.return_value.click.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
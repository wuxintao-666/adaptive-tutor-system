import pytest
from unittest.mock import MagicMock, patch, ANY

# 将 backend 目录添加到 sys.path 中，以便能够导入 app 中的模块
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from app.services.sandbox_service import SandboxService, DefaultPlaywrightManager

# 模拟 Playwright 的 Page 对象，这是测试的核心
@pytest.fixture
def mock_page():
    """创建一个模拟的 Playwright Page 对象。"""
    page = MagicMock()
    # 默认情况下，让 evaluate 和 locator 的行为是成功的
    page.evaluate.return_value = True
    # locator().click() 等交互方法应该不返回任何东西
    page.locator.return_value.click.return_value = None
    page.locator.return_value.fill.return_value = None
    # text_content() 应该返回一个可预期的字符串
    page.locator.return_value.text_content.return_value = "Expected Text"
    return page

# 模拟 Playwright 的 Browser 对象
@pytest.fixture
def mock_browser(mock_page):
    """创建一个模拟的 Playwright Browser 对象。"""
    browser = MagicMock()
    browser.new_page.return_value = mock_page
    return browser

# 模拟 Playwright 的主入口
@pytest.fixture
def mock_playwright_manager(mock_browser):
    """创建一个模拟的 Playwright 管理器，用于注入到 SandboxService 中。"""
    playwright = MagicMock()
    playwright.chromium.launch.return_value = mock_browser

    # 这个上下文管理器模拟 'with sync_playwright() as p:'
    manager = MagicMock()
    manager.__enter__.return_value = playwright
    
    # 包装成 DefaultPlaywrightManager 的模拟实例
    mock_manager_instance = MagicMock(spec=DefaultPlaywrightManager)
    mock_manager_instance.__enter__.return_value = playwright
    mock_manager_instance.__exit__.return_value = None
    return mock_manager_instance

# --- 测试用例开始 ---

class TestSandboxService:
    """针对 SandboxService 的单元测试套件"""

    def test_run_evaluation_success(self, mock_playwright_manager, mock_page):
        """
        测试用例1: 一个快乐的路径，所有检查点都成功通过。
        """
        # 1. 准备
        # 使用模拟的 Playwright 管理器初始化 SandboxService
        service = SandboxService(playwright_manager=mock_playwright_manager)
        
        # 配置mock_page的行为
        mock_page.locator.return_value.text_content.return_value = "Hello"
        mock_page.locator.return_value.evaluate.return_value = False
        
        user_code = {"html": "<h1>Hello</h1>", "css": "", "js": ""}
        
        # 定义两个简单的检查点
        checkpoints = [
            {
                "type": "assert_text_content",
                "selector": "h1",
                "assertion_type": "contains",
                "value": "Hello"
            },
            {
                "type": "assert_attribute",
                "selector": "h1",
                "attribute": "id",
                "assertion_type": "not_exists"
            }
        ]

        # 2. 执行
        result = service.run_evaluation(user_code, checkpoints)

        # 3. 断言
        assert result["passed"] is True
        assert "恭喜！所有测试点都通过了！" in result["message"]
        assert len(result["details"]) == 0

        # 验证 Playwright 的核心方法被正确调用
        mock_playwright_manager.__enter__.assert_called_once()
        playwright_instance = mock_playwright_manager.__enter__.return_value
        playwright_instance.chromium.launch.assert_called_once()
        browser_instance = playwright_instance.chromium.launch.return_value
        browser_instance.new_page.assert_called_once()
        browser_instance.close.assert_called_once()
        
        # 验证 set_content 被调用来加载用户代码
        page_instance = browser_instance.new_page.return_value
        page_instance.set_content.assert_called_once()
        # 我们可以检查传递给 set_content 的内容是否包含了用户的 HTML
        call_args, _ = page_instance.set_content.call_args
        assert "<h1>Hello</h1>" in call_args[0]

    def test_run_evaluation_failure(self, mock_playwright_manager, mock_page):
        """
        测试用例2: 当有检查点失败时的场景。
        """
        # 1. 准备
        # 配置模拟的 page 对象，使其在第二次评估时失败
        mock_page.locator.return_value.text_content.side_effect = [
            "Correct Text", # 第一次调用成功
            "Correct Text" # 第二次调用也成功，但会触发contains检查失败
        ]

        service = SandboxService(playwright_manager=mock_playwright_manager)
        user_code = {"html": "<h1>Wrong Text</h1>", "css": "", "js": ""}
        
        checkpoints = [
            {
                "type": "assert_text_content", "selector": "h1",
                "assertion_type": "contains", "value": "Correct"
            },
            {
                "type": "assert_text_content", "selector": "h1",
                "assertion_type": "contains", "value": "Expected but not present"
            }
        ]
        
        # 2. 执行
        result = service.run_evaluation(user_code, checkpoints)
        
        # 3. 断言
        assert result["passed"] is False
        assert "很遗憾，部分测试点未通过。" in result["message"]
        assert len(result["details"]) == 1
        # 检查失败详情是否包含了预期的错误信息
        assert "检查点 2 失败" in result["details"][0]
        assert "不包含 'Expected but not present'" in result["details"][0]

    def test_run_evaluation_playwright_error(self, mock_playwright_manager):
        """
        测试用例3: 当 Playwright 自身发生错误时的场景。
        """
        # 1. 准备
        # 配置模拟的 playwright 管理器，使其在启动浏览器时就抛出异常
        from playwright.sync_api import Error
        playwright_instance = mock_playwright_manager.__enter__.return_value
        playwright_instance.chromium.launch.side_effect = Error("模拟 Playwright 启动失败")

        service = SandboxService(playwright_manager=mock_playwright_manager)
        user_code = {"html": "<h1>Hello</h1>", "css": "", "js": ""}
        checkpoints = [{"type": "assert_text_content", "selector": "h1", "assertion_type": "contains", "value": "Hello"}]

        # 2. 执行
        result = service.run_evaluation(user_code, checkpoints)

        # 3. 断言
        assert result["passed"] is False
        assert "评测服务发生内部错误" in result["message"]
        assert len(result["details"]) == 1
        assert "模拟 Playwright 启动失败" in result["details"][0]

    def test_interaction_and_assert_checkpoint(self, mock_playwright_manager, mock_page):
        """
        测试用例4: 验证 'interaction_and_assert' 检查点是否能正确工作。
        """
        # 1. 准备
        service = SandboxService(playwright_manager=mock_playwright_manager)
        
        user_code = {
            "html": "<button id='btn'>Click Me</button><p id='text'>Initial</p>",
            "js": "document.getElementById('btn').onclick = () => document.getElementById('text').innerText = 'Changed';"
        }
        
        checkpoints = [
            {
                "type": "interaction_and_assert",
                "action_type": "click",
                "action_selector": "#btn",
                "assertion": {
                    "type": "assert_text_content",
                    "selector": "#text",
                    "assertion_type": "contains",
                    "value": "Changed"
                }
            }
        ]
        
        # 当 text_content 被调用时，我们让它返回 "Changed"，模拟点击事件成功改变了文本
        mock_page.locator.return_value.text_content.return_value = "Changed"

        # 2. 执行
        result = service.run_evaluation(user_code, checkpoints)

        # 3. 断言
        assert result["passed"] is True
        assert "恭喜！" in result["message"]
        
        # 验证交互和断言是否都按预期执行了
        # 验证点击动作
        mock_page.locator.assert_any_call("#btn")
        mock_page.locator.return_value.click.assert_called_once()
        
        # 验证断言
        mock_page.locator.assert_any_call("#text")
        mock_page.locator.return_value.text_content.assert_called_once()

# 使用 parametrize 来高效测试多种断言情况
@pytest.mark.parametrize("assertion, mock_page_config, expected_result, expected_message", [
    # --- assert_text_content ---
    # 成功: contains
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "contains", "value": "llo"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     True, "通过"),
    # 失败: contains
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "contains", "value": "world"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     False, "不包含 'world'"),
    # 成功: equals
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "equals", "value": "Hello"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     True, "通过"),
    # 失败: equals
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "equals", "value": "hello"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     False, "不等于期望的"),
    # 成功: matches_regex
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "matches_regex", "value": "H.*o"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     True, "通过"),
    # 失败: matches_regex
    ({"type": "assert_text_content", "selector": "#t", "assertion_type": "matches_regex", "value": "\\d+"}, 
     {"locator.return_value.text_content.return_value": "Hello"}, 
     False, "不匹配正则表达式"),

    # --- assert_attribute ---
    # 成功: exists
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "exists"},
     {"locator.return_value.evaluate.return_value": True},
     True, "通过"),
    # 失败: exists
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "exists"},
     {"locator.return_value.evaluate.return_value": False},
     False, "没有属性 'href'"),
    # 成功: not_exists
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "not_exists"},
     {"locator.return_value.evaluate.return_value": False},
     True, "通过"),
    # 失败: not_exists
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "not_exists"},
     {"locator.return_value.evaluate.return_value": True},
     False, "不应该有属性 'href'"),
    # 成功: equals
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "equals", "value": "https://example.com"},
     {"locator.return_value.count.return_value": 1, "locator.return_value.evaluate.return_value": "https://example.com"}, # count, getAttribute
     True, "通过"),
    # 失败: equals
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "equals", "value": "https://wrong.com"},
     {"locator.return_value.count.return_value": 1, "locator.return_value.evaluate.return_value": "https://example.com"},
     False, "期望值为 'https://wrong.com'"),
    # 成功: contains
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "contains", "value": "example"},
     {"locator.return_value.count.return_value": 1, "locator.return_value.evaluate.return_value": "https://example.com"},
     True, "通过"),
    # 失败: contains
    ({"type": "assert_attribute", "selector": "a", "attribute": "href", "assertion_type": "contains", "value": "wrong"},
     {"locator.return_value.count.return_value": 1, "locator.return_value.evaluate.return_value": "https://example.com"},
     False, "不包含期望值"),

    # --- assert_style ---
    # 成功: equals (颜色)
    ({"type": "assert_style", "selector": "p", "css_property": "color", "assertion_type": "equals", "value": "rgb(255, 0, 0)"},
     {"locator.return_value.evaluate.return_value": "rgb(255, 0, 0)"},
     True, "通过"),
    # 失败: equals (颜色)
    ({"type": "assert_style", "selector": "p", "css_property": "color", "assertion_type": "equals", "value": "blue"},
     {"locator.return_value.evaluate.return_value": "rgb(255, 0, 0)"},
     False, "不满足 'equals blue'"),
    # 成功: greater_than
    ({"type": "assert_style", "selector": "p", "css_property": "font-size", "assertion_type": "greater_than", "value": "16px"},
     {"locator.return_value.evaluate.return_value": "18px"},
     True, "通过"),
    # 失败: greater_than
    ({"type": "assert_style", "selector": "p", "css_property": "font-size", "assertion_type": "greater_than", "value": "20px"},
     {"locator.return_value.evaluate.return_value": "18px"},
     False, "不满足 'greater_than 20px'"),
    # 成功: less_than
    ({"type": "assert_style", "selector": "p", "css_property": "font-size", "assertion_type": "less_than", "value": "20px"},
     {"locator.return_value.evaluate.return_value": "18px"},
     True, "通过"),
    # 失败: less_than
    ({"type": "assert_style", "selector": "p", "css_property": "font-size", "assertion_type": "less_than", "value": "16px"},
     {"locator.return_value.evaluate.return_value": "18px"},
     False, "不满足 'less_than 16px'"),
    # 成功: contains (样式值包含)
    ({"type": "assert_style", "selector": "p", "css_property": "font-family", "assertion_type": "contains", "value": "Arial"},
     {"locator.return_value.evaluate.return_value": "Arial, sans-serif"},
     True, "通过"),
    # 失败: contains (样式值包含)
    ({"type": "assert_style", "selector": "p", "css_property": "font-family", "assertion_type": "contains", "value": "Times"},
     {"locator.return_value.evaluate.return_value": "Arial, sans-serif"},
     False, "不满足 'contains Times'"),

    # --- custom_script ---
    # 成功: 返回 true
    ({"type": "custom_script", "script": "return true"},
     {"evaluate.return_value": True},
     True, "通过"),
    # 失败: 返回 false
    ({"type": "custom_script", "script": "return false"},
     {"evaluate.return_value": False},
     False, "返回结果为 False"),
    # 成功: 复杂逻辑
    ({"type": "custom_script", "script": "return document.querySelector('div') !== null"},
     {"evaluate.return_value": True},
     True, "通过"),
])
def test_all_assertion_types(mock_page, assertion, mock_page_config, expected_result, expected_message):
    """
    测试用例5: 验证 _evaluate_assertion 方法能正确处理所有类型的断言。
    """
    # 1. 准备
    # 根据参数动态配置 mock_page
    for config_key, config_value in mock_page_config.items():
        # 使用 exec 来动态设置 mock 的属性，例如 mock_page.locator.return_value.text_content.return_value = "Hello"
        # 这是一种灵活配置复杂 mock 对象的方法
        exec(f"mock_page.{config_key} = config_value", {'mock_page': mock_page, 'config_value': config_value})

    service = SandboxService() # 我们是直接测试私有方法，所以不需要 playwright_manager

    # 2. 执行
    passed, detail = service._evaluate_assertion(mock_page, assertion)

    # 3. 断言
    assert passed is expected_result
    assert expected_message in detail


def test_edge_cases(mock_page):
    """
    测试用例6: 测试边界情况和错误处理
    """
    service = SandboxService()
    
    # 测试元素不存在的情况
    mock_page.locator.return_value.count.return_value = 0
    
    # 测试属性断言 - 元素不存在
    passed, detail = service._evaluate_assertion(mock_page, {
        "type": "assert_attribute",
        "selector": ".non-existent",
        "attribute": "href",
        "assertion_type": "exists"
    })
    assert passed is False
    assert "找不到匹配选择器" in detail
    
    # 测试属性断言 - 获取不存在的属性值
    mock_page.locator.return_value.count.return_value = 1
    mock_page.locator.return_value.evaluate.return_value = None
    
    passed, detail = service._evaluate_assertion(mock_page, {
        "type": "assert_attribute",
        "selector": "a",
        "attribute": "data-non-existent",
        "assertion_type": "equals",
        "value": "test"
    })
    assert passed is False
    assert "没有属性 'data-non-existent'" in detail
    
    # 测试文本内容断言 - 元素不存在
    mock_page.locator.return_value.text_content.side_effect = Exception("Element not found")
    
    passed, detail = service._evaluate_assertion(mock_page, {
        "type": "assert_text_content",
        "selector": ".non-existent",
        "assertion_type": "contains",
        "value": "test"
    })
    assert passed is False
    assert "找不到或无法获取选择器" in detail

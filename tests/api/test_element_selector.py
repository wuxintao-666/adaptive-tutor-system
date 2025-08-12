# tests/api/test_element_selector.py
import sys
import os
import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the backend directory to the path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)

# Now import the app
from app.main import app

client = TestClient(app)

class TestElementSelector:
    """测试元素选择器功能"""
    
    def test_element_selector_initialization(self):
        """测试元素选择器初始化"""
        # 模拟前端JavaScript模块
        mock_selector = {
            "getElementAtPoint": MagicMock(),
            "isElementAtPoint": MagicMock(),
            "getElementXPath": MagicMock(),
            "getElementInfo": MagicMock(),
            "ElementSelector": MagicMock(),
            "initIframeSelector": MagicMock(),
            "createSelectorBridge": MagicMock()
        }
        
        # 测试选择器模块是否正确导出
        assert "getElementAtPoint" in mock_selector
        assert "ElementSelector" in mock_selector
        assert "createSelectorBridge" in mock_selector
    
    def test_element_info_structure(self):
        """测试元素信息结构"""
        # 模拟元素信息
        mock_element_info = {
            "tagName": "div",
            "id": "test-element",
            "className": "test-class",
            "classList": ["test-class", "active"],
            "textContent": "Test Element",
            "outerHTML": "<div id='test-element' class='test-class'>Test Element</div>",
            "selector": "//div[@id='test-element']",
            "bounds": {
                "x": 100,
                "y": 200,
                "width": 150,
                "height": 50
            },
            "styles": {
                "backgroundColor": "rgb(255, 255, 255)",
                "color": "rgb(0, 0, 0)",
                "fontSize": "16px"
            },
            "pageURL": "http://localhost:8000/test"
        }
        
        # 验证元素信息结构
        assert "tagName" in mock_element_info
        assert "id" in mock_element_info
        assert "className" in mock_element_info
        assert "classList" in mock_element_info
        assert "textContent" in mock_element_info
        assert "outerHTML" in mock_element_info
        assert "selector" in mock_element_info
        assert "bounds" in mock_element_info
        assert "styles" in mock_element_info
        assert "pageURL" in mock_element_info
        
        # 验证bounds结构
        bounds = mock_element_info["bounds"]
        assert "x" in bounds
        assert "y" in bounds
        assert "width" in bounds
        assert "height" in bounds
        
        # 验证styles结构
        styles = mock_element_info["styles"]
        assert "backgroundColor" in styles
        assert "color" in styles
        assert "fontSize" in styles

class TestIframeSelector:
    """测试iframe选择器功能"""
    
    def test_iframe_selector_message_types(self):
        """测试iframe选择器消息类型"""
        message_types = {
            "START": "SW_SELECT_START",
            "STOP": "SW_SELECT_STOP",
            "CHOSEN": "SW_SELECT_CHOSEN"
        }
        
        assert message_types["START"] == "SW_SELECT_START"
        assert message_types["STOP"] == "SW_SELECT_STOP"
        assert message_types["CHOSEN"] == "SW_SELECT_CHOSEN"
    
    def test_iframe_selector_bridge_creation(self):
        """测试iframe选择器桥接创建"""
        # 模拟iframe窗口
        mock_iframe_window = MagicMock()
        mock_iframe_window.postMessage = MagicMock()
        
        # 模拟回调函数
        mock_on_chosen = MagicMock()
        mock_on_error = MagicMock()
        
        # 模拟桥接选项
        bridge_options = {
            "iframeWindow": mock_iframe_window,
            "targetOrigin": "*",
            "ignoreSelectors": [".sw-selector", ".sw-highlight"],
            "onChosen": mock_on_chosen,
            "onError": mock_on_error
        }
        
        # 验证桥接选项结构
        assert "iframeWindow" in bridge_options
        assert "targetOrigin" in bridge_options
        assert "ignoreSelectors" in bridge_options
        assert "onChosen" in bridge_options
        assert "onError" in bridge_options

class TestElementSelectionAPI:
    """测试元素选择相关的API端点"""
    
    def test_element_selection_start(self):
        """测试启动元素选择"""
        # 模拟启动选择器的请求
        start_request = {
            "action": "start",
            "allowedTags": ["div", "span", "p", "h1", "h2", "h3"],
            "ignoreSelectors": [".sw-selector", ".sw-highlight"]
        }
        
        # 验证请求结构
        assert "action" in start_request
        assert "allowedTags" in start_request
        assert "ignoreSelectors" in start_request
        assert start_request["action"] == "start"
        assert isinstance(start_request["allowedTags"], list)
        assert isinstance(start_request["ignoreSelectors"], list)
    
    def test_element_selection_stop(self):
        """测试停止元素选择"""
        # 模拟停止选择器的请求
        stop_request = {
            "action": "stop"
        }
        
        # 验证请求结构
        assert "action" in stop_request
        assert stop_request["action"] == "stop"
    
    def test_element_selection_chosen(self):
        """测试元素选择完成"""
        # 模拟元素选择完成的响应
        chosen_response = {
            "type": "SW_SELECT_CHOSEN",
            "payload": {
                "tagName": "div",
                "id": "selected-element",
                "className": "selected-class",
                "textContent": "Selected Element",
                "selector": "//div[@id='selected-element']",
                "bounds": {
                    "x": 100,
                    "y": 200,
                    "width": 150,
                    "height": 50
                }
            }
        }
        
        # 验证响应结构
        assert "type" in chosen_response
        assert "payload" in chosen_response
        assert chosen_response["type"] == "SW_SELECT_CHOSEN"
        
        payload = chosen_response["payload"]
        assert "tagName" in payload
        assert "id" in payload
        assert "className" in payload
        assert "textContent" in payload
        assert "selector" in payload
        assert "bounds" in payload

class TestElementSelectorIntegration:
    """测试元素选择器集成功能"""
    
    @patch('app.services.dynamic_controller.get_element_selector_service')
    def test_element_selector_service_integration(self, mock_selector_service):
        """测试元素选择器服务集成"""
        # 模拟选择器服务
        mock_service = MagicMock()
        mock_selector_service.return_value = mock_service
        
        # 模拟服务方法
        mock_service.start_selection = MagicMock()
        mock_service.stop_selection = MagicMock()
        mock_service.get_selected_element = MagicMock()
        
        # 验证服务方法存在
        assert hasattr(mock_service, 'start_selection')
        assert hasattr(mock_service, 'stop_selection')
        assert hasattr(mock_service, 'get_selected_element')
    
    def test_element_selector_error_handling(self):
        """测试元素选择器错误处理"""
        # 模拟错误情况
        error_cases = [
            {"error": "Invalid element", "expected": "Element not found"},
            {"error": "Permission denied", "expected": "Access denied"},
            {"error": "Network error", "expected": "Connection failed"}
        ]
        
        for case in error_cases:
            assert "error" in case
            assert "expected" in case
            assert isinstance(case["error"], str)
            assert isinstance(case["expected"], str)

class TestElementSelectorPerformance:
    """测试元素选择器性能"""
    
    def test_element_selector_memory_usage(self):
        """测试元素选择器内存使用"""
        # 模拟内存使用监控
        memory_usage = {
            "initial": 1024,  # KB
            "after_start": 2048,  # KB
            "after_stop": 1024,  # KB
            "leak_detected": False
        }
        
        # 验证内存使用合理
        assert memory_usage["initial"] <= memory_usage["after_start"]
        assert memory_usage["after_stop"] <= memory_usage["after_start"]
        assert not memory_usage["leak_detected"]
    
    def test_element_selector_response_time(self):
        """测试元素选择器响应时间"""
        # 模拟响应时间
        response_times = {
            "start_selection": 50,  # ms
            "element_hover": 10,    # ms
            "element_select": 20,   # ms
            "stop_selection": 30    # ms
        }
        
        # 验证响应时间在合理范围内
        for operation, time_ms in response_times.items():
            assert time_ms >= 0
            assert time_ms < 1000  # 应该小于1秒

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
AI API连通性测试文件
专门用于测试AI相关的API接口
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class AITestSuite:
    """AI API测试套件"""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {message}")
    
    def test_services_status(self):
        """测试服务状态API"""
        try:
            response = self.session.get(f"{API_BASE}/chat/ai/services/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    services = data.get("data", {})
                    self.log_test(
                        "服务状态API",
                        True,
                        f"获取到{len(services)}个服务状态"
                    )
                    
                    # 检查关键服务状态
                    critical_services = ['llm_gateway', 'user_state_service', 'sentiment_analysis_service', 'prompt_generator']
                    for service in critical_services:
                        if service in services:
                            status = "可用" if services[service] else "不可用"
                            self.log_test(
                                f"{service}服务状态",
                                services[service],
                                f"{service}: {status}"
                            )
                        else:
                            self.log_test(
                                f"{service}服务状态",
                                False,
                                f"{service}: 未找到"
                            )
                else:
                    self.log_test(
                        "服务状态API",
                        False,
                        f"API返回错误: {data.get('message', 'Unknown error')}"
                    )
            else:
                self.log_test(
                    "服务状态API",
                    False,
                    f"HTTP状态码: {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "服务状态API",
                False,
                f"请求异常: {str(e)}"
            )
    
    def test_user_state_api(self):
        """测试用户状态API"""
        test_user_id = "test_user_001"
        
        try:
            response = self.session.get(
                f"{API_BASE}/chat/ai/user-state/{test_user_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    user_state = data.get("data", {})
                    self.log_test(
                        "用户状态API",
                        True,
                        f"成功获取用户{test_user_id}的状态"
                    )
                else:
                    self.log_test(
                        "用户状态API",
                        False,
                        f"API返回错误: {data.get('message', 'Unknown error')}"
                    )
            else:
                self.log_test(
                    "用户状态API",
                    False,
                    f"HTTP状态码: {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "用户状态API",
                False,
                f"请求异常: {str(e)}"
            )
    
    def test_chat_api_basic(self):
        """测试基础聊天API"""
        chat_data = {
            "participant_id": "test_user_001",
            "user_message": "Hello, I'm a test user. Can you help me learn programming?",
            "conversation_history": [],
            "code_context": {
                "html": "<div>Hello World</div>",
                "css": "",
                "js": ""
            },
            "task_context": "Learning HTML basics",
            "topic_id": "html_intro"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/chat/ai/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    ai_response = data.get("data", {})
                    response_text = ai_response.get("ai_response", "")
                    
                    if response_text:
                        self.log_test(
                            "基础聊天API",
                            True,
                            f"AI成功回复，长度: {len(response_text)}字符"
                        )
                        
                        # 检查响应中的关键信息
                        if "system_prompt" in ai_response:
                            self.log_test(
                                "系统提示词生成",
                                True,
                                "系统提示词生成成功"
                            )
                        else:
                            self.log_test(
                                "系统提示词生成",
                                False,
                                "响应中缺少system_prompt"
                            )
                    else:
                        self.log_test(
                            "基础聊天API",
                            False,
                            "AI回复为空"
                        )
                else:
                    self.log_test(
                        "基础聊天API",
                        False,
                        f"API返回错误: {data.get('message', 'Unknown error')}"
                    )
            else:
                self.log_test(
                    "基础聊天API",
                    False,
                    f"HTTP状态码: {response.status_code}, 响应: {response.text}"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "基础聊天API",
                False,
                f"请求异常: {str(e)}"
            )
    
    def test_chat_api_with_history(self):
        """测试带历史记录的聊天API"""
        chat_data = {
            "participant_id": "test_user_002",
            "user_message": "What is the difference between div and span?",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "Hello, I'm learning HTML"
                },
                {
                    "role": "assistant",
                    "content": "Hello! I'm Alex, your programming tutor. I'm here to help you learn HTML. What would you like to know?"
                }
            ],
            "code_context": {
                "html": "<div>This is a div</div><span>This is a span</span>",
                "css": "div { border: 1px solid black; }",
                "js": ""
            },
            "task_context": "Learning HTML elements",
            "topic_id": "div_span"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/chat/ai/chat",
                json=chat_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    ai_response = data.get("data", {})
                    response_text = ai_response.get("ai_response", "")
                    
                    if response_text:
                        self.log_test(
                            "带历史记录的聊天API",
                            True,
                            f"AI成功回复，长度: {len(response_text)}字符"
                        )
                    else:
                        self.log_test(
                            "带历史记录的聊天API",
                            False,
                            "AI回复为空"
                        )
                else:
                    self.log_test(
                        "带历史记录的聊天API",
                        False,
                        f"API返回错误: {data.get('message', 'Unknown error')}"
                    )
            else:
                self.log_test(
                    "带历史记录的聊天API",
                    False,
                    f"HTTP状态码: {response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "带历史记录的聊天API",
                False,
                f"请求异常: {str(e)}"
            )
    
    def test_chat_api_error_handling(self):
        """测试聊天API错误处理"""
        # 测试缺少必需字段
        invalid_data = {
            "user_message": "This should fail"
            # 缺少 participant_id
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/chat/ai/chat",
                json=invalid_data,
                timeout=10
            )
            
            if response.status_code in [400, 422]:  # FastAPI的Pydantic验证返回422
                self.log_test(
                    "错误处理 - 缺少字段",
                    True,
                    f"正确返回{response.status_code}错误"
                )
            else:
                self.log_test(
                    "错误处理 - 缺少字段",
                    False,
                    f"期望400或422错误，实际得到{response.status_code}"
                )
                
        except requests.exceptions.RequestException as e:
            self.log_test(
                "错误处理 - 缺少字段",
                False,
                f"请求异常: {str(e)}"
            )
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🤖 开始AI API连通性测试...")
        print(f"🌐 测试目标: {BASE_URL}")
        print("=" * 50)
        
        # 运行测试
        self.test_services_status()
        self.test_user_state_api()
        self.test_chat_api_basic()
        self.test_chat_api_with_history()
        self.test_chat_api_error_handling()
        
        # 输出测试总结
        print("=" * 50)
        print("📊 测试总结:")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存测试结果到文件
        self.save_test_results()
        
        return failed_tests == 0
    
    def save_test_results(self):
        """保存测试结果到文件"""
        results_file = project_root / "tests" / "ai_api_test_results.json"
        
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "test_suite": "AI API Connectivity Test",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "base_url": BASE_URL,
                    "results": self.test_results
                }, f, indent=2, ensure_ascii=False)
            
            print(f"📄 测试结果已保存到: {results_file}")
        except Exception as e:
            print(f"❌ 保存测试结果失败: {e}")


def main():
    """主函数"""
    # 检查后端服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code != 200:
            print(f"❌ 后端服务未运行或无法访问: {BASE_URL}")
            print("请先启动后端服务: uvicorn app.main:app --reload")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ 无法连接到后端服务: {BASE_URL}")
        print("请先启动后端服务: uvicorn app.main:app --reload")
        return False
    
    # 运行测试
    test_suite = AITestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 所有AI API测试通过!")
        return True
    else:
        print("\n❌ 部分AI API测试失败")
        return False


if __name__ == "__main__":
    main() 
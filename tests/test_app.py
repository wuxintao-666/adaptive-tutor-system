#!/usr/bin/env python3
"""
一键启动测试文件
用于测试前端和后端的启动情况
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_backend_health():
    """检查后端健康状态"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def check_frontend_health():
    """检查前端健康状态"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    
    # 切换到后端目录
    backend_dir = project_root / "backend"
    os.chdir(backend_dir)
    
    # 检查依赖
    print("📦 检查Python依赖...")
    try:
        # 使用项目根目录的requirements.txt
        requirements_path = project_root / "requirements.txt"
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)], 
                      check=True, capture_output=True)
        print("✅ Python依赖检查完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ Python依赖安装失败: {e}")
        return False
    
    # 启动后端服务
    print("🌐 启动FastAPI服务...")
    try:
        # 使用uvicorn启动服务
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        print("⏳ 等待后端服务启动...")
        for i in range(30):  # 最多等待30秒
            if check_backend_health():
                print("✅ 后端服务启动成功!")
                return process
            time.sleep(1)
        
        print("❌ 后端服务启动超时")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ 后端服务启动失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🎨 启动前端服务...")
    
    # 切换到前端目录
    frontend_dir = project_root / "frontend"
    os.chdir(frontend_dir)
    
    # 检查前端文件是否存在
    if not (frontend_dir / "index.html").exists():
        print("⚠️  前端目录中没有index.html，跳过前端启动")
        return None
    
    # 启动前端服务（静态文件服务）
    try:
        # 使用Python的http.server启动静态文件服务
        process = subprocess.Popen([
            "python", "-m", "http.server", "3000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务启动
        print("⏳ 等待前端服务启动...")
        for i in range(10):  # 最多等待10秒
            if check_frontend_health():
                print("✅ 前端服务启动成功!")
                return process
            time.sleep(1)
        
        print("❌ 前端服务启动超时")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ 前端服务启动失败: {e}")
        return None

def test_ai_api():
    """测试AI API连通性"""
    print("🤖 测试AI API连通性...")
    
    try:
        # 测试服务状态API
        response = requests.get("http://localhost:8000/api/v1/chat/ai/services/status", timeout=10)
        if response.status_code == 200:
            services_status = response.json()
            print("✅ 服务状态API测试成功")
            print(f"📊 服务状态: {services_status}")
        else:
            print(f"❌ 服务状态API测试失败: {response.status_code}")
            return False
        
        # 测试聊天API
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
        
        response = requests.post(
            "http://localhost:8000/api/v1/chat/ai/chat",
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 聊天API测试成功")
            print(f"🤖 AI回复: {result['data']['ai_response'][:100]}...")
            return True
        else:
            print(f"❌ 聊天API测试失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🎯 开始一键启动测试...")
    print(f"📁 项目根目录: {project_root}")
    
    # 保存当前目录
    original_dir = os.getcwd()
    
    try:
        # 启动后端
        backend_process = start_backend()
        if not backend_process:
            print("❌ 后端启动失败，测试终止")
            return
        
        # 启动前端
        frontend_process = start_frontend()
        
        # 等待一下让服务完全启动
        time.sleep(2)
        
        # 测试AI API
        api_success = test_ai_api()
        
        if api_success:
            print("\n🎉 所有测试通过!")
            print("📝 测试总结:")
            print("  ✅ 后端服务启动成功")
            print("  ✅ AI API连通性测试通过")
            if frontend_process:
                print("  ✅ 前端服务启动成功")
            else:
                print("  ⚠️  前端服务未启动（可能是正常的）")
        else:
            print("\n❌ 部分测试失败")
            print("📝 测试总结:")
            print("  ✅ 后端服务启动成功")
            print("  ❌ AI API连通性测试失败")
        
        # 保持服务运行一段时间
        print("\n⏳ 服务将保持运行30秒...")
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
    finally:
        # 清理进程
        print("🧹 清理进程...")
        if 'backend_process' in locals() and backend_process:
            backend_process.terminate()
        if 'frontend_process' in locals() and frontend_process:
            frontend_process.terminate()
        
        # 恢复原始目录
        os.chdir(original_dir)
        print("✅ 测试完成")

if __name__ == "__main__":
    main() 
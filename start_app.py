#!/usr/bin/env python3
"""
一键启动应用脚本
启动后端和前端服务，提供完整的Web应用访问
"""

import os
import sys
import subprocess
import time
import requests
import signal
import threading
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class AppLauncher:
    """应用启动器"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        print("\n🛑 收到停止信号，正在关闭服务...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def check_backend_health(self):
        """检查后端健康状态"""
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_frontend_health(self):
        """检查前端健康状态"""
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def start_backend(self):
        """启动后端服务"""
        print("🚀 启动后端服务...")
        
        # 切换到后端目录
        backend_dir = project_root / "backend"
        os.chdir(backend_dir)
        
        try:
            # 使用uvicorn启动服务
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000",
                "--reload"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            print("⏳ 等待后端服务启动...")
            for i in range(30):  # 最多等待30秒
                if self.check_backend_health():
                    print("✅ 后端服务启动成功!")
                    return True
                time.sleep(1)
            
            print("❌ 后端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 后端服务启动失败: {e}")
            return False
    
    def start_frontend(self):
        """启动前端服务"""
        print("🎨 启动前端服务...")
        
        # 切换到前端目录
        frontend_dir = project_root / "frontend"
        os.chdir(frontend_dir)
        
        # 检查前端文件是否存在
        if not (frontend_dir / "pages" / "learning_page.html").exists():
            print("⚠️  前端目录中没有learning_page.html，跳过前端启动")
            return False
        
        try:
            # 使用Python的http.server启动静态文件服务
            self.frontend_process = subprocess.Popen([
                "python", "-m", "http.server", "3000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待服务启动
            print("⏳ 等待前端服务启动...")
            for i in range(10):  # 最多等待10秒
                if self.check_frontend_health():
                    print("✅ 前端服务启动成功!")
                    return True
                time.sleep(1)
            
            print("❌ 前端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 前端服务启动失败: {e}")
            return False
    
    def test_services(self):
        """测试服务状态"""
        print("🔍 测试服务状态...")
        
        # 测试后端API
        try:
            response = requests.get("http://localhost:8000/api/v1/chat/ai/services/status", timeout=10)
            if response.status_code == 200:
                services_status = response.json()
                print("✅ 后端API测试成功")
                print(f"📊 服务状态: {services_status}")
            else:
                print(f"⚠️  后端API测试失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️  后端API测试失败: {e}")
        
        # 测试前端页面
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✅ 前端页面测试成功")
            else:
                print(f"⚠️  前端页面测试失败: {response.status_code}")
        except Exception as e:
            print(f"⚠️  前端页面测试失败: {e}")
    
    def show_access_info(self):
        """显示访问信息"""
        print("\n" + "="*60)
        print("🎉 应用启动完成！")
        print("="*60)
        print("📱 访问地址:")
        print("  🌐 前端页面: http://localhost:3000/pages/learning_page.html")
        print("  🔧 后端API: http://localhost:8000")
        print("  📚 API文档: http://localhost:8000/docs")
        print("  🔍 服务状态: http://localhost:8000/api/v1/chat/ai/services/status")
        print("\n💡 使用说明:")
        print("  • 在浏览器中打开 http://localhost:3000/pages/learning_page.html 访问学习页面")
        print("  • 按 Ctrl+C 停止所有服务")
        print("  • 服务会自动重启（热重载模式）")
        print("="*60)
    
    def monitor_services(self):
        """监控服务状态"""
        print("\n🔍 开始监控服务状态...")
        
        while self.running:
            try:
                # 检查后端
                backend_ok = self.check_backend_health()
                # 检查前端
                frontend_ok = self.check_frontend_health()
                
                # 显示状态
                backend_status = "✅" if backend_ok else "❌"
                frontend_status = "✅" if frontend_ok else "❌"
                
                print(f"\r📊 服务状态: 后端{backend_status} 前端{frontend_status}", end="", flush=True)
                
                time.sleep(10)  # 每10秒检查一次
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n⚠️  监控出错: {e}")
    
    def cleanup(self):
        """清理进程"""
        print("\n🧹 清理进程...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
                print("✅ 后端服务已停止")
            except:
                self.backend_process.kill()
                print("⚠️  强制停止后端服务")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
                print("✅ 前端服务已停止")
            except:
                self.frontend_process.kill()
                print("⚠️  强制停止前端服务")
    
    def run(self):
        """运行启动器"""
        print("🎯 自适应导师系统 - 一键启动")
        print(f"📁 项目根目录: {project_root}")
        print("="*60)
        
        # 保存当前目录
        original_dir = os.getcwd()
        
        try:
            # 启动后端
            if not self.start_backend():
                print("❌ 后端启动失败，应用无法启动")
                return False
            
            # 启动前端
            self.start_frontend()
            
            # 等待服务完全启动
            time.sleep(2)
            
            # 测试服务
            self.test_services()
            
            # 显示访问信息
            self.show_access_info()
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # 保持主线程运行
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 用户中断")
            
        except Exception as e:
            print(f"\n❌ 启动过程中发生错误: {e}")
            return False
        finally:
            # 清理进程
            self.cleanup()
            
            # 恢复原始目录
            os.chdir(original_dir)
            print("✅ 应用已完全停止")

def main():
    """主函数"""
    launcher = AppLauncher()
    launcher.run()

if __name__ == "__main__":
    main() 
# 一键启动应用指南

## 🚀 快速启动

### 方法一：使用Python脚本（推荐）

```bash
python start_app.py
```

### 方法二：使用批处理文件（Windows）

双击 `start_app.bat` 文件

### 方法三：手动启动

```bash
# 启动后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（新终端）
cd frontend
python -m http.server 3000
```

## 📱 访问地址

启动成功后，你可以访问以下地址：

- **🌐 前端页面**: http://localhost:3000
- **🔧 后端API**: http://localhost:8000
- **📚 API文档**: http://localhost:8000/docs
- **🔍 服务状态**: http://localhost:8000/api/v1/chat/ai/services/status

## ✨ 功能特性

### 🎯 一键启动脚本特性

1. **自动启动服务**
   - 自动启动后端FastAPI服务
   - 自动启动前端静态文件服务
   - 智能检测服务状态

2. **健康检查**
   - 自动检测后端API是否正常
   - 自动检测前端页面是否可访问
   - 实时监控服务状态

3. **优雅关闭**
   - 按 `Ctrl+C` 优雅停止所有服务
   - 自动清理进程
   - 防止僵尸进程

4. **实时监控**
   - 每10秒检查服务状态
   - 显示实时状态指示器
   - 自动重启支持（热重载）

### 🔧 服务说明

#### 后端服务 (http://localhost:8000)
- **FastAPI框架**: 提供RESTful API
- **AI对话功能**: 支持与AI进行编程教学对话
- **用户状态管理**: 跟踪学习进度和情感状态
- **自动文档**: 访问 `/docs` 查看API文档

#### 前端服务 (http://localhost:3000)
- **静态文件服务**: 提供Web页面访问
- **响应式设计**: 支持不同设备访问
- **实时交互**: 与后端API实时通信

## 🛠️ 故障排除

### 常见问题

1. **端口被占用**
   ```
   错误: Address already in use
   解决: 关闭占用8000或3000端口的程序
   ```

2. **依赖缺失**
   ```
   错误: ModuleNotFoundError
   解决: 运行 pip install -r requirements.txt
   ```

3. **配置问题**
   ```
   错误: LLM API连接失败
   解决: 检查 .env 文件中的API配置
   ```

4. **权限问题**
   ```
   错误: Permission denied
   解决: 以管理员身份运行或检查文件权限
   ```

### 调试模式

如果需要查看详细日志，可以修改 `start_app.py` 中的输出重定向：

```python
# 将 stdout=subprocess.PIPE 改为 stdout=None
self.backend_process = subprocess.Popen([
    sys.executable, "-m", "uvicorn", 
    "app.main:app", 
    "--host", "0.0.0.0", 
    "--port", "8000",
    "--reload"
], stdout=None, stderr=None)  # 显示所有输出
```

## 📋 使用流程

1. **启动应用**
   ```bash
   python start_app.py
   ```

2. **等待启动完成**
   - 看到 "🎉 应用启动完成！" 消息
   - 确认所有服务状态为 ✅

3. **访问页面**
   - 打开浏览器访问 http://localhost:3000
   - 开始使用自适应导师系统

4. **停止应用**
   - 按 `Ctrl+C` 停止所有服务
   - 等待清理完成

## 🔄 开发模式

在开发过程中，服务支持热重载：

- **后端**: 修改Python代码后自动重启
- **前端**: 修改HTML/CSS/JS后刷新页面即可

## 📞 技术支持

如果遇到问题：

1. 检查控制台输出的错误信息
2. 确认 `.env` 文件配置正确
3. 验证网络连接和API密钥
4. 查看 `START_APP_GUIDE.md` 故障排除部分

---

**�� 现在你可以享受一键启动的便利了！** 
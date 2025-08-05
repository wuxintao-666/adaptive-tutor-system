# 配置设置指南

## 魔搭访问令牌配置

### 1. 获取魔搭访问令牌

1. 访问 [魔搭控制台](https://dashscope.console.aliyun.com/)
2. 登录你的阿里云账号
3. 在控制台中创建或查看你的API密钥
4. 复制你的访问令牌

### 2. 创建 .env 文件

在项目根目录创建 `.env` 文件，内容如下：

```bash
# 自适应导师系统环境配置

# ===== LLM服务配置 =====
# 选择LLM提供商: "modelscope" 或 "openai"
LLM_PROVIDER=modelscope

# ===== 魔搭配置 =====
# 你的魔搭访问令牌 (从 https://dashscope.console.aliyun.com/ 获取)
MODELSCOPE_API_KEY=your_modelscope_api_key_here
# 魔搭API基础URL
MODELSCOPE_API_BASE=https://dashscope.aliyuncs.com/api/v1
# 魔搭模型名称 (可选: qwen-turbo, qwen-plus, qwen-max, qwen-max-longcontext)
MODELSCOPE_MODEL=qwen-turbo

# ===== OpenAI配置 (备用) =====
# OpenAI API密钥
OPENAI_API_KEY=your_openai_api_key_here
# OpenAI API基础URL
OPENAI_API_BASE=https://api.openai.com/v1
# OpenAI模型名称
OPENAI_MODEL=gpt-3.5-turbo

# ===== 嵌入模型配置 =====
# 嵌入模型名称
EMBEDDING_MODEL=text-embedding-ada-002

# ===== LLM参数配置 =====
# 最大token数
LLM_MAX_TOKENS=1000
# 温度参数 (0.0-1.0)
LLM_TEMPERATURE=0.7

# ===== 服务器配置 =====
# 后端端口
BACKEND_PORT=8000

# ===== 数据库配置 =====
# 数据库URL
DATABASE_URL=sqlite:///./database.db
```

### 3. 替换配置值

将 `your_modelscope_api_key_here` 替换为你的实际魔搭访问令牌：

```bash
MODELSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. 验证配置

运行测试来验证配置是否正确：

```bash
# 测试AI API连通性
python tests/test_ai_api.py

# 或者运行一键启动测试
python tests/test_app.py
```

### 5. 可用的魔搭模型

- `qwen-turbo`: 通义千问Turbo版本，响应速度快
- `qwen-plus`: 通义千问Plus版本，能力更强
- `qwen-max`: 通义千问Max版本，最强能力
- `qwen-max-longcontext`: 通义千问Max长文本版本

### 6. 故障排除

如果遇到问题：

1. **检查API密钥**: 确保你的魔搭访问令牌正确且有效
2. **检查网络**: 确保能够访问魔搭API
3. **查看日志**: 运行测试时查看详细的错误信息
4. **模型可用性**: 确保选择的模型在你的账户中可用

### 7. 切换到OpenAI

如果你想使用OpenAI而不是魔搭：

1. 修改 `LLM_PROVIDER=openai`
2. 设置你的 `OPENAI_API_KEY`
3. 选择OpenAI模型如 `gpt-3.5-turbo` 或 `gpt-4` 
# RAG Module

这是一个独立的RAG（Retrieval-Augmented Generation）模块，可以从原始项目中拆分出来单独使用。

## 功能特性

- 文档加载和解析
- 文本分割
- 向量嵌入生成
- 向量存储和检索
- 重排序功能（可选）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from RAGmodule.RAG import initialize_rag_system

# 初始化RAG系统
retriever = initialize_rag_system()

# 检索相关文档
context = retriever.retrieve("你的查询问题")
```

### 构建向量存储

如果需要重新构建向量存储：

```bash
cd RAGmodule
python build_embeddings.py
```

或者在代码中调用：

```python
from RAGmodule.RAG import build_vector_store

# 构建向量存储
success = build_vector_store()
```

## 配置

配置文件位于 `RAGmodule/config.py`，可以根据需要修改以下配置：

- 文档路径
- 向量存储路径
- 嵌入模型配置
- 检索器参数

## 测试

使用诊断脚本测试模块功能：

```bash
cd RAGmodule
python diagnose.py
```

或者：

```bash
python -m RAGmodule
```

## 依赖服务

- Ollama服务（用于嵌入生成和重排序）

确保Ollama服务正在运行，并且可以访问配置中指定的主机地址。
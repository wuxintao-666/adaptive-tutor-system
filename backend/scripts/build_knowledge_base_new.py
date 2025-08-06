# scripts/build_knowledge_base_new.py (使用新架构)
import os
import sys
import json
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 找到项目根目录并设置环境变量
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

from app.core.config import settings
from app.services.knowledge_builder_impl import KnowledgeBaseBuilderImpl

def main():
    """主函数：构建知识库"""
    print("开始构建知识库...")
    
    # 从配置中获取路径
    DOCUMENTS_DIR = settings.DOCUMENTS_DIR
    VECTOR_STORE_DIR = settings.VECTOR_STORE_DIR
    
    # 创建知识库构建器
    builder = KnowledgeBaseBuilderImpl()
    
    # 从文档目录构建知识库
    print(f"从目录加载文档: {DOCUMENTS_DIR}")
    builder.build_from_directory(DOCUMENTS_DIR, recursive=True)
    
    # 保存知识库
    print(f"保存知识库到: {VECTOR_STORE_DIR}")
    builder.save(VECTOR_STORE_DIR)
    
    print("知识库构建完成!")

if __name__ == "__main__":
    main()
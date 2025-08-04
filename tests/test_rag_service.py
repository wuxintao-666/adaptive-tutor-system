#!/usr/bin/env python3

import sys
import os

# 添加项目根目录到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
backend_dir = os.path.join(project_root, 'backend')
sys.path.insert(0, os.path.abspath(project_root))
sys.path.insert(0, os.path.abspath(backend_dir))

from app.services.rag_service import rag_service
from app.core.config import settings

def test_rag_service():
    """
    测试RAG服务的参数传递和返回值
    """
    print("开始测试RAG服务...")
    
    # 测试1: 正常查询
    print("\n测试1: 正常查询")
    query = "什么是codeAID？"
    k = 3
    print(f"查询: '{query}', 需要返回 {k} 个结果")
    results = rag_service.retrieve(query, k)
    print(f"实际返回结果数量: {len(results)}")
    print(f"返回结果类型: {type(results)}")
    if results:
        print("返回结果示例:")
        for i, result in enumerate(results[:2]):  # 只显示前两个结果
            print(f"  {i+1}. {result[:100]}...")
    else:
        print("未返回任何结果")
    
    # 测试2: 空查询
    print("\n测试2: 空查询")
    empty_query = ""
    results = rag_service.retrieve(empty_query, 3)
    print(f"空查询返回结果数量: {len(results)}")
    
    # 测试3: 边界值测试 (k=0)
    print("\n测试3: 边界值测试 (k=0)")
    results = rag_service.retrieve("HTML", 0)
    print(f"k=0时返回结果数量: {len(results)}")
    
    # 测试4: 大量结果请求
    print("\n测试4: 请求大量结果")
    results = rag_service.retrieve("HTML", 10)
    print(f"请求10个结果，实际返回: {len(results)}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_rag_service()
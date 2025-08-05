#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同的ModelScope API配置
"""

import sys
import os

# 添加项目路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openai import OpenAI

def test_different_configs():
    """测试不同的API配置"""
    configs = [
        {
            "name": "当前配置",
            "base_url": "https://ms-fc-1d889e1e-d2ad.api-inference.modelscope.cn/v1",
            "api_key": "ms-e9cb1ee1-d248-4f05-87d1-fbc2083c41ae",
            "model": "Qwen/Qwen3-Embedding-4B-GGUF"
        },
        {
            "name": "ModelScope标准端点(已知会失败)",
            "base_url": "https://api-inference.modelscope.cn/v1",
            "api_key": "ms-e9cb1ee1-d248-4f05-87d1-fbc2083c41ae",
            "model": "Qwen/Qwen3-Embedding-4B-GGUF"
        }
    ]
    
    test_text = "Python是一种高级编程语言"
    
    for config in configs:
        print(f"\n测试配置: {config['name']}")
        print(f"Base URL: {config['base_url']}")
        
        try:
            client = OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
            
            response = client.embeddings.create(
                input=test_text,  # ModelScope API期望字符串而不是列表
                model=config["model"],
                encoding_format="float"
            )
            
            print(f"  ✓ 调用成功")
            print(f"  模型: {getattr(response, 'model', 'N/A')}")
            # 正确访问OpenAI API响应数据
            data = getattr(response, 'data', None)
            print(f"  Data: {data}")
            if data and len(data) > 0:
                embedding = data[0].embedding
                print(f"  Embedding长度: {len(embedding)}")
                # 显示部分embedding数据作为验证
                print(f"  前10个embedding值: {embedding[:10]}")
            else:
                print("  没有返回embedding数据")
                
        except Exception as e:
            print(f"  ✗ 调用失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("ModelScope API配置测试")
    print("=" * 60)
    
    test_different_configs()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
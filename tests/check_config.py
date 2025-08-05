#!/usr/bin/env python3
"""
配置检查脚本
用于验证环境配置是否正确
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载.env文件
load_dotenv(project_root / ".env")

def check_env_file():
    """检查.env文件是否存在"""
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env文件存在")
        return True
    else:
        print("❌ .env文件不存在")
        print("请按照 CONFIG_SETUP.md 中的说明创建 .env 文件")
        return False

def check_required_vars():
    """检查必需的环境变量"""
    print("\n🔍 检查环境变量...")
    
    # 检查LLM提供商
    provider = os.getenv('LLM_PROVIDER', 'modelscope')
    print(f"LLM提供商: {provider}")
    
    if provider == "modelscope":
        # 检查魔搭配置
        api_key = os.getenv('MODELSCOPE_API_KEY', '')
        api_base = os.getenv('MODELSCOPE_API_BASE', '')
        model = os.getenv('MODELSCOPE_MODEL', '')
        
        print(f"魔搭API密钥: {'✅ 已设置' if api_key and api_key != 'your_modelscope_api_key_here' else '❌ 未设置或使用默认值'}")
        print(f"魔搭API基础URL: {api_base}")
        print(f"魔搭模型: {model}")
        
        if not api_key or api_key == 'your_modelscope_api_key_here':
            print("⚠️  请设置你的魔搭访问令牌")
            return False
        return True
        
    elif provider == "openai":
        # 检查OpenAI配置
        api_key = os.getenv('OPENAI_API_KEY', '')
        api_base = os.getenv('OPENAI_API_BASE', '')
        model = os.getenv('OPENAI_MODEL', '')
        
        print(f"OpenAI API密钥: {'✅ 已设置' if api_key and api_key != 'your_openai_api_key_here' else '❌ 未设置或使用默认值'}")
        print(f"OpenAI API基础URL: {api_base}")
        print(f"OpenAI模型: {model}")
        
        if not api_key or api_key == 'your_openai_api_key_here':
            print("⚠️  请设置你的OpenAI API密钥")
            return False
        return True
    
    else:
        print(f"❌ 不支持的LLM提供商: {provider}")
        return False

def test_llm_connection():
    """测试LLM连接"""
    print("\n🔗 测试LLM连接...")
    
    try:
        from backend.app.services.llm_gateway import llm_gateway
        
        # 检查配置
        if not llm_gateway.api_key:
            print("❌ LLM API密钥未配置")
            return False
        
        # 测试连接
        is_valid = llm_gateway.validate_connection()
        if is_valid:
            print("✅ LLM连接测试成功")
            return True
        else:
            print("❌ LLM连接测试失败")
            return False
            
    except Exception as e:
        print(f"❌ LLM连接测试出错: {e}")
        return False

def main():
    """主函数"""
    print("🔧 配置检查工具")
    print("=" * 50)
    
    # 检查.env文件
    env_ok = check_env_file()
    
    # 检查环境变量
    vars_ok = check_required_vars()
    
    # 测试LLM连接
    connection_ok = test_llm_connection()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结:")
    print(f"  .env文件: {'✅' if env_ok else '❌'}")
    print(f"  环境变量: {'✅' if vars_ok else '❌'}")
    print(f"  LLM连接: {'✅' if connection_ok else '❌'}")
    
    if env_ok and vars_ok and connection_ok:
        print("\n🎉 配置检查通过！系统可以正常运行。")
        return True
    else:
        print("\n⚠️  配置检查未通过，请参考 CONFIG_SETUP.md 进行配置。")
        return False

if __name__ == "__main__":
    main() 
import os

print("检查环境变量:")
print(f"MODELSCOPE_API_KEY: {os.getenv('MODELSCOPE_API_KEY', 'Not set')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'Not set')}")

# 检查配置中的值
try:
    from backend.app.core.config import settings
    print(f"\n配置文件中的值:")
    print(f"settings.MODELSCOPE_API_KEY: {settings.MODELSCOPE_API_KEY}")
    print(f"settings.OPENAI_API_KEY: {settings.OPENAI_API_KEY}")
except Exception as e:
    print(f"无法导入配置: {e}")
import os
import sys
import pytest

# 将 backend 目录添加到 sys.path 中，便于按项目方式导入
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.config import settings

def test_settings_are_loaded_correctly():
    """
    测试关键配置项是否从 .env 或环境变量中正确加载到 settings 对象
    """
    required_attributes = [
        "TUTOR_OPENAI_API_KEY",
        "TUTOR_OPENAI_API_BASE",
        "TUTOR_OPENAI_MODEL",
        "TUTOR_EMBEDDING_API_KEY",
        "TUTOR_TRANSLATION_API_KEY",
    ]

    missing_or_empty_settings = []
    for attr in required_attributes:
        # Pydantic v2: required fields without defaults will raise error on instantiation if missing.
        # This test is an extra safeguard, especially for fields that might have defaults but shouldn't be empty.
        value = getattr(settings, attr, None)
        if not value:
            missing_or_empty_settings.append(attr)

    assert not missing_or_empty_settings, (
        f"The following required settings are missing or empty in your configuration "
        f"(check .env file or environment variables): {missing_or_empty_settings}"
    )

if __name__ == "__main__":
    # A simple way to run the check standalone
    try:
        test_settings_are_loaded_correctly()
        print("✅ All required settings are present.")
    except AssertionError as e:
        print(f"❌ Configuration check failed: {e}")

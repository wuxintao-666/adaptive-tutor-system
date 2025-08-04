import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# 这是一个技巧，用于在测试环境中设置正确的模块搜索路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.main import app  # 假设你的FastAPI实例在main.py中
from app.schemas.submission import TestSubmissionRequest, CodePayload

# 使用TestClient来模拟API请求
client = TestClient(app)

# 准备一些模拟数据
MOCK_TOPIC_ID = "js_simple_counter"
MOCK_PARTICIPANT_ID = "test_participant_123"
MOCK_CODE = CodePayload(
    html="<body>...</body>",
    css="h1 { color: red; }",
    js="console.log('hello');"
)
MOCK_REQUEST_PAYLOAD = TestSubmissionRequest(
    participant_id=MOCK_PARTICIPANT_ID,
    topic_id=MOCK_TOPIC_ID,
    code=MOCK_CODE
)

# 模拟的测试检查点
MOCK_CHECKPOINTS = [{"name": "Mock Checkpoint", "type": "assert_text_content", "selector": "p", "value": "Test"}]

@pytest.fixture
def mock_dependencies():
    """
    使用Pytest的fixture和unittest.mock来模拟所有外部依赖。
    这样我们的API测试就只关注API本身的逻辑，而不会真的去调用数据库或沙箱。
    """
    with patch('app.api.endpoints.submission.load_json_content') as mock_load_content, \
         patch('app.api.endpoints.submission.sandbox_service') as mock_sandbox, \
         patch('app.api.endpoints.submission.get_user_state_service') as mock_get_uss:
        
        # 设置模拟函数的返回值
        mock_load_content.return_value = {"checkpoints": MOCK_CHECKPOINTS}
        
        mock_uss_instance = MagicMock()
        mock_get_uss.return_value = mock_uss_instance
        
        # 将所有模拟对象打包，以便在测试函数中使用
        yield mock_load_content, mock_sandbox, mock_uss_instance

def test_submit_test_success(mock_dependencies):
    """
    测试用例1: 模拟评测成功的情况
    """
    mock_load_content, mock_sandbox, mock_uss_instance = mock_dependencies

    # 模拟沙箱返回“通过”的结果
    mock_sandbox.run_evaluation.return_value = {
        "passed": True,
        "message": "恭喜！所有测试点都通过了！",
        "details": []
    }

    # 发送API请求
    response = client.post("/api/v1/submit-test", json=MOCK_REQUEST_PAYLOAD.dict())

    # --- 断言 ---
    # 1. 验证API响应
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["passed"] is True
    assert "恭喜" in response_data["message"]

    # 2. 验证依赖项是否被正确调用
    mock_load_content.assert_called_once_with("test_tasks", MOCK_TOPIC_ID)
    mock_sandbox.run_evaluation.assert_called_once_with(
        user_code=MOCK_CODE.dict(),
        checkpoints=MOCK_CHECKPOINTS
    )
    mock_uss_instance.update_bkt_on_submission.assert_called_once_with(
        participant_id=MOCK_PARTICIPANT_ID,
        topic_id=MOCK_TOPIC_ID,
        is_correct=True  # 关键：验证传入的是True
    )

def test_submit_test_failure(mock_dependencies):
    """
    测试用例2: 模拟评测失败的情况
    """
    mock_load_content, mock_sandbox, mock_uss_instance = mock_dependencies
    
    # 模拟沙箱返回“失败”的结果
    mock_sandbox.run_evaluation.return_value = {
        "passed": False,
        "message": "很遗憾，部分测试点未通过。",
        "details": ["检查点 1 失败: 某个元素没找到"]
    }

    # 发送API请求
    response = client.post("/api/v1/submit-test", json=MOCK_REQUEST_PAYLOAD.dict())

    # --- 断言 ---
    # 1. 验证API响应
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["passed"] is False
    assert "很遗憾" in response_data["message"]
    assert len(response_data["details"]) == 1

    # 2. 验证BKT更新函数被正确调用
    mock_uss_instance.update_bkt_on_submission.assert_called_once_with(
        participant_id=MOCK_PARTICIPANT_ID,
        topic_id=MOCK_TOPIC_ID,
        is_correct=False  # 关键：验证传入的是False
    )

def test_submit_test_topic_not_found(mock_dependencies):
    """
    测试用例3: 模拟请求一个不存在的topic_id
    """
    mock_load_content, mock_sandbox, mock_uss_instance = mock_dependencies

    # 模拟内容加载服务抛出404异常
    mock_load_content.side_effect = HTTPException(status_code=404, detail="Not Found")

    # 发送API请求
    response = client.post("/api/v1/submit-test", json=MOCK_REQUEST_PAYLOAD.dict())

    # --- 断言 ---
    # 1. 验证API返回404错误
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

    # 2. 验证沙箱和BKT服务未被调用
    mock_sandbox.run_evaluation.assert_not_called()
    mock_uss_instance.update_bkt_on_submission.assert_not_called()

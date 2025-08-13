import os
import sys
import pytest


# 将 backend 目录添加到 sys.path 中，便于按项目方式导入
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.prompt_generator import PromptGenerator
from app.schemas.chat import UserStateSummary
from app.schemas.content import CodeContent


def make_user_state(
    *,
    is_new_user: bool,
    emotion: str = "NEUTRAL",
    bkt_models: dict | None = None,
    behavior_counters: dict | None = None,
):
    return UserStateSummary(
        participant_id="u1",
        emotion_state={"current_sentiment": emotion},
        behavior_counters=behavior_counters or {},
        bkt_models=bkt_models or {},
        is_new_user=is_new_user,
    )


def test_build_message_history_with_code_context():
    g = PromptGenerator()

    conversation_history = [
        {"role": "assistant", "content": "Hi"},
        {"role": "user", "content": "Show me"},
    ]
    code = CodeContent(
        html="<h1>Hello</h1>",
        css="h1 { color: red; }",
        js="console.log('x')",
    )

    messages = g._build_message_history(
        conversation_history=conversation_history,
        code_context=code,
        user_message="Why?",
    )

    # 历史消息保留
    assert messages[0] == {"role": "assistant", "content": "Hi"}
    assert messages[1] == {"role": "user", "content": "Show me"}

    # 追加的用户消息包含代码片段与问题
    last = messages[-1]
    assert last["role"] == "user"
    assert "Here is my current code:" in last["content"]
    assert "```html" in last["content"] and "```css" in last["content"] and "```javascript" in last["content"]
    assert "My question is: Why?" in last["content"]


def test_build_system_prompt_new_user_no_context():
    g = PromptGenerator()
    user_state = make_user_state(is_new_user=True, emotion="NEUTRAL")

    prompt = g._build_system_prompt(
        user_state=user_state,
        retrieved_context=[],
        task_context=None,
        topic_title=None,
    )

    # 含基础系统提示
    assert "You are 'Alex', a world-class AI programming tutor" in prompt
    # 情感策略（NEUTRAL）
    assert "The student seems neutral" in prompt
    # 新用户提示
    assert "This is a new student" in prompt
    # 无RAG上下文提示
    assert "No relevant knowledge was retrieved" in prompt


def test_build_system_prompt_existing_user_with_progress_behavior_and_context():
    g = PromptGenerator()
    bkt_models = {
        "topic1": {"mastery_prob": 0.9},    # advanced
        "topic2": {"mastery_prob": 0.6},    # intermediate
        "topic3": {"mastery_prob": 0.2},    # beginner
    }
    behavior = {
        "error_count": 3,
        "submission_timestamps": [1, 2],
    }
    user_state = make_user_state(is_new_user=False, emotion="CONFUSED", bkt_models=bkt_models, behavior_counters=behavior)

    retrieved = ["ctx1", "ctx2"]
    prompt = g._build_system_prompt(
        user_state=user_state,
        retrieved_context=retrieved,
        task_context="Implement stack",
        topic_title="loops",
    )

    # 既有学生提示
    assert "existing student" in prompt
    # 掌握度概览
    assert "topic1: advanced" in prompt
    assert "topic2: intermediate" in prompt
    # 行为统计
    assert "errors: 3" in prompt
    assert "submissions: 2" in prompt
    # RAG 上下文连接符与内容
    assert "REFERENCE KNOWLEDGE" in prompt and "ctx1" in prompt and "ctx2" in prompt
    assert "---" in prompt
    # 任务与主题
    assert "TASK CONTEXT: The student is currently working on: 'Implement stack'" in prompt
    assert "TOPIC: The current learning topic is 'loops'" in prompt


def test_create_prompts_integration():
    g = PromptGenerator()
    user_state = make_user_state(is_new_user=True, emotion="EXCITED")
    conversation_history = [
        {"role": "assistant", "content": "Welcome"},
    ]
    code = CodeContent(html="<p>Hi</p>")

    system_prompt, messages = g.create_prompts(
        user_state=user_state,
        retrieved_context=["Docs"],
        conversation_history=conversation_history,
        user_message="Explain closures",
        code_content=code,
        task_context="Practice functions",
        topic_title="javascript",
    )

    # 系统提示含期待关键字
    assert "EXCITED" not in system_prompt  # 文本不一定直接包含标签，但会包含策略文字
    assert "excited and engaged" in system_prompt
    assert "Docs" in system_prompt

    # 消息历史正确拼装
    assert messages[0] == {"role": "assistant", "content": "Welcome"}
    assert messages[-1]["role"] == "user"
    assert "My question is: Explain closures" in messages[-1]["content"]


def test_get_emotion_strategy_fallback():
    # 静态方法：未知情感走 NEUTRAL 策略
    text = PromptGenerator._get_emotion_strategy("unknown")
    assert "The student seems neutral" in text


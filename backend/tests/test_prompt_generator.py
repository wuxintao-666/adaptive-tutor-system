import os
import sys
from typing import List, Dict


# 确保可以按项目路径导入 app.*
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.prompt_generator import PromptGenerator
from app.schemas.chat import UserStateSummary
from app.schemas.content import CodeContent


def _read_context_text() -> List[str]:
    """优先从 PG_CONTEXT_FILE 读取；否则读取项目自带示例文档的一段作为 RAG 上下文。"""
    context_file = os.getenv("PG_CONTEXT_FILE")
    texts: List[str] = []
    try:
        if context_file and os.path.exists(context_file):
            with open(context_file, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read().strip()
                if data:
                    texts.append(data[:2000])
                    return texts
    except Exception:
        pass

    # 退回到项目内置文档
    fallback = os.path.abspath(os.path.join(backend_path, "app", "data", "documents", "ai_fundamentals.txt"))
    try:
        if os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8", errors="ignore") as f:
                data = f.read().strip()
                if data:
                    texts.append(data[:2000])
    except Exception:
        pass

    return texts


def _make_user_state() -> UserStateSummary:
    participant_id = os.getenv("PG_PARTICIPANT_ID", "u1")
    is_new_user = os.getenv("PG_IS_NEW_USER", "true").lower() == "true"
    emotion = os.getenv("PG_EMOTION", "NEUTRAL")

    # 模拟一些掌握度与行为计数，更贴近真实
    bkt_models = {
        "topic_arrays": {"mastery_prob": 0.62},
        "topic_binary_search": {"mastery_prob": 0.35},
        "topic_complexity": {"mastery_prob": 0.82},
    }
    behavior_counters = {
        "error_count": 3,
        "submission_timestamps": [1, 2, 3, 4],
    }

    return UserStateSummary(
        participant_id=participant_id,
        emotion_state={"current_sentiment": emotion},
        behavior_counters=behavior_counters,
        bkt_models=bkt_models,
        is_new_user=is_new_user,
    )


def _make_conversation_history() -> List[Dict[str, str]]:
    return [
        {"role": "assistant", "content": "你好，我是你的编程助教。"},
        {"role": "user", "content": "我想学会二分查找。"},
    ]


def _maybe_make_code_context() -> CodeContent | None:
    include_code = os.getenv("PG_INCLUDE_CODE", "false").lower() == "true"
    if not include_code:
        return None

    return CodeContent(
        html="""<ul id=\"arr\"><li>1</li><li>3</li><li>5</li><li>9</li></ul>""",
        css="""#arr { list-style: none; } #arr li { display: inline-block; margin-right: 8px; }""",
        js="""function binarySearch(a, t){let l=0,r=a.length-1;while(l<=r){const m=Math.floor((l+r)/2);if(a[m]===t)return m;if(a[m]<t)l=m+1;else r=m-1;}return -1;}""",
    )


def main() -> None:
    generator = PromptGenerator()

    user_state = _make_user_state()
    retrieved_context = _read_context_text()
    history = _make_conversation_history()
    code = _maybe_make_code_context()

    user_message = os.getenv("PG_USER_MESSAGE", "请用通俗的语言解释一下二分查找，并给我一个简单示例。")
    task_context = os.getenv("PG_TASK_CONTEXT", "实现一个可视化二分查找的小练习")
    topic_id = os.getenv("PG_TOPIC_ID", "binary_search")

    system_prompt, messages = generator.create_prompts(
        user_state=user_state,
        retrieved_context=retrieved_context,
        conversation_history=history,
        user_message=user_message,
        code_content=code,
        task_context=task_context,
        topic_id=topic_id,
    )

    print("\n===== system_prompt =====\n")
    print(system_prompt)
    print("\n===== messages =====\n")
    for i, m in enumerate(messages):
        print(f"[{i}] {m['role']}:\n{m['content']}\n")


if __name__ == "__main__":
    main()



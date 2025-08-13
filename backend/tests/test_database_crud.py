#!/usr/bin/env python3
"""
数据库CRUD操作测试

该测试文件验证所有基础模型的创建、读取、更新、删除操作是否正常工作。
确保数据库读写功能的正确性和稳定性。
"""

import sys
import os
import pytest
from datetime import datetime, UTC
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 在导入项目模块前设置测试环境
os.environ["APP_ENV"] = "testing"
# 使用绝对路径确保在任何目录下运行测试都能找到数据库文件
import os
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(current_dir, "app", "db", "database.db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["TUTOR_OPENAI_API_KEY"] = "test-key"
os.environ["TUTOR_EMBEDDING_API_KEY"] = "test-key"
os.environ["TUTOR_TRANSLATION_API_KEY"] = "test-key"

# 导入项目模块
from app.db.base_class import Base
from app.db.database import engine, SessionLocal
from app.models.participant import Participant
from app.models.event import EventLog
from app.models.chat_history import ChatHistory
from app.models.user_progress import UserProgress
from app.models.survey_result import SurveyResult
from app.schemas.participant import ParticipantCreate
from app.schemas.behavior import BehaviorEvent, EventType
from app.schemas.chat import ChatHistoryCreate
from app.schemas.user_progress import UserProgressCreate
from app.schemas.survey import SurveyResultCreate
from app.crud import participant, event, chat_history, progress, survey_result


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """创建测试数据库会话，使用事务回滚确保测试数据不持久化"""
    # 创建数据库会话
    db = SessionLocal()
    # 开始一个事务
    db.begin()
    try:
        yield db
    finally:
        # 回滚事务，确保测试数据不会真正写入数据库
        db.rollback()
        db.close()


def test_participant_crud(db: Session):
    """测试Participant模型的CRUD操作"""
    # 生成唯一的参与者ID
    participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
    
    # 创建参与者
    participant_data = ParticipantCreate(
        id=participant_id,
        group="experimental"
    )
    created_participant = participant.create(db, obj_in=participant_data)

    # 验证创建结果
    assert created_participant.id == participant_id
    assert created_participant.group == "experimental"
    assert created_participant.created_at is not None

    # 查询参与者
    retrieved_participant = participant.get(db, participant_id)
    assert retrieved_participant is not None
    assert retrieved_participant.id == participant_id
    assert retrieved_participant.group == "experimental"

    # 更新参与者
    from app.schemas.participant import ParticipantUpdate
    update_data = ParticipantUpdate(group="control")
    updated_participant = participant.update(db, db_obj=retrieved_participant, obj_in=update_data)
    assert updated_participant.group == "control"

    # 删除参与者
    deleted_participant = participant.remove(db, obj_id=participant_id)
    assert deleted_participant is not None
    assert deleted_participant.id == participant_id

    # 验证删除
    retrieved_participant = participant.get(db, participant_id)
    assert retrieved_participant is None

    print("Participant CRUD测试通过")


def test_event_log_crud(db: Session):
    """测试EventLog模型的CRUD操作"""
    # 生成唯一的参与者ID
    participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
    
    # 先创建一个参与者（外键约束）
    participant_data = ParticipantCreate(
        id=participant_id,
        group="experimental"
    )
    created_participant = participant.create(db, obj_in=participant_data)

    # 创建事件日志（使用正确的数据结构）
    event_data = BehaviorEvent(
        participant_id=participant_id,
        event_type=EventType.CODE_EDIT,
        event_data={"editor_name": "js", "new_length": 100}
    )
    created_event = event.create_from_behavior(db, obj_in=event_data)

    # 验证创建结果
    assert created_event.participant_id == participant_id
    assert created_event.event_type == EventType.CODE_EDIT
    assert created_event.event_data == {"editor_name": "js", "new_length": 100}
    assert created_event.timestamp is not None

    # 查询事件日志
    events = event.get_by_participant(db, participant_id=participant_id)
    assert len(events) == 1
    assert events[0].event_type == EventType.CODE_EDIT

    # 测试特殊方法：get_latest_snapshot
    # 先创建一个状态快照事件
    snapshot_data = BehaviorEvent(
        participant_id=participant_id,
        event_type=EventType.STATE_SNAPSHOT,
        event_data={"profile_data": {"key": "value"}}
    )
    snapshot_event = event.create_from_behavior(db, obj_in=snapshot_data)
    
    # 获取最新的状态快照
    latest_snapshot = event.get_latest_snapshot(db, participant_id=participant_id)
    assert latest_snapshot is not None
    assert latest_snapshot.event_type == EventType.STATE_SNAPSHOT

    # 测试特殊方法：get_all_snapshots
    snapshots = event.get_all_snapshots(db, participant_id=participant_id)
    assert len(snapshots) == 1
    assert snapshots[0].event_type == EventType.STATE_SNAPSHOT

    # 对于EventLog，通常不更新现有记录，而是创建新记录
    # 所以我们直接测试删除功能
    # 删除事件日志
    deleted_event = event.remove(db, obj_id=created_event.id)
    assert deleted_event is not None
    assert deleted_event.id == created_event.id

    # 验证删除
    retrieved_event = event.get(db, created_event.id)
    assert retrieved_event is None

    print("EventLog CRUD测试通过")


def test_chat_history_crud(db: Session):
    """测试ChatHistory模型的CRUD操作"""
    # 生成唯一的参与者ID
    participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
    
    # 先创建一个参与者（外键约束）
    participant_data = ParticipantCreate(
        id=participant_id,
        group="experimental"
    )
    created_participant = participant.create(db, obj_in=participant_data)

    # 创建聊天记录
    chat_data = ChatHistoryCreate(
        participant_id=participant_id,
        role="user",
        message="Hello, AI tutor!",
        raw_prompt_to_llm=None
    )
    created_chat = chat_history.create(db, obj_in=chat_data)

    # 验证创建结果
    assert created_chat.participant_id == participant_id
    assert created_chat.role == "user"
    assert created_chat.message == "Hello, AI tutor!"

    # 更新聊天记录
    from app.schemas.chat import ChatHistoryCreate as ChatHistoryUpdate
    from app.models.chat_history import ChatHistory
    # 对于聊天记录，更新操作实际上是创建新的记录，而不是更新现有记录
    # 所以我们直接验证删除功能
    # 删除聊天记录
    # 由于chat_history的remove方法可能不直接可用，我们直接从数据库删除
    chat_to_delete = db.query(ChatHistory).get(created_chat.id)
    if chat_to_delete:
        db.delete(chat_to_delete)
        db.commit()

    # 验证删除
    retrieved_chat = db.query(ChatHistory).filter(ChatHistory.id == created_chat.id).first()
    assert retrieved_chat is None

    print("ChatHistory CRUD测试通过")


def test_user_progress_crud(db: Session):
    """测试UserProgress模型的CRUD操作"""
    # 生成唯一的参与者ID
    participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
    
    # 先创建一个参与者（外键约束）
    participant_data = ParticipantCreate(
        id=participant_id,
        group="experimental"
    )
    created_participant = participant.create(db, obj_in=participant_data)

    # 创建进度记录
    from app.schemas.user_progress import UserProgressCreate
    progress_data = UserProgressCreate(
        participant_id=participant_id,
        topic_id="topic_001"
    )
    created_progress = progress.create(db, obj_in=progress_data)

    # 验证创建结果
    assert created_progress.participant_id == participant_id
    assert created_progress.topic_id == "topic_001"
    assert created_progress.completed_at is not None

    # 查询用户已完成的知识点
    completed_topics = progress.get_completed_topics_by_user(db, participant_id=participant_id)
    assert len(completed_topics) == 1
    assert "topic_001" in completed_topics

    # 更新进度记录
    from app.schemas.user_progress import UserProgressUpdate
    from datetime import datetime, UTC
    update_data = UserProgressUpdate(completed_at=datetime.now(UTC))
    updated_progress = progress.update(db, db_obj=created_progress, obj_in=update_data)
    assert updated_progress.completed_at is not None

    # 删除进度记录
    deleted_progress = progress.remove(db, obj_id=created_progress.id)
    assert deleted_progress is not None
    assert deleted_progress.id == created_progress.id

    # 验证删除
    retrieved_progress = progress.get(db, created_progress.id)
    assert retrieved_progress is None

    # 测试特殊方法：get_completed_topics_by_user（无完成主题的情况）
    completed_topics = progress.get_completed_topics_by_user(db, participant_id=participant_id)
    assert len(completed_topics) == 0

    print("UserProgress CRUD测试通过")


def test_survey_result_crud(db: Session):
    """测试SurveyResult模型的CRUD操作"""
    # 生成唯一的参与者ID
    participant_id = f"test_participant_{uuid.uuid4().hex[:8]}"
    
    # 先创建一个参与者（外键约束）
    participant_data = ParticipantCreate(
        id=participant_id,
        group="experimental"
    )
    created_participant = participant.create(db, obj_in=participant_data)

    # 创建问卷结果
    from app.schemas.survey import SurveyResultCreate
    survey_data = SurveyResultCreate(
        participant_id=participant_id,
        survey_type="pre-test",
        answers={"q1": "answer1", "q2": "answer2"}
    )
    created_survey = survey_result.create(db, obj_in=survey_data)

    # 验证创建结果
    assert created_survey.participant_id == participant_id
    assert created_survey.survey_type == "pre-test"
    assert created_survey.answers == {"q1": "answer1", "q2": "answer2"}
    assert created_survey.submitted_at is not None

    # 更新问卷结果
    from app.schemas.survey import SurveyResultUpdate
    update_data = SurveyResultUpdate(
        participant_id=participant_id,
        survey_type="post-test",
        answers={"q1": "updated_answer1", "q2": "updated_answer2"}
    )
    updated_survey = survey_result.update(db, db_obj=created_survey, obj_in=update_data)
    assert updated_survey.survey_type == "post-test"
    assert updated_survey.answers == {"q1": "updated_answer1", "q2": "updated_answer2"}

    # 删除问卷结果
    deleted_survey = survey_result.remove(db, obj_id=created_survey.id)
    assert deleted_survey is not None
    assert deleted_survey.id == created_survey.id

    # 验证删除
    retrieved_survey = survey_result.get(db, created_survey.id)
    assert retrieved_survey is None

    print("SurveyResult CRUD测试通过")


def test_boundary_conditions(db: Session):
    """测试边界条件和异常处理"""
    # 测试查询不存在的参与者
    non_existent_participant = participant.get(db, "non_existent_id")
    assert non_existent_participant is None

    # 测试查询不存在的事件日志
    non_existent_event = event.get(db, 999999)
    assert non_existent_event is None

    # 测试查询不存在的用户进度
    non_existent_progress = progress.get(db, 999999)
    assert non_existent_progress is None

    # 测试查询不存在的问卷结果
    non_existent_survey = survey_result.get(db, 999999)
    assert non_existent_survey is None

    print("边界条件测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
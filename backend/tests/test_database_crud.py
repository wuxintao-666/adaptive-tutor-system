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

#Aeolyn:我是在backend目录下运行的联合测试所以改了下路径
os.environ["DATABASE_URL"] = "sqlite:///./app/db/database.db"  

#Aeolyn:原本的设置会覆盖我的环境，所以我把这些注掉了，后续有必要可以取消
# os.environ["DATABASE_URL"] = "sqlite:///./backend/app/db/database.db"  # 使用实际的数据库文件
# os.environ["TUTOR_OPENAI_API_KEY"] = "test-key"
# os.environ["TUTOR_EMBEDDING_API_KEY"] = "test-key"
# os.environ["TUTOR_TRANSLATION_API_KEY"] = "test-key"


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
    participant.create(db, obj_in=participant_data)

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
    participant.create(db, obj_in=participant_data)

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
    participant.create(db, obj_in=participant_data)

    # 创建进度记录
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
    participant.create(db, obj_in=participant_data)

    # 创建问卷结果
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

    print("SurveyResult CRUD测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
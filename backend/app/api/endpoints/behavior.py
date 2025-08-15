# backend/app/api/endpoints/behavior.py
"""
API端点，用于接收和处理前端发送的行为事件。
"""
import logging
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.behavior import BehaviorEvent
from app.crud.crud_event import event as crud_event
from app.services.user_state_service import UserStateService
from app.services.behavior_interpreter_service import behavior_interpreter_service
from app.config.dependency_injection import get_db, get_user_state_service

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/log", status_code=status.HTTP_202_ACCEPTED, summary="记录行为事件")
def log_behavior(
    event_in: BehaviorEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_state_service: UserStateService = Depends(get_user_state_service)
):
    """
    接收、持久化并解释单个行为事件。

    - **异步持久化**: 立即将原始事件加入后台任务队列，写入数据库。
    - **同步解释**: 将事件交给行为解释服务进行实时分析和处理。
    - **快速响应**: 立即返回 `202 Accepted`，不等待后台任务完成。
    """
    # 任务1: 异步持久化原始事件
    background_tasks.add_task(crud_event.create_from_behavior, db=db, obj_in=event_in)

    # 任务2: 同步调用行为解释服务处理事件
    try:
        behavior_interpreter_service.interpret_event(
            event=event_in,
            user_state_service=user_state_service,
            db_session=db
        )
    except Exception as e:
        logger.error(f"Error interpreting event for participant {event_in.participant_id}: {e}", exc_info=True)
        # 即使解释失败，事件也已记录，所以不改变响应状态

    return {"status": "Event received for processing"}

# backend/app/services/behavior_interpreter_service.py
"""
BehaviorInterpreterService（行为解释服务）

- 接收前端上报的单条行为事件（BehaviorEvent 或等价 dict）
- 根据规则（例如 BKT 更新、挫败检测等）解释事件并触发 UserStateService 的具体处理（更新 BKT、设置情绪标志、创建快照等）
- 设计为容错，尽量不抛异常到 API 层

和现有模块的兼容性：
- 依赖 app.services.user_state_service.UserStateService 的方法：
    - get_or_create_profile(participant_id, db: Session = None, group="...")
    - update_bkt_on_submission(participant_id, topic_id, is_correct)
    - maybe_create_snapshot(participant_id, db, background_tasks=None)
- 依赖 app.crud.crud_event.event 中的方法：
    - get_by_participant(db, participant_id)
    - get_latest_snapshot, get_after_timestamp, get_count_after_timestamp, get_count_by_participant, get_all_snapshots
  （如果 crud 接口名称不同，需要调整）
"""

import logging
from datetime import datetime, timedelta
import traceback
from typing import Optional, Any, Dict, Callable

# 规则参数（可在这里调整或从配置中读取）
FRUSTRATION_WINDOW_MINUTES = 2
FRUSTRATION_ERROR_RATE_THRESHOLD = 0.75
FRUSTRATION_INTERVAL_SECONDS = 10

# 配置日志
logger = logging.getLogger(__name__)


class BehaviorInterpreterService:
    def __init__(self, 
                 window_minutes: int = FRUSTRATION_WINDOW_MINUTES,
                 error_rate_threshold: float = FRUSTRATION_ERROR_RATE_THRESHOLD,
                 interval_seconds: int = FRUSTRATION_INTERVAL_SECONDS):
        """
        初始化行为解释服务
        
        Args:
            window_minutes: 挫败检测时间窗口（分钟）
            error_rate_threshold: 挫败检测错误率阈值
            interval_seconds: 挫败检测时间间隔（秒）
        """
        self.window_minutes = window_minutes
        self.error_rate_threshold = error_rate_threshold
        self.interval_seconds = interval_seconds
        
        # 创建事件类型到处理方法的映射
        self._event_handlers: Dict[str, Callable] = {
            "test_submission": self._handle_test_submission,
            "ai_help_request": self._handle_ai_help_request,
        }
        # 添加轻量级事件的处理
        for event_type in ("dom_element_select", "code_edit", "page_focus_change", "user_idle"):
            self._event_handlers[event_type] = self._handle_lightweight_event

    def interpret_event(self, event, user_state_service=None, db_session=None, is_replay: bool = False):
        """
        主入口：解释单条行为事件。
        
        Args:
            event: BehaviorEvent pydantic 实例或等价 dict（必须包含 participant_id, event_type, event_data, timestamp 可选）
            user_state_service: UserStateService 实例，用于状态更新操作
            db_session: 数据库会话，用于挫败检测等需要查询历史数据的操作
            is_replay: 如果为 True，表示这是从历史回放的事件（部分操作可跳过持久化等）
        """
        # --- 1. 规范输入，容错解析 event 字段 ---
        try:
            participant_id = getattr(event, "participant_id", None) or (event.get("participant_id") if isinstance(event, dict) else None)
            event_type = getattr(event, "event_type", None) or (event.get("event_type") if isinstance(event, dict) else None)
            event_data = getattr(event, "event_data", None) or (event.get("event_data") if isinstance(event, dict) else {}) or {}
            timestamp = getattr(event, "timestamp", None) or (event.get("timestamp") if isinstance(event, dict) else None)
            
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    timestamp = datetime.utcnow()
            if timestamp is None:
                timestamp = datetime.utcnow()
                
            if not participant_id or not event_type:
                logger.warning("BehaviorInterpreterService: 缺少必要字段 participant_id 或 event_type")
                return
                
        except Exception as e:
            logger.error(f"BehaviorInterpreterService: 无效的 event 输入：{event}, 错误: {e}")
            return

        # 使用字典映射来分发事件处理
        handler = self._event_handlers.get(event_type)
        if handler:
            try:
                # 为不同的处理方法提供相应的参数
                if event_type == "test_submission":
                    # 延迟导入 crud_event（用于读取历史事件以做挫败检测）
                    crud_event = None
                    SessionLocal = None
                    if db_session is None:
                        try:
                            from app.crud.crud_event import event as crud_event  
                            from app.db.database import SessionLocal
                        except ImportError as e:
                            logger.error(f"BehaviorInterpreterService: 无法导入数据库相关模块: {e}")
                            
                    handler(participant_id, event_data, timestamp, 
                           user_state_service, db_session, crud_event, SessionLocal, is_replay)
                elif event_type == "ai_help_request":
                    handler(participant_id, user_state_service, is_replay)
                elif event_type in ("dom_element_select", "code_edit", "page_focus_change", "user_idle"):
                    handler(participant_id, event_type, user_state_service, is_replay)
            except Exception as e:
                logger.error(f"BehaviorInterpreterService: 处理事件 {event_type} 时发生错误: {e}", exc_info=True)
        else:
            # 默认：不执行任何动作（原始事件仍然会写入 event_logs 以便离线分析）
            logger.info(f"BehaviorInterpreterService: 未处理的事件类型 {event_type}")
            return

    def _handle_test_submission(self, participant_id, event_data, timestamp, 
                               user_state_service, db_session, crud_event, SessionLocal, is_replay):
        """处理测试提交事件"""
        # 从 event_data 中解析 topic_id 与正确性标志
        # 处理 event_data 可能是 Pydantic 模型或字典的情况
        topic_id = getattr(event_data, "topic_id", None) or event_data.get("topic_id") or event_data.get("topic") or None
        # 支持前端可能传的字段名 is_correct 或 passed
        is_correct = None
        if "is_correct" in event_data:
            is_correct = bool(event_data.get("is_correct"))
        elif "passed" in event_data:
            is_correct = bool(event_data.get("passed"))

        # 1) 更新 BKT：优先调用 UserStateService 中的封装方法
        if user_state_service is not None and topic_id is not None and is_correct is not None:
            try:
                # 注意：update_bkt_on_submission 的签名在 user_state_service.py 中为 (participant_id, topic_id, is_correct)
                mastery = user_state_service.update_bkt_on_submission(participant_id, topic_id, is_correct)
                # TODO: 如果需要，可以把 mastery 写入日志或触发其他领域事件
            except Exception as e:
                logger.error(f"BehaviorInterpreterService: 调用 update_bkt_on_submission 失败：{e}")

        # 2) 挫败检测（PRD：过去 window_minutes 分钟内错误率 > threshold 且 最近两次提交间隔 < interval_seconds）
        # 仅在 is_correct 为 False 时触发检测，且 crud_event 可用时才执行
        if is_correct is False and crud_event is not None and SessionLocal is not None:
            self._detect_frustration(
                participant_id, timestamp, user_state_service, 
                db_session, crud_event, SessionLocal, is_replay
            )

    def _detect_frustration(self, participant_id, timestamp, user_state_service, 
                           db_session, crud_event, SessionLocal, is_replay):
        """检测用户挫败状态"""
        db = None
        try:
            # 如果没有传入 db_session，创建新的数据库会话
            if db_session is None:
                db = SessionLocal()
            else:
                db = db_session
                
            # 获取该 participant 的所有历史事件（由 crud_event 提供）
            all_events = crud_event.get_by_participant(db, participant_id=participant_id)
            # 过滤出 window 时间内的 test_submission 事件
            window_start = timestamp - timedelta(minutes=self.window_minutes)
            recent_submissions = [
                ev for ev in (all_events or [])
                if getattr(ev, "event_type", None) == "test_submission"
                and getattr(ev, "timestamp", timestamp) >= window_start
            ]
            total = len(recent_submissions)
            if total > 0:
                error_count = 0
                for ev in recent_submissions:
                    ed = getattr(ev, "event_data", {}) or {}
                    if ed.get("is_correct") is False or ed.get("passed") is False:
                        error_count += 1
                error_rate = error_count / total if total > 0 else 0.0

                # 计算最后两次提交的间隔（秒）
                interval = 999999
                if total >= 2:
                    recent_sorted = sorted(recent_submissions, key=lambda x: x.timestamp)
                    last = recent_sorted[-1].timestamp
                    prev = recent_sorted[-2].timestamp
                    interval = (last - prev).total_seconds()

                # 判定是否挫败
                if error_rate > self.error_rate_threshold and interval < self.interval_seconds:
                    # 遵循TDD架构，调用UserStateService的方法而不是直接修改状态
                    if not is_replay and user_state_service is not None:
                        user_state_service.handle_frustration_event(participant_id)
                    
        except Exception as e:
            logger.error(f"BehaviorInterpreterService: 挫败检测异常（非阻塞）：{e}")
            if not is_replay:
                traceback.print_exc()
        finally:
            # 只有当我们创建了新的数据库会话时才关闭它
            if db is not None and db_session is None:
                db.close()

    def _handle_ai_help_request(self, participant_id, user_state_service, is_replay):
        """处理AI求助请求事件"""
        if user_state_service is None:
            return
            
        try:
            # 遵循TDD架构，调用UserStateService的方法而不是直接修改状态
            if not is_replay:
                user_state_service.handle_ai_help_request(participant_id)
        except Exception as e:
            logger.error(f"BehaviorInterpreterService: ai_help_request 处理异常：{e}")

    def _handle_lightweight_event(self, participant_id, event_type, user_state_service, is_replay):
        """处理轻量级事件（如页面焦点变化、代码编辑等）"""
        if user_state_service is None:
            return
            
        try:
            # 遵循TDD架构，调用UserStateService的方法而不是直接修改状态
            if not is_replay:
                user_state_service.handle_lightweight_event(participant_id, event_type)
        except Exception as e:
            logger.error(f"BehaviorInterpreterService: 轻量事件处理异常：{e}")

# 单例导出
behavior_interpreter_service = BehaviorInterpreterService()
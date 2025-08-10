# backend/app/services/behavior_interpreter_service.py
"""
BehaviorInterpreterService（行为解释服务）

- 接收前端上报的单条行为事件（BehaviorEvent 或等价 dict）
- 根据规则（例如 BKT 更新、挫败检测等）解释事件并触发 UserStateService 的具体处理（更新 BKT、设置情绪标志、创建快照等）
- 设计为容错，尽量不抛异常到 API 层

和现有模块的兼容性：
- 依赖 app.services.user_state_service.UserStateService 的方法：
    - get_or_create_profile(participant_id, db: Session = None, group="...") -> (profile, is_new)
    - update_bkt_on_submission(participant_id, topic_id, is_correct)
    - maybe_create_snapshot(participant_id, db, background_tasks=None)
- 依赖 app.crud.crud_event.event 中的方法：
    - get_by_participant(db, participant_id)
    - get_latest_snapshot, get_after_timestamp, get_count_after_timestamp, get_count_by_participant, get_all_snapshots
  （如果 crud 接口名称不同，需要调整）
"""

from datetime import datetime, timedelta
import traceback

# 规则参数（可在这里调整或从配置中读取）
FRUSTRATION_WINDOW_MINUTES = 2
FRUSTRATION_ERROR_RATE_THRESHOLD = 0.75
FRUSTRATION_INTERVAL_SECONDS = 10


class BehaviorInterpreterService:
    def __init__(self):
        # 将规则参数保存在实例中，便于未来外部配置化
        self.window_minutes = FRUSTRATION_WINDOW_MINUTES
        self.error_rate_threshold = FRUSTRATION_ERROR_RATE_THRESHOLD
        self.interval_seconds = FRUSTRATION_INTERVAL_SECONDS

    def interpret_event(self, event, is_replay: bool = False):
        """
        主入口：解释单条行为事件。
        参数:
            event: BehaviorEvent pydantic 实例或等价 dict（必须包含 participant_id, event_type, event_data, timestamp 可选）
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
                except Exception:
                    timestamp = datetime.utcnow()
            if timestamp is None:
                timestamp = datetime.utcnow()
        except Exception:
            print("BehaviorInterpreterService: 无效的 event 输入：", event)
            traceback.print_exc()
            return

        # 延迟导入以避免循环依赖（UserStateService 会导入解释器）
        try:
            from app.services.user_state_service import UserStateService
        except Exception as e:
            print("BehaviorInterpreterService: 无法导入 UserStateService:", e)
            traceback.print_exc()
            return

        # 延迟导入 crud_event（用于读取历史事件以做挫败检测）
        try:
            from app.crud.crud_event import event as crud_event  
            from app.db.database import SessionLocal  # TODO: 目前项目里的db，里面的内容可能需要修改
        except Exception:
            crud_event = None
            SessionLocal = None

        # 帮助函数：安全获取 UserStateService 实例
        def _get_user_state_service():
            try:
                return UserStateService()
            except Exception as e:
                print("BehaviorInterpreterService: 无法实例化 UserStateService:", e)
                return None

        # ------------------------ 处理 test_submission ------------------------
        if event_type == "test_submission":
            # 从 event_data 中解析 topic_id 与正确性标志
            topic_id = event_data.get("topic_id") or event_data.get("topic") or None
            # 支持前端可能传的字段名 is_correct 或 passed
            is_correct = None
            if "is_correct" in event_data:
                is_correct = bool(event_data.get("is_correct"))
            elif "passed" in event_data:
                is_correct = bool(event_data.get("passed"))

            # 1) 更新 BKT：优先调用 UserStateService 中的封装方法
            try:
                us = _get_user_state_service()
                if us is not None and topic_id is not None and is_correct is not None:
                    # user_state_service.update_bkt_on_submission 返回 mastery probability（float）
                    try:
                        # 注意：update_bkt_on_submission 的签名在 user_state_service.py 中为 (participant_id, topic_id, is_correct)
                        mastery = us.update_bkt_on_submission(participant_id, topic_id, is_correct)
                        # TODO: ceq如果需要，可以把 mastery 写入日志或触发其他领域事件
                    except Exception as e:
                        print("BehaviorInterpreterService: 调用 update_bkt_on_submission 失败：", e)
                else:
                    # 如果缺少必要信息，不进行 BKT 更新
                    pass
            except Exception as e:
                print("BehaviorInterpreterService: BKT 更新异常：", e)

            # 2) 挫败检测（PRD：过去 window_minutes 分钟内错误率 > threshold 且 最近两次提交间隔 < interval_seconds）
            # 仅在 is_correct 为 False 时触发检测，且 crud_event 可用时才执行
            if is_correct is False and crud_event is not None and SessionLocal is not None:
                try:
                    db = SessionLocal()
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
                            # 将挫败信息写入用户内存状态（使用 UserStateService 的 profile）
                            try:
                                us = _get_user_state_service()
                                if us is not None:
                                    # get_or_create_profile 返回 (profile, is_new)
                                    try:
                                        profile, _ = us.get_or_create_profile(participant_id, db)
                                    except TypeError:
                                        # 兼容无 db 参数签名
                                        profile, _ = us.get_or_create_profile(participant_id)
                                    # profile 应是 StudentProfile 实例，设置情绪字段
                                    try:
                                        profile.emotion_state['is_frustrated'] = True
                                    except Exception:
                                        # profile 可能为 dict-like，做兼容处理
                                        try:
                                            profile['emotion_state'] = profile.get('emotion_state', {})
                                            profile['emotion_state']['is_frustrated'] = True
                                        except Exception:
                                            pass

                                    # 创建快照以持久化情绪变化（如果 user_state_service 提供了 maybe_create_snapshot）
                                    try:
                                        if hasattr(us, "maybe_create_snapshot"):
                                            # 调用时尽量传 db，以便 maybe_create_snapshot 能使用它
                                            us.maybe_create_snapshot(participant_id, db=db, background_tasks=None)
                                    except Exception as e:
                                        print("BehaviorInterpreterService: 调用 maybe_create_snapshot 失败：", e)
                            except Exception as e:
                                print("BehaviorInterpreterService: 标记挫败失败：", e)
                    db.close()
                except Exception as e:
                    print("BehaviorInterpreterService: 挫败检测异常（非阻塞）：", e, traceback.format_exc())

            # 处理完 test_submission，返回
            return

        # ------------------------ 处理 ai_help_request ------------------------
        if event_type == "ai_help_request":
            try:
                us = _get_user_state_service()
                if us is not None:
                    # 获取/创建 profile（尝试传 db=None）
                    try:
                        profile, _ = us.get_or_create_profile(participant_id, None)
                    except TypeError:
                        profile, _ = us.get_or_create_profile(participant_id)
                    # 增加求助计数
                    try:
                        profile.behavior_counters.setdefault("help_requests", 0)
                        profile.behavior_counters["help_requests"] += 1
                    except Exception:
                        # 兼容 dict-like profile
                        try:
                            bc = profile.get("behavior_counters", {})
                            bc["help_requests"] = bc.get("help_requests", 0) + 1
                            profile["behavior_counters"] = bc
                        except Exception:
                            pass
                    # 选择性地创建快照以保存状态
                    try:
                        if hasattr(us, "maybe_create_snapshot"):
                            us.maybe_create_snapshot(participant_id, db=None)
                    except Exception:
                        pass
            except Exception as e:
                print("BehaviorInterpreterService: ai_help_request 处理异常：", e)

            return

        # ------------------------ 处理其它轻量事件 ------------------------
        # dom_element_select, code_edit, page_focus_change, user_idle：主要更新行为计数器或简单状态
        if event_type in ("dom_element_select", "code_edit", "page_focus_change", "user_idle"):
            try:
                us = _get_user_state_service()
                if us is not None:
                    try:
                        profile, _ = us.get_or_create_profile(participant_id, None)
                    except TypeError:
                        profile, _ = us.get_or_create_profile(participant_id)
                    # 根据事件类型增加相应计数
                    try:
                        if event_type == "page_focus_change":
                            profile.behavior_counters.setdefault("focus_changes", 0)
                            profile.behavior_counters["focus_changes"] += 1
                        elif event_type == "user_idle":
                            profile.behavior_counters.setdefault("idle_count", 0)
                            profile.behavior_counters["idle_count"] += 1
                        elif event_type == "dom_element_select":
                            profile.behavior_counters.setdefault("dom_selects", 0)
                            profile.behavior_counters["dom_selects"] += 1
                        elif event_type == "code_edit":
                            profile.behavior_counters.setdefault("code_edits", 0)
                            profile.behavior_counters["code_edits"] += 1
                    except Exception:
                        # dict-like 兼容
                        try:
                            bc = profile.get("behavior_counters", {})
                            key_map = {
                                "page_focus_change": "focus_changes",
                                "user_idle": "idle_count",
                                "dom_element_select": "dom_selects",
                                "code_edit": "code_edits"
                            }
                            k = key_map.get(event_type)
                            bc[k] = bc.get(k, 0) + 1
                            profile["behavior_counters"] = bc
                        except Exception:
                            pass

                    # 可选：按策略创建快照
                    try:
                        if hasattr(us, "maybe_create_snapshot"):
                            us.maybe_create_snapshot(participant_id, db=None)
                    except Exception:
                        pass
            except Exception as e:
                print("BehaviorInterpreterService: 轻量事件处理异常：", e)

            return

        # 默认：不执行任何动作（原始事件仍然会写入 event_logs 以便离线分析）
        return


# 单例导出
behavior_interpreter_service = BehaviorInterpreterService()

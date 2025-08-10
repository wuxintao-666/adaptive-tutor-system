from pydantic import BaseModel
from typing import Dict, Any,Literal, Optional
from datetime import datetime


class BehaviorEvent(BaseModel):
    """
    行为事件模型，对应前端behavior_tracker.js捕获的事件
    
    记录用户在学习过程中的各种交互行为，用于行为分析和学习状态评估。
    
    Attributes:
        participant_id: 参与者ID，用于标识特定用户
        event_type: 事件类型，如 'click', 'scroll', 'code_change' 等
        event_data: 事件数据，包含事件相关的详细信息，字典格式
        timestamp: 事件发生的时间戳，可选字段，默认为当前时间
    """
    # 与 TDD-II-07 对齐的事件类型枚举（若将来扩展只需在此添加）TODO：ceq可能添加热力图事件（heatmap_snapshot）
    EventType = Literal[
    "code_edit",
    "ai_help_request",
    "test_submission",
    "dom_element_select",
    "user_idle",
    "page_focus_change"
]
    # TODO: cxz 需要根据TDD-II-07中的事件类型定义，补充字段说明和验证规则
    participant_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
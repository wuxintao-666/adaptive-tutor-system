from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class BehaviorEvent(BaseModel):
    """
    行为事件模型，对应前端behavior_tracker.js捕获的事件
    """
    # TODO: cxz 需要根据TDD-II-07中的事件类型定义，补充字段说明和验证规则
    participant_id: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 接口通用字段
class UserProgressBase(BaseModel):
    participant_id: str
    topic_id: str

# 用于创建接口的输入模型
class UserProgressCreate(UserProgressBase):
    pass

# 用于更新接口的输入模型
class UserProgressUpdate(BaseModel):
    completed_at: Optional[datetime]

# 用于返回用户已完成的知识点ID列表
class UserProgressResponse(BaseModel):
    completed_topics: list[str]

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 用户进度的基础数据结构
class UserProgressBase(BaseModel):
    participant_id: str
    topic_id: str

# 创建用户的数据结构
class UserProgressCreate(UserProgressBase):
    pass

# 更新用户的数据结构
class UserProgressUpdate(BaseModel):
    completed_at: Optional[datetime] = None

# 响应用户进度的数据结构
class UserProgressResponse(BaseModel):
    completed_topics: List[str]

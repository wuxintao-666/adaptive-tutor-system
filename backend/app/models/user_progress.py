from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UserProgress(Base):
    __tablename__ = "user_progress"
    # TODO:  需要根据TDD-II-07中的事件类型定义，补充字段说明和验证规则
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(String, index=True, nullable=False)  # 用户唯一标识
    topic_id = Column(String, index=True, nullable=False)        # 知识点唯一标识
    completed_at = Column(DateTime, default=datetime.utcnow)     # 完成时间，可选字段

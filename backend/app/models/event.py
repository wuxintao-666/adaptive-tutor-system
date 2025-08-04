from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)
    event_data = Column(JSON)

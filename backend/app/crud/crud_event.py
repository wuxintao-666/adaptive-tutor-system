from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from .base import CRUDBase
from ..models.event import EventLog
from ..schemas.behavior import BehaviorEvent

class CRUDEvent(CRUDBase[EventLog, BehaviorEvent, BehaviorEvent]):
    def get_by_participant(self, db: Session, *, participant_id: str) -> List[EventLog]:
        return db.query(self.model).filter(self.model.participant_id == participant_id).order_by(self.model.timestamp).all()

    def get_latest_snapshot(self, db: Session, *, participant_id: str) -> Optional[EventLog]:
        return db.query(self.model).filter(
            self.model.participant_id == participant_id,
            self.model.event_type == "state_snapshot"
        ).order_by(self.model.timestamp.desc()).first()

    def get_after_timestamp(self, db: Session, *, participant_id: str, timestamp: datetime) -> List[EventLog]:
        return db.query(self.model).filter(
            self.model.participant_id == participant_id,
            self.model.timestamp > timestamp
        ).order_by(self.model.timestamp).all()

    def get_count_after_timestamp(self, db: Session, *, participant_id: str, timestamp: datetime) -> int:
        return db.query(self.model).filter(
            self.model.participant_id == participant_id,
            self.model.timestamp > timestamp
        ).count()
        
    def get_count_by_participant(self, db: Session, *, participant_id: str) -> int:
        return db.query(self.model).filter(self.model.participant_id == participant_id).count()

    def get_all_snapshots(self, db: Session, *, participant_id: str) -> List[EventLog]:
        return db.query(self.model).filter(
            self.model.participant_id == participant_id,
            self.model.event_type == "state_snapshot"
        ).order_by(self.model.timestamp.asc()).all()

    def create_from_behavior(self, db: Session, *, obj_in: BehaviorEvent) -> EventLog:
        return self.create(db, obj_in=obj_in)

event = CRUDEvent(EventLog)

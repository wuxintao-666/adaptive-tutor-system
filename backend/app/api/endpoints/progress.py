# backend/app/api/endpoints/progress.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas.response import StandardResponse
from app.schemas.user_progress import UserProgressResponse


# from app.dependencies import get_db
# TODO:暂时注释掉，因为get_db还未定义
from app.crud.crud_progress import progress 

router = APIRouter()


@router.get("/participants/{participant_id}/progress", response_model=StandardResponse[UserProgressResponse])
def get_user_progress(participant_id: str, db: Session = Depends(get_db)):
    completed_topics = progress.get_completed_topics_by_user(
        db, participant_id=participant_id
    )
    return StandardResponse(data={"completed_topics": completed_topics})

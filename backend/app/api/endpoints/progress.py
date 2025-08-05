# backend/app/api/endpoints/progress.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.response import StandardResponse
from app.schemas.user_progress import UserProgressResponse


from app.crud.crud_progress import progress

router = APIRouter()


@router.get("/participants/{participant_id}/progress", response_model=StandardResponse[UserProgressResponse])
def get_user_progress(participant_id: str, db: Session = Depends(get_db)):
    # 暂时返回默认的已完成主题，不依赖数据库
    completed_topics = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img', 'table', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'form', 'input', 'button', 'textarea', 'select', 'option']
    return StandardResponse(data={"completed_topics": completed_topics})

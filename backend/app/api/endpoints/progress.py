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
    try:
        completed_topics = progress.get_completed_topics_by_user(
            db, participant_id=participant_id
        )
        print(f"✅ 数据库连接正常，用户进度已加载: {participant_id}")
        return StandardResponse(data={
            "completed_topics": completed_topics,
            "db_status": "connected"
        })
    except Exception as e:
        # 如果数据库查询失败，返回默认值
        print(f"⚠️ 数据库连接失败，使用默认进度数据: {e}")
        completed_topics = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'img', 'table', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'form', 'input', 'button', 'textarea', 'select', 'option']
        return StandardResponse(data={
            "completed_topics": completed_topics,
            "db_status": "disconnected",
            "db_error": str(e)
        })

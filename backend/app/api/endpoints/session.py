from app.services import user_state_service
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.response import StandardResponse
from app.schemas.session import SessionInitiateRequest, SessionInitiateResponse

router = APIRouter()

@router.post("/initiate", response_model=StandardResponse[SessionInitiateResponse])
def initiate_session(
    response: Response,
    session_in: SessionInitiateRequest,
    db: Session = Depends(get_db)
):
    # 获取或创建用户配置
    profile = user_state_service.get_or_create_profile(session_in.username, db)
    
    if profile.is_new_user:
        response.status_code = status.HTTP_201_CREATED

    # 构建响应数据
    response_data = SessionInitiateResponse(
        participant_id=profile.participant_id,
        username=profile.username,
        is_new_user=profile.is_new_user
    )
    
    # 返回标准成功响应
    return StandardResponse(
        data=response_data
    )
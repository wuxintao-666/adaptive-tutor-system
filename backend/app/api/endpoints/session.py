from fastapi import HTTPException, status
from app.services import user_state_service
from app.schemas.session import SessionInitiateRequest, SessionInitiateResponse
from app.schemas.response import StandardResponse
from sqlalchemy.orm import Session

@router.post("/initiate", response_model=StandardResponse[SessionInitiateResponse])
async def initiate_session(
    session_in: SessionInitiateRequest,
    db: Session = Depends(get_db)
):
    try:
        # 获取或创建用户配置
        profile = user_state_service.get_or_create_profile(session_in.username, db)
        
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
        
    except Exception as e:
        # 记录错误日志
        print(f"Error initiating session: {str(e)}")
        # 返回标准错误响应
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": 500, "message": "Failed to initiate session"}
        )
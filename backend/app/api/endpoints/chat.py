# backend/app/api/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...database import get_db
from ...schemas.chat import ChatRequest, ChatResponse
from ...schemas.response import StandardResponse
from ...config.dependency_injection import get_dynamic_controller

router = APIRouter()


@router.post("/ai/chat", response_model=StandardResponse[ChatResponse])
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
) -> StandardResponse[ChatResponse]:
    """
    与AI进行对话
    
    Args:
        request: 聊天请求
        db: 数据库会话
        
    Returns:
        StandardResponse[ChatResponse]: AI回复
    """
    try:
        # 验证请求
        if not request.participant_id:
            raise HTTPException(status_code=400, detail="participant_id is required")
        
        if not request.user_message:
            raise HTTPException(status_code=400, detail="user_message is required")
        
        # 获取动态控制器实例并调用生成回复
        controller = get_dynamic_controller()
        response = await controller.generate_adaptive_response(
            request=request,
            db=db
        )
        
        return StandardResponse(
            code=200,
            message="AI response generated successfully",
            data=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat_with_ai: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/ai/user-state/{participant_id}")
async def get_user_state(
    participant_id: str,
    db: Session = Depends(get_db)
) -> StandardResponse[Dict[str, Any]]:
    """
    获取用户状态
    
    Args:
        participant_id: 参与者ID
        db: 数据库会话
        
    Returns:
        StandardResponse[Dict[str, Any]]: 用户状态
    """
    try:
        controller = get_dynamic_controller()
        user_state = controller.get_user_state(
            participant_id=participant_id,
            db=db
        )
        
        return StandardResponse(
            code=200,
            message="User state retrieved successfully",
            data=user_state
        )
        
    except Exception as e:
        print(f"Error getting user state: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/ai/services/status")
async def get_services_status() -> StandardResponse[Dict[str, bool]]:
    """
    获取所有服务的状态
    
    Returns:
        StandardResponse[Dict[str, bool]]: 服务状态
    """
    try:
        controller = get_dynamic_controller()
        services_status = controller.validate_services()
        
        return StandardResponse(
            code=200,
            message="Services status retrieved successfully",
            data=services_status
        )
        
    except Exception as e:
        print(f"Error getting services status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

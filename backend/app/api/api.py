from fastapi import APIRouter

from ..api.endpoints import session, chat, submission, content

api_router = APIRouter()
api_router.include_router(session.router, prefix="/session", tags=["session"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(submission.router, prefix="/submission", tags=["submission"])
api_router.include_router(content.router, tags=["learning-content", "test-tasks"])
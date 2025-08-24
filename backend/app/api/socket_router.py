
from fastapi import APIRouter
from app.api.endpoints import ws_chat

ws_router = APIRouter()
ws_router.include_router(ws_chat.router, prefix="/chat", tags=["chat"])

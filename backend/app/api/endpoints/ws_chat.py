from fastapi import APIRouter, WebSocket, WebSocketDisconnect,Depends
import json
import asyncio
from app.services.llm_gateway import llm_gateway
from sqlalchemy.orm import Session
from app.config.dependency_injection import get_db
from app.services.SocketManager import manager
from app.schemas.chat import SocketRequest, SocketResponse
from app.services.chat_handler import handle_ai_message

router = APIRouter()

@router.websocket("/{user_id}")
async def chat_endpoint(websocket: WebSocket, user_id: str, db: Session = Depends(get_db)):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            manager.update_activity(user_id)
            try:
                request = SocketRequest.parse_raw(data)  
                if request.type == "ai_message":
                    task = asyncio.create_task(handle_ai_message(request, websocket))
                    task.add_done_callback(lambda t: print(f"Task finished: {t.exception()}"))
                # elif request.type == "ping":
                #     await manager.send_json(user_id, SocketResponse(type="pong", sender="system"))
                else:
                   
                    await manager.send_json(user_id, SocketResponse(type="message", sender=user_id, message=request.message))
            except Exception as e:
                await manager.send_json(user_id, SocketResponse(type="error", sender="system", message=str(e), status="error"))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@router.get("/")
async def root():
    return {"message": "WebSocket Server is running"}
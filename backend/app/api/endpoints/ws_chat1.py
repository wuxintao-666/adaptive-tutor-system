from fastapi import APIRouter, WebSocket, WebSocketDisconnect,Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uuid
import json
import time
import asyncio
from app.services.llm_gateway import llm_gateway
from app.services.dynamic_controller import DynamicController
from app.schemas.chat import ChatRequest, ChatResponse
from sqlalchemy.orm import Session

from app.config.dependency_injection import get_db
from app.schemas.chat import ChatRequest, ChatResponse

ws_router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # 存储用户ID与WebSocket连接的映射
        self.active_connections: Dict[str, WebSocket] = {}
        # 存储用户最后活动时间
        self.last_activity: Dict[str, float] = {}
        # 心跳检测间隔(秒)
        self.heartbeat_interval = 30
        # 超时时间(秒)
        self.timeout = 45

    #websocket.
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        self.active_connections[user_id] = websocket
        self.last_activity[user_id] = time.time()
        print(f"用户 {user_id} 已连接。当前活跃连接数: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.last_activity:
            del self.last_activity[user_id]
        print(f"用户 {user_id} 已断开连接。当前活跃连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        disconnected_users = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception:
                disconnected_users.append(user_id)
        
        # 清理已断开的连接
        for user_id in disconnected_users:
            self.disconnect(user_id)

    # async def check_heartbeats(self):
    #     """定期检查心跳，关闭不活跃的连接"""
    #     while True:
    #         await asyncio.sleep(self.heartbeat_interval)
    #         current_time = time.time()
    #         disconnected_users = []
            
    #         for user_id, last_active in self.last_activity.items():
    #             if current_time - last_active > self.timeout:
    #                 print(f"用户 {user_id} 心跳超时，强制断开连接")
    #                 disconnected_users.append(user_id)
            
    #         for user_id in disconnected_users:
    #             if user_id in self.active_connections:
    #                 try:
    #                     await self.active_connections[user_id].close()
    #                 except Exception:
    #                     pass
    #                 self.disconnect(user_id)

    def update_activity(self, user_id: str):
        """更新用户最后活动时间"""
        if user_id in self.last_activity:
            self.last_activity[user_id] = time.time()

manager = ConnectionManager()

@ws_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            manager.update_activity(user_id)
            
            # 解析前端发送的JSON数据
            try:
                message_data = json.loads(data)
                
                # 处理心跳消息
                # if message_data.get("type") == "ping":
                #     pong_response = {
                #         "type": "pong",
                #         "timestamp": message_data.get("timestamp")
                #     }
                #     await websocket.send_text(json.dumps(pong_response))
                #     continue
                
                # 处理普通消息
                sender_id = message_data.get("userId", user_id)
                message = message_data.get("message", "")
                '''
                request = ChatRequest(user_message=message.get("user_message", ""),
                                      conversation_history=message_data.get("conversation_history", []),
                                      code_context=message_data.get("code_context", None),
                                      mode=message_data.get("mode", None),
                                      content_id=message_data.get("content_id", None)
                                     )
                response = await DynamicController.generate_adaptive_response(
                    request=request,
                    db=Session=Depends(get_db),
                )
                '''
                # 流式发送开始信号
                start_response = {
                    "sender": "AI",
                    "message": "",
                    "type": "stream_start"
                }
                await websocket.send_text(json.dumps(start_response))
                # 调用LLM服务获取流式响应
                async for chunk in llm_gateway.get_stream_completion(
                    system_prompt="You are a helpful AI programming tutor.",
                    messages=[{"role": "user", "content": message}]
                ):
                    # 构建流式响应消息
                    stream_response = {
                        "sender": "AI",
                        "message": chunk,
                        "type": "stream"
                    }
                    await websocket.send_text(json.dumps(stream_response))
                    # 添加延迟以控制流式输出速度，避免生成过快
                    #await asyncio.sleep(0.05)  # 50ms延迟，可以根据需要调整
                
                # 流式发送结束信号
                end_response = {
                    "sender": "AI",
                    "message": "",
                    "type": "stream_end"
                }
                await websocket.send_text(json.dumps(end_response))
                
            except json.JSONDecodeError:
                # 如果消息不是JSON格式，直接广播
                response = {
                    "sender": user_id,
                    "message": data,
                    "type": "message"
                }
                #await manager.broadcast(json.dumps(response))
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@ws_router.get("/")
async def root():
    return {"message": "WebSocket Server is running"}

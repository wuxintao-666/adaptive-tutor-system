# # app/api/endpoints/chat_ws.py
# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
# from sqlalchemy.orm import Session
# import json
# import logging

# from app.config.dependency_injection import get_db, get_dynamic_controller
# from app.services.socket_connection import manager
# from app.services.dynamic_controller import DynamicController
# #from app.schemas.socket_message import ChatMessage

# logger = logging.getLogger(__name__)
# ws_router = APIRouter()

# @ws_router.websocket("/chat")
# async def websocket_chat(
#     websocket: WebSocket,
#     participant_id: str,
#     db: Session = Depends(get_db),
#     controller: DynamicController = Depends(get_dynamic_controller)
# ):
#     """WebSocket 端点用于流式 AI 聊天"""
#     async def reconnect_callback():
#         """
#         重连回调函数
#         当连接断开时，此函数将被调用来尝试重新建立连接
#         """
#         try:
#             # 尝试建立新的WebSocket连接
#             await websocket.accept()
#             return websocket
#         except Exception as e:
#             logger.error(f"Failed to reconnect for participant {participant_id}: {str(e)}")
#             return None

#     # 注册重连回调函数
#     manager.register_reconnect_callback(participant_id, reconnect_callback)
        
#     # 将连接加入管理器
#     await manager.connect(websocket, participant_id)
    
#     try:
#         while True:
#             # 接收客户端消息
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
            
#             # 验证消息格式
#             #message = ChatMessage(**message_data)
#             message = message_data
#             logger.info(f"Received message from participant {participant_id}")
            
#             # 创建聊天请求对象（类似于 HTTP 端点中的 ChatRequest）
#             from app.schemas.chat import ChatRequest
#             chat_request = ChatRequest(
#                 participant_id=participant_id,
#                 user_message=,
#                 session_id=message.session_id,
#                 # 其他可能需要从消息中提取的字段
#             )
            
#             # 调用流式生成响应
#             async for chunk in controller.generate_streaming_response(
#                 request=chat_request,
#                 db=db
#             ):
#                 # 发送流式块
#                 await websocket.send_text(json.dumps({
#                     "content": chunk,
#                     "type": "chunk",
#                     "session_id": message.session_id
#                 }))
                
#             # 发送结束信号
#             await websocket.send_text(json.dumps({
#                 "type": "end",
#                 "session_id": message.session_id
#             }))
                
#     except WebSocketDisconnect:
#         logger.info(f"WebSocket disconnected for participant {participant_id}")
#         await manager.handle_connection_error(participant_id)
#     except Exception as e:
#         logger.error(f"WebSocket error for participant {participant_id}: {str(e)}")
#         # 发送错误信息
#         try:
#             await websocket.send_text(json.dumps({
#                 "type": "error",
#                 "content": f"发生错误: {str(e)}",
#                 "session_id": message.session_id if 'message' in locals() else "unknown"
#             }))
#         except:
#             pass
#         finally:
#             await connection_manager.handle_connection_error(participant_id)
# from typing import Dict, Optional
# from fastapi import WebSocket
# from datetime import datetime
# import logging
# import asyncio
# from asyncio import Task
# import json

# logger = logging.getLogger(__name__)

# class ConnectionManager:
#     """
#     WebSocket连接管理器
#     负责管理所有活跃的WebSocket连接，支持连接的添加、删除和广播消息
#     """
    
#     def __init__(self):
#         # 存储所有活跃的连接，格式为 {user_id: WebSocket}
#         self.active_connections: Dict[str, WebSocket] = {}
#         # 存储连接的最后活跃时间，用于连接状态监控
#         self.last_activity: Dict[str, datetime] = {}
#         # 心跳检测间隔（秒）
#         self.heartbeat_interval: int = 30
#         # 心跳响应超时时间（秒）
#         self.heartbeat_timeout: int = 5
#         # 存储心跳检测任务
#         self.heartbeat_tasks: Dict[str, Task] = {}
#         # 重连配置
#         self.max_reconnect_attempts: int = 3  # 最大重连尝试次数
#         self.reconnect_delay: int = 5  # 重连等待时间（秒）
#         self.reconnection_callbacks: Dict[str, callable] = {}  # 存储重连回调函数

#     async def connect(self, websocket: WebSocket, user_id: str):
#         """
#         建立新的WebSocket连接
        
#         Args:
#             websocket (WebSocket): WebSocket连接实例
#             user_id (str): 用户ID
#         """
#         await websocket.accept()
#         self.active_connections[user_id] = websocket
#         self.last_activity[user_id] = datetime.now()
#         # 启动心跳检测任务
#         self.heartbeat_tasks[user_id] = asyncio.create_task(self._heartbeat_check(user_id))
#         logger.info(f"User {user_id} connected. Total active connections: {len(self.active_connections)}")

#     def disconnect(self, user_id: str):
#         """
#         断开指定用户的WebSocket连接
        
#         Args:
#             user_id (str): 用户ID
#         """
#         if user_id in self.active_connections:
#             # 取消心跳检测任务
#             if user_id in self.heartbeat_tasks:
#                 self.heartbeat_tasks[user_id].cancel()
#                 del self.heartbeat_tasks[user_id]
            
#             del self.active_connections[user_id]
#             del self.last_activity[user_id]
#             logger.info(f"User {user_id} disconnected. Total active connections: {len(self.active_connections)}")

#     def get_connection(self, user_id: str) -> Optional[WebSocket]:
#         """
#         获取指定用户的WebSocket连接
        
#         Args:
#             user_id (str): 用户ID
            
#         Returns:
#             Optional[WebSocket]: 返回WebSocket连接实例，如果不存在则返回None
#         """
#         return self.active_connections.get(user_id)

#     async def send_message(self, message: dict, user_id: str):
#         """
#         向指定用户发送消息
        
#         Args:
#             message (dict): 要发送的消息内容
#             user_id (str): 目标用户ID
#         """
#         if websocket := self.get_connection(user_id):
#             try:
#                 await websocket.send_json(message)
#                 self.last_activity[user_id] = datetime.now()
#                 logger.debug(f"Message sent to user {user_id}")
#             except Exception as e:
#                 logger.error(f"Error sending message to user {user_id}: {str(e)}")
#                 await self.handle_connection_error(user_id)

#     async def broadcast(self, message: dict, exclude: Optional[str] = None):
#         """
#         广播消息给所有连接的用户
        
#         Args:
#             message (dict): 要广播的消息内容
#             exclude (Optional[str]): 要排除的用户ID
#         """
#         disconnected_users = []
#         for user_id, websocket in self.active_connections.items():
#             if user_id != exclude:
#                 try:
#                     await websocket.send_json(message)
#                     self.last_activity[user_id] = datetime.now()
#                 except Exception as e:
#                     logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
#                     disconnected_users.append(user_id)

#         # 清理断开的连接
#         for user_id in disconnected_users:
#             self.disconnect(user_id)

#     def register_reconnect_callback(self, user_id: str, callback: callable):
#         """
#         注册重连回调函数
        
#         Args:
#             user_id (str): 用户ID
#             callback (callable): 异步回调函数，用于重新建立连接
#         """
#         self.reconnection_callbacks[user_id] = callback

#     async def handle_connection_error(self, user_id: str):
#         """
#         处理连接错误，尝试重连
        
#         Args:
#             user_id (str): 发生错误的用户ID
#         """
#         logger.info(f"Handling connection error for user {user_id}")
        
#         # 如果存在重连回调函数，尝试重连
#         if user_id in self.reconnection_callbacks:
#             reconnect_callback = self.reconnection_callbacks[user_id]
            
#             for attempt in range(self.max_reconnect_attempts):
#                 try:
#                     logger.info(f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts} for user {user_id}")
                    
#                     # 先断开现有连接
#                     self.disconnect(user_id)
                    
#                     # 等待一段时间后尝试重连
#                     await asyncio.sleep(self.reconnect_delay)
                    
#                     # 调用重连回调函数
#                     new_websocket = await reconnect_callback()
#                     if new_websocket:
#                         # 重新建立连接
#                         await self.connect(new_websocket, user_id)
#                         logger.info(f"Successfully reconnected user {user_id}")
#                         return
                    
#                 except Exception as e:
#                     logger.error(f"Reconnection attempt {attempt + 1} failed for user {user_id}: {str(e)}")
#                     continue
                
#             logger.error(f"All reconnection attempts failed for user {user_id}")
        
#         # 如果没有重连回调或重连失败，则断开连接
#         self.disconnect(user_id)

#     def is_connected(self, user_id: str) -> bool:
#         """
#         检查用户是否处于连接状态
        
#         Args:
#             user_id (str): 用户ID
            
#         Returns:
#             bool: 如果用户已连接则返回True，否则返回False
#         """
#         return user_id in self.active_connections

#     def get_connection_status(self, user_id: str) -> dict:
#         """
#         获取指定用户的连接状态信息
        
#         Args:
#             user_id (str): 用户ID
            
#         Returns:
#             dict: 包含连接状态信息的字典
#         """
#         if user_id in self.active_connections:
#             return {
#                 "connected": True,
#                 "last_activity": self.last_activity[user_id].isoformat(),
#                 "connection_duration": (datetime.now() - self.last_activity[user_id]).total_seconds()
#             }
#         return {
#             "connected": False,
#             "last_activity": None,
#             "connection_duration": 0
#         }

#     async def _heartbeat_check(self, user_id: str):
#         """
#         心跳检测机制
#         定期发送心跳消息并检查连接状态
        
#         Args:
#             user_id (str): 用户ID
#         """
#         while True:
#             try:
#                 websocket = self.get_connection(user_id)
#                 if not websocket:
#                     break

#                 # 发送心跳消息
#                 heartbeat_message = {
#                     "type": "heartbeat",
#                     "timestamp": datetime.now().isoformat()
#                 }
                
#                 try:
#                     await websocket.send_json(heartbeat_message)
#                     # 等待客户端响应，添加超时控制
#                     try:
#                         response = await asyncio.wait_for(
#                             websocket.receive_json(),
#                             timeout=self.heartbeat_timeout
#                         )
                        
#                         if response.get("type") == "heartbeat_response":
#                             self.last_activity[user_id] = datetime.now()
#                             logger.debug(f"Heartbeat successful for user {user_id}")
#                         else:
#                             logger.warning(f"Invalid heartbeat response from user {user_id}")
#                             await self.handle_connection_error(user_id)
#                             break
#                     except asyncio.TimeoutError:
#                         logger.warning(f"Heartbeat timeout for user {user_id}")
#                         await self.handle_connection_error(user_id)
#                         break
                        
#                 except Exception as e:
#                     logger.error(f"Heartbeat failed for user {user_id}: {str(e)}")
#                     await self.handle_connection_error(user_id)
#                     break

#                 # 等待下一次心跳检测
#                 await asyncio.sleep(self.heartbeat_interval)
                
#             except asyncio.CancelledError:
#                 logger.info(f"Heartbeat check cancelled for user {user_id}")
#                 break
#             except Exception as e:
#                 logger.error(f"Error in heartbeat check for user {user_id}: {str(e)}")
#                 await asyncio.sleep(self.heartbeat_interval)

# # 创建全局连接管理器实例
# manager = ConnectionManager()

# app/services/chat_handler.py
from fastapi import WebSocket
from app.services.llm_gateway import llm_gateway
from app.schemas.chat import SocketRequest, SocketResponse

async def handle_ai_message(request: SocketRequest, websocket: WebSocket):
    """处理 AI 消息，流式返回"""
    # 发送开始信号
    await websocket.send_text(SocketResponse(type="stream_start", sender="AI").json())

    # 调用 LLM 服务
    async for chunk in llm_gateway.get_stream_completion(
        system_prompt="You are a helpful AI programming tutor.",
        messages=[{"role": "user", "content": request.message}]
    ):
        await websocket.send_text(
            SocketResponse(type="stream", sender="AI", message=chunk).json()
        )

    # 发送结束信号
    await websocket.send_text(SocketResponse(type="stream_end", sender="AI").json())

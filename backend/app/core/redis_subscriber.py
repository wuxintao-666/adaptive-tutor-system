# ws_pubsub.py
import asyncio
import json
from app.config.dependency_injection import get_aioredis
from app.core.websocket_manager import ws_manager

async def redis_subscriber():
    redis = get_aioredis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("ws:user:*")
    async for message in pubsub.listen():
        if message["type"] == "pmessage":
            channel = message["channel"].decode()  # ws:user:{participant_id}
            raw_data = message["message"].decode()
            try:
                payload = json.loads(raw_data)
            except Exception:
                continue
            participant_id = channel.split(":")[-1]
            #await ws_manager.send_to_user(participant_id, raw_data)
            asyncio.create_task(ws_manager.send_to_user(participant_id, raw_data))

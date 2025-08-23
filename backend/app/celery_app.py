from celery import Celery
from app.core.config import settings
import os

# 创建 Celery 应用实例
celery_app = Celery(
    "async_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

# Celery 配置
celery_app.conf.update(
    # 任务序列化格式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 时区设置
    timezone="Asia/Shanghai",
    enable_utc=True,
)
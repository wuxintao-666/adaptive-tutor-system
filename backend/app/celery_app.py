from celery import Celery, signals
from app.core.config import settings
from app.config.dependency_injection import create_dynamic_controller, get_redis_client, get_user_state_service as create_user_state_service
import os

# 创建 Celery 应用实例
celery_app = Celery(
    "adaptive_tutor_system",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

# 全局变量，用于在单个 Worker 进程中存储依赖实例
_dynamic_controller_instance = None
_user_state_service_instance = None

@signals.worker_process_init.connect
def init_worker_process(sender=None, **kwargs):
    """
    在 Worker 进程启动时，根据其监听的队列有条件地初始化依赖。
    """
    global _dynamic_controller_instance, _user_state_service_instance
    
    # 1. 初始化所有 Worker 都需要的轻量级服务
    if _user_state_service_instance is None:
        print(f"Initializing UserStateService for Worker (PID: {os.getpid()})...")
        redis_client = get_redis_client()
        _user_state_service_instance = create_user_state_service(redis_client=redis_client)
        print("UserStateService initialized.")

    # 2. 获取 Worker 实例正在监听的队列名称集合
    queues = {q.name for q in sender.options.get('queues', [])}
    
    # 3. 只有当 Worker 明确服务于 'chat_queue' 时，才初始化重量级依赖
    if 'chat_queue' in queues:
        if _dynamic_controller_instance is None:
            print(f"Initializing DynamicController for Chat Worker (PID: {os.getpid()})...")
            # UserStateService 已经初始化，直接从 DynamicController 中使用
            # 注意：create_dynamic_controller 内部会创建自己的 UserStateService 实例
            redis_client = get_redis_client()
            _dynamic_controller_instance = create_dynamic_controller(redis_client=redis_client)
            print("DynamicController initialized.")
    else:
        print(f"Worker (PID: {os.getpid()}) is not serving 'chat_queue'. Skipping DynamicController initialization.")

def get_dynamic_controller():
    """
    在 Celery 任务中获取 DynamicController 实例。
    
    重要: 此函数只应在路由到 'chat_queue' 的任务中调用。
    """
    global _dynamic_controller_instance
    if _dynamic_controller_instance is None:
        raise RuntimeError(
            "DynamicController not initialized. This function should only be called "
            "from tasks routed to the 'chat_queue'."
        )
    return _dynamic_controller_instance

def get_user_state_service():
    """
    在 Celery 任务中获取 UserStateService 实例。
    """
    global _user_state_service_instance
    if _user_state_service_instance is None:
        raise RuntimeError("UserStateService not initialized.")
    return _user_state_service_instance

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
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
import asyncio
from contextlib import asynccontextmanager
from app.api.endpoints.ws_chat1 import manager, ws_router

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """FastAPI生命周期管理函数，替代弃用的on_event方法"""
#     # 启动时执行的代码
#     asyncio.create_task(manager.check_heartbeats())
#     yield
#     # 关闭时执行的代码（如果需要的话）

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
    #,lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=settings.BACKEND_PORT,
        reload=True
    )
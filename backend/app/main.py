# backend/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.endpoints.config import router as config_router
from app.api.endpoints.learning_data import router as learning_data_router

app = FastAPI(
    title='配置分发服务',
    version='1.0.0'
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 允许的前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 添加静态文件服务
data_dir = Path(__file__).parent / "data"
frontend_dir = Path(__file__).parent.parent.parent / "frontend"

app.mount("/backend/app/data", StaticFiles(directory=str(data_dir)), name="data")
app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")

app.include_router(config_router)
app.include_router(learning_data_router)

if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host='0.0.0.0',
        port=8000,
        reload=True
    )
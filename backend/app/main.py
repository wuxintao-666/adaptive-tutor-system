# backend/main.py
import uvicorn
from fastapi import FastAPI
from app.api.endpoints.config import router as config_router

app = FastAPI(
    title='配置分发服务',
    version='1.0.0'
)
app.include_router(config_router)

if __name__ == '__main__':
    uvicorn.run(
        'backend.main:app',
        host='0.0.0.0',
        port=app.dependency_overrides.get('BACKEND_PORT', 8000),
        reload=True
    )
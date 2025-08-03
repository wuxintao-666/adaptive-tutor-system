from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库引擎
# connect_args 是SQLite特有的，用于允许多线程访问
engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# 创建一个Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI 依赖项，用于在每个请求中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

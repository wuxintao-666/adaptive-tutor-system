#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有必要的数据库表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from app.core.config import settings
from app.models.event import Base as EventBase
from app.models.user_progress import Base as ProgressBase
from app.models.bkt import Base as BktBase

def init_database():
    """初始化数据库"""
    print("🗄️  初始化数据库...")
    
    # 创建数据库引擎
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    try:
        # 创建所有表
        print("📋 创建事件日志表...")
        EventBase.metadata.create_all(bind=engine)
        
        print("📋 创建用户进度表...")
        ProgressBase.metadata.create_all(bind=engine)
        
        print("📋 创建BKT模型表...")
        BktBase.metadata.create_all(bind=engine)
        
        print("✅ 数据库初始化完成!")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"📊 已创建的表: {tables}")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    init_database() 
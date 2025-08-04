# backend/app/api/endpoints/learning_data.py
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session

# 使用前缀统一版本管理,可修改
router = APIRouter(prefix='/api/v1')

# 配置日志
logger = logging.getLogger(__name__)

# 定义路径
CATALOG_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_graph.json"
ELEMENTS_DIR = Path(__file__).parent.parent.parent / "data" / "elements"
ELEMENTS_DIR.mkdir(exist_ok=True)


# ==================== 文档模块功能 ====================

@router.get("/users/{user_id}/allowed-tags")
async def get_allowed_tags(user_id: str) -> Dict[str, Any]:
    """获取用户允许学习的标签列表"""
    try:
        # 这里可以根据用户ID从数据库获取允许的标签
        # 目前返回默认的HTML标签列表
        allowed_tags = [
            'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'a', 'img', 'table', 'tr', 'td', 'th', 'ul', 'ol', 'li',
            'form', 'input', 'button', 'textarea', 'select', 'option',
            'section', 'article', 'header', 'footer', 'nav', 'aside',
            'main', 'figure', 'figcaption', 'blockquote', 'cite',
            'code', 'pre', 'em', 'strong', 'mark', 'small', 'sub', 'sup'
        ]
        
        return {
            "status": "success",
            "user_id": user_id,
            "allowed_tags": allowed_tags
        }
    except Exception as e:
        logger.error(f"获取允许标签失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取允许标签失败: {str(e)}")

@router.get("/docs/catalog")
async def get_docs_catalog() -> Dict[str, Any]:
    """返回知识点目录和内容"""
    try:
        if not CATALOG_PATH.exists():
            raise HTTPException(status_code=404, detail="知识点目录文件不存在")
            
        with open(CATALOG_PATH, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        return {
            "module": "docs_module",
            "status": "active",
            "data": {
                "catalog": catalog
            }
        }
    except Exception as e:
        logger.error(f"加载知识点目录失败: {e}")
        raise HTTPException(status_code=500, detail=f"加载知识点目录失败: {str(e)}")

@router.post("/docs/record-time")
async def record_learning_time(request: Request) -> Dict[str, Any]:
    """记录学习时间"""
    try:
        data = await request.json()
        action = data.get("action")
        if action == "record_time":
            base_time = int(data.get("base_time", 0))
            advanced_time = int(data.get("advanced_time", 0))
            
            from app.core.models import UserTime
            from app.core.config import SessionLocal
            
            db = SessionLocal()
            try:
                user_time = db.query(UserTime).first()
                if user_time:
                    user_time.base_time += base_time
                    user_time.advanced_time += advanced_time
                else:
                    user_time = UserTime(base_time=base_time, advanced_time=advanced_time)
                    db.add(user_time)
                db.commit()
                return {"status": "success", "message": "记录成功"}
            except Exception as e:
                return {"status": "error", "message": f"数据库写入失败: {str(e)}"}
            finally:
                db.close()
        
        raise HTTPException(status_code=400, detail="无效的action参数")
    except Exception as e:
        logger.error(f"记录学习时间失败: {e}")
        raise HTTPException(status_code=500, detail=f"记录学习时间失败: {str(e)}")

@router.post("/docs/tag-content")
async def get_tag_content(request: Request) -> Dict[str, Any]:
    """获取标签内容"""
    try:
        data = await request.json()
        tag_name = data.get("tag_name")
        if not tag_name:
            raise HTTPException(status_code=400, detail="缺少 tag_name")
        
        from app.core.models import Tag
        from app.core.config import SessionLocal
        
        db = SessionLocal()
        try:
            tag_data = {}
            for level in ['basic', 'intermediate', 'advanced', 'expert']:
                tag = db.query(Tag).filter_by(tag_name=tag_name, level=level).first()
                if tag:
                    tag_data[level] = tag.description
            if not tag_data:
                return {"status": "error", "message": f"未找到标签 {tag_name} 的内容"}
            return {
                "module": "docs_module",
                "status": "success",
                "data": {
                    "tag_name": tag_name,
                    "contents": tag_data
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"后端异常: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"获取标签内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取标签内容失败: {str(e)}")

# ==================== 元素选择器模块功能 ====================

@router.get("/elements")
async def get_all_elements() -> Dict[str, Any]:
    """获取所有已保存的元素信息"""
    try:
        elements = []
        for filename in os.listdir(ELEMENTS_DIR):
            if filename.endswith('.json'):
                with open(ELEMENTS_DIR / filename, 'r', encoding='utf-8') as f:
                    element_data = json.load(f)
                    element_id = filename.replace('.json', '')
                    elements.append({
                        "id": element_id,
                        **element_data
                    })
        return {
            "module": "element_selector",
            "status": "success",
            "data": elements
        }
    except Exception as e:
        logger.error(f"获取元素信息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取元素信息失败: {str(e)}")

@router.post("/elements")
async def save_element(request: Request) -> Dict[str, Any]:
    """接收并保存前端传来的元素信息"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        element_tag = data.get("element_tag")
        
        from app.core.knowledge_map import knowledge_map
        from app.core.models import UserKnowledge
        from app.core.config import SessionLocal
        
        if user_id and element_tag:
            db: Session = SessionLocal()
            try:
                learned = db.query(UserKnowledge).filter_by(user_id=user_id).all()
                allowed_tags = set()
                for rec in learned:
                    allowed_tags.update(knowledge_map.get(rec.knowledge_id, []))
                if element_tag not in allowed_tags:
                    return {
                        "module": "element_selector",
                        "status": "forbidden",
                        "message": f"你还未学过该标签: {element_tag}"
                    }
            finally:
                db.close()
        
        # 生成唯一ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        element_id = f"element_{timestamp}"
        
        # 保存到JSON文件
        filename = ELEMENTS_DIR / f"{element_id}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存元素信息: {element_id}")
        
        return {
            "module": "element_selector",
            "status": "success",
            "element_id": element_id,
            "element": {
                "id": element_id,
                **data
            },
            "message": "元素信息已成功接收"
        }
    except Exception as e:
        logger.error(f"处理元素信息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理元素信息失败: {str(e)}")

 
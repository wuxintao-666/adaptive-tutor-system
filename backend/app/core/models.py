# backend/app/core/models.py
from sqlalchemy import Column, Integer, String, Enum, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserKnowledge(Base):
    """用户知识掌握情况模型
    
    记录用户与知识点的关联关系，用于跟踪用户的学习进度和知识掌握状态。
    
    Attributes:
        id: 主键，自增整数
        user_id: 用户ID，用于标识特定用户
        knowledge_id: 知识点ID，用于标识特定的知识点
    """
    __tablename__ = "user_knowledge"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), index=True)
    knowledge_id = Column(String(64), index=True)
    __table_args__ = (UniqueConstraint('user_id', 'knowledge_id', name='_user_knowledge_uc'),)

class Tag(Base):
    """技能标签模型
    
    用于对知识点和技能进行分类和分级管理，支持不同难度级别的标签体系。
    
    Attributes:
        id: 主键，自增整数
        tag_name: 标签名称，如 "HTML", "CSS", "JavaScript" 等
        level: 难度级别，可选值: 'basic', 'intermediate', 'advanced', 'expert'
        description: 标签描述，详细说明该标签代表的技能内容
    """
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(64), index=True, nullable=False)
    level = Column(Enum('basic', 'intermediate', 'advanced', 'expert'), nullable=False)
    description = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('tag_name', 'level', name='_tag_level_uc'),)

class UserTime(Base):
    """用户学习时间统计模型
    
    记录用户在不同学习阶段花费的时间，用于分析学习进度和优化学习路径。
    
    Attributes:
        id: 主键，自增整数
        base_time: 基础学习时间（秒），记录用户在基础概念学习上花费的时间
        advanced_time: 进阶学习时间（秒），记录用户在高级应用和项目实践中花费的时间
    """
    __tablename__ = "user_time"
    id = Column(Integer, primary_key=True, autoincrement=True)
    base_time = Column(Integer, default=0)
    advanced_time = Column(Integer, default=0) 
# backend/app/schemas/content.py
from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Union


class CodeContent(BaseModel):
    """代码内容模型"""
    html: str = ""
    css: str = ""
    js: str = ""


class LearningContent(BaseModel):
    """学习内容模型"""
    topic_id: str
    title: str
    code: CodeContent
    documentation_md: str


class CheckpointAssertion(BaseModel):
    """检查点断言模型"""
    type: str
    selector: str
    assertion_type: str
    value: str
    feedback: str


class CheckpointAssertionWrapper(BaseModel):
    """检查点断言包装器模型"""
    type: str
    selector: str
    assertion_type: str
    value: str
    feedback: str


class Checkpoint(BaseModel):
    """检查点模型"""
    name: str
    type: str
    selector: Optional[str] = None
    assertion_type: Optional[str] = None
    value: Optional[str] = None
    feedback: Optional[str] = None
    action_selector: Optional[str] = None
    action_type: Optional[str] = None
    assertion: Optional[Union[CheckpointAssertion, CheckpointAssertionWrapper]] = None
    css_property: Optional[str] = None


class TestTask(BaseModel):
    """测试任务模型"""
    topic_id: str
    description_md: str
    start_code: CodeContent
    checkpoints: List[Checkpoint]
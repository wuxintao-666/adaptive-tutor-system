from pydantic import BaseModel, Field
from typing import Dict, Any, List

class CodePayload(BaseModel):
    html: str = ""
    css: str = ""
    js: str = ""

class TestSubmissionRequest(BaseModel):
    participant_id: str = Field(..., description="参与者ID")
    topic_id: str = Field(..., description="知识点ID")
    code: CodePayload = Field(..., description="用户提交的代码")

class TestSubmissionResponse(BaseModel):
    passed: bool = Field(..., description="是否所有检查点都通过")
    message: str = Field(..., description="总体评测信息")
    details: List[str] = Field(..., description="详细的失败反馈列表")

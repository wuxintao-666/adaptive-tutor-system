# backend/app/schemas/content.py
from pydantic import BaseModel
from typing import Optional, Dict, List, Any, Union


class CodeContent(BaseModel):
    """代码内容模型
    
    用于承载完整的Web代码内容，包含HTML、CSS和JavaScript三个部分。
    
    Attributes:
        html: HTML代码内容，包含页面结构和内容
        css: CSS样式代码内容，用于页面美化
        js: JavaScript脚本代码内容，用于页面交互
    """
    html: str = ""
    css: str = ""
    js: str = ""


class LearningContent(BaseModel):
    """学习内容模型
    
    完整的学习内容结构，包含主题信息、代码示例和文档说明。
    
    Attributes:
        topic_id: 知识点ID，用于标识特定的学习主题
        title: 学习内容标题
        code: 代码示例内容，包含HTML、CSS、JS三部分
        documentation_md: 文档说明，Markdown格式的详细说明
    """
    topic_id: str
    title: str
    code: CodeContent
    documentation_md: str


class CheckpointAssertion(BaseModel):
    """检查点断言模型
    
    定义代码测试的检查点断言规则，用于验证用户代码的正确性。
    
    Attributes:
        type: 断言类型，如 'text', 'style', 'attribute' 等
        selector: 选择器，用于定位要检查的DOM元素
        assertion_type: 断言方式，如 'equals', 'contains', 'exists' 等
        value: 期望值，用于与实际值进行比较
        feedback: 反馈信息，当断言失败时显示给用户
    """
    type: str
    selector: str
    assertion_type: str
    value: str
    feedback: str


class CheckpointAssertionWrapper(BaseModel):
    """检查点断言包装器模型
    
    检查点断言的包装器，提供与CheckpointAssertion相同的字段但结构更灵活。
    
    Attributes:
        type: 断言类型，如 'text', 'style', 'attribute' 等
        selector: 选择器，用于定位要检查的DOM元素
        assertion_type: 断言方式，如 'equals', 'contains', 'exists' 等
        value: 期望值，用于与实际值进行比较
        feedback: 反馈信息，当断言失败时显示给用户
    """
    type: str
    selector: str
    assertion_type: str
    value: str
    feedback: str


class Checkpoint(BaseModel):
    """检查点模型
    
    代码测试的检查点定义，包含验证规则和执行动作。
    
    Attributes:
        name: 检查点名称，用于标识和描述检查点
        type: 检查点类型，如 'checkpoint', 'action' 等
        selector: 选择器，用于定位要检查的DOM元素
        assertion_type: 断言方式，如 'equals', 'contains', 'exists' 等
        value: 期望值，用于与实际值进行比较
        feedback: 反馈信息，当检查点失败时显示给用户
        action_selector: 动作选择器，用于定位要执行动作的元素
        action_type: 动作类型，如 'click', 'input' 等
        assertion: 断言对象，可以是CheckpointAssertion或CheckpointAssertionWrapper
        css_property: CSS属性，用于检查元素的样式属性
    """
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
    """测试任务模型
    
    完整的测试任务定义，包含任务描述、初始代码和检查点列表。
    
    Attributes:
        topic_id: 知识点ID，用于标识测试任务对应的知识点
        description_md: 任务描述，Markdown格式的详细说明
        start_code: 初始代码，用户开始测试时的基础代码
        checkpoints: 检查点列表，包含所有需要验证的检查点
    """
    topic_id: str
    description_md: str
    start_code: CodeContent
    checkpoints: List[Checkpoint]
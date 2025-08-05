# backend/app/services/prompt_generator.py
from typing import List, Dict, Any, Tuple
from ..schemas.chat import UserStateSummary, SentimentAnalysisResult
from ..schemas.content import CodeContent


class PromptGenerator:
    """提示词生成器"""
    
    def __init__(self):
        self.base_system_prompt = """You are 'Alex', a world-class AI programming tutor. Your goal is to help a student master a specific topic by providing personalized, empathetic, and insightful guidance. You must respond in Markdown format.

Key principles:
1. Be encouraging and supportive
2. Provide clear, step-by-step explanations
3. Use examples and analogies when helpful
4. Adapt your teaching style based on the student's emotional state
5. Focus on the current learning topic
6. Respond in a conversational, friendly tone"""
    
    def create_prompts(
        self,
        user_state: UserStateSummary,
        retrieved_context: List[str],
        conversation_history: List[Dict[str, str]],
        user_message: str,
        code_context: CodeContent = None,
        task_context: str = None,
        topic_id: str = None
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        创建完整的提示词和消息列表
        
        Args:
            user_state: 用户状态摘要
            retrieved_context: RAG检索的上下文
            conversation_history: 对话历史
            user_message: 用户当前消息
            code_context: 代码上下文
            task_context: 任务上下文
            topic_id: 主题ID
            
        Returns:
            Tuple[str, List[Dict[str, str]]]: (system_prompt, messages)
        """
        # 构建系统提示词
        system_prompt = self._build_system_prompt(
            user_state=user_state,
            retrieved_context=retrieved_context,
            task_context=task_context,
            topic_id=topic_id
        )
        
        # 构建消息列表
        messages = self._build_message_history(
            conversation_history=conversation_history,
            code_context=code_context,
            user_message=user_message
        )
        
        return system_prompt, messages
    
    def _build_system_prompt(
        self,
        user_state: UserStateSummary,
        retrieved_context: List[str],
        task_context: str = None,
        topic_id: str = None
    ) -> str:
        """构建系统提示词"""
        prompt_parts = [self.base_system_prompt]
        
        # 添加情感策略
        emotion = user_state.emotion_state.get('current_sentiment', 'NEUTRAL')
        emotion_strategy = self._get_emotion_strategy(emotion)
        prompt_parts.append(f"STRATEGY: {emotion_strategy}")
        
        # 添加用户状态信息
        if user_state.is_new_user:
            prompt_parts.append("STUDENT INFO: This is a new student. Start with basic concepts and be extra patient.")
        else:
            # 可以添加更多用户状态信息，如学习进度等
            prompt_parts.append("STUDENT INFO: This is an existing student. Build upon previous knowledge.")
        
        # 添加RAG上下文（暂时注释，等待RAG模块修复）
        # if retrieved_context:
        #     formatted_context = "\n\n---\n\n".join(retrieved_context)
        #     prompt_parts.append(f"REFERENCE KNOWLEDGE: Use the following information from the knowledge base to answer the user's question accurately.\n\n{formatted_context}")
        
        # 添加任务上下文
        if task_context:
            prompt_parts.append(f"TASK CONTEXT: The student is currently working on: '{task_context}'. Frame your explanations within this context.")
        
        # 添加主题信息
        if topic_id:
            prompt_parts.append(f"TOPIC: The current learning topic is '{topic_id}'. Focus your explanations on this specific topic.")
        
        return "\n\n".join(prompt_parts)
    
    def _get_emotion_strategy(self, emotion: str) -> str:
        """根据情感获取教学策略"""
        strategies = {
            'FRUSTRATED': "The student seems frustrated. Your top priority is to be encouraging and empathetic. Acknowledge the difficulty before offering help. Use phrases like 'Don't worry, this is a tricky part' or 'Let's try a different approach'.",
            'CONFUSED': "The student seems confused. Break down concepts into smaller, simpler steps. Use analogies. Provide the simplest possible examples. Avoid jargon.",
            'EXCITED': "The student seems excited and engaged. You can introduce more advanced concepts and challenge them with deeper explanations.",
            'NEUTRAL': "The student seems neutral. Provide clear, structured explanations and check for understanding."
        }
        
        return strategies.get(emotion.upper(), strategies['NEUTRAL'])
    
    def _build_message_history(
        self,
        conversation_history: List[Dict[str, str]],
        code_context: CodeContent = None,
        user_message: str = ""
    ) -> List[Dict[str, str]]:
        """构建消息历史"""
        messages = []
        
        # 添加历史对话
        for msg in conversation_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        # 构建当前用户消息
        current_user_content = user_message
        
        # 如果有代码上下文，添加到用户消息中
        if code_context:
            code_section = self._format_code_context(code_context)
            current_user_content = f"{code_section}\n\nMy question is: {user_message}"
        
        # 添加当前用户消息
        if current_user_content.strip():
            messages.append({
                "role": "user",
                "content": current_user_content
            })
        
        return messages
    
    def _format_code_context(self, code_context: CodeContent) -> str:
        """格式化代码上下文"""
        parts = []
        
        if code_context.html.strip():
            parts.append(f"HTML Code:\n```html\n{code_context.html}\n```")
        
        if code_context.css.strip():
            parts.append(f"CSS Code:\n```css\n{code_context.css}\n```")
        
        if code_context.js.strip():
            parts.append(f"JavaScript Code:\n```javascript\n{code_context.js}\n```")
        
        if parts:
            return "Here is my current code:\n\n" + "\n\n".join(parts)
        else:
            return ""


# 创建单例实例
prompt_generator = PromptGenerator()

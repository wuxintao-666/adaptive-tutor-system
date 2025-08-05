# backend/app/services/dynamic_controller.py
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..schemas.chat import ChatRequest, ChatResponse, UserStateSummary, SentimentAnalysisResult
from ..schemas.content import CodeContent
from .user_state_service import UserStateService
from .sentiment_analysis_service import sentiment_analysis_service
# from .rag_service import rag_service  # 暂时注释，等待RAG模块修复
from .prompt_generator import prompt_generator
from .llm_gateway import llm_gateway


class DynamicController:
    """动态控制器 - 编排各个服务的核心逻辑"""
    
    def __init__(self):
        self.user_state_service = UserStateService()
    
    async def generate_adaptive_response(
        self, 
        request: ChatRequest, 
        db: Session
    ) -> ChatResponse:
        """
        生成自适应AI回复的核心流程
        
        Args:
            request: 聊天请求
            db: 数据库会话
            
        Returns:
            ChatResponse: AI回复
        """
        try:
            # 步骤1: 获取或创建用户档案
            profile = self.user_state_service.get_or_create_profile(
                participant_id=request.participant_id,
                db=db
            )
            
            # 步骤2: 情感分析
            sentiment_result = sentiment_analysis_service.analyze_sentiment(
                request.user_message
            )
            
            # 步骤3: 更新用户状态（包含情感信息）
            self._update_user_state_with_sentiment(profile, sentiment_result)
            
            # 步骤4: 构建用户状态摘要
            user_state_summary = self._build_user_state_summary(profile, sentiment_result)
            
            # 步骤5: RAG检索（暂时注释，等待RAG模块修复）
            # retrieved_context = rag_service.retrieve(request.user_message)
            retrieved_context = []  # 暂时返回空列表
            
            # 步骤6: 生成提示词
            system_prompt, messages = prompt_generator.create_prompts(
                user_state=user_state_summary,
                retrieved_context=retrieved_context,
                conversation_history=request.conversation_history,
                user_message=request.user_message,
                code_context=request.code_context,
                task_context=request.task_context,
                topic_id=request.topic_id
            )
            
            # 步骤7: 调用LLM
            ai_response = await llm_gateway.get_completion(
                system_prompt=system_prompt,
                messages=messages
            )
            
            # 步骤8: 构建响应
            response = ChatResponse(
                ai_response=ai_response,
                user_state_summary=user_state_summary.dict(),
                retrieved_context=retrieved_context,
                system_prompt=system_prompt
            )
            
            # 步骤9: 异步记录交互日志（简化版本）
            self._log_interaction(request, response, db)
            
            return response
            
        except Exception as e:
            print(f"Error in generate_adaptive_response: {e}")
            # 返回错误响应
            return ChatResponse(
                ai_response=f"I apologize, but I encountered an error: {str(e)}",
                user_state_summary={},
                retrieved_context=[],
                system_prompt=""
            )
    
    def _update_user_state_with_sentiment(
        self, 
        profile: Any, 
        sentiment_result: SentimentAnalysisResult
    ):
        """更新用户状态中的情感信息"""
        if hasattr(profile, 'emotion_state'):
            profile.emotion_state['current_sentiment'] = sentiment_result.label
            profile.emotion_state['sentiment_confidence'] = sentiment_result.confidence
            profile.emotion_state['sentiment_details'] = sentiment_result.details
    
    def _build_user_state_summary(
        self, 
        profile: Any, 
        sentiment_result: SentimentAnalysisResult
    ) -> UserStateSummary:
        """构建用户状态摘要"""
        return UserStateSummary(
            participant_id=profile.participant_id,
            emotion_state=profile.emotion_state if hasattr(profile, 'emotion_state') else {},
            behavior_counters=profile.behavior_counters if hasattr(profile, 'behavior_counters') else {},
            bkt_models=profile.bkt_model if hasattr(profile, 'bkt_model') else {},
            is_new_user=profile.is_new_user if hasattr(profile, 'is_new_user') else True
        )
    
    def _log_interaction(
        self, 
        request: ChatRequest, 
        response: ChatResponse, 
        db: Session
    ):
        """记录交互日志"""
        try:
            # 这里可以添加详细的日志记录逻辑
            # 例如记录到数据库或日志文件
            print(f"Interaction logged: {request.participant_id} -> {len(response.ai_response)} chars")
        except Exception as e:
            print(f"Error logging interaction: {e}")
    
    def get_user_state(self, participant_id: str, db: Session) -> Dict[str, Any]:
        """获取用户状态"""
        try:
            profile = self.user_state_service.get_or_create_profile(
                participant_id=participant_id,
                db=db
            )
            return self._build_user_state_summary(
                profile, 
                SentimentAnalysisResult(label="NEUTRAL", confidence=1.0)
            ).dict()
        except Exception as e:
            print(f"Error getting user state: {e}")
            return {}
    
    def validate_services(self) -> Dict[str, bool]:
        """验证所有服务的状态"""
        return {
            'llm_gateway': llm_gateway.validate_connection(),
            'user_state_service': True,  # 本地服务，总是可用
            'sentiment_analysis_service': True,  # 本地服务，总是可用
            'rag_service': False,  # 暂时禁用
            'prompt_generator': True  # 本地服务，总是可用
        }


# 创建单例实例
dynamic_controller = DynamicController()

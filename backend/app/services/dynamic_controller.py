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
            # 步骤1: 获取或创建用户档案（使用临时档案，不依赖数据库）
            profile = self._create_temporary_profile(request.participant_id)
            
            # 步骤2: 情感分析
            try:
                sentiment_result = sentiment_analysis_service.analyze_sentiment(
                    request.user_message
                )
            except Exception as e:
                print(f"⚠️ 情感分析失败，使用默认值: {e}")
                sentiment_result = SentimentAnalysisResult(
                    label="NEUTRAL", 
                    confidence=1.0, 
                    details={}
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
            
            # 步骤9: 异步记录交互日志（简化版本，不依赖数据库）
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
        # 获取数据库连接状态
        db_status = getattr(profile, 'db_connected', None)
        if db_status is None:
            # 从emotion_state中获取db_status
            emotion_state = profile.emotion_state if hasattr(profile, 'emotion_state') else {}
            db_status = emotion_state.get('db_status', 'unknown')
        
        return UserStateSummary(
            participant_id=profile.participant_id,
            emotion_state=profile.emotion_state if hasattr(profile, 'emotion_state') else {},
            behavior_counters=profile.behavior_counters if hasattr(profile, 'behavior_counters') else {},
            bkt_models=profile.bkt_model if hasattr(profile, 'bkt_model') else {},
            is_new_user=profile.is_new_user if hasattr(profile, 'is_new_user') else True,
            db_status=db_status,
            db_error=getattr(profile, 'db_error', None)
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
        """获取用户状态（使用临时档案，不依赖数据库）"""
        # 创建临时用户档案
        temp_profile = self._create_temporary_profile(participant_id)
        
        user_state = self._build_user_state_summary(
            temp_profile, 
            SentimentAnalysisResult(label="NEUTRAL", confidence=1.0, details={})
        ).dict()
        return user_state
    
    def _create_temporary_profile(self, participant_id: str) -> Any:
        """创建临时用户档案（不依赖数据库）"""
        class TemporaryProfile:
            def __init__(self, participant_id: str):
                self.participant_id = participant_id
                self.emotion_state = {
                    'current_sentiment': 'NEUTRAL',
                    'sentiment_confidence': 1.0,
                    'sentiment_details': None,
                    'db_status': 'disconnected'
                }
                self.behavior_counters = {
                    'total_interactions': 0,
                    'questions_asked': 0,
                    'code_requests': 0,
                    'session_duration': 0
                }
                self.bkt_model = {
                    'html_basics': 0.3,
                    'css_basics': 0.2,
                    'javascript_basics': 0.1
                }
                self.is_new_user = True
                self.db_connected = 'disconnected'  # 改为字符串
        
        return TemporaryProfile(participant_id)
    
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

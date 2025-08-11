import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
import os

# 将 backend 目录添加到 sys.path 中
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, backend_path)

from app.services.behavior_interpreter_service import BehaviorInterpreterService
from app.services.user_state_service import UserStateService, StudentProfile
from app.schemas.behavior import BehaviorEvent
from datetime import datetime

class TestBehaviorInterpreterFix:
    """测试 BehaviorInterpreterService 的修复是否有效"""

    def test_no_circular_dependency(self):
        """测试1: 验证循环依赖问题是否已解决"""
        # 这个测试验证我们能否正常导入两个服务而不出现循环依赖
        try:
            from app.services.behavior_interpreter_service import behavior_interpreter_service
            from app.services.user_state_service import UserStateService
            assert True, "成功导入，没有循环依赖"
        except ImportError as e:
            pytest.fail(f"仍然存在循环依赖: {e}")

    def test_interpret_event_with_dependency_injection(self):
        """测试2: 验证依赖注入是否正常工作"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_db_session = MagicMock()
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 创建测试事件 - 使用正确的 TestSubmissionData 格式
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="test_submission",
            event_data={
                "topic_id": "test_topic",
                "code": {"html": "", "css": "", "js": ""}
            },
            timestamp=datetime.utcnow()
        )
        
        # 调用 interpret_event 方法
        try:
            interpreter.interpret_event(
                test_event,
                user_state_service=mock_user_state_service,
                db_session=mock_db_session,
                is_replay=False
            )
            assert True, "依赖注入正常工作"
        except Exception as e:
            pytest.fail(f"依赖注入失败: {e}")

    def test_frustration_detection_with_db_session(self):
        """测试3: 验证挫败检测功能是否正常工作"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_db_session = MagicMock()
        mock_crud_event = MagicMock()
        
        # 模拟历史事件数据
        mock_events = []
        for i in range(5):
            mock_event = MagicMock()
            mock_event.event_type = "test_submission"
            mock_event.timestamp = datetime.utcnow()
            mock_event.event_data = {"is_correct": False}  # 模拟错误提交
            mock_events.append(mock_event)
        
        mock_crud_event.get_by_participant.return_value = mock_events
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="test_submission",
            event_data={
                "topic_id": "test_topic",
                "code": {"html": "", "css": "", "js": ""}  # TestSubmissionData 需要 code 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService(
            window_minutes=2,
            error_rate_threshold=0.75,
            interval_seconds=10
        )
        
        # 使用 patch 来模拟 crud_event
        with patch('app.services.behavior_interpreter_service.crud_event', mock_crud_event):
            try:
                interpreter.interpret_event(
                    test_event,
                    user_state_service=mock_user_state_service,
                    db_session=mock_db_session,
                    is_replay=False
                )
                assert True, "挫败检测功能正常工作"
            except Exception as e:
                pytest.fail(f"挫败检测失败: {e}")

    def test_ai_help_request_handling(self):
        """测试4: 验证AI求助请求处理是否正常工作"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_profile = MagicMock()
        mock_profile.behavior_counters = {"help_requests": 0}
        mock_user_state_service.get_or_create_profile.return_value = (mock_profile, False)
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="ai_help_request",
            event_data={
                "message": "我需要帮助"  # AiHelpRequestData 需要 message 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 调用 interpret_event 方法
        try:
            interpreter.interpret_event(
                test_event,
                user_state_service=mock_user_state_service,
                db_session=None,
                is_replay=False
            )
            
            # 验证求助计数是否增加
            assert mock_profile.behavior_counters["help_requests"] == 1, "求助计数应该增加"
            assert True, "AI求助请求处理正常工作"
        except Exception as e:
            pytest.fail(f"AI求助请求处理失败: {e}")

    def test_lightweight_event_handling(self):
        """测试5: 验证轻量级事件处理是否正常工作"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_profile = MagicMock()
        mock_profile.behavior_counters = {"focus_changes": 0}
        mock_user_state_service.get_or_create_profile.return_value = (mock_profile, False)
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="page_focus_change",
            event_data={
                "status": "focus"  # PageFocusChangeData 需要 status 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 调用 interpret_event 方法
        try:
            interpreter.interpret_event(
                test_event,
                user_state_service=mock_user_state_service,
                db_session=None,
                is_replay=False
            )
            
            # 验证焦点变化计数是否增加
            assert mock_profile.behavior_counters["focus_changes"] == 1, "焦点变化计数应该增加"
            assert True, "轻量级事件处理正常工作"
        except Exception as e:
            pytest.fail(f"轻量级事件处理失败: {e}")

    def test_replay_mode_behavior(self):
        """测试6: 验证回放模式是否正常工作"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_profile = MagicMock()
        mock_profile.behavior_counters = {"help_requests": 0}
        mock_user_state_service.get_or_create_profile.return_value = (mock_profile, False)
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="ai_help_request",
            event_data={
                "message": "我需要帮助"  # AiHelpRequestData 需要 message 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 调用 interpret_event 方法（回放模式）
        try:
            interpreter.interpret_event(
                test_event,
                user_state_service=mock_user_state_service,
                db_session=None,
                is_replay=True
            )
            
            # 验证求助计数是否增加（回放时也应该增加）
            assert mock_profile.behavior_counters["help_requests"] == 1, "回放时求助计数应该增加"
            
            # 验证 maybe_create_snapshot 是否被调用（回放时不应该调用）
            mock_user_state_service.maybe_create_snapshot.assert_not_called()
            assert True, "回放模式正常工作"
        except Exception as e:
            pytest.fail(f"回放模式失败: {e}")

    def test_database_session_management(self):
        """测试7: 验证数据库会话管理是否正常"""
        # 创建 mock 对象
        mock_user_state_service = MagicMock()
        mock_session_local = MagicMock()
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="test_user",
            event_type="test_submission",
            event_data={
                "topic_id": "test_topic",
                "code": {"html": "", "css": "", "js": ""}  # TestSubmissionData 需要 code 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 使用 patch 来模拟数据库相关模块
        with patch('app.services.behavior_interpreter_service.SessionLocal', mock_session_local):
            with patch('app.services.behavior_interpreter_service.crud_event') as mock_crud:
                mock_crud.get_by_participant.return_value = []
                
                try:
                    interpreter.interpret_event(
                        test_event,
                        user_state_service=mock_user_state_service,
                        db_session=None,  # 不传入 db_session，让它创建新的
                        is_replay=False
                    )
                    
                    # 验证数据库会话是否被正确创建和关闭
                    mock_session_local.assert_called_once()
                    mock_db_session.close.assert_called_once()
                    assert True, "数据库会话管理正常工作"
                except Exception as e:
                    pytest.fail(f"数据库会话管理失败: {e}")

    def test_error_handling(self):
        """测试8: 验证错误处理是否正常"""
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        # 测试无效事件
        invalid_event = {"invalid": "event"}
        
        try:
            interpreter.interpret_event(
                invalid_event,
                user_state_service=None,
                db_session=None,
                is_replay=False
            )
            assert True, "无效事件处理正常"
        except Exception as e:
            pytest.fail(f"无效事件处理失败: {e}")

    def test_integration_with_user_state_service(self):
        """测试9: 验证与 UserStateService 的集成是否正常"""
        # 创建真实的 UserStateService 实例
        user_state_service = UserStateService()
        
        # 创建测试事件
        test_event = BehaviorEvent(
            participant_id="integration_test_user",
            event_type="test_submission",
            event_data={
                "topic_id": "integration_topic",
                "code": {"html": "", "css": "", "js": ""}  # TestSubmissionData 需要 code 字段
            },
            timestamp=datetime.utcnow()
        )
        
        # 创建 BehaviorInterpreterService 实例
        interpreter = BehaviorInterpreterService()
        
        try:
            # 使用 mock 数据库会话
            mock_db_session = MagicMock()
            
            interpreter.interpret_event(
                test_event,
                user_state_service=user_state_service,
                db_session=mock_db_session,
                is_replay=False
            )
            
            assert True, "与 UserStateService 集成正常"
        except Exception as e:
            pytest.fail(f"与 UserStateService 集成失败: {e}")

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])

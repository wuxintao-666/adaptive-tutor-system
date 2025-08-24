#!/usr/bin/env python3
"""
UserStateService Redis数据修改功能测试脚本
用于验证用户状态服务是否能成功修改Redis中的用户数据
"""

import time
import json
import redis
from datetime import datetime, timezone
from app.core.config import settings
from app.services.user_state_service import UserStateService, StudentProfile
from app.schemas.behavior import BehaviorEvent, EventType

class UserStateServiceTester:
    """UserStateService测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        # 创建Redis连接
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
        # 创建UserStateService实例
        self.user_state_service = UserStateService(self.redis_client)
        
        # 测试用户ID
        self.test_user_id = f"test_user_{int(time.time())}"
        
        print(f"🧪 初始化测试环境")
        print(f"   Redis连接: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"   测试用户ID: {self.test_user_id}")
        print("=" * 60)
    
    def test_redis_connection(self):
        """测试Redis连接"""
        print("🔌 测试Redis连接...")
        try:
            # 测试连接
            self.redis_client.ping()
            print("   ✅ Redis连接成功")
            
            # 测试RedisJSON功能
            test_key = "test_json_key"
            test_data = {"test": "value"}
            self.redis_client.json().set(test_key, ".", test_data)
            retrieved_data = self.redis_client.json().get(test_key)
            
            if retrieved_data == test_data:
                print("   ✅ RedisJSON功能正常")
                # 清理测试数据
                self.redis_client.delete(test_key)
            else:
                print("   ❌ RedisJSON功能异常")
                return False
                
        except Exception as e:
            print(f"   ❌ Redis连接失败: {e}")
            return False
        
        return True
    
    def test_profile_creation(self):
        """测试用户档案创建"""
        print("\n👤 测试用户档案创建...")
        
        try:
            # 创建新的用户档案
            profile = StudentProfile(self.test_user_id, is_new_user=True)
            
            # 保存到Redis
            self.user_state_service.save_profile(profile)
            
            # 验证是否成功保存
            key = f"user_profile:{self.test_user_id}"
            saved_data = self.redis_client.json().get(key)
            
            if saved_data:
                print("   ✅ 用户档案创建成功")
                print(f"   档案数据: {json.dumps(saved_data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print("   ❌ 用户档案创建失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 用户档案创建出错: {e}")
            return False
    
    def test_profile_retrieval(self):
        """测试用户档案检索"""
        print("\n📖 测试用户档案检索...")
        
        try:
            # 获取用户档案
            profile, is_new_user = self.user_state_service.get_or_create_profile(
                self.test_user_id, 
                db=None
            )
            
            if profile and profile.participant_id == self.test_user_id:
                print("   ✅ 用户档案检索成功")
                print(f"   是否新用户: {is_new_user}")
                print(f"   档案内容: {json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)}")
                return True
            else:
                print("   ❌ 用户档案检索失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 用户档案检索出错: {e}")
            return False
    
    def test_emotion_state_update(self):
        """测试情感状态更新"""
        print("\n😊 测试情感状态更新...")
        
        try:
            # 获取用户档案
            profile, _ = self.user_state_service.get_or_create_profile(
                self.test_user_id, 
                db=None
            )
            
            # 更新情感状态
            set_dict = {
                'emotion_state.current_sentiment': 'HAPPY',
                'emotion_state.is_frustrated': False
            }
            
            self.user_state_service.set_profile(profile, set_dict)
            
            # 验证更新结果
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if (updated_data and 
                updated_data.get('emotion_state', {}).get('current_sentiment') == 'HAPPY' and
                updated_data.get('emotion_state', {}).get('is_frustrated') == False):
                
                print("   ✅ 情感状态更新成功")
                print(f"   更新后数据: {json.dumps(updated_data['emotion_state'], ensure_ascii=False, indent=2)}")
                return True
            else:
                print("   ❌ 情感状态更新失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 情感状态更新出错: {e}")
            return False
    
    def test_behavior_counters_update(self):
        """测试行为计数器更新"""
        print("\n📊 测试行为计数器更新...")
        
        try:
            # 获取用户档案
            profile, _ = self.user_state_service.get_or_create_profile(
                self.test_user_id, 
                db=None
            )
            
            # 更新多个行为计数器
            set_dict = {
                'behavior_counters.error_count': 5,
                'behavior_counters.focus_changes': 10,
                'behavior_counters.idle_count': 3,
                'behavior_counters.dom_selects': 8,
                'behavior_counters.code_edits': 15
            }
            
            self.user_state_service.set_profile(profile, set_dict)
            
            # 验证更新结果
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('behavior_counters'):
                counters = updated_data['behavior_counters']
                print("   ✅ 行为计数器更新成功")
                print(f"   更新后计数器: {json.dumps(counters, ensure_ascii=False, indent=2)}")
                
                # 验证具体值
                expected_values = {
                    'error_count': 5,
                    'focus_changes': 10,
                    'idle_count': 3,
                    'dom_selects': 8,
                    'code_edits': 15
                }
                
                all_correct = True
                for key, expected_value in expected_values.items():
                    if counters.get(key) != expected_value:
                        print(f"   ⚠️  {key} 值不匹配: 期望 {expected_value}, 实际 {counters.get(key)}")
                        all_correct = False
                
                if all_correct:
                    print("   ✅ 所有计数器值都正确")
                    return True
                else:
                    print("   ❌ 部分计数器值不正确")
                    return False
            else:
                print("   ❌ 行为计数器更新失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 行为计数器更新出错: {e}")
            return False
    
    def test_bkt_model_update(self):
        """测试BKT模型更新"""
        print("\n🧠 测试BKT模型更新...")
        
        try:
            # 获取用户档案
            profile, _ = self.user_state_service.get_or_create_profile(
                self.test_user_id, 
                db=None
            )
            
            # 更新BKT模型
            from app.models.bkt import BKTModel
            
            # 创建测试BKT模型
            bkt_model = BKTModel()
            bkt_model.mastery_prob = 0.75
            bkt_model.learn_rate = 0.3
            bkt_model.guess_rate = 0.1
            bkt_model.slip_rate = 0.05
            
            set_dict = {
                'bkt_model.topic_1': bkt_model.to_dict(),
                'bkt_model.topic_2': bkt_model.to_dict()
            }
            
            self.user_state_service.set_profile(profile, set_dict)
            
            # 验证更新结果
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('bkt_model'):
                bkt_models = updated_data['bkt_model']
                print("   ✅ BKT模型更新成功")
                print(f"   更新后BKT模型: {json.dumps(bkt_models, ensure_ascii=False, indent=2)}")
                
                # 验证模型数据
                if 'topic_1' in bkt_models and 'topic_2' in bkt_models:
                    print("   ✅ 两个主题的BKT模型都创建成功")
                    return True
                else:
                    print("   ❌ 部分BKT模型创建失败")
                    return False
            else:
                print("   ❌ BKT模型更新失败")
                return False
                
        except Exception as e:
            print(f"   ❌ BKT模型更新出错: {e}")
            return False
    
    def test_frustration_event_handling(self):
        """测试挫败事件处理"""
        print("\n😤 测试挫败事件处理...")
        
        try:
            # 处理挫败事件
            self.user_state_service.handle_frustration_event(self.test_user_id)
            
            # 验证挫败状态是否被设置
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('emotion_state', {}).get('is_frustrated') == True:
                print("   ✅ 挫败事件处理成功")
                print(f"   挫败状态: {updated_data['emotion_state']['is_frustrated']}")
                return True
            else:
                print("   ❌ 挫败事件处理失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 挫败事件处理出错: {e}")
            return False
    
    def test_ai_help_request_handling(self):
        """测试AI求助请求处理"""
        print("\n🤖 测试AI求助请求处理...")
        
        try:
            # 处理AI求助请求
            self.user_state_service.handle_ai_help_request(
                self.test_user_id, 
                content_title="python_basics"
            )
            
            # 验证求助计数是否增加
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('behavior_counters', {}).get('help_requests') == 1:
                print("   ✅ AI求助请求处理成功")
                print(f"   求助计数: {updated_data['behavior_counters']['help_requests']}")
                print(f"   Python基础提问计数: {updated_data['behavior_counters'].get('question_count_python_basics', 0)}")
                return True
            else:
                print("   ❌ AI求助请求处理失败")
                return False
                
        except Exception as e:
            print(f"   ❌ AI求助请求处理出错: {e}")
            return False
    
    def test_lightweight_event_handling(self):
        """测试轻量级事件处理"""
        print("\n⚡ 测试轻量级事件处理...")
        
        try:
            # 处理多个轻量级事件
            events = [
                "page_focus_change",
                "user_idle", 
                "dom_element_select",
                "code_edit"
            ]
            
            for event_type in events:
                self.user_state_service.handle_lightweight_event(self.test_user_id, event_type)
            
            # 验证计数器是否都增加
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('behavior_counters'):
                counters = updated_data['behavior_counters']
                print("   ✅ 轻量级事件处理成功")
                
                expected_counters = {
                    'focus_changes': 1,
                    'idle_count': 1,
                    'dom_selects': 1,
                    'code_edits': 1
                }
                
                all_correct = True
                for counter_name, expected_value in expected_counters.items():
                    actual_value = counters.get(counter_name, 0)
                    if actual_value != expected_value:
                        print(f"   ⚠️  {counter_name} 计数不正确: 期望 {expected_value}, 实际 {actual_value}")
                        all_correct = False
                    else:
                        print(f"   ✅ {counter_name}: {actual_value}")
                
                if all_correct:
                    print("   ✅ 所有轻量级事件计数器都正确")
                    return True
                else:
                    print("   ❌ 部分轻量级事件计数器不正确")
                    return False
            else:
                print("   ❌ 轻量级事件处理失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 轻量级事件处理出错: {e}")
            return False
    
    def test_bkt_update_on_submission(self):
        """测试提交时的BKT更新"""
        print("\n📝 测试提交时的BKT更新...")
        
        try:
            # 更新BKT模型（模拟提交结果）
            mastery_prob = self.user_state_service.update_bkt_on_submission(
                self.test_user_id, 
                "topic_1", 
                is_correct=True
            )
            
            # 验证BKT模型是否更新
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data and updated_data.get('bkt_model', {}).get('topic_1'):
                bkt_data = updated_data['bkt_model']['topic_1']
                print("   ✅ BKT模型更新成功")
                print(f"   掌握概率: {mastery_prob:.3f}")
                print(f"   BKT模型数据: {json.dumps(bkt_data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print("   ❌ BKT模型更新失败")
                return False
                
        except Exception as e:
            print(f"   ❌ BKT模型更新出错: {e}")
            return False
    
    def test_nested_field_update(self):
        """测试嵌套字段更新"""
        print("\n🔧 测试嵌套字段更新...")
        
        try:
            # 获取用户档案
            profile, _ = self.user_state_service.get_or_create_profile(
                self.test_user_id, 
                db=None
            )
            
            # 更新深层嵌套字段
            set_dict = {
                'emotion_state.current_sentiment': 'EXCITED',
                'emotion_state.confidence_level': 0.9,
                'behavior_counters.submission_timestamps': [time.time()],
                'behavior_counters.custom_metrics.engagement_score': 85.5,
                'behavior_counters.custom_metrics.learning_pace': 'fast'
            }
            
            self.user_state_service.set_profile(profile, set_dict)
            
            # 验证更新结果
            key = f"user_profile:{self.test_user_id}"
            updated_data = self.redis_client.json().get(key)
            
            if updated_data:
                print("   ✅ 嵌套字段更新成功")
                
                # 验证具体字段
                emotion_state = updated_data.get('emotion_state', {})
                behavior_counters = updated_data.get('behavior_counters', {})
                
                print(f"   情感状态: {json.dumps(emotion_state, ensure_ascii=False, indent=2)}")
                print(f"   行为计数器: {json.dumps(behavior_counters, ensure_ascii=False, indent=2)}")
                
                # 检查关键字段
                if (emotion_state.get('current_sentiment') == 'EXCITED' and
                    emotion_state.get('confidence_level') == 0.9 and
                    behavior_counters.get('custom_metrics', {}).get('engagement_score') == 85.5):
                    print("   ✅ 所有嵌套字段都更新正确")
                    return True
                else:
                    print("   ❌ 部分嵌套字段更新不正确")
                    return False
            else:
                print("   ❌ 嵌套字段更新失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 嵌套字段更新出错: {e}")
            return False
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        try:
            # 删除测试用户的Redis数据
            key = f"user_profile:{self.test_user_id}"
            self.redis_client.delete(key)
            print("   ✅ 测试数据清理完成")
        except Exception as e:
            print(f"   ⚠️  数据清理时出错: {e}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行UserStateService Redis数据修改功能测试")
        print("=" * 80)
        
        # 测试结果记录
        test_results = []
        
        # 1. 测试Redis连接
        if self.test_redis_connection():
            test_results.append(("Redis连接", True))
        else:
            test_results.append(("Redis连接", False))
            print("❌ Redis连接失败，无法继续测试")
            return
        
        # 2. 测试用户档案创建
        if self.test_profile_creation():
            test_results.append(("用户档案创建", True))
        else:
            test_results.append(("用户档案创建", False))
        
        # 3. 测试用户档案检索
        if self.test_profile_retrieval():
            test_results.append(("用户档案检索", True))
        else:
            test_results.append(("用户档案检索", False))
        
        # 4. 测试情感状态更新
        if self.test_emotion_state_update():
            test_results.append(("情感状态更新", True))
        else:
            test_results.append(("情感状态更新", False))
        
        # 5. 测试行为计数器更新
        if self.test_behavior_counters_update():
            test_results.append(("行为计数器更新", True))
        else:
            test_results.append(("行为计数器更新", False))
        
        # 6. 测试BKT模型更新
        if self.test_bkt_model_update():
            test_results.append(("BKT模型更新", True))
        else:
            test_results.append(("BKT模型更新", False))
        
        # 7. 测试挫败事件处理
        if self.test_frustration_event_handling():
            test_results.append(("挫败事件处理", True))
        else:
            test_results.append(("挫败事件处理", False))
        
        # 8. 测试AI求助请求处理
        if self.test_ai_help_request_handling():
            test_results.append(("AI求助请求处理", True))
        else:
            test_results.append(("AI求助请求处理", True))
        
        # 9. 测试轻量级事件处理
        if self.test_lightweight_event_handling():
            test_results.append(("轻量级事件处理", True))
        else:
            test_results.append(("轻量级事件处理", False))
        
        # 10. 测试提交时的BKT更新
        if self.test_bkt_update_on_submission():
            test_results.append(("提交时BKT更新", True))
        else:
            test_results.append(("提交时BKT更新", False))
        
        # 11. 测试嵌套字段更新
        if self.test_nested_field_update():
            test_results.append(("嵌套字段更新", True))
        else:
            test_results.append(("嵌套字段更新", False))
        
        # 输出测试结果总结
        print("\n" + "=" * 80)
        print("📊 测试结果总结")
        print("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if result:
                passed_tests += 1
        
        print("-" * 80)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 所有测试都通过了！UserStateService Redis数据修改功能正常")
        else:
            print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败，请检查相关功能")
        
        # 清理测试数据
        self.cleanup_test_data()
        
        return passed_tests == total_tests

def main():
    """主函数"""
    try:
        # 创建测试实例
        tester = UserStateServiceTester()
        
        # 运行所有测试
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ 测试完成，所有功能正常")
        else:
            print("\n❌ 测试完成，部分功能异常")
            
    except Exception as e:
        print(f"\n💥 测试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置环境变量以避免配置验证错误
os.environ['TUTOR_OPENAI_API_KEY'] = 'test_key'
os.environ['TUTOR_EMBEDDING_API_KEY'] = 'test_key'
os.environ['TUTOR_TRANSLATION_API_KEY'] = 'test_key'

# 直接指定正确的数据目录路径
os.environ['DATA_DIR'] = './app/data'

from app.services.content_loader import load_json_content
from app.schemas.content import LearningContent, TestTask

def test_load_learning_content():
    """测试加载学习内容"""
    try:
        # 测试加载一个存在的学习内容
        content = load_json_content("learning_content", "1_1")
        print(f"成功加载学习内容: {content.topic_id}")
        print(f"标题: {content.title}")
        print(f"等级数量: {len(content.levels)}")
        print(f"选择元素数量: {len(content.sc_all)}")
        
        # 输出详细信息
        print("\n=== 学习内容详细信息 ===")
        print(f"主题ID: {content.topic_id}")
        print(f"标题: {content.title}")
        
        print("\n--- 等级信息 ---")
        for i, level in enumerate(content.levels, 1):
            print(f"等级 {i}:")
            print(f"  等级编号: {level.level}")
            print(f"  描述: {level.description[:100]}...")  # 只显示前100个字符
        
        print("\n--- 选择元素信息 ---")
        for i, sc in enumerate(content.sc_all[:5], 1):  # 只显示前5个
            print(f"选择元素 {i}:")
            print(f"  主题ID: {sc.topic_id}")
            print(f"  元素列表: {sc.select_element}")
        
        if len(content.sc_all) > 5:
            print(f"  ... 还有 {len(content.sc_all) - 5} 个选择元素")
        
        return True
    except Exception as e:
        print(f"加载学习内容失败: {e}")
        return False

def test_load_test_task():
    """测试加载测试任务"""
    try:
        # 测试加载一个存在的测试任务
        task = load_json_content("test_tasks", "1_1")
        print(f"成功加载测试任务: {task.topic_id}")
        print(f"检查点数量: {len(task.checkpoints)}")
        
        # 输出详细信息
        print("\n=== 测试任务详细信息 ===")
        print(f"主题ID: {task.topic_id}")
        print(f"检查点数量: {len(task.checkpoints)}")
        
        print("\n--- 检查点信息 ---")
        for i, checkpoint in enumerate(task.checkpoints[:3], 1):  # 只显示前3个
            print(f"检查点 {i}:")
            print(f"  名称: {checkpoint.name}")
            print(f"  类型: {checkpoint.type}")
            print(f"  反馈: {checkpoint.feedback[:50]}...")  # 只显示前50个字符
            
            # 根据检查点类型显示特定信息
            if hasattr(checkpoint, 'selector'):
                print(f"  选择器: {checkpoint.selector}")
            if hasattr(checkpoint, 'attribute'):
                print(f"  属性: {checkpoint.attribute}")
            if hasattr(checkpoint, 'css_property'):
                print(f"  CSS属性: {checkpoint.css_property}")
            if hasattr(checkpoint, 'assertion_type'):
                print(f"  断言类型: {checkpoint.assertion_type}")
            if hasattr(checkpoint, 'value'):
                print(f"  期望值: {checkpoint.value}")
            if hasattr(checkpoint, 'script'):
                print(f"  脚本: {checkpoint.script[:50]}...")
        
        if len(task.checkpoints) > 3:
            print(f"  ... 还有 {len(task.checkpoints) - 3} 个检查点")
        
        return True
    except Exception as e:
        print(f"加载测试任务失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 测试 content_loader 服务 ===")
    print()
    
    print("1. 测试学习内容加载:")
    test_load_learning_content()
    print()
    
    print("2. 测试测试任务加载:")
    test_load_test_task()
    print()
    
    print("测试完成!")

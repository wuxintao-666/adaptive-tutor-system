import pytest
import sys
import os
import json

# 获取项目根目录路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.app.models.bkt import BKTModel

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "bkt_test_cases.json")

# 验证路径是否存在
if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(
        f"测试数据文件未找到，预期路径: {DATA_FILE}\n"
        f"当前工作目录: {os.getcwd()}"
    )
class TestBKTModel:
    def test_default_initialization(self):
        """测试默认参数初始化"""
        model = BKTModel()
        assert model.p_init == 0.2
        assert model.get_mastery_prob() == 0.2

    def test_custom_initialization(self):
        """测试自定义参数初始化"""
        params = {
            'p_init': 0.5,
            'p_transit': 0.3,
            'p_slip': 0.05,
            'p_guess': 0.25
        }
        model = BKTModel(params)
        assert model.p_init == 0.5
        assert model.p_transit == 0.3
        assert model.p_slip == 0.05
        assert model.p_guess == 0.25
        assert model.get_mastery_prob() == 0.5

    def test_update_correct_answer(self):
        """测试答对题后掌握概率上升"""
        model = BKTModel({'p_init': 0.2, 'p_transit': 0.15, 'p_slip': 0.1, 'p_guess': 0.2})
        old_prob = model.get_mastery_prob()
        new_prob = model.update(is_correct=True)
        assert new_prob > old_prob
        assert 0 <= new_prob <= 1

    def test_update_wrong_answer(self):
        """测试答错题后掌握概率下降"""
        model = BKTModel({'p_init': 0.8, 'p_transit': 0.15, 'p_slip': 0.1, 'p_guess': 0.2})
        old_prob = model.get_mastery_prob()
        new_prob = model.update(is_correct=False)
        assert new_prob < old_prob
        assert 0 <= new_prob <= 1

    def test_update_probability_bounds(self):
        """测试概率边界值（不能超过[0,1]）"""
        model = BKTModel({'p_init': 1.0, 'p_transit': 0.5, 'p_slip': 0.0, 'p_guess': 0.0})
        prob = model.update(is_correct=True)
        assert 0.0 <= prob <= 1.0

        model = BKTModel({'p_init': 0.0, 'p_transit': 0.0, 'p_slip': 1.0, 'p_guess': 0.0})
        prob = model.update(is_correct=False)
        assert 0.0 <= prob <= 1.0

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        model = BKTModel({'p_init': 0.3, 'p_transit': 0.2, 'p_slip': 0.05, 'p_guess': 0.25})
        model.update(True)  # 更新一次状态
        data = model.to_dict()
        assert isinstance(data, dict)
        new_model = BKTModel.from_dict(data)
        assert new_model.to_dict() == data

    def test_str_representation(self):
        """测试 __str__ 方法输出格式"""
        model = BKTModel()
        assert "BKTModel" in str(model)
        assert "mastery_prob" in str(model)

    @pytest.mark.parametrize("answers", [
        [True, True, False, True],
        [False, False, True, True],
        [True, False, True, False]
    ])
    def test_update_sequence(self, answers):
        """测试一组答题序列的掌握概率变化"""
        model = BKTModel()
        probs = []
        for ans in answers:
            probs.append(model.update(ans))
        assert all(0.0 <= p <= 1.0 for p in probs)


class TestBKTModelDataDriven:
    """从数据文件读取测试用例"""
    @pytest.mark.parametrize("case", json.load(open(DATA_FILE)))
    def test_cases_from_file(self, case):
        print(f"\nTesting Case: {case['params']}")
        model = BKTModel(case["params"])
        
        for i, ans in enumerate(case["answers"], 1):
            prob = model.update(ans)
            print(f"  Step {i}: {'✓' if ans else '✗'} → mastery={prob:.3f}")
        
        mastery = model.get_mastery_prob()
        low, high = case["expected_range"]
        print(f"  Final: {mastery:.3f} (expected {low}-{high})")
        
        assert low <= mastery <= high

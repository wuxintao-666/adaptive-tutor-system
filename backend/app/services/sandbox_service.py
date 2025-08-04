import re
from playwright.sync_api import sync_playwright, Page, expect, Error
from typing import Dict, Any, List


class SandboxService:
    def run_evaluation(self, user_code: Dict[str, str], checkpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        passed_all = True

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                full_html = f"""
                  <!DOCTYPE html><html><head><style>{user_code.get('css', '')}</style></head>
                  <body>{user_code.get('html', '')}</body>
                  <script>{user_code.get('js', '')}</script></html>
                  """
                page.set_content(full_html, wait_until="load")  # 等待页面加载完成

                for i, cp in enumerate(checkpoints):
                    passed, detail = SandboxService._evaluate_checkpoint(page, cp)
                    if not passed:
                        passed_all = False
                        # 如果检查点有自定义反馈，使用它，否则用默认的
                        feedback = cp.get("feedback", detail)
                        results.append(f"检查点 {i + 1} 失败: {feedback}")

                browser.close()
        except Error as e:
            return {"passed": False, "message": "评测服务发生内部错误。", "details": [str(e)]}

        message = "恭喜！所有测试点都通过了！" if passed_all else "很遗憾，部分测试点未通过。"
        return {"passed": passed_all, "message": message, "details": results}


    @staticmethod
    def _evaluate_checkpoint(page: Page, checkpoint: Dict[str, Any]) -> (bool, str):
        cp_type = checkpoint.get("type")
        try:
            # 执行交互 (如果需要)
            if cp_type == "interaction_and_assert":
                action_type = checkpoint.get("action_type")
                action_selector = checkpoint.get("action_selector")
                if action_type == "click":
                    page.locator(action_selector).click()
                # TODO: cxz 需要和佳迪做对接，补充其他的操作，如输入文本、悬停、拖拽等

                # 交互后，对嵌套的断言进行评估
                return SandboxService._evaluate_assertion(page, checkpoint.get("assertion"))
            else:
                # 如果不是交互式检查点，直接评估断言
                return SandboxService._evaluate_assertion(page, checkpoint)

        except Exception as e:
            return False, f"执行检查点时发生错误: {e}"


    @staticmethod
    def _evaluate_assertion(page: Page, assertion: Dict[str, Any]) -> (bool, str):
        """
        专门处理各种非交互的断言的私有方法
        """
        assertion_type = assertion.get("type")
        selector = assertion.get("selector")

        try:
            if assertion_type == "assert_style":
                """
                 actual_value = page.locator(selector).evaluate(...)
                 if assertion['assertion_type'] == 'greater_than':
                     return float(actual_value.replace('px','')) > float(assertion['value'].replace('px',''))
                 
                  1. 获取逻辑不完整: evaluate(...) 里面的核心 JavaScript
                  代码没有写。你需要提供一个函数来获取具体的样式属性，例如：
                  // JS to be run inside evaluate
                  (element, prop) => window.getComputedStyle(element).getPropertyValue(prop)
                  1. 并且，你需要从 assertion 数据中知道要获取哪个CSS属性 (比如 width, color,
                  font-size)。
                  2. 单位处理过于简单: 代码 actual_value.replace('px','')
                  只处理了像素（px）单位，非常脆弱。CSS 的值可以有各种单位（em, rem, %, vh
                  等），甚至没有单位（如
                  font-weight）。一个健壮的实现需要能够解析这些不同的单位并进行正确比较。
                  3. 比较逻辑不完整: 它只示意了 greater_than 的情况，而一个完整的样式断言需要支持等于       
                """
                # TODO: cxz 需要实现完整的样式断言逻辑，包括获取CSS属性值、处理不同单位、支持多种比较操作符（等于、大于、小于等）
                pass  # 示意

            elif assertion_type == "assert_text_content":
                locator = page.locator(selector)
                if assertion['assertion_type'] == 'contains':
                    expect(locator).to_contain_text(assertion['value'])
                elif assertion['assertion_type'] == 'matches_regex':
                    expect(locator).to_have_text(re.compile(assertion['value']))

            # ... 实现其他所有断言类型的逻辑 ...
            elif assertion_type == "assert_attribute":
                # TODO: cxz 需要实现属性断言逻辑，支持检查DOM元素的各种属性值
                pass

            elif assertion_type == "custom_script":
                # TODO: cxz 需要实现自定义脚本断言逻辑，允许执行任意JavaScript代码进行复杂验证
                pass

            return True, "通过"
        except AssertionError as e:
            return False, str(e)
        except Exception as e:
            return False, f"执行断言时发生错误: {e}"


sandbox_service = SandboxService()

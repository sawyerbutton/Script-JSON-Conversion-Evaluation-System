#!/usr/bin/env python3
"""
系统测试脚本
用于快速测试评估系统是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluators.main_evaluator import EvaluationConfig, ScriptEvaluator  # noqa: E402


def test_basic_evaluation():
    """测试基本评估功能"""

    print("=" * 60)
    print("剧本JSON转换评估系统 - 系统测试")
    print("=" * 60)

    # 配置评估器
    config = EvaluationConfig(
        use_deepseek_judge=False,  # 测试时关闭LLM评估（避免API调用）
        run_consistency_check=False,
        save_detailed_report=True,
        save_html_report=False,
    )

    print("\n配置评估器...")
    evaluator = ScriptEvaluator(config)

    # 准备测试数据
    test_case = {
        "source_text": """内景 咖啡馆 - 日

李雷坐在角落里，不安地看着手表。韩梅梅推门而入，表情冷漠。

韩梅梅
（冷淡地）
你想说什么？

李雷
（紧张）
梅梅，关于昨晚的事...

韩梅梅
不用解释了。我都看到了。

韩梅梅转身要走，李雷急忙拉住她的手。

李雷
请听我说完！那不是你想的那样！

韩梅梅甩开他的手，眼中含泪。

韩梅梅
够了。我们结束了。

她快步离开，留下李雷一个人呆坐在那里。""",
        "extracted_json": [
            {
                "scene_id": "S01",
                "setting": "内景 咖啡馆 - 日",
                "characters": ["李雷", "韩梅梅"],
                "scene_mission": "展现两人关系的破裂",
                "key_events": ["韩梅梅冷漠地到来", "李雷试图解释被拒绝", "韩梅梅宣布分手离开"],
                "info_change": [{"character": "观众", "learned": "两人关系出现重大危机"}],
                "relation_change": [{"chars": ["李雷", "韩梅梅"], "from": "恋人", "to": "分手"}],
                "key_object": [],
                "setup_payoff": {"setup_for": [], "payoff_from": []},
            }
        ],
        "scene_type": "standard",
        "source_file": "test_script_01.txt",
    }

    print("\n准备测试数据...")
    print(f"  - 源文本长度: {len(test_case['source_text'])} 字符")
    print(f"  - 场景数量: {len(test_case['extracted_json'])}")
    print(f"  - 场景类型: {test_case['scene_type']}")

    # 运行评估
    print("\n开始评估...")
    try:
        result = evaluator.evaluate_script(**test_case)

        # 显示结果
        print("\n" + "=" * 60)
        print("评估完成！")
        print("=" * 60)

        print(f"\n文件: {result.source_file}")
        print(f"质量级别: {result.quality_level}")
        print(f"总分: {result.overall_score:.3f}")
        print(f"通过: {'✅ 是' if result.passed else '❌ 否'}")

        print("\n各项得分:")
        print(f"  结构验证: {result.structure_score:.3f}")
        print(f"  场景边界: {result.boundary_score:.3f}")
        print(f"  角色提取: {result.character_score:.3f}")
        print(f"  语义准确: {result.semantic_score:.3f}")

        if result.issues:
            print(f"\n发现 {len(result.issues)} 个问题:")
            for i, issue in enumerate(result.issues[:5], 1):
                print(f"  {i}. [{issue.get('severity', 'unknown')}] {issue.get('message', 'N/A')}")

        print("\n改进建议:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")

        print("\n统计信息:")
        print(f"  场景总数: {result.total_scenes}")
        print(f"  角色总数: {result.total_characters}")

        print("\n" + "=" * 60)
        print("测试成功完成！✅")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_model_validation():
    """测试Pydantic模型验证"""

    print("\n" + "=" * 60)
    print("测试数据模型验证")
    print("=" * 60)

    try:
        from models.scene_models import validate_script_json

        # 测试有效数据
        valid_scene = {
            "scene_id": "S01",
            "setting": "内景 咖啡馆 - 日",
            "characters": ["角色A", "角色B"],
            "scene_mission": "测试场景",
            "key_events": ["事件1"],
        }

        print("\n测试有效数据...")
        result = validate_script_json(valid_scene, "standard")

        if result["valid"]:
            print("✅ 有效数据验证通过")
        else:
            print("❌ 有效数据验证失败")
            for error in result["errors"]:
                print(f"  错误: {error}")

        # 测试无效数据
        invalid_scene = {
            "scene_id": "场景1",  # 格式错误
            "setting": "某个地方",  # 缺少内外景标记
            "characters": [],
            "scene_mission": "测试",
            "key_events": [],  # 不能为空
        }

        print("\n测试无效数据（应该失败）...")
        result2 = validate_script_json(invalid_scene, "standard")

        if not result2["valid"]:
            print("✅ 无效数据正确被拒绝")
            print("  错误信息:")
            for error in result2["errors"]:
                print(f"    - {error}")
        else:
            print("❌ 无效数据未被检测到")

        print("\n模型验证测试完成！✅")
        return True

    except Exception as e:
        print(f"\n❌ 模型验证测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_file_handler():
    """测试文件处理功能"""

    print("\n" + "=" * 60)
    print("测试文件处理功能")
    print("=" * 60)

    try:
        from utils.file_handler import FileHandler

        handler = FileHandler()

        # 测试写入和读取
        test_data = {"test": "数据", "中文": "支持"}

        test_file = "test_temp.json"

        print("\n测试JSON文件写入...")
        handler.write_json_file(test_file, test_data)
        print("✅ 写入成功")

        print("\n测试JSON文件读取...")
        loaded_data = handler.read_json_file(test_file)
        print("✅ 读取成功")

        if loaded_data == test_data:
            print("✅ 数据一致性验证通过")
        else:
            print("❌ 数据不一致")

        # 清理
        os.remove(test_file)
        print("\n文件处理测试完成！✅")
        return True

    except Exception as e:
        print(f"\n❌ 文件处理测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """主测试函数"""

    print("\n🚀 开始系统测试...\n")

    results = []

    # 运行各项测试
    results.append(("文件处理", test_file_handler()))
    results.append(("模型验证", test_model_validation()))
    results.append(("基本评估", test_basic_evaluation()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(result for _, result in results)

    if all_passed:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

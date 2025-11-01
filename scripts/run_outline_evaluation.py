#!/usr/bin/env python3
"""
故事大纲完整评估流程脚本
从大纲文本 -> JSON转换 -> 质量评估
"""

import sys
from pathlib import Path

# 添加src到路径  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from convert_outline_to_json import convert_outline_to_json  # noqa: E402

from evaluators.main_evaluator import EvaluationConfig, ScriptEvaluator  # noqa: E402
from utils.file_handler import FileHandler  # noqa: E402


def run_outline_evaluation(
    outline_file: str,
    use_llm_judge: bool = True,
    save_json: bool = True,
):
    """
    运行完整的大纲评估流程

    Args:
        outline_file: 大纲文件路径
        use_llm_judge: 是否使用LLM进行语义评估
        save_json: 是否保存转换后的JSON
    """
    print("=" * 70)
    print("故事大纲JSON转换评估系统 - 完整评估流程")
    print("=" * 70)

    # 步骤1: 读取大纲
    print(f"\n[步骤 1/3] 读取故事大纲文件: {outline_file}")
    file_handler = FileHandler()
    outline_text = file_handler.read_text_file(outline_file)
    print(f"  文件大小: {len(outline_text)} 字符")

    # 步骤2: 转换为JSON
    print("\n[步骤 2/3] 使用DeepSeek API转换大纲为JSON...")
    print("  场景类型: outline（允许推断和简化）")

    try:
        json_data = convert_outline_to_json(outline_text, validate=True)

        if save_json:
            # 保存到outputs/converted/目录
            output_dir = Path(__file__).parent.parent / "outputs" / "converted"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{Path(outline_file).stem}_outline_output.json"
            file_handler.write_json_file(str(output_file), json_data)
            print(f"  ✅ JSON已保存到: {output_file}")

    except Exception as e:
        print(f"  ❌ 转换失败: {e}")
        return None

    # 步骤3: 质量评估
    print("\n[步骤 3/3] 运行质量评估...")
    print(f"  使用LLM语义评估: {'是' if use_llm_judge else '否'}")

    config = EvaluationConfig(
        use_deepseek_judge=use_llm_judge,
        run_consistency_check=False,  # 关闭一致性检查节省时间
        save_detailed_report=True,
        save_html_report=False,  # 关闭HTML报告
    )

    evaluator = ScriptEvaluator(config)

    try:
        result = evaluator.evaluate_script(
            source_text=outline_text,
            extracted_json=json_data,
            scene_type="outline",  # 使用outline场景类型
            source_file=outline_file,
        )

        # 显示评估结果
        print("\n" + "=" * 70)
        print("评估结果")
        print("=" * 70)

        print(f"\n文件: {result.source_file}")
        print("类型: 故事大纲")
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

        if result.recommendations:
            print("\n改进建议:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")

        print("\n统计信息:")
        print(f"  场景总数: {result.total_scenes}")
        print(f"  角色总数: {result.total_characters}")

        print("\n大纲特点:")
        inferred_count = sum(1 for scene in json_data if "推断" in scene.get("setting", ""))
        print(f"  推断的场景设置: {inferred_count}/{len(json_data)}")

        print("\n" + "=" * 70)
        print("✅ 评估完成！")
        print("=" * 70)

        return result

    except Exception as e:
        print(f"\n❌ 评估失败: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="运行完整的故事大纲评估流程")
    parser.add_argument("outline_file", help="故事大纲文件路径")
    parser.add_argument(
        "--no-llm-judge", action="store_true", help="不使用LLM进行语义评估（节省API调用）"
    )
    parser.add_argument("--no-save-json", action="store_true", help="不保存转换后的JSON文件")

    args = parser.parse_args()

    result = run_outline_evaluation(
        outline_file=args.outline_file,
        use_llm_judge=not args.no_llm_judge,
        save_json=not args.no_save_json,
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()

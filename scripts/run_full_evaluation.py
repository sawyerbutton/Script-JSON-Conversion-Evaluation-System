#!/usr/bin/env python3
"""
完整评估流程脚本
从剧本文本 -> JSON转换 -> 质量评估
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from convert_script_to_json import convert_script_to_json
from evaluators.main_evaluator import EvaluationConfig, ScriptEvaluator
from utils.file_handler import FileHandler


def run_full_evaluation(
    script_file: str,
    scene_type: str = "standard",
    use_llm_judge: bool = True,  # 默认使用LLM评估以获得更准确的语义评分
    save_json: bool = True,
):
    """
    运行完整的评估流程

    Args:
        script_file: 剧本文件路径
        scene_type: 场景类型
        use_llm_judge: 是否使用LLM进行语义评估
        save_json: 是否保存转换后的JSON
    """
    print("=" * 70)
    print("剧本JSON转换评估系统 - 完整评估流程")
    print("=" * 70)

    # 步骤1: 读取剧本
    print(f"\n[步骤 1/3] 读取剧本文件: {script_file}")
    file_handler = FileHandler()
    script_text = file_handler.read_text_file(script_file)
    print(f"  文件大小: {len(script_text)} 字符")

    # 步骤2: 转换为JSON
    print(f"\n[步骤 2/3] 使用DeepSeek API转换剧本为JSON...")
    print(f"  场景类型: {scene_type}")

    try:
        json_data = convert_script_to_json(
            script_text, scene_type=scene_type, validate=True
        )

        if save_json:
            # 保存到outputs/converted/目录
            output_dir = Path(__file__).parent.parent / "outputs" / "converted"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{Path(script_file).stem}_output.json"
            file_handler.write_json_file(str(output_file), json_data)
            print(f"  ✅ JSON已保存到: {output_file}")

    except Exception as e:
        print(f"  ❌ 转换失败: {e}")
        return None

    # 步骤3: 质量评估
    print(f"\n[步骤 3/3] 运行质量评估...")
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
            source_text=script_text,
            extracted_json=json_data,
            scene_type=scene_type,
            source_file=script_file,
        )

        # 显示评估结果
        print("\n" + "=" * 70)
        print("评估结果")
        print("=" * 70)

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
                print(
                    f"  {i}. [{issue.get('severity', 'unknown')}] {issue.get('message', 'N/A')}"
                )

        if result.recommendations:
            print("\n改进建议:")
            for i, rec in enumerate(result.recommendations, 1):
                print(f"  {i}. {rec}")

        print("\n统计信息:")
        print(f"  场景总数: {result.total_scenes}")
        print(f"  角色总数: {result.total_characters}")

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

    parser = argparse.ArgumentParser(description="运行完整的剧本评估流程")
    parser.add_argument("script_file", help="剧本文件路径")
    parser.add_argument(
        "-t",
        "--type",
        choices=["standard", "outline"],
        default="standard",
        help="场景类型（默认: standard）",
    )
    parser.add_argument(
        "--no-llm-judge", action="store_true", help="不使用LLM进行语义评估（节省API调用）"
    )
    parser.add_argument(
        "--no-save-json", action="store_true", help="不保存转换后的JSON文件"
    )

    args = parser.parse_args()

    result = run_full_evaluation(
        script_file=args.script_file,
        scene_type=args.type,
        use_llm_judge=not args.no_llm_judge,  # 默认True，除非用户指定--no-llm-judge
        save_json=not args.no_save_json,
    )

    if result is None:
        sys.exit(1)


if __name__ == "__main__":
    main()

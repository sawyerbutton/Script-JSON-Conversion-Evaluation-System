#!/usr/bin/env python3
"""
剧本转JSON转换脚本
使用DeepSeek API将剧本文本转换为结构化JSON
"""

import json
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.deepseek_client import DeepSeekClient
from models.scene_models import SceneInfo, validate_script_json
from utils.file_handler import FileHandler


def load_prompt_template(template_name: str = "scene1_extraction.txt") -> str:
    """加载prompt模板"""
    prompt_path = Path(__file__).parent.parent / "prompts" / template_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def convert_script_to_json(
    script_text: str, scene_type: str = "standard", validate: bool = True
) -> dict:
    """
    将剧本文本转换为JSON

    Args:
        script_text: 剧本文本
        scene_type: 场景类型 ("standard" 或 "outline")
        validate: 是否验证生成的JSON

    Returns:
        转换后的JSON数据
    """
    # 初始化DeepSeek客户端
    client = DeepSeekClient()

    # 加载prompt模板
    template_name = (
        "scene1_extraction.txt" if scene_type == "standard" else "scene2_extraction.txt"
    )
    prompt_template = load_prompt_template(template_name)

    # 填充prompt
    prompt = prompt_template.replace("{script_text}", script_text)

    print("正在调用DeepSeek API转换剧本...")
    print(f"使用模板: {template_name}")

    # 调用LLM
    response = client.complete(
        prompt=prompt,
        temperature=0.1,
        max_tokens=4000,
    )

    # 提取JSON
    response_text = response["content"].strip()

    # 尝试从response中提取JSON（可能被包裹在```json```中）
    if "```json" in response_text:
        # 提取代码块中的JSON
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    elif "```" in response_text:
        # 可能没有json标记
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    else:
        # 直接是JSON
        json_text = response_text

    # 解析JSON
    try:
        json_data = json.loads(json_text)
        print(f"✅ JSON解析成功，包含 {len(json_data)} 个场景")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"响应内容:\n{response_text}")
        raise

    # 验证JSON（如果启用）
    if validate:
        print("\n验证JSON格式...")
        for i, scene in enumerate(json_data, 1):
            result = validate_script_json(scene, scene_type)
            if result["valid"]:
                print(f"  场景{i}: ✅ 验证通过")
            else:
                print(f"  场景{i}: ❌ 验证失败")
                for error in result["errors"]:
                    print(f"    - {error}")

    return json_data


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="将剧本文本转换为JSON格式")
    parser.add_argument("input_file", help="输入剧本文件路径")
    parser.add_argument(
        "-o", "--output", help="输出JSON文件路径（可选，默认为input_file.json）"
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["standard", "outline"],
        default="standard",
        help="场景类型（默认: standard）",
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="跳过JSON验证"
    )

    args = parser.parse_args()

    # 读取输入文件
    file_handler = FileHandler()
    print(f"读取剧本文件: {args.input_file}")
    script_text = file_handler.read_text_file(args.input_file)
    print(f"文件大小: {len(script_text)} 字符\n")

    # 转换
    try:
        json_data = convert_script_to_json(
            script_text, scene_type=args.type, validate=not args.no_validate
        )

        # 保存输出
        if args.output:
            output_file = args.output
        else:
            # 默认保存到outputs/converted/目录
            output_dir = Path(__file__).parent.parent / "outputs" / "converted"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{Path(args.input_file).stem}_output.json"

        file_handler.write_json_file(str(output_file), json_data)

        print(f"\n✅ 转换完成！JSON已保存到: {output_file}")

        # 显示统计信息
        print(f"\n统计信息:")
        print(f"  场景数量: {len(json_data)}")

        all_characters = set()
        for scene in json_data:
            all_characters.update(scene.get("characters", []))
        print(f"  角色数量: {len(all_characters)}")
        print(f"  角色列表: {', '.join(sorted(all_characters))}")

    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

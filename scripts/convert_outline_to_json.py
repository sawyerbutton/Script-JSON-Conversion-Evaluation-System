#!/usr/bin/env python3
"""
故事大纲转JSON转换脚本
使用DeepSeek API将故事大纲转换为结构化JSON
与标准剧本相比，大纲转换更灵活，允许合理推断
"""

import json
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.deepseek_client import DeepSeekClient
from models.scene_models import OutlineSceneInfo, validate_script_json
from utils.file_handler import FileHandler


def load_prompt_template(template_name: str = "scene2_extraction.txt") -> str:
    """加载prompt模板"""
    prompt_path = Path(__file__).parent.parent / "prompts" / template_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def convert_outline_to_json(
    outline_text: str, validate: bool = True
) -> dict:
    """
    将故事大纲转换为JSON

    Args:
        outline_text: 故事大纲文本
        validate: 是否验证生成的JSON

    Returns:
        转换后的JSON数据
    """
    # 初始化DeepSeek客户端
    client = DeepSeekClient()

    # 加载prompt模板
    prompt_template = load_prompt_template("scene2_extraction.txt")

    # 填充prompt
    prompt = prompt_template.replace("{outline_text}", outline_text)

    print("正在调用DeepSeek API转换故事大纲...")
    print(f"使用模板: scene2_extraction.txt")
    print(f"大纲特点: 允许合理推断、简化场景ID格式、更灵活的验证规则")

    # 调用LLM
    response = client.complete(
        prompt=prompt,
        temperature=0.2,  # 大纲转换允许稍高的温度以支持推断
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
        print("\n验证JSON格式（使用大纲模式）...")
        for i, scene in enumerate(json_data, 1):
            result = validate_script_json(scene, scene_type="outline")
            if result["valid"]:
                print(f"  场景{i}: ✅ 验证通过")

                # 显示推断的内容
                if scene.get("setting") and "推断" in scene.get("setting", ""):
                    print(f"    ℹ️ 场景设置为推断: {scene['setting']}")
            else:
                print(f"  场景{i}: ❌ 验证失败")
                for error in result["errors"]:
                    print(f"    - {error}")

    return json_data


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="将故事大纲转换为JSON格式")
    parser.add_argument("input_file", help="输入大纲文件路径")
    parser.add_argument(
        "-o", "--output", help="输出JSON文件路径（可选，默认为input_file.json）"
    )
    parser.add_argument(
        "--no-validate", action="store_true", help="跳过JSON验证"
    )

    args = parser.parse_args()

    # 读取输入文件
    file_handler = FileHandler()
    print(f"读取故事大纲文件: {args.input_file}")
    outline_text = file_handler.read_text_file(args.input_file)
    print(f"文件大小: {len(outline_text)} 字符\n")

    # 转换
    try:
        json_data = convert_outline_to_json(
            outline_text, validate=not args.no_validate
        )

        # 保存输出
        if args.output:
            output_file = args.output
        else:
            # 默认保存到outputs/converted/目录
            output_dir = Path(__file__).parent.parent / "outputs" / "converted"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{Path(args.input_file).stem}_outline_output.json"

        file_handler.write_json_file(str(output_file), json_data)

        print(f"\n✅ 转换完成！JSON已保存到: {output_file}")

        # 显示统计信息
        print(f"\n统计信息:")
        print(f"  场景数量: {len(json_data)}")

        all_characters = set()
        inferred_settings = 0
        for scene in json_data:
            all_characters.update(scene.get("characters", []))
            if scene.get("setting") and "推断" in scene.get("setting", ""):
                inferred_settings += 1

        print(f"  角色数量: {len(all_characters)}")
        if all_characters:
            print(f"  角色列表: {', '.join(sorted(all_characters))}")
        print(f"  推断场景设置数: {inferred_settings}/{len(json_data)}")

        # 显示示例场景
        if json_data:
            print(f"\n示例场景（第1个）:")
            first_scene = json_data[0]
            print(f"  ID: {first_scene.get('scene_id')}")
            print(f"  设置: {first_scene.get('setting')}")
            print(f"  任务: {first_scene.get('scene_mission')}")
            print(f"  关键事件: {len(first_scene.get('key_events', []))} 个")

    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

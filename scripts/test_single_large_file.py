#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单个大文件快速测试脚本
用于验证优化后的reasoner模型处理效果
"""

import os
import sys
import json
import re
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_handler import FileHandler
from src.llm.deepseek_client import DeepSeekClient, DeepSeekConfig

# 从批量测试脚本导入函数
sys.path.insert(0, str(project_root / "scripts"))
from batch_test_all_scripts import (
    load_prompt_template,
    extract_and_clean_json,
    attempt_json_repair,
)


def test_single_file(script_path: str):
    """测试单个剧本文件"""
    print("=" * 70)
    print("单个大文件测试")
    print("=" * 70)
    print(f"测试文件: {script_path}")
    print()

    # 初始化
    file_handler = FileHandler()
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    # 初始化reasoner模型客户端
    reasoner_config = DeepSeekConfig(api_key=api_key, model="deepseek-reasoner")
    llm_client = DeepSeekClient(config=reasoner_config, debug=True)

    print(f"模型配置: {reasoner_config.model}")
    print(f"最大输出: {reasoner_config.max_tokens} tokens")
    print()

    # 读取文件
    script_text = file_handler.read_text_file(script_path)
    file_size = len(script_text)
    print(f"文件大小: {file_size} 字符")
    print()

    # 加载prompt模板
    prompt_template = load_prompt_template("scene1_extraction.txt")
    prompt = prompt_template.replace("{script_text}", script_text)

    # 调用LLM
    print("正在调用DeepSeek Reasoner API...")
    print("(允许模型思考，这可能需要较长时间)")
    print()

    start_time = time.time()
    response = llm_client.complete(
        prompt=prompt, temperature=0.1, max_tokens=reasoner_config.max_tokens
    )
    duration = time.time() - start_time

    print(f"✅ API调用完成，耗时: {duration:.2f}秒")
    print()

    # 获取原始响应
    response_text = response["content"].strip()
    response_length = len(response_text)
    tokens_used = response.get("tokens_used", 0)

    print(f"响应长度: {response_length} 字符")
    print(f"Tokens使用: {tokens_used}")
    print()

    # 检查是否包含思考过程
    has_thinking = "<think>" in response_text or "<thinking>" in response_text
    if has_thinking:
        print("✅ 检测到思考过程标签")
        # 提取思考内容长度
        think_match = re.search(
            r"<think>(.*?)</think>", response_text, re.DOTALL
        ) or re.search(r"<thinking>(.*?)</thinking>", response_text, re.DOTALL)
        if think_match:
            thinking_content = think_match.group(1)
            print(f"   思考内容长度: {len(thinking_content)} 字符")
            print(f"   思考内容预览: {thinking_content[:200]}...")
    else:
        print("ℹ️  未检测到思考过程标签")
    print()

    # 提取并清理JSON
    print("提取JSON...")
    json_text = extract_and_clean_json(response_text, is_large_file=True)
    print(f"清理后JSON长度: {len(json_text)} 字符")
    print(f"JSON预览: {json_text[:300]}...")
    print()

    # 解析JSON
    print("解析JSON...")
    try:
        json_data = json.loads(json_text)
        scene_count = len(json_data)
        print(f"✅ JSON解析成功！")
        print(f"   场景数量: {scene_count}")
        print()

        # 显示第一个场景
        if json_data:
            print("第一个场景示例:")
            print(json.dumps(json_data[0], ensure_ascii=False, indent=2)[:500])
            print()

        return {
            "success": True,
            "scene_count": scene_count,
            "duration": duration,
            "tokens_used": tokens_used,
            "response_length": response_length,
            "has_thinking": has_thinking,
        }

    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"   错误位置: 第{e.lineno}行, 第{e.colno}列")
        print()

        # 尝试修复
        print("尝试自动修复JSON...")
        fixed_json = attempt_json_repair(json_text)
        if fixed_json:
            try:
                json_data = json.loads(fixed_json)
                print(f"✅ JSON修复成功！")
                print(f"   场景数量: {len(json_data)}")
                return {
                    "success": True,
                    "scene_count": len(json_data),
                    "duration": duration,
                    "tokens_used": tokens_used,
                    "repaired": True,
                }
            except Exception as e2:
                print(f"❌ 修复后仍无法解析: {e2}")
                return {"success": False, "error": str(e), "repair_error": str(e2)}
        else:
            print(f"❌ 无法自动修复")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # 测试之前失败的大文件
    test_files = [
        "script_examples/scripts/script_08_yunyangyi_ep02.md",  # 之前耗时512秒，31个错误
        "script_examples/scripts/script_09_yunyangyi_ep08.md",  # 之前耗时328秒，32个错误
    ]

    results = []
    for test_file in test_files:
        file_path = project_root / test_file
        if file_path.exists():
            result = test_single_file(str(file_path))
            results.append({"file": test_file, **result})
            print("\n" + "=" * 70 + "\n")
        else:
            print(f"文件不存在: {test_file}")

    # 打印总结
    print("\n测试总结:")
    print("=" * 70)
    for r in results:
        status = "✅ 成功" if r.get("success") else "❌ 失败"
        print(f"{r['file']}: {status}")
        if r.get("success"):
            print(f"  场景数: {r.get('scene_count')}")
            print(f"  耗时: {r.get('duration', 0):.2f}秒")
            print(f"  Tokens: {r.get('tokens_used', 0)}")
            if r.get("has_thinking"):
                print(f"  包含思考过程: 是")
            if r.get("repaired"):
                print(f"  自动修复: 是")
        else:
            print(f"  错误: {r.get('error', 'Unknown')}")
        print()

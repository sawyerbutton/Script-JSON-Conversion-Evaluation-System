#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量测试所有剧本文件的评估脚本

该脚本会对 script_examples/scripts/ 目录下的所有剧本文件进行全流程评估测试，
并生成详细的测试报告。
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.file_handler import FileHandler
from src.utils.logger import get_logger, OperationLogger
from src.utils.performance import PerformanceProfiler
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig
from src.llm.deepseek_client import DeepSeekClient, DeepSeekConfig
from src.models.scene_models import validate_script_json

logger = get_logger(__name__)

# 文件大小阈值：超过此大小使用 reasoner 模型（字符数）
LARGE_FILE_THRESHOLD = 12000  # 约12K字符


def load_prompt_template(template_name: str) -> str:
    """加载prompt模板"""
    prompt_path = project_root / "prompts" / template_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def convert_script_to_json_internal(
    llm_client_chat: DeepSeekClient,
    llm_client_reasoner: DeepSeekClient,
    script_text: str,
    scene_type: str = "standard"
) -> list:
    """
    内部转换函数，将剧本文本转换为JSON

    智能选择模型：
    - 小文件(<12K字符): 使用 deepseek-chat (8K输出限制)
    - 大文件(>=12K字符): 使用 deepseek-reasoner (64K输出限制)

    Args:
        llm_client_chat: DeepSeek Chat客户端
        llm_client_reasoner: DeepSeek Reasoner客户端
        script_text: 剧本文本
        scene_type: 场景类型

    Returns:
        转换后的JSON数据（场景列表）
    """
    # 加载prompt模板
    template_name = (
        "scene1_extraction.txt" if scene_type == "standard" else "scene2_extraction.txt"
    )
    prompt_template = load_prompt_template(template_name)

    # 填充prompt
    prompt = prompt_template.replace("{script_text}", script_text)

    # 根据文件大小智能选择模型
    file_size = len(script_text)
    is_large_file = file_size >= LARGE_FILE_THRESHOLD

    if is_large_file:
        model_info = f"大文件 ({file_size} 字符) - 使用 deepseek-reasoner 模型 (32K输出)"
        logger.info(model_info)
        print(f"  ⚡ {model_info}")
        llm_client = llm_client_reasoner
        max_tokens = 32768  # reasoner模型默认32K输出
    else:
        model_info = f"普通文件 ({file_size} 字符) - 使用 deepseek-chat 模型 (8K输出)"
        logger.info(model_info)
        print(f"  💬 {model_info}")
        llm_client = llm_client_chat
        max_tokens = 8192  # chat模型最大8K输出

    # 调用LLM
    response = llm_client.complete(prompt=prompt, temperature=0.1, max_tokens=max_tokens)

    # 提取并清理JSON
    response_text = response["content"].strip()
    json_text = extract_and_clean_json(response_text, is_large_file)

    # 解析JSON
    try:
        json_data = json.loads(json_text)
        return json_data
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {e}")
        logger.debug(f"问题JSON片段: {json_text[:500]}...")

        # 尝试修复常见的JSON问题
        fixed_json = attempt_json_repair(json_text)
        if fixed_json:
            logger.info("JSON修复成功，重新解析")
            return json.loads(fixed_json)
        else:
            raise


def extract_and_clean_json(response_text: str, is_large_file: bool = False) -> str:
    """
    从LLM响应中提取并清理JSON

    处理多种情况：
    1. markdown代码块包裹
    2. reasoner模型的思考过程
    3. 额外的解释文字

    Args:
        response_text: LLM原始响应
        is_large_file: 是否为大文件（使用reasoner模型）

    Returns:
        清理后的JSON字符串
    """
    text = response_text.strip()

    # 1. 移除reasoner模型可能的思考标记
    # DeepSeek reasoner可能使用<think>...</think>或类似标记
    if is_large_file:
        # 移除<think>标签及其内容
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        # 移除可能的"让我思考"等文字
        text = re.sub(r'^.*?(让我|首先|分析|思考).*?[\n\r]', '', text, flags=re.MULTILINE)

    # 2. 提取markdown代码块中的JSON
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()

    # 3. 查找JSON数组的开始和结束
    # 寻找第一个 [ 和最后一个 ]
    first_bracket = text.find('[')
    last_bracket = text.rfind(']')

    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        text = text[first_bracket:last_bracket + 1]

    # 4. 清理常见问题
    # 移除BOM标记
    text = text.lstrip('\ufeff')
    # 移除前后的非JSON字符
    text = text.strip()

    return text


def attempt_json_repair(json_text: str) -> str:
    """
    尝试修复常见的JSON问题

    Args:
        json_text: 可能损坏的JSON字符串

    Returns:
        修复后的JSON字符串，如果无法修复则返回None
    """
    try:
        # 1. 修复未转义的引号
        # 这是一个简化版本，实际情况可能更复杂

        # 2. 修复尾部缺少的括号
        if json_text.count('[') > json_text.count(']'):
            # 补充缺失的 ]
            missing_brackets = json_text.count('[') - json_text.count(']')
            json_text += ']' * missing_brackets
            logger.info(f"补充了 {missing_brackets} 个缺失的 ]")

        # 3. 移除尾部的逗号
        json_text = re.sub(r',\s*([\]}])', r'\1', json_text)

        # 4. 尝试解析，如果成功就返回
        json.loads(json_text)
        return json_text

    except Exception as e:
        logger.error(f"JSON修复失败: {e}")
        return None


def run_batch_test(use_llm_judge=True):
    """
    批量测试所有剧本文件

    Args:
        use_llm_judge: 是否使用LLM语义评估（默认True，完整测试）
    """
    print("=" * 70)
    print("剧本批量测试系统")
    print("=" * 70)
    print()

    profiler = PerformanceProfiler("批量测试")
    profiler.start("初始化")

    # 初始化组件
    file_handler = FileHandler()
    config = EvaluationConfig(
        use_deepseek_judge=use_llm_judge,
        save_detailed_report=True
    )
    evaluator = ScriptEvaluator(config)

    # 初始化两个LLM客户端：chat模型和reasoner模型
    import os
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    chat_config = DeepSeekConfig(api_key=api_key, model="deepseek-chat")
    llm_client_chat = DeepSeekClient(config=chat_config, debug=True)

    reasoner_config = DeepSeekConfig(api_key=api_key, model="deepseek-reasoner")
    llm_client_reasoner = DeepSeekClient(config=reasoner_config, debug=True)

    logger.info(f"初始化完成 - Chat模型: {chat_config.model} (max_tokens={chat_config.max_tokens})")
    logger.info(f"初始化完成 - Reasoner模型: {reasoner_config.model} (max_tokens={reasoner_config.max_tokens})")

    # 获取所有剧本文件
    scripts_dir = project_root / "script_examples" / "scripts"
    script_files = sorted([f for f in scripts_dir.glob("*.md")])

    print(f"找到 {len(script_files)} 个剧本文件")
    print(f"使用LLM语义评估: {'是' if use_llm_judge else '否'}")
    print()

    profiler.checkpoint("开始测试")

    # 测试结果
    results = []
    success_count = 0
    fail_count = 0

    # 逐个测试
    for idx, script_file in enumerate(script_files, 1):
        print(f"\n[{idx}/{len(script_files)}] 测试文件: {script_file.name}")
        print("-" * 70)

        test_start_time = time.time()

        try:
            with OperationLogger(logger, f"测试 {script_file.name}"):
                # 读取剧本
                script_text = file_handler.read_text_file(str(script_file))
                print(f"  文件大小: {len(script_text)} 字符")

                # 转换为JSON
                print(f"  正在调用DeepSeek API转换剧本...")
                json_data = convert_script_to_json_internal(
                    llm_client_chat=llm_client_chat,
                    llm_client_reasoner=llm_client_reasoner,
                    script_text=script_text,
                    scene_type="standard"
                )

                if not json_data:
                    raise ValueError("转换失败：未能提取场景数据")

                scene_count = len(json_data)
                print(f"  ✅ 转换成功，包含 {scene_count} 个场景")

                # 运行评估
                print(f"  正在运行质量评估...")
                result = evaluator.evaluate_script(
                    source_text=script_text,
                    extracted_json=json_data,
                    scene_type="standard",
                    source_file=script_file.name
                )

                test_duration = time.time() - test_start_time

                # 记录结果
                test_result = {
                    "file": script_file.name,
                    "status": "成功",
                    "duration": round(test_duration, 2),
                    "scene_count": scene_count,
                    "overall_score": round(result.overall_score, 3),
                    "quality_level": result.quality_level,
                    "passed": "是" if result.passed else "否",
                    "scores": {
                        "structure": round(result.structure_score, 3),
                        "boundary": round(result.boundary_score, 3),
                        "character": round(result.character_score, 3),
                        "semantic": round(result.semantic_score, 3) if use_llm_judge else 0.0
                    }
                }

                results.append(test_result)
                success_count += 1

                # 显示结果
                print(f"\n  评估结果:")
                print(f"    质量级别: {result.quality_level}")
                print(f"    总分: {result.overall_score:.3f}")
                print(f"    通过: {'✅ 是' if result.passed else '❌ 否'}")
                print(f"    耗时: {test_duration:.2f}秒")

        except Exception as e:
            test_duration = time.time() - test_start_time
            logger.error(f"测试失败: {script_file.name}", exc_info=True)

            test_result = {
                "file": script_file.name,
                "status": "失败",
                "duration": round(test_duration, 2),
                "error": str(e)
            }

            results.append(test_result)
            fail_count += 1

            print(f"  ❌ 测试失败: {str(e)}")

    profiler.checkpoint("测试完成")

    # 生成报告
    print("\n" + "=" * 70)
    print("测试汇总")
    print("=" * 70)
    print(f"总文件数: {len(script_files)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"成功率: {(success_count/len(script_files)*100):.1f}%")
    print()

    # 统计信息
    if success_count > 0:
        successful_results = [r for r in results if r["status"] == "成功"]
        avg_score = sum(r["overall_score"] for r in successful_results) / len(successful_results)
        avg_duration = sum(r["duration"] for r in successful_results) / len(successful_results)

        print("成功测试统计:")
        print(f"  平均分数: {avg_score:.3f}")
        print(f"  平均耗时: {avg_duration:.2f}秒")

        # 质量级别分布
        quality_dist = {}
        for r in successful_results:
            level = r["quality_level"]
            quality_dist[level] = quality_dist.get(level, 0) + 1

        print(f"\n  质量级别分布:")
        for level, count in sorted(quality_dist.items()):
            print(f"    {level}: {count} 个")

    # 失败详情
    if fail_count > 0:
        print(f"\n失败详情:")
        failed_results = [r for r in results if r["status"] == "失败"]
        for r in failed_results:
            print(f"  - {r['file']}: {r.get('error', '未知错误')}")

    profiler.stop()
    print()
    profiler.print_report()

    # 保存详细报告
    report_file = project_root / "outputs" / "reports" / f"batch_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)

    report_data = {
        "test_time": datetime.now().isoformat(),
        "use_llm_judge": use_llm_judge,
        "total_files": len(script_files),
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": round(success_count/len(script_files)*100, 2),
        "results": results
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存到: {report_file}")
    print()
    print("=" * 70)
    print("批量测试完成!")
    print("=" * 70)

    return results


if __name__ == "__main__":
    # 检查命令行参数
    use_llm = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-llm-judge":
        use_llm = False

    run_batch_test(use_llm_judge=use_llm)

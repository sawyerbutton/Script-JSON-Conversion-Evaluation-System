#!/usr/bin/env python
"""
剧本评估系统 - 快速测试脚本
用于验证环境配置和基本功能
"""

import json
import sys
from pathlib import Path


def test_imports():
    """测试必需的包是否安装"""
    print("📦 检查依赖包...")
    
    required_packages = {
        "pydantic": "数据验证",
        "openai": "API客户端",
        "pandas": "数据处理",
        "numpy": "数值计算",
        "dotenv": "环境变量"
    }
    
    missing = []
    for package, desc in required_packages.items():
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f"  ✅ {package} ({desc})")
        except ImportError:
            print(f"  ❌ {package} ({desc}) - 未安装")
            missing.append(package)
    
    # DeepEval单独检查（可选）
    try:
        import deepeval
        print(f"  ✅ deepeval (评估框架)")
    except ImportError:
        print(f"  ⚠️  deepeval (评估框架) - 可选，未安装")
    
    if missing:
        print(f"\n请安装缺失的包: pip install {' '.join(missing)}")
        return False
    return True


def test_deepseek_connection():
    """测试DeepSeek API连接"""
    print("\n🔌 测试DeepSeek API连接...")
    
    try:
        from deepseek_client import DeepSeekClient
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        if not os.getenv("DEEPSEEK_API_KEY"):
            print("  ⚠️  未找到DEEPSEEK_API_KEY环境变量")
            print("  请在.env文件中设置: DEEPSEEK_API_KEY=your_key_here")
            return False
        
        client = DeepSeekClient()
        
        # 简单测试
        response = client.complete(
            prompt="回复OK",
            temperature=0,
            max_tokens=10
        )
        
        if response and "content" in response:
            print("  ✅ API连接成功")
            return True
        else:
            print("  ❌ API响应异常")
            return False
            
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
        return False


def test_data_validation():
    """测试数据模型验证"""
    print("\n📋 测试数据验证...")
    
    try:
        from scene_models import SceneInfo, validate_script_json
        
        # 测试有效数据
        valid_data = {
            "scene_id": "S01",
            "setting": "内景 咖啡馆 - 日",
            "characters": ["李雷", "韩梅梅"],
            "scene_mission": "展现关系危机",
            "key_events": ["争吵"]
        }
        
        result = validate_script_json(valid_data, "standard")
        if result["valid"]:
            print("  ✅ 有效数据验证通过")
        else:
            print("  ❌ 有效数据验证失败")
            return False
        
        # 测试无效数据
        invalid_data = {
            "scene_id": "场景1",  # 格式错误
            "setting": "某个地方",
            "characters": [],
            "scene_mission": "测试",
            "key_events": []  # 不能为空
        }
        
        result = validate_script_json(invalid_data, "standard")
        if not result["valid"]:
            print("  ✅ 无效数据正确识别")
        else:
            print("  ❌ 无效数据未能识别")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 验证失败: {e}")
        return False


def test_basic_evaluation():
    """测试基本评估功能"""
    print("\n🎯 测试评估功能...")
    
    try:
        from main_evaluator import ScriptEvaluator, EvaluationConfig
        
        # 配置（不使用API）
        config = EvaluationConfig(
            use_deepseek_judge=False,  # 不使用API
            run_consistency_check=False,
            save_detailed_report=False
        )
        
        evaluator = ScriptEvaluator(config)
        
        # 测试数据
        test_case = {
            "source_text": "内景 咖啡馆 - 日\n李雷和韩梅梅在交谈。",
            "extracted_json": [{
                "scene_id": "S01",
                "setting": "内景 咖啡馆 - 日",
                "characters": ["李雷", "韩梅梅"],
                "scene_mission": "展现两人对话",
                "key_events": ["交谈"],
                "info_change": [],
                "relation_change": [],
                "key_object": [],
                "setup_payoff": {"setup_for": [], "payoff_from": []}
            }],
            "scene_type": "standard",
            "source_file": "test.txt"
        }
        
        result = evaluator.evaluate_script(**test_case)
        
        print(f"  ✅ 评估完成")
        print(f"     总分: {result.overall_score:.3f}")
        print(f"     质量: {result.quality_level}")
        print(f"     通过: {'是' if result.passed else '否'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 评估失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_sample_evaluation():
    """运行完整的示例评估"""
    print("\n🚀 运行示例评估...")
    
    # 示例剧本
    sample_script = """
内景 咖啡馆 - 日

李雷坐在角落，看着窗外。韩梅梅推门进入。

韩梅梅：你等很久了吗？

李雷：（勉强微笑）没有，刚到。

两人相对而坐，气氛有些尴尬。

韩梅梅：我们需要谈谈。

李雷：我知道。关于昨晚的事...

韩梅梅打断他，眼中含泪。

韩梅梅：不只是昨晚。是这三个月来的一切。
"""
    
    # 示例JSON（模拟提取结果）
    sample_json = [
        {
            "scene_id": "S01",
            "setting": "内景 咖啡馆 - 日",
            "characters": ["李雷", "韩梅梅"],
            "scene_mission": "展现两人关系的紧张和需要解决的问题",
            "key_events": [
                "韩梅梅到达咖啡馆",
                "两人开始严肃对话",
                "韩梅梅提及三个月来的问题"
            ],
            "info_change": [
                {
                    "character": "观众",
                    "learned": "两人关系存在长期问题"
                },
                {
                    "character": "李雷",
                    "learned": "问题不只是昨晚的事"
                }
            ],
            "relation_change": [
                {
                    "chars": ["李雷", "韩梅梅"],
                    "from": "表面平静的恋人",
                    "to": "准备摊牌的恋人"
                }
            ],
            "key_object": [],
            "setup_payoff": {
                "setup_for": ["S02", "S03"],
                "payoff_from": []
            }
        }
    ]
    
    print("\n📝 剧本内容（前100字）:")
    print(sample_script[:100] + "...")
    
    print("\n📊 提取的JSON（简化）:")
    print(f"  场景ID: {sample_json[0]['scene_id']}")
    print(f"  角色: {', '.join(sample_json[0]['characters'])}")
    print(f"  场景任务: {sample_json[0]['scene_mission']}")
    
    # 运行评估
    try:
        from main_evaluator import ScriptEvaluator, EvaluationConfig
        
        config = EvaluationConfig(
            use_deepseek_judge=False,  # 演示模式不使用API
            run_consistency_check=False,
            save_detailed_report=False
        )
        
        evaluator = ScriptEvaluator(config)
        
        result = evaluator.evaluate_script(
            source_text=sample_script,
            extracted_json=sample_json,
            scene_type="standard",
            source_file="sample.txt"
        )
        
        print("\n📈 评估结果:")
        print(f"  总分: {result.overall_score:.3f}/1.000")
        print(f"  质量级别: {result.quality_level}")
        print(f"  评估通过: {'✅ 是' if result.passed else '❌ 否'}")
        
        print("\n  各维度得分:")
        print(f"    - 结构验证: {result.structure_score:.3f}")
        print(f"    - 场景边界: {result.boundary_score:.3f}")
        print(f"    - 角色提取: {result.character_score:.3f}")
        print(f"    - 语义准确: {result.semantic_score:.3f}")
        
        if result.recommendations:
            print("\n  改进建议:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"    {i}. {rec}")
        
        print("\n✨ 示例评估完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 示例评估失败: {e}")
        return False


def main():
    """主测试流程"""
    print("=" * 50)
    print("剧本评估系统 - 环境测试")
    print("=" * 50)
    
    # 运行测试
    tests = [
        ("依赖包检查", test_imports),
        ("数据验证", test_data_validation),
        ("基本评估", test_basic_evaluation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name}测试异常: {e}")
            results.append((name, False))
    
    # API测试（可选）
    print("\n" + "=" * 50)
    choice = input("是否测试DeepSeek API连接？(y/n): ").lower()
    if choice == 'y':
        api_success = test_deepseek_connection()
        results.append(("API连接", api_success))
    
    # 运行示例
    print("\n" + "=" * 50)
    choice = input("是否运行完整示例评估？(y/n): ").lower()
    if choice == 'y':
        run_sample_evaluation()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print("-" * 30)
    
    all_passed = True
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")
        if not success:
            all_passed = False
    
    print("-" * 30)
    
    if all_passed:
        print("\n🎉 所有测试通过！系统准备就绪。")
        print("\n下一步:")
        print("1. 准备您的剧本数据")
        print("2. 调用prompt获取JSON")
        print("3. 使用评估系统验证质量")
    else:
        print("\n⚠️  部分测试失败，请检查相应配置。")
        print("\n故障排除:")
        print("1. 确认所有依赖包已安装")
        print("2. 检查文件路径是否正确")
        print("3. 如使用API，确认密钥配置正确")
    
    print("\n📚 查看 quick_start_guide.md 获取详细指南")
    print("=" * 50)


if __name__ == "__main__":
    main()

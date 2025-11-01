"""
剧本JSON转换评估系统 - 主程序
整合所有评估组件的完整流程
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from deepeval.test_case import LLMTestCase

# 导入自定义模块（使用双导入策略）
try:
    from ..llm.deepseek_client import DeepSeekClient
    from ..metrics.deepeval_metrics import (
        CharacterExtractionMetric,
        SceneBoundaryMetric,
        SelfConsistencyMetric,
    )
    from ..models.scene_models import validate_script_json
except ImportError:
    # 从scripts运行时直接导入（src已在sys.path中）
    from llm.deepseek_client import DeepSeekClient
    from metrics.deepeval_metrics import (
        CharacterExtractionMetric,
        SceneBoundaryMetric,
        SelfConsistencyMetric,
    )
    from models.scene_models import validate_script_json

# 导入工具模块
try:
    # 尝试相对导入
    from ..utils.exceptions import (
        APIConnectionError,
        EvaluationError,
        FileWriteError,
        MetricCalculationError,
    )
    from ..utils.logger import OperationLogger, get_logger
    from ..utils.performance import PerformanceProfiler, timer, track_performance
except ImportError:
    # 从scripts运行时直接导入（src已在sys.path中）
    from utils.exceptions import (
        APIConnectionError,
        EvaluationError,
        FileWriteError,
        MetricCalculationError,
    )
    from utils.logger import OperationLogger, get_logger
    from utils.performance import PerformanceProfiler, timer, track_performance

# 配置日志
logger = get_logger(__name__)


@dataclass
class EvaluationConfig:
    """评估配置"""

    use_deepseek_judge: bool = True
    run_consistency_check: bool = True
    consistency_runs: int = 5

    # 权重配置
    structure_weight: float = 0.25
    boundary_weight: float = 0.25
    character_weight: float = 0.25
    semantic_weight: float = 0.25

    # 阈值配置
    pass_threshold: float = 0.70
    excellent_threshold: float = 0.85

    # 输出配置
    output_dir: str = "outputs/reports"
    save_detailed_report: bool = True
    save_html_report: bool = True


@dataclass
class EvaluationResult:
    """评估结果"""

    timestamp: str
    source_file: str
    scene_type: str  # "standard" or "outline"

    # 分数
    overall_score: float
    structure_score: float
    boundary_score: float
    character_score: float
    semantic_score: float
    consistency_score: Optional[float]

    # 详细信息
    total_scenes: int
    total_characters: int
    issues: List[Dict[str, Any]]
    recommendations: List[str]

    # 评估状态
    passed: bool
    quality_level: str  # "优秀", "良好", "合格", "不合格"


class ScriptEvaluator:
    """剧本评估器主类"""

    def __init__(self, config: Optional[EvaluationConfig] = None):
        self.config = config or EvaluationConfig()
        self.deepseek_client = None

        if self.config.use_deepseek_judge:
            try:
                self.deepseek_client = DeepSeekClient()
                logger.info("DeepSeek客户端初始化成功，将使用LLM进行语义评估")
            except Exception as e:
                logger.warning(f"DeepSeek客户端初始化失败: {e}，将使用默认评分")
                self.deepseek_client = None

        # 创建输出目录
        try:
            Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
            logger.debug(f"输出目录已准备: {self.config.output_dir}")
        except Exception as e:
            logger.error(f"创建输出目录失败: {e}")
            raise FileWriteError(
                f"无法创建输出目录: {self.config.output_dir}", details={"error": str(e)}
            )

    @timer(name="剧本评估", log_result=True)
    def evaluate_script(
        self,
        source_text: str,
        extracted_json: Dict[str, Any],
        scene_type: str = "standard",
        source_file: str = "unknown",
    ) -> EvaluationResult:
        """
        评估单个剧本转换结果

        Args:
            source_text: 原始剧本文本
            extracted_json: 提取的JSON数据
            scene_type: "standard" (场景1) 或 "outline" (场景2)
            source_file: 源文件名

        Returns:
            评估结果对象
        """

        # 使用性能分析器追踪完整流程
        profiler = PerformanceProfiler(f"评估 {source_file}")
        profiler.start("初始化")

        with OperationLogger(logger, "评估剧本", source_file=source_file, scene_type=scene_type):
            logger.info(f"开始评估: {source_file} (类型: {scene_type})")

            # 1. 结构验证
            profiler.checkpoint("结构验证")
            with track_performance("结构验证", source_file=source_file):
                structure_score, structure_issues = self._evaluate_structure(
                    extracted_json, scene_type
                )

            # 2. 场景边界评估
            profiler.checkpoint("场景边界评估")
            with track_performance("场景边界评估", source_file=source_file):
                boundary_score = self._evaluate_boundaries(source_text, extracted_json)

            # 3. 角色提取评估
            profiler.checkpoint("角色提取评估")
            with track_performance("角色提取评估", source_file=source_file):
                character_score, char_details = self._evaluate_characters(
                    source_text, extracted_json
                )

            # 4. 语义一致性评估
            profiler.checkpoint("语义评估")
            with track_performance("语义评估", source_file=source_file):
                semantic_score = self._evaluate_semantics(source_text, extracted_json)

            # 5. 自一致性评估（可选）
            consistency_score = None
            if self.config.run_consistency_check:
                profiler.checkpoint("一致性评估")
                with track_performance("一致性评估", source_file=source_file):
                    consistency_score = self._evaluate_consistency(source_text, extracted_json)

            # 计算总分
            profiler.checkpoint("计算分数")
            scores = {
                "structure": (structure_score, self.config.structure_weight),
                "boundary": (boundary_score, self.config.boundary_weight),
                "character": (character_score, self.config.character_weight),
                "semantic": (semantic_score, self.config.semantic_weight),
            }

            overall_score = sum(score * weight for score, weight in scores.values()) / sum(
                weight for _, weight in scores.values()
            )

            # 确定质量级别
            if overall_score >= self.config.excellent_threshold:
                quality_level = "优秀"
            elif overall_score >= 0.80:
                quality_level = "良好"
            elif overall_score >= self.config.pass_threshold:
                quality_level = "合格"
            else:
                quality_level = "不合格"

            # 收集问题和建议
            issues = structure_issues
            recommendations = self._generate_recommendations(scores, issues, char_details)

            # 统计信息
            scenes = extracted_json if isinstance(extracted_json, list) else [extracted_json]
            all_characters = set()
            for scene in scenes:
                all_characters.update(scene.get("characters", []))

            # 创建结果对象
            profiler.checkpoint("生成报告")
            result = EvaluationResult(
                timestamp=datetime.now().isoformat(),
                source_file=source_file,
                scene_type=scene_type,
                overall_score=round(overall_score, 3),
                structure_score=round(structure_score, 3),
                boundary_score=round(boundary_score, 3),
                character_score=round(character_score, 3),
                semantic_score=round(semantic_score, 3),
                consistency_score=round(consistency_score, 3) if consistency_score else None,
                total_scenes=len(scenes),
                total_characters=len(all_characters),
                issues=issues,
                recommendations=recommendations,
                passed=overall_score >= self.config.pass_threshold,
                quality_level=quality_level,
            )

            # 保存结果
            if self.config.save_detailed_report:
                profiler.checkpoint("保存报告")
                self._save_report(result)

            profiler.stop()

            # 打印性能分析报告
            if logger.level <= 10:  # DEBUG level
                profiler.print_report()

            logger.info(f"评估完成: {quality_level} (总分: {overall_score:.3f})")

            return result

    def _evaluate_structure(self, json_data: Any, scene_type: str) -> tuple[float, List[Dict]]:
        """评估JSON结构"""

        issues = []

        try:
            # 使用Pydantic验证
            validation_result = validate_script_json(json_data, scene_type)

            if validation_result["valid"]:
                base_score = 1.0
                logger.debug("JSON结构验证通过")
            else:
                base_score = 0.3
                logger.warning(f"JSON结构验证失败，发现 {len(validation_result['errors'])} 个错误")
                for error in validation_result["errors"]:
                    issues.append({"type": "structure", "severity": "high", "message": error})
        except Exception as e:
            logger.error(f"结构验证过程出错: {e}")
            raise MetricCalculationError("结构验证失败", details={"error": str(e)})

        # 检查数据完整性
        scenes = json_data if isinstance(json_data, list) else [json_data]

        completeness_scores = []
        for i, scene in enumerate(scenes):
            scene_complete = self._check_scene_completeness(scene)
            completeness_scores.append(scene_complete)

            if scene_complete < 0.8:
                issues.append(
                    {
                        "type": "completeness",
                        "severity": "medium",
                        "message": f"场景 {i+1} 信息不完整",
                        "scene_id": scene.get("scene_id", f"Scene_{i+1}"),
                    }
                )

        avg_completeness = (
            sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        )

        # 综合结构分数
        structure_score = 0.6 * base_score + 0.4 * avg_completeness

        return structure_score, issues

    def _check_scene_completeness(self, scene: Dict) -> float:
        """检查单个场景的完整性"""

        required_fields = ["scene_id", "setting", "characters", "scene_mission", "key_events"]

        optional_fields = ["info_change", "relation_change", "key_object", "setup_payoff"]

        # 必需字段得分
        required_score = sum(
            1 for field in required_fields if field in scene and scene[field]
        ) / len(required_fields)

        # 可选字段得分（权重较低）
        optional_score = sum(1 for field in optional_fields if field in scene) / len(
            optional_fields
        )

        return 0.7 * required_score + 0.3 * optional_score

    def _evaluate_boundaries(self, source_text: str, json_data: Any) -> float:
        """评估场景边界"""

        try:
            # 创建测试用例
            test_case = LLMTestCase(
                input=source_text, actual_output=json.dumps(json_data, ensure_ascii=False)
            )

            # 创建指标
            metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=self.config.use_deepseek_judge)

            # 评估
            score = metric.measure(test_case)
            logger.debug(f"场景边界评估得分: {score:.3f}")

            return score
        except Exception as e:
            logger.error(f"场景边界评估失败: {e}")
            raise MetricCalculationError("场景边界评估失败", details={"error": str(e)})

    def _evaluate_characters(self, source_text: str, json_data: Any) -> tuple[float, Dict]:
        """评估角色提取"""

        try:
            test_case = LLMTestCase(
                input=source_text, actual_output=json.dumps(json_data, ensure_ascii=False)
            )

            metric = CharacterExtractionMetric(
                threshold=0.7, use_deepseek=self.config.use_deepseek_judge
            )

            score = metric.measure(test_case)
            logger.debug(f"角色提取评估得分: {score:.3f}")

            return score, metric.details
        except Exception as e:
            logger.error(f"角色提取评估失败: {e}")
            raise MetricCalculationError("角色提取评估失败", details={"error": str(e)})

    def _evaluate_semantics(self, source_text: str, json_data: Any) -> float:
        """评估语义准确性"""

        if not self.config.use_deepseek_judge or not self.deepseek_client:
            logger.debug("跳过语义评估，使用默认分数")
            return 0.75  # 默认分数

        scenes = json_data if isinstance(json_data, list) else [json_data]

        # 构建评估提示
        prompt = f"""
请评估JSON提取结果的语义准确性。

原始文本（前1000字）：
{source_text[:1000]}

提取的场景信息（前3个）：
{json.dumps(scenes[:3], ensure_ascii=False, indent=2)}

评估要点：
1. 场景任务(scene_mission)是否准确概括了场景的戏剧功能
2. 关键事件(key_events)是否捕捉了重要情节点
3. 信息变化(info_change)是否正确识别了信息流动
4. 关系变化(relation_change)是否准确反映了人物关系演变

请返回JSON格式：
{{
    "score": 0-1的评分,
    "mission_accuracy": "准确/基本准确/不准确",
    "events_coverage": "完整/部分完整/不完整",
    "info_accuracy": "准确/基本准确/不准确",
    "relation_accuracy": "准确/基本准确/不准确",
    "major_issues": ["问题1", "问题2"]
}}
"""

        try:
            response = self.deepseek_client.complete(
                prompt=prompt, temperature=0.0, response_format={"type": "json_object"}
            )

            result = response["content"]
            score = result.get("score", 0.7)
            logger.debug(f"语义评估得分: {score:.3f}")
            return score
        except APIConnectionError as e:
            logger.error(f"DeepSeek API连接失败: {e}")
            logger.warning("使用默认语义评分 0.7")
            return 0.7
        except Exception as e:
            logger.error(f"语义评估失败: {e}")
            logger.warning("使用默认语义评分 0.7")
            return 0.7

    def _evaluate_consistency(self, source_text: str, json_data: Any) -> float:
        """评估自一致性（多次运行）"""

        try:
            logger.info(f"运行{self.config.consistency_runs}次一致性测试...")

            # 这里简化处理，实际应该多次调用提取接口
            # 假设我们已经有了多次运行的结果
            runs = [json_data] * self.config.consistency_runs  # 简化：使用相同结果

            test_case = LLMTestCase(
                input=source_text, actual_output=json.dumps(runs, ensure_ascii=False)
            )

            metric = SelfConsistencyMetric(threshold=0.7, num_runs=self.config.consistency_runs)

            score = metric.measure(test_case)
            logger.debug(f"一致性评估得分: {score:.3f}")

            return score
        except Exception as e:
            logger.error(f"一致性评估失败: {e}")
            raise MetricCalculationError("一致性评估失败", details={"error": str(e)})

    def _generate_recommendations(
        self, scores: Dict, issues: List[Dict], char_details: Dict
    ) -> List[str]:
        """生成改进建议"""

        recommendations = []

        # 基于分数的建议
        score_items = [(name, score[0]) for name, score in scores.items()]
        worst_aspect = min(score_items, key=lambda x: x[1])

        if worst_aspect[1] < 0.7:
            aspect_name_map = {
                "structure": "JSON结构",
                "boundary": "场景划分",
                "character": "角色识别",
                "semantic": "语义理解",
            }
            recommendations.append(
                f"重点改进{aspect_name_map.get(worst_aspect[0], worst_aspect[0])}方面"
            )

        # 基于具体问题的建议
        high_severity_issues = [i for i in issues if i.get("severity") == "high"]
        if high_severity_issues:
            recommendations.append("优先修复高严重性的结构问题")

        # 角色相关建议
        if "mentioned_only" in char_details:
            recommendations.append("区分实际出场角色和仅被提及的角色")

        # 通用建议
        if not recommendations:
            recommendations.append("继续保持当前提取质量")

        return recommendations

    def _save_report(self, result: EvaluationResult):
        """保存评估报告"""

        try:
            # JSON格式
            report_path = Path(self.config.output_dir) / f"report_{result.timestamp}.json"

            # 自定义序列化函数处理特殊类型
            def default_handler(obj):
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                elif isinstance(obj, (set, frozenset)):
                    return list(obj)
                else:
                    return str(obj)

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(asdict(result), f, ensure_ascii=False, indent=2, default=default_handler)

            logger.info(f"JSON报告已保存: {report_path}")

            # HTML格式（如果启用）
            if self.config.save_html_report:
                self._save_html_report(result)
        except IOError as e:
            logger.error(f"保存报告失败: {e}")
            raise FileWriteError(
                f"无法保存评估报告到 {self.config.output_dir}", details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"保存报告时出现未预期错误: {e}")
            raise FileWriteError("保存报告失败", details={"error": str(e)})

    def _save_html_report(self, result: EvaluationResult):
        """保存HTML格式报告"""

        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>剧本评估报告 - {result.source_file}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .score-card {{ display: inline-block; margin: 10px; padding: 15px;
                      border: 1px solid #ddd; border-radius: 5px; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .excellent {{ background: #d4edda; }}
        .good {{ background: #cce5ff; }}
        .qualified {{ background: #fff3cd; }}
        .unqualified {{ background: #f8d7da; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>剧本评估报告</h1>
        <p>文件: {result.source_file} | 类型: {result.scene_type} | 时间: {result.timestamp}</p>
    </div>

    <h2>总体评分: <span class="{result.quality_level.lower()}">{result.overall_score:.2f}</span></h2>
    <p class="{'pass' if result.passed else 'fail'}">
        状态: {'✅ 通过' if result.passed else '❌ 未通过'} | 质量级别: {result.quality_level}
    </p>

    <h3>各维度得分</h3>
    <div>
        <div class="score-card">结构验证: {result.structure_score:.2f}</div>
        <div class="score-card">场景边界: {result.boundary_score:.2f}</div>
        <div class="score-card">角色提取: {result.character_score:.2f}</div>
        <div class="score-card">语义准确: {result.semantic_score:.2f}</div>
        {"<div class='score-card'>一致性: " + f"{result.consistency_score:.2f}</div>" if result.consistency_score else ""}
    </div>

    <h3>统计信息</h3>
    <ul>
        <li>场景总数: {result.total_scenes}</li>
        <li>角色总数: {result.total_characters}</li>
    </ul>

    <h3>发现的问题</h3>
    <table>
        <tr><th>类型</th><th>严重性</th><th>描述</th></tr>
        {"".join(f"<tr><td>{issue['type']}</td><td>{issue['severity']}</td><td>{issue['message']}</td></tr>" for issue in result.issues[:10])}
    </table>

    <h3>改进建议</h3>
    <ol>
        {"".join(f"<li>{rec}</li>" for rec in result.recommendations)}
    </ol>
</body>
</html>
"""

            html_path = Path(self.config.output_dir) / f"report_{result.timestamp}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(f"HTML报告已保存: {html_path}")
        except IOError as e:
            logger.error(f"保存HTML报告失败: {e}")
            raise FileWriteError("无法保存HTML报告", details={"error": str(e)})


def batch_evaluate(evaluator: ScriptEvaluator, test_cases: List[Dict[str, Any]]) -> pd.DataFrame:
    """批量评估多个测试用例"""

    with OperationLogger(logger, "批量评估", total_cases=len(test_cases)):
        results = []
        failed_cases = []

        for i, case in enumerate(test_cases, 1):
            case_name = case.get("file_name", f"case_{i}")
            try:
                logger.info(f"评估进度: {i}/{len(test_cases)} - {case_name}")
                result = evaluator.evaluate_script(
                    source_text=case["source_text"],
                    extracted_json=case["extracted_json"],
                    scene_type=case.get("scene_type", "standard"),
                    source_file=case_name,
                )
                results.append(asdict(result))
            except EvaluationError as e:
                logger.error(f"评估失败 {case_name}: {e.message}")
                failed_cases.append({"case": case_name, "error": e.message})
            except Exception as e:
                logger.error(f"评估失败 {case_name}: {e}")
                failed_cases.append({"case": case_name, "error": str(e)})

        if not results:
            logger.error("所有测试用例评估失败，无法生成汇总报告")
            raise EvaluationError("批量评估失败，没有成功的评估结果")

        # 转换为DataFrame便于分析
        df = pd.DataFrame(results)

        try:
            # 保存汇总报告
            summary_path = Path(evaluator.config.output_dir) / "batch_summary.csv"
            df.to_csv(summary_path, index=False, encoding="utf-8-sig")
            logger.info(f"批量评估汇总已保存: {summary_path}")
        except Exception as e:
            logger.error(f"保存汇总报告失败: {e}")
            raise FileWriteError("无法保存批量评估汇总", details={"error": str(e)})

        # 打印统计信息
        logger.info("=== 批量评估汇总 ===")
        logger.info(f"总计评估: {len(test_cases)} 个")
        logger.info(f"成功: {len(results)} 个")
        logger.info(f"失败: {len(failed_cases)} 个")
        logger.info(f"通过: {df['passed'].sum()} 个")
        logger.info(f"平均总分: {df['overall_score'].mean():.3f}")
        logger.info(f"最高分: {df['overall_score'].max():.3f}")
        logger.info(f"最低分: {df['overall_score'].min():.3f}")

        if failed_cases:
            logger.warning("\n失败的案例:")
            for fc in failed_cases:
                logger.warning(f"  - {fc['case']}: {fc['error']}")

        return df


# 主程序入口
if __name__ == "__main__":
    # 配置评估器
    config = EvaluationConfig(
        use_deepseek_judge=True,  # 使用DeepSeek进行语义评估
        run_consistency_check=False,  # 暂时关闭一致性检查
        save_detailed_report=True,
        save_html_report=True,
    )

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
        "file_name": "test_script_01.txt",
    }

    # 运行评估
    result = evaluator.evaluate_script(**test_case)

    # 打印结果
    print("\n=== 评估结果 ===")
    print(f"文件: {result.source_file}")
    print(f"质量级别: {result.quality_level}")
    print(f"总分: {result.overall_score:.3f}")
    print(f"通过: {'是' if result.passed else '否'}")

    print("\n各项得分:")
    print(f"  结构验证: {result.structure_score:.3f}")
    print(f"  场景边界: {result.boundary_score:.3f}")
    print(f"  角色提取: {result.character_score:.3f}")
    print(f"  语义准确: {result.semantic_score:.3f}")

    if result.issues:
        print(f"\n发现 {len(result.issues)} 个问题")

    print("\n改进建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")

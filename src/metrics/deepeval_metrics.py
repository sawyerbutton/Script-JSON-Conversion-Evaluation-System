"""
DeepEval自定义评估指标
用于剧本JSON转换质量评估
"""

import json
from collections import Counter
from typing import Dict, List, Optional

import numpy as np
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

try:
    from ..llm.deepseek_client import DeepSeekClient
except ImportError:
    # 从scripts运行时直接导入（src已在sys.path中）
    from llm.deepseek_client import DeepSeekClient


class SceneBoundaryMetric(BaseMetric):
    """场景边界评估指标"""

    def __init__(
        self,
        threshold: float = 0.75,
        tolerance: int = 2,  # off-by-n 容差
        use_deepseek: bool = True,
    ):
        self.threshold = threshold
        self.tolerance = tolerance
        self.use_deepseek = use_deepseek

        if use_deepseek:
            self.llm_client = DeepSeekClient()

        # 指标结果
        self.score = 0.0
        self.success = False
        self.reason = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """同步评估方法"""

        # 提取输入
        source_text = test_case.input
        extracted_json = json.loads(test_case.actual_output)

        # 1. 结构评估
        structural_score = self._evaluate_structure(extracted_json)

        # 2. 语义评估（如果启用）
        semantic_score = 1.0
        if self.use_deepseek:
            semantic_score = self._evaluate_semantic(source_text, extracted_json)

        # 3. 综合评分
        self.score = 0.4 * structural_score + 0.6 * semantic_score
        self.success = self.score >= self.threshold

        # 生成评估理由
        self._generate_reason(structural_score, semantic_score)

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """异步评估方法"""
        # 简单包装同步方法
        return self.measure(test_case)

    def _evaluate_structure(self, json_data: List[Dict]) -> float:
        """评估结构合理性"""

        if not json_data:
            return 0.0

        scores = []

        # 1. 场景ID连续性
        scene_ids = [scene.get("scene_id", "") for scene in json_data]
        continuity_score = self._check_id_continuity(scene_ids)
        scores.append(continuity_score)

        # 2. 场景设置完整性
        settings_score = sum(
            1 for scene in json_data if self._is_valid_setting(scene.get("setting", ""))
        ) / len(json_data)
        scores.append(settings_score)

        # 3. 必要字段存在性
        required_fields = ["scene_id", "setting", "characters", "scene_mission", "key_events"]
        field_score = sum(
            all(field in scene for field in required_fields) for scene in json_data
        ) / len(json_data)
        scores.append(field_score)

        return np.mean(scores)

    def _evaluate_semantic(self, source_text: str, json_data: List[Dict]) -> float:
        """使用LLM评估语义正确性"""

        prompt = f"""
请评估以下场景划分的合理性。

原始剧本文本：
{source_text[:2000]}  # 限制长度

提取的场景列表（共{len(json_data)}个场景）：
{json.dumps(json_data[:5], ensure_ascii=False, indent=2)}  # 只显示前5个

评估标准：
1. 场景边界是否在合理的转换点（时间、地点、角色组变化）
2. 场景划分是否过细或过粗
3. 是否遗漏了重要的场景转换
4. 场景顺序是否符合叙事逻辑

请以JSON格式返回：
{{
    "score": 0-1的分数,
    "boundary_accuracy": "准确/基本准确/不准确",
    "granularity": "合适/过细/过粗",
    "completeness": "完整/有遗漏/有多余",
    "issues": ["具体问题1", "具体问题2"],
    "reasoning": "详细评估理由"
}}
"""

        response = self.llm_client.complete(
            prompt=prompt, temperature=0.0, response_format={"type": "json_object"}
        )

        try:
            result = response["content"]
            # 如果content是字符串，先解析
            if isinstance(result, str):
                result = json.loads(result)
            return result.get("score", 0.5)
        except (KeyError, TypeError, ValueError, AttributeError, json.JSONDecodeError):
            return 0.5  # 默认中等分数

    def _check_id_continuity(self, scene_ids: List[str]) -> float:
        """检查场景ID连续性"""

        try:
            # 提取数字部分
            numbers = []
            for sid in scene_ids:
                # 支持 S01 和 E01S01 格式
                import re

                match = re.search(r"S(\d+)$", sid)
                if match:
                    numbers.append(int(match.group(1)))

            if not numbers:
                return 0.0

            # 检查连续性
            expected = list(range(min(numbers), max(numbers) + 1))
            if numbers == expected:
                return 1.0

            # 计算缺失比例
            missing = len(expected) - len(set(numbers) & set(expected))
            return max(0, 1 - missing / len(expected))

        except (ValueError, TypeError, AttributeError):
            return 0.5

    def _is_valid_setting(self, setting: str) -> bool:
        """检查场景设置格式"""

        if not setting:
            return False

        # 检查是否包含位置类型
        has_location = any(x in setting for x in ["内", "外", "INT", "EXT"])

        return has_location

    def _generate_reason(self, structural_score: float, semantic_score: float):
        """生成评估理由"""

        reasons = []

        if structural_score < 0.6:
            reasons.append(f"结构评分较低({structural_score:.2f})，可能存在格式问题")
        elif structural_score > 0.8:
            reasons.append(f"结构良好({structural_score:.2f})")

        if self.use_deepseek:
            if semantic_score < 0.6:
                reasons.append(f"语义评分较低({semantic_score:.2f})，场景划分可能不合理")
            elif semantic_score > 0.8:
                reasons.append(f"语义合理({semantic_score:.2f})")

        self.reason = "；".join(reasons) if reasons else "评估完成"

    @property
    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "场景边界评估"


class CharacterExtractionMetric(BaseMetric):
    """角色提取评估指标"""

    def __init__(self, threshold: float = 0.80, use_deepseek: bool = True):
        self.threshold = threshold
        self.use_deepseek = use_deepseek

        if use_deepseek:
            self.llm_client = DeepSeekClient()

        self.score = 0.0
        self.success = False
        self.reason = ""
        self.details = {}

    def measure(self, test_case: LLMTestCase) -> float:
        """评估角色提取质量"""

        source_text = test_case.input
        extracted_json = json.loads(test_case.actual_output)

        # 收集所有角色
        all_characters = self._collect_characters(extracted_json)
        scene_characters = self._collect_scene_characters(extracted_json)

        # 1. 角色一致性评分
        consistency_score = self._evaluate_consistency(all_characters, scene_characters)

        # 2. 角色重要性分析
        importance_score = self._evaluate_importance(all_characters, extracted_json)

        # 3. LLM验证（如果启用）
        validation_score = 1.0
        if self.use_deepseek:
            validation_score = self._validate_with_llm(source_text, all_characters)

        # 综合评分
        self.score = 0.3 * consistency_score + 0.3 * importance_score + 0.4 * validation_score

        self.success = self.score >= self.threshold
        self._generate_character_reason()

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def _collect_characters(self, json_data: List[Dict]) -> List[str]:
        """收集所有出现的角色"""

        characters = set()

        for scene in json_data:
            # 场景中的角色
            characters.update(scene.get("characters", []))

            # 信息变化中的角色
            for info in scene.get("info_change", []):
                if info.get("character") != "观众":
                    characters.add(info.get("character", ""))

            # 关系变化中的角色
            for relation in scene.get("relation_change", []):
                characters.update(relation.get("chars", []))

        return list(characters - {""})

    def _collect_scene_characters(self, json_data: List[Dict]) -> Dict[str, List[int]]:
        """收集每个角色出现的场景"""

        character_scenes = {}

        for i, scene in enumerate(json_data):
            for char in scene.get("characters", []):
                if char not in character_scenes:
                    character_scenes[char] = []
                character_scenes[char].append(i)

        return character_scenes

    def _evaluate_consistency(
        self, all_characters: List[str], scene_characters: Dict[str, List[int]]
    ) -> float:
        """评估角色一致性"""

        if not all_characters:
            return 0.0

        # 检查是否所有角色都至少在一个场景中出现
        appearing_chars = set(scene_characters.keys())
        mentioned_only = set(all_characters) - appearing_chars

        if mentioned_only:
            self.details["mentioned_only"] = list(mentioned_only)

        # 一致性分数
        consistency = len(appearing_chars) / len(all_characters) if all_characters else 0

        return consistency

    def _evaluate_importance(self, characters: List[str], json_data: List[Dict]) -> float:
        """评估角色重要性分布"""

        if not characters or not json_data:
            return 0.0

        # 统计每个角色的出现次数
        char_frequency = Counter()

        for scene in json_data:
            for char in scene.get("characters", []):
                char_frequency[char] += 1

        if not char_frequency:
            return 0.0

        # 计算分布熵（理想情况下应该有主次分明）
        total = sum(char_frequency.values())
        probs = [count / total for count in char_frequency.values()]

        # 熵越低说明有主角突出，越高说明分布均匀
        entropy = -sum(p * np.log(p) if p > 0 else 0 for p in probs)
        max_entropy = np.log(len(char_frequency))

        # 我们希望有适度的不均匀（有主次）
        # 熵在最大值的30%-70%之间最好
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy
            if 0.3 <= normalized_entropy <= 0.7:
                score = 1.0
            elif normalized_entropy < 0.3:
                score = normalized_entropy / 0.3
            else:
                score = (1 - normalized_entropy) / 0.3
        else:
            score = 1.0

        # 记录主要角色
        self.details["main_characters"] = [char for char, count in char_frequency.most_common(3)]

        return score

    def _validate_with_llm(self, source_text: str, characters: List[str]) -> float:
        """使用LLM验证角色提取"""

        prompt = f"""
请验证以下角色提取的准确性和完整性。

原始文本片段：
{source_text[:1500]}

提取的角色列表：
{json.dumps(characters, ensure_ascii=False)}

请评估：
1. 是否遗漏了重要角色？
2. 是否包含了不存在的角色？
3. 角色名称是否准确？
4. 是否正确区分了实际出场和仅被提及的角色？

返回JSON格式：
{{
    "score": 0-1的分数,
    "missing_characters": ["遗漏的角色"],
    "invalid_characters": ["不存在的角色"],
    "accuracy": "准确/基本准确/不准确",
    "reasoning": "评估理由"
}}
"""

        response = self.llm_client.complete(
            prompt=prompt, temperature=0.0, response_format={"type": "json_object"}
        )

        try:
            result = response["content"]
            # 如果content是字符串，先解析
            if isinstance(result, str):
                result = json.loads(result)
            return result.get("score", 0.7)
        except (KeyError, TypeError, ValueError, AttributeError, json.JSONDecodeError):
            return 0.7

    def _generate_character_reason(self):
        """生成角色评估理由"""

        reasons = []

        if self.score >= 0.8:
            reasons.append("角色提取准确完整")
        elif self.score >= 0.6:
            reasons.append("角色提取基本准确")
        else:
            reasons.append("角色提取存在问题")

        if "mentioned_only" in self.details:
            reasons.append(
                f"部分角色仅被提及未实际出场: {', '.join(self.details['mentioned_only'][:3])}"
            )

        if "main_characters" in self.details:
            reasons.append(f"识别的主要角色: {', '.join(self.details['main_characters'])}")

        self.reason = "；".join(reasons)

    @property
    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "角色提取评估"


class SelfConsistencyMetric(BaseMetric):
    """自一致性评估指标（无监督）"""

    def __init__(
        self,
        threshold: float = 0.70,
        num_runs: int = 5,
        field_weights: Optional[Dict[str, float]] = None,
    ):
        self.threshold = threshold
        self.num_runs = num_runs
        self.field_weights = field_weights or {
            "scene_id": 0.15,
            "setting": 0.15,
            "characters": 0.25,
            "key_events": 0.25,
            "scene_mission": 0.20,
        }

        self.score = 0.0
        self.success = False
        self.reason = ""
        self.field_scores = {}

    def measure(self, test_case: LLMTestCase) -> float:
        """
        评估多次运行的一致性
        注意：test_case.actual_output 应该包含多次运行的结果
        """

        # 假设 actual_output 是一个包含多次运行结果的列表
        runs = json.loads(test_case.actual_output)

        if not isinstance(runs, list) or len(runs) < 2:
            self.score = 0.0
            self.reason = "需要至少2次运行结果进行一致性评估"
            return self.score

        # 计算各字段的一致性
        self.field_scores = self._calculate_field_consistency(runs)

        # 加权平均
        self.score = sum(
            self.field_scores.get(field, 0) * weight for field, weight in self.field_weights.items()
        )

        self.success = self.score >= self.threshold
        self._generate_consistency_reason()

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def _calculate_field_consistency(self, runs: List[List[Dict]]) -> Dict[str, float]:
        """计算每个字段的一致性分数"""

        field_scores = {}

        # 确保所有运行有相同数量的场景
        scene_counts = [len(run) for run in runs]
        if len(set(scene_counts)) > 1:
            field_scores["scene_count"] = 1 - np.std(scene_counts) / np.mean(scene_counts)
        else:
            field_scores["scene_count"] = 1.0

        # 对每个字段计算一致性
        for field in self.field_weights.keys():
            field_scores[field] = self._field_agreement(runs, field)

        return field_scores

    def _field_agreement(self, runs: List[List[Dict]], field: str) -> float:
        """计算特定字段的一致性"""

        if not runs or not runs[0]:
            return 0.0

        agreements = []

        # 对每个场景位置计算一致性
        min_scenes = min(len(run) for run in runs)

        for scene_idx in range(min_scenes):
            values = []

            for run in runs:
                if scene_idx < len(run):
                    value = run[scene_idx].get(field)

                    # 转换为可比较的格式
                    if isinstance(value, list):
                        value = tuple(sorted(value))
                    elif isinstance(value, dict):
                        value = json.dumps(value, sort_keys=True)

                    values.append(value)

            # 计算这个位置的一致性
            if values:
                # 使用最常见值的比例作为一致性分数
                value_counts = Counter(values)
                most_common_count = value_counts.most_common(1)[0][1]
                agreement = most_common_count / len(values)
                agreements.append(agreement)

        return np.mean(agreements) if agreements else 0.0

    def _generate_consistency_reason(self):
        """生成一致性评估理由"""

        reasons = []

        if self.score >= 0.8:
            reasons.append(f"高一致性({self.score:.2f})")
        elif self.score >= 0.6:
            reasons.append(f"中等一致性({self.score:.2f})")
        else:
            reasons.append(f"低一致性({self.score:.2f})")

        # 找出一致性最低的字段
        if self.field_scores:
            worst_field = min(self.field_scores.items(), key=lambda x: x[1])
            if worst_field[1] < 0.6:
                reasons.append(f"{worst_field[0]}字段一致性较差({worst_field[1]:.2f})")

        self.reason = "；".join(reasons)

    @property
    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "自一致性评估"


# 使用示例
if __name__ == "__main__":
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase

    # 创建测试用例
    test_case = LLMTestCase(
        input="内景 咖啡馆 - 日\n李雷和韩梅梅在角落交谈...",
        actual_output=json.dumps(
            [
                {
                    "scene_id": "S01",
                    "setting": "内景 咖啡馆 - 日",
                    "characters": ["李雷", "韩梅梅"],
                    "scene_mission": "展现关系危机",
                    "key_events": ["争吵爆发"],
                }
            ]
        ),
    )

    # 创建评估指标
    boundary_metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=False)
    character_metric = CharacterExtractionMetric(threshold=0.7, use_deepseek=False)

    # 运行评估
    results = evaluate(test_cases=[test_case], metrics=[boundary_metric, character_metric])

    # 打印结果
    print("评估结果:")
    print(f"场景边界分数: {boundary_metric.score:.2f}")
    print(f"角色提取分数: {character_metric.score:.2f}")

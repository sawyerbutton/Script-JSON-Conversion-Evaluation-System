"""
测试DeepEval自定义评估指标
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from deepeval.test_case import LLMTestCase

from src.metrics.deepeval_metrics import (
    CharacterExtractionMetric,
    SceneBoundaryMetric,
    SelfConsistencyMetric,
)


class TestSceneBoundaryMetric:
    """测试场景边界评估指标"""

    @pytest.fixture
    def sample_json_data(self):
        """示例JSON数据"""
        return [
            {
                "scene_id": "S01",
                "setting": "内景 咖啡馆 - 日",
                "characters": ["李雷", "韩梅梅"],
                "scene_mission": "展现关系危机",
                "key_events": ["争吵爆发", "韩梅梅离开"],
            },
            {
                "scene_id": "S02",
                "setting": "外景 街道 - 日",
                "characters": ["李雷"],
                "scene_mission": "李雷的反思",
                "key_events": ["独自行走"],
            },
        ]

    @pytest.fixture
    def test_case(self, sample_json_data):
        """测试用例"""
        return LLMTestCase(
            input="内景 咖啡馆 - 日\n李雷和韩梅梅在角落交谈...",
            actual_output=json.dumps(sample_json_data, ensure_ascii=False),
        )

    def test_metric_initialization_without_llm(self):
        """测试不使用LLM的初始化"""
        metric = SceneBoundaryMetric(threshold=0.75, use_deepseek=False)
        assert metric.threshold == 0.75
        assert metric.use_deepseek is False
        assert metric.score == 0.0
        assert metric.success is False

    def test_metric_initialization_with_llm(self):
        """测试使用LLM的初始化"""
        with patch("src.metrics.deepeval_metrics.DeepSeekClient"):
            metric = SceneBoundaryMetric(threshold=0.75, use_deepseek=True)
            assert metric.use_deepseek is True
            assert hasattr(metric, "llm_client")

    def test_measure_without_llm(self, test_case):
        """测试不使用LLM的评估"""
        metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=False)
        score = metric.measure(test_case)

        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert metric.score == score
        assert metric.success in [True, False]  # numpy布尔值兼容
        assert isinstance(metric.reason, str)

    def test_measure_with_llm(self, test_case):
        """测试使用LLM的评估"""
        mock_client = MagicMock()
        mock_client.complete.return_value = {
            "content": {
                "score": 0.85,
                "boundary_accuracy": "准确",
                "granularity": "合适",
                "completeness": "完整",
                "issues": [],
                "reasoning": "场景划分合理",
            }
        }

        with patch("src.metrics.deepeval_metrics.DeepSeekClient", return_value=mock_client):
            metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=True)
            score = metric.measure(test_case)

            assert isinstance(score, float)
            assert score > 0
            mock_client.complete.assert_called_once()

    def test_async_measure(self, test_case):
        """测试异步评估方法"""
        import asyncio

        metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=False)
        score = asyncio.run(metric.a_measure(test_case))

        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_evaluate_structure(self):
        """测试结构评估"""
        metric = SceneBoundaryMetric(use_deepseek=False)

        # 测试有效数据
        valid_data = [
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色1"],
                "scene_mission": "任务",
                "key_events": ["事件"],
            }
        ]
        score = metric._evaluate_structure(valid_data)
        assert 0 <= score <= 1

        # 测试空数据
        score = metric._evaluate_structure([])
        assert score == 0.0

    def test_check_id_continuity(self):
        """测试场景ID连续性检查"""
        metric = SceneBoundaryMetric(use_deepseek=False)

        # 测试连续ID
        continuous_ids = ["S01", "S02", "S03"]
        score = metric._check_id_continuity(continuous_ids)
        assert score == 1.0

        # 测试不连续ID
        discontinuous_ids = ["S01", "S03", "S04"]
        score = metric._check_id_continuity(discontinuous_ids)
        assert 0 <= score < 1.0

        # 测试空ID
        score = metric._check_id_continuity([])
        assert score == 0.0

        # 测试无效格式
        invalid_ids = ["invalid", "format"]
        score = metric._check_id_continuity(invalid_ids)
        assert score >= 0

    def test_is_valid_setting(self):
        """测试场景设置验证"""
        metric = SceneBoundaryMetric(use_deepseek=False)

        # 有效设置
        assert metric._is_valid_setting("内景 房间 - 日") is True
        assert metric._is_valid_setting("外景 街道 - 夜") is True
        assert metric._is_valid_setting("INT. ROOM - DAY") is True
        assert metric._is_valid_setting("EXT. STREET - NIGHT") is True

        # 无效设置
        assert metric._is_valid_setting("") is False
        assert metric._is_valid_setting("房间 - 日") is False
        assert metric._is_valid_setting(None) is False

    def test_generate_reason(self):
        """测试理由生成"""
        metric = SceneBoundaryMetric(use_deepseek=False)

        metric._generate_reason(structural_score=0.85, semantic_score=0.90)
        assert isinstance(metric.reason, str)
        assert len(metric.reason) > 0

        metric._generate_reason(structural_score=0.50, semantic_score=0.45)
        assert "较低" in metric.reason

    def test_is_successful_property(self):
        """测试成功状态属性"""
        metric = SceneBoundaryMetric(threshold=0.75, use_deepseek=False)

        metric.success = True
        assert metric.is_successful is True

        metric.success = False
        assert metric.is_successful is False

    def test_name_property(self):
        """测试名称属性"""
        metric = SceneBoundaryMetric(use_deepseek=False)
        assert metric.__name__ == "场景边界评估"


class TestCharacterExtractionMetric:
    """测试角色提取评估指标"""

    @pytest.fixture
    def sample_json_data(self):
        """示例JSON数据"""
        return [
            {
                "scene_id": "S01",
                "characters": ["李雷", "韩梅梅"],
                "info_change": [{"character": "李雷", "learned": "韩梅梅生气了"}],
                "relation_change": [{"chars": ["李雷", "韩梅梅"], "from": "恋人", "to": "分手"}],
            },
            {
                "scene_id": "S02",
                "characters": ["李雷", "Jim"],
                "info_change": [],
                "relation_change": [],
            },
        ]

    @pytest.fixture
    def test_case(self, sample_json_data):
        """测试用例"""
        return LLMTestCase(
            input="剧本文本...",
            actual_output=json.dumps(sample_json_data, ensure_ascii=False),
        )

    def test_metric_initialization(self):
        """测试初始化"""
        metric = CharacterExtractionMetric(threshold=0.80, use_deepseek=False)
        assert metric.threshold == 0.80
        assert metric.use_deepseek is False
        assert metric.score == 0.0
        assert metric.details == {}

    def test_measure_without_llm(self, test_case):
        """测试不使用LLM的评估"""
        metric = CharacterExtractionMetric(threshold=0.7, use_deepseek=False)
        score = metric.measure(test_case)

        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert isinstance(metric.details, dict)
        assert metric.success in [True, False]  # numpy布尔值兼容

    def test_measure_with_llm(self, test_case):
        """测试使用LLM的评估"""
        mock_client = MagicMock()
        mock_client.complete.return_value = {
            "content": {
                "score": 0.85,
                "missing_characters": [],
                "invalid_characters": [],
                "accuracy": "准确",
                "reasoning": "角色提取准确",
            }
        }

        with patch("src.metrics.deepeval_metrics.DeepSeekClient", return_value=mock_client):
            metric = CharacterExtractionMetric(threshold=0.7, use_deepseek=True)
            score = metric.measure(test_case)

            assert isinstance(score, float)
            assert score > 0
            mock_client.complete.assert_called_once()

    def test_collect_characters(self):
        """测试角色收集"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        json_data = [
            {
                "characters": ["角色1", "角色2"],
                "info_change": [{"character": "角色3", "learned": "信息"}],
                "relation_change": [{"chars": ["角色1", "角色4"]}],
            }
        ]

        characters = metric._collect_characters(json_data)
        assert isinstance(characters, list)
        assert "角色1" in characters
        assert "角色2" in characters
        assert "角色3" in characters
        assert "角色4" in characters
        assert "观众" not in characters  # 应该过滤掉"观众"

    def test_collect_scene_characters(self):
        """测试场景角色收集"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        json_data = [
            {"characters": ["角色1", "角色2"]},
            {"characters": ["角色1", "角色3"]},
            {"characters": ["角色2"]},
        ]

        scene_chars = metric._collect_scene_characters(json_data)
        assert isinstance(scene_chars, dict)
        assert "角色1" in scene_chars
        assert len(scene_chars["角色1"]) == 2  # 出现在2个场景
        assert len(scene_chars["角色2"]) == 2

    def test_evaluate_consistency(self):
        """测试角色一致性评估"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        all_chars = ["角色1", "角色2", "角色3"]
        scene_chars = {"角色1": [0, 1], "角色2": [0]}

        score = metric._evaluate_consistency(all_chars, scene_chars)
        assert 0 <= score <= 1

        # 应该记录仅被提及的角色
        assert "mentioned_only" in metric.details
        assert "角色3" in metric.details["mentioned_only"]

    def test_evaluate_importance(self):
        """测试角色重要性评估"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        characters = ["角色1", "角色2", "角色3"]
        json_data = [
            {"characters": ["角色1", "角色2"]},
            {"characters": ["角色1"]},
            {"characters": ["角色1", "角色3"]},
        ]

        score = metric._evaluate_importance(characters, json_data)
        assert 0 <= score <= 1

        # 应该记录主要角色
        assert "main_characters" in metric.details
        assert len(metric.details["main_characters"]) <= 3

    def test_evaluate_importance_edge_cases(self):
        """测试重要性评估的边界情况"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        # 空数据
        score = metric._evaluate_importance([], [])
        assert score == 0.0

        # 单个角色
        score = metric._evaluate_importance(["角色1"], [{"characters": ["角色1"]}])
        assert score >= 0

    def test_generate_character_reason(self):
        """测试理由生成"""
        metric = CharacterExtractionMetric(use_deepseek=False)

        metric.score = 0.85
        metric.details = {
            "mentioned_only": ["角色X", "角色Y"],
            "main_characters": ["主角1", "主角2"],
        }
        metric._generate_character_reason()

        assert isinstance(metric.reason, str)
        assert "角色提取" in metric.reason

    def test_async_measure(self, test_case):
        """测试异步评估"""
        import asyncio

        metric = CharacterExtractionMetric(threshold=0.7, use_deepseek=False)
        score = asyncio.run(metric.a_measure(test_case))

        assert isinstance(score, float)

    def test_is_successful_property(self):
        """测试成功状态"""
        metric = CharacterExtractionMetric(threshold=0.75, use_deepseek=False)

        metric.success = True
        assert metric.is_successful is True

    def test_name_property(self):
        """测试名称属性"""
        metric = CharacterExtractionMetric(use_deepseek=False)
        assert metric.__name__ == "角色提取评估"


class TestSelfConsistencyMetric:
    """测试自一致性评估指标"""

    @pytest.fixture
    def multiple_runs_data(self):
        """多次运行的数据"""
        run1 = [
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色1", "角色2"],
                "scene_mission": "任务1",
                "key_events": ["事件1", "事件2"],
            },
            {
                "scene_id": "S02",
                "setting": "外景 街道 - 日",
                "characters": ["角色1"],
                "scene_mission": "任务2",
                "key_events": ["事件3"],
            },
        ]

        run2 = [
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色1", "角色2"],
                "scene_mission": "任务1",
                "key_events": ["事件1", "事件2"],
            },
            {
                "scene_id": "S02",
                "setting": "外景 街道 - 日",
                "characters": ["角色1"],
                "scene_mission": "任务2",
                "key_events": ["事件3"],
            },
        ]

        return [run1, run2]

    @pytest.fixture
    def test_case(self, multiple_runs_data):
        """测试用例"""
        return LLMTestCase(
            input="剧本文本...",
            actual_output=json.dumps(multiple_runs_data, ensure_ascii=False),
        )

    def test_metric_initialization(self):
        """测试初始化"""
        metric = SelfConsistencyMetric(threshold=0.70, num_runs=5)
        assert metric.threshold == 0.70
        assert metric.num_runs == 5
        assert isinstance(metric.field_weights, dict)
        assert metric.score == 0.0

    def test_metric_initialization_custom_weights(self):
        """测试自定义权重"""
        custom_weights = {"scene_id": 0.5, "setting": 0.5}
        metric = SelfConsistencyMetric(field_weights=custom_weights)
        assert metric.field_weights == custom_weights

    def test_measure_with_valid_data(self, test_case):
        """测试有效数据的评估"""
        metric = SelfConsistencyMetric(threshold=0.7, num_runs=2)
        score = metric.measure(test_case)

        assert isinstance(score, float)
        assert 0 <= score <= 1
        assert metric.score == score
        assert metric.success in [True, False]  # numpy布尔值兼容
        assert isinstance(metric.field_scores, dict)

    def test_measure_with_insufficient_data(self):
        """测试数据不足的情况"""
        # 只有一次运行
        single_run = LLMTestCase(
            input="文本",
            actual_output=json.dumps([{"scene_id": "S01"}], ensure_ascii=False),
        )

        metric = SelfConsistencyMetric(threshold=0.7)
        score = metric.measure(single_run)

        assert score == 0.0
        assert "至少2次运行" in metric.reason

    def test_measure_with_inconsistent_data(self):
        """测试不一致的数据"""
        inconsistent_data = [
            [{"scene_id": "S01", "setting": "内景 房间 - 日"}],
            [{"scene_id": "S02", "setting": "外景 街道 - 日"}],  # 完全不同
        ]

        test_case = LLMTestCase(
            input="文本",
            actual_output=json.dumps(inconsistent_data, ensure_ascii=False),
        )

        metric = SelfConsistencyMetric(threshold=0.7)
        score = metric.measure(test_case)

        assert isinstance(score, float)
        assert score < 1.0  # 不一致的数据应该得分较低

    def test_calculate_field_consistency(self):
        """测试字段一致性计算"""
        metric = SelfConsistencyMetric()

        runs = [
            [{"scene_id": "S01", "setting": "内景"}],
            [{"scene_id": "S01", "setting": "内景"}],
        ]

        field_scores = metric._calculate_field_consistency(runs)
        assert isinstance(field_scores, dict)
        assert "scene_count" in field_scores
        assert field_scores["scene_count"] == 1.0  # 场景数相同

    def test_calculate_field_consistency_different_counts(self):
        """测试不同场景数的一致性"""
        metric = SelfConsistencyMetric()

        runs = [
            [{"scene_id": "S01"}],
            [{"scene_id": "S01"}, {"scene_id": "S02"}],  # 不同数量
        ]

        field_scores = metric._calculate_field_consistency(runs)
        assert field_scores["scene_count"] < 1.0

    def test_field_agreement(self):
        """测试字段一致性"""
        metric = SelfConsistencyMetric()

        # 完全一致的数据
        consistent_runs = [
            [{"scene_id": "S01"}],
            [{"scene_id": "S01"}],
        ]

        score = metric._field_agreement(consistent_runs, "scene_id")
        assert score == 1.0

        # 部分一致的数据
        partial_runs = [
            [{"scene_id": "S01"}],
            [{"scene_id": "S02"}],
        ]

        score = metric._field_agreement(partial_runs, "scene_id")
        assert 0 <= score < 1.0

    def test_field_agreement_with_lists(self):
        """测试列表字段的一致性"""
        metric = SelfConsistencyMetric()

        runs = [
            [{"characters": ["角色1", "角色2"]}],
            [{"characters": ["角色2", "角色1"]}],  # 顺序不同但内容相同
        ]

        score = metric._field_agreement(runs, "characters")
        assert score == 1.0  # 应该识别为相同（排序后比较）

    def test_field_agreement_with_dicts(self):
        """测试字典字段的一致性"""
        metric = SelfConsistencyMetric()

        runs = [
            [{"info": {"key": "value"}}],
            [{"info": {"key": "value"}}],
        ]

        score = metric._field_agreement(runs, "info")
        assert score > 0

    def test_field_agreement_empty_data(self):
        """测试空数据的字段一致性"""
        metric = SelfConsistencyMetric()

        score = metric._field_agreement([], "scene_id")
        assert score == 0.0

    def test_generate_consistency_reason(self):
        """测试理由生成"""
        metric = SelfConsistencyMetric()

        # 高一致性
        metric.score = 0.85
        metric.field_scores = {"scene_id": 0.9, "setting": 0.8}
        metric._generate_consistency_reason()
        assert "高一致性" in metric.reason

        # 低一致性
        metric.score = 0.45
        metric.field_scores = {"scene_id": 0.5, "setting": 0.4}
        metric._generate_consistency_reason()
        assert "低一致性" in metric.reason

    def test_generate_consistency_reason_worst_field(self):
        """测试最差字段提示"""
        metric = SelfConsistencyMetric()

        metric.score = 0.70
        metric.field_scores = {"scene_id": 0.9, "setting": 0.5}
        metric._generate_consistency_reason()

        # 应该提及一致性差的字段
        assert "setting" in metric.reason

    def test_async_measure(self, test_case):
        """测试异步评估"""
        import asyncio

        metric = SelfConsistencyMetric(threshold=0.7)
        score = asyncio.run(metric.a_measure(test_case))

        assert isinstance(score, float)

    def test_is_successful_property(self):
        """测试成功状态"""
        metric = SelfConsistencyMetric(threshold=0.75)

        metric.success = True
        assert metric.is_successful is True

    def test_name_property(self):
        """测试名称属性"""
        metric = SelfConsistencyMetric()
        assert metric.__name__ == "自一致性评估"


class TestIntegration:
    """集成测试"""

    def test_all_metrics_together(self):
        """测试所有指标一起工作"""
        json_data = [
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色1", "角色2"],
                "scene_mission": "展现冲突",
                "key_events": ["争吵"],
                "info_change": [{"character": "角色1", "learned": "真相"}],
                "relation_change": [],
            }
        ]

        test_case = LLMTestCase(
            input="剧本文本内容...",
            actual_output=json.dumps(json_data, ensure_ascii=False),
        )

        # 创建所有指标（不使用LLM避免API调用）
        boundary_metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=False)
        character_metric = CharacterExtractionMetric(threshold=0.7, use_deepseek=False)

        # 评估
        boundary_score = boundary_metric.measure(test_case)
        character_score = character_metric.measure(test_case)

        # 验证所有指标都返回有效分数
        assert 0 <= boundary_score <= 1
        assert 0 <= character_score <= 1

        # 验证所有指标都有理由
        assert len(boundary_metric.reason) > 0
        assert len(character_metric.reason) > 0

    def test_metrics_with_edge_case_data(self):
        """测试边界情况数据"""
        # 空场景列表
        empty_data = []
        test_case = LLMTestCase(
            input="空文本",
            actual_output=json.dumps(empty_data, ensure_ascii=False),
        )

        metric = SceneBoundaryMetric(use_deepseek=False)
        score = metric.measure(test_case)
        # 空数据structural_score=0, 但semantic_score默认为1.0
        # 总分 = 0.4*0 + 0.6*1.0 = 0.6
        assert score == 0.6

    def test_metrics_with_minimal_data(self):
        """测试最小数据集"""
        minimal_data = [
            {
                "scene_id": "S01",
                "setting": "内景 房间",
                "characters": [],
                "scene_mission": "",
                "key_events": [],
            }
        ]

        test_case = LLMTestCase(
            input="最小文本",
            actual_output=json.dumps(minimal_data, ensure_ascii=False),
        )

        metric = SceneBoundaryMetric(use_deepseek=False)
        score = metric.measure(test_case)
        assert isinstance(score, float)
        assert 0 <= score <= 1


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_json_in_test_case(self):
        """测试无效JSON"""
        test_case = LLMTestCase(input="文本", actual_output="invalid json")

        metric = SceneBoundaryMetric(use_deepseek=False)
        with pytest.raises(json.JSONDecodeError):
            metric.measure(test_case)

    def test_llm_client_error_handling(self):
        """测试LLM客户端错误处理"""
        mock_client = MagicMock()
        mock_client.complete.side_effect = Exception("API错误")

        json_data = [{"scene_id": "S01", "setting": "内景", "characters": []}]
        test_case = LLMTestCase(
            input="文本",
            actual_output=json.dumps(json_data),
        )

        with patch("src.metrics.deepeval_metrics.DeepSeekClient", return_value=mock_client):
            metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=True)

            # 应该捕获异常并返回默认分数
            with pytest.raises(Exception):
                metric.measure(test_case)

    def test_llm_returns_invalid_format(self):
        """测试LLM返回无效格式"""
        mock_client = MagicMock()
        mock_client.complete.return_value = {"content": "not a dict"}

        json_data = [{"scene_id": "S01", "setting": "内景", "characters": []}]
        test_case = LLMTestCase(
            input="文本",
            actual_output=json.dumps(json_data),
        )

        with patch("src.metrics.deepeval_metrics.DeepSeekClient", return_value=mock_client):
            metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=True)
            score = metric.measure(test_case)

            # 应该使用默认分数
            assert isinstance(score, float)

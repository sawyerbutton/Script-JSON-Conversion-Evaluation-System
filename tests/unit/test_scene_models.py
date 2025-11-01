"""
测试 scene_models.py 中的数据模型
覆盖所有Pydantic模型的验证逻辑
"""

import pytest
from pydantic import ValidationError

from src.models.scene_models import (
    InfoChange,
    KeyObject,
    OutlineSceneInfo,
    RelationChange,
    SceneInfo,
    ScriptEvaluation,
    SetupPayoff,
    validate_script_json,
)


class TestInfoChange:
    """测试InfoChange模型"""

    def test_valid_info_change(self):
        """测试有效的信息变化"""
        info = InfoChange(character="李雷", learned="韩梅梅有外遇")
        assert info.character == "李雷"
        assert info.learned == "韩梅梅有外遇"

    def test_observer_as_character(self):
        """测试'观众'作为角色"""
        info = InfoChange(character="观众", learned="两人关系破裂")
        assert info.character == "观众"

    def test_empty_character_fails(self):
        """测试空角色名称应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            InfoChange(character="", learned="某信息")
        assert "角色名称不能为空" in str(exc_info.value)

    def test_whitespace_only_character_fails(self):
        """测试只有空白字符的角色名称应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            InfoChange(character="   ", learned="某信息")
        assert "角色名称不能为空" in str(exc_info.value)

    def test_character_strips_whitespace(self):
        """测试角色名称会去除空白"""
        info = InfoChange(character="  李雷  ", learned="某信息")
        assert info.character == "李雷"


class TestRelationChange:
    """测试RelationChange模型"""

    def test_valid_relation_change(self):
        """测试有效的关系变化"""
        relation = RelationChange(chars=["李雷", "韩梅梅"], **{"from": "恋人", "to": "陌生人"})
        assert relation.chars == ["李雷", "韩梅梅"]
        assert relation.from_relation == "恋人"
        assert relation.to_relation == "陌生人"

    def test_alias_from_to(self):
        """测试from/to别名正常工作"""
        # 使用别名
        relation = RelationChange(chars=["A", "B"], **{"from": "朋友", "to": "敌人"})
        assert relation.from_relation == "朋友"
        assert relation.to_relation == "敌人"

    def test_exactly_two_characters_required(self):
        """测试必须恰好两个角色"""
        # 只有一个角色
        with pytest.raises(ValidationError) as exc_info:
            RelationChange(chars=["李雷"], **{"from": "单身", "to": "恋爱"})
        # Pydantic会先检查min_length，然后才执行自定义验证
        error_msg = str(exc_info.value)
        assert "chars" in error_msg and (
            "at least 2" in error_msg or "关系变化必须涉及恰好两个角色" in error_msg
        )

        # 三个角色（Pydantic max_length先触发）
        with pytest.raises(ValidationError) as exc_info:
            RelationChange(chars=["李雷", "韩梅梅", "王芳"], **{"from": "朋友", "to": "敌人"})
        error_msg = str(exc_info.value)
        assert "chars" in error_msg and (
            "at most 2" in error_msg or "关系变化必须涉及恰好两个角色" in error_msg
        )

    def test_same_character_fails(self):
        """测试相同角色应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            RelationChange(chars=["李雷", "李雷"], **{"from": "自信", "to": "自卑"})
        assert "关系变化不能是同一个角色" in str(exc_info.value)


class TestKeyObject:
    """测试KeyObject模型"""

    def test_valid_key_object(self):
        """测试有效的关键物品"""
        obj = KeyObject(object="订婚戒指", status="被扔在桌上")
        assert obj.object == "订婚戒指"
        assert obj.status == "被扔在桌上"

    def test_empty_object_name_fails(self):
        """测试空物品名称应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            KeyObject(object="", status="某状态")
        assert "物品名称不能为空" in str(exc_info.value)

    def test_object_strips_whitespace(self):
        """测试物品名称去除空白"""
        obj = KeyObject(object="  手机  ", status="响起")
        assert obj.object == "手机"


class TestSetupPayoff:
    """测试SetupPayoff模型"""

    def test_valid_setup_payoff(self):
        """测试有效的伏笔回收"""
        sp = SetupPayoff(setup_for=["S03", "S05"], payoff_from=["S01"])
        assert sp.setup_for == ["S03", "S05"]
        assert sp.payoff_from == ["S01"]

    def test_empty_lists_allowed(self):
        """测试允许空列表"""
        sp = SetupPayoff()
        assert sp.setup_for == []
        assert sp.payoff_from == []

    def test_invalid_scene_id_format_fails(self):
        """测试无效的场景ID格式应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            SetupPayoff(setup_for=["场景1", "S02"])
        assert "无效的场景ID格式" in str(exc_info.value)

    def test_valid_scene_id_formats(self):
        """测试各种有效的场景ID格式"""
        # S01 格式
        sp1 = SetupPayoff(setup_for=["S01", "S02"])
        assert sp1.setup_for == ["S01", "S02"]

        # E01 格式（虽然在伏笔中不常见，但应该允许）
        sp2 = SetupPayoff(payoff_from=["E01"])
        assert sp2.payoff_from == ["E01"]


class TestSceneInfo:
    """测试SceneInfo模型（标准剧本）"""

    def test_valid_scene_info(self):
        """测试有效的场景信息"""
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 咖啡馆 - 日",
            characters=["李雷", "韩梅梅"],
            scene_mission="展现关系危机",
            key_events=["李雷迟到", "韩梅梅生气"],
        )
        assert scene.scene_id == "S01"
        assert scene.setting == "内景 咖啡馆 - 日"
        assert len(scene.characters) == 2
        assert len(scene.key_events) == 2

    def test_scene_id_validation(self):
        """测试场景ID格式验证"""
        # 有效格式：S01
        scene1 = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene1.scene_id == "S01"

        # 有效格式：E01S01
        scene2 = SceneInfo(
            scene_id="E01S01",
            setting="内景 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene2.scene_id == "E01S01"

        # 无效格式
        with pytest.raises(ValidationError) as exc_info:
            SceneInfo(
                scene_id="场景1",
                setting="内景 - 日",
                characters=[],
                scene_mission="测试",
                key_events=["事件1"],
            )
        assert "场景ID格式错误" in str(exc_info.value)

    def test_setting_validation(self):
        """测试场景设置验证"""
        # 有效：包含"内"
        scene1 = SceneInfo(
            scene_id="S01",
            setting="内景 咖啡馆 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert "内" in scene1.setting

        # 有效：包含"外"
        scene2 = SceneInfo(
            scene_id="S01",
            setting="外景 公园 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert "外" in scene2.setting

        # 无效：不包含内/外
        with pytest.raises(ValidationError) as exc_info:
            SceneInfo(
                scene_id="S01",
                setting="某个地方 - 日",
                characters=[],
                scene_mission="测试",
                key_events=["事件1"],
            )
        assert "场景设置应包含位置类型" in str(exc_info.value)

    def test_key_events_validation(self):
        """测试关键事件验证"""
        # 至少1个
        scene1 = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert len(scene1.key_events) == 1

        # 最多3个
        scene2 = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=[],
            scene_mission="测试",
            key_events=["事件1", "事件2", "事件3"],
        )
        assert len(scene2.key_events) == 3

        # 0个应该失败（Pydantic min_items约束）
        with pytest.raises(ValidationError) as exc_info:
            SceneInfo(
                scene_id="S01",
                setting="内景 - 日",
                characters=[],
                scene_mission="测试",
                key_events=[],
            )
        error_msg = str(exc_info.value)
        # Pydantic V2使用min_items约束，会显示"at least 1 item"
        assert "key_events" in error_msg and (
            "at least 1" in error_msg or "至少需要一个关键事件" in error_msg
        )

        # 超过3个应该失败（Pydantic max_items先触发）
        with pytest.raises(ValidationError) as exc_info:
            SceneInfo(
                scene_id="S01",
                setting="内景 - 日",
                characters=[],
                scene_mission="测试",
                key_events=["事件1", "事件2", "事件3", "事件4"],
            )
        error_msg = str(exc_info.value)
        assert "key_events" in error_msg and (
            "at most 3" in error_msg or "关键事件不应超过3个" in error_msg
        )

    def test_character_validation(self):
        """测试角色验证"""
        # 空角色名应该失败
        with pytest.raises(ValidationError) as exc_info:
            SceneInfo(
                scene_id="S01",
                setting="内景 - 日",
                characters=["李雷", ""],
                scene_mission="测试",
                key_events=["事件1"],
            )
        assert "角色名称不能为空" in str(exc_info.value)

        # 空白字符会被去除
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=["  李雷  ", "韩梅梅"],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene.characters == ["李雷", "韩梅梅"]

    def test_default_optional_fields(self):
        """测试可选字段的默认值"""
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=["李雷"],
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene.info_change == []
        assert scene.relation_change == []
        assert scene.key_object == []
        assert isinstance(scene.setup_payoff, SetupPayoff)


class TestOutlineSceneInfo:
    """测试OutlineSceneInfo模型（故事大纲）"""

    def test_valid_outline_scene(self):
        """测试有效的大纲场景"""
        scene = OutlineSceneInfo(
            scene_id="S1",
            setting="推断：城市街道",
            characters=["主角"],
            scene_mission="展现主角困境",
            key_events=["失业", "接到电话"],
        )
        assert scene.scene_id == "S1"
        assert scene.setting == "推断：城市街道"

    def test_flexible_scene_id_format(self):
        """测试大纲允许更灵活的场景ID格式"""
        # S0, S1, S2 等简化格式
        scene1 = OutlineSceneInfo(scene_id="S0", scene_mission="开场", key_events=["事件1"])
        assert scene1.scene_id == "S0"

        # S01, S02 等标准格式
        scene2 = OutlineSceneInfo(scene_id="S01", scene_mission="开场", key_events=["事件1"])
        assert scene2.scene_id == "S01"

    def test_flexible_setting_validation(self):
        """测试大纲允许更灵活的场景设置"""
        # 允许推断格式
        scene1 = OutlineSceneInfo(
            scene_id="S1",
            setting="推断：办公室",
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene1.setting == "推断：办公室"

        # 允许None（会设置为"未指定"）
        scene2 = OutlineSceneInfo(
            scene_id="S1", setting=None, scene_mission="测试", key_events=["事件1"]
        )
        assert scene2.setting == "未指定"

        # 允许背景说明
        scene3 = OutlineSceneInfo(
            scene_id="S1",
            setting="背景说明：某地",
            scene_mission="测试",
            key_events=["事件1"],
        )
        assert scene3.setting == "背景说明：某地"

    def test_more_key_events_allowed(self):
        """测试大纲允许更多关键事件（1-5个）"""
        # 5个事件（允许）
        scene = OutlineSceneInfo(
            scene_id="S1",
            scene_mission="测试",
            key_events=["事件1", "事件2", "事件3", "事件4", "事件5"],
        )
        assert len(scene.key_events) == 5

        # 0个事件（不允许，Pydantic min_length约束）
        with pytest.raises(ValidationError) as exc_info:
            OutlineSceneInfo(scene_id="S1", scene_mission="测试", key_events=[])
        error_msg = str(exc_info.value)
        assert "key_events" in error_msg and (
            "at least 1" in error_msg or "至少需要一个关键事件" in error_msg
        )

    def test_empty_characters_allowed(self):
        """测试大纲允许空角色列表"""
        scene = OutlineSceneInfo(
            scene_id="S1", characters=[], scene_mission="测试", key_events=["事件1"]
        )
        assert scene.characters == []


class TestScriptEvaluation:
    """测试ScriptEvaluation模型"""

    def test_valid_evaluation(self):
        """测试有效的评估结果"""
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=["李雷"],
            scene_mission="测试",
            key_events=["事件1"],
        )

        evaluation = ScriptEvaluation(
            scenes=[scene],
            total_scenes=1,
            total_characters=1,
            structure_score=0.9,
            completeness_score=0.85,
            accuracy_score=0.88,
            overall_score=0.87,
        )

        assert len(evaluation.scenes) == 1
        assert evaluation.total_scenes == 1
        assert evaluation.overall_score == 0.87

    def test_auto_calculate_overall_score(self):
        """测试自动计算总分"""
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=["李雷"],
            scene_mission="测试",
            key_events=["事件1"],
        )

        evaluation = ScriptEvaluation(
            scenes=[scene],
            total_scenes=1,
            total_characters=1,
            structure_score=0.9,
            completeness_score=0.8,
            accuracy_score=0.7,
            overall_score=0.0,  # 设为0会自动计算
        )

        # 0.3 * 0.9 + 0.35 * 0.8 + 0.35 * 0.7 = 0.27 + 0.28 + 0.245 = 0.795
        assert evaluation.overall_score == 0.795

    def test_scene_count_mismatch_fails(self):
        """测试场景数量不匹配应该失败"""
        scene = SceneInfo(
            scene_id="S01",
            setting="内景 - 日",
            characters=["李雷"],
            scene_mission="测试",
            key_events=["事件1"],
        )

        with pytest.raises(ValidationError) as exc_info:
            ScriptEvaluation(
                scenes=[scene],
                total_scenes=2,  # 不匹配
                total_characters=1,
                structure_score=0.9,
                completeness_score=0.85,
                accuracy_score=0.88,
                overall_score=0.87,
            )
        assert "场景总数" in str(exc_info.value) and "不匹配" in str(exc_info.value)

    def test_empty_scenes_fails(self):
        """测试空场景列表应该失败"""
        with pytest.raises(ValidationError) as exc_info:
            ScriptEvaluation(
                scenes=[],
                total_scenes=0,
                total_characters=0,
                structure_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                overall_score=0.0,
            )
        assert "场景列表不能为空" in str(exc_info.value)


class TestValidateScriptJson:
    """测试validate_script_json函数"""

    def test_validate_single_standard_scene(self):
        """测试验证单个标准场景"""
        json_data = {
            "scene_id": "S01",
            "setting": "内景 咖啡馆 - 日",
            "characters": ["李雷"],
            "scene_mission": "测试",
            "key_events": ["事件1"],
        }

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is True
        assert result["data"] is not None
        assert result["errors"] == []

    def test_validate_scene_list(self):
        """测试验证场景列表"""
        json_data = [
            {
                "scene_id": "S01",
                "setting": "内景 - 日",
                "characters": ["李雷"],
                "scene_mission": "测试1",
                "key_events": ["事件1"],
            },
            {
                "scene_id": "S02",
                "setting": "外景 - 日",
                "characters": ["韩梅梅"],
                "scene_mission": "测试2",
                "key_events": ["事件2"],
            },
        ]

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is True
        assert len(result["data"]) == 2

    def test_validate_invalid_data(self):
        """测试验证无效数据"""
        json_data = {
            "scene_id": "无效ID",  # 格式错误
            "setting": "某地",  # 缺少内/外
            "characters": [],
            "scene_mission": "测试",
            "key_events": [],  # 不能为空
        }

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_outline_scene(self):
        """测试验证大纲场景"""
        json_data = {
            "scene_id": "S1",  # 简化格式
            "setting": "推断：某地",  # 灵活格式
            "characters": [],
            "scene_mission": "测试",
            "key_events": ["事件1"],
        }

        result = validate_script_json(json_data, "outline")
        assert result["valid"] is True

    def test_partial_validation_failure(self):
        """测试部分场景验证失败"""
        json_data = [
            {
                "scene_id": "S01",
                "setting": "内景 - 日",
                "characters": ["李雷"],
                "scene_mission": "测试1",
                "key_events": ["事件1"],
            },
            {
                "scene_id": "无效",  # 这个会失败
                "setting": "某地",
                "characters": [],
                "scene_mission": "测试2",
                "key_events": [],
            },
        ]

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is False
        assert "场景 2 验证失败" in result["errors"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

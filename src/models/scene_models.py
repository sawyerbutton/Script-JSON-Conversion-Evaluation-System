"""
剧本JSON数据模型定义
使用Pydantic进行严格的类型验证和数据校验
"""

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# 全局警告收集器（线程安全）
_validation_warnings = []


def add_validation_warning(message: str, severity: str = "WARNING"):
    """添加验证警告"""
    _validation_warnings.append({"severity": severity, "message": message})


def get_and_clear_warnings():
    """获取并清空警告列表"""
    global _validation_warnings
    warnings = _validation_warnings.copy()
    _validation_warnings.clear()
    return warnings


def is_group_character(char_name: str) -> bool:
    """
    判断是否为群体角色

    群体角色包括：学员、学子、兵组、家人、众人、群众等

    Args:
        char_name: 角色名称

    Returns:
        是否为群体角色
    """
    group_keywords = [
        "学员", "学子", "学生",
        "组", "兵", "士兵",
        "众人", "人们", "群众", "大家",
        "家人", "亲人", "亲戚",
        "同学", "同事", "同僚",
        "村民", "百姓", "居民",
        "观众", "听众", "旁人"
    ]
    return any(keyword in char_name for keyword in group_keywords)


def fuzzy_match_character(char_name: str, character_set: set) -> bool:
    """
    模糊匹配角色名称（支持别名和部分匹配）

    匹配规则：
    1. 精确匹配
    2. 部分匹配：角色A包含角色B或角色B包含角色A
    3. 示例：'张三' 可以匹配 '张三丰', '老张', '张三的朋友'

    Args:
        char_name: 要匹配的角色名称
        character_set: 场景中的角色列表

    Returns:
        是否匹配成功
    """
    # 1. 精确匹配
    if char_name in character_set:
        return True

    # 2. 部分匹配（至少2个字符）
    if len(char_name) >= 2:
        for char in character_set:
            # A包含B 或 B包含A
            if char_name in char or char in char_name:
                return True

    return False


class TimeOfDay(str, Enum):
    """时间枚举"""

    DAY = "日"
    NIGHT = "夜"
    DAWN = "黎明"
    DUSK = "黄昏"
    MORNING = "早晨"
    AFTERNOON = "下午"
    EVENING = "傍晚"


class LocationType(str, Enum):
    """场景类型枚举"""

    INT = "内"  # 内景
    EXT = "外"  # 外景
    INT_EXT = "内/外"  # 内外景


class InfoChange(BaseModel):
    """信息变化模型"""

    character: str = Field(..., description="获得信息的角色或'观众'")
    learned: str = Field(..., description="获得的具体信息")

    @field_validator("character")
    @classmethod
    def validate_character(cls, v):
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


class RelationChange(BaseModel):
    """关系变化模型"""

    chars: List[str] = Field(..., min_length=2, max_length=2, description="涉及的两个角色")
    from_relation: str = Field(..., alias="from", description="原始关系")
    to_relation: str = Field(..., alias="to", description="变化后的关系")

    @field_validator("chars")
    @classmethod
    def validate_chars(cls, v):
        if len(v) != 2:
            raise ValueError("关系变化必须涉及恰好两个角色")
        if v[0] == v[1]:
            raise ValueError("关系变化不能是同一个角色")
        return v

    model_config = ConfigDict(populate_by_name=True)


class KeyObject(BaseModel):
    """关键物品模型"""

    object: str = Field(..., description="物品名称")
    status: str = Field(..., description="物品状态")

    @field_validator("object")
    @classmethod
    def validate_object(cls, v):
        if not v or not v.strip():
            raise ValueError("物品名称不能为空")
        return v.strip()


class SetupPayoff(BaseModel):
    """伏笔与回收模型"""

    setup_for: List[str] = Field(default_factory=list, description="为哪些场景埋伏笔")
    payoff_from: List[str] = Field(default_factory=list, description="回收哪些场景的伏笔")

    @field_validator("setup_for", "payoff_from")
    @classmethod
    def validate_scene_ids(cls, v):
        # 验证场景ID格式 (v is the whole list now in Pydantic V2)
        for item in v:
            if not re.match(r"^[ES]\d+$", item):
                raise ValueError(f"无效的场景ID格式: {item}，应该类似 'S01' 或 'E01S05'")
        return v


class SceneInfo(BaseModel):
    """场景信息模型 - 用于场景1（标准剧本）"""

    scene_id: str = Field(..., description="场景唯一标识符")
    setting: str = Field(..., description="场景环境描述")
    characters: List[str] = Field(..., min_items=0, description="实际出场的角色列表")
    scene_mission: str = Field(..., description="场景的核心戏剧任务")
    key_events: List[str] = Field(..., min_items=1, max_items=3, description="关键事件")
    info_change: List[InfoChange] = Field(default_factory=list, description="信息差变化")
    relation_change: List[RelationChange] = Field(default_factory=list, description="关系变化")
    key_object: List[KeyObject] = Field(default_factory=list, description="关键物品")
    setup_payoff: SetupPayoff = Field(default_factory=SetupPayoff, description="伏笔与照应")

    @field_validator("scene_id")
    @classmethod
    def validate_scene_id(cls, v):
        """验证场景ID格式"""
        # 支持的格式: S01, S02, E01S01, E02S05等
        if not re.match(r"^(E\d{2})?S\d{2}$", v):
            raise ValueError(f"场景ID格式错误: {v}。" f"应该是 'S01' 格式或 'E01S01' 格式")
        return v

    @field_validator("setting")
    @classmethod
    def validate_setting(cls, v):
        """验证场景设置格式"""
        # 应该包含 内/外 和 时间
        if not any(loc in v for loc in ["内", "外", "INT", "EXT"]):
            raise ValueError(f"场景设置应包含位置类型（内/外）: {v}")
        return v

    @field_validator("characters")
    @classmethod
    def validate_character_names(cls, v):
        """验证角色名称"""
        validated = []
        for item in v:
            if not item or not item.strip():
                raise ValueError("角色名称不能为空")
            validated.append(item.strip())
        return validated

    @field_validator("key_events")
    @classmethod
    def validate_key_events(cls, v):
        """验证关键事件数量"""
        if not v:
            raise ValueError("至少需要一个关键事件")
        if len(v) > 3:
            raise ValueError("关键事件不应超过3个")
        return v

    @model_validator(mode="after")
    def validate_scene_consistency(self):
        """场景级别的一致性验证（支持群体角色和别名匹配）"""

        # 检查关系变化中的角色是否都在场景中出现
        characters = set(self.characters)

        for rel_change in self.relation_change:
            for char in rel_change.chars:
                # 跳过特殊角色和群体角色
                if char == "观众" or is_group_character(char):
                    continue

                # 使用模糊匹配（支持别名）
                if not fuzzy_match_character(char, characters):
                    add_validation_warning(
                        f"场景 {self.scene_id}: 关系变化涉及的角色 '{char}' 未在场景角色列表中",
                        severity="WARNING"
                    )

        # 检查信息变化的角色
        for info in self.info_change:
            # 跳过特殊角色和群体角色
            if info.character == "观众" or is_group_character(info.character):
                continue

            # 使用模糊匹配（支持别名）
            if not fuzzy_match_character(info.character, characters):
                add_validation_warning(
                    f"场景 {self.scene_id}: 信息变化涉及的角色 '{info.character}' 未在场景角色列表中",
                    severity="WARNING"
                )

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scene_id": "S01",
                "setting": "内景 咖啡馆 - 日",
                "characters": ["李雷", "韩梅梅"],
                "scene_mission": "展现两人关系的裂痕",
                "key_events": ["李雷提出分手", "韩梅梅愤怒离开"],
                "info_change": [{"character": "韩梅梅", "learned": "李雷一直在欺骗她"}],
                "relation_change": [{"chars": ["李雷", "韩梅梅"], "from": "恋人", "to": "陌生人"}],
                "key_object": [{"object": "订婚戒指", "status": "被扔在桌上"}],
                "setup_payoff": {"setup_for": ["S05"], "payoff_from": []},
            }
        }
    )


class OutlineSceneInfo(BaseModel):
    """
    大纲场景信息模型 - 用于场景2（故事大纲）
    相比SceneInfo更灵活，允许推断和简化
    """

    # 基础字段（放宽限制）
    scene_id: str = Field(..., description="场景唯一标识符（简化格式）")
    setting: Optional[str] = Field(None, description="场景环境描述（可推断）")
    characters: List[str] = Field(default_factory=list, description="实际出场的角色列表")
    scene_mission: str = Field(..., description="场景的核心戏剧任务")
    key_events: List[str] = Field(
        ..., min_length=1, max_length=5, description="关键事件（大纲可多）"
    )

    # 可选字段
    info_change: List[InfoChange] = Field(default_factory=list, description="信息差变化")
    relation_change: List[RelationChange] = Field(default_factory=list, description="关系变化")
    key_object: List[KeyObject] = Field(default_factory=list, description="关键物品")
    setup_payoff: SetupPayoff = Field(default_factory=SetupPayoff, description="伏笔与照应")

    @field_validator("scene_id")
    @classmethod
    def validate_outline_scene_id(cls, v):
        """大纲的场景ID可以更简单"""
        # 允许 S0, S1, S2 等简化格式，以及 S01, S02 等标准格式
        if not re.match(r"^S\d+$", v):
            raise ValueError(f"场景ID格式错误: {v}。应该是 'S0', 'S1', 'S01' 等格式")
        return v

    @field_validator("setting")
    @classmethod
    def validate_outline_setting(cls, v):
        """大纲的场景设置可以更灵活"""
        # 完全允许推断格式、背景说明等
        # 不强制要求包含"内/外"标记
        if v is None:
            return "未指定"
        return v

    @field_validator("characters")
    @classmethod
    def validate_outline_characters(cls, v):
        """验证角色列表（可以为空）"""
        # 清理空白字符
        return [c.strip() for c in v if c and c.strip()]

    @field_validator("key_events")
    @classmethod
    def validate_outline_key_events(cls, v):
        """验证关键事件数量（大纲允许更多）"""
        if not v:
            raise ValueError("至少需要一个关键事件")
        if len(v) > 5:
            add_validation_warning(
                f"关键事件较多({len(v)}个)，建议精简到5个以内",
                severity="INFO"
            )
        return v

    @model_validator(mode="after")
    def validate_outline_consistency(self):
        """大纲的一致性验证（更宽松，支持群体角色和别名匹配）"""
        # 检查关系变化中的角色（只警告，不报错）
        if self.characters:
            characters = set(self.characters)
            for rel_change in self.relation_change:
                for char in rel_change.chars:
                    # 跳过特殊角色和群体角色
                    if char == "观众" or is_group_character(char):
                        continue

                    # 使用模糊匹配（支持别名）
                    if not fuzzy_match_character(char, characters):
                        add_validation_warning(
                            f"场景 {self.scene_id}: 关系变化涉及的角色 '{char}' 未在场景角色列表中",
                            severity="INFO"
                        )

            # 检查信息变化的角色（只警告）
            for info in self.info_change:
                # 跳过特殊角色和群体角色
                if info.character == "观众" or is_group_character(info.character):
                    continue

                # 使用模糊匹配（支持别名）
                if not fuzzy_match_character(info.character, characters):
                    add_validation_warning(
                        f"场景 {self.scene_id}: 信息变化涉及的角色 '{info.character}' 未在场景角色列表中",
                        severity="INFO"
                    )

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scene_id": "S1",
                "setting": "推断：城市街道",
                "characters": ["主角", "路人"],
                "scene_mission": "展现主角的日常困境",
                "key_events": ["主角失业", "接到神秘电话", "决定接受挑战"],
                "info_change": [{"character": "观众", "learned": "主角处境艰难"}],
                "relation_change": [],
                "key_object": [{"object": "神秘信封", "status": "推动情节"}],
                "setup_payoff": {"setup_for": ["S3"], "payoff_from": []},
            }
        }
    )


class ScriptEvaluation(BaseModel):
    """剧本评估结果模型"""

    scenes: List[SceneInfo] = Field(..., description="所有场景列表")
    total_scenes: int = Field(..., description="场景总数")
    total_characters: int = Field(..., description="角色总数")

    # 评估分数
    structure_score: float = Field(..., ge=0, le=1, description="结构分数")
    completeness_score: float = Field(..., ge=0, le=1, description="完整性分数")
    accuracy_score: float = Field(..., ge=0, le=1, description="准确性分数")
    overall_score: float = Field(..., ge=0, le=1, description="总体分数")

    # 详细问题
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    @field_validator("scenes")
    @classmethod
    def validate_scenes_not_empty(cls, v):
        if not v:
            raise ValueError("场景列表不能为空")
        return v

    @model_validator(mode="after")
    def validate_scene_count_and_calculate_score(self):
        """验证场景数量并计算总分"""
        # 验证场景总数
        if self.total_scenes != len(self.scenes):
            raise ValueError(f"场景总数({self.total_scenes})与实际场景数({len(self.scenes)})不匹配")

        # 如果没有提供总分，自动计算
        if self.overall_score == 0:
            # 加权平均
            structure = self.structure_score * 0.3
            completeness = self.completeness_score * 0.35
            accuracy = self.accuracy_score * 0.35
            self.overall_score = round(structure + completeness + accuracy, 3)

        return self


# 批量验证函数
def validate_script_json(json_data: Dict[str, Any], scene_type: str = "standard") -> Dict[str, Any]:
    """
    验证剧本JSON数据

    Args:
        json_data: 要验证的JSON数据
        scene_type: "standard" 或 "outline"

    Returns:
        验证结果字典，包含:
        - valid: 是否通过验证（仅指fatal错误）
        - errors: 致命错误列表（导致验证失败）
        - warnings: 警告列表（不影响验证通过）
        - data: 验证后的数据
    """
    result = {"valid": False, "errors": [], "warnings": [], "data": None}

    try:
        # 清空之前的警告
        get_and_clear_warnings()

        # 根据类型选择模型
        model_class = SceneInfo if scene_type == "standard" else OutlineSceneInfo

        # 如果是场景列表
        if isinstance(json_data, list):
            validated_scenes = []
            for i, scene_data in enumerate(json_data):
                try:
                    scene = model_class(**scene_data)
                    validated_scenes.append(scene)
                except Exception as e:
                    result["errors"].append(f"场景 {i+1} 验证失败: {str(e)}")

            # 收集验证过程中的警告
            validation_warnings = get_and_clear_warnings()
            result["warnings"] = [w["message"] for w in validation_warnings]

            if not result["errors"]:
                result["valid"] = True
                result["data"] = [scene.dict() for scene in validated_scenes]

        # 如果是单个场景
        else:
            scene = model_class(**json_data)
            result["valid"] = True
            result["data"] = scene.dict()

            # 收集验证过程中的警告
            validation_warnings = get_and_clear_warnings()
            result["warnings"] = [w["message"] for w in validation_warnings]

    except Exception as e:
        result["errors"].append(f"验证失败: {str(e)}")
        # 即使失败也要收集警告
        validation_warnings = get_and_clear_warnings()
        result["warnings"] = [w["message"] for w in validation_warnings]

    return result


# 使用示例
if __name__ == "__main__":
    # 测试场景数据
    test_scene = {
        "scene_id": "S01",
        "setting": "内景 咖啡馆 - 日",
        "characters": ["李雷", "韩梅梅"],
        "scene_mission": "展现两人的感情危机",
        "key_events": ["李雷迟到了半小时", "韩梅梅发现李雷手机里的暧昧短信"],
        "info_change": [{"character": "韩梅梅", "learned": "李雷可能有外遇"}],
        "relation_change": [{"chars": ["李雷", "韩梅梅"], "from": "恋人", "to": "产生隔阂的恋人"}],
        "key_object": [{"object": "李雷的手机", "status": "屏幕显示暧昧短信"}],
        "setup_payoff": {"setup_for": ["S03", "S05"], "payoff_from": []},
    }

    # 验证数据
    result = validate_script_json(test_scene, "standard")

    if result["valid"]:
        print("✅ 验证通过!")
        print("数据:", result["data"])
    else:
        print("❌ 验证失败!")
        for error in result["errors"]:
            print(f"  错误: {error}")

    # 测试错误数据
    bad_scene = {
        "scene_id": "场景1",  # 格式错误
        "setting": "某个地方",  # 缺少内外景标记
        "characters": [],  # 可能为空
        "scene_mission": "测试",
        "key_events": [],  # 不能为空
    }

    result2 = validate_script_json(bad_scene, "standard")
    print("\n测试错误数据:")
    if not result2["valid"]:
        print("❌ 预期的验证失败:")
        for error in result2["errors"]:
            print(f"  错误: {error}")

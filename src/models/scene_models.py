"""
剧本JSON数据模型定义
使用Pydantic进行严格的类型验证和数据校验
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import re


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
    
    @validator('character')
    def validate_character(cls, v):
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


class RelationChange(BaseModel):
    """关系变化模型"""
    chars: List[str] = Field(..., min_items=2, max_items=2, description="涉及的两个角色")
    from_relation: str = Field(..., alias="from", description="原始关系")
    to_relation: str = Field(..., alias="to", description="变化后的关系")
    
    @validator('chars')
    def validate_chars(cls, v):
        if len(v) != 2:
            raise ValueError("关系变化必须涉及恰好两个角色")
        if v[0] == v[1]:
            raise ValueError("关系变化不能是同一个角色")
        return v
    
    class Config:
        allow_population_by_field_name = True


class KeyObject(BaseModel):
    """关键物品模型"""
    object: str = Field(..., description="物品名称")
    status: str = Field(..., description="物品状态")
    
    @validator('object')
    def validate_object(cls, v):
        if not v or not v.strip():
            raise ValueError("物品名称不能为空")
        return v.strip()


class SetupPayoff(BaseModel):
    """伏笔与回收模型"""
    setup_for: List[str] = Field(default_factory=list, description="为哪些场景埋伏笔")
    payoff_from: List[str] = Field(default_factory=list, description="回收哪些场景的伏笔")
    
    @validator('setup_for', 'payoff_from', each_item=True)
    def validate_scene_ids(cls, v):
        # 验证场景ID格式
        if not re.match(r'^[ES]\d+$', v):
            raise ValueError(f"无效的场景ID格式: {v}，应该类似 'S01' 或 'E01S05'")
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
    
    @validator('scene_id')
    def validate_scene_id(cls, v):
        """验证场景ID格式"""
        # 支持的格式: S01, S02, E01S01, E02S05等
        if not re.match(r'^(E\d{2})?S\d{2}$', v):
            raise ValueError(
                f"场景ID格式错误: {v}。"
                f"应该是 'S01' 格式或 'E01S01' 格式"
            )
        return v
    
    @validator('setting')
    def validate_setting(cls, v):
        """验证场景设置格式"""
        # 应该包含 内/外 和 时间
        if not any(loc in v for loc in ['内', '外', 'INT', 'EXT']):
            raise ValueError(f"场景设置应包含位置类型（内/外）: {v}")
        return v
    
    @validator('characters', each_item=True)
    def validate_character_names(cls, v):
        """验证角色名称"""
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        # 移除多余空格
        return v.strip()
    
    @validator('key_events')
    def validate_key_events(cls, v):
        """验证关键事件数量"""
        if not v:
            raise ValueError("至少需要一个关键事件")
        if len(v) > 3:
            raise ValueError("关键事件不应超过3个")
        return v
    
    @root_validator
    def validate_scene_consistency(cls, values):
        """场景级别的一致性验证"""
        
        # 检查关系变化中的角色是否都在场景中出现
        characters = set(values.get('characters', []))
        relation_changes = values.get('relation_change', [])
        
        for rel_change in relation_changes:
            for char in rel_change.chars:
                if char not in characters and char != "观众":
                    # 警告但不阻止（某些情况下可能合理）
                    print(f"警告: 关系变化涉及的角色 '{char}' 未在场景角色列表中")
        
        # 检查信息变化的角色
        info_changes = values.get('info_change', [])
        for info in info_changes:
            if info.character not in characters and info.character != "观众":
                print(f"警告: 信息变化涉及的角色 '{info.character}' 未在场景角色列表中")
        
        return values
    
    class Config:
        # 允许字段描述
        schema_extra = {
            "example": {
                "scene_id": "S01",
                "setting": "内景 咖啡馆 - 日",
                "characters": ["李雷", "韩梅梅"],
                "scene_mission": "展现两人关系的裂痕",
                "key_events": ["李雷提出分手", "韩梅梅愤怒离开"],
                "info_change": [
                    {
                        "character": "韩梅梅",
                        "learned": "李雷一直在欺骗她"
                    }
                ],
                "relation_change": [
                    {
                        "chars": ["李雷", "韩梅梅"],
                        "from": "恋人",
                        "to": "陌生人"
                    }
                ],
                "key_object": [
                    {
                        "object": "订婚戒指",
                        "status": "被扔在桌上"
                    }
                ],
                "setup_payoff": {
                    "setup_for": ["S05"],
                    "payoff_from": []
                }
            }
        }


class OutlineSceneInfo(SceneInfo):
    """
    大纲场景信息模型 - 用于场景2（故事大纲）
    继承自SceneInfo但放宽某些验证规则
    """
    
    # 重写某些字段以放宽限制
    setting: Optional[str] = Field(None, description="推断的场景环境")
    
    @validator('setting')
    def validate_outline_setting(cls, v):
        """大纲的场景设置可以更灵活"""
        # 可以为空或推断的
        if v and "推断" not in v and not any(loc in v for loc in ['内', '外', 'INT', 'EXT']):
            # 只是警告，不报错
            print(f"提示: 场景设置可能需要包含位置类型: {v}")
        return v
    
    @validator('scene_id')
    def validate_outline_scene_id(cls, v):
        """大纲的场景ID可以更简单"""
        # 允许 S1, S2 等简化格式
        if not re.match(r'^S\d+$', v):
            raise ValueError(f"场景ID格式错误: {v}。应该是 'S1', 'S01' 等格式")
        return v


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
    
    @validator('scenes')
    def validate_scenes_not_empty(cls, v):
        if not v:
            raise ValueError("场景列表不能为空")
        return v
    
    @validator('total_scenes')
    def validate_scene_count(cls, v, values):
        scenes = values.get('scenes', [])
        if v != len(scenes):
            raise ValueError(f"场景总数({v})与实际场景数({len(scenes)})不匹配")
        return v
    
    @root_validator
    def calculate_overall_score(cls, values):
        """如果没有提供总分，自动计算"""
        if 'overall_score' not in values or values['overall_score'] == 0:
            # 加权平均
            structure = values.get('structure_score', 0) * 0.3
            completeness = values.get('completeness_score', 0) * 0.35
            accuracy = values.get('accuracy_score', 0) * 0.35
            values['overall_score'] = round(structure + completeness + accuracy, 3)
        return values


# 批量验证函数
def validate_script_json(json_data: Dict[str, Any], scene_type: str = "standard") -> Dict[str, Any]:
    """
    验证剧本JSON数据
    
    Args:
        json_data: 要验证的JSON数据
        scene_type: "standard" 或 "outline"
        
    Returns:
        验证结果字典
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "data": None
    }
    
    try:
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
            
            if not result["errors"]:
                result["valid"] = True
                result["data"] = [scene.dict() for scene in validated_scenes]
        
        # 如果是单个场景
        else:
            scene = model_class(**json_data)
            result["valid"] = True
            result["data"] = scene.dict()
            
    except Exception as e:
        result["errors"].append(f"验证失败: {str(e)}")
    
    return result


# 使用示例
if __name__ == "__main__":
    # 测试场景数据
    test_scene = {
        "scene_id": "S01",
        "setting": "内景 咖啡馆 - 日",
        "characters": ["李雷", "韩梅梅"],
        "scene_mission": "展现两人的感情危机",
        "key_events": [
            "李雷迟到了半小时",
            "韩梅梅发现李雷手机里的暧昧短信"
        ],
        "info_change": [
            {
                "character": "韩梅梅",
                "learned": "李雷可能有外遇"
            }
        ],
        "relation_change": [
            {
                "chars": ["李雷", "韩梅梅"],
                "from": "恋人",
                "to": "产生隔阂的恋人"
            }
        ],
        "key_object": [
            {
                "object": "李雷的手机",
                "status": "屏幕显示暧昧短信"
            }
        ],
        "setup_payoff": {
            "setup_for": ["S03", "S05"],
            "payoff_from": []
        }
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
        "key_events": []  # 不能为空
    }
    
    result2 = validate_script_json(bad_scene, "standard")
    print("\n测试错误数据:")
    if not result2["valid"]:
        print("❌ 预期的验证失败:")
        for error in result2["errors"]:
            print(f"  错误: {error}")

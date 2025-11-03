# 剧本/大纲转JSON技术实现文档

## 文档信息

- **文档版本**: v1.0
- **创建日期**: 2025-11-03
- **技术栈**: Python 3.9+, Pydantic V2, OpenAI SDK, DeepSeek API
- **代码仓库**: Script-JSON-Conversion-Evaluation-System

---

## 目录

1. [技术架构](#1-技术架构)
2. [核心模块实现](#2-核心模块实现)
3. [LLM客户端封装](#3-llm客户端封装)
4. [Prompt工程](#4-prompt工程)
5. [数据模型设计](#5-数据模型设计)
6. [JSON解析与后处理](#6-json解析与后处理)
7. [错误处理机制](#7-错误处理机制)
8. [性能优化](#8-性能优化)
9. [测试策略](#9-测试策略)
10. [部署指南](#10-部署指南)

---

## 1. 技术架构

### 1.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (Scripts)                      │
│  ┌────────────────────┐        ┌────────────────────┐      │
│  │ convert_script_    │        │ convert_outline_   │      │
│  │ to_json.py         │        │ to_json.py         │      │
│  └─────────┬──────────┘        └─────────┬──────────┘      │
└────────────┼─────────────────────────────┼─────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      业务逻辑层 (Core)                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            LLM Client (deepseek_client.py)          │   │
│  │  - DeepSeekClient: API调用封装                      │   │
│  │  - DeepSeekConfig: 配置管理                         │   │
│  │  - 重试机制、成本追踪、性能监控                     │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────┴──────────────────────────────┐   │
│  │         Data Models (scene_models.py)               │   │
│  │  - SceneInfo: 标准剧本模型                          │   │
│  │  - OutlineSceneInfo: 大纲模型                       │   │
│  │  - 子模型: InfoChange, RelationChange等             │   │
│  │  - 验证函数: validate_script_json()                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      工具层 (Utils)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Exceptions   │  │ Logger       │  │ Performance  │     │
│  │ - 16种自定义  │  │ - 彩色日志    │  │ - API追踪    │     │
│  │   异常类型    │  │ - 文件日志    │  │ - 性能分析   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            File Handler (file_handler.py)            │  │
│  │  - 文件读写、路径处理                                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
             │                              │
             ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    外部服务层 (External)                     │
│  ┌────────────────────┐        ┌────────────────────┐      │
│  │  DeepSeek API      │        │  File System       │      │
│  │  - chat模型        │        │  - Prompt模板      │      │
│  │  - reasoner模型    │        │  - 输出目录        │      │
│  └────────────────────┘        └────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术选型

| 组件 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| 编程语言 | Python | 3.9+ | AI生态丰富，开发效率高 |
| 数据验证 | Pydantic | V2 | 强大的数据验证和类型系统 |
| LLM服务 | DeepSeek API | V3.2 | 高性价比，中文友好 |
| API客户端 | OpenAI SDK | Latest | 兼容DeepSeek，生态成熟 |
| 日志 | logging + colorlog | - | 标准库 + 彩色输出 |
| 测试 | pytest | Latest | Python标准测试框架 |

### 1.3 目录结构

```
Script-JSON-Conversion-Evaluation-System/
├── src/
│   ├── llm/
│   │   └── deepseek_client.py      # LLM客户端封装
│   ├── models/
│   │   └── scene_models.py         # Pydantic数据模型
│   └── utils/
│       ├── exceptions.py           # 自定义异常
│       ├── logger.py               # 日志系统
│       ├── performance.py          # 性能监控
│       └── file_handler.py         # 文件处理
├── scripts/
│   ├── convert_script_to_json.py   # 标准剧本转换脚本
│   └── convert_outline_to_json.py  # 大纲转换脚本
├── prompts/
│   ├── scene1_extraction.txt       # 标准剧本Prompt
│   └── scene2_extraction.txt       # 大纲Prompt
├── configs/
│   └── deepseek_config.yaml        # DeepSeek配置
└── tests/
    └── unit/
        ├── test_deepseek_client.py # LLM客户端测试
        └── test_scene_models.py    # 数据模型测试
```

---

## 2. 核心模块实现

### 2.1 转换脚本架构

**文件**: `scripts/convert_script_to_json.py`

```python
#!/usr/bin/env python3
"""
剧本转JSON转换脚本
核心流程: 读取 → Prompt填充 → LLM调用 → JSON解析 → 验证 → 保存
"""

import json
import sys
from pathlib import Path

# 关键函数1: 加载Prompt模板
def load_prompt_template(template_name: str = "scene1_extraction.txt") -> str:
    """从prompts/目录加载预定义的Prompt模板"""
    prompt_path = Path(__file__).parent.parent / "prompts" / template_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# 关键函数2: 转换核心逻辑
def convert_script_to_json(
    script_text: str,
    scene_type: str = "standard",
    validate: bool = True
) -> dict:
    """
    剧本转JSON核心逻辑

    Args:
        script_text: 剧本原文
        scene_type: "standard" 或 "outline"
        validate: 是否执行Pydantic验证

    Returns:
        dict: JSON数据（已验证）
    """
    # 步骤1: 初始化DeepSeek客户端
    client = DeepSeekClient()

    # 步骤2: 选择并加载Prompt模板
    template_name = (
        "scene1_extraction.txt" if scene_type == "standard"
        else "scene2_extraction.txt"
    )
    prompt_template = load_prompt_template(template_name)

    # 步骤3: 填充Prompt（简单字符串替换）
    prompt = prompt_template.replace("{script_text}", script_text)

    # 步骤4: 调用LLM
    response = client.complete(
        prompt=prompt,
        temperature=0.1 if scene_type == "standard" else 0.2,
        max_tokens=4000,
    )

    # 步骤5: 提取和解析JSON
    json_data = extract_json_from_response(response["content"])

    # 步骤6: Pydantic验证（可选）
    if validate:
        validation_result = validate_script_json(json_data, scene_type)
        if not validation_result["valid"]:
            raise ValueError(f"验证失败: {validation_result['errors']}")

    return json_data
```

**关键设计点**:
1. **模板化Prompt**: 将Prompt与代码分离，便于调整
2. **参数化**: 支持不同场景类型和验证选项
3. **错误传播**: 异常向上传播，由调用方处理

### 2.2 JSON提取逻辑

**核心挑战**: LLM响应可能包含多种格式

```python
def extract_json_from_response(response_text: str) -> dict:
    """
    从LLM响应中提取JSON内容

    处理三种情况:
    1. 被```json```包裹
    2. 被```包裹（无语言标记）
    3. 纯JSON文本
    """
    response_text = response_text.strip()

    # 情况1: ```json ... ```
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()

    # 情况2: ``` ... ```
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()

    # 情况3: 直接是JSON
    else:
        json_text = response_text

    # 解析JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"响应内容:\n{response_text[:500]}...")
        raise
```

**错误处理**:
- 如果三种模式都无法提取有效JSON，抛出异常
- 打印部分响应内容（前500字符）以便调试

---

## 3. LLM客户端封装

### 3.1 DeepSeekClient设计

**文件**: `src/llm/deepseek_client.py`

```python
from dataclasses import dataclass
from openai import OpenAI
import time

@dataclass
class DeepSeekConfig:
    """DeepSeek API配置"""
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"  # 或 "deepseek-reasoner"
    temperature: float = 0.1
    max_tokens: int = 8192
    max_retries: int = 3
    retry_delay: int = 2  # 秒

    def __post_init__(self):
        """根据模型自动调整max_tokens"""
        if self.model == "deepseek-reasoner":
            # reasoner模型支持更大输出
            if self.max_tokens < 32768:
                self.max_tokens = 32768
        elif self.model == "deepseek-chat":
            # chat模型最大8K
            if self.max_tokens > 8192:
                self.max_tokens = 8192


class DeepSeekClient:
    """DeepSeek API客户端封装"""

    def __init__(self, config: Optional[DeepSeekConfig] = None):
        # 配置初始化
        if config is None:
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            config = DeepSeekConfig(api_key=api_key)

        self.config = config

        # 使用OpenAI SDK（兼容DeepSeek）
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )

        # 统计信息
        self.total_tokens = 0
        self.total_cost = 0.0
        self.api_tracker = APICallTracker()

    @timer(name="DeepSeek API调用")  # 性能装饰器
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        发送完成请求到DeepSeek

        核心功能:
        1. 构建messages格式
        2. 发送API请求
        3. 重试机制
        4. 统计追踪
        """
        # 构建messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 参数覆盖
        temperature = temperature or self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        # 重试循环
        for attempt in range(self.config.max_retries):
            try:
                # 发送请求
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # 提取内容
                content = response.choices[0].message.content

                # 更新统计
                tokens_used = response.usage.total_tokens
                self.total_tokens += tokens_used
                cost = self._update_cost(tokens_used)

                # 记录API调用
                self.api_tracker.record_call(
                    endpoint=self.config.model,
                    duration=time.time() - start_time,
                    tokens=tokens_used,
                    cost=cost,
                    success=True,
                )

                # 返回结果
                return {
                    "content": content,
                    "raw_response": response,
                    "tokens_used": tokens_used,
                    "model": response.model,
                }

            except openai.RateLimitError as e:
                # 限流错误：重试
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise APIRateLimitError("API请求频率超限")

            except openai.APIError as e:
                # API错误：重试
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise APIConnectionError(f"API调用失败: {str(e)}")

    def _update_cost(self, tokens: int) -> float:
        """
        成本估算
        DeepSeek定价: 输入¥1/1M, 输出¥2/1M
        简化假设: 输入输出各占一半
        """
        estimated_cost = tokens * 1.5 / 1_000_000
        self.total_cost += estimated_cost
        return estimated_cost
```

### 3.2 关键设计模式

**1. 依赖注入**:
```python
# 支持自定义配置
custom_config = DeepSeekConfig(
    api_key="sk-xxx",
    model="deepseek-reasoner",
    max_tokens=32768,
)
client = DeepSeekClient(config=custom_config)
```

**2. 装饰器模式**:
```python
@timer(name="DeepSeek API调用")  # 自动计时
def complete(self, ...):
    ...
```

**3. 策略模式**:
```python
# 根据模型自动调整参数
def __post_init__(self):
    if self.model == "deepseek-reasoner":
        self.max_tokens = 32768
    elif self.model == "deepseek-chat":
        self.max_tokens = 8192
```

### 3.3 重试机制实现

```python
# 指数退避策略
for attempt in range(max_retries):
    try:
        return api_call()
    except RateLimitError:
        if attempt < max_retries - 1:
            delay = 2 ** attempt  # 1s, 2s, 4s, 8s...
            time.sleep(delay)
        else:
            raise
```

---

## 4. Prompt工程

### 4.1 Prompt模板结构

**标准剧本模板** (`prompts/scene1_extraction.txt`):

```
┌──────────────────────────────────────┐
│ 1. 系统提示 (Role Definition)         │
│    "你是一个专业的剧本分析专家..."    │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 2. 任务说明 (Task Description)        │
│    "请将以下标准格式剧本转换为..."    │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 3. 输入文本 (Input Placeholder)       │
│    {script_text}                     │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 4. 输出格式 (Output Schema)           │
│    JSON Schema示例                    │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 5. 提取规则 (Extraction Rules)        │
│    9条详细规则                        │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 6. 注意事项 (Important Notes)         │
│    格式要求、一致性要求等             │
└──────────────────────────────────────┘
           ↓
┌──────────────────────────────────────┐
│ 7. 示例输出 (Example Output)          │
│    完整JSON示例                       │
└──────────────────────────────────────┘
```

### 4.2 Prompt优化技巧

**1. 角色定位**:
```
你是一个专业的剧本分析专家，擅长从标准格式剧本中提取结构化信息。
```
- 明确AI的角色和专业领域
- 建立任务背景和权威性

**2. Few-Shot Learning**:
```json
// 示例输出
[
  {
    "scene_id": "S01",
    "setting": "内景 咖啡馆 - 日",
    ...
  }
]
```
- 提供完整的JSON示例
- 展示期望的输出格式

**3. 规则明确化**:
```
### 1. 场景划分 (scene_id)
- 根据场景标题（通常包含"内景/外景"）划分
- 场景ID从S01开始递增
- 如果有集的概念，使用E01S01格式
```
- 编号列表清晰
- 每条规则具体明确
- 提供示例和反例

**4. 格式约束**:
```
## 注意事项
1. **严格遵循JSON格式**，确保所有字段都存在
2. **输出纯JSON**，不要包含任何解释性文字
```
- 强调关键约束
- 使用粗体突出重点

**5. 容错处理**:
```
**输出格式要求**：
1. 可以先进行分析思考（使用<think>标签）
2. 最终输出必须是完整的JSON数组
3. JSON可以用```json```代码块包裹
```
- 允许LLM思考过程
- 兼容多种输出格式
- 提高解析成功率

### 4.3 标准剧本 vs 大纲 Prompt差异

| 维度 | 标准剧本 (scene1) | 大纲 (scene2) |
|------|------------------|---------------|
| 角色定位 | "剧本分析专家" | "故事分析专家，擅长合理推断" |
| 任务说明 | "转换标准格式剧本" | "转换大纲并进行合理推断" |
| 场景ID规则 | "S01, S02格式" | "S0, S1, S2简化格式" |
| Setting要求 | "必须明确" | "可以推断并标注'推断：'" |
| 关键事件数 | "1-3个" | "1-5个" |
| 推断指导 | 无 | 详细的推断规范和标注要求 |
| 特殊场景 | 无 | 背景说明场景、时间跳跃处理 |

### 4.4 Prompt动态填充

```python
# 简单的字符串替换
def fill_prompt(template: str, script_text: str) -> str:
    """
    将剧本文本填充到Prompt模板中

    注意:
    - 使用简单的字符串替换（不是复杂的模板引擎）
    - 占位符: {script_text}
    - 保持原文格式（换行、缩进）
    """
    return template.replace("{script_text}", script_text)
```

**为什么不用Jinja2等模板引擎？**
- Prompt只有一个占位符，简单替换足够
- 避免引入额外依赖
- 性能更好

---

## 5. 数据模型设计

### 5.1 Pydantic模型架构

**文件**: `src/models/scene_models.py`

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
import re

# 子模型1: 信息变化
class InfoChange(BaseModel):
    """信息差变化模型"""
    character: str = Field(..., description="获得信息的角色或'观众'")
    learned: str = Field(..., description="获得的具体信息")

    @field_validator("character")
    @classmethod
    def validate_character(cls, v):
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


# 子模型2: 关系变化
class RelationChange(BaseModel):
    """角色关系变化模型"""
    chars: List[str] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="涉及的两个角色"
    )
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

    # Pydantic V2配置
    model_config = ConfigDict(populate_by_name=True)


# 子模型3: 关键物品
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


# 子模型4: 伏笔与回收
class SetupPayoff(BaseModel):
    """伏笔与回收模型"""
    setup_for: List[str] = Field(default_factory=list)
    payoff_from: List[str] = Field(default_factory=list)

    @field_validator("setup_for", "payoff_from")
    @classmethod
    def validate_scene_ids(cls, v):
        for item in v:
            if not re.match(r"^[ES]\d+$", item):
                raise ValueError(f"无效的场景ID: {item}")
        return v


# 主模型: 标准剧本场景
class SceneInfo(BaseModel):
    """标准剧本场景信息模型"""

    scene_id: str = Field(..., description="场景唯一标识符")
    setting: str = Field(..., description="场景环境描述")
    characters: List[str] = Field(..., min_items=0)
    scene_mission: str = Field(..., description="场景核心任务")
    key_events: List[str] = Field(..., min_items=1, max_items=3)

    # 可选字段
    info_change: List[InfoChange] = Field(default_factory=list)
    relation_change: List[RelationChange] = Field(default_factory=list)
    key_object: List[KeyObject] = Field(default_factory=list)
    setup_payoff: SetupPayoff = Field(default_factory=SetupPayoff)

    # 字段级验证
    @field_validator("scene_id")
    @classmethod
    def validate_scene_id(cls, v):
        """验证场景ID格式: S01 或 E01S01"""
        if not re.match(r"^(E\d{2})?S\d{2}$", v):
            raise ValueError(f"场景ID格式错误: {v}")
        return v

    @field_validator("setting")
    @classmethod
    def validate_setting(cls, v):
        """验证场景设置必须包含内/外景标记"""
        if not any(loc in v for loc in ["内", "外", "INT", "EXT"]):
            raise ValueError(f"场景设置应包含位置类型: {v}")
        return v

    @field_validator("key_events")
    @classmethod
    def validate_key_events(cls, v):
        """验证关键事件数量"""
        if not v:
            raise ValueError("至少需要一个关键事件")
        if len(v) > 3:
            raise ValueError("关键事件不应超过3个")
        return v

    # 模型级验证
    @model_validator(mode="after")
    def validate_scene_consistency(self):
        """场景级别的一致性验证"""
        characters = set(self.characters)

        # 检查关系变化中的角色是否都在场景中
        for rel_change in self.relation_change:
            for char in rel_change.chars:
                # 跳过特殊角色和群体角色
                if char == "观众" or is_group_character(char):
                    continue

                # 使用模糊匹配（支持别名）
                if not fuzzy_match_character(char, characters):
                    add_validation_warning(
                        f"角色 '{char}' 未在场景角色列表中"
                    )

        return self
```

### 5.2 Pydantic V2关键特性

**1. field_validator装饰器**:
```python
# Pydantic V2语法
@field_validator("scene_id")
@classmethod
def validate_scene_id(cls, v):
    # v是字段值
    if not re.match(r"^S\d{2}$", v):
        raise ValueError("格式错误")
    return v
```

**2. model_validator装饰器**:
```python
# 模型级验证（所有字段已填充）
@model_validator(mode="after")
def validate_scene_consistency(self):
    # self是完整的模型实例
    if some_condition:
        raise ValueError("一致性错误")
    return self
```

**3. Field配置**:
```python
# 字段定义与验证
key_events: List[str] = Field(
    ...,                    # 必填
    min_items=1,            # 最少1个
    max_items=3,            # 最多3个
    description="关键事件"   # 文档说明
)
```

**4. 别名支持**:
```python
# 支持JSON字段别名
from_relation: str = Field(..., alias="from")

# 使用时
relation_change = RelationChange(
    chars=["A", "B"],
    **{"from": "陌生", "to": "朋友"}  # JSON使用"from"
)
# 访问时
relation_change.from_relation  # Python使用完整名称
```

### 5.3 验证函数封装

```python
def validate_script_json(
    json_data: Dict[str, Any],
    scene_type: str = "standard"
) -> Dict[str, Any]:
    """
    统一的验证入口函数

    Returns:
        {
            "valid": bool,           # 是否通过验证
            "errors": List[str],     # 致命错误（阻断）
            "warnings": List[str],   # 警告（不阻断）
            "data": Optional[dict]   # 验证后的数据
        }
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "data": None
    }

    try:
        # 选择模型
        ModelClass = SceneInfo if scene_type == "standard" else OutlineSceneInfo

        # 验证（支持列表和单个对象）
        if isinstance(json_data, list):
            validated_scenes = []
            for i, scene_data in enumerate(json_data):
                try:
                    scene = ModelClass(**scene_data)
                    validated_scenes.append(scene)
                except Exception as e:
                    result["errors"].append(f"场景 {i+1} 验证失败: {str(e)}")

            if not result["errors"]:
                result["valid"] = True
                result["data"] = [scene.dict() for scene in validated_scenes]
        else:
            scene = ModelClass(**json_data)
            result["valid"] = True
            result["data"] = scene.dict()

        # 收集警告
        result["warnings"] = get_and_clear_warnings()

    except Exception as e:
        result["errors"].append(str(e))
        result["warnings"] = get_and_clear_warnings()

    return result
```

### 5.4 警告与错误分离 (v0.2.1新增)

```python
# 全局警告收集器
_validation_warnings = []

def add_validation_warning(message: str, severity: str = "WARNING"):
    """添加验证警告（不抛出异常）"""
    _validation_warnings.append({
        "severity": severity,
        "message": message
    })

def get_and_clear_warnings():
    """获取并清空警告列表"""
    global _validation_warnings
    warnings = _validation_warnings.copy()
    _validation_warnings.clear()
    return warnings
```

**设计理念**:
- **致命错误**: 抛出异常，阻断流程（如必填字段缺失）
- **警告**: 记录但不阻断（如角色一致性问题）
- **分离处理**: 让用户决定如何处理警告

---

## 6. JSON解析与后处理

### 6.1 多格式JSON提取

```python
def extract_json_from_response(response_text: str) -> dict:
    """
    从LLM响应中智能提取JSON

    支持的格式:
    1. ```json\n{...}\n```
    2. ```\n{...}\n```
    3. {...}
    4. <think>...</think>\n[{...}]  (reasoner模型)
    """
    response_text = response_text.strip()

    # 去除思考过程（reasoner模型）
    if "<think>" in response_text:
        think_end = response_text.rfind("</think>")
        if think_end != -1:
            response_text = response_text[think_end + 8:].strip()

    # 提取代码块
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        json_text = response_text[start:end].strip()
    else:
        json_text = response_text

    # 解析JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        # 尝试修复常见问题
        json_text = fix_common_json_errors(json_text)
        return json.loads(json_text)
```

### 6.2 JSON修复策略

```python
def fix_common_json_errors(json_text: str) -> str:
    """
    修复常见的JSON格式错误

    常见问题:
    1. 末尾缺少 ]
    2. 尾随逗号
    3. 单引号替代双引号
    4. 未转义的换行符
    """
    # 1. 检查数组闭合
    if json_text.startswith("[") and not json_text.rstrip().endswith("]"):
        json_text = json_text.rstrip() + "]"

    # 2. 移除尾随逗号
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

    # 3. 替换单引号（谨慎）
    # json_text = json_text.replace("'", '"')

    # 4. 修复换行符
    json_text = json_text.replace('\n', '\\n')

    return json_text
```

### 6.3 大文件处理 (v0.2.0新增)

**问题**: 超大剧本（40+场景）可能超出max_tokens限制

**解决方案**:

```python
def smart_model_selection(script_text: str) -> str:
    """
    根据剧本大小智能选择模型

    规则:
    - < 5000字符: deepseek-chat (max_tokens=8K)
    - >= 5000字符: deepseek-reasoner (max_tokens=64K)
    """
    char_count = len(script_text)

    if char_count >= 5000:
        return "deepseek-reasoner"
    else:
        return "deepseek-chat"


# 使用
model = smart_model_selection(script_text)
client = DeepSeekClient(
    config=DeepSeekConfig(
        api_key=api_key,
        model=model,
        max_tokens=32768 if model == "reasoner" else 4000
    )
)
```

---

## 7. 错误处理机制

### 7.1 自定义异常体系

**文件**: `src/utils/exceptions.py`

```python
class BaseScriptException(Exception):
    """基础异常类"""
    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


# API相关异常
class APIConnectionError(BaseScriptException):
    """API连接错误"""
    pass


class APIRateLimitError(BaseScriptException):
    """API限流错误"""
    pass


class APIResponseError(BaseScriptException):
    """API响应错误（如JSON格式不正确）"""
    pass


# 数据验证异常
class ValidationError(BaseScriptException):
    """数据验证错误"""
    pass


# 文件处理异常
class FileReadError(BaseScriptException):
    """文件读取错误"""
    pass
```

### 7.2 错误上下文管理

```python
class ErrorContext:
    """错误上下文管理器"""

    def __init__(self, operation: str, **kwargs):
        self.operation = operation
        self.context = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"操作失败: {self.operation}",
                extra={"context": self.context, "error": str(exc_val)}
            )
        return False  # 不吞掉异常


# 使用
with ErrorContext("JSON解析", file="script.md"):
    json_data = json.loads(json_text)
```

### 7.3 重试装饰器

```python
def retry_on_error(max_attempts=3, delay=2, exceptions=(Exception,)):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"尝试 {attempt + 1} 失败，{delay}秒后重试: {e}"
                        )
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator


# 使用
@retry_on_error(max_attempts=3, exceptions=(APIConnectionError,))
def call_api():
    return client.complete(prompt)
```

---

## 8. 性能优化

### 8.1 性能监控

**文件**: `src/utils/performance.py`

```python
from functools import wraps
import time

def timer(name: str = "操作"):
    """计时装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger.info(f"{name} 耗时: {duration:.2f}秒")
            return result
        return wrapper
    return decorator


class APICallTracker:
    """API调用追踪器"""

    def __init__(self):
        self.calls = []

    def record_call(
        self,
        endpoint: str,
        duration: float,
        tokens: int = 0,
        cost: float = 0.0,
        success: bool = True,
        error: str = None
    ):
        """记录API调用"""
        self.calls.append({
            "endpoint": endpoint,
            "duration": duration,
            "tokens": tokens,
            "cost": cost,
            "success": success,
            "error": error,
            "timestamp": time.time(),
        })

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.calls:
            return {}

        total_calls = len(self.calls)
        successful = sum(1 for c in self.calls if c["success"])
        total_tokens = sum(c["tokens"] for c in self.calls)
        total_cost = sum(c["cost"] for c in self.calls)
        avg_duration = sum(c["duration"] for c in self.calls) / total_calls

        return {
            "total_calls": total_calls,
            "successful": successful,
            "failed": total_calls - successful,
            "success_rate": successful / total_calls,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "avg_duration": avg_duration,
        }
```

### 8.2 缓存策略

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_prompt_template(template_name: str) -> str:
    """缓存Prompt模板"""
    with open(f"prompts/{template_name}", "r") as f:
        return f.read()
```

### 8.3 批量处理优化

```python
def batch_convert(
    script_files: List[str],
    max_workers: int = 3
) -> List[Dict]:
    """
    批量转换多个剧本

    优化:
    1. 并发处理（使用线程池）
    2. 错误隔离（单个失败不影响其他）
    3. 进度追踪
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务
        futures = {
            executor.submit(convert_single_script, file): file
            for file in script_files
        }

        # 收集结果
        for future in as_completed(futures):
            file = futures[future]
            try:
                result = future.result()
                results.append({"file": file, "status": "success", "data": result})
            except Exception as e:
                results.append({"file": file, "status": "error", "error": str(e)})
                logger.error(f"处理 {file} 失败: {e}")

    return results
```

---

## 9. 测试策略

### 9.1 单元测试

**文件**: `tests/unit/test_scene_models.py`

```python
import pytest
from src.models.scene_models import SceneInfo, validate_script_json

class TestSceneInfo:
    """SceneInfo模型测试"""

    def test_valid_scene(self):
        """测试有效场景数据"""
        scene_data = {
            "scene_id": "S01",
            "setting": "内景 咖啡馆 - 日",
            "characters": ["李雷", "韩梅梅"],
            "scene_mission": "展现关系裂痕",
            "key_events": ["迟到", "发现短信"],
        }

        scene = SceneInfo(**scene_data)
        assert scene.scene_id == "S01"
        assert len(scene.characters) == 2

    def test_invalid_scene_id(self):
        """测试无效场景ID"""
        scene_data = {
            "scene_id": "场景1",  # 格式错误
            "setting": "内景 咖啡馆 - 日",
            "characters": [],
            "scene_mission": "测试",
            "key_events": ["事件"],
        }

        with pytest.raises(ValueError, match="场景ID格式错误"):
            SceneInfo(**scene_data)

    def test_key_events_limit(self):
        """测试关键事件数量限制"""
        scene_data = {
            "scene_id": "S01",
            "setting": "内景 房间 - 日",
            "characters": [],
            "scene_mission": "测试",
            "key_events": ["事件1", "事件2", "事件3", "事件4"],  # 超过3个
        }

        with pytest.raises(ValueError, match="不应超过3个"):
            SceneInfo(**scene_data)


class TestValidateScriptJson:
    """验证函数测试"""

    def test_validate_list(self):
        """测试验证场景列表"""
        json_data = [
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色A"],
                "scene_mission": "任务",
                "key_events": ["事件"],
            }
        ]

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_with_errors(self):
        """测试带错误的验证"""
        json_data = [
            {
                "scene_id": "错误ID",
                "setting": "内景 房间 - 日",
                "characters": [],
                "scene_mission": "任务",
                "key_events": [],  # 不能为空
            }
        ]

        result = validate_script_json(json_data, "standard")
        assert result["valid"] is False
        assert len(result["errors"]) > 0
```

### 9.2 Mock LLM客户端

```python
from unittest.mock import Mock, patch

class TestConversion:
    """转换流程测试"""

    @patch('src.llm.deepseek_client.DeepSeekClient')
    def test_convert_script_to_json(self, mock_client_class):
        """测试转换函数（Mock LLM调用）"""
        # 配置Mock
        mock_client = Mock()
        mock_client.complete.return_value = {
            "content": '''```json
            [
              {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色A"],
                "scene_mission": "任务",
                "key_events": ["事件"]
              }
            ]
            ```''',
            "tokens_used": 1000,
        }
        mock_client_class.return_value = mock_client

        # 调用转换函数
        result = convert_script_to_json("测试剧本文本")

        # 验证
        assert len(result) == 1
        assert result[0]["scene_id"] == "S01"
        mock_client.complete.assert_called_once()
```

### 9.3 集成测试

```python
class TestIntegration:
    """端到端集成测试"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="需要API密钥"
    )
    def test_real_api_call(self):
        """真实API调用测试（需要API密钥）"""
        script_text = """
        # 场景1

        ## 内景 房间 - 日

        角色A走进房间。
        """

        result = convert_script_to_json(script_text, validate=True)

        assert isinstance(result, list)
        assert len(result) > 0
        assert "scene_id" in result[0]
```

---

## 10. 部署指南

### 10.1 环境配置

**requirements.txt**:
```txt
# 核心依赖
pydantic>=2.0.0
openai>=1.0.0
python-dotenv>=1.0.0

# 日志和工具
colorlog>=6.7.0

# 测试
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
```

**安装**:
```bash
pip install -r requirements.txt
```

### 10.2 环境变量

**.env文件**:
```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 目录配置
DATA_DIR=./data
OUTPUT_DIR=./outputs
LOG_LEVEL=INFO

# 模型配置（可选）
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=4000
DEEPSEEK_TEMPERATURE=0.1
```

### 10.3 Docker部署

**Dockerfile**:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY prompts/ ./prompts/

# 环境变量
ENV PYTHONPATH=/app

# 入口
ENTRYPOINT ["python", "scripts/convert_script_to_json.py"]
```

**使用**:
```bash
# 构建
docker build -t script-converter .

# 运行
docker run -v $(pwd)/script_examples:/data \
           -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
           script-converter /data/script_01.md
```

### 10.4 API服务化

**Flask示例**:
```python
from flask import Flask, request, jsonify
from src.llm.deepseek_client import DeepSeekClient
from scripts.convert_script_to_json import convert_script_to_json

app = Flask(__name__)

@app.route('/api/convert', methods=['POST'])
def convert_api():
    """
    POST /api/convert
    Body: {
      "script_text": "剧本内容...",
      "scene_type": "standard"
    }
    """
    try:
        data = request.json
        script_text = data.get('script_text')
        scene_type = data.get('scene_type', 'standard')

        if not script_text:
            return jsonify({"error": "缺少script_text"}), 400

        result = convert_script_to_json(script_text, scene_type)

        return jsonify({
            "success": True,
            "data": result,
            "scene_count": len(result)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 11. 常见问题排查

### 11.1 API调用失败

**问题**: `APIConnectionError: 无法初始化DeepSeek客户端`

**排查**:
1. 检查API密钥是否正确
   ```bash
   echo $DEEPSEEK_API_KEY
   ```
2. 检查网络连接
   ```bash
   curl https://api.deepseek.com/v1/models
   ```
3. 检查base_url配置

**解决**:
```python
# 调试模式
client = DeepSeekClient(debug=True)
```

### 11.2 JSON解析失败

**问题**: `JSONDecodeError: Expecting value`

**排查**:
1. 查看LLM响应原文（打印response_text）
2. 检查是否有非JSON内容
3. 检查是否截断（max_tokens不足）

**解决**:
```python
# 增加max_tokens
response = client.complete(prompt, max_tokens=8192)

# 或使用reasoner模型
config = DeepSeekConfig(model="deepseek-reasoner", max_tokens=32768)
```

### 11.3 验证失败

**问题**: `ValidationError: 场景ID格式错误`

**排查**:
1. 检查LLM输出的scene_id格式
2. 查看是否符合正则表达式
3. 检查是否是大纲模式但使用了标准验证

**解决**:
```python
# 使用正确的scene_type
result = validate_script_json(json_data, scene_type="outline")

# 或调整正则表达式
```

### 11.4 性能问题

**问题**: 转换速度慢

**优化方案**:
1. 使用批量处理
2. 减少max_tokens
3. 使用更快的模型
4. 启用缓存

```python
# 批量处理
results = batch_convert(script_files, max_workers=5)

# 缓存Prompt模板
@lru_cache(maxsize=128)
def load_prompt_template(name):
    ...
```

---

## 12. 扩展开发

### 12.1 添加新的场景类型

**步骤**:
1. 定义新的Pydantic模型
   ```python
   class TVSeriesSceneInfo(BaseModel):
       scene_id: str
       episode_id: str  # 新增字段
       ...
   ```

2. 创建新的Prompt模板
   ```
   prompts/scene3_tv_series.txt
   ```

3. 在转换脚本中添加支持
   ```python
   if scene_type == "tv_series":
       template = "scene3_tv_series.txt"
       model = TVSeriesSceneInfo
   ```

### 12.2 集成新的LLM服务

**步骤**:
1. 创建新的客户端类
   ```python
   class OpenAIClient(BaseLLMClient):
       def complete(self, prompt, **kwargs):
           ...
   ```

2. 统一接口
   ```python
   class LLMClientFactory:
       @staticmethod
       def create(provider: str):
           if provider == "deepseek":
               return DeepSeekClient()
           elif provider == "openai":
               return OpenAIClient()
   ```

### 12.3 添加后处理插件

```python
class PostProcessor:
    """后处理器基类"""
    def process(self, json_data: dict) -> dict:
        raise NotImplementedError


class CharacterNormalizer(PostProcessor):
    """角色名称标准化"""
    def process(self, json_data: dict) -> dict:
        # 实现角色名称统一
        ...


# 使用
json_data = convert_script_to_json(script_text)
json_data = CharacterNormalizer().process(json_data)
json_data = OtherProcessor().process(json_data)
```

---

## 13. 参考资料

### 13.1 内部文档
- [业务流程文档](剧本大纲转JSON业务流程文档.md)
- [API参考](ref/api-reference.md)
- [测试参考](ref/testing-reference.md)

### 13.2 外部资源
- [Pydantic V2文档](https://docs.pydantic.dev/2.0/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [DeepSeek API文档](https://platform.deepseek.com/api-docs/)

### 13.3 代码示例
- `tests/unit/` - 单元测试示例
- `scripts/test_system.py` - 系统测试
- `code-samples/` - 参考实现

---

## 附录A: 完整代码示例

### 示例1: 最小化转换脚本

```python
#!/usr/bin/env python3
"""最小化的剧本转换示例"""

import json
import os
from openai import OpenAI

def convert_script_minimal(script_text: str) -> list:
    """最小化实现"""
    # 1. 初始化客户端
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com/v1"
    )

    # 2. 构建Prompt
    prompt = f"""
请将以下剧本转换为JSON格式，每个场景包含:
- scene_id: 场景ID
- setting: 场景设置
- characters: 角色列表
- scene_mission: 场景任务
- key_events: 关键事件列表

剧本:
{script_text}

输出JSON数组:
"""

    # 3. 调用API
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    # 4. 解析结果
    content = response.choices[0].message.content

    # 提取JSON
    if "```json" in content:
        start = content.find("```json") + 7
        end = content.find("```", start)
        content = content[start:end]

    return json.loads(content)


# 使用
if __name__ == "__main__":
    script = """
    ## 内景 咖啡馆 - 日

    李雷坐在窗边。

    李雷
    你好。
    """

    result = convert_script_minimal(script)
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 示例2: 带验证的转换

```python
from pydantic import BaseModel, Field
from typing import List

class SimpleScene(BaseModel):
    scene_id: str
    setting: str
    characters: List[str]
    scene_mission: str
    key_events: List[str] = Field(min_items=1)

def convert_with_validation(script_text: str) -> List[SimpleScene]:
    """带Pydantic验证的转换"""
    # 转换
    json_data = convert_script_minimal(script_text)

    # 验证
    scenes = [SimpleScene(**scene) for scene in json_data]

    return scenes


# 使用
scenes = convert_with_validation(script_text)
for scene in scenes:
    print(f"场景: {scene.scene_id}, 任务: {scene.scene_mission}")
```

---

## 附录B: 性能基准

### 测试环境
- CPU: Intel i7-9700K
- RAM: 16GB
- Python: 3.9.13
- 网络: 100Mbps

### 基准数据

| 剧本大小 | 场景数 | 字符数 | API耗时 | 总耗时 | 成本 |
|---------|-------|-------|--------|-------|------|
| 小型 | 5-10 | 2000 | 8s | 10s | ¥0.008 |
| 中型 | 10-20 | 5000 | 18s | 22s | ¥0.015 |
| 大型 | 30-50 | 12000 | 45s | 52s | ¥0.035 |

---

**文档维护**: Development Team
**最后更新**: 2025-11-03
**版本**: v1.0

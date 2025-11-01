# 剧本JSON转换评估系统

## 项目简介

这是一个基于 **DeepEval** 框架和 **DeepSeek API** 的自动化系统，提供两大核心功能：

1. **剧本→JSON自动转换**：使用DeepSeek API将剧本文本智能转换为结构化JSON数据
2. **转换质量评估**：采用三层评估架构验证转换质量

系统支持标准剧本和故事大纲两种场景，提供从转换到评估的完整工作流。

## 核心特性

- 🚀 **完整的转换评估工作流**
  - 一键转换：剧本文本 → 结构化JSON
  - 自动评估：转换质量即时反馈
  - 5个核心脚本支持不同使用场景

- 🎯 **双场景支持**
  - **标准剧本（Standard）**：严格验证规则，scene_id必须S01格式，setting必须包含"内/外"
  - **故事大纲（Outline）**：灵活验证规则，scene_id可以是S0/S1，setting允许推断

- ✅ **三层评估架构**
  - **结构层**：Pydantic V2模型验证JSON格式、字段完整性
  - **统计层**：场景边界F1分数、角色提取准确率
  - **语义层**：DeepSeek LLM评估场景任务、关键事件、信息/关系变化

- 📊 **全面的质量指标**
  - 结构验证：字段格式、类型、必填项检查
  - 场景边界：F1、Precision、Recall
  - 角色提取：准确率、一致性
  - 语义准确：场景任务匹配度、关键事件覆盖率

- 🤖 **智能LLM集成**
  - DeepSeek API自动转换剧本为JSON
  - 专门优化的prompt模板（scene1/scene2）
  - LLM-as-Judge语义评估
  - 智能重试和错误处理

- 📁 **清晰的项目结构**
  - 输出文件自动分类管理（outputs/converted/, outputs/reports/）
  - 支持批量处理脚本
  - 完整的参考文档系统

## 项目结构

```
Script-JSON-Conversion-Evaluation-System/
│
├── src/                      # 源代码
│   ├── models/               # Pydantic V2数据模型
│   │   └── scene_models.py   # SceneInfo & OutlineSceneInfo
│   ├── metrics/              # 评估指标
│   │   └── deepeval_metrics.py
│   ├── llm/                  # LLM集成
│   │   └── deepseek_client.py
│   ├── evaluators/           # 评估器
│   │   └── main_evaluator.py
│   └── utils/                # 工具函数
│       └── file_handler.py
│
├── scripts/                  # 核心脚本（5个）
│   ├── test_system.py        # 系统测试（无需API）
│   ├── convert_script_to_json.py      # 标准剧本→JSON转换
│   ├── convert_outline_to_json.py     # 故事大纲→JSON转换
│   ├── run_full_evaluation.py         # 标准剧本完整评估
│   └── run_outline_evaluation.py      # 故事大纲完整评估
│
├── script_examples/          # 测试样本
│   ├── 测试1.md              # 标准剧本示例
│   ├── 测试2.md
│   ├── 测试3.md
│   ├── 测试4.md
│   └── 故事大纲示例.md       # 故事大纲示例
│
├── prompts/                  # Prompt模板
│   ├── scene1_extraction.txt      # 标准剧本转换prompt
│   ├── scene2_extraction.txt      # 故事大纲转换prompt
│   ├── boundary_evaluation.txt    # 场景边界评估prompt
│   └── semantic_evaluation.txt    # 语义评估prompt
│
├── configs/                  # 配置文件
│   ├── default_config.yaml
│   ├── evaluation_weights.yaml
│   └── deepseek_config.yaml
│
├── ref/                      # 参考文档
│   ├── scripts-guide.md      # 脚本使用指南（413行）
│   ├── models-reference.md   # 模型参考文档（477行）
│   ├── project-overview.md
│   ├── architecture.md
│   ├── development.md
│   └── api-reference.md
│
├── docs/                     # 其他文档
│   ├── project_structure.md
│   └── script_eval_development_checklist.md
│
├── tests/                    # 测试文件
│   ├── unit/
│   ├── integration/
│   └── test_data/
│
├── outputs/                  # 输出目录（自动生成，已.gitignore）
│   ├── converted/            # 转换后的JSON文件
│   └── reports/              # 评估报告
│
├── requirements.txt          # 依赖列表
├── .env.example              # 环境变量示例
├── CLAUDE.md                 # AI开发助手参考文档
└── README.md                 # 本文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone <repository-url>
cd Script-JSON-Conversion-Evaluation-System

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API

创建 `.env` 文件并添加DeepSeek API Key：

```bash
cp .env.example .env
# 编辑.env文件，添加：DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 运行系统测试（无需API）

```bash
python scripts/test_system.py
```

### 4. 使用核心脚本

#### 场景A：只做转换（不评估）

```bash
# 转换标准剧本
python scripts/convert_script_to_json.py script_examples/测试1.md

# 转换故事大纲
python scripts/convert_outline_to_json.py script_examples/故事大纲示例.md

# 输出位置：outputs/converted/
```

#### 场景B：完整流程（转换+评估）

```bash
# 标准剧本：转换+评估（默认启用LLM语义评估）
python scripts/run_full_evaluation.py script_examples/测试1.md

# 故事大纲：转换+评估
python scripts/run_outline_evaluation.py script_examples/故事大纲示例.md

# 输出位置：
# - JSON: outputs/converted/
# - 报告: outputs/reports/
```

#### 场景C：节省API调用（跳过LLM评估）

```bash
# 不使用LLM语义评估（更快、更便宜）
python scripts/run_full_evaluation.py script_examples/测试1.md --no-llm-judge
```

#### 场景D：批量处理

```bash
# 批量转换所有剧本
for file in script_examples/测试*.md; do
    python scripts/run_full_evaluation.py "$file"
done
```

### 5. 使用Python API（高级用法）

```python
# 方式1：使用转换脚本（推荐）
from scripts.convert_script_to_json import convert_script_to_json
from utils.file_handler import FileHandler

file_handler = FileHandler()
script_text = file_handler.read_text_file("script_examples/测试1.md")
json_data = convert_script_to_json(script_text, scene_type="standard")

# 方式2：使用评估器API
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig

config = EvaluationConfig(
    use_deepseek_judge=True,  # 启用LLM语义评估
    save_detailed_report=True
)

evaluator = ScriptEvaluator(config)

result = evaluator.evaluate_script(
    source_text=script_text,
    extracted_json=json_data,
    scene_type="standard",  # 或 "outline"
    source_file="测试1.md"
)

print(f"总分: {result.overall_score:.3f}")
print(f"质量级别: {result.quality_level}")
print(f"通过: {'✅' if result.passed else '❌'}")
```

## 📋 完整工作流示例

### 示例：标准剧本完整评估

#### 输入：剧本文本文件

```markdown
# 文件: script_examples/测试1.md

内景 咖啡馆 - 日

李雷坐在角落里，不安地看着手表。韩梅梅推门而入，表情冷漠。

韩梅梅
（冷淡地）
你想说什么？

李雷
（紧张）
我...我想解释上次的事。

韩梅梅站着不动，面无表情地看着他。

韩梅梅
没必要了。我们结束吧。

韩梅梅转身离开，李雷呆坐原地。
```

#### 执行：运行评估脚本

```bash
python scripts/run_full_evaluation.py script_examples/测试1.md
```

#### 输出：评估结果

```
======================================================================
剧本JSON转换评估系统 - 完整评估流程
======================================================================

[步骤 1/3] 读取剧本文件: script_examples/测试1.md
  文件大小: 234 字符

[步骤 2/3] 使用DeepSeek API转换剧本为JSON...
  场景类型: standard
正在调用DeepSeek API转换剧本...
✅ JSON解析成功，包含 1 个场景

验证JSON格式...
  场景1: ✅ 验证通过
  ✅ JSON已保存到: outputs/converted/测试1_output.json

[步骤 3/3] 运行质量评估...
  使用LLM语义评估: 是

======================================================================
评估结果
======================================================================

文件: script_examples/测试1.md
质量级别: 优秀
总分: 0.865
通过: ✅ 是

各项得分:
  结构验证: 1.000
  场景边界: 1.000
  角色提取: 0.709
  语义准确: 0.750

统计信息:
  场景总数: 1
  角色总数: 2

======================================================================
✅ 评估完成！
======================================================================
```

#### 生成的文件

```
outputs/
├── converted/
│   └── 测试1_output.json          # 转换后的JSON
└── reports/
    └── report_2025-11-01T13:30:00.json  # 详细评估报告
```

## 🔧 核心模块说明

### 1. 核心脚本 (scripts/)

**5个脚本，覆盖所有使用场景：**

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `test_system.py` | 系统测试 | 无 | 测试结果 |
| `convert_script_to_json.py` | 标准剧本转换 | 剧本.md | JSON |
| `convert_outline_to_json.py` | 故事大纲转换 | 大纲.md | JSON |
| `run_full_evaluation.py` | 标准剧本完整评估 | 剧本.md | JSON + 报告 |
| `run_outline_evaluation.py` | 故事大纲完整评估 | 大纲.md | JSON + 报告 |

详见：[ref/scripts-guide.md](ref/scripts-guide.md)

### 2. 数据模型 (src/models/)

**Pydantic V2严格验证：**

- **`SceneInfo`**（标准剧本）
  - scene_id: S01, S02格式
  - setting: 必须包含"内/外"
  - key_events: 1-3个

- **`OutlineSceneInfo`**（故事大纲）
  - scene_id: S0, S1, S01都可以
  - setting: 允许"推断："、"背景说明"
  - key_events: 1-5个

- **支持模型**
  - `InfoChange`: 信息变化
  - `RelationChange`: 关系变化
  - `KeyObject`: 关键物品
  - `SetupPayoff`: 伏笔与回收

详见：[ref/models-reference.md](ref/models-reference.md)

### 3. 评估指标 (src/metrics/)

**三层评估架构：**

- **结构层**：JSON schema验证（Pydantic）
- **统计层**：
  - `SceneBoundaryMetric`: F1、Precision、Recall
  - `CharacterExtractionMetric`: 角色提取准确率
- **语义层**：
  - DeepSeek LLM评估场景任务、关键事件
  - 信息变化、关系变化匹配度

### 4. LLM集成 (src/llm/)

**DeepSeek客户端功能：**

- OpenAI兼容接口
- 自动重试机制
- Token统计和成本追踪
- 支持两个温度模式（0.1标准剧本，0.2故事大纲）

### 5. 评估器 (src/evaluators/)

**主评估器协调：**

- 三层评估流程编排
- 权重管理和分数聚合
- 报告生成（JSON格式）
- 质量级别判定（优秀/良好/合格/不合格）

## 配置说明

### 评估权重配置

编辑 `configs/evaluation_weights.yaml`:

```yaml
weights:
  structure: 0.25    # 结构验证权重
  boundary: 0.25     # 场景边界权重
  character: 0.25    # 角色提取权重
  semantic: 0.25     # 语义准确权重
```

### DeepSeek API配置

编辑 `configs/deepseek_config.yaml`:

```yaml
api:
  model: "deepseek-chat"
  temperature: 0.1
  max_retries: 3

cost_tracking:
  enabled: true
  daily_limit: 100.0  # 每日预算（人民币）
```

## 开发指南

### 添加新的评估指标

1. 在 `src/metrics/` 创建新的指标类
2. 继承 `deepeval.metrics.BaseMetric`
3. 实现 `measure()` 和 `a_measure()` 方法
4. 在主评估器中集成

### 自定义Prompt模板

编辑 `prompts/` 目录下的模板文件，自定义评估标准和输出格式。

### 运行测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 系统测试
python scripts/test_system.py
```

## 📚 文档

### 核心参考文档
- 📘 [脚本使用指南](ref/scripts-guide.md) - 5个脚本的完整使用说明（413行）
- 📗 [模型参考文档](ref/models-reference.md) - Pydantic模型详细说明（477行）
- 📙 [AI开发助手指南](CLAUDE.md) - AI辅助开发参考

### 详细文档
- 🏗️ [架构设计](ref/architecture.md) - 三层评估架构详解
- 🔧 [开发指南](ref/development.md) - 添加新功能、最佳实践
- 📖 [API参考](ref/api-reference.md) - Python API详细文档
- 🌟 [项目概览](ref/project-overview.md) - 快速了解项目

### 其他文档
- 📂 [项目结构说明](docs/project_structure.md)
- ✅ [开发任务清单](docs/script_eval_development_checklist.md)

## 技术栈

- **评估框架**: DeepEval 0.21+
- **LLM Provider**: DeepSeek API
- **数据验证**: Pydantic 2.5+
- **API客户端**: OpenAI Python SDK
- **配置管理**: PyYAML
- **数据处理**: Pandas, NumPy
- **测试框架**: Pytest

## 🗺️ 路线图

### ✅ 已完成（v0.2.0）
- [x] Pydantic V2完整迁移
- [x] 标准剧本和故事大纲双场景支持
- [x] 5个核心脚本（转换×2 + 评估×2 + 测试×1）
- [x] 三层评估架构（结构+统计+语义）
- [x] DeepSeek API集成
- [x] 输出目录重构（outputs/converted/ + outputs/reports/）
- [x] 完整参考文档系统（890行）
- [x] 批量处理支持

### 🚧 进行中（v0.3.0）
- [ ] 完整的单元测试覆盖（>80%）
- [ ] 性能优化（异步API调用）
- [ ] 缓存机制（减少重复API调用）
- [ ] HTML可视化报告

### 📋 未来计划（v1.0.0+）
- [ ] Web界面（剧本上传→转换→评估）
- [ ] 交互式评估仪表板
- [ ] 更多评估指标（MINEA、一致性检测）
- [ ] 支持更多LLM提供商（OpenAI、Claude）
- [ ] 多语言支持（英文剧本）

## 💡 项目工作原理

### 整体流程

```
输入剧本文本
    ↓
┌─────────────────────────────────────┐
│  步骤1: LLM转换（DeepSeek API）      │
│  - 使用prompt模板指导LLM             │
│  - 提取场景信息为JSON               │
│  - 温度: 0.1(标准) / 0.2(大纲)      │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  步骤2: 结构验证（Pydantic V2）     │
│  - SceneInfo / OutlineSceneInfo     │
│  - 字段格式、类型、必填项检查        │
│  - 验证成功率: 100%                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  步骤3: 三层评估                    │
│  ┌───────────────────────────────┐  │
│  │ 结构层: JSON schema验证        │  │
│  │ 得分: 1.0 or 0.0              │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 统计层: 场景边界 + 角色提取    │  │
│  │ 指标: F1, Precision, Recall   │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 语义层: LLM-as-Judge评估      │  │
│  │ 评估: 场景任务、关键事件等     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  步骤4: 分数聚合                    │
│  总分 = 结构×0.25 + 边界×0.25      │
│        + 角色×0.25 + 语义×0.25     │
└─────────────────────────────────────┘
    ↓
输出评估报告（JSON）+ 转换后的JSON
```

### 关键区别：标准剧本 vs 故事大纲

| 特性 | 标准剧本 | 故事大纲 |
|------|---------|---------|
| **scene_id** | S01, S02（严格） | S0, S1, S01（灵活） |
| **setting** | 必须包含"内/外" | 允许"推断："、None |
| **key_events** | 1-3个 | 1-5个 |
| **验证策略** | 严格错误 | 友好警告 |
| **prompt温度** | 0.1 | 0.2 |
| **使用脚本** | convert_script_to_json.py<br>run_full_evaluation.py | convert_outline_to_json.py<br>run_outline_evaluation.py |

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 如何贡献
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](https://github.com/your-repo/issues)
- 发起 [Pull Request](https://github.com/your-repo/pulls)

---

**开发团队** | 2025 | 基于DeepSeek API + DeepEval框架构建

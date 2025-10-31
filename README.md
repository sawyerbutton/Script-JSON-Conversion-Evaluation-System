# 剧本JSON转换评估系统

## 项目简介

这是一个基于 **DeepEval** 框架和 **DeepSeek API** 的自动化评估系统，用于验证将剧本文本转换为结构化JSON数据的质量。系统采用三层评估架构，结合规则验证、统计分析和LLM语义评估，提供全面的质量评估。

## 核心特性

- ✅ **三层评估架构**
  - 结构层：JSON格式、字段完整性验证
  - 统计层：场景边界、角色识别等指标
  - 语义层：LLM-as-Judge深度语义评估

- 🎯 **多场景支持**
  - 场景1：标准格式剧本转JSON
  - 场景2：故事大纲转JSON（更灵活的验证规则）

- 📊 **丰富的评估指标**
  - 场景边界准确性（F1, Precision, Recall）
  - 角色提取完整性和一致性
  - 语义准确性（场景任务、关键事件、信息变化、关系变化）
  - 自一致性评估（可选）

- 🤖 **DeepSeek集成**
  - OpenAI兼容的API封装
  - 智能重试机制
  - 成本追踪和控制
  - 缓存优化

- 📝 **详细的评估报告**
  - JSON格式详细报告
  - HTML可视化报告
  - 问题定位和改进建议

## 项目结构

```
script-evaluation-system/
│
├── src/                      # 源代码
│   ├── models/               # Pydantic数据模型
│   ├── metrics/              # 评估指标
│   ├── llm/                  # LLM集成
│   ├── evaluators/           # 评估器
│   └── utils/                # 工具函数
│
├── tests/                    # 测试文件
│   ├── unit/                 # 单元测试
│   ├── integration/          # 集成测试
│   └── test_data/            # 测试数据
│       ├── scene1/           # 场景1测试样本
│       └── scene2/           # 场景2测试样本
│
├── configs/                  # 配置文件
│   ├── default_config.yaml
│   ├── evaluation_weights.yaml
│   └── deepseek_config.yaml
│
├── prompts/                  # Prompt模板
│   ├── scene1_extraction.txt
│   ├── scene2_extraction.txt
│   ├── boundary_evaluation.txt
│   └── semantic_evaluation.txt
│
├── scripts/                  # 脚本文件
│   └── test_system.py        # 系统测试脚本
│
├── docs/                     # 文档
│   ├── README.md
│   ├── project_structure.md
│   ├── quick_start_guide.md
│   └── script_eval_development_checklist.md
│
├── code-samples/             # 代码示例
│
├── outputs/                  # 输出目录（自动生成）
│   ├── reports/
│   └── logs/
│
├── requirements.txt          # 依赖列表
├── .env.example              # 环境变量示例
└── README.md                 # 本文件
```

## 快速开始

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

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，添加你的 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 运行测试

```bash
# 运行系统测试（不需要API Key）
python scripts/test_system.py
```

### 4. 运行评估

```python
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig

# 配置评估器
config = EvaluationConfig(
    use_deepseek_judge=True,  # 启用LLM评估
    save_detailed_report=True
)

evaluator = ScriptEvaluator(config)

# 准备数据
test_case = {
    "source_text": "你的剧本文本...",
    "extracted_json": {...},  # 提取的JSON
    "scene_type": "standard",  # 或 "outline"
    "source_file": "test.txt"
}

# 运行评估
result = evaluator.evaluate_script(**test_case)

print(f"评估得分: {result.overall_score:.3f}")
print(f"质量级别: {result.quality_level}")
```

## 评估示例

### 输入数据

**剧本文本**（source_text）:
```
内景 咖啡馆 - 日

李雷坐在角落里，不安地看着手表。韩梅梅推门而入，表情冷漠。

韩梅梅
（冷淡地）
你想说什么？
...
```

**提取的JSON**（extracted_json）:
```json
[
  {
    "scene_id": "S01",
    "setting": "内景 咖啡馆 - 日",
    "characters": ["李雷", "韩梅梅"],
    "scene_mission": "展现两人关系的破裂",
    "key_events": ["韩梅梅冷漠地到来", "李雷试图解释被拒绝", "韩梅梅宣布分手离开"],
    ...
  }
]
```

### 输出结果

```
评估完成！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

文件: test_script_01.txt
质量级别: 优秀
总分: 0.875
通过: ✅ 是

各项得分:
  结构验证: 0.950
  场景边界: 0.850
  角色提取: 0.900
  语义准确: 0.800

统计信息:
  场景总数: 1
  角色总数: 2

改进建议:
  1. 场景任务描述准确到位
  2. 关键事件覆盖完整
```

## 核心模块说明

### 1. 数据模型 (src/models/)

使用 Pydantic 定义严格的数据模型：
- `SceneInfo`: 场景1（标准剧本）模型
- `OutlineSceneInfo`: 场景2（故事大纲）模型
- 自动验证字段格式、类型、取值范围

### 2. 评估指标 (src/metrics/)

实现多种评估指标：
- `SceneBoundaryMetric`: 场景边界评估
- `CharacterExtractionMetric`: 角色提取评估
- `SelfConsistencyMetric`: 自一致性评估

### 3. LLM集成 (src/llm/)

DeepSeek API客户端封装：
- OpenAI兼容接口
- 智能重试机制
- Token使用统计
- 成本追踪

### 4. 评估器 (src/evaluators/)

协调整个评估流程：
- 三层评估架构实现
- 分数聚合和权重管理
- 报告生成

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

## 文档

- 📖 [项目结构说明](docs/project_structure.md)
- 🚀 [快速开始指南](docs/quick_start_guide.md)
- ✅ [开发任务清单](docs/script_eval_development_checklist.md)

## 技术栈

- **评估框架**: DeepEval 0.21+
- **LLM Provider**: DeepSeek API
- **数据验证**: Pydantic 2.5+
- **API客户端**: OpenAI Python SDK
- **配置管理**: PyYAML
- **数据处理**: Pandas, NumPy
- **测试框架**: Pytest

## 路线图

### 已完成
- [x] 基础项目架构
- [x] Pydantic数据模型
- [x] DeepSeek客户端封装
- [x] 三层评估架构
- [x] 基础评估指标
- [x] 报告生成系统

### 进行中
- [ ] 完整的单元测试覆盖
- [ ] 批量评估脚本
- [ ] 性能优化（异步、缓存）

### 未来计划
- [ ] Web界面
- [ ] 评估结果可视化仪表板
- [ ] 更多评估指标（MINEA、异常检测等）
- [ ] 多语言支持
- [ ] Docker容器化部署

## 贡献

欢迎贡献代码、报告问题或提出建议！

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发起 Pull Request

---

**开发团队** | 2024

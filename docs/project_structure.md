# 剧本评估系统 - 项目结构

```
script-evaluation-system/
│
├── 📂 src/                          # 源代码目录
│   ├── 📂 models/                   # 数据模型
│   │   ├── scene_models.py          # Pydantic模型定义
│   │   ├── validation_rules.py      # 验证规则
│   │   └── __init__.py
│   │
│   ├── 📂 metrics/                  # 评估指标
│   │   ├── deepeval_metrics.py      # DeepEval自定义指标
│   │   ├── boundary_metrics.py      # 场景边界指标
│   │   ├── character_metrics.py     # 角色提取指标
│   │   ├── consistency_metrics.py   # 一致性指标
│   │   └── __init__.py
│   │
│   ├── 📂 llm/                      # LLM集成
│   │   ├── deepseek_client.py       # DeepSeek客户端
│   │   ├── prompt_templates.py      # Prompt模板
│   │   └── __init__.py
│   │
│   ├── 📂 evaluators/               # 评估器
│   │   ├── main_evaluator.py        # 主评估器
│   │   ├── structure_evaluator.py   # 结构评估
│   │   ├── semantic_evaluator.py    # 语义评估
│   │   └── __init__.py
│   │
│   └── 📂 utils/                    # 工具函数
│       ├── file_handler.py          # 文件处理
│       ├── report_generator.py      # 报告生成
│       ├── data_processor.py        # 数据处理
│       └── __init__.py
│
├── 📂 tests/                        # 测试文件
│   ├── 📂 unit/                     # 单元测试
│   │   ├── test_models.py
│   │   ├── test_metrics.py
│   │   └── test_client.py
│   │
│   ├── 📂 integration/              # 集成测试
│   │   └── test_evaluation_flow.py
│   │
│   └── 📂 test_data/                # 测试数据
│       ├── 📂 scene1/               # 场景1测试样本
│       │   ├── sample_01.txt
│       │   ├── sample_01.json
│       │   └── ...
│       │
│       └── 📂 scene2/               # 场景2测试样本
│           ├── outline_01.txt
│           ├── outline_01.json
│           └── ...
│
├── 📂 configs/                      # 配置文件
│   ├── default_config.yaml          # 默认配置
│   ├── evaluation_weights.yaml      # 评估权重
│   └── deepseek_config.yaml         # API配置
│
├── 📂 prompts/                      # Prompt文件
│   ├── scene1_extraction.txt        # 场景1提取prompt
│   ├── scene2_extraction.txt        # 场景2提取prompt
│   ├── boundary_evaluation.txt      # 边界评估prompt
│   └── semantic_evaluation.txt      # 语义评估prompt
│
├── 📂 outputs/                      # 输出目录
│   ├── 📂 reports/                  # 评估报告
│   │   ├── json/
│   │   └── html/
│   │
│   └── 📂 logs/                     # 日志文件
│       └── evaluation.log
│
├── 📂 docs/                         # 文档
│   ├── quick_start_guide.md         # 快速开始
│   ├── api_reference.md             # API文档
│   ├── evaluation_methodology.md    # 评估方法论
│   └── development_checklist.md     # 开发清单
│
├── 📂 scripts/                      # 脚本文件
│   ├── test_system.py               # 系统测试脚本
│   ├── batch_evaluate.py            # 批量评估脚本
│   └── generate_report.py           # 报告生成脚本
│
├── 📄 requirements.txt              # 依赖列表
├── 📄 .env.example                  # 环境变量示例
├── 📄 .gitignore                    # Git忽略文件
├── 📄 README.md                     # 项目说明
├── 📄 setup.py                      # 安装脚本
└── 📄 pyproject.toml               # 项目配置
```

## 核心模块说明

### 1. models/ - 数据模型层
负责定义和验证剧本JSON的数据结构：
- 使用Pydantic进行严格的类型检查
- 支持场景1（标准剧本）和场景2（故事大纲）两种模式
- 提供自定义验证规则

### 2. metrics/ - 评估指标层
实现各种评估指标：
- **结构指标**：JSON格式、字段完整性
- **语义指标**：内容准确性、逻辑一致性
- **统计指标**：分布特征、异常检测

### 3. llm/ - LLM集成层
处理与大语言模型的交互：
- DeepSeek API客户端封装
- Prompt模板管理
- 响应解析和错误处理

### 4. evaluators/ - 评估器层
协调整个评估流程：
- 三层评估架构实现
- 分数聚合和权重管理
- 评估结果封装

### 5. utils/ - 工具层
提供辅助功能：
- 文件读写处理
- 报告生成（JSON/HTML/PDF）
- 数据预处理和后处理

## 配置文件说明

### default_config.yaml
```yaml
evaluation:
  pass_threshold: 0.70
  excellent_threshold: 0.85
  use_deepseek_judge: true
  
api:
  model: deepseek-chat
  temperature: 0.1
  max_retries: 3
  
output:
  save_reports: true
  report_format: ["json", "html"]
```

### evaluation_weights.yaml
```yaml
weights:
  structure: 0.25
  boundary: 0.25
  character: 0.25
  semantic: 0.25
  
scene1:
  boundary_tolerance: 2
  min_characters: 1
  
scene2:
  boundary_tolerance: 3
  allow_inference: true
```

## 环境变量配置

创建 `.env` 文件：
```env
# API配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 路径配置
DATA_DIR=./data
OUTPUT_DIR=./outputs
LOG_DIR=./logs

# 调试配置
DEBUG=false
LOG_LEVEL=INFO
```

## 命令行使用

### 单文件评估
```bash
python scripts/evaluate.py --input sample.txt --json sample.json --type scene1
```

### 批量评估
```bash
python scripts/batch_evaluate.py --dir ./test_data/scene1/ --output ./reports/
```

### 生成报告
```bash
python scripts/generate_report.py --results ./outputs/results.json --format html
```

## 开发工作流

### 1. 初始设置
```bash
git clone <repository>
cd script-evaluation-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑.env添加API密钥
```

### 2. 运行测试
```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 系统测试
python scripts/test_system.py
```

### 3. 开发新功能
1. 在相应模块创建新文件
2. 编写单元测试
3. 实现功能
4. 运行测试验证
5. 更新文档

### 4. 提交代码
```bash
git add .
git commit -m "feat: 添加新评估指标"
git push
```

## 最佳实践

### 代码组织
- 每个类一个文件
- 模块之间低耦合
- 使用依赖注入
- 编写完整的docstring

### 错误处理
- 使用自定义异常类
- 记录详细的错误日志
- 提供用户友好的错误信息
- 实现优雅的降级策略

### 性能优化
- 缓存API响应
- 批量处理请求
- 使用异步IO
- 监控内存使用

### 测试策略
- 单元测试覆盖率>80%
- 集成测试覆盖主流程
- 使用mock避免API调用
- 定期运行回归测试

## 部署清单

- [ ] 环境变量配置完成
- [ ] 所有测试通过
- [ ] 文档更新完成
- [ ] 性能基准测试通过
- [ ] 日志配置正确
- [ ] 错误处理完善
- [ ] 监控告警设置
- [ ] 备份策略确定

## 维护指南

### 日常维护
- 监控API使用量
- 检查错误日志
- 更新评估权重
- 优化Prompt模板

### 定期任务
- 每周：分析评估报告，识别改进点
- 每月：更新依赖包，进行安全扫描
- 每季：收集用户反馈，规划新功能

### 故障排查
1. 检查日志文件
2. 验证API连接
3. 检查数据格式
4. 测试单个组件
5. 逐步调试流程

---

通过这个结构，您可以构建一个模块化、可维护、易扩展的剧本评估系统。

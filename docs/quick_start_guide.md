# 剧本评估系统 - 快速启动指南

## 项目文件说明

您已获得以下开发资源：

### 📋 核心文档
- `script_eval_development_checklist.md` - **详细的开发任务清单**（28天开发计划）
- `script_evaluation_report_cn.md` - **评估方法论中文报告**（理论基础）

### 💻 代码示例

#### 1. 客户端与配置
- `deepseek_client.py` - DeepSeek API客户端封装
  - 兼容OpenAI格式
  - 包含重试机制
  - Token计费追踪

#### 2. 数据模型
- `scene_models.py` - Pydantic数据模型
  - 场景1（标准剧本）模型
  - 场景2（故事大纲）模型
  - 数据验证函数

#### 3. 评估指标
- `deepeval_metrics.py` - DeepEval自定义指标
  - 场景边界评估
  - 角色提取评估
  - 自一致性评估

#### 4. 主程序
- `main_evaluator.py` - 完整评估流程
  - 多层评估架构
  - 报告生成
  - 批量处理

## 快速开始步骤

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install deepeval==0.21.0
pip install pydantic==2.5.0
pip install openai
pip install python-dotenv
pip install pandas numpy
pip install rich
```

### 2. 配置API

创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 3. 运行第一个评估

```python
from main_evaluator import ScriptEvaluator, EvaluationConfig

# 配置
config = EvaluationConfig(
    use_deepseek_judge=True,
    save_detailed_report=True
)

# 创建评估器
evaluator = ScriptEvaluator(config)

# 准备测试数据
test_case = {
    "source_text": "你的剧本文本...",
    "extracted_json": {...},  # 提取的JSON
    "scene_type": "standard",
    "file_name": "test.txt"
}

# 运行评估
result = evaluator.evaluate_script(**test_case)
print(f"评估得分: {result.overall_score:.3f}")
print(f"质量级别: {result.quality_level}")
```

## 开发优先级建议

### 第1周重点
1. ✅ 搭建基础环境
2. ✅ 实现Pydantic模型验证
3. ✅ 完成结构层评估

### 第2周重点
1. 实现LLM-as-Judge
2. 集成DeepSeek API
3. 开发核心评估指标

### 第3周重点
1. 实现自一致性检查
2. 添加MINEA测试
3. 完成报告生成

### 第4周重点
1. 性能优化
2. 批量处理
3. 部署准备

## 关键决策点

### 1. DeepSeek模型选择
- **deepseek-chat**: 用于语义评估（推荐）
- **deepseek-coder**: 用于JSON结构分析

### 2. 评估权重配置
```python
# 建议初始权重
structure_weight = 0.25  # 结构验证
boundary_weight = 0.25   # 场景边界
character_weight = 0.25  # 角色提取
semantic_weight = 0.25   # 语义准确
```

### 3. 成本控制
- 开发阶段使用小样本（5-10个）
- 使用缓存避免重复调用
- 监控Token使用量

## 测试数据准备

### 场景1示例（标准剧本）
```json
{
  "scene_id": "S01",
  "setting": "内景 咖啡馆 - 日",
  "characters": ["李雷", "韩梅梅"],
  "scene_mission": "展现关系危机",
  "key_events": ["争吵爆发", "分手宣言"],
  "info_change": [...],
  "relation_change": [...],
  "key_object": [...],
  "setup_payoff": {...}
}
```

### 场景2示例（故事大纲）
```json
{
  "scene_id": "S1",
  "setting": "推断：办公室",
  "characters": ["主角"],
  "scene_mission": "建立人物背景",
  "key_events": ["接到神秘电话"],
  ...
}
```

## 常见问题解决

### Q1: DeepSeek API调用失败
- 检查API Key是否正确
- 确认网络连接
- 查看是否触发限流

### Q2: 评估分数异常低
- 检查JSON格式是否符合schema
- 验证场景ID格式
- 确认必需字段完整

### Q3: 内存占用过高
- 减少并发请求数
- 使用批处理而非全量加载
- 清理缓存数据

## 后续优化方向

1. **性能优化**
   - 实现异步API调用
   - 添加结果缓存层
   - 优化批处理逻辑

2. **功能扩展**
   - 支持更多剧本格式
   - 添加可视化报告
   - 实现增量评估

3. **质量提升**
   - 收集人工标注数据
   - 优化评估Prompt
   - 调整权重配置

## 联系与支持

如需进一步帮助，可以：
1. 查阅详细开发清单：`script_eval_development_checklist.md`
2. 参考理论报告：`script_evaluation_report_cn.md`
3. 运行示例代码进行实验

祝您开发顺利！🎬

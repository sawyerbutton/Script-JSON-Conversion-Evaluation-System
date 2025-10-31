# 剧本JSON转换评估系统 - 开发任务清单

## 项目概览
- **框架**: DeepEval
- **LLM Provider**: DeepSeek API
- **目标**: 构建自动化评估系统，验证剧本到JSON转换的质量
- **场景**: 场景1（标准剧本→JSON）、场景2（故事大纲→JSON）

---

## 阶段一：环境搭建与基础配置 (Day 1-2)

### 1.1 项目初始化
```bash
# 任务清单
□ 创建项目目录结构
  ├── src/
  │   ├── models/          # Pydantic模型定义
  │   ├── metrics/         # 自定义评估指标
  │   ├── prompts/         # Prompt模板
  │   ├── validators/      # 验证器
  │   └── utils/           # 工具函数
  ├── tests/
  │   ├── test_data/       # 测试数据
  │   └── unit_tests/      # 单元测试
  ├── configs/             # 配置文件
  ├── outputs/             # 输出结果
  └── docs/               # 文档
  
□ 初始化Git仓库
□ 创建.env文件配置
□ 创建requirements.txt
```

### 1.2 依赖安装
```python
# requirements.txt 内容
□ 安装核心依赖
  - deepeval==0.21.0+     # 评估框架
  - pydantic==2.5.0+      # 数据验证
  - openai==1.0.0+        # DeepSeek兼容的OpenAI客户端
  - python-dotenv         # 环境变量
  - pandas                # 数据处理
  - numpy                 # 数值计算
  - pytest               # 测试框架
  - rich                 # 美化输出
  - jsonschema          # JSON验证
```

### 1.3 DeepSeek API配置
```python
# 任务清单
□ 创建 configs/deepseek_config.py
  - API endpoint配置
  - 模型选择（deepseek-chat/deepseek-coder）
  - 温度参数设置（评估用0.0-0.25）
  - 重试机制配置
  
□ 创建 src/llm/deepseek_client.py
  - OpenAI兼容客户端初始化
  - 请求封装
  - 错误处理
  - Token计数和成本追踪
```

### 1.4 DeepEval初始化
```python
# 任务清单
□ 配置 deepeval_config.py
  - 设置评估模型
  - 配置输出格式
  - 设置缓存策略
  
□ 创建自定义LLM包装器
  - 继承DeepEval的BaseLLM
  - 实现DeepSeek调用接口
  - 添加请求日志
```

---

## 阶段二：数据模型与验证层 (Day 3-4)

### 2.1 Pydantic模型定义
```python
# 任务清单
□ 创建 models/scene_models.py - 场景1剧本模型
  - SceneInfo模型
    * scene_id: str (格式验证: E01S01)
    * setting: str (验证INT/EXT格式)
    * characters: List[str] (非空验证)
    * scene_mission: str
    * key_events: List[str] (1-3个事件)
    * info_change: List[InfoChange]
    * relation_change: List[RelationChange]
    * key_object: List[KeyObject]
    * setup_payoff: SetupPayoff
    
□ 创建 models/outline_models.py - 场景2大纲模型
  - 与场景1类似但允许更灵活的字段
  
□ 创建验证器集合 validators/
  - scene_id_validator.py (格式验证)
  - character_validator.py (角色一致性)
  - temporal_validator.py (时序逻辑)
  - relationship_validator.py (关系合理性)
```

### 2.2 JSON Schema生成
```python
# 任务清单
□ 自动生成JSON Schema
  - 从Pydantic模型导出Schema
  - 创建验证函数
  - 错误信息本地化（中文）
  
□ 创建 validators/schema_validator.py
  - 结构验证
  - 字段完整性检查
  - 类型检查
  - 值范围验证
```

---

## 阶段三：核心评估指标开发 (Day 5-8)

### 3.1 场景分割评估指标
```python
# 任务清单
□ 创建 metrics/scene_boundary_metrics.py
  - SceneBoundaryF1Metric类
    * 实现off-by-n容差算法
    * 计算精确率和召回率
    * 支持部分匹配评分
  
  - SceneCountAccuracyMetric类
    * 场景数量准确性
    * 绝对/相对误差计算
    
  - SceneSequenceMetric类
    * 时序一致性检查
    * 场景转换合理性
```

### 3.2 角色识别评估指标
```python
# 任务清单
□ 创建 metrics/character_metrics.py
  - CharacterRecallMetric类
    * 主要角色识别率
    * 次要角色覆盖度
    
  - CharacterNetworkMetric类
    * 中心性度量计算
    * 关系网络密度分析
    * 角色重要性排序验证
    
  - NameNormalizationMetric类
    * 共指消解准确性
    * 别名/昵称处理
```

### 3.3 事件与关系评估指标
```python
# 任务清单
□ 创建 metrics/event_metrics.py
  - EventExtractionF1Metric类
    * 事件触发词识别
    * 事件类型分类准确性
    * 参与者角色提取
    
□ 创建 metrics/relationship_metrics.py  
  - RelationshipChangeMetric类
    * 关系演变合理性
    * 时间对应性验证
    * 因果链完整性检查
```

### 3.4 信息差与伏笔评估
```python
# 任务清单
□ 创建 metrics/narrative_metrics.py
  - InformationGapMetric类
    * 信息变化追踪
    * 角色认知状态验证
    
  - SetupPayoffMetric类
    * 伏笔-回收对应关系
    * 跨场景引用验证
```

---

## 阶段四：LLM-as-Judge实现 (Day 9-12)

### 4.1 评估Prompt模板设计
```python
# 任务清单
□ 创建 prompts/evaluation_prompts.py
  - SceneBoundaryEvalPrompt
    * 场景划分合理性判断模板
    * 评分标准说明
    * CoT推理步骤
    
  - CharacterConsistencyEvalPrompt
    * 角色一致性评估模板
    * 多维度评分指导
    
  - NarrativeCoherenceEvalPrompt
    * 叙事连贯性评估模板
    * 逻辑检查要点
    
  - SemanticAccuracyEvalPrompt
    * 语义准确性评估模板
    * 源文本对照验证
```

### 4.2 DeepEval自定义指标
```python
# 任务清单
□ 创建 metrics/llm_judge_metrics.py
  - 继承DeepEval的BaseMetric
  
  - SceneBoundaryJudge类
    * 集成DeepSeek API
    * 实现score()方法
    * 添加reasoning输出
    
  - CharacterExtractionJudge类
    * 多轮对话验证
    * 一致性检查
    
  - OverallQualityJudge类
    * 综合质量评分
    * 多维度聚合
```

### 4.3 偏见缓解机制
```python
# 任务清单
□ 实现偏见缓解策略
  - 位置随机化（避免位置偏见）
  - 多次运行取中位数（减少随机性）
  - 温度参数优化（0.0-0.25）
  - 评分校准函数
```

---

## 阶段五：无监督评估方法 (Day 13-15)

### 5.1 自一致性检查
```python
# 任务清单
□ 创建 metrics/consistency_metrics.py
  - SelfConsistencyMetric类
    * 多次提取运行（5-10次）
    * 字段级一致性计算
    * 投票机制实现
    * 置信度评分
```

### 5.2 MINEA合成测试
```python
# 任务清单
□ 创建 utils/synthetic_data_generator.py
  - 合成场景生成器
    * 创建简单场景标题
    * 生成明确角色对话
    * 插入关键事件
    
□ 创建 metrics/minea_metric.py
  - 合成数据注入
  - 提取成功率测量
  - 错误模式分析
```

### 5.3 统计异常检测
```python
# 任务清单
□ 创建 metrics/anomaly_detection.py
  - 使用Isolation Forest
  - 特征工程：
    * 场景长度分布
    * 角色数量
    * 对话密度
    * 关系复杂度
  - 异常评分和阈值设定
```

---

## 阶段六：聚合与报告系统 (Day 16-18)

### 6.1 分数聚合策略
```python
# 任务清单
□ 创建 scoring/aggregator.py
  - WeightedSumAggregator类
    * 可配置权重
    * 归一化处理
    
  - GeometricMeanAggregator类
    * 非补偿性聚合
    * 最低阈值保证
    
  - HierarchicalAggregator类
    * 多层聚合
    * 维度分组
```

### 6.2 评分校准
```python
# 任务清单
□ 创建 scoring/calibration.py
  - 线性校准
  - 等渗回归
  - Beta校准
  - 与人工标注对齐（如有）
```

### 6.3 报告生成
```python
# 任务清单
□ 创建 reporting/report_generator.py
  - 详细评估报告
    * 总体分数
    * 各维度分数
    * 问题定位
    * 改进建议
    
  - 可视化仪表板
    * 雷达图（多维度）
    * 趋势图（时间序列）
    * 热力图（错误分布）
    
  - 导出格式
    * JSON详细报告
    * HTML可视化报告
    * CSV数据导出
```

---

## 阶段七：测试与优化 (Day 19-21)

### 7.1 单元测试
```python
# 任务清单
□ 编写测试用例 tests/
  - test_models.py (模型验证)
  - test_metrics.py (指标计算)
  - test_llm_judge.py (LLM评估)
  - test_aggregation.py (聚合逻辑)
  
□ 集成测试
  - 端到端流程测试
  - 性能基准测试
  - 错误恢复测试
```

### 7.2 性能优化
```python
# 任务清单
□ 并发处理优化
  - 批量API调用
  - 异步处理
  - 结果缓存
  
□ 成本优化
  - Token使用监控
  - 智能采样策略
  - 缓存复用
```

### 7.3 错误处理
```python
# 任务清单
□ 完善错误处理机制
  - API失败重试
  - 部分失败恢复
  - 详细错误日志
  - 用户友好提示
```

---

## 阶段八：集成与部署 (Day 22-24)

### 8.1 CLI工具
```python
# 任务清单
□ 创建 cli.py
  - 命令行接口
  - 批量处理模式
  - 交互式模式
  - 进度显示
```

### 8.2 配置管理
```python
# 任务清单
□ 创建配置系统
  - YAML配置文件
  - 环境变量覆盖
  - 配置验证
  - 配置模板
```

### 8.3 Docker化
```python
# 任务清单
□ 创建Docker配置
  - Dockerfile
  - docker-compose.yml
  - 环境隔离
  - 批量处理脚本
```

---

## 阶段九：实验与验证 (Day 25-28)

### 9.1 基准测试
```python
# 任务清单
□ 建立基准数据集
  - 收集5个场景1样本
  - 收集5个场景2样本
  - 人工标注（可选）
  
□ 运行基准测试
  - 记录各指标表现
  - 分析错误模式
  - 识别改进点
```

### 9.2 A/B测试
```python
# 任务清单
□ 对比不同配置
  - 不同权重组合
  - 不同LLM温度
  - 不同聚合策略
  
□ 统计分析
  - 显著性检验
  - 效果量计算
  - 最优配置选择
```

### 9.3 迭代优化
```python
# 任务清单
□ 根据测试结果优化
  - Prompt调优
  - 权重调整
  - 阈值优化
  - 规则完善
```

---

## 特殊考虑事项

### DeepSeek API特殊配置
```python
# 任务清单
□ DeepSeek特定优化
  - 使用deepseek-chat模型进行语义评估
  - 使用deepseek-coder分析JSON结构
  - 中文Prompt优化
  - Token定价优化策略
  
□ API限流处理
  - 请求频率控制
  - 并发数限制
  - 自动降级策略
```

### 场景1 vs 场景2差异化处理
```python
# 任务清单
□ 场景1（标准剧本）特殊处理
  - 严格的场景标题格式验证
  - 对话格式标准化检查
  - 场景转换明确性验证
  
□ 场景2（故事大纲）特殊处理
  - 更灵活的边界判断
  - 隐含信息推理验证
  - 时序重建准确性
```

---

## 代码示例模板

### 主评估流程
```python
# main.py 示例结构
class ScriptEvaluator:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.deepseek_client = DeepSeekClient(self.config)
        self.metrics = self._initialize_metrics()
        
    def evaluate_scene1(self, script_text: str, json_output: dict):
        """评估场景1：标准剧本转JSON"""
        results = {}
        
        # 第1层：结构验证
        structure_score = self.validate_structure(json_output)
        
        # 第2层：统计检查
        statistical_score = self.run_statistical_checks(json_output)
        
        # 第3层：LLM语义评估
        semantic_score = self.run_llm_evaluation(script_text, json_output)
        
        # 聚合分数
        final_score = self.aggregate_scores(
            structure_score, 
            statistical_score, 
            semantic_score
        )
        
        return EvaluationResult(
            score=final_score,
            details=results,
            recommendations=self.generate_recommendations(results)
        )
```

### DeepEval集成示例
```python
# deepeval_integration.py
from deepeval import evaluate
from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

class SceneBoundaryMetric(BaseMetric):
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.deepseek_client = DeepSeekClient()
        
    async def a_measure(self, test_case: LLMTestCase):
        # 实现异步评估逻辑
        prompt = self.build_evaluation_prompt(
            test_case.input,
            test_case.actual_output
        )
        
        response = await self.deepseek_client.async_complete(prompt)
        score = self.parse_score(response)
        
        self.score = score
        self.reason = response.get("reasoning", "")
        self.success = score >= self.threshold
        
        return self.score
```

---

## 交付物清单

### 必需交付
```
□ 源代码（完整注释）
□ 配置文件模板
□ 测试数据集
□ 使用文档
□ API文档
□ 性能报告
```

### 可选交付
```
□ Docker镜像
□ CI/CD配置
□ 监控仪表板
□ 培训材料
```

---

## 时间线建议

**第1周**: 环境搭建 + 数据模型
**第2周**: 核心指标 + LLM-as-Judge  
**第3周**: 无监督方法 + 聚合系统
**第4周**: 测试优化 + 部署准备

---

## 注意事项

1. **优先级**: 先实现场景1，场景2可以复用大部分代码
2. **成本控制**: 开发阶段使用小数据集，避免API费用过高
3. **版本控制**: 保存所有Prompt版本，便于对比优化
4. **监控**: 记录所有API调用，便于成本分析和调试
5. **文档**: 边开发边文档化，特别是评估逻辑的设计决策

---

## 风险管理

1. **API不稳定**: 实现本地缓存和降级方案
2. **成本超支**: 设置费用预警和限制
3. **性能瓶颈**: 准备异步和批处理方案
4. **评估偏差**: 保留人工审核接口

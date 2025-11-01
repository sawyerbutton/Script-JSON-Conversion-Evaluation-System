# Scripts Guide

Complete guide to all conversion and evaluation scripts in the system.

## Overview

The system provides 5 main scripts for different workflows:

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `test_system.py` | System validation | None | Test results |
| `convert_script_to_json.py` | Script → JSON | Script file | JSON file |
| `convert_outline_to_json.py` | Outline → JSON | Outline file | JSON file |
| `run_full_evaluation.py` | Script → JSON → Evaluation | Script file | JSON + Report |
| `run_outline_evaluation.py` | Outline → JSON → Evaluation | Outline file | JSON + Report |

---

## 1. System Test Script

**File:** `scripts/test_system.py`

**Purpose:** Validate that the system is working correctly without API calls.

### Usage

```bash
python scripts/test_system.py
```

### What it Tests

1. **File Handler** - JSON read/write operations
2. **Model Validation** - Pydantic schema validation
3. **Basic Evaluation** - End-to-end evaluation flow (no LLM)

### Expected Output

```
✅ 所有测试通过！系统运行正常。
```

---

## 2. Script to JSON Converter

**File:** `scripts/convert_script_to_json.py`

**Purpose:** Convert standard script format to structured JSON.

### Usage

```bash
# Basic conversion
python scripts/convert_script_to_json.py input_script.md

# With custom output path
python scripts/convert_script_to_json.py input_script.md -o output.json

# Skip validation (faster)
python scripts/convert_script_to_json.py input_script.md --no-validate
```

### Parameters

- `input_file` (required) - Path to script file
- `-o, --output` - Output JSON path (default: `{input_stem}.json`)
- `-t, --type` - Scene type: `standard` or `outline` (default: `standard`)
- `--no-validate` - Skip JSON validation

### Input Format

Standard script with scene markers:

```
内景 咖啡馆 - 日

李雷坐在角落里，不安地看着手表。韩梅梅推门而入，表情冷漠。

韩梅梅
（冷淡地）
你想说什么？
...
```

### Output Format

```json
[
  {
    "scene_id": "S01",
    "setting": "内景 咖啡馆 - 日",
    "characters": ["李雷", "韩梅梅"],
    "scene_mission": "展现两人关系的破裂",
    "key_events": ["韩梅梅冷漠地到来", ...],
    ...
  }
]
```

### API Usage

- Uses DeepSeek API via `scene1_extraction.txt` prompt
- Temperature: 0.1 (low for consistency)
- Max tokens: 4000

---

## 3. Outline to JSON Converter

**File:** `scripts/convert_outline_to_json.py`

**Purpose:** Convert story outlines to structured JSON with flexible validation.

### Usage

```bash
# Basic conversion
python scripts/convert_outline_to_json.py story_outline.md

# With custom output
python scripts/convert_outline_to_json.py outline.md -o result.json
```

### Parameters

Same as script converter, but always uses `outline` scene type.

### Input Format

Flexible story outline:

```markdown
## 背景设定
2145年，人类发明了时间旅行技术...

## 第一幕：发现异常
林悦接到任务，2025年出现了多个时间线异常波动...
```

### Output Format

More flexible than standard scripts:

```json
[
  {
    "scene_id": "S0",  // ✅ Allows S0, S1 format
    "setting": "背景说明",  // ✅ No "内/外" required
    "characters": ["林悦"],
    "scene_mission": "建立故事世界观",
    "key_events": [  // ✅ Allows 1-5 events
      "介绍时空背景",
      "说明主要设定",
      ...
    ],
    ...
  }
]
```

### Key Differences from Script Converter

| Feature | Script | Outline |
|---------|--------|---------|
| scene_id | S01, S02 | S0, S1, S01 all valid |
| setting | Must have "内/外" | Can be "推断：..." or "背景说明" |
| key_events | 1-3 items | 1-5 items |
| Validation | Strict | Flexible |

### API Usage

- Uses `scene2_extraction.txt` prompt
- Temperature: 0.2 (slightly higher for inference)
- Max tokens: 4000

---

## 4. Full Script Evaluation

**File:** `scripts/run_full_evaluation.py`

**Purpose:** Complete pipeline from script to JSON to quality report.

### Usage

```bash
# Default (with LLM semantic evaluation)
python scripts/run_full_evaluation.py script.md

# Without LLM evaluation (faster, cheaper)
python scripts/run_full_evaluation.py script.md --no-llm-judge

# Don't save JSON
python scripts/run_full_evaluation.py script.md --no-save-json
```

### Parameters

- `script_file` (required) - Path to script file
- `-t, --type` - Scene type: `standard` or `outline`
- `--no-llm-judge` - Disable LLM semantic evaluation
- `--no-save-json` - Don't save converted JSON

### Workflow

```
1. Read script file
2. Convert to JSON using DeepSeek API
3. Validate JSON structure
4. Run evaluation (structure + stats + optional LLM)
5. Generate report
```

### Output

**Console Output:**
```
======================================================================
评估结果
======================================================================

文件: script.md
质量级别: 优秀
总分: 0.865

各项得分:
  结构验证: 1.000
  场景边界: 1.000
  角色提取: 0.709
  语义准确: 0.750
```

**Generated Files:**
- `{script_stem}_output.json` - Converted JSON
- `evaluation_results/report_{timestamp}.json` - Detailed report

### Evaluation Metrics

| Metric | Weight | Description |
|--------|--------|-------------|
| Structure | 0.25 | JSON schema validation |
| Boundary | 0.25 | Scene boundary F1 score |
| Character | 0.25 | Character extraction accuracy |
| Semantic | 0.25 | LLM-judged semantic quality |

### Quality Levels

- **优秀 (Excellent)**: ≥ 0.85
- **良好 (Good)**: ≥ 0.70
- **合格 (Pass)**: ≥ 0.60
- **不合格 (Fail)**: < 0.60

---

## 5. Full Outline Evaluation

**File:** `scripts/run_outline_evaluation.py`

**Purpose:** Complete pipeline for story outlines with flexible validation.

### Usage

```bash
# Default (with LLM evaluation)
python scripts/run_outline_evaluation.py outline.md

# Without LLM (faster)
python scripts/run_outline_evaluation.py outline.md --no-llm-judge
```

### Parameters

Same as full script evaluation.

### Workflow

Same as script evaluation but uses:
- `convert_outline_to_json()` for conversion
- `OutlineSceneInfo` model for validation
- `scene_type="outline"` for evaluation

### Output

Additional outline-specific info:

```
大纲特点:
  推断的场景设置: 3/5
```

---

## Common Patterns

### Batch Processing

```bash
# Process all scripts
for file in scripts/*.md; do
    python scripts/run_full_evaluation.py "$file"
done

# Process all outlines
for file in outlines/*.md; do
    python scripts/run_outline_evaluation.py "$file"
done
```

### Conversion Only (No Evaluation)

```bash
# Convert multiple files
for file in *.md; do
    python scripts/convert_script_to_json.py "$file"
done
```

### Testing Without API Costs

```bash
# Use --no-llm-judge to skip semantic evaluation
python scripts/run_full_evaluation.py test.md --no-llm-judge
```

---

## Error Handling

### Common Errors

1. **Missing API Key**
   ```
   Error: DEEPSEEK_API_KEY not found
   Solution: Add key to .env file
   ```

2. **JSON Parse Error**
   ```
   Error: JSON解析失败
   Solution: Check LLM output, may need to retry
   ```

3. **Validation Error**
   ```
   Error: 场景ID格式错误
   Solution: For outlines, this is expected; model auto-fixes
   ```

### Debug Mode

All scripts support verbose logging via environment variable:

```bash
export LOG_LEVEL=DEBUG
python scripts/run_full_evaluation.py script.md
```

---

## Cost Estimation

### API Calls Per Script

| Script | API Calls | Typical Tokens |
|--------|-----------|----------------|
| `convert_script_to_json.py` | 1 | 2000-4000 |
| `convert_outline_to_json.py` | 1 | 1500-3000 |
| `run_full_evaluation.py` (no LLM) | 1 | 2000-4000 |
| `run_full_evaluation.py` (with LLM) | 4 | 6000-10000 |
| `run_outline_evaluation.py` (with LLM) | 4 | 5000-8000 |

### Cost Example (DeepSeek Pricing)

Assuming ¥1/1M input tokens, ¥2/1M output tokens:

- Single script conversion: ~¥0.01
- Full evaluation with LLM: ~¥0.03-0.05
- 100 scripts: ~¥3-5

---

## Best Practices

### 1. Start with System Test

Always run `test_system.py` first to ensure setup is correct.

### 2. Test with --no-llm-judge

For initial testing, use `--no-llm-judge` to save API costs.

### 3. Validate Small Samples

Test on 2-3 files before batch processing.

### 4. Use Appropriate Script Type

- Standard scripts → `run_full_evaluation.py`
- Story outlines → `run_outline_evaluation.py`

### 5. Check Generated JSON

Always inspect a few generated JSON files to ensure quality.

---

## Related Documentation

- [API Reference](./api-reference.md) - Python API details
- [Architecture](./architecture.md) - System design
- [Development Guide](./development.md) - Adding new scripts

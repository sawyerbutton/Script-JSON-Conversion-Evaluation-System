# System Architecture

## Three-Tier Evaluation Architecture

### 1. Structure Layer (`src/models/`)
**Purpose**: Validate JSON format and schema compliance

**Components**:
- `SceneInfo`: Standard script scene model (Pydantic)
- `OutlineSceneInfo`: Story outline scene model (Pydantic)

**Validation**:
- JSON schema validation
- Required field presence
- Data type checking
- Value range constraints

**Files**:
- `src/models/scene_models.py` - Data model definitions
- `src/models/__init__.py` - Model exports

---

### 2. Statistical Layer (`src/metrics/`)
**Purpose**: Measure extraction quality with quantitative metrics

**Metrics Implemented**:
- **Scene Boundary Metrics**:
  - Precision, Recall, F1 score
  - Boundary tolerance configuration
- **Character Extraction Metrics**:
  - Completeness
  - Consistency
- **Self-Consistency Metrics** (optional)

**Files**:
- `src/metrics/deepeval_metrics.py` - Custom DeepEval metrics
- `src/metrics/__init__.py` - Metrics exports

---

### 3. Semantic Layer (`src/llm/` + `src/evaluators/`)
**Purpose**: Deep semantic validation using LLM-as-Judge

**Evaluation Aspects**:
- Scene mission accuracy
- Key events coverage
- Information changes tracking
- Relationship changes tracking

**Components**:
- DeepSeek API client with OpenAI compatibility
- Prompt template management
- Smart retry mechanism
- Token and cost tracking

**Files**:
- `src/llm/deepseek_client.py` - DeepSeek API client
- `src/evaluators/main_evaluator.py` - Main orchestrator
- `prompts/semantic_evaluation.txt` - Semantic evaluation prompts

---

## Data Flow

```
Input (Script Text + Extracted JSON)
           ↓
    ┌──────────────────┐
    │ Main Evaluator   │
    └──────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ 1. Structure Validation          │
    │    (Pydantic Models)             │
    └──────────────────────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ 2. Statistical Metrics           │
    │    (Boundary, Character, etc.)   │
    └──────────────────────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ 3. Semantic Evaluation           │
    │    (DeepSeek LLM-as-Judge)       │
    └──────────────────────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ Score Aggregation                │
    │ (Weighted by config)             │
    └──────────────────────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ Report Generation                │
    │ (JSON/HTML)                      │
    └──────────────────────────────────┘
           ↓
      Output Results
```

## Configuration System

### Location: `configs/`

**File Breakdown**:

1. **`default_config.yaml`**
   - Pass threshold (0.70)
   - Excellence threshold (0.85)
   - API model selection
   - Output formats

2. **`evaluation_weights.yaml`**
   - Layer weights (structure, boundary, character, semantic)
   - Scene-specific tolerances
   - Validation rules

3. **`deepseek_config.yaml`**
   - API endpoint configuration
   - Model parameters (temperature, retries)
   - Cost tracking settings
   - Rate limiting

## Prompt Management

### Location: `prompts/`

**Template Files**:
- `scene1_extraction.txt` - Standard script extraction
- `scene2_extraction.txt` - Story outline extraction
- `boundary_evaluation.txt` - Scene boundary evaluation
- `semantic_evaluation.txt` - Semantic accuracy evaluation

**Design Pattern**:
- Structured prompt templates with clear evaluation criteria
- Output format specifications
- Few-shot examples embedded

## Evaluation Workflow

### Entry Point: `src/evaluators/main_evaluator.py`

```python
ScriptEvaluator.evaluate_script(
    source_text: str,
    extracted_json: dict,
    scene_type: str,  # "standard" or "outline"
    source_file: str
) -> EvaluationResult
```

**Orchestration Steps**:
1. Load configuration from YAML files
2. Validate structure with Pydantic models
3. Calculate statistical metrics (boundary, character)
4. Perform semantic evaluation via DeepSeek API
5. Aggregate scores with configured weights
6. Determine quality level (Excellent/Good/Pass/Fail)
7. Generate detailed reports
8. Return structured results

## Integration Points

### DeepSeek API Integration
- **Client**: `src/llm/deepseek_client.py`
- **API Style**: OpenAI-compatible
- **Features**:
  - Automatic retries with exponential backoff
  - Token usage tracking
  - Cost calculation
  - Response caching (optional)

### DeepEval Framework Integration
- Custom metric implementations
- Test case management
- Batch evaluation support
- Report generation utilities

## Extensibility

### Adding New Metrics
1. Create new metric class in `src/metrics/`
2. Inherit from `deepeval.metrics.BaseMetric`
3. Implement `measure()` and `a_measure()` methods
4. Register in main evaluator
5. Update weight configuration

### Adding New Scene Types
1. Define Pydantic model in `src/models/scene_models.py`
2. Create extraction prompt in `prompts/`
3. Add validation rules in `configs/evaluation_weights.yaml`
4. Update main evaluator to handle new type

### Custom LLM Providers
1. Create new client in `src/llm/`
2. Implement OpenAI-compatible interface
3. Update configuration files
4. Modify evaluator to use new client

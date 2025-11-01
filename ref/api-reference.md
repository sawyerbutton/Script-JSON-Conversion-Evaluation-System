# API Reference

## Core Modules

### Data Models (`src/models/scene_models.py`)

#### SceneInfo
Pydantic model for standard script scenes.

```python
from src.models.scene_models import SceneInfo

class SceneInfo(BaseModel):
    scene_id: str              # Scene identifier (e.g., "S01")
    setting: str               # Scene setting/location
    characters: List[str]      # Character names in scene
    scene_mission: str         # Main purpose of the scene
    key_events: List[str]      # Major events in the scene
    info_changes: List[str]    # Information revealed
    relation_changes: List[str] # Relationship changes

# Usage
scene = SceneInfo(
    scene_id="S01",
    setting="Interior Cafe - Day",
    characters=["Alice", "Bob"],
    scene_mission="Introduce conflict",
    key_events=["Bob arrives late", "Alice confronts Bob"],
    info_changes=["Bob has been lying"],
    relation_changes=["Trust between Alice and Bob deteriorates"]
)
```

#### OutlineSceneInfo
Pydantic model for story outline scenes (more flexible).

```python
from src.models.scene_models import OutlineSceneInfo

class OutlineSceneInfo(BaseModel):
    scene_id: str
    setting: Optional[str]     # Optional for outlines
    characters: List[str]
    scene_mission: str
    key_events: List[str]
    # ... similar fields with relaxed validation
```

---

### Evaluators (`src/evaluators/main_evaluator.py`)

#### ScriptEvaluator
Main evaluation orchestrator.

```python
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig

# Configuration
config = EvaluationConfig(
    use_deepseek_judge: bool = True,
    save_detailed_report: bool = True,
    output_dir: str = "./outputs",
    pass_threshold: float = 0.70,
    excellent_threshold: float = 0.85
)

# Initialize evaluator
evaluator = ScriptEvaluator(config)

# Evaluate script
result = evaluator.evaluate_script(
    source_text: str,           # Original script text
    extracted_json: dict,       # Converted JSON data
    scene_type: str,           # "standard" or "outline"
    source_file: str           # Source filename for reporting
) -> EvaluationResult
```

#### EvaluationResult
Returned by `evaluate_script()`.

```python
class EvaluationResult:
    overall_score: float       # 0-1 aggregate score
    quality_level: str         # "Excellent", "Good", "Pass", "Fail"
    passed: bool              # Meets pass threshold

    # Component scores
    structure_score: float
    boundary_score: float
    character_score: float
    semantic_score: float

    # Statistics
    total_scenes: int
    total_characters: int

    # Feedback
    improvement_suggestions: List[str]

    # Reports
    detailed_report: dict     # Full JSON report
    report_path: Optional[str] # Path to saved report
```

**Usage Example**:
```python
result = evaluator.evaluate_script(
    source_text=open("script.txt").read(),
    extracted_json=json.load(open("output.json")),
    scene_type="standard",
    source_file="script.txt"
)

print(f"Score: {result.overall_score:.3f}")
print(f"Quality: {result.quality_level}")
print(f"Passed: {result.passed}")

for suggestion in result.improvement_suggestions:
    print(f"- {suggestion}")
```

---

### Metrics (`src/metrics/deepeval_metrics.py`)

#### SceneBoundaryMetric
Evaluates scene boundary detection accuracy.

```python
from src.metrics.deepeval_metrics import SceneBoundaryMetric

metric = SceneBoundaryMetric(
    tolerance: int = 2,        # Allowed boundary position error
    threshold: float = 0.70    # Pass threshold for F1 score
)

# Measure
metric.measure(test_case)

# Results
metric.score          # F1 score (0-1)
metric.precision      # Precision score
metric.recall         # Recall score
metric.success        # True if score >= threshold
```

#### CharacterExtractionMetric
Evaluates character extraction completeness.

```python
from src.metrics.deepeval_metrics import CharacterExtractionMetric

metric = CharacterExtractionMetric(
    threshold: float = 0.70
)

metric.measure(test_case)

# Results
metric.score          # Completeness score (0-1)
metric.success        # Meets threshold
metric.missing_chars  # List of missed characters
metric.extra_chars    # List of incorrectly added characters
```

#### SelfConsistencyMetric
Checks internal consistency of extracted data.

```python
from src.metrics.deepeval_metrics import SelfConsistencyMetric

metric = SelfConsistencyMetric(
    threshold: float = 0.80
)

metric.measure(test_case)

# Results
metric.score              # Consistency score (0-1)
metric.inconsistencies    # List of found inconsistencies
```

---

### LLM Client (`src/llm/deepseek_client.py`)

#### DeepSeekClient
OpenAI-compatible DeepSeek API client.

```python
from src.llm.deepseek_client import DeepSeekClient

client = DeepSeekClient(
    api_key: Optional[str] = None,        # Defaults to env DEEPSEEK_API_KEY
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
    temperature: float = 0.1,
    max_retries: int = 3,
    retry_delay: int = 1,
    timeout: int = 60,
    enable_cost_tracking: bool = True,
    debug: bool = False
)
```

**Methods**:

```python
# Create chat completion
response = client.create_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> dict

# Example
response = client.create_completion(
    prompt="Evaluate the following scene conversion...",
    system_prompt="You are an expert script evaluator",
    max_tokens=1000
)

content = response['choices'][0]['message']['content']
```

```python
# Get token usage statistics
stats = client.get_usage_stats() -> dict
# Returns:
# {
#     'total_tokens': 12345,
#     'prompt_tokens': 8000,
#     'completion_tokens': 4345,
#     'total_cost': 0.0123  # In USD
# }
```

```python
# Reset usage tracking
client.reset_usage_stats()
```

**Error Handling**:
```python
from src.llm.deepseek_client import DeepSeekAPIError

try:
    response = client.create_completion(prompt="...")
except DeepSeekAPIError as e:
    print(f"API Error: {e}")
    print(f"Retry count: {e.retry_count}")
```

---

### Utilities (`src/utils/file_handler.py`)

#### FileHandler
File I/O operations.

```python
from src.utils.file_handler import FileHandler

handler = FileHandler()

# Read script file
text = handler.read_script(
    file_path: str,
    encoding: str = "utf-8"
) -> str

# Load JSON file
data = handler.load_json(
    file_path: str
) -> dict

# Save evaluation report
handler.save_report(
    report: dict,
    output_path: str,
    format: str = "json"  # "json" or "html"
)

# Save HTML report
handler.save_html_report(
    report: dict,
    output_path: str,
    template: Optional[str] = None
)
```

---

## Configuration API

### Loading Configuration

```python
import yaml

# Load default config
with open("configs/default_config.yaml") as f:
    config = yaml.safe_load(f)

# Load evaluation weights
with open("configs/evaluation_weights.yaml") as f:
    weights = yaml.safe_load(f)

# Load DeepSeek config
with open("configs/deepseek_config.yaml") as f:
    api_config = yaml.safe_load(f)
```

### Configuration Schema

**default_config.yaml**:
```python
{
    'evaluation': {
        'pass_threshold': float,        # 0-1
        'excellent_threshold': float,   # 0-1
        'use_deepseek_judge': bool
    },
    'api': {
        'model': str,
        'temperature': float,
        'max_retries': int
    },
    'output': {
        'save_reports': bool,
        'report_format': List[str]      # ["json", "html"]
    }
}
```

**evaluation_weights.yaml**:
```python
{
    'weights': {
        'structure': float,    # 0-1, must sum to 1.0
        'boundary': float,
        'character': float,
        'semantic': float
    },
    'scene1': {
        'boundary_tolerance': int,
        'min_characters': int
    },
    'scene2': {
        'boundary_tolerance': int,
        'allow_inference': bool
    }
}
```

---

## Test Case API

### Creating Test Cases

```python
from deepeval.test_case import LLMTestCase

test_case = LLMTestCase(
    input=source_text,              # Original script
    actual_output=extracted_json,   # Converted JSON
    expected_output=ground_truth,   # Optional: reference JSON
    context=[...]                   # Optional: additional context
)

# Evaluate with metrics
from deepeval import evaluate

evaluate(
    test_cases=[test_case],
    metrics=[boundary_metric, character_metric, semantic_metric]
)
```

---

## Batch Evaluation API

```python
from src.evaluators.main_evaluator import ScriptEvaluator

evaluator = ScriptEvaluator(config)

# Prepare multiple test cases
test_cases = [
    {
        "source_text": "...",
        "extracted_json": {...},
        "scene_type": "standard",
        "source_file": "script1.txt"
    },
    {
        "source_text": "...",
        "extracted_json": {...},
        "scene_type": "outline",
        "source_file": "outline1.txt"
    }
]

# Batch evaluate
results = []
for case in test_cases:
    result = evaluator.evaluate_script(**case)
    results.append(result)

# Aggregate results
total_passed = sum(r.passed for r in results)
avg_score = sum(r.overall_score for r in results) / len(results)

print(f"Passed: {total_passed}/{len(results)}")
print(f"Average Score: {avg_score:.3f}")
```

---

## Prompt Template API

### Loading Prompts

```python
from pathlib import Path

def load_prompt(prompt_name: str) -> str:
    """Load prompt template from prompts/ directory"""
    prompt_path = Path("prompts") / f"{prompt_name}.txt"
    return prompt_path.read_text(encoding="utf-8")

# Load specific prompts
scene1_prompt = load_prompt("scene1_extraction")
boundary_prompt = load_prompt("boundary_evaluation")
semantic_prompt = load_prompt("semantic_evaluation")
```

### Using Prompts with Variables

```python
# Prompt template with placeholders
template = load_prompt("semantic_evaluation")

# Fill in variables
prompt = template.format(
    source_text=source_text,
    extracted_json=json.dumps(extracted_json, indent=2),
    evaluation_criteria="..."
)

# Send to LLM
response = client.create_completion(prompt=prompt)
```

---

## Type Definitions

```python
from typing import List, Dict, Optional, Literal

# Scene type
SceneType = Literal["standard", "outline"]

# Quality level
QualityLevel = Literal["Excellent", "Good", "Pass", "Fail"]

# Report format
ReportFormat = Literal["json", "html"]

# Score range
Score = float  # 0.0 to 1.0

# Common type aliases
SceneData = Dict[str, any]
EvaluationMetrics = Dict[str, Score]
```

---

## Error Classes

```python
# Base exception
class EvaluationError(Exception):
    """Base exception for evaluation errors"""
    pass

# Validation errors
class ValidationError(EvaluationError):
    """Raised when data validation fails"""
    pass

# API errors
class DeepSeekAPIError(EvaluationError):
    """Raised when DeepSeek API call fails"""
    def __init__(self, message: str, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message)

# Configuration errors
class ConfigurationError(EvaluationError):
    """Raised when configuration is invalid"""
    pass

# Metric errors
class MetricError(EvaluationError):
    """Raised when metric calculation fails"""
    pass
```

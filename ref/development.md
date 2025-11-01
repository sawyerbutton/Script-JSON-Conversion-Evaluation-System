# Development Guide

## Development Workflow

### Setup

#### Local Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Setup environment
cp .env.example .env
# Edit .env and add DEEPSEEK_API_KEY
```

## Common Development Tasks

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# System tests
python scripts/test_system.py

# With coverage report
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Sort imports
isort src/ tests/
```

### Running Evaluations

```python
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig

# Configure
config = EvaluationConfig(
    use_deepseek_judge=True,
    save_detailed_report=True,
    output_dir="./outputs"
)

evaluator = ScriptEvaluator(config)

# Evaluate
result = evaluator.evaluate_script(
    source_text="...",
    extracted_json={...},
    scene_type="standard",  # or "outline"
    source_file="test.txt"
)

print(f"Score: {result.overall_score:.3f}")
print(f"Level: {result.quality_level}")
```

## Project Structure by Concern

### Core Source Files

**Data Models** (`src/models/`)
- `scene_models.py` - Pydantic models for JSON validation
  - `SceneInfo` - Standard script format
  - `OutlineSceneInfo` - Story outline format

**Metrics** (`src/metrics/`)
- `deepeval_metrics.py` - Custom DeepEval metrics
  - Scene boundary metrics
  - Character extraction metrics
  - Self-consistency metrics

**LLM Integration** (`src/llm/`)
- `deepseek_client.py` - DeepSeek API client
  - OpenAI-compatible interface
  - Retry logic
  - Cost tracking
  - Token usage stats

**Evaluators** (`src/evaluators/`)
- `main_evaluator.py` - Main evaluation orchestrator
  - Three-tier evaluation logic
  - Score aggregation
  - Report generation

**Utilities** (`src/utils/`)
- `file_handler.py` - File I/O operations
  - Read scripts
  - Load JSON
  - Save reports

### Configuration Files

**configs/**
- `default_config.yaml` - General settings
- `evaluation_weights.yaml` - Metric weights
- `deepseek_config.yaml` - API configuration

**prompts/**
- `scene1_extraction.txt` - Standard script prompts
- `scene2_extraction.txt` - Outline prompts
- `boundary_evaluation.txt` - Boundary eval prompts
- `semantic_evaluation.txt` - Semantic eval prompts

### Test Files

**tests/unit/** - Unit tests
- `test_models.py` - Model validation tests
- `test_metrics.py` - Metric calculation tests
- `test_client.py` - API client tests

**tests/integration/** - Integration tests
- `test_evaluation_flow.py` - End-to-end evaluation tests

**tests/test_data/** - Test samples
- `scene1/` - Standard script samples
- `scene2/` - Outline samples

## Adding New Features

### Add a New Evaluation Metric

1. **Create metric class** (`src/metrics/custom_metric.py`)
```python
from deepeval.metrics import BaseMetric

class CustomMetric(BaseMetric):
    def __init__(self):
        self.threshold = 0.7

    def measure(self, test_case):
        # Implement scoring logic
        score = self._calculate_score(test_case)
        self.score = score
        self.success = score >= self.threshold
        return self.score

    async def a_measure(self, test_case):
        return self.measure(test_case)
```

2. **Register in evaluator** (`src/evaluators/main_evaluator.py`)
```python
from src.metrics.custom_metric import CustomMetric

# In ScriptEvaluator class
custom_metric = CustomMetric()
metrics.append(custom_metric)
```

3. **Update weight configuration** (`configs/evaluation_weights.yaml`)
```yaml
weights:
  structure: 0.20
  boundary: 0.20
  character: 0.20
  semantic: 0.20
  custom: 0.20  # Add new metric
```

4. **Write tests** (`tests/unit/test_custom_metric.py`)

### Add a New Scene Type

1. **Define Pydantic model** (`src/models/scene_models.py`)
```python
class NewSceneInfo(BaseModel):
    scene_id: str
    # ... add required fields

    @validator('scene_id')
    def validate_scene_id(cls, v):
        # Add validation logic
        return v
```

2. **Create prompt template** (`prompts/new_scene_extraction.txt`)

3. **Update configuration** (`configs/evaluation_weights.yaml`)
```yaml
new_scene_type:
  boundary_tolerance: 2
  min_characters: 1
  # ... specific rules
```

4. **Extend evaluator** (`src/evaluators/main_evaluator.py`)
```python
def _validate_structure(self, scene_type, json_data):
    if scene_type == "new_type":
        return NewSceneInfo(**json_data)
    # ... existing logic
```

### Customize Prompts

Edit prompt files in `prompts/` directory:

**Example**: `prompts/semantic_evaluation.txt`
```
You are evaluating the semantic accuracy of script-to-JSON conversion.

Input:
- Source text: {source_text}
- Extracted JSON: {extracted_json}

Evaluate the following aspects:
1. Scene mission accuracy
2. Key events coverage
3. Information changes
4. Relationship changes

Output a score from 0-1 and detailed reasoning.
```

## Environment Variables

Create `.env` file with:

```env
# Required
DEEPSEEK_API_KEY=your_api_key_here

# Optional
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATA_DIR=./data
OUTPUT_DIR=./outputs
LOG_DIR=./logs
DEBUG=false
LOG_LEVEL=INFO
```

## Best Practices

### Code Organization
- One class per file
- Clear module boundaries
- Use dependency injection
- Write comprehensive docstrings
- Follow PEP 8 style guide

### Error Handling
```python
class EvaluationError(Exception):
    """Base exception for evaluation errors"""
    pass

class ValidationError(EvaluationError):
    """Raised when validation fails"""
    pass

# Use in code
try:
    result = validate_structure(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Starting evaluation")
logger.debug(f"Config: {config}")
logger.error(f"Evaluation failed: {error}")
```

### Testing Strategy
- Unit test coverage > 80%
- Use pytest fixtures
- Mock external API calls
- Test edge cases
- Integration tests for main flows

**Example Test**:
```python
import pytest
from src.models.scene_models import SceneInfo

def test_scene_info_validation():
    # Valid data
    valid_data = {
        "scene_id": "S01",
        "setting": "Interior Cafe - Day",
        "characters": ["Alice", "Bob"]
    }
    scene = SceneInfo(**valid_data)
    assert scene.scene_id == "S01"

    # Invalid data
    with pytest.raises(ValidationError):
        SceneInfo(**{"scene_id": ""})  # Empty ID
```

## Debugging Tips

### Debug API Calls
```python
import os
os.environ['DEBUG'] = 'true'

from src.llm.deepseek_client import DeepSeekClient
client = DeepSeekClient(debug=True)  # Enables verbose logging
```

### View Generated Reports
```bash
# JSON reports
cat outputs/reports/json/evaluation_*.json

# HTML reports (open in browser)
open outputs/reports/html/evaluation_*.html
```

## Contributing Checklist

- [ ] Code follows project style (black, flake8, isort)
- [ ] New features have unit tests
- [ ] All tests pass (`pytest tests/`)
- [ ] Documentation updated
- [ ] Type hints added (mypy compatible)
- [ ] Error handling implemented
- [ ] Logging added for key operations
- [ ] Configuration options documented

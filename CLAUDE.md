# Claude Code Reference Documentation

This document provides pointers to important documentation and resources for AI-assisted development of the Script JSON Conversion Evaluation System.

## Project Overview

**Script JSON Conversion Evaluation System** is an automated quality assurance system for validating script-to-JSON conversions using a three-tier evaluation architecture combining rule-based validation, statistical analysis, and LLM semantic evaluation.

- **Language**: Python 3.9+
- **Main Framework**: DeepEval 0.21+
- **LLM Provider**: DeepSeek API
- **Architecture**: Three-tier evaluation (Structure, Statistical, Semantic)

---

## Essential Documentation

### Core References (Start Here)

1. **[Project Overview](ref/project-overview.md)**
   - Quick facts and key features
   - High-level architecture
   - Quick start guide
   - Related documentation links

2. **[Architecture](ref/architecture.md)**
   - Three-tier evaluation system design
   - Data flow and component interactions
   - Configuration system
   - Extensibility points

3. **[Development Guide](ref/development.md)**
   - Development workflow
   - Common tasks and commands
   - Adding new features (metrics, scene types)
   - Best practices and testing

4. **[API Reference](ref/api-reference.md)**
   - Complete API documentation
   - Data models, evaluators, metrics
   - LLM client usage
   - Error handling

### Detailed Documentation (docs/)

- **[Project Structure](docs/project_structure.md)** - Detailed file organization
- **[Development Checklist](docs/script_eval_development_checklist.md)** - Implementation tasks

---

## Quick Start

### For Development

```bash
# Using local Python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add DEEPSEEK_API_KEY
python scripts/test_system.py
```

### For Understanding the Codebase

1. Start with **[ref/project-overview.md](ref/project-overview.md)** for high-level understanding
2. Review **[ref/architecture.md](ref/architecture.md)** for system design
3. Check **[ref/api-reference.md](ref/api-reference.md)** for code APIs
4. Read **[ref/development.md](ref/development.md)** for development workflows

---

## Key Source Files

### Core Modules

| Module | Location | Purpose |
|--------|----------|---------|
| Data Models | `src/models/scene_models.py` | Pydantic models for JSON validation |
| Metrics | `src/metrics/deepeval_metrics.py` | Custom evaluation metrics |
| LLM Client | `src/llm/deepseek_client.py` | DeepSeek API client |
| Evaluator | `src/evaluators/main_evaluator.py` | Main orchestrator |
| Utils | `src/utils/file_handler.py` | File I/O operations |

### Configuration Files

| File | Purpose |
|------|---------|
| `configs/default_config.yaml` | General settings |
| `configs/evaluation_weights.yaml` | Metric weights |
| `configs/deepseek_config.yaml` | API configuration |

### Prompt Templates

| File | Purpose |
|------|---------|
| `prompts/scene1_extraction.txt` | Standard script extraction |
| `prompts/scene2_extraction.txt` | Outline extraction |
| `prompts/boundary_evaluation.txt` | Boundary evaluation |
| `prompts/semantic_evaluation.txt` | Semantic evaluation |

---

## Common Development Tasks

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# System tests
python scripts/test_system.py

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
black src/ tests/     # Format with black
flake8 src/ tests/    # Lint with flake8
mypy src/             # Type check with mypy
```

### Evaluation

```python
from src.evaluators.main_evaluator import ScriptEvaluator, EvaluationConfig

config = EvaluationConfig(use_deepseek_judge=True)
evaluator = ScriptEvaluator(config)

result = evaluator.evaluate_script(
    source_text="...",
    extracted_json={...},
    scene_type="standard",
    source_file="test.txt"
)
```

---

## Project Structure

```
Script-JSON-Conversion-Evaluation-System/
├── src/                    # Source code
│   ├── models/             # Pydantic models
│   ├── metrics/            # Evaluation metrics
│   ├── llm/                # LLM integration
│   ├── evaluators/         # Evaluation orchestrators
│   └── utils/              # Utilities
├── tests/                  # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── test_data/          # Test samples
├── configs/                # YAML configurations
├── prompts/                # LLM prompt templates
├── docs/                   # Detailed documentation
├── ref/                    # Reference docs (this directory)
├── scripts/                # Utility scripts
├── docker-compose*.yml     # Docker configurations
├── Dockerfile              # Container definition
├── Makefile               # Command shortcuts
└── CLAUDE.md              # This file
```

---

## Architecture Overview

### Three-Tier Evaluation

1. **Structure Layer** (`src/models/`)
   - Validates JSON schema with Pydantic
   - Checks required fields and data types

2. **Statistical Layer** (`src/metrics/`)
   - Scene boundary metrics (F1, Precision, Recall)
   - Character extraction metrics
   - Self-consistency checks

3. **Semantic Layer** (`src/llm/` + `src/evaluators/`)
   - LLM-as-Judge evaluation via DeepSeek API
   - Scene mission accuracy
   - Key events coverage
   - Information/relationship changes

### Data Flow

```
Input → Structure Validation → Statistical Metrics → Semantic Evaluation → Score Aggregation → Report
```

---

## Configuration

### Environment Variables (.env)

```bash
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATA_DIR=./data
OUTPUT_DIR=./outputs
LOG_LEVEL=INFO
```

### Evaluation Weights

Edit `configs/evaluation_weights.yaml`:

```yaml
weights:
  structure: 0.25
  boundary: 0.25
  character: 0.25
  semantic: 0.25
```

---

## Extending the System

### Add New Metric

1. Create metric class in `src/metrics/`
2. Inherit from `deepeval.metrics.BaseMetric`
3. Implement `measure()` method
4. Register in main evaluator
5. Update weight configuration

See [ref/development.md#adding-new-features](ref/development.md) for details.

### Add New Scene Type

1. Define Pydantic model in `src/models/scene_models.py`
2. Create prompt template in `prompts/`
3. Add validation rules in `configs/evaluation_weights.yaml`
4. Update main evaluator

---

## Troubleshooting

### Common Issues

**API connection fails**:
```bash
# Check environment variable
echo $DEEPSEEK_API_KEY

# Test connection
python -c "from src.llm.deepseek_client import DeepSeekClient; client = DeepSeekClient(debug=True)"
```

**Tests failing**:
```bash
pytest tests/unit/ -v    # Run tests with verbose output
pytest tests/unit/ --pdb # Debug with pdb
```

---

## Best Practices

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Format with black (`make fmt`)

### Testing
- Unit test coverage > 80%
- Mock external API calls
- Test edge cases
- Use pytest fixtures

### Error Handling
- Use custom exception classes
- Log errors with context
- Provide user-friendly messages
- Implement graceful degradation

### Development Workflow
1. Create feature branch
2. Write tests first (TDD)
3. Implement feature
4. Run tests (`make test-all`)
5. Format code (`make fmt`)
6. Lint code (`make lint`)
7. Commit and push

---

## Additional Resources

### External Documentation
- [DeepEval Documentation](https://docs.confident-ai.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [DeepSeek API Documentation](https://platform.deepseek.com/api-docs/)

### Code Examples
- `code-samples/` - Reference implementations
- `scripts/test_system.py` - System test example
- `tests/` - Test examples

---

## Getting Help

### Documentation Order

For new contributors:
1. [ref/project-overview.md](ref/project-overview.md) - Start here
2. [ref/architecture.md](ref/architecture.md) - Understand design
3. [ref/development.md](ref/development.md) - Development guide
4. [ref/api-reference.md](ref/api-reference.md) - API details

For specific tasks:
- **Adding features**: [ref/development.md](ref/development.md)
- **API usage**: [ref/api-reference.md](ref/api-reference.md)
- **Development workflow**: [ref/development.md](ref/development.md)

### Commands Reference

```bash
pytest tests/        # Run all tests
python scripts/test_system.py  # Run system tests
black src/ tests/    # Format code
flake8 src/ tests/   # Lint code
mypy src/            # Type check
```

---

**Last Updated**: 2025-11-01
**Version**: 0.1.0
**Maintained by**: Development Team

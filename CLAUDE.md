# Claude Code Reference Documentation

This document provides pointers to important documentation and resources for AI-assisted development of the Script JSON Conversion Evaluation System.

## Project Overview

**Script JSON Conversion Evaluation System** is an automated quality assurance system for validating script-to-JSON conversions using a three-tier evaluation architecture combining rule-based validation, statistical analysis, and LLM semantic evaluation.

- **Language**: Python 3.9+
- **Main Framework**: DeepEval 0.21+
- **LLM Provider**: DeepSeek API
- **Architecture**: Three-tier evaluation (Structure, Statistical, Semantic)
- **Test Coverage**: 64% overall, 85% core modules
- **Test Suite**: 241 unit tests, 100% pass rate

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

4. **[Scripts Guide](ref/scripts-guide.md)**
   - All 5 conversion and evaluation scripts
   - Usage examples and parameters
   - Batch processing patterns
   - Cost estimation and API usage

5. **[Models Reference](ref/models-reference.md)**
   - Complete Pydantic model documentation
   - SceneInfo vs OutlineSceneInfo comparison
   - Field validation rules and examples
   - Pydantic V2 migration notes
   - Common validation errors

6. **[API Reference](ref/api-reference.md)**
   - Complete API documentation
   - Data models, evaluators, metrics
   - LLM client usage
   - Error handling

### New References (Recently Added)

7. **[Utils Reference](ref/utils-reference.md)** ⭐ NEW
   - Exception system (16 custom exception types)
   - Logging system (colored output, file logging)
   - Performance monitoring (profiling, timing, API tracking)
   - File handler utilities
   - Complete usage examples

8. **[Testing Reference](ref/testing-reference.md)** ⭐ NEW
   - Test suite overview (241 tests, 64% coverage)
   - Running tests (unit, integration, system)
   - Testing patterns and best practices
   - Mock strategies for LLM clients
   - Coverage reports and analysis

9. **[Bug Fixes Reference](ref/bug-fixes-reference.md)** ⭐ NEW (v0.2.1)
   - Critical bug fixes from batch testing
   - JSON serialization, performance timer, validation rules
   - Character consistency improvements
   - Verification and troubleshooting

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

### For Running Tests

```bash
# Run all unit tests
pytest tests/

# Run with coverage report
pytest --cov=src --cov-report=html tests/

# Run system test (no API required)
python scripts/test_system.py
```

### For Running Scripts

```bash
# Convert script to JSON only
python scripts/convert_script_to_json.py script_examples/scripts/script_01_wuxia_tech.md

# Convert outline to JSON only
python scripts/convert_outline_to_json.py script_examples/outlines/outline_01_time_traveler.md

# Full script evaluation (with LLM semantic evaluation)
python scripts/run_full_evaluation.py script_examples/scripts/script_01_wuxia_tech.md

# Full outline evaluation
python scripts/run_outline_evaluation.py script_examples/outlines/outline_01_time_traveler.md

# Skip LLM evaluation (faster, cheaper)
python scripts/run_full_evaluation.py script_examples/scripts/script_01_wuxia_tech.md --no-llm-judge
```

See **[ref/scripts-guide.md](ref/scripts-guide.md)** for complete script documentation.

### For Understanding the Codebase

**New contributors** should read in this order:

1. **[ref/project-overview.md](ref/project-overview.md)** - Start here for high-level understanding
2. **[ref/architecture.md](ref/architecture.md)** - Understand system design
3. **[ref/scripts-guide.md](ref/scripts-guide.md)** - Learn script usage
4. **[ref/models-reference.md](ref/models-reference.md)** - Understand data models
5. **[ref/utils-reference.md](ref/utils-reference.md)** - Error handling, logging, performance
6. **[ref/api-reference.md](ref/api-reference.md)** - API details
7. **[ref/development.md](ref/development.md)** - Development workflows
8. **[ref/testing-reference.md](ref/testing-reference.md)** - Testing guide

**For specific tasks**:
- **Running scripts**: [ref/scripts-guide.md](ref/scripts-guide.md)
- **Understanding models**: [ref/models-reference.md](ref/models-reference.md)
- **Error handling**: [ref/utils-reference.md#exceptions](ref/utils-reference.md#exceptions)
- **Logging**: [ref/utils-reference.md#logger](ref/utils-reference.md#logger)
- **Performance**: [ref/utils-reference.md#performance-monitoring](ref/utils-reference.md#performance-monitoring)
- **Writing tests**: [ref/testing-reference.md](ref/testing-reference.md)
- **Adding features**: [ref/development.md](ref/development.md)
- **API usage**: [ref/api-reference.md](ref/api-reference.md)
- **Bug fixes and troubleshooting**: [ref/bug-fixes-reference.md](ref/bug-fixes-reference.md)

---

## Key Source Files

### Core Modules

| Module | Location | Purpose | Tests | Coverage |
|--------|----------|---------|-------|----------|
| Data Models | `src/models/scene_models.py` | Pydantic models for JSON validation | 37 | 86% |
| Metrics | `src/metrics/deepeval_metrics.py` | Custom evaluation metrics | 45 | 92% ⭐ |
| LLM Client | `src/llm/deepseek_client.py` | DeepSeek API client | 21 | 81% |
| Evaluator | `src/evaluators/main_evaluator.py` | Main orchestrator | 0* | 0%* |
| File Handler | `src/utils/file_handler.py` | File I/O operations | 0* | 0%* |
| Exceptions | `src/utils/exceptions.py` | Exception system (16 types) | 59 | 86% |
| Logger | `src/utils/logger.py` | Logging system | 34 | 83% |
| Performance | `src/utils/performance.py` | Performance monitoring | 46 | 82% |

*Integration tested, unit tests pending

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

# Specific test file
pytest tests/unit/test_deepeval_metrics.py -v

# Specific test class
pytest tests/unit/test_exceptions.py::TestAPIExceptions -v

# With coverage
pytest --cov=src --cov-report=html tests/

# System tests (no API required)
python scripts/test_system.py
```

See **[ref/testing-reference.md](ref/testing-reference.md)** for comprehensive testing guide.

### Code Quality

```bash
black src/ tests/     # Format with black
flake8 src/ tests/    # Lint with flake8
mypy src/             # Type check with mypy
```

### Using Utilities

```python
# Exception handling
from src.utils.exceptions import ErrorContext, APIConnectionError

with ErrorContext("处理文件", file_path="data.json"):
    process_file()

# Logging
from src.utils.logger import get_logger, OperationLogger

logger = get_logger(__name__)
with OperationLogger(logger, "数据处理"):
    process_data()

# Performance monitoring
from src.utils.performance import track_performance, PerformanceProfiler

with track_performance("文件处理"):
    process_file()

profiler = PerformanceProfiler("评估流程")
profiler.start("初始化")
# ... operations ...
profiler.checkpoint("验证")
# ... more operations ...
profiler.stop()
profiler.print_report()
```

See **[ref/utils-reference.md](ref/utils-reference.md)** for complete utilities documentation.

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
│   ├── models/             # Pydantic models (37 tests, 86% coverage)
│   ├── metrics/            # Evaluation metrics (45 tests, 92% coverage)
│   ├── llm/                # LLM integration (21 tests, 81% coverage)
│   ├── evaluators/         # Evaluation orchestrators (0 tests, 0% coverage*)
│   └── utils/              # Utilities (139 tests, 84% avg coverage)
│       ├── exceptions.py   # Exception system (59 tests, 86%)
│       ├── logger.py       # Logging (34 tests, 83%)
│       ├── performance.py  # Performance monitoring (46 tests, 82%)
│       └── file_handler.py # File I/O (0 tests, 0%*)
├── tests/                  # Test suites (241 tests total)
│   ├── unit/               # Unit tests
│   │   ├── test_deepeval_metrics.py    (45 tests)
│   │   ├── test_deepseek_client.py     (21 tests)
│   │   ├── test_exceptions.py          (59 tests)
│   │   ├── test_logger.py              (34 tests)
│   │   ├── test_performance.py         (46 tests)
│   │   └── test_scene_models.py        (37 tests)
│   ├── integration/        # Integration tests
│   └── test_data/          # Test samples
├── configs/                # YAML configurations
├── prompts/                # LLM prompt templates
├── docs/                   # Detailed documentation
├── ref/                    # Reference docs (8 files)
│   ├── project-overview.md
│   ├── architecture.md
│   ├── development.md
│   ├── scripts-guide.md
│   ├── models-reference.md
│   ├── api-reference.md
│   ├── utils-reference.md      ⭐ NEW
│   └── testing-reference.md    ⭐ NEW
├── scripts/                # Utility scripts (5 files)
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
├── pyproject.toml         # Project configuration
└── CLAUDE.md              # This file

*Integration tested, unit tests pending
```

---

## Architecture Overview

### Three-Tier Evaluation

1. **Structure Layer** (`src/models/`)
   - Validates JSON schema with Pydantic V2
   - Checks required fields and data types
   - 37 tests, 86% coverage

2. **Statistical Layer** (`src/metrics/`)
   - Scene boundary metrics (F1, Precision, Recall)
   - Character extraction metrics
   - Self-consistency checks
   - 45 tests, 92% coverage ⭐

3. **Semantic Layer** (`src/llm/` + `src/evaluators/`)
   - LLM-as-Judge evaluation via DeepSeek API
   - Scene mission accuracy
   - Key events coverage
   - Information/relationship changes
   - 21 tests for LLM client, 81% coverage

### Data Flow

```
Input → Structure Validation → Statistical Metrics → Semantic Evaluation → Score Aggregation → Report
```

### Error Handling & Logging

- **Exception System**: 16 custom exception types with severity levels
- **Logging**: Colored console output + file logging with 3 format styles
- **Performance**: Profiling, timing decorators, API call tracking
- See **[ref/utils-reference.md](ref/utils-reference.md)** for details

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
6. **Write tests** (see [ref/testing-reference.md](ref/testing-reference.md))

See [ref/development.md#adding-new-features](ref/development.md) for details.

### Add New Scene Type

1. Define Pydantic model in `src/models/scene_models.py`
2. Create prompt template in `prompts/`
3. Add validation rules in `configs/evaluation_weights.yaml`
4. Update main evaluator
5. **Write tests** for the new model

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

**Import errors**:
- Ensure `src/` is in Python path
- Use dual import strategy (see [ref/utils-reference.md](ref/utils-reference.md))

**Coverage reports**:
```bash
pytest --cov=src --cov-report=html tests/
# Open htmlcov/index.html
```

See **[ref/testing-reference.md#common-test-issues](ref/testing-reference.md#common-test-issues-and-solutions)** for more troubleshooting.

---

## Best Practices

### Code Style
- Follow PEP 8
- Use type hints
- Write docstrings
- Format with black (`black src/ tests/`)

### Testing
- Unit test coverage > 80% (current: 64% overall, 85% core modules)
- Mock external API calls (see [ref/testing-reference.md#mock-strategies](ref/testing-reference.md#mock-strategies))
- Test edge cases (empty data, invalid input)
- Use pytest fixtures for reusable data

### Error Handling
- Use custom exception classes from `src.utils.exceptions`
- Use `ErrorContext` for complex operations
- Log errors with context using `OperationLogger`
- Provide user-friendly messages
- Implement graceful degradation

See **[ref/utils-reference.md#usage-patterns](ref/utils-reference.md#usage-patterns)** for complete examples.

### Development Workflow
1. Create feature branch
2. Write tests first (TDD) - see [ref/testing-reference.md](ref/testing-reference.md)
3. Implement feature
4. Run tests (`pytest tests/`)
5. Check coverage (`pytest --cov=src tests/`)
6. Format code (`black src/ tests/`)
7. Lint code (`flake8 src/ tests/`)
8. Commit and push

---

## Test Suite Overview

### Statistics

- **Total Tests**: 241
- **Pass Rate**: 100% ✅
- **Overall Coverage**: 64%
- **Core Modules Coverage**: 85% average

### By Module

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| deepeval_metrics | 45 | 92% | ⭐ Excellent |
| scene_models | 37 | 86% | ✅ Excellent |
| exceptions | 59 | 86% | ✅ Excellent |
| logger | 34 | 83% | ✅ Good |
| performance | 46 | 82% | ✅ Good |
| deepseek_client | 21 | 81% | ✅ Good |

See **[ref/testing-reference.md](ref/testing-reference.md)** for comprehensive testing documentation.

---

## Additional Resources

### External Documentation
- [DeepEval Documentation](https://docs.confident-ai.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [DeepSeek API Documentation](https://platform.deepseek.com/api-docs/)
- [pytest Documentation](https://docs.pytest.org/)

### Code Examples
- `code-samples/` - Reference implementations
- `scripts/test_system.py` - System test example
- `tests/` - Test examples (241 tests)

---

## Getting Help

### Documentation Index

**By Role**:

- **New Contributors**: Start with docs 1-5 above
- **Developers**: Focus on docs 3, 6, 7, 8
- **Testers**: Focus on docs 7, 8
- **DevOps**: Focus on docs 2, 3, 4

**By Topic**:

- **Running scripts**: [ref/scripts-guide.md](ref/scripts-guide.md)
- **Understanding models**: [ref/models-reference.md](ref/models-reference.md)
- **Error handling**: [ref/utils-reference.md#exceptions](ref/utils-reference.md#exceptions)
- **Logging**: [ref/utils-reference.md#logger](ref/utils-reference.md#logger)
- **Performance monitoring**: [ref/utils-reference.md#performance-monitoring](ref/utils-reference.md#performance-monitoring)
- **Writing tests**: [ref/testing-reference.md](ref/testing-reference.md)
- **Adding features**: [ref/development.md](ref/development.md)
- **API usage**: [ref/api-reference.md](ref/api-reference.md)
- **System architecture**: [ref/architecture.md](ref/architecture.md)
- **Bug fixes and troubleshooting**: [ref/bug-fixes-reference.md](ref/bug-fixes-reference.md)

### Commands Reference

```bash
# Testing
pytest tests/                                  # Run all tests
pytest tests/unit/test_deepeval_metrics.py -v # Run specific tests
pytest --cov=src --cov-report=html tests/     # Coverage report
python scripts/test_system.py                 # System test

# Conversion & Evaluation
python scripts/convert_script_to_json.py <script.md>      # Convert script to JSON
python scripts/convert_outline_to_json.py <outline.md>    # Convert outline to JSON
python scripts/run_full_evaluation.py <script.md>         # Full script evaluation
python scripts/run_outline_evaluation.py <outline.md>     # Full outline evaluation

# Code Quality
black src/ tests/    # Format code
flake8 src/ tests/   # Lint code
mypy src/            # Type check
```

---

## Recent Updates

**Version 0.2.1** (2025-11-02): 🐛 Bug Fix Release
- ✅ Fixed JSON serialization error in batch test reports
- ✅ Fixed performance timer negative duration display
- ✅ Implemented proper warning/error separation in validation
- ✅ Added smart character validation (group characters, aliases)
- ✅ Created bug fixes reference documentation
- ✅ All 241 unit tests passing

**Version 0.2.0** (2025-11-01): ⭐ Full Testing Release
- ✅ Completed batch testing of 16 script files (100% success rate)
- ✅ Smart model selection system (chat vs reasoner)
- ✅ Large file processing (up to 41 scenes)
- ✅ JSON post-processing and error recovery
- ✅ Comprehensive utility modules (exceptions, logger, performance)
- ✅ Created 241 unit tests with 64% coverage
- ✅ Added utils and testing reference documentation

**Version 0.1.0** (Initial):
- Basic evaluation system
- Core metrics and models
- Script conversion functionality
- Initial documentation

---

**Last Updated**: 2025-11-02
**Version**: 0.2.1
**Maintained by**: Development Team

# Testing Reference

Comprehensive guide to the test suite for the Script JSON Conversion Evaluation System.

## Table of Contents

- [Overview](#overview)
- [Test Statistics](#test-statistics)
- [Test Organization](#test-organization)
- [Running Tests](#running-tests)
- [Unit Tests](#unit-tests)
- [Testing Patterns](#testing-patterns)
- [Mock Strategies](#mock-strategies)
- [Coverage Reports](#coverage-reports)

---

## Overview

The project has a comprehensive test suite with **241 unit tests** achieving **64% overall coverage** and **85% average coverage** for core modules.

### Test Framework

- **pytest**: Primary testing framework
- **pytest-cov**: Code coverage reporting
- **pytest-asyncio**: Async test support
- **unittest.mock**: Mocking external dependencies

---

## Test Statistics

### Overall Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 241 |
| Pass Rate | 100% ✅ |
| Overall Coverage | 64% |
| Core Modules Coverage | 85% avg |

### Module Coverage

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| **deepeval_metrics.py** | 45 | 92% | ⭐ Excellent |
| **scene_models.py** | 37 | 86% | ✅ Excellent |
| **exceptions.py** | 59 | 86% | ✅ Excellent |
| **logger.py** | 34 | 83% | ✅ Good |
| **performance.py** | 46 | 82% | ✅ Good |
| **deepseek_client.py** | 21 | 81% | ✅ Good |
| **main_evaluator.py** | 0* | 0% | ⏸️ Integration tested |
| **file_handler.py** | 0* | 0% | ⏸️ Integration tested |

*Covered by integration tests but lacking dedicated unit tests

---

## Test Organization

```
tests/
├── unit/                           # Unit tests
│   ├── test_deepeval_metrics.py    # Evaluation metrics (45 tests)
│   ├── test_deepseek_client.py     # LLM client (21 tests)
│   ├── test_exceptions.py          # Exception system (59 tests)
│   ├── test_logger.py              # Logging system (34 tests)
│   ├── test_performance.py         # Performance monitoring (46 tests)
│   └── test_scene_models.py        # Pydantic models (37 tests)
├── integration/                     # Integration tests (planned)
└── test_data/                       # Test data files
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test File

```bash
pytest tests/unit/test_deepeval_metrics.py
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html tests/
```

Coverage report generated in `htmlcov/index.html`

### Run with Verbose Output

```bash
pytest tests/ -v
```

### Run Specific Test Class

```bash
pytest tests/unit/test_exceptions.py::TestAPIExceptions -v
```

### Run Specific Test Method

```bash
pytest tests/unit/test_logger.py::TestOperationLogger::test_operation_logger_success -v
```

### Run Tests Matching Pattern

```bash
pytest tests/ -k "test_measure"
```

### Run System Test

```bash
python scripts/test_system.py
```

System test validates:
- ✅ File handling
- ✅ Model validation
- ✅ Basic evaluation workflow
- ✅ Performance profiling

---

## Unit Tests

### test_deepeval_metrics.py (45 tests, 92% coverage)

Tests for custom DeepEval evaluation metrics.

**Test Classes**:

1. **TestSceneBoundaryMetric** (11 tests)
   - Initialization with/without LLM
   - Measure method (sync/async)
   - Structure evaluation
   - Scene ID continuity checking
   - Setting validation
   - Reason generation

2. **TestCharacterExtractionMetric** (13 tests)
   - Character collection from scenes
   - Scene-character mapping
   - Consistency evaluation
   - Importance scoring
   - Edge cases (empty data, single character)

3. **TestSelfConsistencyMetric** (15 tests)
   - Field consistency calculation
   - List and dict field handling
   - Worst field identification
   - Insufficient data handling

4. **TestIntegration** (3 tests)
   - Multiple metrics working together
   - Edge case data handling
   - Minimal data validation

5. **TestErrorHandling** (3 tests)
   - Invalid JSON handling
   - LLM client errors
   - Invalid LLM response formats

**Key Patterns**:
```python
# Mocking LLM client
mock_client = MagicMock()
mock_client.complete.return_value = {
    "content": {"score": 0.85, ...}
}

with patch("src.metrics.deepeval_metrics.DeepSeekClient",
           return_value=mock_client):
    metric = SceneBoundaryMetric(use_deepseek=True)
    score = metric.measure(test_case)
```

### test_deepseek_client.py (21 tests, 81% coverage)

Tests for DeepSeek API client.

**Test Classes**:

1. **TestDeepSeekConfig** (2 tests)
   - Default configuration
   - Custom configuration

2. **TestDeepSeekClient** (15 tests)
   - Client initialization
   - Successful API calls
   - System prompts
   - JSON response format
   - Temperature settings
   - Retry logic (rate limits, API errors)
   - Max retries exceeded
   - Batch processing
   - LLM evaluation
   - Cost tracking
   - Usage statistics

3. **TestDeepSeekForDeepEval** (4 tests)
   - DeepEval integration
   - Sync/async generation
   - Model name retrieval

**Key Patterns**:
```python
# Mocking OpenAI client
mock_client = MagicMock()
mock_response = MagicMock()
mock_response.choices = [...]
mock_response.usage.total_tokens = 1000
mock_client.chat.completions.create.return_value = mock_response

with patch("src.llm.deepseek_client.OpenAI", return_value=mock_client):
    client = DeepSeekClient(config)
    result = client.complete("prompt")
```

### test_exceptions.py (59 tests, 86% coverage)

Tests for custom exception system.

**Test Classes**:

1. **TestBaseException** (3 tests)
   - Basic exception creation
   - Exception with details
   - String representation

2. **TestAPIExceptions** (6 tests)
   - Connection errors
   - Rate limit errors
   - Timeout errors
   - Response errors
   - Quota exceeded errors

3. **TestValidationExceptions** (4 tests)
   - JSON validation
   - Scene validation
   - Character validation

4. **TestFileExceptions** (5 tests)
   - File not found
   - Read errors
   - Write errors
   - Format errors

5. **TestEvaluationExceptions** (4 tests)
   - Metric calculation errors
   - Configuration errors
   - Insufficient data errors

6. **TestConversionExceptions** (3 tests)
   - Script parsing errors
   - JSON generation errors

7. **TestConfigurationExceptions** (3 tests)
   - Missing config
   - Invalid config

8. **TestHelperFunctions** (11 tests)
   - Retryable error detection
   - Error severity classification
   - Exception formatting

9. **TestErrorContext** (6 tests)
   - Success case
   - Exception handling
   - No-raise mode
   - Context data

10. **TestExceptionHierarchy** (7 tests)
    - Inheritance validation
    - Type checking

11. **TestExceptionUsagePatterns** (5 tests)
    - Catching specific exceptions
    - Parent exception catching
    - Multiple exception handling
    - Retry logic

### test_logger.py (34 tests, 83% coverage)

Tests for logging system.

**Test Classes**:

1. **TestGetLogger** (3 tests)
   - Default logger
   - Named logger
   - Singleton behavior

2. **TestSetupLogger** (5 tests)
   - Default configuration
   - Level setting
   - File logging
   - Format styles
   - Duplicate handler prevention

3. **TestColoredFormatter** (2 tests)
   - Formatter creation
   - Log formatting

4. **TestLoggerContext** (3 tests)
   - Temporary level changes
   - Level restoration
   - Exception handling

5. **TestOperationLogger** (3 tests)
   - Successful operations
   - Failed operations
   - Context data logging

6. **TestLogFunctionCall** (4 tests)
   - Basic function logging
   - Keyword arguments
   - Exception logging
   - Auto logger

7. **TestSessionLogger** (2 tests)
   - Default session logger
   - Custom session ID

8. **TestApplicationLogging** (4 tests)
   - Basic setup
   - File logging
   - Error file
   - Handler cleanup

9. **TestLOGLEVELS** (2 tests)
   - Level mapping
   - Completeness

10. **TestIntegration** (2 tests)
    - Full workflow
    - Logger isolation

11. **TestEdgeCases** (4 tests)
    - Unicode support
    - Long messages
    - Zero-time operations
    - Nested loggers

### test_performance.py (46 tests, 82% coverage)

Tests for performance monitoring.

**Test Classes**:

1. **TestPerformanceMetrics** (5 tests)
   - Metrics creation
   - Finalization
   - Error handling
   - Dictionary conversion
   - Metadata

2. **TestPerformanceMonitor** (7 tests)
   - Singleton pattern
   - Recording metrics
   - Disabled mode
   - Slow operation warnings
   - Statistics retrieval
   - Clearing metrics

3. **TestTrackPerformance** (3 tests)
   - Basic tracking
   - With metadata
   - Exception handling

4. **TestTimerDecorator** (4 tests)
   - Basic timing
   - Named operations
   - Result logging
   - Non-function usage

5. **TestPerformanceProfiler** (5 tests)
   - Basic profiling
   - Multiple checkpoints
   - Report generation
   - Empty reports
   - Percentage calculation

6. **TestBenchmark** (4 tests)
   - Basic benchmarking
   - With arguments
   - With keyword arguments
   - Statistics calculation

7. **TestAPICallTracker** (7 tests)
   - Tracker creation
   - Recording calls
   - Multiple calls
   - Metadata tracking
   - Statistics
   - Summary printing
   - Empty statistics

8. **TestConvenienceFunctions** (5 tests)
   - Get performance stats
   - Get all metrics
   - Clear metrics
   - Print summary

9. **TestIntegration** (2 tests)
   - Full workflow
   - API tracker integration

10. **TestEdgeCases** (4 tests)
    - Zero duration
    - Nested tracking
    - Single checkpoint profiler
    - No psutil support

### test_scene_models.py (37 tests, 86% coverage)

Tests for Pydantic data models.

**Test Classes**:

1. **TestInfoChange** (5 tests)
   - Valid info change
   - Observer character
   - Empty character validation
   - Whitespace handling
   - Character stripping

2. **TestRelationChange** (4 tests)
   - Valid relation change
   - from/to aliases
   - Two character requirement
   - Same character prevention

3. **TestKeyObject** (3 tests)
   - Valid key object
   - Empty object validation
   - Whitespace handling

4. **TestSetupPayoff** (4 tests)
   - Valid setup/payoff
   - Empty lists
   - Invalid scene ID format
   - Valid formats (S01, E01S01)

5. **TestSceneInfo** (6 tests)
   - Valid scene data
   - Scene ID validation
   - Setting validation
   - Key events validation
   - Character validation
   - Default optional fields

6. **TestOutlineSceneInfo** (5 tests)
   - Valid outline scene
   - Flexible scene ID
   - Flexible setting
   - More key events allowed
   - Empty characters allowed

7. **TestScriptEvaluation** (5 tests)
   - Valid evaluation
   - Auto score calculation
   - Scene count mismatch
   - Empty scenes
   - Partial validation

8. **TestValidateScriptJson** (5 tests)
   - Single scene validation
   - Scene list validation
   - Invalid data handling
   - Outline scene validation
   - Partial failures

---

## Testing Patterns

### Fixture Usage

**pytest fixtures** provide reusable test data:

```python
@pytest.fixture
def test_case(self):
    """Create LLMTestCase for testing"""
    return LLMTestCase(
        input="剧本文本内容...",
        actual_output=json.dumps([
            {
                "scene_id": "S01",
                "setting": "内景 房间 - 日",
                "characters": ["角色1", "角色2"],
                # ...
            }
        ], ensure_ascii=False)
    )

def test_measure_without_llm(self, test_case):
    metric = SceneBoundaryMetric(use_deepseek=False)
    score = metric.measure(test_case)
    assert 0 <= score <= 1
```

### Parametrized Tests

Test multiple inputs with single test function:

```python
@pytest.mark.parametrize("scene_id,expected", [
    ("S01", True),
    ("S02", True),
    ("E01S01", True),
    ("invalid", False),
    ("场景1", False),
])
def test_scene_id_validation(scene_id, expected):
    try:
        SceneInfo(
            scene_id=scene_id,
            setting="内景 房间 - 日",
            # ...
        )
        assert expected is True
    except ValidationError:
        assert expected is False
```

### Async Tests

Testing async methods:

```python
def test_async_measure(self, test_case):
    """测试异步评估方法"""
    import asyncio

    metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=False)
    score = asyncio.run(metric.a_measure(test_case))

    assert isinstance(score, float)
    assert 0 <= score <= 1
```

### Exception Testing

Testing expected exceptions:

```python
def test_invalid_json_in_test_case(self):
    """测试无效JSON"""
    test_case = LLMTestCase(
        input="文本",
        actual_output="invalid json"
    )

    metric = SceneBoundaryMetric(use_deepseek=False)
    with pytest.raises(json.JSONDecodeError):
        metric.measure(test_case)
```

### Capturing Output

Test logging output:

```python
def test_operation_logger_success(self, caplog):
    """测试成功操作的日志"""
    logger = get_logger("test_operation")

    with caplog.at_level(logging.INFO):
        with OperationLogger(logger, "测试操作", param1="value1"):
            time.sleep(0.01)

    assert "开始测试操作" in caplog.text
    assert "测试操作完成" in caplog.text
    assert "耗时" in caplog.text
```

---

## Mock Strategies

### Mocking LLM Client

Avoid actual API calls in tests:

```python
from unittest.mock import MagicMock, patch

def test_measure_with_llm(self, test_case):
    """测试使用LLM的评估"""
    mock_client = MagicMock()
    mock_client.complete.return_value = {
        "content": {
            "score": 0.85,
            "boundary_accuracy": "准确",
            "granularity": "合适",
            "completeness": "完整",
            "issues": [],
            "reasoning": "场景划分合理"
        }
    }

    with patch("src.metrics.deepeval_metrics.DeepSeekClient",
               return_value=mock_client):
        metric = SceneBoundaryMetric(threshold=0.7, use_deepseek=True)
        score = metric.measure(test_case)

        assert isinstance(score, float)
        assert score > 0
        mock_client.complete.assert_called_once()
```

### Mocking OpenAI API

```python
def test_complete_success(self):
    """测试成功的API调用"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"result": "success"}'))
    ]
    mock_response.usage.total_tokens = 1000
    mock_client.chat.completions.create.return_value = mock_response

    with patch("src.llm.deepseek_client.OpenAI", return_value=mock_client):
        client = DeepSeekClient(config)
        result = client.complete("test prompt")

        assert result["content"]["result"] == "success"
        assert result["tokens_used"] == 1000
```

### Mocking File Operations

```python
def test_file_read_error(self):
    """测试文件读取错误"""
    with patch("builtins.open", side_effect=IOError("Permission denied")):
        handler = FileHandler()
        with pytest.raises(FileReadError):
            handler.read_json("/path/to/file.json")
```

### Mocking Environment Variables

```python
def test_client_initialization_with_env(self):
    """测试从环境变量初始化"""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test_key_from_env",
        "DEEPSEEK_BASE_URL": "https://custom.api.url"
    }):
        client = DeepSeekClient()
        assert client.config.api_key == "test_key_from_env"
        assert client.config.base_url == "https://custom.api.url"
```

---

## Coverage Reports

### Generate Coverage Report

```bash
pytest --cov=src --cov-report=html tests/
```

Opens `htmlcov/index.html` in browser.

### Coverage by Module

```bash
pytest --cov=src --cov-report=term-missing tests/
```

Shows line-by-line coverage with missing lines.

### Current Coverage Summary

```
Name                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------
src/__init__.py                        0      0   100%
src/evaluators/__init__.py             0      0   100%
src/evaluators/main_evaluator.py     303    303     0%   6-715
src/llm/__init__.py                    0      0   100%
src/llm/deepseek_client.py           152     29    81%   28-38, 66...
src/metrics/__init__.py                0      0   100%
src/metrics/deepeval_metrics.py      280     21    92%   16-17...
src/models/__init__.py                 0      0   100%
src/models/scene_models.py           218     31    86%   58, 143...
src/utils/__init__.py                  0      0   100%
src/utils/exceptions.py              187     26    86%   89-93...
src/utils/file_handler.py            116    116     0%   6-296
src/utils/logger.py                  150     25    83%   91, 283...
src/utils/performance.py             244     44    82%   17-21...
----------------------------------------------------------------
TOTAL                               1650    595    64%
```

---

## Common Test Issues and Solutions

### Issue: numpy Boolean Type

**Problem**: `metric.success` returns `np.True_`/`np.False_` instead of Python bool

**Solution**:
```python
# Instead of:
assert isinstance(metric.success, bool)

# Use:
assert metric.success in [True, False]  # numpy compatible
```

### Issue: Import Errors in Tests

**Problem**: Relative imports fail when running tests

**Solution**: Use dual import strategy:
```python
try:
    from ..utils.exceptions import APIError
except ImportError:
    from utils.exceptions import APIError
```

### Issue: LLM Response Format

**Problem**: LLM may return JSON string instead of dict

**Solution**:
```python
result = response["content"]
if isinstance(result, str):
    result = json.loads(result)
return result.get("score", 0.5)
```

---

## Best Practices

1. **Always use fixtures for reusable data** - Avoid duplication
2. **Mock external dependencies** - No real API calls, no network I/O
3. **Test edge cases** - Empty data, invalid input, boundary values
4. **Use descriptive test names** - Should explain what is being tested
5. **One assertion per test** - Or related assertions only
6. **Clean up after tests** - Use fixtures with cleanup or context managers
7. **Test both success and failure paths** - Positive and negative cases
8. **Use parametrize for similar tests** - Reduces code duplication
9. **Check coverage regularly** - Aim for >80% on core modules
10. **Write tests before fixing bugs** - TDD for bug fixes

---

## Future Testing Plans

### Short-term

- [ ] Add unit tests for `main_evaluator.py` (currently 0% coverage)
- [ ] Add unit tests for `file_handler.py` (currently 0% coverage)
- [ ] Increase overall coverage to 75%+

### Medium-term

- [ ] Add integration tests for complete evaluation workflows
- [ ] Add end-to-end tests with real script samples
- [ ] Add performance regression tests
- [ ] Set up CI/CD with automated testing

### Long-term

- [ ] Achieve 80%+ overall coverage
- [ ] Add property-based testing with hypothesis
- [ ] Add mutation testing
- [ ] Benchmark suite for performance tracking

---

## Related Documentation

- [Utils Reference](utils-reference.md) - Utilities being tested
- [API Reference](api-reference.md) - APIs being tested
- [Development Guide](development.md) - Development workflows

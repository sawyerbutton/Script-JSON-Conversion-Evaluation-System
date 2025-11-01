# Utilities Reference

This document covers the utility modules that provide error handling, logging, and performance monitoring for the Script JSON Conversion Evaluation System.

## Table of Contents

- [Exceptions](#exceptions)
- [Logger](#logger)
- [Performance Monitoring](#performance-monitoring)
- [File Handler](#file-handler)

---

## Exceptions

**Module**: `src/utils/exceptions.py` (187 lines, 86% test coverage)

Comprehensive exception hierarchy for type-safe error handling across the system.

### Exception Hierarchy

```
Exception
└── ScriptEvaluationError (base for all custom exceptions)
    ├── APIError
    │   ├── APIConnectionError
    │   ├── APIRateLimitError
    │   ├── APITimeoutError
    │   ├── APIResponseError
    │   └── APIQuotaExceededError
    ├── ValidationError
    │   ├── JSONValidationError
    │   ├── SceneValidationError
    │   └── CharacterValidationError
    ├── FileError
    │   ├── FileNotFoundError
    │   ├── FileReadError
    │   ├── FileWriteError
    │   └── FileFormatError
    ├── EvaluationError
    │   ├── MetricCalculationError
    │   ├── EvaluationConfigError
    │   └── InsufficientDataError
    ├── ConversionError
    │   ├── ScriptParsingError
    │   └── JSONGenerationError
    └── ConfigurationError
        ├── MissingConfigError
        └── InvalidConfigError
```

### Base Exception

All custom exceptions inherit from `ScriptEvaluationError`:

```python
class ScriptEvaluationError(Exception):
    """Base exception for script evaluation system"""

    def __init__(self, message: str, details: Optional[Dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
```

### API Exceptions

**APIConnectionError** - Network connection failures
```python
raise APIConnectionError(
    "无法连接到DeepSeek API",
    details={"endpoint": "https://api.deepseek.com", "error": str(e)}
)
```

**APIRateLimitError** - Rate limit exceeded
```python
raise APIRateLimitError(
    "API请求频率超限",
    details={"retry_after": 60}
)
```

**APITimeoutError** - Request timeout
```python
raise APITimeoutError(
    "API请求超时",
    details={"timeout": 30}
)
```

**APIQuotaExceededError** - API quota exceeded (critical)
```python
raise APIQuotaExceededError(
    "API配额已用尽",
    details={"quota": 1000000}
)
```

### Validation Exceptions

**SceneValidationError** - Scene data validation failures
```python
raise SceneValidationError(
    scene_id="S01",
    message="场景信息不完整",
    details={"missing_fields": ["key_events"]}
)
```

**CharacterValidationError** - Character data validation failures
```python
raise CharacterValidationError(
    character="角色A",
    message="角色信息不一致"
)
```

### File Exceptions

**FileNotFoundError** - File not found
```python
raise FileNotFoundError("/path/to/file.json")
```

**FileReadError** - File read failures
```python
raise FileReadError(
    "/path/to/file.json",
    details={"error": "Permission denied"}
)
```

**FileWriteError** - File write failures
```python
raise FileWriteError(
    "/path/to/output.json",
    details={"error": str(e)}
)
```

### Helper Functions

**is_retryable_error(error)** - Check if error is retryable
```python
from src.utils.exceptions import is_retryable_error

try:
    api_call()
except Exception as e:
    if is_retryable_error(e):
        retry_with_backoff()
    else:
        raise
```

Retryable errors:
- `APIConnectionError`
- `APITimeoutError`
- `APIRateLimitError`

**get_error_severity(error)** - Get error severity level
```python
from src.utils.exceptions import get_error_severity

try:
    operation()
except Exception as e:
    severity = get_error_severity(e)
    if severity == "critical":
        alert_admin()
```

Severity levels:
- `critical`: APIQuotaExceededError, ConfigurationError
- `high`: APIError, FileError, EvaluationError
- `medium`: ValidationError, ConversionError
- `low`: Other exceptions

**format_exception(error, include_traceback=False)** - Format exception for logging
```python
from src.utils.exceptions import format_exception

try:
    operation()
except Exception as e:
    formatted = format_exception(e, include_traceback=True)
    logger.error(formatted)
```

### Error Context Manager

**ErrorContext** - Context manager for structured error handling
```python
from src.utils.exceptions import ErrorContext

with ErrorContext("处理文件", file_path="/path/to/file.json") as ctx:
    process_file()

# Access error info after block
if ctx.exception:
    print(f"Error occurred: {ctx.exception}")
    print(f"Context: {ctx.context}")
```

Options:
- `raise_on_error`: Re-raise exceptions (default: True)
- `log_errors`: Log errors automatically (default: True)
- `logger`: Custom logger instance

---

## Logger

**Module**: `src/utils/logger.py` (150 lines, 83% test coverage)

Professional logging system with colored console output, file logging, and context managers.

### Quick Start

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
logger.warning("Low memory")
logger.error("Failed to connect")
```

### Logger Configuration

**get_logger(name)** - Get or create logger
```python
logger = get_logger("my_module")
```

**setup_logger(name, level, log_file, log_dir, format_style, use_colors)** - Setup custom logger
```python
from src.utils.logger import setup_logger

logger = setup_logger(
    name="evaluation",
    level="DEBUG",
    log_file="evaluation.log",
    log_dir="logs",
    format_style="detailed",  # simple/standard/detailed
    use_colors=True
)
```

Format styles:
- `simple`: `"%(message)s"`
- `standard`: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- `detailed`: `"%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"`

**setup_application_logging(level, log_to_file, log_dir)** - Setup root logger
```python
from src.utils.logger import setup_application_logging

setup_application_logging(
    level="INFO",
    log_to_file=True,
    log_dir="logs"
)
```

Creates two log files:
- `app_YYYYMMDD_HHMMSS.log` - All logs
- `error_YYYYMMDD_HHMMSS.log` - Errors only

### Context Managers

**LoggerContext** - Temporarily change log level
```python
from src.utils.logger import LoggerContext

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

with LoggerContext(logger, level="DEBUG"):
    logger.debug("This will be logged")
    detailed_operation()

# Logger restored to INFO level
logger.debug("This will NOT be logged")
```

**OperationLogger** - Log operation start/end with timing
```python
from src.utils.logger import OperationLogger

logger = get_logger(__name__)

with OperationLogger(logger, "数据处理", file_path="data.json"):
    process_data()

# Logs:
# INFO: 开始数据处理 - file_path=data.json
# INFO: 数据处理完成 - 耗时: 1.23秒
```

### Decorators

**@log_function_call** - Log function entry/exit
```python
from src.utils.logger import log_function_call, get_logger

logger = get_logger(__name__)

@log_function_call(logger=logger, level="INFO")
def process_file(path: str, validate: bool = True):
    # ... function code ...
    return result

# Logs:
# INFO: 调用 process_file(path='/data.json', validate=True)
# INFO: process_file 完成 - 耗时: 0.5秒
```

### Session Logger

**create_session_logger(session_id, log_dir)** - Create session-specific logger
```python
from src.utils.logger import create_session_logger

session_logger = create_session_logger(
    session_id="eval_20231101_143022",
    log_dir="logs/sessions"
)
```

### Colored Formatting

**ColoredFormatter** - Color-coded log levels for console
```python
from src.utils.logger import ColoredFormatter

formatter = ColoredFormatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
```

Colors:
- DEBUG: Cyan
- INFO: Green
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Red + Bold

---

## Performance Monitoring

**Module**: `src/utils/performance.py` (244 lines, 82% test coverage)

Comprehensive performance profiling, timing, and API call tracking.

### Performance Metrics

**PerformanceMetrics** - Container for performance data
```python
from src.utils.performance import PerformanceMetrics

metrics = PerformanceMetrics(operation="evaluation")
# ... perform operation ...
metrics.finalize()

print(f"Duration: {metrics.duration:.2f}s")
print(f"Memory: {metrics.memory_delta_mb:.2f}MB")
```

### Performance Monitor (Singleton)

**PerformanceMonitor** - Global performance tracking
```python
from src.utils.performance import PerformanceMonitor

monitor = PerformanceMonitor()

# Record operation
metrics = PerformanceMetrics(operation="processing")
metrics.finalize()
monitor.record(metrics)

# Get stats
stats = monitor.get_stats("processing")
print(f"Average: {stats['avg_duration']:.2f}s")
print(f"Total calls: {stats['count']}")

# Get all stats
all_stats = monitor.get_all_stats()

# Clear stats
monitor.clear()
```

Disable monitoring:
```python
monitor = PerformanceMonitor(enabled=False)
```

### Decorators and Context Managers

**@timer** - Time function execution
```python
from src.utils.performance import timer

@timer(name="数据处理", log_result=True)
def process_data(data):
    # ... processing ...
    return result

# Logs: 数据处理 耗时: 1.23秒
```

**track_performance** - Context manager for performance tracking
```python
from src.utils.performance import track_performance

with track_performance("文件处理", file_path="data.json"):
    process_file()

# Automatically records metrics to PerformanceMonitor
```

### Performance Profiler

**PerformanceProfiler** - Multi-checkpoint profiling
```python
from src.utils.performance import PerformanceProfiler

profiler = PerformanceProfiler("评估流程")

profiler.start("初始化")
initialize()

profiler.checkpoint("验证")
validate()

profiler.checkpoint("计算指标")
calculate_metrics()

profiler.checkpoint("生成报告")
generate_report()

profiler.stop()
profiler.print_report()
```

Output:
```
============================================================
性能分析报告: 评估流程
总耗时: 2.45秒
============================================================

初始化 → 验证: 0.50秒 (20.4%)
验证 → 计算指标: 1.20秒 (49.0%)
计算指标 → 生成报告: 0.75秒 (30.6%)

============================================================
```

### Benchmarking

**benchmark(func, iterations, *args, **kwargs)** - Benchmark function performance
```python
from src.utils.performance import benchmark

def expensive_operation(n):
    return sum(i**2 for i in range(n))

stats = benchmark(expensive_operation, iterations=100, n=10000)

print(f"Mean: {stats['mean']:.4f}s")
print(f"Min: {stats['min']:.4f}s")
print(f"Max: {stats['max']:.4f}s")
print(f"Std: {stats['std']:.4f}s")
```

### API Call Tracker

**APICallTracker** - Track API usage and costs
```python
from src.utils.performance import APICallTracker

tracker = APICallTracker()

# Record API call
tracker.record_call(
    endpoint="deepseek_chat",
    duration=1.5,
    tokens=1000,
    cost=0.002,
    success=True,
    metadata={"model": "deepseek-chat"}
)

# Get statistics
stats = tracker.get_stats()
print(f"Total calls: {stats['total_calls']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Total tokens: {stats['total_tokens']:,}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Avg duration: {stats['avg_duration']:.2f}s")

# Print summary
tracker.print_summary()
```

Output:
```
============================================================
API调用统计
============================================================
总调用次数: 42
成功: 40 (95.2%)
失败: 2 (4.8%)

总tokens: 125,430
总耗时: 52.3秒
总成本: $0.2509

平均每次调用:
  - Tokens: 2,986
  - 耗时: 1.24秒
  - 成本: $0.0060
============================================================
```

### Convenience Functions

```python
from src.utils.performance import (
    get_performance_stats,
    get_all_metrics,
    clear_metrics,
    print_performance_summary
)

# Get stats for specific operation
stats = get_performance_stats("evaluation")

# Get all recorded metrics
all_metrics = get_all_metrics()

# Clear all metrics
clear_metrics()

# Print summary of all operations
print_performance_summary()
```

---

## File Handler

**Module**: `src/utils/file_handler.py` (116 lines, 0% test coverage*)

*Note: Covered by integration tests, unit tests pending*

File I/O operations with error handling.

### FileHandler Class

```python
from src.utils.file_handler import FileHandler

handler = FileHandler()

# Read JSON
data = handler.read_json("input.json")

# Write JSON
handler.write_json(data, "output.json", ensure_dir=True)

# Read text
content = handler.read_text("script.md")

# Write text
handler.write_text("converted output", "result.txt")

# Check file exists
if handler.file_exists("config.yaml"):
    # ...

# Ensure directory exists
handler.ensure_dir("outputs/reports")
```

### Error Handling

All methods raise appropriate exceptions from `src.utils.exceptions`:
- `FileNotFoundError` - File doesn't exist
- `FileReadError` - Cannot read file
- `FileWriteError` - Cannot write file
- `FileFormatError` - Invalid JSON format

---

## Usage Patterns

### Complete Error Handling Example

```python
from src.utils.exceptions import (
    ErrorContext,
    APIConnectionError,
    is_retryable_error
)
from src.utils.logger import get_logger, OperationLogger
from src.utils.performance import track_performance

logger = get_logger(__name__)

def process_with_monitoring(file_path: str):
    """Complete example with all utilities"""

    with ErrorContext("处理文件", file_path=file_path):
        with OperationLogger(logger, "文件处理", file=file_path):
            with track_performance("文件处理", file_path=file_path):
                # Your processing logic
                data = read_file(file_path)
                result = transform(data)
                save_result(result)

                return result

# With retry logic
max_retries = 3
for attempt in range(max_retries):
    try:
        result = api_call()
        break
    except Exception as e:
        if is_retryable_error(e) and attempt < max_retries - 1:
            logger.warning(f"Retry {attempt + 1}/{max_retries}")
            time.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

### Performance Profiling Example

```python
from src.utils.performance import PerformanceProfiler, APICallTracker
from src.utils.logger import get_logger

logger = get_logger(__name__)

def evaluate_script(script_text: str):
    profiler = PerformanceProfiler("剧本评估")
    api_tracker = APICallTracker()

    profiler.start("初始化")
    evaluator = setup_evaluator()

    profiler.checkpoint("结构验证")
    structure_score = validate_structure(script_text)

    profiler.checkpoint("LLM评估")
    start = time.time()
    llm_score = llm_evaluate(script_text)
    duration = time.time() - start

    api_tracker.record_call(
        endpoint="deepseek_evaluate",
        duration=duration,
        tokens=2500,
        cost=0.005,
        success=True
    )

    profiler.checkpoint("生成报告")
    report = generate_report(structure_score, llm_score)

    profiler.stop()

    if logger.level <= 10:  # DEBUG
        profiler.print_report()
        api_tracker.print_summary()

    return report
```

---

## Best Practices

1. **Always use custom exceptions** - Don't raise generic `Exception`
2. **Use ErrorContext for complex operations** - Automatic error logging and context
3. **Use OperationLogger for long operations** - Track start/end and duration
4. **Profile performance-critical code** - Use PerformanceProfiler for multi-step operations
5. **Track API usage** - Use APICallTracker to monitor costs and performance
6. **Log at appropriate levels** - DEBUG for details, INFO for progress, WARNING for issues, ERROR for failures
7. **Clean up metrics periodically** - Call `clear_metrics()` to avoid memory buildup

---

## Related Documentation

- [API Reference](api-reference.md) - Main API documentation
- [Development Guide](development.md) - Development workflows
- [Testing Guide](testing-reference.md) - Testing utilities and patterns

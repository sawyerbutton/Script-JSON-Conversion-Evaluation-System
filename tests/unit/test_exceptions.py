"""
测试自定义异常模块
"""

import pytest

from src.utils.exceptions import (
    # 基础异常
    ScriptEvaluationError,
    # API异常
    APIError,
    APIConnectionError,
    APIRateLimitError,
    APITimeoutError,
    APIResponseError,
    APIQuotaExceededError,
    # 验证异常
    ValidationError,
    JSONValidationError,
    SceneValidationError,
    CharacterValidationError,
    # 文件异常
    FileError,
    FileNotFoundError,
    FileReadError,
    FileWriteError,
    FileFormatError,
    # 评估异常
    EvaluationError,
    MetricCalculationError,
    EvaluationConfigError,
    InsufficientDataError,
    # 转换异常
    ConversionError,
    ScriptParsingError,
    JSONGenerationError,
    # 配置异常
    ConfigurationError,
    MissingConfigError,
    InvalidConfigError,
    # 辅助函数
    is_retryable_error,
    get_error_severity,
    format_exception,
    ErrorContext,
)


class TestBaseException:
    """测试基础异常类"""

    def test_script_evaluation_error_basic(self):
        """测试基础异常创建"""
        error = ScriptEvaluationError("测试错误")
        assert str(error) == "测试错误"
        assert error.message == "测试错误"
        assert error.details == {}

    def test_script_evaluation_error_with_details(self):
        """测试带详细信息的异常"""
        details = {"file": "test.json", "line": 10}
        error = ScriptEvaluationError("测试错误", details=details)
        assert error.message == "测试错误"
        assert error.details == details
        assert error.details["file"] == "test.json"
        assert error.details["line"] == 10

    def test_script_evaluation_error_str(self):
        """测试异常字符串表示"""
        error = ScriptEvaluationError("错误信息", details={"key": "value"})
        error_str = str(error)
        assert "错误信息" in error_str


class TestAPIExceptions:
    """测试API相关异常"""

    def test_api_error(self):
        """测试API基础错误"""
        error = APIError("API错误")
        assert isinstance(error, ScriptEvaluationError)
        assert error.message == "API错误"

    def test_api_connection_error(self):
        """测试API连接错误"""
        error = APIConnectionError("连接失败", details={"host": "api.example.com"})
        assert isinstance(error, APIError)
        assert error.message == "连接失败"
        assert error.details["host"] == "api.example.com"

    def test_api_rate_limit_error(self):
        """测试API限流错误"""
        error = APIRateLimitError("请求过于频繁")
        assert isinstance(error, APIError)
        assert "请求过于频繁" in error.message

    def test_api_timeout_error(self):
        """测试API超时错误"""
        error = APITimeoutError("请求超时", details={"timeout": 30})
        assert isinstance(error, APIError)
        assert error.details["timeout"] == 30

    def test_api_response_error(self):
        """测试API响应错误"""
        error = APIResponseError("响应格式错误", details={"status_code": 500})
        assert isinstance(error, APIError)
        assert error.details["status_code"] == 500

    def test_api_quota_exceeded_error(self):
        """测试API配额超限错误"""
        error = APIQuotaExceededError("配额已用完")
        assert isinstance(error, APIError)
        assert "配额" in error.message


class TestValidationExceptions:
    """测试验证相关异常"""

    def test_validation_error(self):
        """测试验证基础错误"""
        error = ValidationError("验证失败")
        assert isinstance(error, ScriptEvaluationError)

    def test_json_validation_error(self):
        """测试JSON验证错误"""
        error = JSONValidationError(
            "JSON格式错误", details={"field": "scene_id", "expected": "string"}
        )
        assert isinstance(error, ValidationError)
        assert error.details["field"] == "scene_id"

    def test_scene_validation_error(self):
        """测试场景验证错误"""
        error = SceneValidationError(scene_id="S01", message="场景信息不完整")
        assert isinstance(error, ValidationError)
        assert error.details["scene_id"] == "S01"
        assert "场景信息不完整" in error.message

    def test_character_validation_error(self):
        """测试角色验证错误"""
        error = CharacterValidationError(
            "角色列表为空", details={"scene": "S01", "characters": []}
        )
        assert isinstance(error, ValidationError)
        assert error.details["characters"] == []


class TestFileExceptions:
    """测试文件相关异常"""

    def test_file_error(self):
        """测试文件基础错误"""
        error = FileError("文件操作失败")
        assert isinstance(error, ScriptEvaluationError)

    def test_file_not_found_error(self):
        """测试文件不存在错误"""
        error = FileNotFoundError("/path/to/file.txt")
        assert isinstance(error, FileError)
        assert error.details["file_path"] == "/path/to/file.txt"
        assert "不存在" in error.message

    def test_file_read_error(self):
        """测试文件读取错误"""
        error = FileReadError("test.json")
        assert isinstance(error, FileError)
        assert error.details["file_path"] == "test.json"

    def test_file_write_error(self):
        """测试文件写入错误"""
        error = FileWriteError("output.json")
        assert isinstance(error, FileError)
        assert error.details["file_path"] == "output.json"

    def test_file_format_error(self):
        """测试文件格式错误"""
        error = FileFormatError("test.xyz", expected_format=".json")
        assert isinstance(error, FileError)
        assert error.details["file_path"] == "test.xyz"
        assert error.details["expected_format"] == ".json"


class TestEvaluationExceptions:
    """测试评估相关异常"""

    def test_evaluation_error(self):
        """测试评估基础错误"""
        error = EvaluationError("评估失败")
        assert isinstance(error, ScriptEvaluationError)

    def test_metric_calculation_error(self):
        """测试指标计算错误"""
        error = MetricCalculationError("boundary_score", details={"value": None})
        assert isinstance(error, EvaluationError)
        assert error.details["metric_name"] == "boundary_score"
        assert "boundary_score" in error.message

    def test_evaluation_config_error(self):
        """测试评估配置错误"""
        error = EvaluationConfigError(
            "配置参数无效", details={"parameter": "threshold", "value": 1.5}
        )
        assert isinstance(error, EvaluationError)

    def test_insufficient_data_error(self):
        """测试数据不足错误"""
        error = InsufficientDataError(
            "数据不足以进行评估", details={"required": 10, "actual": 3}
        )
        assert isinstance(error, EvaluationError)
        assert error.details["required"] == 10
        assert error.details["actual"] == 3


class TestConversionExceptions:
    """测试转换相关异常"""

    def test_conversion_error(self):
        """测试转换基础错误"""
        error = ConversionError("转换失败")
        assert isinstance(error, ScriptEvaluationError)

    def test_script_parsing_error(self):
        """测试剧本解析错误"""
        error = ScriptParsingError("无法解析剧本", details={"line": 42, "content": "..."})
        assert isinstance(error, ConversionError)
        assert error.details["line"] == 42

    def test_json_generation_error(self):
        """测试JSON生成错误"""
        error = JSONGenerationError("生成JSON失败", details={"reason": "缺少必需字段"})
        assert isinstance(error, ConversionError)


class TestConfigurationExceptions:
    """测试配置相关异常"""

    def test_configuration_error(self):
        """测试配置基础错误"""
        error = ConfigurationError("配置错误")
        assert isinstance(error, ScriptEvaluationError)

    def test_missing_config_error(self):
        """测试缺少配置错误"""
        error = MissingConfigError("API_KEY")
        assert isinstance(error, ConfigurationError)
        assert error.details["config_key"] == "API_KEY"
        assert "API_KEY" in error.message

    def test_invalid_config_error(self):
        """测试无效配置错误"""
        error = InvalidConfigError("timeout", "-1")
        assert isinstance(error, ConfigurationError)
        assert error.details["config_key"] == "timeout"
        assert error.details["value"] == "-1"


class TestHelperFunctions:
    """测试辅助函数"""

    def test_is_retryable_error_connection(self):
        """测试连接错误是可重试的"""
        error = APIConnectionError("连接失败")
        assert is_retryable_error(error) is True

    def test_is_retryable_error_timeout(self):
        """测试超时错误是可重试的"""
        error = APITimeoutError("请求超时")
        assert is_retryable_error(error) is True

    def test_is_retryable_error_rate_limit(self):
        """测试限流错误是可重试的"""
        error = APIRateLimitError("请求过于频繁")
        assert is_retryable_error(error) is True

    def test_is_retryable_error_not_retryable(self):
        """测试不可重试的错误"""
        error = JSONValidationError("JSON格式错误")
        assert is_retryable_error(error) is False

    def test_is_retryable_error_generic_exception(self):
        """测试通用异常不可重试"""
        error = ValueError("普通错误")
        assert is_retryable_error(error) is False

    def test_get_error_severity_critical(self):
        """测试严重错误级别"""
        assert get_error_severity(APIQuotaExceededError("配额超限")) == "critical"
        assert get_error_severity(ConfigurationError("配置错误")) == "critical"
        assert get_error_severity(MissingConfigError("API_KEY")) == "critical"

    def test_get_error_severity_high(self):
        """测试高级别错误"""
        assert get_error_severity(FileNotFoundError("test.txt")) == "high"
        assert get_error_severity(FileReadError("test.txt")) == "high"
        assert get_error_severity(JSONValidationError("验证失败")) == "high"
        assert get_error_severity(ScriptParsingError("解析失败")) == "high"

    def test_get_error_severity_medium(self):
        """测试中级别错误"""
        assert get_error_severity(ValidationError("验证失败")) == "medium"
        assert get_error_severity(EvaluationError("评估失败")) == "medium"
        assert get_error_severity(SceneValidationError()) == "medium"
        assert get_error_severity(ValueError("普通异常")) == "medium"  # 默认值

    def test_get_error_severity_low(self):
        """测试低级别错误"""
        assert get_error_severity(APITimeoutError("超时")) == "low"
        assert get_error_severity(APIConnectionError("连接失败")) == "low"

    def test_format_exception_basic(self):
        """测试格式化错误信息（基础）"""
        error = ScriptEvaluationError("测试错误")
        formatted = format_exception(error)
        assert "ScriptEvaluationError" in formatted
        assert "测试错误" in formatted

    def test_format_exception_with_details(self):
        """测试格式化错误信息（带详细信息）"""
        error = APIConnectionError("连接失败", details={"host": "api.test.com", "port": 443})
        formatted = format_exception(error)
        assert "APIConnectionError" in formatted
        assert "连接失败" in formatted

    def test_format_exception_with_traceback(self):
        """测试格式化错误信息（带堆栈跟踪）"""
        try:
            raise ScriptEvaluationError("测试错误")
        except ScriptEvaluationError as e:
            formatted = format_exception(e, include_traceback=True)
            assert "ScriptEvaluationError" in formatted
            assert "堆栈跟踪" in formatted

    def test_format_exception_generic_exception(self):
        """测试格式化通用异常"""
        error = ValueError("普通错误")
        formatted = format_exception(error)
        assert "ValueError" in formatted
        assert "普通错误" in formatted


class TestErrorContext:
    """测试错误上下文管理器"""

    def test_error_context_success(self):
        """测试成功执行的情况"""
        with ErrorContext("测试操作"):
            result = 1 + 1
        assert result == 2

    def test_error_context_with_exception(self):
        """测试捕获异常"""
        # ErrorContext 默认会记录日志并重新抛出原始异常
        with pytest.raises(ValueError) as exc_info:
            with ErrorContext("测试操作", operation_type="test"):
                raise ValueError("测试错误")

        assert "测试错误" in str(exc_info.value)

    def test_error_context_no_raise(self):
        """测试不抛出异常模式"""
        with ErrorContext("测试操作", raise_on_error=False) as ctx:
            raise ValueError("测试错误")

        assert ctx.exception is not None
        assert isinstance(ctx.exception, ValueError)

    def test_error_context_with_context_data(self):
        """测试带上下文数据"""
        # ErrorContext 会记录上下文数据到日志，但不会修改异常本身
        with pytest.raises(ValueError) as exc_info:
            with ErrorContext("测试操作", file_path="test.json", line_number=10):
                raise ValueError("测试错误")

        assert "测试错误" in str(exc_info.value)

    def test_error_context_returns_self(self):
        """测试上下文管理器返回自身"""
        with ErrorContext("测试操作") as ctx:
            assert ctx is not None
            assert ctx.operation == "测试操作"

    def test_error_context_script_evaluation_error(self):
        """测试捕获ScriptEvaluationError时不包装"""
        original_error = APIConnectionError("连接失败", details={"host": "test.com"})

        with pytest.raises(APIConnectionError) as exc_info:
            with ErrorContext("测试操作"):
                raise original_error

        # 应该是同一个错误，不是被包装的
        assert exc_info.value is original_error or exc_info.value.message == original_error.message


class TestExceptionHierarchy:
    """测试异常继承层次"""

    def test_api_exceptions_hierarchy(self):
        """测试API异常继承层次"""
        assert issubclass(APIConnectionError, APIError)
        assert issubclass(APIRateLimitError, APIError)
        assert issubclass(APITimeoutError, APIError)
        assert issubclass(APIResponseError, APIError)
        assert issubclass(APIQuotaExceededError, APIError)
        assert issubclass(APIError, ScriptEvaluationError)

    def test_validation_exceptions_hierarchy(self):
        """测试验证异常继承层次"""
        assert issubclass(JSONValidationError, ValidationError)
        assert issubclass(SceneValidationError, ValidationError)
        assert issubclass(CharacterValidationError, ValidationError)
        assert issubclass(ValidationError, ScriptEvaluationError)

    def test_file_exceptions_hierarchy(self):
        """测试文件异常继承层次"""
        assert issubclass(FileNotFoundError, FileError)
        assert issubclass(FileReadError, FileError)
        assert issubclass(FileWriteError, FileError)
        assert issubclass(FileFormatError, FileError)
        assert issubclass(FileError, ScriptEvaluationError)

    def test_evaluation_exceptions_hierarchy(self):
        """测试评估异常继承层次"""
        assert issubclass(MetricCalculationError, EvaluationError)
        assert issubclass(EvaluationConfigError, EvaluationError)
        assert issubclass(InsufficientDataError, EvaluationError)
        assert issubclass(EvaluationError, ScriptEvaluationError)

    def test_conversion_exceptions_hierarchy(self):
        """测试转换异常继承层次"""
        assert issubclass(ScriptParsingError, ConversionError)
        assert issubclass(JSONGenerationError, ConversionError)
        assert issubclass(ConversionError, ScriptEvaluationError)

    def test_configuration_exceptions_hierarchy(self):
        """测试配置异常继承层次"""
        assert issubclass(MissingConfigError, ConfigurationError)
        assert issubclass(InvalidConfigError, ConfigurationError)
        assert issubclass(ConfigurationError, ScriptEvaluationError)

    def test_all_inherit_from_exception(self):
        """测试所有异常都继承自Exception"""
        exceptions = [
            ScriptEvaluationError,
            APIError,
            ValidationError,
            FileError,
            EvaluationError,
            ConversionError,
            ConfigurationError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, Exception)


class TestExceptionUsagePatterns:
    """测试异常使用模式"""

    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        with pytest.raises(APIConnectionError):
            raise APIConnectionError("连接失败")

    def test_catch_parent_exception(self):
        """测试捕获父类异常"""
        with pytest.raises(APIError):
            raise APIConnectionError("连接失败")

    def test_catch_base_exception(self):
        """测试捕获基类异常"""
        with pytest.raises(ScriptEvaluationError):
            raise JSONValidationError("验证失败")

    def test_multiple_exception_handling(self):
        """测试多异常处理"""

        def risky_operation(error_type):
            if error_type == "connection":
                raise APIConnectionError("连接失败")
            elif error_type == "validation":
                raise JSONValidationError("验证失败")
            elif error_type == "file":
                raise FileReadError("读取失败")

        # 捕获API错误
        with pytest.raises(APIError):
            risky_operation("connection")

        # 捕获验证错误
        with pytest.raises(ValidationError):
            risky_operation("validation")

        # 捕获文件错误
        with pytest.raises(FileError):
            risky_operation("file")

    def test_exception_with_retry_logic(self):
        """测试带重试逻辑的异常处理"""
        max_retries = 3
        attempts = 0

        def operation_with_retry():
            nonlocal attempts
            attempts += 1
            if attempts < max_retries:
                raise APIRateLimitError("限流")
            return "成功"

        result = None
        for i in range(max_retries):
            try:
                result = operation_with_retry()
                break
            except Exception as e:
                if is_retryable_error(e) and i < max_retries - 1:
                    continue
                else:
                    raise

        assert result == "成功"
        assert attempts == max_retries

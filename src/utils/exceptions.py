"""
自定义异常类
为不同的错误场景定义清晰的异常层次结构
"""


class ScriptEvaluationError(Exception):
    """评估系统基础异常类"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# ============================================================================
# API相关异常
# ============================================================================


class APIError(ScriptEvaluationError):
    """API调用相关的基础异常"""

    pass


class APIConnectionError(APIError):
    """API连接失败"""

    def __init__(self, message: str = "无法连接到API服务", details: dict = None):
        super().__init__(message, details)


class APIRateLimitError(APIError):
    """API限流错误"""

    def __init__(self, message: str = "API请求频率超限", details: dict = None):
        super().__init__(message, details)


class APITimeoutError(APIError):
    """API请求超时"""

    def __init__(self, message: str = "API请求超时", details: dict = None):
        super().__init__(message, details)


class APIResponseError(APIError):
    """API响应格式错误"""

    def __init__(self, message: str = "API响应格式不正确", details: dict = None):
        super().__init__(message, details)


class APIQuotaExceededError(APIError):
    """API配额耗尽"""

    def __init__(self, message: str = "API配额已用尽", details: dict = None):
        super().__init__(message, details)


# ============================================================================
# 数据验证相关异常
# ============================================================================


class ValidationError(ScriptEvaluationError):
    """数据验证相关的基础异常"""

    pass


class JSONValidationError(ValidationError):
    """JSON格式验证失败"""

    def __init__(
        self,
        message: str = "JSON数据验证失败",
        validation_errors: list = None,
        details: dict = None,
    ):
        self.validation_errors = validation_errors or []
        super().__init__(message, details)

    def __str__(self):
        base = super().__str__()
        if self.validation_errors:
            errors_str = "\n  - ".join(str(e) for e in self.validation_errors[:5])
            return f"{base}\n验证错误:\n  - {errors_str}"
        return base


class SceneValidationError(ValidationError):
    """场景数据验证失败"""

    def __init__(
        self, scene_id: str = None, message: str = "场景数据验证失败", details: dict = None
    ):
        details = details or {}
        if scene_id:
            details["scene_id"] = scene_id
        super().__init__(message, details)


class CharacterValidationError(ValidationError):
    """角色数据验证失败"""

    def __init__(
        self, character: str = None, message: str = "角色数据验证失败", details: dict = None
    ):
        details = details or {}
        if character:
            details["character"] = character
        super().__init__(message, details)


# ============================================================================
# 文件处理相关异常
# ============================================================================


class FileError(ScriptEvaluationError):
    """文件处理相关的基础异常"""

    pass


class FileNotFoundError(FileError):
    """文件不存在"""

    def __init__(self, file_path: str, message: str = None, details: dict = None):
        message = message or f"文件不存在: {file_path}"
        details = details or {}
        details["file_path"] = file_path
        super().__init__(message, details)


class FileReadError(FileError):
    """文件读取失败"""

    def __init__(self, file_path: str, message: str = None, details: dict = None):
        message = message or f"无法读取文件: {file_path}"
        details = details or {}
        details["file_path"] = file_path
        super().__init__(message, details)


class FileWriteError(FileError):
    """文件写入失败"""

    def __init__(self, file_path: str, message: str = None, details: dict = None):
        message = message or f"无法写入文件: {file_path}"
        details = details or {}
        details["file_path"] = file_path
        super().__init__(message, details)


class FileFormatError(FileError):
    """文件格式错误"""

    def __init__(self, file_path: str, expected_format: str = None, details: dict = None):
        message = f"文件格式错误: {file_path}"
        if expected_format:
            message += f"，期望格式: {expected_format}"
        details = details or {}
        details["file_path"] = file_path
        if expected_format:
            details["expected_format"] = expected_format
        super().__init__(message, details)


# ============================================================================
# 评估相关异常
# ============================================================================


class EvaluationError(ScriptEvaluationError):
    """评估过程相关的基础异常"""

    pass


class MetricCalculationError(EvaluationError):
    """指标计算失败"""

    def __init__(self, metric_name: str, message: str = None, details: dict = None):
        message = message or f"指标 '{metric_name}' 计算失败"
        details = details or {}
        details["metric_name"] = metric_name
        super().__init__(message, details)


class EvaluationConfigError(EvaluationError):
    """评估配置错误"""

    def __init__(self, message: str = "评估配置不正确", details: dict = None):
        super().__init__(message, details)


class InsufficientDataError(EvaluationError):
    """数据不足无法评估"""

    def __init__(self, message: str = "数据不足，无法进行评估", details: dict = None):
        super().__init__(message, details)


# ============================================================================
# 转换相关异常
# ============================================================================


class ConversionError(ScriptEvaluationError):
    """脚本转换相关的基础异常"""

    pass


class ScriptParsingError(ConversionError):
    """剧本解析失败"""

    def __init__(self, message: str = "剧本解析失败", details: dict = None):
        super().__init__(message, details)


class JSONGenerationError(ConversionError):
    """JSON生成失败"""

    def __init__(self, message: str = "JSON生成失败", details: dict = None):
        super().__init__(message, details)


# ============================================================================
# 配置相关异常
# ============================================================================


class ConfigurationError(ScriptEvaluationError):
    """配置相关的基础异常"""

    pass


class MissingConfigError(ConfigurationError):
    """缺少必需的配置"""

    def __init__(self, config_key: str, message: str = None, details: dict = None):
        message = message or f"缺少必需的配置项: {config_key}"
        details = details or {}
        details["config_key"] = config_key
        super().__init__(message, details)


class InvalidConfigError(ConfigurationError):
    """配置值无效"""

    def __init__(self, config_key: str, value: str, message: str = None, details: dict = None):
        message = message or f"配置项 '{config_key}' 的值无效: {value}"
        details = details or {}
        details["config_key"] = config_key
        details["value"] = value
        super().__init__(message, details)


# ============================================================================
# 工具函数
# ============================================================================


def format_exception(exc: Exception, include_traceback: bool = False) -> str:
    """
    格式化异常信息

    Args:
        exc: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        格式化的异常字符串
    """
    import traceback

    if isinstance(exc, ScriptEvaluationError):
        result = f"{exc.__class__.__name__}: {exc}"
    else:
        result = f"{exc.__class__.__name__}: {str(exc)}"

    if include_traceback:
        result += "\n\n堆栈跟踪:\n" + "".join(traceback.format_tb(exc.__traceback__))

    return result


def is_retryable_error(exc: Exception) -> bool:
    """
    判断异常是否可以重试

    Args:
        exc: 异常对象

    Returns:
        是否应该重试
    """
    # API相关的某些错误可以重试
    retryable_errors = (APIConnectionError, APITimeoutError, APIRateLimitError)

    return isinstance(exc, retryable_errors)


def get_error_severity(exc: Exception) -> str:
    """
    获取错误严重程度

    Args:
        exc: 异常对象

    Returns:
        严重程度：'low', 'medium', 'high', 'critical'
    """
    # 关键错误
    if isinstance(exc, (APIQuotaExceededError, ConfigurationError)):
        return "critical"

    # 高严重性错误
    if isinstance(exc, (FileError, JSONValidationError, ScriptParsingError)):
        return "high"

    # 中等严重性错误
    if isinstance(exc, (ValidationError, EvaluationError)):
        return "medium"

    # 低严重性错误
    if isinstance(exc, (APITimeoutError, APIConnectionError)):
        return "low"

    # 默认中等
    return "medium"


# ============================================================================
# 异常上下文管理器
# ============================================================================


class ErrorContext:
    """
    错误上下文管理器，用于捕获和处理异常

    Example:
        with ErrorContext("处理文件", file_path="test.json"):
            # 可能抛出异常的代码
            process_file("test.json")
    """

    def __init__(
        self,
        operation: str,
        raise_on_error: bool = True,
        log_errors: bool = True,
        **context_data,
    ):
        """
        Args:
            operation: 操作描述
            raise_on_error: 是否重新抛出异常
            log_errors: 是否记录错误日志
            **context_data: 上下文数据
        """
        self.operation = operation
        self.raise_on_error = raise_on_error
        self.log_errors = log_errors
        self.context_data = context_data
        self.exception = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val is not None:
            self.exception = exc_val

            if self.log_errors:
                import logging

                logger = logging.getLogger(__name__)
                severity = get_error_severity(exc_val)

                log_message = f"{self.operation}失败: {format_exception(exc_val)}"
                if self.context_data:
                    log_message += f"\n上下文: {self.context_data}"

                if severity in ["critical", "high"]:
                    logger.error(log_message)
                elif severity == "medium":
                    logger.warning(log_message)
                else:
                    logger.info(log_message)

            if not self.raise_on_error:
                return True  # 抑制异常

        return False  # 正常传播异常


if __name__ == "__main__":
    # 测试自定义异常
    print("=== 测试自定义异常 ===\n")

    # 测试基础异常
    try:
        raise APIConnectionError(details={"endpoint": "https://api.example.com"})
    except APIConnectionError as e:
        print(f"捕获到异常: {e}")
        print(f"严重程度: {get_error_severity(e)}")
        print(f"可重试: {is_retryable_error(e)}\n")

    # 测试JSON验证错误
    try:
        raise JSONValidationError(
            validation_errors=["字段 'scene_id' 缺失", "字段 'setting' 格式错误"]
        )
    except JSONValidationError as e:
        print(f"捕获到异常:\n{e}\n")

    # 测试错误上下文管理器
    print("=== 测试错误上下文管理器 ===\n")

    with ErrorContext("读取配置文件", file_path="config.yaml", raise_on_error=False):
        raise FileNotFoundError("config.yaml")

    print("程序继续运行...\n")

    # 测试格式化异常
    try:
        raise MetricCalculationError("scene_boundary", details={"score": 0.5})
    except MetricCalculationError as e:
        print("格式化的异常信息:")
        print(format_exception(e, include_traceback=False))

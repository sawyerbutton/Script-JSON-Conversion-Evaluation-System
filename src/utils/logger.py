"""
日志系统配置
提供统一的日志配置和工具函数
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 日志格式配置
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅在终端输出时使用）"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record):
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"

        return super().format(record)


def setup_logger(
    name: str = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[str] = "logs",
    use_colors: bool = True,
    format_style: str = "standard",
) -> logging.Logger:
    """
    配置并返回logger实例

    Args:
        name: logger名称，默认为root logger
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名（不包含路径）
        log_dir: 日志文件目录
        use_colors: 是否在控制台输出中使用颜色
        format_style: 格式风格 ('simple', 'standard', 'detailed')

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

    # 防止重复添加handler
    if logger.handlers:
        return logger

    # 选择日志格式
    if format_style == "simple":
        log_format = SIMPLE_FORMAT
    elif format_style == "detailed":
        log_format = DETAILED_FORMAT
    else:
        log_format = LOG_FORMAT

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

    if use_colors and sys.stdout.isatty():
        console_formatter = ColoredFormatter(log_format)
    else:
        console_formatter = logging.Formatter(log_format)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件handler（如果指定）
    if log_file:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)

        file_path = log_dir_path / log_file
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别

        # 文件不使用颜色
        file_formatter = logging.Formatter(DETAILED_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取logger实例（简化版）

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    return logging.getLogger(name)


class LoggerContext:
    """
    日志上下文管理器，用于临时改变日志级别

    Example:
        logger = get_logger(__name__)
        with LoggerContext(logger, level="DEBUG"):
            logger.debug("这条调试信息会被记录")
    """

    def __init__(self, logger: logging.Logger, level: str):
        self.logger = logger
        self.new_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        self.old_level = None

    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


class OperationLogger:
    """
    操作日志记录器，自动记录操作的开始、结束和耗时

    Example:
        logger = get_logger(__name__)
        with OperationLogger(logger, "处理文件", file_path="test.json"):
            process_file("test.json")
    """

    def __init__(self, logger: logging.Logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        message = f"开始{self.operation}"
        if context_str:
            message += f" ({context_str})"
        self.logger.info(message)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()

        if exc_val is not None:
            self.logger.error(
                f"{self.operation}失败 (耗时: {elapsed:.2f}秒): {exc_val}"
            )
        else:
            self.logger.info(f"{self.operation}完成 (耗时: {elapsed:.2f}秒)")


def log_function_call(logger: logging.Logger = None, level: str = "DEBUG"):
    """
    装饰器：自动记录函数调用

    Args:
        logger: logger实例，默认使用函数所在模块的logger
        level: 日志级别

    Example:
        @log_function_call(level="INFO")
        def process_data(data):
            return data * 2
    """

    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取logger
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            # 记录函数调用
            args_str = ", ".join(repr(arg) for arg in args)
            kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
            params = ", ".join(filter(None, [args_str, kwargs_str]))

            log_level = LOG_LEVELS.get(level.upper(), logging.DEBUG)
            logger.log(log_level, f"调用 {func.__name__}({params})")

            try:
                result = func(*args, **kwargs)
                logger.log(log_level, f"{func.__name__} 返回: {result!r}")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} 抛出异常: {e}")
                raise

        return wrapper

    return decorator


def create_session_logger(session_id: str = None) -> logging.Logger:
    """
    创建会话级别的logger，输出到单独的日志文件

    Args:
        session_id: 会话ID，如果不提供则自动生成

    Returns:
        配置好的logger
    """
    if session_id is None:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    log_file = f"session_{session_id}.log"
    return setup_logger(
        name=f"session.{session_id}",
        level="DEBUG",
        log_file=log_file,
        format_style="detailed",
    )


# ============================================================================
# 预配置的logger
# ============================================================================


def setup_application_logging(
    level: str = "INFO", log_to_file: bool = True, log_dir: str = "logs"
):
    """
    设置应用程序级别的日志配置

    Args:
        level: 日志级别
        log_to_file: 是否记录到文件
        log_dir: 日志目录
    """
    # 配置root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

    # 清除已有的handlers
    root_logger.handlers = []

    # 添加控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))

    if sys.stdout.isatty():
        console_formatter = ColoredFormatter(LOG_FORMAT)
    else:
        console_formatter = logging.Formatter(LOG_FORMAT)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 添加文件handler
    if log_to_file:
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(parents=True, exist_ok=True)

        # 主日志文件
        main_log_file = log_dir_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(main_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(DETAILED_FORMAT)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # 错误日志文件
        error_log_file = log_dir_path / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    # 设置应用程序日志
    setup_application_logging(level="DEBUG", log_to_file=True)

    logger = get_logger(__name__)

    print("=== 测试基础日志 ===\n")
    logger.debug("这是调试信息")
    logger.info("这是一般信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")

    print("\n=== 测试操作日志记录器 ===\n")
    with OperationLogger(logger, "处理数据", batch_size=100):
        import time

        time.sleep(0.1)

    print("\n=== 测试函数调用日志 ===\n")

    @log_function_call(logger=logger, level="INFO")
    def add(a, b):
        return a + b

    result = add(3, 5)

    print("\n=== 测试日志上下文 ===\n")
    logger.info("当前日志级别: INFO")
    with LoggerContext(logger, level="DEBUG"):
        logger.debug("临时启用DEBUG级别")
    logger.debug("这条不会显示（回到INFO级别）")

    print("\n日志文件已保存到 logs/ 目录")

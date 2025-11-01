"""
测试日志系统模块
"""

import logging
import time

import pytest

from src.utils.logger import (
    LOG_LEVELS,
    ColoredFormatter,
    LoggerContext,
    OperationLogger,
    create_session_logger,
    get_logger,
    log_function_call,
    setup_application_logging,
    setup_logger,
)


class TestGetLogger:
    """测试get_logger函数"""

    def test_get_logger_default(self):
        """测试默认获取logger"""
        logger = get_logger()
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_name(self):
        """测试带名称获取logger"""
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_get_logger_returns_same_instance(self):
        """测试同名logger返回相同实例"""
        logger1 = get_logger("same_module")
        logger2 = get_logger("same_module")
        assert logger1 is logger2


class TestSetupLogger:
    """测试setup_logger函数"""

    def test_setup_logger_default(self, tmp_path):
        """测试默认配置"""
        logger = setup_logger("test_logger", log_dir=str(tmp_path))
        assert logger is not None
        assert logger.level == logging.INFO

    def test_setup_logger_with_level(self, tmp_path):
        """测试设置日志级别"""
        logger = setup_logger("test_logger_debug", level="DEBUG", log_dir=str(tmp_path))
        assert logger.level == logging.DEBUG

    def test_setup_logger_with_file(self, tmp_path):
        """测试文件日志"""
        log_file = "test.log"
        logger = setup_logger(
            "test_logger_file",
            log_file=log_file,
            log_dir=str(tmp_path),
            use_colors=False,
        )

        # 记录日志
        logger.info("测试消息")

        # 验证文件创建
        log_path = tmp_path / log_file
        assert log_path.exists()

        # 验证内容
        content = log_path.read_text(encoding="utf-8")
        assert "测试消息" in content

    def test_setup_logger_format_styles(self, tmp_path):
        """测试不同的格式风格"""
        for style in ["simple", "standard", "detailed"]:
            logger = setup_logger(
                f"test_logger_{style}",
                format_style=style,
                log_dir=str(tmp_path),
                use_colors=False,
            )
            assert logger is not None

    def test_setup_logger_prevents_duplicate_handlers(self, tmp_path):
        """测试防止重复添加handler"""
        logger_name = "test_no_duplicate"
        logger1 = setup_logger(logger_name, log_dir=str(tmp_path))
        handlers_count_1 = len(logger1.handlers)

        logger2 = setup_logger(logger_name, log_dir=str(tmp_path))
        handlers_count_2 = len(logger2.handlers)

        assert handlers_count_1 == handlers_count_2


class TestColoredFormatter:
    """测试彩色格式化器"""

    def test_colored_formatter_creation(self):
        """测试创建彩色格式化器"""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        assert formatter is not None

    def test_colored_formatter_format(self):
        """测试格式化日志记录"""
        formatter = ColoredFormatter("%(levelname)s: %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="测试消息",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        assert "INFO" in formatted
        assert "测试消息" in formatted


class TestLoggerContext:
    """测试日志上下文管理器"""

    def test_logger_context_temp_level(self, caplog):
        """测试临时改变日志级别"""
        logger = get_logger("test_context")
        logger.setLevel(logging.INFO)

        # 默认级别下不显示DEBUG
        logger.debug("不应该显示")
        assert "不应该显示" not in caplog.text

        # 使用上下文临时启用DEBUG
        with LoggerContext(logger, level="DEBUG"):
            logger.debug("应该显示")

        # 恢复原级别
        caplog.clear()
        logger.debug("又不应该显示")
        assert "又不应该显示" not in caplog.text

    def test_logger_context_restores_level(self):
        """测试退出后恢复日志级别"""
        logger = get_logger("test_context_restore")
        original_level = logging.WARNING
        logger.setLevel(original_level)

        with LoggerContext(logger, level="DEBUG"):
            assert logger.level == logging.DEBUG

        assert logger.level == original_level

    def test_logger_context_with_exception(self):
        """测试异常时仍恢复级别"""
        logger = get_logger("test_context_exception")
        original_level = logging.INFO
        logger.setLevel(original_level)

        try:
            with LoggerContext(logger, level="ERROR"):
                assert logger.level == logging.ERROR
                raise ValueError("测试异常")
        except ValueError:
            pass

        assert logger.level == original_level


class TestOperationLogger:
    """测试操作日志记录器"""

    def test_operation_logger_success(self, caplog):
        """测试成功操作的日志"""
        logger = get_logger("test_operation")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            with OperationLogger(logger, "测试操作", param1="value1"):
                time.sleep(0.01)  # 模拟操作

        # 验证日志
        assert "开始测试操作" in caplog.text
        assert "测试操作完成" in caplog.text
        assert "耗时" in caplog.text

    def test_operation_logger_failure(self, caplog):
        """测试失败操作的日志"""
        logger = get_logger("test_operation_fail")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            try:
                with OperationLogger(logger, "失败操作"):
                    raise ValueError("操作失败")
            except ValueError:
                pass

        # 验证日志
        assert "开始失败操作" in caplog.text
        assert "失败操作失败" in caplog.text or "失败" in caplog.text

    def test_operation_logger_with_context(self, caplog):
        """测试带上下文数据的操作日志"""
        logger = get_logger("test_operation_context")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            with OperationLogger(logger, "处理文件", file_path="/path/to/file.txt"):
                pass

        # 验证上下文数据在日志中
        assert "file_path" in caplog.text or "/path/to/file.txt" in caplog.text


class TestLogFunctionCall:
    """测试函数调用日志装饰器"""

    def test_log_function_call_basic(self, caplog):
        """测试基础函数调用日志"""
        logger = get_logger("test_function_call")
        logger.setLevel(logging.DEBUG)

        @log_function_call(logger=logger, level="DEBUG")
        def test_function(a, b):
            return a + b

        with caplog.at_level(logging.DEBUG):
            result = test_function(1, 2)

        assert result == 3
        assert "test_function" in caplog.text

    def test_log_function_call_with_kwargs(self, caplog):
        """测试带关键字参数的函数调用日志"""
        logger = get_logger("test_function_kwargs")
        logger.setLevel(logging.INFO)

        @log_function_call(logger=logger, level="INFO")
        def test_function(a, b=10):
            return a * b

        with caplog.at_level(logging.INFO):
            result = test_function(5, b=3)

        assert result == 15
        assert "test_function" in caplog.text

    def test_log_function_call_with_exception(self, caplog):
        """测试函数抛出异常时的日志"""
        logger = get_logger("test_function_exception")
        logger.setLevel(logging.ERROR)

        @log_function_call(logger=logger, level="INFO")
        def failing_function():
            raise ValueError("函数错误")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()

        assert "failing_function" in caplog.text
        assert "异常" in caplog.text or "ValueError" in caplog.text

    def test_log_function_call_auto_logger(self, caplog):
        """测试自动获取logger"""

        @log_function_call(level="DEBUG")
        def auto_logger_function(x):
            return x * 2

        with caplog.at_level(logging.DEBUG):
            result = auto_logger_function(5)

        assert result == 10


class TestSessionLogger:
    """测试会话级别logger"""

    def test_create_session_logger_default(self, tmp_path):
        """测试创建默认会话logger"""
        logger = create_session_logger()
        assert logger is not None
        assert logger.name.startswith("session.")

    def test_create_session_logger_with_id(self, tmp_path):
        """测试创建指定ID的会话logger"""
        session_id = "test_session_123"
        logger = create_session_logger(session_id)
        assert logger.name == f"session.{session_id}"


class TestApplicationLogging:
    """测试应用程序级别日志配置"""

    def test_setup_application_logging_basic(self, tmp_path):
        """测试基础应用程序日志配置"""
        setup_application_logging(level="INFO", log_to_file=False)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_application_logging_with_file(self, tmp_path):
        """测试带文件的应用程序日志配置"""
        setup_application_logging(level="DEBUG", log_to_file=True, log_dir=str(tmp_path))
        root_logger = logging.getLogger()

        # 记录日志
        root_logger.info("应用程序测试消息")

        # 验证日志文件创建（应该有 app_*.log）
        log_files = list(tmp_path.glob("app_*.log"))
        assert len(log_files) > 0

    def test_setup_application_logging_error_file(self, tmp_path):
        """测试错误日志文件"""
        setup_application_logging(level="DEBUG", log_to_file=True, log_dir=str(tmp_path))
        root_logger = logging.getLogger()

        # 记录错误日志
        root_logger.error("错误测试消息")

        # 验证错误日志文件创建
        error_files = list(tmp_path.glob("error_*.log"))
        assert len(error_files) > 0

        # 验证内容
        error_content = error_files[0].read_text(encoding="utf-8")
        assert "错误测试消息" in error_content

    def test_setup_application_logging_clears_handlers(self):
        """测试清除已有handlers"""
        root_logger = logging.getLogger()

        setup_application_logging(level="INFO", log_to_file=False)
        # 配置后应该清除旧的handlers并添加新的
        assert len(root_logger.handlers) >= 1


class TestLOGLEVELS:
    """测试日志级别映射"""

    def test_log_levels_mapping(self):
        """测试所有日志级别映射"""
        assert LOG_LEVELS["DEBUG"] == logging.DEBUG
        assert LOG_LEVELS["INFO"] == logging.INFO
        assert LOG_LEVELS["WARNING"] == logging.WARNING
        assert LOG_LEVELS["ERROR"] == logging.ERROR
        assert LOG_LEVELS["CRITICAL"] == logging.CRITICAL

    def test_log_levels_complete(self):
        """测试日志级别映射完整性"""
        expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in expected_levels:
            assert level in LOG_LEVELS


class TestIntegration:
    """集成测试"""

    def test_full_logging_workflow(self, tmp_path, caplog):
        """测试完整的日志工作流"""
        # 1. 设置logger
        logger = setup_logger(
            "integration_test",
            level="DEBUG",
            log_file="integration.log",
            log_dir=str(tmp_path),
            use_colors=False,
        )

        # 2. 使用不同级别记录日志
        logger.debug("调试信息")
        logger.info("普通信息")
        logger.warning("警告信息")
        logger.error("错误信息")

        # 3. 使用操作日志
        with OperationLogger(logger, "集成测试操作"):
            logger.info("操作中...")

        # 4. 使用函数调用日志
        @log_function_call(logger=logger, level="INFO")
        def test_func(x):
            return x * 2

        test_func(5)

        # 5. 验证文件内容
        log_file = tmp_path / "integration.log"
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")

        assert "调试信息" in content
        assert "普通信息" in content
        assert "警告信息" in content
        assert "错误信息" in content
        assert "集成测试操作" in content

    def test_multiple_loggers_isolation(self, tmp_path):
        """测试多个logger的隔离性"""
        logger1 = setup_logger("logger1", log_file="log1.log", log_dir=str(tmp_path))
        logger2 = setup_logger("logger2", log_file="log2.log", log_dir=str(tmp_path))

        logger1.info("来自logger1")
        logger2.info("来自logger2")

        log1_file = tmp_path / "log1.log"
        log2_file = tmp_path / "log2.log"

        content1 = log1_file.read_text(encoding="utf-8")
        content2 = log2_file.read_text(encoding="utf-8")

        assert "来自logger1" in content1
        assert "来自logger1" not in content2
        assert "来自logger2" in content2
        assert "来自logger2" not in content1


class TestEdgeCases:
    """边界情况测试"""

    def test_logger_with_unicode(self, tmp_path):
        """测试Unicode字符"""
        logger = setup_logger(
            "unicode_test", log_file="unicode.log", log_dir=str(tmp_path), use_colors=False
        )

        chinese_text = "这是中文测试 🎉"
        logger.info(chinese_text)

        log_file = tmp_path / "unicode.log"
        content = log_file.read_text(encoding="utf-8")
        assert chinese_text in content

    def test_logger_with_long_message(self, tmp_path):
        """测试长消息"""
        logger = setup_logger(
            "long_message_test", log_file="long.log", log_dir=str(tmp_path), use_colors=False
        )

        long_message = "A" * 10000
        logger.info(long_message)

        log_file = tmp_path / "long.log"
        content = log_file.read_text(encoding="utf-8")
        assert long_message in content

    def test_operation_logger_zero_time(self, caplog):
        """测试极短操作时间"""
        logger = get_logger("zero_time_test")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            with OperationLogger(logger, "极短操作"):
                pass  # 几乎不耗时

        assert "极短操作完成" in caplog.text

    def test_nested_operation_loggers(self, caplog):
        """测试嵌套操作日志"""
        logger = get_logger("nested_test")
        logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            with OperationLogger(logger, "外层操作"):
                with OperationLogger(logger, "内层操作"):
                    logger.info("执行内层任务")

        assert "外层操作" in caplog.text
        assert "内层操作" in caplog.text

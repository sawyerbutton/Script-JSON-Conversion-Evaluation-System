"""
测试性能监控模块
"""

import time
from unittest.mock import patch

import pytest

from src.utils.performance import (
    APICallTracker,
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceProfiler,
    benchmark,
    clear_metrics,
    get_all_metrics,
    get_performance_stats,
    print_performance_summary,
    timer,
    track_performance,
)


class TestPerformanceMetrics:
    """测试性能指标数据类"""

    def test_performance_metrics_creation(self):
        """测试创建性能指标"""
        metrics = PerformanceMetrics(operation="test_op", start_time=time.time())
        assert metrics.operation == "test_op"
        assert metrics.start_time > 0
        assert metrics.duration == 0.0
        assert metrics.success is True

    def test_performance_metrics_finalize(self):
        """测试完成计时"""
        start = time.time()
        metrics = PerformanceMetrics(operation="test_op", start_time=start)
        time.sleep(0.01)
        metrics.finalize(success=True)

        assert metrics.end_time > 0
        assert metrics.duration > 0
        assert metrics.success is True

    def test_performance_metrics_finalize_with_error(self):
        """测试失败操作"""
        metrics = PerformanceMetrics(operation="test_op", start_time=time.time())
        metrics.finalize(success=False, error_message="测试错误")

        assert metrics.success is False
        assert metrics.error_message == "测试错误"

    def test_performance_metrics_to_dict(self):
        """测试转换为字典"""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time(),
            metadata={"key": "value"},
        )
        metrics.finalize()

        result = metrics.to_dict()
        assert isinstance(result, dict)
        assert result["operation"] == "test_op"
        assert "duration" in result
        assert "key" in result
        assert result["key"] == "value"

    def test_performance_metrics_with_metadata(self):
        """测试带元数据的指标"""
        metadata = {"user": "test", "batch_size": 100}
        metrics = PerformanceMetrics(
            operation="process_data",
            start_time=time.time(),
            metadata=metadata,
        )

        assert metrics.metadata == metadata


class TestPerformanceMonitor:
    """测试性能监控器"""

    def test_monitor_singleton(self):
        """测试单例模式"""
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        assert monitor1 is monitor2

    def test_monitor_record(self):
        """测试记录性能指标"""
        monitor = PerformanceMonitor()
        monitor.clear()

        metrics = PerformanceMetrics(operation="test_record", start_time=time.time())
        metrics.finalize()

        monitor.record(metrics)
        assert len(monitor.metrics) > 0

    def test_monitor_disabled(self):
        """测试禁用监控"""
        monitor = PerformanceMonitor()
        monitor.clear()
        monitor.disable()

        metrics = PerformanceMetrics(operation="test_disabled", start_time=time.time())
        metrics.finalize()

        initial_count = len(monitor.metrics)
        monitor.record(metrics)
        assert len(monitor.metrics) == initial_count

        monitor.enable()

    def test_monitor_slow_operation_warning(self, caplog):
        """测试慢操作警告"""
        monitor = PerformanceMonitor()
        monitor.clear()

        metrics = PerformanceMetrics(operation="slow_op", start_time=time.time())
        time.sleep(1.1)  # 超过1秒
        metrics.finalize()

        monitor.record(metrics)
        # 应该有慢操作警告
        assert any("慢操作" in record.message for record in caplog.records)

    def test_monitor_get_stats(self):
        """测试获取统计"""
        monitor = PerformanceMonitor()
        monitor.clear()

        # 记录几个指标
        for i in range(3):
            metrics = PerformanceMetrics(operation="test_stats", start_time=time.time())
            time.sleep(0.01)
            metrics.finalize()
            monitor.record(metrics)

        stats = monitor.get_stats("test_stats")
        assert stats["count"] == 3
        assert "mean" in stats
        assert "min" in stats
        assert "max" in stats

    def test_monitor_get_all_stats(self):
        """测试获取所有统计"""
        monitor = PerformanceMonitor()
        monitor.clear()

        # 记录不同操作
        for op in ["op1", "op2"]:
            metrics = PerformanceMetrics(operation=op, start_time=time.time())
            metrics.finalize()
            monitor.record(metrics)

        stats = monitor.get_stats()
        assert isinstance(stats, dict)
        assert "op1" in stats or "op2" in stats

    def test_monitor_clear(self):
        """测试清除指标"""
        monitor = PerformanceMonitor()

        metrics = PerformanceMetrics(operation="test_clear", start_time=time.time())
        metrics.finalize()
        monitor.record(metrics)

        monitor.clear()
        assert len(monitor.metrics) == 0
        assert len(monitor.operation_stats) == 0


class TestTrackPerformance:
    """测试性能跟踪上下文管理器"""

    def test_track_performance_basic(self):
        """测试基础性能跟踪"""
        with track_performance("test_operation"):
            time.sleep(0.01)

        # 验证指标被记录
        monitor = PerformanceMonitor()
        assert len(monitor.metrics) > 0

    def test_track_performance_with_metadata(self):
        """测试带元数据的性能跟踪"""
        monitor = PerformanceMonitor()
        monitor.clear()

        with track_performance("test_meta", batch_size=100, user="test"):
            pass

        metrics = monitor.metrics[-1]
        assert metrics.metadata["batch_size"] == 100
        assert metrics.metadata["user"] == "test"

    def test_track_performance_with_exception(self):
        """测试异常时的性能跟踪"""
        monitor = PerformanceMonitor()
        monitor.clear()

        with pytest.raises(ValueError):
            with track_performance("test_exception"):
                raise ValueError("测试异常")

        # 即使有异常，也应该记录
        assert len(monitor.metrics) > 0
        metrics = monitor.metrics[-1]
        assert metrics.success is False
        assert "ValueError" in metrics.error_message or "测试异常" in metrics.error_message


class TestTimerDecorator:
    """测试计时装饰器"""

    def test_timer_basic(self):
        """测试基础计时"""
        monitor = PerformanceMonitor()
        monitor.clear()

        @timer
        def test_function():
            time.sleep(0.01)
            return "result"

        result = test_function()
        assert result == "result"
        assert len(monitor.metrics) > 0

    def test_timer_with_name(self):
        """测试自定义名称"""
        monitor = PerformanceMonitor()
        monitor.clear()

        @timer(name="自定义操作")
        def test_function():
            return 42

        result = test_function()
        assert result == 42

        metrics = monitor.metrics[-1]
        assert "自定义操作" in metrics.operation

    def test_timer_with_log_result(self, caplog):
        """测试日志输出"""

        @timer(name="测试操作", log_result=True)
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_timer_no_function(self):
        """测试装饰器支持两种用法"""

        # 用法1: @timer
        @timer
        def func1():
            return 1

        # 用法2: @timer()
        @timer()
        def func2():
            return 2

        assert func1() == 1
        assert func2() == 2


class TestPerformanceProfiler:
    """测试性能分析器"""

    def test_profiler_basic(self):
        """测试基础分析"""
        profiler = PerformanceProfiler("测试分析")
        profiler.start("开始")
        time.sleep(0.01)

        profiler.checkpoint("中间点")
        time.sleep(0.01)

        profiler.stop()

        report = profiler.get_report()
        assert report["name"] == "测试分析"
        assert report["total_time"] > 0
        assert len(report["segments"]) > 0

    def test_profiler_multiple_checkpoints(self):
        """测试多个检查点"""
        profiler = PerformanceProfiler()
        profiler.start("初始化")

        for i in range(3):
            profiler.checkpoint(f"阶段{i+1}")
            time.sleep(0.01)

        profiler.stop()

        report = profiler.get_report()
        assert len(report["segments"]) >= 3

    def test_profiler_print_report(self, capsys):
        """测试打印报告"""
        profiler = PerformanceProfiler("打印测试")
        profiler.start()
        profiler.checkpoint("阶段1")
        profiler.stop()

        profiler.print_report()
        captured = capsys.readouterr()
        assert "性能分析报告" in captured.out
        assert "打印测试" in captured.out

    def test_profiler_empty_report(self):
        """测试空报告"""
        profiler = PerformanceProfiler()
        report = profiler.get_report()
        assert report == {}

    def test_profiler_percentage_calculation(self):
        """测试百分比计算"""
        profiler = PerformanceProfiler()
        profiler.start()
        time.sleep(0.05)
        profiler.checkpoint("50%点")
        time.sleep(0.05)
        profiler.stop()

        report = profiler.get_report()
        # 验证百分比加起来接近100%
        total_percentage = sum(seg["percentage"] for seg in report["segments"])
        assert 95 <= total_percentage <= 105  # 允许一些误差


class TestBenchmark:
    """测试基准测试函数"""

    def test_benchmark_basic(self):
        """测试基础基准测试"""

        def test_func():
            return sum(range(100))

        result = benchmark(test_func, iterations=10)
        assert result["iterations"] == 10
        assert "mean_time" in result
        assert "min_time" in result
        assert "max_time" in result
        assert "median_time" in result

    def test_benchmark_with_args(self):
        """测试带参数的基准测试"""

        def test_func(a, b):
            return a + b

        result = benchmark(test_func, 5, 10, iterations=5)
        assert result["iterations"] == 5

    def test_benchmark_with_kwargs(self):
        """测试带关键字参数的基准测试"""

        def test_func(x, y=10):
            return x * y

        result = benchmark(test_func, 5, y=3, iterations=5)
        assert result["iterations"] == 5

    def test_benchmark_statistics(self):
        """测试基准统计的正确性"""

        def test_func():
            return 42

        result = benchmark(test_func, iterations=100)
        # 最小时间应该 <= 平均时间 <= 最大时间
        assert result["min_time"] <= result["mean_time"] <= result["max_time"]


class TestAPICallTracker:
    """测试API调用追踪器"""

    def test_tracker_creation(self):
        """测试创建追踪器"""
        tracker = APICallTracker()
        assert tracker.total_tokens == 0
        assert tracker.total_cost == 0.0
        assert len(tracker.calls) == 0

    def test_tracker_record_call(self):
        """测试记录API调用"""
        tracker = APICallTracker()

        tracker.record_call(
            endpoint="test_api",
            duration=0.5,
            tokens=1000,
            cost=0.01,
            success=True,
        )

        assert len(tracker.calls) == 1
        assert tracker.total_tokens == 1000
        assert tracker.total_cost == 0.01

    def test_tracker_multiple_calls(self):
        """测试多次调用"""
        tracker = APICallTracker()

        for i in range(5):
            tracker.record_call(
                endpoint="api",
                duration=0.1 * i,
                tokens=100 * i,
                cost=0.001 * i,
                success=True,
            )

        assert len(tracker.calls) == 5
        assert tracker.total_tokens == sum(100 * i for i in range(5))

    def test_tracker_with_metadata(self):
        """测试带元数据的调用记录"""
        tracker = APICallTracker()

        tracker.record_call(
            endpoint="api",
            duration=0.5,
            tokens=1000,
            cost=0.01,
            success=True,
            model="gpt-4",
            temperature=0.7,
        )

        call = tracker.calls[0]
        assert call["model"] == "gpt-4"
        assert call["temperature"] == 0.7

    def test_tracker_get_stats(self):
        """测试获取统计"""
        tracker = APICallTracker()

        # 添加成功和失败的调用
        tracker.record_call("api", 0.5, 1000, 0.01, success=True)
        tracker.record_call("api", 0.3, 800, 0.008, success=True)
        tracker.record_call("api", 0.2, 0, 0, success=False)

        stats = tracker.get_stats()
        assert stats["total_calls"] == 3
        assert stats["successful_calls"] == 2
        assert stats["failed_calls"] == 1
        assert stats["total_tokens"] == 1800
        assert "average_duration" in stats

    def test_tracker_print_summary(self, capsys):
        """测试打印摘要"""
        tracker = APICallTracker()
        tracker.record_call("api", 0.5, 1000, 0.01, success=True)

        tracker.print_summary()
        captured = capsys.readouterr()
        assert "API调用统计" in captured.out

    def test_tracker_empty_stats(self):
        """测试空统计"""
        tracker = APICallTracker()
        stats = tracker.get_stats()
        assert stats == {}


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_performance_stats(self):
        """测试获取性能统计"""
        monitor = PerformanceMonitor()
        monitor.clear()

        # 记录一些指标
        metrics = PerformanceMetrics(operation="test_conv", start_time=time.time())
        metrics.finalize()
        monitor.record(metrics)

        stats = get_performance_stats("test_conv")
        assert isinstance(stats, dict)

    def test_get_all_metrics(self):
        """测试获取所有指标"""
        monitor = PerformanceMonitor()
        monitor.clear()

        metrics = PerformanceMetrics(operation="test_all", start_time=time.time())
        metrics.finalize()
        monitor.record(metrics)

        all_metrics = get_all_metrics()
        assert isinstance(all_metrics, list)
        assert len(all_metrics) > 0

    def test_clear_metrics(self):
        """测试清除指标"""
        monitor = PerformanceMonitor()

        metrics = PerformanceMetrics(operation="test_clear_func", start_time=time.time())
        metrics.finalize()
        monitor.record(metrics)

        clear_metrics()
        assert len(monitor.metrics) == 0

    def test_print_performance_summary(self, capsys):
        """测试打印性能摘要"""
        monitor = PerformanceMonitor()
        monitor.clear()

        # 记录一些指标
        metrics = PerformanceMetrics(operation="test_summary", start_time=time.time())
        metrics.finalize()
        monitor.record(metrics)

        print_performance_summary()
        captured = capsys.readouterr()
        assert "性能统计摘要" in captured.out or "test_summary" in captured.out

    def test_print_performance_summary_empty(self, capsys):
        """测试打印空摘要"""
        monitor = PerformanceMonitor()
        monitor.clear()

        print_performance_summary()
        captured = capsys.readouterr()
        assert "没有性能数据" in captured.out


class TestIntegration:
    """集成测试"""

    def test_full_performance_workflow(self):
        """测试完整性能监控流程"""
        monitor = PerformanceMonitor()
        monitor.clear()

        # 1. 使用装饰器
        @timer(name="步骤1")
        def step1():
            time.sleep(0.01)

        # 2. 使用上下文管理器
        with track_performance("步骤2"):
            time.sleep(0.01)

        # 3. 使用分析器
        profiler = PerformanceProfiler("完整流程")
        profiler.start()
        step1()
        profiler.checkpoint("步骤1完成")
        profiler.stop()

        # 4. 验证所有指标都被记录
        assert len(monitor.metrics) >= 2

        # 5. 获取统计
        stats = get_performance_stats()
        assert isinstance(stats, dict)

    def test_api_tracker_integration(self):
        """测试API追踪器集成"""
        tracker = APICallTracker()

        # 模拟API调用
        for i in range(3):
            start = time.time()
            time.sleep(0.01)
            duration = time.time() - start

            tracker.record_call(
                endpoint="test_endpoint",
                duration=duration,
                tokens=100 + i * 50,
                cost=0.001 * (i + 1),
                success=True,
            )

        stats = tracker.get_stats()
        assert stats["total_calls"] == 3
        assert stats["total_tokens"] > 0
        assert stats["total_cost"] > 0


class TestEdgeCases:
    """边界情况测试"""

    def test_zero_duration_operation(self):
        """测试零耗时操作"""
        monitor = PerformanceMonitor()
        monitor.clear()

        with track_performance("instant_op"):
            pass  # 几乎不耗时

        assert len(monitor.metrics) > 0

    def test_nested_tracking(self):
        """测试嵌套追踪"""
        monitor = PerformanceMonitor()
        monitor.clear()

        with track_performance("外层"):
            with track_performance("内层"):
                time.sleep(0.01)

        assert len(monitor.metrics) >= 2

    def test_profiler_single_checkpoint(self):
        """测试单个检查点的分析器"""
        profiler = PerformanceProfiler()
        profiler.start()
        profiler.stop()

        report = profiler.get_report()
        assert "segments" in report

    def test_track_performance_without_psutil(self):
        """测试没有psutil时的性能追踪"""
        # 注意：psutil是在函数内部动态导入的，所以我们只测试正常情况
        monitor = PerformanceMonitor()
        monitor.clear()

        with track_performance("test_op"):
            time.sleep(0.01)

        # 应该正常工作
        assert len(monitor.metrics) > 0
        metrics = monitor.metrics[-1]
        # memory_delta可能是0（如果没有psutil）或非0（如果有psutil）
        assert metrics.memory_delta >= 0

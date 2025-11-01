"""
性能监控工具
提供计时、内存监控和性能统计功能
"""

import functools
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List

try:
    from .logger import get_logger

    logger = get_logger(__name__)
except ImportError:
    # 允许独立运行
    import logging

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    operation: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    memory_before: int = 0
    memory_after: int = 0
    memory_delta: int = 0
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finalize(self, success: bool = True, error_message: str = ""):
        """完成计时并计算指标"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "operation": self.operation,
            "duration": round(self.duration, 3),
            "memory_delta_mb": round(self.memory_delta / 1024 / 1024, 2),
            "success": self.success,
            "error": self.error_message,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            **self.metadata,
        }


class PerformanceMonitor:
    """性能监控器 - 单例模式"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.metrics: List[PerformanceMetrics] = []
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.enabled = True
        self._initialized = True

    def record(self, metric: PerformanceMetrics):
        """记录性能指标"""
        if not self.enabled:
            return

        self.metrics.append(metric)
        self.operation_stats[metric.operation].append(metric.duration)

        # 记录慢操作（超过1秒）
        if metric.duration > 1.0:
            logger.warning(f"慢操作检测: {metric.operation} 耗时 {metric.duration:.2f}秒")

    def get_stats(self, operation: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        if operation:
            durations = self.operation_stats.get(operation, [])
            if not durations:
                return {}

            return {
                "operation": operation,
                "count": len(durations),
                "total": round(sum(durations), 3),
                "mean": round(sum(durations) / len(durations), 3),
                "min": round(min(durations), 3),
                "max": round(max(durations), 3),
            }
        else:
            # 所有操作的统计
            stats = {}
            for op, durations in self.operation_stats.items():
                stats[op] = {
                    "count": len(durations),
                    "total": round(sum(durations), 3),
                    "mean": round(sum(durations) / len(durations), 3),
                }
            return stats

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """获取所有指标"""
        return [m.to_dict() for m in self.metrics]

    def clear(self):
        """清除所有指标"""
        self.metrics.clear()
        self.operation_stats.clear()

    def disable(self):
        """禁用监控"""
        self.enabled = False

    def enable(self):
        """启用监控"""
        self.enabled = True


# 全局监控器实例
_monitor = PerformanceMonitor()


@contextmanager
def track_performance(operation: str, **metadata):
    """
    性能跟踪上下文管理器

    Args:
        operation: 操作名称
        **metadata: 额外的元数据

    Example:
        with track_performance("处理数据", batch_size=100):
            process_data()
    """
    # 尝试使用psutil进行内存监控（可选）
    memory_before = 0
    memory_after = 0

    try:
        import os

        import psutil

        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss
    except ImportError:
        pass  # psutil不可用时跳过内存监控

    metric = PerformanceMetrics(
        operation=operation,
        start_time=time.time(),
        memory_before=memory_before,
        metadata=metadata,
    )

    try:
        yield metric
        metric.finalize(success=True)
    except Exception as e:
        metric.finalize(success=False, error_message=str(e))
        raise
    finally:
        # 尝试获取结束时的内存
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())
            memory_after = process.memory_info().rss
        except ImportError:
            pass

        metric.memory_after = memory_after
        metric.memory_delta = memory_after - memory_before
        _monitor.record(metric)


def timer(func: Callable = None, *, name: str = None, log_result: bool = True):
    """
    计时装饰器

    Args:
        func: 被装饰的函数
        name: 操作名称，默认使用函数名
        log_result: 是否记录日志

    Example:
        @timer
        def process_data():
            pass

        @timer(name="数据处理", log_result=True)
        def process_data():
            pass
    """

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            operation_name = name or f"{f.__module__}.{f.__name__}"

            with track_performance(operation_name) as metric:
                result = f(*args, **kwargs)

                if log_result:
                    logger.info(f"{operation_name} 完成，耗时: {metric.duration:.3f}秒")

                return result

        return wrapper

    # 支持 @timer 和 @timer() 两种用法
    if func is None:
        return decorator
    else:
        return decorator(func)


class PerformanceProfiler:
    """
    性能分析器 - 用于详细分析代码性能

    Example:
        profiler = PerformanceProfiler()
        profiler.start("初始化")
        # 初始化代码
        profiler.checkpoint("加载数据")
        # 加载数据代码
        profiler.checkpoint("处理数据")
        # 处理数据代码
        profiler.stop()
        profiler.print_report()
    """

    def __init__(self, name: str = "性能分析"):
        self.name = name
        self.checkpoints: List[tuple] = []
        self.start_time: float = 0
        self.current_checkpoint: str = ""

    def start(self, initial_checkpoint: str = "开始"):
        """开始分析"""
        self.start_time = time.time()
        self.current_checkpoint = initial_checkpoint
        self.checkpoints = [(initial_checkpoint, self.start_time, 0.0)]

    def checkpoint(self, name: str):
        """记录检查点"""
        now = time.time()
        elapsed = now - self.start_time
        self.checkpoints.append((name, now, elapsed))
        self.current_checkpoint = name

    def stop(self):
        """停止分析"""
        self.checkpoint("结束")

    def get_report(self) -> Dict[str, Any]:
        """获取分析报告"""
        if not self.checkpoints:
            return {}

        total_time = self.checkpoints[-1][2]
        segments = []

        for i in range(len(self.checkpoints) - 1):
            name1, time1, _ = self.checkpoints[i]
            name2, time2, _ = self.checkpoints[i + 1]
            duration = time2 - time1
            percentage = (duration / total_time * 100) if total_time > 0 else 0

            segments.append(
                {
                    "from": name1,
                    "to": name2,
                    "duration": round(duration, 3),
                    "percentage": round(percentage, 1),
                }
            )

        return {
            "name": self.name,
            "total_time": round(total_time, 3),
            "segments": segments,
        }

    def print_report(self):
        """打印分析报告"""
        report = self.get_report()
        if not report:
            print("没有性能数据")
            return

        print(f"\n{'='*60}")
        print(f"性能分析报告: {report['name']}")
        print(f"总耗时: {report['total_time']:.3f}秒")
        print(f"{'='*60}\n")

        for segment in report["segments"]:
            print(
                f"{segment['from']} → {segment['to']}: "
                f"{segment['duration']:.3f}秒 ({segment['percentage']:.1f}%)"
            )

        print(f"\n{'='*60}\n")


def benchmark(func: Callable, *args, iterations: int = 100, **kwargs) -> Dict[str, Any]:
    """
    基准测试函数

    Args:
        func: 要测试的函数
        *args: 函数参数
        iterations: 迭代次数
        **kwargs: 函数关键字参数

    Returns:
        基准测试结果
    """
    times = []

    for _ in range(iterations):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        times.append(end - start)

    return {
        "function": f"{func.__module__}.{func.__name__}",
        "iterations": iterations,
        "total_time": round(sum(times), 3),
        "mean_time": round(sum(times) / iterations, 6),
        "min_time": round(min(times), 6),
        "max_time": round(max(times), 6),
        "median_time": round(sorted(times)[iterations // 2], 6),
    }


class APICallTracker:
    """API调用追踪器"""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    def record_call(
        self,
        endpoint: str,
        duration: float,
        tokens: int = 0,
        cost: float = 0.0,
        success: bool = True,
        **metadata,
    ):
        """记录API调用"""
        call_record = {
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat(),
            "duration": round(duration, 3),
            "tokens": tokens,
            "cost": round(cost, 4),
            "success": success,
            **metadata,
        }

        self.calls.append(call_record)
        self.total_tokens += tokens
        self.total_cost += cost

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.calls:
            return {}

        successful_calls = [c for c in self.calls if c["success"]]
        failed_calls = [c for c in self.calls if not c["success"]]

        return {
            "total_calls": len(self.calls),
            "successful_calls": len(successful_calls),
            "failed_calls": len(failed_calls),
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "average_duration": round(sum(c["duration"] for c in self.calls) / len(self.calls), 3),
        }

    def print_summary(self):
        """打印摘要"""
        stats = self.get_stats()
        if not stats:
            print("没有API调用记录")
            return

        print("\n=== API调用统计 ===")
        print(f"总调用次数: {stats['total_calls']}")
        print(f"成功: {stats['successful_calls']}")
        print(f"失败: {stats['failed_calls']}")
        print(f"总Token数: {stats['total_tokens']}")
        print(f"总成本: ¥{stats['total_cost']:.4f}")
        print(f"平均耗时: {stats['average_duration']:.3f}秒\n")


# ============================================================================
# 便捷函数
# ============================================================================


def get_performance_stats(operation: str = None) -> Dict[str, Any]:
    """获取性能统计"""
    return _monitor.get_stats(operation)


def get_all_metrics() -> List[Dict[str, Any]]:
    """获取所有性能指标"""
    return _monitor.get_all_metrics()


def clear_metrics():
    """清除所有指标"""
    _monitor.clear()


def print_performance_summary():
    """打印性能摘要"""
    stats = _monitor.get_stats()

    if not stats:
        print("没有性能数据")
        return

    print("\n" + "=" * 60)
    print("性能统计摘要")
    print("=" * 60 + "\n")

    for operation, data in stats.items():
        print(f"{operation}:")
        print(f"  调用次数: {data['count']}")
        print(f"  总耗时: {data['total']:.3f}秒")
        print(f"  平均耗时: {data['mean']:.3f}秒")
        print()

    print("=" * 60 + "\n")


# ============================================================================
# 使用示例
# ============================================================================

if __name__ == "__main__":
    print("=== 测试性能监控工具 ===\n")

    # 测试计时装饰器
    @timer(name="示例函数")
    def example_function():
        time.sleep(0.1)
        return "完成"

    result = example_function()

    # 测试性能跟踪上下文
    with track_performance("数据处理", batch_size=100):
        time.sleep(0.05)

    # 测试性能分析器
    profiler = PerformanceProfiler("完整流程")
    profiler.start("初始化")
    time.sleep(0.02)

    profiler.checkpoint("加载数据")
    time.sleep(0.03)

    profiler.checkpoint("处理数据")
    time.sleep(0.05)

    profiler.stop()
    profiler.print_report()

    # 打印性能摘要
    print_performance_summary()

    # 测试基准测试
    def test_func():
        return sum(range(1000))

    bench_result = benchmark(test_func, iterations=1000)
    print("=== 基准测试结果 ===")
    print(f"函数: {bench_result['function']}")
    print(f"迭代次数: {bench_result['iterations']}")
    print(f"平均耗时: {bench_result['mean_time']*1000:.3f}ms")
    print(f"最小耗时: {bench_result['min_time']*1000:.3f}ms")
    print(f"最大耗时: {bench_result['max_time']*1000:.3f}ms\n")

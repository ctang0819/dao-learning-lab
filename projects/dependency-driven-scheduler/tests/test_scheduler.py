# 导入 sys，用于调整 Python 查找模块的路径。
import sys
# 导入 unittest，Python 标准库中的单元测试框架。
import unittest
# 从 pathlib 导入 Path，用面向对象方式处理文件路径。
from pathlib import Path

# parents[1] 取得 tests 目录的上一级项目目录；str(...) 将 Path 转为字符串。
# append 把项目目录加入模块搜索路径，下面才能直接 import 同目录外的 Python 文件。
sys.path.append(str(Path(__file__).resolve().parents[1]))

# 导入待对照的全量扫描实现。
from baseline import ScanningScheduler
# 导入待验证的增量实现。
from scheduler import IncrementalScheduler


# 继承 unittest.TestCase；以 test_ 开头的方法会被测试框架自动执行。
class SchedulerTest(unittest.TestCase):
    # 验证一个任务必须等待所有前置依赖完成。
    def test_task_waits_for_every_dependency(self) -> None:
        # 字典表示依赖图：T 同时依赖 A、B、C；空集合表示没有前置依赖。
        dependencies = {"A": set(), "B": set(), "C": set(), "T": {"A", "B", "C"}}
        # 创建被测的增量调度器对象。
        scheduler = IncrementalScheduler(dependencies)
        # assertEqual 比较两个值；初始时 A、B、C 应当就绪。
        self.assertEqual({"A", "B", "C"}, set(scheduler.drain_ready()))
        # 标记 A 已完成。
        scheduler.complete("A")
        # 标记 B 已完成。
        scheduler.complete("B")
        # C 未完成前，T 不应进入就绪队列。
        self.assertEqual([], scheduler.drain_ready())
        # 标记最后一个依赖 C 已完成。
        scheduler.complete("C")
        # 此时 T 才应成为唯一就绪任务。
        self.assertEqual(["T"], scheduler.drain_ready())

    # 验证增量调度器只更新完成任务的直接后继。
    def test_updates_only_dependents_of_completed_task(self) -> None:
        # T1、T2 依赖 A，T3 依赖 B。
        dependencies = {"A": set(), "B": set(), "T1": {"A"}, "T2": {"A"}, "T3": {"B"}}
        # 创建增量调度器。
        scheduler = IncrementalScheduler(dependencies)
        # 领取 A、B 的初始就绪事件，隔离本次测试关注的事件。
        scheduler.drain_ready()
        # 标记 A 完成。
        scheduler.complete("A")
        # A 只有两个后继，所以更新次数应该是二。
        self.assertEqual(2, scheduler.metrics.dependency_updates)
        # T1、T2 就绪，而依赖 B 的 T3 不应就绪。
        self.assertEqual({"T1", "T2"}, set(scheduler.drain_ready()))

    # 验证两种模型的结果一致，同时全量扫描的检查次数更多。
    def test_matches_full_scan_result(self) -> None:
        # T1 只依赖 A，T2 同时依赖 A、B。
        dependencies = {"A": set(), "B": set(), "T1": {"A"}, "T2": {"A", "B"}}
        # 创建增量模型。
        incremental = IncrementalScheduler(dependencies)
        # 创建全量扫描模型。
        scanning = ScanningScheduler(dependencies)
        # 元组 ("A", "B") 是不可变序列；循环让两种模型接收相同完成事件。
        for completed in ("A", "B"):
            # 通知增量模型。
            incremental.complete(completed)
            # 通知基线模型。
            scanning.complete(completed)
        # 将两边结果转为集合后比较，忽略队列内部顺序。
        self.assertEqual(set(scanning.drain_ready()), set(incremental.drain_ready()))
        # assertGreater 断言左侧大于右侧，验证基线确实做了更多检查。
        self.assertGreater(scanning.metrics.task_checks, incremental.metrics.dependency_updates)

    # 验证重复的完成事件不会导致重复更新或再次扫描。
    def test_duplicate_completion_is_ignored_by_both_models(self) -> None:
        # T 依赖 A，构造最小重复事件场景。
        dependencies = {"A": set(), "T": {"A"}}
        # 创建增量模型。
        incremental = IncrementalScheduler(dependencies)
        # 创建全量扫描模型。
        scanning = ScanningScheduler(dependencies)
        # 第一次通知 A 完成。
        incremental.complete("A")
        # 基线接收同一事件。
        scanning.complete("A")
        # 保存第一次完成后增量模型的更新次数。
        incremental_updates = incremental.metrics.dependency_updates
        # 保存第一次完成后基线模型的扫描次数。
        scan_checks = scanning.metrics.task_checks
        # 再次通知相同的 A 完成。
        incremental.complete("A")
        # 基线也接收重复事件。
        scanning.complete("A")
        # 断言重复事件没有增加增量更新次数。
        self.assertEqual(incremental_updates, incremental.metrics.dependency_updates)
        # 断言重复事件没有增加基线扫描次数。
        self.assertEqual(scan_checks, scanning.metrics.task_checks)


# 当该测试文件被直接运行时，启动 unittest 的命令行测试入口。
if __name__ == "__main__":
    # unittest.main() 会发现并执行本文件中的测试方法。
    unittest.main()

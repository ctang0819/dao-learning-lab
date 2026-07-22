# 三引号包住的是模块文档字符串，说明本文件用于比较两种调度策略。
"""Compare dependency-driven scheduling with repeated full scans."""

# 从同目录的 baseline 模块导入全量扫描调度器类。
from baseline import ScanningScheduler
# 从同目录的 scheduler 模块导入增量调度器类。
from scheduler import IncrementalScheduler


# def 定义函数；默认参数表示不传值时使用 100,000 和 100。
# -> dict[str, set[str]] 是返回值类型标注：键是字符串，值是字符串集合。
def make_workload(task_count: int = 100_000, fan_out: int = 100) -> dict[str, set[str]]:
    # 创建依赖图；root 没有前置依赖，因此它一开始就是就绪任务。
    dependencies = {"root": set()}
    # range(task_count - 1) 产生从 0 到 task_count - 2 的整数序列。
    for number in range(task_count - 1):
        # f"..." 是 f-string，可将大括号中的变量值插入字符串。
        task = f"task-{number}"
        # 条件表达式“值 A if 条件 else 值 B”根据 number 选择任务依赖。
        # 前 fan_out 个任务依赖 root，其余任务依赖一个永远不完成的任务。
        dependencies[task] = {"root"} if number < fan_out else {"never-completes"}
    # 返回构造好的依赖图。
    return dependencies


# 定义程序主入口函数。
def main() -> None:
    # 调用函数构造默认的 100,000 任务场景。
    dependencies = make_workload()
    # 用同一份输入创建增量调度器。
    incremental = IncrementalScheduler(dependencies)
    # 用同一份输入创建全量扫描基线。
    scanning = ScanningScheduler(dependencies)

    # 领取 root 的初始就绪事件，避免它干扰后面对 root 完成的比较。
    incremental.drain_ready()
    # 基线也领取同一批初始就绪事件。
    scanning.drain_ready()
    # 将初始化扫描次数归零，只统计 root 完成后的这一次扫描。
    scanning.metrics.task_checks = 0
    # 通知增量调度器 root 已完成；它只更新 root 的后继任务。
    incremental.complete("root")
    # 通知基线 root 已完成；它会扫描所有任务。
    scanning.complete("root")

    # assert 断言两个集合相同；若不同，程序会抛出 AssertionError 并停止。
    assert set(incremental.drain_ready()) == set(scanning.drain_ready())
    # print 输出候选任务数；:, 让大整数显示千位分隔符。
    print(f"candidate tasks: {len(dependencies):,}")
    # 输出真实被 root 影响的任务数。
    print(f"affected tasks: {incremental.metrics.dependency_updates:,}")
    # 输出增量模型实际进行的依赖更新次数。
    print(f"incremental updates: {incremental.metrics.dependency_updates:,}")
    # 输出基线模型为同一事件扫描的候选任务数。
    print(f"full-scan task checks: {scanning.metrics.task_checks:,}")


# 当这个文件被“直接执行”时，__name__ 的值是 "__main__"。
if __name__ == "__main__":
    # 调用主函数启动演示；被其他文件 import 时则不会自动执行。
    main()

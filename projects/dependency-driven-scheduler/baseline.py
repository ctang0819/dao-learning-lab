# 三引号包住的是模块文档字符串，说明这是用于对照的朴素实现。
"""Naive scheduler: rescan every task after each completion event."""

# 启用延迟解析类型标注。
from __future__ import annotations

# 导入双端队列类 deque。
from collections import deque
# 导入用于声明指标数据类的 dataclass。
from dataclasses import dataclass


# 让下面的类自动获得数据对象常用能力。
@dataclass
# 定义基线调度器使用的指标类。
class Metrics:
    # 记录累计扫描过多少个任务。
    task_checks: int = 0
    # 记录累计有多少任务被放入就绪队列。
    ready_enqueues: int = 0


# 定义全量扫描调度器类。
class ScanningScheduler:
    # 创建调度器时接收“任务 -> 前置依赖集合”的字典。
    def __init__(self, dependencies: dict[str, set[str]]) -> None:
        # 保存原始依赖图，后续每次事件都从头扫描它。
        self.dependencies = dependencies
        # 创建空集合保存已完成任务。
        self.completed: set[str] = set()
        # 创建空双端队列保存就绪任务。
        self.ready: deque[str] = deque()
        # 创建空集合防止重复入队。
        self.enqueued: set[str] = set()
        # 创建指标对象。
        self.metrics = Metrics()
        # 初始化时扫描一次，使没有依赖的任务进入就绪队列。
        self._scan()

    # 接收一个完成事件并重新扫描完整任务集合。
    def complete(self, task: str) -> None:
        # 若已经完成过，直接忽略重复事件，使其与增量模型语义一致。
        if task in self.completed:
            # 提前结束方法。
            return
        # 将任务标记为已完成。
        self.completed.add(task)
        # 调用以下划线开头的内部方法进行全量扫描。
        self._scan()

    # 下划线表示这是类内部使用的方法，不是主要公开接口。
    def _scan(self) -> None:
        # 遍历所有任务及其依赖，因此这里的工作量接近候选总数 N。
        for task, dependencies in self.dependencies.items():
            # 每访问一个候选任务就增加一次检查计数。
            self.metrics.task_checks += 1
            # <= 对集合表示“左边是否是右边的子集”，即所有依赖是否都已完成。
            if task not in self.enqueued and dependencies <= self.completed:
                # 将已满足条件且尚未入队的任务放到队尾。
                self.ready.append(task)
                # 记录该任务已经入队。
                self.enqueued.add(task)
                # 记录一次入队事件。
                self.metrics.ready_enqueues += 1

    # 领取并清空当前就绪任务。
    def drain_ready(self) -> list[str]:
        # 复制队列内容为普通列表。
        items = list(self.ready)
        # 清空原队列。
        self.ready.clear()
        # 返回本批任务。
        return items

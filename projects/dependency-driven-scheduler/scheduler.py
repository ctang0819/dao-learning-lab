# 三引号包住的是模块文档字符串，用来说明整个文件的用途。
"""Incremental, dependency-driven scheduler used to test the learning model."""

# 让类型标注在 Python 3.11 及以后版本中按需解析，便于写现代类型语法。
from __future__ import annotations

# 从标准库导入 defaultdict（带默认值的字典）和 deque（双端队列）。
from collections import defaultdict, deque
# 从标准库导入 dataclass，用较少代码定义数据对象。
from dataclasses import dataclass


# 装饰器会为下面的类自动生成初始化等常用方法。
@dataclass
# class 定义一个类；Metrics 用来保存调度器运行指标。
class Metrics:
    # 类型标注 int 表示整数；= 0 表示默认值为零。
    dependency_updates: int = 0
    # 记录有多少任务被放入就绪队列。
    ready_enqueues: int = 0


# 定义增量调度器类；它只更新完成任务的直接后继。
class IncrementalScheduler:
    # __init__ 是创建对象后自动执行的构造方法。
    def __init__(self, dependencies: dict[str, set[str]]) -> None:
        # self 表示当前对象；remaining 字典保存每个任务还缺多少依赖。
        # 字典推导式会遍历 dependencies.items() 的键值对并生成新字典。
        self.remaining = {task: len(items) for task, items in dependencies.items()}
        # defaultdict(list) 在读取不存在的键时自动提供空列表。
        self.dependents: dict[str, list[str]] = defaultdict(list)
        # for 循环依次取出任务名和它依赖的任务集合。
        for task, items in dependencies.items():
            # 再遍历当前任务的每一个前置依赖。
            for dependency in items:
                # append 把当前任务加入“该依赖完成后需要通知谁”的反向索引。
                self.dependents[dependency].append(task)
        # set() 创建空集合，用来记录已经完成的任务并支持快速成员判断。
        self.completed: set[str] = set()
        # deque(...) 创建双端队列；生成器表达式筛选出没有依赖的初始就绪任务。
        self.ready: deque[str] = deque(
            task for task, count in self.remaining.items() if count == 0
        )
        # set(self.ready) 复制当前就绪任务，避免同一任务被重复入队。
        self.enqueued = set(self.ready)
        # 用关键字参数创建 Metrics 对象，并把初始入队数量记录下来。
        self.metrics = Metrics(ready_enqueues=len(self.ready))

    # 定义实例方法；task 是本次刚完成的任务名，返回 None 表示无返回值。
    def complete(self, task: str) -> None:
        # in 判断 task 是否已在集合中，保证重复完成事件是幂等的。
        if task in self.completed:
            # return 立即结束当前方法，不做重复更新。
            return
        # add 把刚完成的任务加入已完成集合。
        self.completed.add(task)
        # 只遍历该任务的后继任务，而不是扫描所有任务。
        for dependent in self.dependents[task]:
            # += 1 是“原值加一再赋回”的简写，记录一次真实影响。
            self.metrics.dependency_updates += 1
            # -= 1 是“原值减一再赋回”的简写，表示一个前置依赖已完成。
            self.remaining[dependent] -= 1
            # and 要求两个条件都成立：依赖刚好清零，且该任务此前未入队。
            if self.remaining[dependent] == 0 and dependent not in self.enqueued:
                # append 把满足全部依赖的任务加入队尾。
                self.ready.append(dependent)
                # add 记录它已入队，防止后续重复加入。
                self.enqueued.add(dependent)
                # 记录一次新的就绪任务入队。
                self.metrics.ready_enqueues += 1

    # 定义领取就绪任务的方法；list[str] 表示返回字符串列表。
    def drain_ready(self) -> list[str]:
        # list(...) 将队列当前内容复制为普通列表，作为本次领取结果。
        items = list(self.ready)
        # clear() 清空队列，表示这些任务已被消费者领取。
        self.ready.clear()
        # return 把领取到的列表返回给调用者。
        return items

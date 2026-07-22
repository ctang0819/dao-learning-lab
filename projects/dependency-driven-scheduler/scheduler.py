"""Incremental, dependency-driven scheduler used to test the learning model."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class Metrics:
    dependency_updates: int = 0
    ready_enqueues: int = 0


class IncrementalScheduler:
    def __init__(self, dependencies: dict[str, set[str]]) -> None:
        self.remaining = {task: len(items) for task, items in dependencies.items()}
        self.dependents: dict[str, list[str]] = defaultdict(list)
        for task, items in dependencies.items():
            for dependency in items:
                self.dependents[dependency].append(task)
        self.completed: set[str] = set()
        self.ready: deque[str] = deque(
            task for task, count in self.remaining.items() if count == 0
        )
        self.enqueued = set(self.ready)
        self.metrics = Metrics(ready_enqueues=len(self.ready))

    def complete(self, task: str) -> None:
        if task in self.completed:
            return
        self.completed.add(task)
        for dependent in self.dependents[task]:
            self.metrics.dependency_updates += 1
            self.remaining[dependent] -= 1
            if self.remaining[dependent] == 0 and dependent not in self.enqueued:
                self.ready.append(dependent)
                self.enqueued.add(dependent)
                self.metrics.ready_enqueues += 1

    def drain_ready(self) -> list[str]:
        items = list(self.ready)
        self.ready.clear()
        return items

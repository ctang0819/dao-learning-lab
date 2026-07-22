"""Naive scheduler: rescan every task after each completion event."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class Metrics:
    task_checks: int = 0
    ready_enqueues: int = 0


class ScanningScheduler:
    def __init__(self, dependencies: dict[str, set[str]]) -> None:
        self.dependencies = dependencies
        self.completed: set[str] = set()
        self.ready: deque[str] = deque()
        self.enqueued: set[str] = set()
        self.metrics = Metrics()
        self._scan()

    def complete(self, task: str) -> None:
        if task in self.completed:
            return
        self.completed.add(task)
        self._scan()

    def _scan(self) -> None:
        for task, dependencies in self.dependencies.items():
            self.metrics.task_checks += 1
            if task not in self.enqueued and dependencies <= self.completed:
                self.ready.append(task)
                self.enqueued.add(task)
                self.metrics.ready_enqueues += 1

    def drain_ready(self) -> list[str]:
        items = list(self.ready)
        self.ready.clear()
        return items

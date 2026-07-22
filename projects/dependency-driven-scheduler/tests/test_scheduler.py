import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from baseline import ScanningScheduler
from scheduler import IncrementalScheduler


class SchedulerTest(unittest.TestCase):
    def test_task_waits_for_every_dependency(self) -> None:
        dependencies = {"A": set(), "B": set(), "C": set(), "T": {"A", "B", "C"}}
        scheduler = IncrementalScheduler(dependencies)
        self.assertEqual({"A", "B", "C"}, set(scheduler.drain_ready()))
        scheduler.complete("A")
        scheduler.complete("B")
        self.assertEqual([], scheduler.drain_ready())
        scheduler.complete("C")
        self.assertEqual(["T"], scheduler.drain_ready())

    def test_updates_only_dependents_of_completed_task(self) -> None:
        dependencies = {"A": set(), "B": set(), "T1": {"A"}, "T2": {"A"}, "T3": {"B"}}
        scheduler = IncrementalScheduler(dependencies)
        scheduler.drain_ready()
        scheduler.complete("A")
        self.assertEqual(2, scheduler.metrics.dependency_updates)
        self.assertEqual({"T1", "T2"}, set(scheduler.drain_ready()))

    def test_matches_full_scan_result(self) -> None:
        dependencies = {"A": set(), "B": set(), "T1": {"A"}, "T2": {"A", "B"}}
        incremental = IncrementalScheduler(dependencies)
        scanning = ScanningScheduler(dependencies)
        for completed in ("A", "B"):
            incremental.complete(completed)
            scanning.complete(completed)
        self.assertEqual(set(scanning.drain_ready()), set(incremental.drain_ready()))
        self.assertGreater(scanning.metrics.task_checks, incremental.metrics.dependency_updates)

    def test_duplicate_completion_is_ignored_by_both_models(self) -> None:
        dependencies = {"A": set(), "T": {"A"}}
        incremental = IncrementalScheduler(dependencies)
        scanning = ScanningScheduler(dependencies)
        incremental.complete("A")
        scanning.complete("A")
        incremental_updates = incremental.metrics.dependency_updates
        scan_checks = scanning.metrics.task_checks
        incremental.complete("A")
        scanning.complete("A")
        self.assertEqual(incremental_updates, incremental.metrics.dependency_updates)
        self.assertEqual(scan_checks, scanning.metrics.task_checks)


if __name__ == "__main__":
    unittest.main()

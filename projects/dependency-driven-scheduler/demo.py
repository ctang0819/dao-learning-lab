"""Compare dependency-driven scheduling with repeated full scans."""

from baseline import ScanningScheduler
from scheduler import IncrementalScheduler


def make_workload(task_count: int = 100_000, fan_out: int = 100) -> dict[str, set[str]]:
    dependencies = {"root": set()}
    for number in range(task_count - 1):
        task = f"task-{number}"
        dependencies[task] = {"root"} if number < fan_out else {"never-completes"}
    return dependencies


def main() -> None:
    dependencies = make_workload()
    incremental = IncrementalScheduler(dependencies)
    scanning = ScanningScheduler(dependencies)

    incremental.drain_ready()
    scanning.drain_ready()
    scanning.metrics.task_checks = 0
    incremental.complete("root")
    scanning.complete("root")

    assert set(incremental.drain_ready()) == set(scanning.drain_ready())
    print(f"candidate tasks: {len(dependencies):,}")
    print(f"affected tasks: {incremental.metrics.dependency_updates:,}")
    print(f"incremental updates: {incremental.metrics.dependency_updates:,}")
    print(f"full-scan task checks: {scanning.metrics.task_checks:,}")


if __name__ == "__main__":
    main()

"""
metrics.py

Performance metric calculations shared by every algorithm. Kept separate
from the algorithms themselves so metric definitions are computed
identically regardless of which scheduler produced the SchedulingResult.
"""

from dataclasses import dataclass
from typing import List

from src.scheduler import SchedulingResult


@dataclass
class PerformanceMetrics:
    """
    Aggregate performance numbers for one algorithm's run.

    Attributes:
        algorithm_name: Name of the algorithm this summarizes.
        avg_waiting_time: Mean of all processes' waiting_time.
        avg_turnaround_time: Mean of all processes' turnaround_time.
        avg_response_time: Mean of all processes' response_time.
        cpu_utilization: Percentage of total_time the CPU was busy
            (not idle), 0-100.
        throughput: Completed processes per unit time
            (num_processes / total_time).
        total_time: Makespan of the schedule.
        num_processes: Number of processes in the workload.
    """

    algorithm_name: str
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    cpu_utilization: float
    throughput: float
    total_time: int
    num_processes: int

    def as_dict(self) -> dict:
        """Return metrics as a flat dict, convenient for building DataFrames."""
        return {
            "Algorithm": self.algorithm_name,
            "Avg Waiting Time": round(self.avg_waiting_time, 3),
            "Avg Turnaround Time": round(self.avg_turnaround_time, 3),
            "Avg Response Time": round(self.avg_response_time, 3),
            "CPU Utilization (%)": round(self.cpu_utilization, 2),
            "Throughput (proc/unit time)": round(self.throughput, 4),
            "Total Time": self.total_time,
            "Num Processes": self.num_processes,
        }


def calculate_metrics(result: SchedulingResult) -> PerformanceMetrics:
    """
    Compute PerformanceMetrics from a completed SchedulingResult.

    Args:
        result: Output of Scheduler.run(); every process must already
            have waiting_time, turnaround_time, and response_time set.

    Returns:
        A PerformanceMetrics summary.

    Raises:
        ValueError: If result.processes is empty.
    """
    procs = result.processes
    n = len(procs)
    if n == 0:
        raise ValueError("Cannot calculate metrics for an empty process list")

    avg_waiting = sum(p.waiting_time for p in procs) / n
    avg_turnaround = sum(p.turnaround_time for p in procs) / n
    avg_response = sum(p.response_time for p in procs) / n

    idle_time = sum(end - start for (pid, start, end) in result.timeline if pid == "IDLE")
    busy_time = result.total_time - idle_time
    cpu_utilization = (busy_time / result.total_time * 100) if result.total_time > 0 else 0.0

    throughput = (n / result.total_time) if result.total_time > 0 else 0.0

    return PerformanceMetrics(
        algorithm_name=result.algorithm_name,
        avg_waiting_time=avg_waiting,
        avg_turnaround_time=avg_turnaround,
        avg_response_time=avg_response,
        cpu_utilization=cpu_utilization,
        throughput=throughput,
        total_time=result.total_time,
        num_processes=n,
    )


def compare_metrics(results: List[SchedulingResult]) -> List[PerformanceMetrics]:
    """Convenience helper: calculate_metrics for a batch of results."""
    return [calculate_metrics(r) for r in results]

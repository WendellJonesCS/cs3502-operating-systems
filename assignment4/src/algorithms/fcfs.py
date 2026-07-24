"""
fcfs.py

First-Come, First-Served (FCFS) scheduling.

Non-preemptive: processes run in strict order of arrival_time (ties
broken by pid). This is the simplest possible scheduler and serves as
the baseline every other algorithm is compared against.
"""

from typing import List

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def fcfs(processes: List[Process]) -> SchedulingResult:
    """
    Simulate First-Come, First-Served scheduling.

    Args:
        processes: Workload to schedule (already cloned by the caller).

    Returns:
        SchedulingResult with every process's waiting/turnaround/response
        times filled in, and a Gantt-chart timeline.
    """
    # Sort by arrival time; earlier arrival runs first, pid breaks ties.
    queue = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    timeline = []

    for proc in queue:
        # If the CPU is idle waiting for this process to arrive, log idle time.
        if current_time < proc.arrival_time:
            timeline.append(("IDLE", current_time, proc.arrival_time))
            current_time = proc.arrival_time

        proc.start_time = current_time
        proc.response_time = proc.start_time - proc.arrival_time
        proc.waiting_time = proc.start_time - proc.arrival_time

        end_time = current_time + proc.burst_time
        proc.history.append((current_time, end_time))
        timeline.append((proc.pid, current_time, end_time))

        current_time = end_time
        proc.remaining_time = 0
        proc.completion_time = current_time
        proc.turnaround_time = proc.completion_time - proc.arrival_time
        proc.state = ProcessState.TERMINATED

    return SchedulingResult(
        algorithm_name="FCFS",
        processes=queue,
        timeline=timeline,
        total_time=current_time,
    )

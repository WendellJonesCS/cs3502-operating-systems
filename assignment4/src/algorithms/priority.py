"""
priority.py

Priority scheduling - non-preemptive.

At every point the CPU is free, the ready process with the numerically
smallest priority value (1 = highest priority) is selected and run to
completion. Ties are broken by arrival time, then pid, so behavior is
deterministic. Note: this simple implementation can starve low-priority
processes under heavy load; see the LaTeX report's trade-offs section
for discussion (aging is a common real-world mitigation, not implemented
here to keep the algorithm's behavior easy to verify by hand).
"""

from typing import List

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def priority_scheduling(processes: List[Process]) -> SchedulingResult:
    """
    Simulate non-preemptive Priority scheduling.

    Args:
        processes: Workload to schedule (already cloned by the caller).

    Returns:
        SchedulingResult with computed metrics and Gantt timeline.
    """
    remaining = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    n = len(remaining)
    completed = []
    timeline = []
    current_time = 0
    ready = []
    i = 0

    while len(completed) < n:
        while i < n and remaining[i].arrival_time <= current_time:
            ready.append(remaining[i])
            i += 1

        if not ready:
            next_arrival = remaining[i].arrival_time
            timeline.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            continue

        # Lowest priority value = highest priority; break ties by arrival, pid.
        ready.sort(key=lambda p: (p.priority, p.arrival_time, p.pid))
        proc = ready.pop(0)

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
        completed.append(proc)

    return SchedulingResult(
        algorithm_name="Priority",
        processes=completed,
        timeline=timeline,
        total_time=current_time,
    )

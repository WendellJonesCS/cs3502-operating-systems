"""
sjf.py

Shortest Job First (SJF) scheduling - non-preemptive.

At every point the CPU is free, the scheduler picks the ready process
with the smallest total burst_time. Once started, a process runs to
completion (contrast with SRTF, the preemptive variant, in srtf.py).
"""

import heapq
from typing import List

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def sjf(processes: List[Process]) -> SchedulingResult:
    """
    Simulate non-preemptive Shortest Job First scheduling.

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
    # Min-heap of (burst_time, pid, process) for processes that have arrived.
    ready_heap = []
    i = 0

    while len(completed) < n:
        # Push all processes that have arrived by current_time.
        while i < n and remaining[i].arrival_time <= current_time:
            heapq.heappush(ready_heap, (remaining[i].burst_time, remaining[i].pid, remaining[i]))
            i += 1

        if not ready_heap:
            # CPU idle until the next process arrives.
            next_arrival = remaining[i].arrival_time
            timeline.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            continue

        _, _, proc = heapq.heappop(ready_heap)
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
        algorithm_name="SJF",
        processes=completed,
        timeline=timeline,
        total_time=current_time,
    )

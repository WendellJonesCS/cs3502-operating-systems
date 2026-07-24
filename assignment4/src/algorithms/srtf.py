"""
srtf.py

Shortest Remaining Time First (SRTF) - preemptive variant of SJF.

At every time step, the ready process with the smallest remaining_time
runs. If a newly arriving process has a shorter burst than the time
left on the currently running process, the CPU preempts immediately.
This is one of the two "new" algorithms required beyond the starter's
FCFS/SJF/RR/Priority set.

Implementation approach: event-driven simulation over unit time steps
using a min-heap keyed on remaining_time. Unit-time stepping keeps the
preemption logic simple and easy to verify by hand for small workloads,
at the cost of iterating once per time unit rather than jumping between
events; for the workload sizes and burst magnitudes used in this project
(see workload_generator.py) this is fast enough (tests confirm large
workloads of 100+ processes still run in well under a second).
"""

import heapq
from typing import List

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def srtf(processes: List[Process]) -> SchedulingResult:
    """
    Simulate preemptive Shortest Remaining Time First scheduling.

    Args:
        processes: Workload to schedule (already cloned by the caller).

    Returns:
        SchedulingResult with computed metrics and a Gantt timeline where
        consecutive same-process segments are merged for readability.
    """
    procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    n = len(procs)
    i = 0  # pointer into procs for arrivals not yet admitted
    ready_heap = []  # (remaining_time, pid, process)
    completed = []
    raw_segments = []  # one entry per unit time: (pid_or_IDLE, t)

    current_time = procs[0].arrival_time if n > 0 else 0

    def admit_arrivals(t: int) -> None:
        nonlocal i
        while i < n and procs[i].arrival_time <= t:
            heapq.heappush(ready_heap, (procs[i].remaining_time, procs[i].pid, procs[i]))
            i += 1

    admit_arrivals(current_time)

    while len(completed) < n:
        if not ready_heap:
            next_arrival = procs[i].arrival_time
            raw_segments.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            admit_arrivals(current_time)
            continue

        _, _, proc = heapq.heappop(ready_heap)
        if proc.start_time is None:
            proc.start_time = current_time
            proc.response_time = proc.start_time - proc.arrival_time

        # Run this process for exactly one time unit, then re-check the heap,
        # since a shorter job may arrive during that unit.
        run_end = current_time + 1
        raw_segments.append((proc.pid, current_time, run_end))
        proc.remaining_time -= 1
        current_time = run_end

        admit_arrivals(current_time)

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.state = ProcessState.TERMINATED
            completed.append(proc)
        else:
            heapq.heappush(ready_heap, (proc.remaining_time, proc.pid, proc))

    timeline = _merge_segments(raw_segments)
    for proc in completed:
        proc.history = [(s, e) for (pid, s, e) in timeline if pid == proc.pid]

    return SchedulingResult(
        algorithm_name="SRTF",
        processes=completed,
        timeline=timeline,
        total_time=current_time,
    )


def _merge_segments(raw_segments):
    """Merge consecutive (pid, start, end) tuples that share the same pid."""
    if not raw_segments:
        return []
    merged = [list(raw_segments[0])]
    for pid, start, end in raw_segments[1:]:
        if pid == merged[-1][0] and start == merged[-1][2]:
            merged[-1][2] = end
        else:
            merged.append([pid, start, end])
    return [tuple(seg) for seg in merged]

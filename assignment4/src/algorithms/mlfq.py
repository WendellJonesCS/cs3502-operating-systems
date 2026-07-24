"""
mlfq.py

Multi-Level Feedback Queue (MLFQ) - preemptive, adaptive scheduling.

This is the second "new" algorithm required beyond the starter's
FCFS/SJF/RR/Priority set. MLFQ approximates SJF-like behavior without
requiring a-priori knowledge of burst times, by observing how much CPU
a process actually uses:

    - Multiple queues, numbered 0 (highest priority) .. k-1 (lowest).
    - Each queue level has its own time quantum; lower-numbered queues
      have shorter quanta (fast turnaround for short/interactive jobs).
    - A new process enters at queue level 0.
    - If a process uses its entire quantum without finishing, it is
      demoted one level (it "looks" CPU-bound).
    - If a process finishes its burst within the quantum, it completes
      normally (no demotion needed).
    - The scheduler always picks from the highest non-empty queue level
      (strict priority between levels); within a level it is round robin.

Default configuration: 3 levels with quanta [4, 8, 16]. The last level
runs remaining processes to completion (or FCFS among level-2 processes)
to guarantee progress and avoid starvation growing unbounded for this
project's finite workloads.
"""

from collections import deque
from typing import List, Optional

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def mlfq(
    processes: List[Process],
    quantums: Optional[List[int]] = None,
) -> SchedulingResult:
    """
    Simulate Multi-Level Feedback Queue scheduling.

    Args:
        processes: Workload to schedule (already cloned by the caller).
        quantums: Time quantum for each queue level, highest priority
            first. Defaults to [4, 8, 16] (3 levels).

    Returns:
        SchedulingResult with computed metrics and Gantt timeline.
    """
    if quantums is None:
        quantums = [4, 8, 16]
    num_levels = len(quantums)

    procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    n = len(procs)
    queues = [deque() for _ in range(num_levels)]
    timeline = []
    completed = []
    current_time = procs[0].arrival_time if n > 0 else 0
    i = 0

    def admit_arrivals(t: int) -> None:
        nonlocal i
        while i < n and procs[i].arrival_time <= t:
            procs[i].current_queue_level = 0
            queues[0].append(procs[i])
            i += 1

    admit_arrivals(current_time)

    def highest_nonempty_level() -> Optional[int]:
        for lvl in range(num_levels):
            if queues[lvl]:
                return lvl
        return None

    while len(completed) < n:
        lvl = highest_nonempty_level()
        if lvl is None:
            next_arrival = procs[i].arrival_time
            timeline.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            admit_arrivals(current_time)
            continue

        proc = queues[lvl].popleft()
        if proc.start_time is None:
            proc.start_time = current_time
            proc.response_time = proc.start_time - proc.arrival_time

        quantum = quantums[lvl]
        run_for = min(quantum, proc.remaining_time)
        end_time = current_time + run_for
        proc.history.append((current_time, end_time))
        timeline.append((proc.pid, current_time, end_time))
        proc.remaining_time -= run_for
        current_time = end_time

        # Admit new arrivals (always enter at level 0) before requeueing.
        admit_arrivals(current_time)

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.state = ProcessState.TERMINATED
            completed.append(proc)
        else:
            # Only demote if it used the FULL quantum (didn't just get lucky
            # with a short remaining_time at the last level).
            used_full_quantum = run_for == quantum
            if used_full_quantum and lvl < num_levels - 1:
                proc.current_queue_level = lvl + 1
                queues[lvl + 1].append(proc)
            else:
                # Stays at the same (already lowest, or under-quantum) level.
                queues[lvl].append(proc)

    return SchedulingResult(
        algorithm_name="MLFQ",
        processes=completed,
        timeline=timeline,
        total_time=current_time,
    )

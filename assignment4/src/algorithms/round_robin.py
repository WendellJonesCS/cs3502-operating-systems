"""
round_robin.py

Round Robin (RR) scheduling - preemptive.

Each ready process gets at most `time_quantum` time units of CPU before
being preempted and sent to the back of the ready queue. Newly arriving
processes are appended to the ready queue in arrival order. This is the
classic time-sharing algorithm, favoring fairness and responsiveness
over throughput.
"""

from collections import deque
from typing import List

from src.process import Process, ProcessState
from src.scheduler import SchedulingResult


def round_robin(processes: List[Process], time_quantum: int = 4) -> SchedulingResult:
    """
    Simulate Round Robin scheduling.

    Args:
        processes: Workload to schedule (already cloned by the caller).
        time_quantum: Maximum CPU time given to a process per turn.

    Returns:
        SchedulingResult with computed metrics and Gantt timeline.
    """
    if time_quantum <= 0:
        raise ValueError("time_quantum must be a positive integer")

    procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    n = len(procs)
    ready_queue = deque()
    timeline = []
    completed = []
    current_time = 0
    i = 0  # index into procs for not-yet-arrived processes

    # Seed the ready queue with anything arriving at time 0 (or before the first process).
    if n > 0:
        current_time = procs[0].arrival_time

    def admit_arrivals(up_to_time: int) -> None:
        nonlocal i
        while i < n and procs[i].arrival_time <= up_to_time:
            ready_queue.append(procs[i])
            i += 1

    admit_arrivals(current_time)

    while len(completed) < n:
        if not ready_queue:
            # Nothing ready: jump forward to the next arrival.
            next_arrival = procs[i].arrival_time
            timeline.append(("IDLE", current_time, next_arrival))
            current_time = next_arrival
            admit_arrivals(current_time)
            continue

        proc = ready_queue.popleft()

        if proc.start_time is None:
            proc.start_time = current_time
            proc.response_time = proc.start_time - proc.arrival_time

        run_for = min(time_quantum, proc.remaining_time)
        end_time = current_time + run_for
        proc.history.append((current_time, end_time))
        timeline.append((proc.pid, current_time, end_time))

        proc.remaining_time -= run_for
        current_time = end_time

        # Admit any processes that arrived during this quantum BEFORE
        # re-queueing the just-run process (standard RR tie-breaking rule).
        admit_arrivals(current_time)

        if proc.remaining_time == 0:
            proc.completion_time = current_time
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time
            proc.state = ProcessState.TERMINATED
            completed.append(proc)
        else:
            ready_queue.append(proc)

    return SchedulingResult(
        algorithm_name="Round Robin",
        processes=completed,
        timeline=timeline,
        total_time=current_time,
    )

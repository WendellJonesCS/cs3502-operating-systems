"""
workload_generator.py

Generates reproducible synthetic workloads for benchmarking the
scheduling algorithms, as required by the assignment:
  - Small (5-10), Medium (20-50), Large (100+) process counts
  - CPU-bound, I/O-bound, and Mixed process type distributions
  - Reproducible via an explicit random seed
"""

import random
from typing import List

from src.process import Process, ProcessType

# (min_burst, max_burst) ranges per process type. CPU-bound processes get
# long, uninterrupted bursts; I/O-bound processes get short CPU bursts
# (they spend most of their time waiting on I/O in a real system); mixed
# processes fall in between.
BURST_RANGES = {
    ProcessType.CPU_BOUND: (10, 30),
    ProcessType.IO_BOUND: (1, 6),
    ProcessType.MIXED: (3, 15),
}


def generate_workload(
    num_processes: int,
    workload_type: str = "mixed",
    seed: int = 42,
    max_arrival_spread: int = None,
    priority_range: tuple = (1, 5),
) -> List[Process]:
    """
    Generate a reproducible synthetic workload.

    Args:
        num_processes: Number of processes to generate (e.g. 8, 35, 120).
        workload_type: One of "cpu_bound", "io_bound", "mixed"
            (case-insensitive). "mixed" produces a mixture of all three
            ProcessType categories in roughly equal proportion.
        seed: Random seed; identical seed + args always produce the same
            workload, which is required for reproducible experiments.
        max_arrival_spread: Latest possible arrival_time. Defaults to
            roughly num_processes // 2, so arrivals cluster realistically
            rather than spreading across an arbitrarily huge range.
        priority_range: Inclusive (min, max) range for process priority,
            where 1 is highest priority.

    Returns:
        List of Process objects, sorted by arrival_time.
    """
    rng = random.Random(seed)
    workload_type = workload_type.lower()
    if max_arrival_spread is None:
        max_arrival_spread = max(1, num_processes // 2)

    processes = []
    for idx in range(1, num_processes + 1):
        pid = f"P{idx}"
        arrival_time = rng.randint(0, max_arrival_spread)

        if workload_type == "cpu_bound":
            ptype = ProcessType.CPU_BOUND
        elif workload_type == "io_bound":
            ptype = ProcessType.IO_BOUND
        elif workload_type == "mixed":
            ptype = rng.choice(list(ProcessType))
        else:
            raise ValueError(
                f"Unknown workload_type '{workload_type}'. "
                "Expected 'cpu_bound', 'io_bound', or 'mixed'."
            )

        low, high = BURST_RANGES[ptype]
        burst_time = rng.randint(low, high)
        priority = rng.randint(*priority_range)

        processes.append(
            Process(
                pid=pid,
                arrival_time=arrival_time,
                burst_time=burst_time,
                priority=priority,
                process_type=ptype,
            )
        )

    processes.sort(key=lambda p: (p.arrival_time, p.pid))
    return processes


def workload_to_rows(processes: List[Process]) -> List[dict]:
    """Convert a workload into plain dicts, convenient for a DataFrame/editable table."""
    return [
        {
            "Process ID": p.pid,
            "Arrival Time": p.arrival_time,
            "Burst Time": p.burst_time,
            "Priority": p.priority,
            "Type": p.process_type.value,
        }
        for p in processes
    ]


def rows_to_workload(rows: List[dict]) -> List[Process]:
    """
    Convert plain dicts (e.g. from an editable Streamlit table) back into
    Process objects. Accepts the same keys produced by workload_to_rows.
    """
    type_lookup = {t.value: t for t in ProcessType}
    processes = []
    for row in rows:
        ptype = type_lookup.get(row.get("Type", "CPU-bound"), ProcessType.CPU_BOUND)
        processes.append(
            Process(
                pid=str(row["Process ID"]),
                arrival_time=int(row["Arrival Time"]),
                burst_time=int(row["Burst Time"]),
                priority=int(row.get("Priority", 0)),
                process_type=ptype,
            )
        )
    return processes

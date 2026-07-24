"""
utils.py

Small shared helpers that don't belong in any single module:
CSV export of results and process tables, and a process-table validator
used before running any simulation (so bad manual edits in the Streamlit
table fail with a clear message instead of crashing a scheduler mid-run).
"""

import io
from typing import List, Tuple

import pandas as pd

from src.metrics import PerformanceMetrics
from src.process import Process
from src.scheduler import SchedulingResult


def validate_processes(processes: List[Process]) -> Tuple[bool, str]:
    """
    Validate a workload before simulation.

    Checks performed:
        - At least one process.
        - No duplicate process IDs.
        - arrival_time >= 0 and burst_time >= 1 for every process.

    Args:
        processes: Workload to validate.

    Returns:
        (True, "") if valid, otherwise (False, message) describing the
        first problem found.
    """
    if not processes:
        return False, "Workload is empty. Add at least one process."

    seen_ids = set()
    for p in processes:
        if p.pid in seen_ids:
            return False, f"Duplicate Process ID found: '{p.pid}'."
        seen_ids.add(p.pid)

        if p.arrival_time < 0:
            return False, f"Process '{p.pid}' has a negative arrival time."
        if p.burst_time < 1:
            return False, f"Process '{p.pid}' must have burst time >= 1."

    return True, ""


def results_to_csv_bytes(result: SchedulingResult) -> bytes:
    """Serialize one algorithm's per-process results as CSV bytes."""
    rows = [
        {
            "Process ID": p.pid,
            "Arrival Time": p.arrival_time,
            "Burst Time": p.burst_time,
            "Priority": p.priority,
            "Start Time": p.start_time,
            "Completion Time": p.completion_time,
            "Waiting Time": p.waiting_time,
            "Turnaround Time": p.turnaround_time,
            "Response Time": p.response_time,
        }
        for p in result.processes
    ]
    df = pd.DataFrame(rows)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def metrics_to_csv_bytes(metrics: List[PerformanceMetrics]) -> bytes:
    """Serialize a list of PerformanceMetrics (algorithm comparison) as CSV bytes."""
    df = pd.DataFrame([m.as_dict() for m in metrics])
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")

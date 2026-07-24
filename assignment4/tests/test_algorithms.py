"""
test_algorithms.py

Unit tests for the six scheduling algorithms. Uses the exact process
table given in the assignment PDF's Section 4.1 (P1-P4) for hand-
verifiable small-set tests, plus generated workloads for edge cases.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src.process import Process, ProcessType
from src.scheduler import Scheduler
from src.metrics import calculate_metrics
from src.workload_generator import generate_workload
from src.utils import validate_processes


def assignment_sample_processes():
    """The P1-P4 table from the assignment PDF (Section 4.1)."""
    return [
        Process("P1", 0, 8, priority=3, process_type=ProcessType.CPU_BOUND),
        Process("P2", 1, 4, priority=1, process_type=ProcessType.CPU_BOUND),
        Process("P3", 2, 9, priority=4, process_type=ProcessType.CPU_BOUND),
        Process("P4", 3, 5, priority=2, process_type=ProcessType.CPU_BOUND),
    ]


@pytest.fixture
def scheduler():
    return Scheduler()


def test_fcfs_matches_hand_calculation(scheduler):
    """
    FCFS by hand: P1 runs 0-8, P2 runs 8-12, P3 runs 12-21, P4 runs 21-26.
    Waiting times: P1=0, P2=8-1=7, P3=12-2=10, P4=21-3=18. Avg = 8.75.
    """
    result = scheduler.run("FCFS", assignment_sample_processes())
    by_pid = {p.pid: p for p in result.processes}
    assert by_pid["P1"].waiting_time == 0
    assert by_pid["P2"].waiting_time == 7
    assert by_pid["P3"].waiting_time == 10
    assert by_pid["P4"].waiting_time == 18
    assert result.total_time == 26


def test_sjf_non_preemptive_order(scheduler):
    """Once P1 starts (only process ready at t=0), SJF cannot preempt it."""
    result = scheduler.run("SJF", assignment_sample_processes())
    by_pid = {p.pid: p for p in result.processes}
    assert by_pid["P1"].start_time == 0
    assert by_pid["P1"].completion_time == 8
    # After P1, ready set at t=8 is {P2(4), P3(9), P4(5)} -> P2 shortest.
    assert by_pid["P2"].start_time == 8


def test_round_robin_response_time_better_than_fcfs(scheduler):
    """RR should give shorter average response time than FCFS for this table."""
    rr = scheduler.run("Round Robin", assignment_sample_processes(), time_quantum=4)
    fcfs = scheduler.run("FCFS", assignment_sample_processes())
    rr_metrics = calculate_metrics(rr)
    fcfs_metrics = calculate_metrics(fcfs)
    assert rr_metrics.avg_response_time <= fcfs_metrics.avg_response_time


def test_priority_selects_lowest_value_first(scheduler):
    """P2 has priority=1 (highest) but arrives at t=1, so P1 (already running) finishes first."""
    result = scheduler.run("Priority", assignment_sample_processes())
    by_pid = {p.pid: p for p in result.processes}
    # At t=0 only P1 is ready, so it must run first despite lower priority.
    assert by_pid["P1"].start_time == 0
    # Next selection among {P2(pri1), P3(pri4), P4(pri2)} at t=8 -> P2.
    assert by_pid["P2"].start_time == 8


def test_srtf_is_preemptive_and_optimal_for_avg_waiting_time(scheduler):
    """SRTF must never produce a *worse* average waiting time than FCFS."""
    srtf = scheduler.run("SRTF", assignment_sample_processes())
    fcfs = scheduler.run("FCFS", assignment_sample_processes())
    srtf_metrics = calculate_metrics(srtf)
    fcfs_metrics = calculate_metrics(fcfs)
    assert srtf_metrics.avg_waiting_time <= fcfs_metrics.avg_waiting_time


def test_mlfq_all_processes_complete(scheduler):
    result = scheduler.run("MLFQ", assignment_sample_processes(), quantums=[4, 8, 16])
    assert len(result.processes) == 4
    assert all(p.remaining_time == 0 for p in result.processes)


@pytest.mark.parametrize("algo", ["FCFS", "SJF", "Round Robin", "Priority", "SRTF", "MLFQ"])
def test_all_algorithms_conserve_total_burst_time(scheduler, algo):
    """Every process must fully execute: sum of history segment lengths == burst_time."""
    kwargs = {"time_quantum": 4} if algo == "Round Robin" else {}
    result = scheduler.run(algo, assignment_sample_processes(), **kwargs)
    for p in result.processes:
        executed = sum(end - start for start, end in p.history)
        assert executed == p.burst_time, f"{algo}: {p.pid} executed {executed}, expected {p.burst_time}"


@pytest.mark.parametrize("algo", ["FCFS", "SJF", "Round Robin", "Priority", "SRTF", "MLFQ"])
@pytest.mark.parametrize("n", [5, 25, 100])
def test_all_algorithms_handle_various_workload_sizes(scheduler, algo, n):
    """Small/medium/large workloads all complete without error."""
    workload = generate_workload(n, workload_type="mixed", seed=7)
    ok, msg = validate_processes(workload)
    assert ok, msg
    kwargs = {"time_quantum": 4} if algo == "Round Robin" else {}
    result = scheduler.run(algo, workload, **kwargs)
    assert len(result.processes) == n
    assert all(p.completion_time is not None for p in result.processes)


def test_all_arrivals_at_time_zero(scheduler):
    """Edge case: every process arrives simultaneously."""
    workload = [Process(f"P{i}", 0, burst_time=i + 1) for i in range(5)]
    for algo in scheduler.available_algorithms():
        kwargs = {"time_quantum": 3} if algo == "Round Robin" else {}
        result = scheduler.run(algo, workload, **kwargs)
        assert all(p.waiting_time >= 0 for p in result.processes)


def test_identical_burst_times(scheduler):
    """Edge case: all processes share the same burst time (tie-breaking must be stable)."""
    workload = [Process(f"P{i}", i, burst_time=5) for i in range(4)]
    result = scheduler.run("SJF", workload)
    assert len(result.processes) == 4


def test_mixed_short_and_long_bursts(scheduler):
    """Edge case: one very short and one very long process together."""
    workload = [Process("Pshort", 0, burst_time=1), Process("Plong", 0, burst_time=150)]
    result = scheduler.run("SRTF", workload)
    by_pid = {p.pid: p for p in result.processes}
    # SRTF must run the short job to completion before (or interleaved ahead of) the long one.
    assert by_pid["Pshort"].completion_time <= by_pid["Plong"].completion_time


def test_reproducible_workload_generation():
    """Same seed must produce an identical workload every time."""
    w1 = generate_workload(20, workload_type="mixed", seed=99)
    w2 = generate_workload(20, workload_type="mixed", seed=99)
    for p1, p2 in zip(w1, w2):
        assert p1.pid == p2.pid
        assert p1.arrival_time == p2.arrival_time
        assert p1.burst_time == p2.burst_time


def test_validate_processes_rejects_duplicate_ids():
    workload = [Process("P1", 0, 5), Process("P1", 1, 3)]
    ok, msg = validate_processes(workload)
    assert not ok
    assert "Duplicate" in msg


def test_validate_processes_rejects_zero_burst():
    workload = [Process("P1", 0, 0)]
    ok, msg = validate_processes(workload)
    assert not ok

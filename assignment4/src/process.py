"""
process.py

Defines the Process (PCB - Process Control Block) data structure used
throughout the CPU scheduling simulator. Every scheduling algorithm
operates on lists of Process objects and mutates their runtime fields
(start_time, completion_time, waiting_time, etc.) as the simulation
progresses.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ProcessType(Enum):
    """Classifies a process by its dominant resource usage pattern."""

    CPU_BOUND = "CPU-bound"
    IO_BOUND = "I/O-bound"
    MIXED = "Mixed"


class ProcessState(Enum):
    """Lifecycle states a process can be in during simulation."""

    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    TERMINATED = "Terminated"


@dataclass
class Process:
    """
    Represents a single process / PCB (Process Control Block).

    Static attributes (set at creation, never changed by a scheduler):
        pid: Unique process identifier, e.g. "P1".
        arrival_time: Simulation time at which the process becomes ready.
        burst_time: Total CPU time (in time units) the process needs.
        priority: Lower number = higher priority (1 is highest).
        process_type: CPU-bound, I/O-bound, or Mixed, used only for
            workload generation/analysis, not by the schedulers.
        io_bursts: Optional list of (cpu_time, io_time) pairs describing
            alternating CPU/I/O phases for I/O-bound and mixed workloads.
            Simple schedulers (FCFS, SJF, RR, Priority, SRTF, MLFQ as
            implemented here) treat burst_time as one CPU phase; io_bursts
            is retained for extensibility and workload characterization.

    Dynamic attributes (filled in / updated by a scheduler as it runs):
        remaining_time: CPU time still left to execute. Initialized to
            burst_time and decremented as the process runs.
        start_time: Simulation time of the process's first ever CPU burst
            (used to compute response time).
        completion_time: Simulation time the process finishes.
        waiting_time: Total time spent ready but not running.
        turnaround_time: completion_time - arrival_time.
        response_time: start_time - arrival_time.
        state: Current lifecycle state of the process.
        history: List of (start, end) tuples of CPU bursts actually
            executed, used to build Gantt charts.
    """

    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 0
    process_type: ProcessType = ProcessType.CPU_BOUND
    io_bursts: Optional[List[tuple]] = None

    # Dynamic / simulation-computed fields
    remaining_time: int = field(init=False)
    start_time: Optional[int] = field(default=None, init=False)
    completion_time: Optional[int] = field(default=None, init=False)
    waiting_time: int = field(default=0, init=False)
    turnaround_time: int = field(default=0, init=False)
    response_time: Optional[int] = field(default=None, init=False)
    state: ProcessState = field(default=ProcessState.NEW, init=False)
    history: List[tuple] = field(default_factory=list, init=False)

    # MLFQ-specific bookkeeping (ignored by other algorithms)
    current_queue_level: int = field(default=0, init=False)
    time_in_current_quantum: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        """Initialize remaining_time from burst_time after dataclass init."""
        self.remaining_time = self.burst_time

    def reset(self) -> None:
        """
        Reset all dynamic fields so this Process can be re-simulated by a
        different algorithm without creating a brand-new object. Static
        attributes (pid, arrival_time, burst_time, priority, ...) are
        left untouched.
        """
        self.remaining_time = self.burst_time
        self.start_time = None
        self.completion_time = None
        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None
        self.state = ProcessState.NEW
        self.history = []
        self.current_queue_level = 0
        self.time_in_current_quantum = 0

    def clone(self) -> "Process":
        """
        Return a fresh Process with the same static attributes and reset
        dynamic state. Used so each algorithm run gets an independent copy
        of a workload instead of sharing mutable state.
        """
        p = Process(
            pid=self.pid,
            arrival_time=self.arrival_time,
            burst_time=self.burst_time,
            priority=self.priority,
            process_type=self.process_type,
            io_bursts=self.io_bursts,
        )
        return p

    def __repr__(self) -> str:
        return (
            f"Process(pid={self.pid!r}, arrival={self.arrival_time}, "
            f"burst={self.burst_time}, priority={self.priority}, "
            f"type={self.process_type.value})"
        )

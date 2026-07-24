"""
scheduler.py

Defines SchedulingResult (the output of running one algorithm over one
workload) and Scheduler, a thin dispatcher that maps algorithm names to
the algorithm implementations in src/algorithms/.

All algorithm functions share a common contract:

    def run(processes: List[Process]) -> SchedulingResult

They receive a list of *cloned* Process objects (so the caller's original
workload is never mutated), simulate execution, fill in each process's
dynamic fields (waiting_time, turnaround_time, completion_time,
response_time, history), and return a SchedulingResult bundling the
processed list with a Gantt-chart-friendly execution timeline.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

from src.process import Process


@dataclass
class SchedulingResult:
    """
    Output of simulating one algorithm on one workload.

    Attributes:
        algorithm_name: Human-readable algorithm name, e.g. "SRTF".
        processes: The simulated processes with all dynamic fields set.
        timeline: Ordered list of (pid, start, end) execution segments,
            used to draw Gantt charts. A pid of "IDLE" marks CPU idle time.
        total_time: The makespan of the schedule (last completion time).
    """

    algorithm_name: str
    processes: List[Process]
    timeline: List[Tuple[str, int, int]] = field(default_factory=list)
    total_time: int = 0


class Scheduler:
    """
    Dispatcher that runs a named algorithm against a workload.

    This class intentionally contains no scheduling logic itself; each
    algorithm lives in its own module under src/algorithms/ so that every
    algorithm can be read, tested, and reasoned about independently.
    """

    def __init__(self) -> None:
        # Imported lazily inside __init__ to avoid circular imports since
        # each algorithm module imports Process/SchedulingResult types.
        from src.algorithms.fcfs import fcfs
        from src.algorithms.sjf import sjf
        from src.algorithms.round_robin import round_robin
        from src.algorithms.priority import priority_scheduling
        from src.algorithms.srtf import srtf
        from src.algorithms.mlfq import mlfq

        self._registry: Dict[str, Callable[..., SchedulingResult]] = {
            "FCFS": fcfs,
            "SJF": sjf,
            "Round Robin": round_robin,
            "Priority": priority_scheduling,
            "SRTF": srtf,
            "MLFQ": mlfq,
        }

    def available_algorithms(self) -> List[str]:
        """Return the list of algorithm names this scheduler can run."""
        return list(self._registry.keys())

    def run(self, algorithm_name: str, processes: List[Process], **kwargs) -> SchedulingResult:
        """
        Run the named algorithm on a fresh clone of `processes`.

        Args:
            algorithm_name: One of the keys returned by available_algorithms().
            processes: The workload to schedule (not mutated).
            **kwargs: Algorithm-specific parameters, e.g. time_quantum=4
                for Round Robin, or quantums=[4, 8, 16] for MLFQ.

        Returns:
            A SchedulingResult describing the simulated run.

        Raises:
            ValueError: If algorithm_name is not registered.
        """
        if algorithm_name not in self._registry:
            raise ValueError(
                f"Unknown algorithm '{algorithm_name}'. "
                f"Available: {self.available_algorithms()}"
            )
        # Clone so repeated runs / different algorithms never share state.
        workload = [p.clone() for p in processes]
        algorithm_fn = self._registry[algorithm_name]
        return algorithm_fn(workload, **kwargs)

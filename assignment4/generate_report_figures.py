"""
generate_report_figures.py

Standalone script (not part of the Streamlit app) that renders the
figures embedded in report/report.tex using matplotlib, since the
report needs static raster/vector images rather than the interactive
Plotly charts used in app.py. Run this after any change to the
algorithms or workload generator to refresh report/figures/*.png.

Usage:
    PYTHONPATH=. python3 generate_report_figures.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.metrics import calculate_metrics
from src.scheduler import Scheduler
from src.workload_generator import generate_workload

FIG_DIR = "report/figures"
ALGO_COLORS = {
    "FCFS": "#4C72B0",
    "SJF": "#DD8452",
    "Round Robin": "#55A868",
    "Priority": "#C44E52",
    "SRTF": "#8172B2",
    "MLFQ": "#937860",
}


def run_kwargs(algo: str) -> dict:
    if algo == "Round Robin":
        return {"time_quantum": 4}
    if algo == "MLFQ":
        return {"quantums": [4, 8, 16]}
    return {}


def gantt_figure(result, algo_name: str, path: str) -> None:
    """Render one algorithm's schedule as a horizontal Gantt bar."""
    fig, ax = plt.subplots(figsize=(10, 1.8))
    pids = sorted({pid for pid, _, _ in result.timeline if pid != "IDLE"})
    palette = plt.cm.tab20.colors
    pid_color = {pid: palette[i % len(palette)] for i, pid in enumerate(pids)}

    for pid, start, end in result.timeline:
        color = "#d9d9d9" if pid == "IDLE" else pid_color[pid]
        ax.barh(0, end - start, left=start, height=0.6, color=color, edgecolor="white")
        if end - start >= 1 and pid != "IDLE":
            ax.text((start + end) / 2, 0, pid, ha="center", va="center", fontsize=7)

    ax.set_yticks([])
    ax.set_xlabel("Time")
    ax.set_title(f"{algo_name} - Gantt Chart", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def comparison_bar(metrics, metric_attr: str, ylabel: str, title: str, path: str) -> None:
    algos = [m.algorithm_name for m in metrics]
    values = [getattr(m, metric_attr) for m in metrics]
    colors = [ALGO_COLORS.get(a, "#888888") for a in algos]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(algos, values, color=colors)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=11)
    ax.tick_params(axis="x", rotation=20)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def scaling_line_chart(path: str) -> None:
    sched = Scheduler()
    sizes = [("small", 8), ("medium", 30), ("large", 120)]
    series = {algo: [] for algo in sched.available_algorithms()}

    for _, n in sizes:
        wl = generate_workload(n, workload_type="mixed", seed=42)
        for algo in sched.available_algorithms():
            result = sched.run(algo, wl, **run_kwargs(algo))
            m = calculate_metrics(result)
            series[algo].append(m.avg_waiting_time)

    x = [n for _, n in sizes]
    fig, ax = plt.subplots(figsize=(8, 5))
    for algo, ys in series.items():
        ax.plot(x, ys, marker="o", label=algo, color=ALGO_COLORS.get(algo))
    ax.set_xlabel("Number of Processes")
    ax.set_ylabel("Average Waiting Time")
    ax.set_title("Average Waiting Time vs. Workload Size (Mixed Workloads)", fontsize=11)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main() -> None:
    sched = Scheduler()

    # Gantt charts: small mixed workload (readable at report scale).
    wl_small = generate_workload(8, workload_type="mixed", seed=42)
    for algo in sched.available_algorithms():
        result = sched.run(algo, wl_small, **run_kwargs(algo))
        fname = f"{FIG_DIR}/gantt_{algo.replace(' ', '_').lower()}.png"
        gantt_figure(result, algo, fname)
    print("Gantt charts written.")

    # Comparison bar charts: medium mixed workload (representative middle ground).
    wl_medium = generate_workload(30, workload_type="mixed", seed=42)
    metrics = [
        calculate_metrics(sched.run(algo, wl_medium, **run_kwargs(algo)))
        for algo in sched.available_algorithms()
    ]
    comparison_bar(metrics, "avg_waiting_time", "Time Units", "Average Waiting Time", f"{FIG_DIR}/compare_waiting_time.png")
    comparison_bar(metrics, "avg_turnaround_time", "Time Units", "Average Turnaround Time", f"{FIG_DIR}/compare_turnaround_time.png")
    comparison_bar(metrics, "cpu_utilization", "Percent", "CPU Utilization (%)", f"{FIG_DIR}/compare_cpu_utilization.png")
    comparison_bar(metrics, "throughput", "Processes / Unit Time", "Throughput", f"{FIG_DIR}/compare_throughput.png")
    print("Comparison bar charts written.")

    # Scaling behavior across workload sizes.
    scaling_line_chart(f"{FIG_DIR}/scaling_waiting_time.png")
    print("Scaling chart written.")


if __name__ == "__main__":
    main()

"""
visualization.py

Chart-building helpers built on Plotly, used by both the Streamlit app
and (optionally) standalone scripts that export static images for the
LaTeX report. Kept separate from app.py so charts can be unit tested
and reused without a running Streamlit session.
"""

from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.metrics import PerformanceMetrics
from src.scheduler import SchedulingResult

# A stable, readable color per process id so the same process keeps the
# same color across different algorithms' Gantt charts, making it easier
# to visually compare how each algorithm treats the same process.
_PALETTE = px.colors.qualitative.Set3


def _color_for_pid(pid: str, pid_list: List[str]) -> str:
    if pid == "IDLE":
        return "#d9d9d9"
    idx = pid_list.index(pid) % len(_PALETTE)
    return _PALETTE[idx]


def build_gantt_chart(result: SchedulingResult) -> go.Figure:
    """
    Build a horizontal Gantt chart of CPU execution for one algorithm run.

    Args:
        result: A SchedulingResult with a populated timeline.

    Returns:
        A Plotly Figure ready to be passed to st.plotly_chart().
    """
    pid_list = sorted({pid for pid, _, _ in result.timeline if pid != "IDLE"})
    fig = go.Figure()

    for pid, start, end in result.timeline:
        fig.add_trace(
            go.Bar(
                x=[end - start],
                y=["CPU"],
                base=start,
                orientation="h",
                name=pid,
                marker=dict(color=_color_for_pid(pid, pid_list)),
                hovertemplate=f"{pid}<br>Start: {start}<br>End: {end}<extra></extra>",
                showlegend=False,
                text=pid if pid != "IDLE" else "",
                textposition="inside",
            )
        )

    fig.update_layout(
        title=f"{result.algorithm_name} - Gantt Chart",
        barmode="stack",
        xaxis_title="Time",
        yaxis_title="",
        height=220,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def build_metric_comparison_chart(metrics: List[PerformanceMetrics], metric_key: str, title: str) -> go.Figure:
    """
    Build a bar chart comparing one metric across all algorithms.

    Args:
        metrics: List of PerformanceMetrics, one per algorithm.
        metric_key: Attribute name on PerformanceMetrics to plot, e.g.
            "avg_waiting_time".
        title: Chart title / y-axis label.

    Returns:
        A Plotly Figure.
    """
    df = pd.DataFrame(
        {
            "Algorithm": [m.algorithm_name for m in metrics],
            title: [getattr(m, metric_key) for m in metrics],
        }
    )
    fig = px.bar(df, x="Algorithm", y=title, color="Algorithm", title=title, text_auto=".2f")
    fig.update_layout(showlegend=False, height=350, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def build_all_comparison_charts(metrics: List[PerformanceMetrics]) -> dict:
    """
    Build the standard set of comparison charts required by the assignment:
    average waiting time, turnaround time, CPU utilization, and throughput.

    Returns:
        Dict mapping a short key to a Plotly Figure.
    """
    return {
        "waiting_time": build_metric_comparison_chart(metrics, "avg_waiting_time", "Average Waiting Time"),
        "turnaround_time": build_metric_comparison_chart(metrics, "avg_turnaround_time", "Average Turnaround Time"),
        "cpu_utilization": build_metric_comparison_chart(metrics, "cpu_utilization", "CPU Utilization (%)"),
        "throughput": build_metric_comparison_chart(metrics, "throughput", "Throughput (proc/unit time)"),
    }


def metrics_to_dataframe(metrics: List[PerformanceMetrics]) -> pd.DataFrame:
    """Convert a list of PerformanceMetrics into a display-ready DataFrame."""
    return pd.DataFrame([m.as_dict() for m in metrics])

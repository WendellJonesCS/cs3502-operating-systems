"""
app.py

Streamlit web interface for the CPU Scheduling Simulator.

Layout:
    Sidebar   - workload generation controls (size, type, seed) and an
                editable process table; algorithm selection.
    Main area - Run Simulation button, per-algorithm Gantt charts,
                a metrics comparison table, comparison bar charts, and
                CSV download buttons.

Run with:  streamlit run app.py
"""

from typing import List

import pandas as pd
import streamlit as st

from src.metrics import calculate_metrics, PerformanceMetrics
from src.process import Process
from src.scheduler import Scheduler
from src.utils import metrics_to_csv_bytes, results_to_csv_bytes, validate_processes
from src.visualization import build_all_comparison_charts, build_gantt_chart, metrics_to_dataframe
from src.workload_generator import generate_workload, rows_to_workload, workload_to_rows

st.set_page_config(page_title="CPU Scheduling Simulator", layout="wide")

ALL_ALGORITHMS = ["FCFS", "SJF", "Round Robin", "Priority", "SRTF", "MLFQ"]


# --------------------------------------------------------------------------
# Session state initialization
# --------------------------------------------------------------------------
if "workload_rows" not in st.session_state:
    st.session_state.workload_rows = workload_to_rows(
        generate_workload(8, workload_type="mixed", seed=42)
    )
if "results" not in st.session_state:
    st.session_state.results = None  # dict[algo_name] -> SchedulingResult
if "metrics" not in st.session_state:
    st.session_state.metrics = None  # list[PerformanceMetrics]


# --------------------------------------------------------------------------
# Sidebar: workload generation + algorithm selection
# --------------------------------------------------------------------------
st.sidebar.title("⚙️ Simulation Setup")

st.sidebar.subheader("1. Generate Workload")
size_preset = st.sidebar.selectbox(
    "Size preset",
    ["Small (5-10)", "Medium (20-50)", "Large (100+)", "Custom"],
)
default_by_preset = {"Small (5-10)": 8, "Medium (20-50)": 30, "Large (100+)": 120, "Custom": 10}
num_processes = st.sidebar.number_input(
    "Number of processes",
    min_value=1,
    max_value=500,
    value=default_by_preset[size_preset],
    disabled=(size_preset != "Custom"),
)
workload_type = st.sidebar.selectbox(
    "Workload type",
    ["mixed", "cpu_bound", "io_bound"],
    format_func=lambda v: {"mixed": "Mixed", "cpu_bound": "CPU-bound", "io_bound": "I/O-bound"}[v],
)
seed = st.sidebar.number_input("Random seed", min_value=0, max_value=10_000, value=42, step=1)

if st.sidebar.button("🎲 Generate Workload", use_container_width=True):
    n = default_by_preset[size_preset] if size_preset != "Custom" else num_processes
    workload = generate_workload(int(n), workload_type=workload_type, seed=int(seed))
    st.session_state.workload_rows = workload_to_rows(workload)
    st.session_state.results = None
    st.session_state.metrics = None

st.sidebar.subheader("2. Choose Algorithms")
selected_algorithms = st.sidebar.multiselect(
    "Algorithms to run", ALL_ALGORITHMS, default=ALL_ALGORITHMS
)
time_quantum = st.sidebar.slider("Round Robin time quantum", min_value=1, max_value=20, value=4)
mlfq_quanta_text = st.sidebar.text_input("MLFQ quantums (comma-separated)", value="4,8,16")

st.sidebar.subheader("3. Run")
run_clicked = st.sidebar.button("▶️ Run Simulation", type="primary", use_container_width=True)


# --------------------------------------------------------------------------
# Main area: title + editable process table
# --------------------------------------------------------------------------
st.title("🖥️ CPU Scheduling Simulator")
st.caption(
    "CS 3502 - Project 2 | OwlTech Industries Performance Optimization Division | "
    "FCFS · SJF · Round Robin · Priority · SRTF · MLFQ"
)

st.subheader("Process Table (editable)")
st.write(
    "Edit values directly in the table below, or use the sidebar to generate a new "
    "random workload. Columns: Process ID, Arrival Time, Burst Time, Priority (1 = highest), Type."
)

edited_df = st.data_editor(
    pd.DataFrame(st.session_state.workload_rows),
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Priority": st.column_config.NumberColumn(min_value=1, max_value=10, step=1),
        "Arrival Time": st.column_config.NumberColumn(min_value=0, step=1),
        "Burst Time": st.column_config.NumberColumn(min_value=1, step=1),
        "Type": st.column_config.SelectboxColumn(options=["CPU-bound", "I/O-bound", "Mixed"]),
    },
    key="process_editor",
)
st.session_state.workload_rows = edited_df.to_dict("records")


# --------------------------------------------------------------------------
# Run simulation
# --------------------------------------------------------------------------
def parse_mlfq_quanta(text: str) -> List[int]:
    try:
        values = [int(x.strip()) for x in text.split(",") if x.strip()]
        return values if values else [4, 8, 16]
    except ValueError:
        st.warning("Could not parse MLFQ quantums, falling back to default [4, 8, 16].")
        return [4, 8, 16]


if run_clicked:
    workload = rows_to_workload(st.session_state.workload_rows)
    ok, msg = validate_processes(workload)

    if not ok:
        st.error(f"Invalid workload: {msg}")
    elif not selected_algorithms:
        st.error("Select at least one algorithm to run.")
    else:
        scheduler = Scheduler()
        results = {}
        for algo in selected_algorithms:
            kwargs = {}
            if algo == "Round Robin":
                kwargs = {"time_quantum": int(time_quantum)}
            elif algo == "MLFQ":
                kwargs = {"quantums": parse_mlfq_quanta(mlfq_quanta_text)}
            results[algo] = scheduler.run(algo, workload, **kwargs)

        st.session_state.results = results
        st.session_state.metrics = [calculate_metrics(r) for r in results.values()]
        st.success(f"Simulation complete: {len(results)} algorithm(s) x {len(workload)} process(es).")


# --------------------------------------------------------------------------
# Results: metrics table, comparison charts, per-algorithm Gantt + downloads
# --------------------------------------------------------------------------
if st.session_state.results:
    results = st.session_state.results
    metrics: List[PerformanceMetrics] = st.session_state.metrics

    st.header("📊 Performance Metrics")
    metrics_df = metrics_to_dataframe(metrics)
    st.dataframe(metrics_df, use_container_width=True)
    st.download_button(
        "⬇️ Download comparison metrics (CSV)",
        data=metrics_to_csv_bytes(metrics),
        file_name="algorithm_comparison_metrics.csv",
        mime="text/csv",
    )

    st.header("📈 Algorithm Comparison Charts")
    charts = build_all_comparison_charts(metrics)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts["waiting_time"], use_container_width=True)
        st.plotly_chart(charts["cpu_utilization"], use_container_width=True)
    with col2:
        st.plotly_chart(charts["turnaround_time"], use_container_width=True)
        st.plotly_chart(charts["throughput"], use_container_width=True)

    st.header("📅 Gantt Charts & Per-Process Results")
    tabs = st.tabs(list(results.keys()))
    for tab, (algo_name, result) in zip(tabs, results.items()):
        with tab:
            st.plotly_chart(build_gantt_chart(result), use_container_width=True)

            rows = [
                {
                    "Process ID": p.pid,
                    "Arrival": p.arrival_time,
                    "Burst": p.burst_time,
                    "Priority": p.priority,
                    "Start": p.start_time,
                    "Completion": p.completion_time,
                    "Waiting": p.waiting_time,
                    "Turnaround": p.turnaround_time,
                    "Response": p.response_time,
                }
                for p in sorted(result.processes, key=lambda p: p.pid)
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
            st.download_button(
                f"⬇️ Download {algo_name} results (CSV)",
                data=results_to_csv_bytes(result),
                file_name=f"{algo_name.replace(' ', '_').lower()}_results.csv",
                mime="text/csv",
                key=f"download_{algo_name}",
            )
else:
    st.info("Configure a workload above, choose algorithms in the sidebar, then click **Run Simulation**.")

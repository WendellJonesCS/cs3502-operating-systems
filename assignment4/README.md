# CPU Scheduling Simulator

**CS 3502: Operating Systems — Project 2**
OwlTech Industries — Performance Optimization Division

A from-scratch CPU scheduling simulator and performance analysis tool, built
in Python with a Streamlit web interface (Hybrid approach: algorithm logic
extracted into an original console/web implementation rather than extending
the C# starter).

## Features

- **Six scheduling algorithms**: FCFS, SJF, Round Robin, Priority (starter
  set) plus **SRTF** and **MLFQ** (the two new algorithms required by the
  assignment)
- **Performance metrics** for every algorithm: average waiting time,
  average turnaround time, average response time, CPU utilization,
  throughput
- **Reproducible workload generation**: small (5-10), medium (20-50), and
  large (100+) process counts; CPU-bound, I/O-bound, and mixed process
  types; seeded for exact reproducibility
- **Interactive Streamlit interface**: editable process table, workload
  generator, algorithm selector, Gantt charts, comparison charts, CSV export
- **36 unit tests** covering correctness (hand-verified against the
  assignment's own example table), edge cases, and scale
- **LaTeX report** with real generated data, figures, and analysis

## Directory Structure

```
assignment4/
├── app.py                     Streamlit web interface
├── requirements.txt
├── README.md
├── generate_report_figures.py Regenerates report figures from live code
├── report/
│   ├── report.tex             Full LaTeX report source
│   ├── report.pdf             Compiled report (generate via instructions below)
│   ├── references.bib
│   ├── results_tables.tex     Auto-generated result tables (real data)
│   └── figures/                Gantt charts, comparison charts, screenshots
├── src/
│   ├── process.py             Process / PCB data structure
│   ├── scheduler.py           Algorithm dispatcher
│   ├── metrics.py             Metric calculations
│   ├── workload_generator.py  Reproducible workload generation
│   ├── visualization.py       Plotly Gantt & comparison charts
│   ├── utils.py                Validation, CSV export
│   └── algorithms/
│       ├── fcfs.py
│       ├── sjf.py
│       ├── round_robin.py
│       ├── priority.py
│       ├── srtf.py             (new algorithm)
│       └── mlfq.py             (new algorithm)
├── data/                       Generated sample workloads (CSV)
├── screenshots/                Streamlit screenshots for the report
├── results/                    Generated per-run results and comparisons
└── tests/
    └── test_algorithms.py     36 unit tests
```

## Installation (WSL2 Ubuntu)

### 1. Prerequisites

Confirm Python 3.10+ is available:

```bash
python3 --version
```

### 2. Create and activate a virtual environment

```bash
cd ~/cs3502/assignment4
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now start with `(venv)`.

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Running the Simulator

With the virtual environment activated:

```bash
streamlit run app.py
```

Streamlit will print a local URL (typically `http://localhost:8501`). Open
it in your browser. If you're on WSL2, Windows browsers can usually reach
`localhost` URLs opened from WSL2 directly; if not, use the Network URL
Streamlit prints instead.

## Running the Tests

```bash
pytest tests/ -q
```

Expected output: `36 passed`.

## Generating Sample Data

The `data/` and `results/` directories already contain generated
workloads and results (seed=42) for all 9 (size × type) combinations. To
regenerate them (e.g. after changing an algorithm):

```bash
python3 -c "
from src.workload_generator import generate_workload, workload_to_rows
from src.scheduler import Scheduler
from src.metrics import calculate_metrics
from src.utils import results_to_csv_bytes
import pandas as pd

sched = Scheduler()
for size_name, n in [('small', 8), ('medium', 30), ('large', 120)]:
    for wt in ['cpu_bound', 'io_bound', 'mixed']:
        wl = generate_workload(n, workload_type=wt, seed=42)
        pd.DataFrame(workload_to_rows(wl)).to_csv(f'data/workload_{size_name}_{wt}.csv', index=False)
        for algo in sched.available_algorithms():
            kwargs = {'time_quantum': 4} if algo == 'Round Robin' else ({'quantums':[4,8,16]} if algo=='MLFQ' else {})
            result = sched.run(algo, wl, **kwargs)
            with open(f'results/{size_name}_{wt}_{algo.replace(\" \",\"_\").lower()}_results.csv', 'wb') as f:
                f.write(results_to_csv_bytes(result))
"
```

Or simply run `streamlit run app.py` and use the "Generate Workload" +
"Run Simulation" buttons interactively, then use the in-app CSV download
buttons.

## Generating the Report Figures

The LaTeX report uses static matplotlib figures (not the interactive
Plotly charts in the app) so it can compile without a browser dependency:

```bash
python3 generate_report_figures.py
```

This regenerates every PNG in `report/figures/` from the current
algorithm code and a fixed seed (42), so the report always reflects real,
reproducible simulation output.

## Compiling the LaTeX Report

Requires a LaTeX distribution (e.g. `texlive-full` or at minimum
`texlive-latex-extra`):

```bash
sudo apt update
sudo apt install texlive-latex-extra texlive-fonts-recommended
```

Then, from the `report/` directory:

```bash
cd report
pdflatex -interaction=nonstopmode report.tex
bibtex report
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
```

(Two `pdflatex` passes after `bibtex` are needed to correctly resolve
citations and the table of contents.) The output is `report/report.pdf`.

## Adding Your Screenshots

See the walkthrough at the end of this conversation for exactly how to
capture and insert screenshots into `report.tex`.

## Algorithms Implemented

| Algorithm | Type | Notes |
|---|---|---|
| FCFS | Non-preemptive | Baseline; suffers from convoy effect |
| SJF | Non-preemptive | Optimal AWT among non-preemptive algorithms |
| Round Robin | Preemptive | Fair, low response time; configurable quantum |
| Priority | Non-preemptive | Lower value = higher priority; no aging |
| **SRTF** | Preemptive | *New algorithm* — optimal AWT overall |
| **MLFQ** | Preemptive, adaptive | *New algorithm* — 3 levels, quanta [4,8,16] by default |

## Author

Bryce Wendell Jones — CS 3502: Operating Systems, Kennesaw State University

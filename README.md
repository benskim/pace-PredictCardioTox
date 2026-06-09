# PredictCardioTox ECG Analytics Workspace

This repository is a GitHub Codespace-ready Python 3.12 workspace for ECG analytics validation against the PhysioNet QT Database. It focuses on notebook-driven analytics, repeatable data loading, QTc calculation, baseline analysis, and alert generation. It does not include a web application.

## Codespace setup

Open the repository in GitHub Codespaces. The dev container installs Python 3.12 and runs:

```bash
python -m pip install --upgrade pip && python -m pip install -e .[dev]
```

Start Jupyter Lab from the terminal:

```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

## Project structure

- `notebooks/` — validation notebooks for each analytics stage.
- `src/ecg_analytics/` — reusable ECG loading, QTc, baseline, and alert utilities.
- `scripts/` — command-line helpers for PhysioNet QT Database download and inspection.
- `tests/` — unit tests for analytics utilities.
- `data/` — local data mount/download target; generated files are git-ignored.

## Download the PhysioNet QT Database

Use the WFDB-backed downloader:

```bash
python scripts/download_physionet_qt.py --data-dir data/physionet --records sel100 sel102 --annotators pu0
```

Omit `--records` to download the full QT Database. The full database can be large; start with a few records for validation.

## Notebook workflow

1. `notebooks/01_load_physionet.ipynb` — download/load QT Database records and annotations.
2. `notebooks/02_qtc_calculation.ipynb` — calculate QTc using Bazett, Fridericia, Framingham, and Hodges corrections.
3. `notebooks/03_baseline_analysis.ipynb` — summarize baseline QT/QTc distributions by subject or cohort.
4. `notebooks/04_alert_generation.ipynb` — generate analytics validation alerts from QTc thresholds and deltas.

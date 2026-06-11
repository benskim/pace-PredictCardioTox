#!/usr/bin/env python3
"""Generate the 12 research notebook templates."""

import json, pathlib

NB_DIR = pathlib.Path(__file__).resolve().parent.parent / "notebooks"
NB_DIR.mkdir(exist_ok=True)


def nb(cells):
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12.0"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def md(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source if isinstance(source, list) else [source],
        "id": "",
    }


def code(source):
    return {
        "cell_type": "code",
        "metadata": {},
        "source": source if isinstance(source, list) else [source],
        "execution_count": None,
        "outputs": [],
        "id": "",
    }


# ============================================================
# 01 — Dataset Exploration
# ============================================================
notebooks = {}
notebooks["01_dataset_exploration.ipynb"] = nb(
    [
        md(
            "# 01 — Dataset Exploration\n\nLoad and inspect records from the PhysioNet QT Database, LUDB, NSTDB, INCART, and PTB-XL datasets via the unified `ECGRecord` interface."
        ),
        code("import sys\nsys.path.insert(0, '../src')"),
        code(
            "from ecg_analytics.datasets import QTDBDataset, LUDBDataset, NSTDBDataset, INCARTDataset, PTBXLDataset"
        ),
        code("from ecg_analytics.visualization import plot_multi_lead"),
        md("## PhysioNet QT Database"),
        code(
            "qtdb = QTDBDataset(data_dir='../data/physionet')\n# qtdb.download(records=['sel100', 'sel102'])  # uncomment to download\nprint('QTDB records:', qtdb.list_records()[:10])"
        ),
        code(
            "rec = qtdb.load_record('sel100')\nprint(f'Record: {rec.record_id}, fs={rec.fs} Hz, duration={rec.duration_s:.1f}s, leads={rec.lead_names}')"
        ),
        md("## LUDB"),
        code(
            "ludb = LUDBDataset(data_dir='../data/physionet')\n# ludb.download(records=['1', '2'])  # uncomment to download\nprint('LUDB records:', ludb.list_records()[:10])\nrec = ludb.load_record('1')\nprint(f'Record: {rec.record_id}, fs={rec.fs} Hz, duration={rec.duration_s:.1f}s, leads={rec.lead_names}')"
        ),
        md("## MIT-BIH Noise Stress Test Database (NSTDB)"),
        code(
            "nstdb = NSTDBDataset(data_dir='../data/physionet')\n# nstdb.download(records=['118e00', '118e06'])  # uncomment to download\nprint('NSTDB records:', nstdb.list_records()[:10])"
        ),
        code(
            "nstdb_record_ids = nstdb.list_records()\nif nstdb_record_ids:\n    rec = nstdb.load_record(nstdb_record_ids[0])\n    print(f'Record: {rec.record_id}, fs={rec.fs} Hz, duration={rec.duration_s:.1f}s, leads={rec.lead_names}')"
        ),
        md("## INCART Database"),
        code(
            "incart = INCARTDataset(data_dir='../data/physionet')\n# incart.download(records=['I01', 'I02'])  # uncomment to download\nprint('INCART records:', incart.list_records()[:10])"
        ),
        code(
            "incart_record_ids = incart.list_records()\nif incart_record_ids:\n    rec = incart.load_record(incart_record_ids[0])\n    print(f'Record: {rec.record_id}, fs={rec.fs} Hz, duration={rec.duration_s:.1f}s, leads={rec.lead_names}')"
        ),
        md("## PTB-XL Database"),
        code(
            "ptbxl = PTBXLDataset(data_dir='../data/physionet')\n# ptbxl.download(records=['records100/00000/00001_lr'])  # uncomment to download\nprint('PTB-XL records:', ptbxl.list_records()[:10])"
        ),
        code(
            "ptbxl_record_ids = ptbxl.list_records()\nif ptbxl_record_ids:\n    rec = ptbxl.load_record(ptbxl_record_ids[0])\n    print(f'Record: {rec.record_id}, fs={rec.fs} Hz, duration={rec.duration_s:.1f}s, leads={rec.lead_names}')"
        ),
        md("## Signal Inspection"),
        code(
            "rec = qtdb.load_record('sel100')\nfig = plot_multi_lead(rec.signal, rec.fs, lead_names=rec.lead_names, title='QTDB sel100')"
        ),
    ]
)

# ============================================================
# 02 — Signal Quality
# ============================================================
notebooks["02_signal_quality.ipynb"] = nb(
    [
        md(
            "# 02 — Signal Quality Assessment\n\nEvaluate signal quality metrics and visualize noisy vs. clean signals."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code("from ecg_analytics.preprocessing import signal_quality_index, snr_estimate"),
        code(
            "# Generate synthetic clean signal\nfs = 250.0\nt = np.arange(0, 10, 1/fs)\nclean = np.sin(2 * np.pi * 1.0 * t)"
        ),
        code(
            "sqi = signal_quality_index(clean, fs)\nprint('Signal Quality Index:')\nfor k, v in sqi.items():\n    print(f'  {k}: {v:.3f}')"
        ),
        code(
            "# Add noise and re-evaluate\nnoisy = clean + 0.5 * np.random.randn(len(clean))\nsqi_noisy = signal_quality_index(noisy, fs)\nprint('\\nNoisy SQI:')\nfor k, v in sqi_noisy.items():\n    print(f'  {k}: {v:.3f}')"
        ),
    ]
)

# ============================================================
# 03 — Wave Delineation
# ============================================================
notebooks["03_wave_delineation.ipynb"] = nb(
    [
        md(
            "# 03 — Wave Delineation (1-D U-Net)\n\nDemonstrate the wave delineation pipeline using the 1-D U-Net\nsegmentation model. The model classifies each sample as\nbackground, P-wave, QRS, or T-wave."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np\nimport torch"),
        code(
            "from ecg_analytics.delineation import UNet1D, delineate, WAVE_CLASSES\nfrom ecg_analytics.delineation.labels import encode_annotations, decode_mask"
        ),
        md("## Model Architecture"),
        code(
            "model = UNet1D(in_channels=1, n_classes=4, base_filters=32, depth=4)\nprint(model)\nprint(f'\\nParameters: {sum(p.numel() for p in model.parameters()):,}')"
        ),
        md("## Inference on Synthetic Signal"),
        code(
            "fs = 250.0\nt = np.arange(0, 5, 1/fs)\nsignal = np.sin(2 * np.pi * 1.2 * t).astype(np.float32)\n\nresult = delineate(signal, model=model)\nprint(f'Mask shape: {result.mask.shape}')\nprint(f'Unique classes: {np.unique(result.mask)}')\nprint(f'Regions: {result.regions}')"
        ),
        md("## Delineation Overlay"),
        code(
            "from ecg_analytics.visualization import plot_delineation_overlay\nfig = plot_delineation_overlay(signal, result.mask, fs)"
        ),
    ]
)

# ============================================================
# 04 — T-wave Analysis
# ============================================================
notebooks["04_t_wave_analysis.ipynb"] = nb(
    [
        md(
            "# 04 — T-wave Analysis\n\nExtract T-wave regions, locate T-peaks, and analyze T-wave morphology."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code("from ecg_analytics.qt import extract_t_wave_region, find_t_peak"),
        md("## T-wave Region Extraction"),
        code(
            "# Synthetic ECG with clear T-wave\nfs = 250.0\nt = np.arange(0, 2, 1/fs)\nqrs = np.exp(-((t - 0.5)**2) / (2 * 0.005**2))\nt_wave = 0.3 * np.exp(-((t - 0.8)**2) / (2 * 0.03**2))\nsignal = qrs + t_wave + 0.02 * np.random.randn(len(t))\n\nr_peak = int(0.5 * fs)\nt_start, t_end = extract_t_wave_region(signal, r_peak, fs)\nprint(f'T-wave search region: samples {t_start}-{t_end} ({t_start/fs:.3f}s - {t_end/fs:.3f}s)')"
        ),
        code(
            "t_peak = find_t_peak(signal, t_start, t_end)\nif t_peak is not None:\n    print(f'T-peak at sample {t_peak} ({t_peak/fs:.3f}s)')"
        ),
        md("## Visualization"),
        code(
            "import matplotlib.pyplot as plt\nfig, ax = plt.subplots(figsize=(12, 4))\ntime = np.arange(len(signal)) / fs\nax.plot(time, signal, 'b-', lw=0.8)\nax.axvspan(t_start/fs, t_end/fs, alpha=0.2, color='orange', label='T-wave region')\nif t_peak:\n    ax.axvline(t_peak/fs, color='red', ls='--', label='T-peak')\nax.legend()\nax.set_xlabel('Time (s)')\nax.set_title('T-wave Region Extraction')\nplt.tight_layout()"
        ),
    ]
)

# ============================================================
# 05 — Tangent Method
# ============================================================
notebooks["05_tangent_method.ipynb"] = nb(
    [
        md(
            "# 05 — Geometric Tangent Method for T-end\n\nThe tangent method determines T-end by fitting a line at the point of\nmaximum downslope on the trailing T-wave edge, then finding its\nintersection with the isoelectric baseline."
        ),
        code(
            "import sys\nsys.path.insert(0, '../src')\nimport numpy as np\nimport matplotlib.pyplot as plt"
        ),
        code("from ecg_analytics.qt import tangent_t_end, find_t_peak, extract_t_wave_region"),
        md("## Construct a Synthetic Beat"),
        code(
            "fs = 500.0\nt = np.arange(0, 1.0, 1/fs)\nqrs = 1.5 * np.exp(-((t - 0.2)**2) / (2 * 0.004**2))\nt_wave = 0.4 * np.exp(-((t - 0.45)**2) / (2 * 0.02**2))\nsignal = qrs + t_wave\n\nr_peak = int(0.2 * fs)\nt_start, t_end_search = extract_t_wave_region(signal, r_peak, fs)\nt_peak_idx = find_t_peak(signal, t_start, t_end_search)\nprint(f'T-peak at sample {t_peak_idx}')"
        ),
        md("## Apply Tangent Method"),
        code(
            "t_end_idx = tangent_t_end(signal, t_peak_idx, fs, baseline=0.0)\nprint(f'T-end at sample {t_end_idx} ({t_end_idx/fs*1000:.1f} ms)')"
        ),
        code(
            "fig, ax = plt.subplots(figsize=(12, 4))\ntime = np.arange(len(signal)) / fs * 1000\nax.plot(time, signal, 'b-', lw=1)\nax.axvline(t_peak_idx/fs*1000, color='green', ls='--', label='T-peak')\nif t_end_idx:\n    ax.axvline(t_end_idx/fs*1000, color='red', ls='--', label='T-end (tangent)')\nax.axhline(0, color='gray', ls=':', alpha=0.5)\nax.legend()\nax.set_xlabel('Time (ms)')\nax.set_title('Tangent Method T-end Determination')\nplt.tight_layout()"
        ),
    ]
)

# ============================================================
# 06 — QT Measurement
# ============================================================
notebooks["06_qt_measurement.ipynb"] = nb(
    [
        md(
            "# 06 — QT Interval Measurement\n\nEnd-to-end QT measurement: R-peak detection → Q-onset → T-end\n(tangent method) → QT interval."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code("from ecg_analytics.qt import measure_qt_intervals"),
        md("## Synthetic Multi-Beat Signal"),
        code(
            "fs = 500.0\nt = np.arange(0, 5.0, 1/fs)\n# Three beats\nsignal = np.zeros_like(t)\nfor beat_time in [0.5, 1.5, 2.5, 3.5]:\n    qrs = 1.5 * np.exp(-((t - beat_time)**2) / (2 * 0.004**2))\n    tw = 0.4 * np.exp(-((t - beat_time - 0.25)**2) / (2 * 0.02**2))\n    signal += qrs + tw\nsignal += 0.02 * np.random.randn(len(t))"
        ),
        code(
            "results = measure_qt_intervals(signal, fs)\nfor m in results:\n    qt = f'{m.qt_ms:.1f} ms' if m.qt_ms else 'N/A'\n    rr = f'{m.rr_ms:.1f} ms' if m.rr_ms else 'N/A'\n    print(f'R={m.r_peak}, Q={m.q_onset}, T-end={m.t_end}, QT={qt}, RR={rr}')"
        ),
    ]
)

# ============================================================
# 07 — QTc Calculations
# ============================================================
notebooks["07_qtc_calculations.ipynb"] = nb(
    [
        md(
            "# 07 — QTc Calculations\n\nCompute all four QTc corrections simultaneously.\nDefault reporting formula: **Fridericia**."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np\nimport pandas as pd"),
        code("from ecg_analytics.qtc import compute_all_qtc, qtc_fridericia"),
        md("## Single-Value Computation"),
        code(
            "qt_ms = 400.0\nrr_ms = 800.0  # 75 bpm\nall_qtc = compute_all_qtc(qt_ms, rr_ms)\nfor name, val in all_qtc.items():\n    print(f'{name:>12s}: {float(val):.2f} ms')"
        ),
        md("## Vectorised (Per-Beat) Computation"),
        code(
            "qt_array = np.array([380, 390, 400, 410, 420], dtype=float)\nrr_array = np.array([900, 850, 800, 750, 700], dtype=float)\n\ndf = pd.DataFrame({'qt_ms': qt_array, 'rr_ms': rr_array})\nall_qtc = compute_all_qtc(df['qt_ms'], df['rr_ms'])\nfor name, vals in all_qtc.items():\n    df[f'qtc_{name}'] = vals\ndf"
        ),
        md("## Fridericia as Default"),
        code("print('Default (Fridericia):', qtc_fridericia(400, 800))"),
    ]
)

# ============================================================
# 08 — QTc Shift Tracking
# ============================================================
notebooks["08_qtc_shift_tracking.ipynb"] = nb(
    [
        md(
            "# 08 — Longitudinal QTc Shift Tracking\n\nTrack QTc changes from baseline across time points and flag\nclinically significant shifts (|ΔQTc| ≥ 60 ms)."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np\nimport pandas as pd"),
        code("from ecg_analytics.qtc import compute_qtc_shift, subject_drift_summary"),
        md("## Subject-Level Shift"),
        code(
            "result = compute_qtc_shift(\n    baseline_qtc_ms=420.0,\n    current_qtc_ms=490.0,\n    subject_id='SUBJ-001',\n    threshold_ms=60.0,\n)\nprint(result)"
        ),
        md("## Cohort-Level Drift Summary"),
        code(
            "np.random.seed(42)\nn_subjects, n_timepoints = 20, 5\nrows = []\nfor s in range(n_subjects):\n    bl = np.random.normal(420, 20)\n    for tp in range(n_timepoints):\n        qtc = bl + tp * np.random.normal(5, 10)\n        rows.append({'subject_id': f'S{s:03d}', 'time_point': tp, 'qtc_fridericia': qtc})\ndf = pd.DataFrame(rows)\n\nsummary = subject_drift_summary(df, baseline_time=0)\nsummary"
        ),
        code("# Flag subjects with significant drift\nsummary[summary['exceeds_threshold']]"),
    ]
)

# ============================================================
# 09 — LUDB Validation
# ============================================================
notebooks["09_ludb_validation.ipynb"] = nb(
    [
        md(
            "# 09 — LUDB Validation\n\nValidate T-wave delineation accuracy against LUDB expert annotations.\nLUDB provides detailed P/QRS/T boundaries on 200 twelve-lead records."
        ),
        code("import sys\nsys.path.insert(0, '../src')"),
        code(
            "from ecg_analytics.datasets import LUDBDataset\nfrom ecg_analytics.validation import delineation_metrics"
        ),
        md("## Load LUDB Data\n\n> Download first: `ludb.download()`"),
        code(
            "# ludb = LUDBDataset(data_dir='../data/physionet')\n# ludb.download()\n# records = ludb.list_records()\n# print(f'Available records: {len(records)}')"
        ),
        md("## Compute Delineation Metrics"),
        code(
            "import numpy as np\n# Example with synthetic ground truth\npredicted = np.array([100, 200, 300, 400])\nreference = np.array([102, 198, 305, 395])\n\nmetrics = delineation_metrics(predicted, reference, fs=250.0)\nfor k, v in metrics.items():\n    print(f'{k}: {v:.2f}')"
        ),
        md("## Publication Table"),
        code("import pandas as pd\npd.DataFrame([metrics], index=['T-end'])"),
    ]
)

# ============================================================
# 10 — Cross-Dataset Validation
# ============================================================
notebooks["10_cross_dataset_validation.ipynb"] = nb(
    [
        md(
            "# 10 — Cross-Dataset Validation\n\nCompare QT/QTc measurement accuracy across QTDB, LUDB, and CSE\ndatabases to assess generalizability."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code(
            "from ecg_analytics.validation import ValidationPipeline, qt_metrics, qtc_metrics\nfrom ecg_analytics.validation.reports import results_to_markdown"
        ),
        md("## Pipeline Setup"),
        code(
            "pipeline = ValidationPipeline()\n# For each dataset, load records, run pipeline.evaluate_record(), collect results\n# results = [pipeline.evaluate_record(rec, ref_qt, ref_qtc) for rec in records]"
        ),
        md("## Synthetic Cross-Dataset Comparison"),
        code(
            "datasets = ['QTDB', 'LUDB', 'CSE']\nnp.random.seed(42)\nrows = []\nfor ds in datasets:\n    pred = np.random.normal(400, 20, 50)\n    ref = pred + np.random.normal(0, 5, 50)\n    m = qt_metrics(pred, ref)\n    m['dataset'] = ds\n    rows.append(m)\n\nimport pandas as pd\npd.DataFrame(rows).set_index('dataset')"
        ),
    ]
)

# ============================================================
# 11 — Noise Robustness
# ============================================================
notebooks["11_noise_robustness.ipynb"] = nb(
    [
        md(
            "# 11 — Noise Robustness Evaluation\n\nEvaluate T-end and QT accuracy degradation under controlled noise\nconditions at SNR levels: 24, 18, 12, 6, 0 dB."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code(
            "from ecg_analytics.preprocessing.noise import NOISE_FUNCTIONS, STANDARD_SNR_LEVELS, inject_noise\nfrom ecg_analytics.visualization import plot_noise_comparison, plot_noise_degradation, plot_error_heatmap"
        ),
        md("## Noise Types"),
        code(
            "print('Noise types:', list(NOISE_FUNCTIONS.keys()))\nprint('SNR levels:', STANDARD_SNR_LEVELS)"
        ),
        md("## Visual Comparison"),
        code(
            "fs = 250.0\nt = np.arange(0, 5, 1/fs)\nclean = np.sin(2 * np.pi * 1.2 * t)\n\nfor noise_type in NOISE_FUNCTIONS:\n    noisy = inject_noise(clean, fs, noise_type, snr_db=12.0, rng=np.random.default_rng(42))\n    fig = plot_noise_comparison(clean, noisy, fs, noise_label=noise_type, snr_db=12.0)"
        ),
        md("## Degradation Curves"),
        code(
            "# Synthetic degradation data\nmae_values = {}\nfor noise_type in NOISE_FUNCTIONS:\n    mae_values[noise_type] = [2 + (24 - s) * 0.5 + np.random.rand() for s in STANDARD_SNR_LEVELS]\n\nfig = plot_noise_degradation(STANDARD_SNR_LEVELS, mae_values, metric_name='QT MAE (ms)')"
        ),
        md("## Error Heatmap"),
        code(
            "noise_types = list(NOISE_FUNCTIONS.keys())\nerrors = np.array([[mae_values[nt][i] for i in range(len(STANDARD_SNR_LEVELS))] for nt in noise_types])\nfig = plot_error_heatmap(noise_types, STANDARD_SNR_LEVELS, errors)"
        ),
    ]
)

# ============================================================
# 12 — Error Analysis
# ============================================================
notebooks["12_error_analysis.ipynb"] = nb(
    [
        md(
            "# 12 — Error Analysis\n\nDeep-dive into measurement errors: Bland-Altman plots, error\ndistributions, and outlier identification."
        ),
        code("import sys\nsys.path.insert(0, '../src')\nimport numpy as np"),
        code(
            "from ecg_analytics.validation import qt_metrics, qtc_metrics, delineation_metrics\nfrom ecg_analytics.visualization import plot_bland_altman, plot_error_distribution"
        ),
        md("## Bland-Altman Analysis"),
        code(
            "np.random.seed(42)\npredicted = np.random.normal(400, 20, 100)\nreference = predicted + np.random.normal(2, 8, 100)\n\nfig = plot_bland_altman(predicted, reference, title='QT Bland-Altman')"
        ),
        md("## Error Distribution"),
        code(
            "errors = predicted - reference\nfig = plot_error_distribution(errors, title='QT Error Distribution')"
        ),
        md("## Summary Metrics"),
        code(
            "metrics = qt_metrics(predicted, reference)\nimport pandas as pd\npd.DataFrame([metrics], index=['QT Measurement'])"
        ),
        md("## Outlier Identification"),
        code(
            "threshold = 2 * np.std(errors)\noutliers = np.where(np.abs(errors) > threshold)[0]\nprint(f'Outliers (>{threshold:.1f} ms): {len(outliers)} of {len(errors)} ({100*len(outliers)/len(errors):.1f}%)')"
        ),
    ]
)

# Write all notebooks
for name, content in notebooks.items():
    path = NB_DIR / name
    path.write_text(json.dumps(content, indent=1))
    print(f"  Created {name}")

print(f"\nDone — {len(notebooks)} notebooks generated.")

import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
notebooks_dir = root / 'notebooks'
artifacts_dir = root / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)

common_metadata = {
    'kernelspec': {'name': 'python3', 'display_name': 'Python 3'},
    'language_info': {'name': 'python', 'version': '3.12'},
}


def mk_md(source: str) -> dict:
    return {'cell_type': 'markdown', 'metadata': {}, 'source': [source]}


def mk_code(source: str) -> dict:
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': [source]}


def write_notebook(name: str, cells: list[dict]) -> None:
    path = notebooks_dir / name
    notebook = {
        'cells': cells,
        'metadata': common_metadata,
        'nbformat': 4,
        'nbformat_minor': 5,
    }
    path.write_text(json.dumps(notebook, indent=2))
    print(f'Wrote {path}')


if __name__ == '__main__':
    notebooks = []

    notebooks.append(
        (
            '01_dataset_audit.ipynb',
            [
                mk_md(
                    'Notebook: 01_dataset_audit.ipynb\n\nPurpose: Inventory datasets and export standardized record metadata.\n\nInputs:\n- raw dataset files in data/*\n\nOutputs:\n- inventory.csv\n- clinical_context.parquet\n\nNotes:\n- Must produce record-level metadata exact to DATA_CONTRACT.md.'
                ),
                mk_md(
                    '# 01 — Dataset Audit and Inventory\n\nCollect dataset metadata, verify sampling information, and export a canonical record inventory for downstream evidence pipelines.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.datasets import PTBXLDataset, LUDBDataset, NSTDBDataset, INCARTDataset, QTDBDataset

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)
data_dir = root_dir / 'data'

adapters = {
    'ptbxl': PTBXLDataset,
    'ludb': LUDBDataset,
    'nstdb': NSTDBDataset,
    'incart': INCARTDataset,
    'qtdb': QTDBDataset,
}

inventory_rows = []
clinical_rows = []

for dataset_name, adapter_cls in adapters.items():
    dataset_path = data_dir / dataset_name
    if not dataset_path.exists():
        continue
    adapter = adapter_cls(data_dir=data_dir)
    try:
        record_names = adapter.list_records()
    except Exception as exc:
        print(f'Warning: {dataset_name} listing failed: {exc}')
        continue

    for record_name in record_names:
        try:
            record = adapter.load_record(record_name)
        except Exception as exc:
            print(f'Warning: failed loading {dataset_name}/{record_name}: {exc}')
            continue

        record_id = f'{dataset_name}/{record_name}'
        lead_names = [str(name).lower() for name in getattr(record, 'lead_names', [])] if getattr(record, 'lead_names', None) else []
        sampling_rate = float(getattr(record, 'fs', np.nan))
        duration_seconds = float(getattr(record, 'duration_s', np.nan))
        time_resolution_ms = float(1000.0 / sampling_rate) if sampling_rate and sampling_rate > 0 else np.nan
        annotations = getattr(record, 'annotations', []) or []
        annotation_source = 'manual' if annotations else 'none'
        has_manual_t_end = any(
            getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() in {'t', ')'}
            or getattr(getattr(ann, 'label', None), 'lower', lambda: '')().startswith('t-end')
            for ann in annotations
        )

        inventory_rows.append({
            'record_id': record_id,
            'dataset_name': dataset_name,
            'sampling_rate': sampling_rate,
            'time_resolution_ms': time_resolution_ms,
            'duration_seconds': duration_seconds,
            'num_leads': int(getattr(record, 'n_leads', len(lead_names))),
            'lead_names': lead_names,
            'annotation_source': annotation_source,
            'has_manual_t_end': bool(has_manual_t_end),
        })
        clinical_rows.append({
            'record_id': record_id,
            'arrhythmia_flag': bool(dataset_name == 'incart'),
            'diagnostic_class': record.metadata.get('diagnostic_class', np.nan) if getattr(record, 'metadata', None) else np.nan,
            'dataset_origin': dataset_name,
        })

inventory = pd.DataFrame(inventory_rows)
clinical_context = pd.DataFrame(clinical_rows)
expected_inventory = {
    'record_id', 'dataset_name', 'sampling_rate', 'time_resolution_ms',
    'duration_seconds', 'num_leads', 'lead_names', 'annotation_source',
    'has_manual_t_end',
}
assert expected_inventory.issubset(set(inventory.columns)), 'inventory missing required columns'
assert inventory['record_id'].is_unique, 'record_id must be unique'
expected_clinical = {'record_id', 'arrhythmia_flag', 'diagnostic_class', 'dataset_origin'}
assert expected_clinical.issubset(set(clinical_context.columns)), 'clinical_context missing required columns'

inventory.to_csv(artifacts_dir / 'inventory.csv', index=False)
clinical_context.to_parquet(artifacts_dir / 'clinical_context.parquet', index=False)
print('Wrote inventory and clinical_context artifacts')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '02_signal_quality.ipynb',
            [
                mk_md(
                    'Notebook: 02_signal_quality.ipynb\n\nPurpose: Generate lead-level signal quality evidence using raw ECG waveforms only.\n\nInputs:\n- raw ECG waveforms\n- sampling rate\n\nOutputs:\n- signal_quality_features.parquet\n\nForbidden upstream evidence: delineation, QT measurement, confidence targets.'
                ),
                mk_md(
                    '# 02 — Signal Quality Evidence\n\nCompute canonical signal quality metrics at the record+lead level without using delineation or measurement evidence.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import signal
from scipy.fft import rfft, rfftfreq
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.datasets import PTBXLDataset, LUDBDataset, NSTDBDataset, INCARTDataset, QTDBDataset

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)
data_dir = root_dir / 'data'

adapters = {
    'ptbxl': PTBXLDataset,
    'ludb': LUDBDataset,
    'nstdb': NSTDBDataset,
    'incart': INCARTDataset,
    'qtdb': QTDBDataset,
}

rows = []

for dataset_name, adapter_cls in adapters.items():
    dataset_path = data_dir / dataset_name
    if not dataset_path.exists():
        continue
    adapter = adapter_cls(data_dir=data_dir)
    try:
        record_names = adapter.list_records()
    except Exception:
        continue

    for record_name in record_names:
        try:
            record = adapter.load_record(record_name)
        except Exception:
            continue

        record_id = f'{dataset_name}/{record_name}'
        signal = np.asarray(record.signal, dtype=float)
        if signal.ndim == 1:
            signal = signal.reshape(-1, 1)
        fs = float(getattr(record, 'fs', np.nan))
        lead_names = getattr(record, 'lead_names', []) or []

        for lead_index, lead_name in enumerate(lead_names):
            lead_signal = signal[:, lead_index] if signal.shape[1] > lead_index else signal[:, 0]
            freq = rfftfreq(lead_signal.size, 1.0 / fs)
            spectrum = np.abs(rfft(lead_signal))
            band = (freq >= 40) & (freq <= 100)
            hfn_value = float(np.sum(spectrum[band]) / (np.sum(spectrum) + 1e-12)) if np.any(band) else 0.0
            powerline = 0.0
            for target in (50.0, 60.0):
                idx = int(np.argmin(np.abs(freq - target)))
                powerline += spectrum[idx] ** 2
            pli_value = float(powerline / (np.sum(spectrum ** 2) + 1e-12))
            clipped = np.abs(lead_signal - np.clip(lead_signal, np.percentile(lead_signal, 0.5), np.percentile(lead_signal, 99.5))) < 1e-6
            clipping_value = float(np.mean(clipped))
            flat_ratio = float(np.mean(np.abs(np.diff(lead_signal)) < max(1e-6, 0.01 * np.std(lead_signal)))) if lead_signal.size > 1 else 0.0
            rows.append({
                'record_id': record_id,
                'lead_id': str(lead_name).lower(),
                'bw_index': float(np.nan),
                'hfn_index': hfn_value,
                'pli_index': pli_value,
                'clipping_ratio': clipping_value,
                'flatline_ratio': flat_ratio,
                'signal_quality_score': float(np.clip(1.0 - hfn_value - pli_value - clipping_value, 0.0, 1.0)),
            })

signal_quality = pd.DataFrame(rows)
if not signal_quality.empty:
    signal_quality = signal_quality[['record_id','lead_id','bw_index','hfn_index','pli_index','clipping_ratio','flatline_ratio','signal_quality_score']]
    assert signal_quality[['record_id','lead_id']].duplicated().sum() == 0
    assert signal_quality['signal_quality_score'].between(0.0, 1.0).all()

signal_quality.to_parquet(artifacts_dir / 'signal_quality_features.parquet', index=False)
print('Wrote signal_quality_features.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '03_delineation_validation.ipynb',
            [
                mk_md(
                    'Notebook: 03_delineation_validation.ipynb\n\nPurpose: Quantify boundary uncertainty using available annotations and raw ECG waveforms.\n\nInputs:\n- raw ECG waveforms\n- delineation annotations\n\nOutputs:\n- delineation_features.parquet'
                ),
                mk_md(
                    '# 03 — Delineation Validation\n\nEstimate lead-level uncertainty for waveform fiducial boundaries and derive a boundary confidence score.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.datasets import PTBXLDataset, LUDBDataset, NSTDBDataset, INCARTDataset, QTDBDataset

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)
data_dir = root_dir / 'data'

adapters = {
    'ptbxl': PTBXLDataset,
    'ludb': LUDBDataset,
    'nstdb': NSTDBDataset,
    'incart': INCARTDataset,
    'qtdb': QTDBDataset,
}

rows = []

for dataset_name, adapter_cls in adapters.items():
    dataset_path = data_dir / dataset_name
    if not dataset_path.exists():
        continue
    adapter = adapter_cls(data_dir=data_dir)
    try:
        record_names = adapter.list_records()
    except Exception:
        continue

    for record_name in record_names:
        try:
            record = adapter.load_record(record_name)
        except Exception:
            continue

        record_id = f'{dataset_name}/{record_name}'
        signal = np.asarray(record.signal, dtype=float)
        if signal.ndim == 1:
            signal = signal.reshape(-1, 1)
        annotations = getattr(record, 'annotations', []) or []
        lead_names = getattr(record, 'lead_names', []) or []

        for lead_index, lead_name in enumerate(lead_names):
            lead_signal = signal[:, lead_index] if signal.shape[1] > lead_index else signal[:, 0]
            lead_annotations = [ann for ann in annotations if getattr(ann, 'lead', None) == lead_index]
            samples = [getattr(ann, 'sample', None) for ann in lead_annotations if getattr(ann, 'sample', None) is not None]
            window = int(max(1, 0.04 * float(getattr(record, 'fs', np.nan))))
            def sample_uncertainty(sample_list):
                values = []
                for sample in sample_list:
                    if sample is None or sample < 0 or sample >= lead_signal.size:
                        continue
                    left = max(0, sample - window)
                    right = min(lead_signal.size, sample + window)
                    segment = lead_signal[left:right]
                    if segment.size < 2:
                        continue
                    values.append(float(np.mean(np.abs(np.diff(segment)))))
                if not values:
                    return np.nan
                return float(np.std(values) / (np.mean(values) + 1e-12) * 1000.0)

            p_onsets = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() in {'(', 'p'}]
            p_offsets = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == ')' and getattr(getattr(ann, 'label', None), 'lower', lambda: '')().startswith('p')]
            qrs_onsets = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == 'n']
            qrs_offsets = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == ')']
            t_onsets = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() in {'(', 't'} and getattr(getattr(ann, 'label', None), 'lower', lambda: '')().startswith('t')]
            t_ends = [ann.sample for ann in lead_annotations if getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == ')']

            p_onset_unc = sample_uncertainty(p_onsets)
            p_offset_unc = sample_uncertainty(p_offsets)
            qrs_onset_unc = sample_uncertainty(qrs_onsets)
            qrs_offset_unc = sample_uncertainty(qrs_offsets)
            t_onset_unc = sample_uncertainty(t_onsets)
            t_end_unc = sample_uncertainty(t_ends)
            boundary_confidence = float(np.clip(1.0 - np.nanmean([p_onset_unc, p_offset_unc, qrs_onset_unc, qrs_offset_unc, t_onset_unc, t_end_unc]) / 100.0, 0.0, 1.0))

            rows.append({
                'record_id': record_id,
                'lead_id': str(lead_name).lower(),
                'p_onset_uncertainty_ms': p_onset_unc,
                'p_offset_uncertainty_ms': p_offset_unc,
                'qrs_onset_uncertainty_ms': qrs_onset_unc,
                'qrs_offset_uncertainty_ms': qrs_offset_unc,
                't_onset_uncertainty_ms': t_onset_unc,
                't_end_uncertainty_ms': t_end_unc,
                'boundary_confidence': boundary_confidence,
            })

if rows:
    delineation = pd.DataFrame(rows)
else:
    delineation = pd.DataFrame(columns=[
        'record_id','lead_id','p_onset_uncertainty_ms','p_offset_uncertainty_ms',
        'qrs_onset_uncertainty_ms','qrs_offset_uncertainty_ms','t_onset_uncertainty_ms',
        't_end_uncertainty_ms','boundary_confidence',
    ])

expected = {'record_id','lead_id','p_onset_uncertainty_ms','p_offset_uncertainty_ms','qrs_onset_uncertainty_ms','qrs_offset_uncertainty_ms','t_onset_uncertainty_ms','t_end_uncertainty_ms','boundary_confidence'}
assert expected.issubset(set(delineation.columns)), 'delineation feature schema mismatch'
assert delineation[['record_id','lead_id']].duplicated().sum() == 0

delineation.to_parquet(artifacts_dir / 'delineation_features.parquet', index=False)
print('Wrote delineation_features.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '04_twave_analysis.ipynb',
            [
                mk_md(
                    'Notebook: 04_twave_analysis.ipynb\n\nPurpose: Characterize beat-level T-wave morphology and ambiguity.\n\nInputs:\n- raw ECG waveforms\n- delineated T-wave boundaries\n\nOutputs:\n- twave_features.parquet'
                ),
                mk_md(
                    '# 04 — T-Wave Morphology Analysis\n\nExtract beat-level T-wave metrics that capture amplitude, width, slope, symmetry, and ambiguity.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.datasets import PTBXLDataset, LUDBDataset, NSTDBDataset, INCARTDataset, QTDBDataset

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)
data_dir = root_dir / 'data'

adapters = {
    'ptbxl': PTBXLDataset,
    'ludb': LUDBDataset,
    'nstdb': NSTDBDataset,
    'incart': INCARTDataset,
    'qtdb': QTDBDataset,
}

rows = []

for dataset_name, adapter_cls in adapters.items():
    dataset_path = data_dir / dataset_name
    if not dataset_path.exists():
        continue
    adapter = adapter_cls(data_dir=data_dir)
    try:
        record_names = adapter.list_records()
    except Exception:
        continue

    for record_name in record_names:
        try:
            record = adapter.load_record(record_name)
        except Exception:
            continue

        record_id = f'{dataset_name}/{record_name}'
        signal = np.asarray(record.signal, dtype=float)
        if signal.ndim == 1:
            signal = signal.reshape(-1, 1)
        annotations = getattr(record, 'annotations', []) or []
        lead_names = getattr(record, 'lead_names', []) or []

        for lead_index, lead_name in enumerate(lead_names):
            lead_signal = signal[:, lead_index] if signal.shape[1] > lead_index else signal[:, 0]
            t_points = [ann.sample for ann in annotations if getattr(ann, 'lead', None) == lead_index and getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == 't']
            t_starts = [ann.sample for ann in annotations if getattr(ann, 'lead', None) == lead_index and getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() in {'(',} and 't' in getattr(getattr(ann, 'label', None), 'lower', lambda: '')()]
            t_ends = [ann.sample for ann in annotations if getattr(ann, 'lead', None) == lead_index and getattr(getattr(ann, 'symbol', None), 'lower', lambda: '')() == ')']
            beat_count = min(len(t_starts), len(t_points), len(t_ends))
            for beat_idx in range(beat_count):
                start = t_starts[beat_idx]
                peak = t_points[beat_idx]
                end = t_ends[beat_idx]
                segment = lead_signal[start:end] if end > start else np.array([])
                if segment.size < 2:
                    amplitude = np.nan
                    width = np.nan
                    slope = np.nan
                    symmetry = np.nan
                    biphasic = False
                    flattened = False
                    cluster = 'unknown'
                    ambiguity = np.nan
                    confidence = np.nan
                else:
                    amplitude = float(np.max(segment) - np.min(segment))
                    width = float((end - start) / float(getattr(record, 'fs', np.nan)) * 1000.0)
                    slope = float(np.nanmax(np.abs(np.diff(segment))) * float(getattr(record, 'fs', np.nan)))
                    rising = float(peak - start)
                    falling = float(end - peak) if end > peak else 1.0
                    symmetry = float(rising / falling) if falling > 0 else np.nan
                    biphasic = bool(np.any(segment < 0) and np.any(segment > 0))
                    flattened = bool(np.ptp(segment) < 0.1 * np.nanstd(lead_signal)) if np.nanstd(lead_signal) > 0 else False
                    cluster = 'biphasic' if biphasic else 'flattened' if flattened else 'monophasic'
                    ambiguity = float(np.std(segment) / (np.max(np.abs(segment)) + 1e-12))
                    confidence = float(np.clip(1.0 - ambiguity, 0.0, 1.0))

                rows.append({
                    'record_id': record_id,
                    'lead_id': str(lead_name).lower(),
                    'beat_id': int(beat_idx + 1),
                    't_amplitude_mv': amplitude,
                    't_width_ms': width,
                    't_slope': slope,
                    't_symmetry': symmetry,
                    'biphasic_flag': bool(biphasic),
                    'flattened_flag': bool(flattened),
                    'morphology_cluster': cluster,
                    't_end_ambiguity_score': ambiguity,
                    'morphology_confidence': confidence,
                })

if rows:
    twave = pd.DataFrame(rows)
else:
    twave = pd.DataFrame(columns=[
        'record_id','lead_id','beat_id','t_amplitude_mv','t_width_ms','t_slope','t_symmetry',
        'biphasic_flag','flattened_flag','morphology_cluster','t_end_ambiguity_score','morphology_confidence',
    ])

expected = {
    'record_id','lead_id','beat_id','t_amplitude_mv','t_width_ms','t_slope','t_symmetry',
    'biphasic_flag','flattened_flag','morphology_cluster','t_end_ambiguity_score','morphology_confidence',
}
assert expected.issubset(set(twave.columns)), 'twave schema mismatch'
assert twave[['record_id','lead_id','beat_id']].duplicated().sum() == 0

twave.to_parquet(artifacts_dir / 'twave_features.parquet', index=False)
print('Wrote twave_features.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '05_qt_measurement.ipynb',
            [
                mk_md(
                    'Notebook: 05_qt_measurement.ipynb\n\nPurpose: Generate beat-level QT measurements and reliability evidence from raw ECG signals.\n\nInputs:\n- raw ECG waveforms\n\nOutputs:\n- qt_measurements.parquet\n- measurement_reliability.parquet\n\nForbidden inputs: signal quality evidence from 02_signal_quality.ipynb.'
                ),
                mk_md(
                    '# 05 — QT Measurement Reliability\n\nCompute QT intervals every beat and derive reliability metrics based on multi-lead agreement and repeatability.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.datasets import PTBXLDataset, LUDBDataset, NSTDBDataset, INCARTDataset, QTDBDataset
from ecg_analytics.qt.measurement import measure_qt_intervals

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
artifacts_dir.mkdir(exist_ok=True)
data_dir = root_dir / 'data'

adapters = {
    'ptbxl': PTBXLDataset,
    'ludb': LUDBDataset,
    'nstdb': NSTDBDataset,
    'incart': INCARTDataset,
    'qtdb': QTDBDataset,
}

rows = []

for dataset_name, adapter_cls in adapters.items():
    dataset_path = data_dir / dataset_name
    if not dataset_path.exists():
        continue
    adapter = adapter_cls(data_dir=data_dir)
    try:
        record_names = adapter.list_records()
    except Exception:
        continue

    for record_name in record_names:
        try:
            record = adapter.load_record(record_name)
        except Exception:
            continue

        record_id = f'{dataset_name}/{record_name}'
        signal = np.asarray(record.signal, dtype=float)
        if signal.ndim == 1:
            signal = signal.reshape(-1, 1)
        lead_names = getattr(record, 'lead_names', []) or []
        fs = float(getattr(record, 'fs', np.nan))

        for lead_index, lead_name in enumerate(lead_names):
            lead_signal = signal[:, lead_index] if signal.shape[1] > lead_index else signal[:, 0]
            measurements = measure_qt_intervals(lead_signal, fs)
            for beat_idx, m in enumerate(measurements, start=1):
                rows.append({
                    'record_id': record_id,
                    'lead_id': str(lead_name).lower(),
                    'beat_id': beat_idx,
                    'qt_ms': float(m.qt_ms) if getattr(m, 'qt_ms', None) is not None else np.nan,
                    'qrs_onset_sample': int(m.q_onset) if getattr(m, 'q_onset', None) is not None else np.nan,
                    't_end_sample': int(m.t_end) if getattr(m, 't_end', None) is not None else np.nan,
                    'measurement_valid': bool(getattr(m, 'qt_ms', None) is not None),
                    'rr_ms': float(m.rr_ms) if getattr(m, 'rr_ms', None) is not None else np.nan,
                })

qt_df = pd.DataFrame(rows)
if qt_df.empty:
    qt_df = pd.DataFrame(columns=[
        'record_id','lead_id','beat_id','qt_ms','qrs_onset_sample','t_end_sample','measurement_valid','rr_ms',
    ])
qt_df['qt_ms'] = pd.to_numeric(qt_df['qt_ms'], errors='coerce')
qt_df['rr_ms'] = pd.to_numeric(qt_df['rr_ms'], errors='coerce')
qt_df['measurement_valid'] = qt_df['measurement_valid'].astype(bool)
qt_measurements = qt_df[['record_id','lead_id','beat_id','qt_ms','qrs_onset_sample','t_end_sample','measurement_valid']].copy()

if not qt_df.empty:
    grouped = qt_df.groupby(['record_id','beat_id'])
    median_qt = grouped['qt_ms'].transform('median')
    mean_qt = grouped['qt_ms'].transform('mean')
    qt_df['qt_variance_leads'] = grouped['qt_ms'].transform('var').fillna(0.0)
    qt_df['qt_variance_beats'] = qt_df.groupby(['record_id','lead_id'])['qt_ms'].transform('var').fillna(0.0)
    qt_df['lead_agreement_score'] = (1.0 - np.clip(np.abs(qt_df['qt_ms'] - median_qt) / (median_qt + 1e-6), 0.0, 1.0)).fillna(0.0)
    qt_df['beat_agreement_score'] = (1.0 - np.clip(np.abs(qt_df['qt_ms'] - mean_qt) / (mean_qt + 1e-6), 0.0, 1.0)).fillna(0.0)
    lead_count = qt_df.groupby(['record_id','beat_id'])['lead_id'].transform('nunique').fillna(1.0)
    qt_df['missing_lead_penalty'] = 1.0 - np.clip((12.0 - lead_count) / 12.0, 0.0, 1.0)
    repeatability = qt_df.groupby(['record_id','lead_id'])['qt_ms'].transform('std').fillna(0.0)
    qt_df['repeatability_score'] = (1.0 - np.clip(repeatability / (qt_df['qt_ms'].abs() + 1e-6), 0.0, 1.0)).fillna(0.0)
    qt_df['bsqi'] = (0.5 + 0.5 * (1.0 - np.clip(np.abs(qt_df['qt_ms'] - median_qt) / 150.0, 0.0, 1.0))).fillna(0.0)
    qt_df['wsqi'] = (0.5 + 0.5 * (1.0 - np.clip(np.abs(qt_df['qt_ms'] - mean_qt) / 150.0, 0.0, 1.0))).fillna(0.0)
    qt_df['internal_consistency_score'] = qt_df[['bsqi','wsqi','lead_agreement_score','beat_agreement_score','repeatability_score']].mean(axis=1)
    reliability_df = qt_df[['record_id','lead_id','beat_id','bsqi','wsqi','lead_agreement_score','beat_agreement_score','qt_variance_leads','qt_variance_beats','missing_lead_penalty','repeatability_score','internal_consistency_score']].copy()
else:
    reliability_df = pd.DataFrame(columns=[
        'record_id','lead_id','beat_id','bsqi','wsqi','lead_agreement_score','beat_agreement_score','qt_variance_leads','qt_variance_beats','missing_lead_penalty','repeatability_score','internal_consistency_score',
    ])

assert set(qt_measurements.columns) >= {'record_id','lead_id','beat_id','qt_ms','qrs_onset_sample','t_end_sample','measurement_valid'}
assert set(reliability_df.columns) >= {'record_id','lead_id','beat_id','bsqi','wsqi','lead_agreement_score','beat_agreement_score','qt_variance_leads','qt_variance_beats','missing_lead_penalty','repeatability_score','internal_consistency_score'}
assert qt_measurements[['record_id','lead_id','beat_id']].duplicated().sum() == 0
assert reliability_df[['record_id','lead_id','beat_id']].duplicated().sum() == 0

qt_measurements.to_parquet(artifacts_dir / 'qt_measurements.parquet', index=False)
reliability_df.to_parquet(artifacts_dir / 'measurement_reliability.parquet', index=False)
print('Wrote qt_measurements.parquet and measurement_reliability.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '06_qtc_methods.ipynb',
            [
                mk_md(
                    'Notebook: 06_qtc_methods.ipynb\n\nPurpose: Calculate standard QTc formulas at the beat level.\n\nInputs:\n- qt_measurements.parquet\n\nOutputs:\n- qtc_comparison.parquet'
                ),
                mk_md(
                    '# 06 — QTc Calculations\n\nCompute Fridericia, Bazett, Framingham, and Hodges corrections for each beat and summarize formula spread.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))
from ecg_analytics.qtc.formulas import compute_all_qtc

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
qt_path = artifacts_dir / 'qt_measurements.parquet'
qt_df = pd.read_parquet(qt_path)
qt_df['qt_ms'] = pd.to_numeric(qt_df['qt_ms'], errors='coerce')
qt_df['rr_ms'] = pd.to_numeric(qt_df['rr_ms'], errors='coerce')

records = []
for (record_id, beat_id), subset in qt_df.groupby(['record_id','beat_id']):
    valid = subset.dropna(subset=['qt_ms','rr_ms'])
    if valid.empty:
        continue
    qt_ms = float(valid['qt_ms'].mean())
    rr_ms = float(valid['rr_ms'].mean())
    qtc = compute_all_qtc(qt_ms, rr_ms)
    qtc_values = np.array([qtc['fridericia'], qtc['bazett'], qtc['framingham'], qtc['hodges']], dtype=float)
    records.append({
        'record_id': record_id,
        'beat_id': int(beat_id),
        'rr_ms': rr_ms,
        'qtc_bazett': float(qtc['bazett']),
        'qtc_fridericia': float(qtc['fridericia']),
        'qtc_framingham': float(qtc['framingham']),
        'qtc_hodges': float(qtc['hodges']),
        'qtc_formula_variance': float(np.nanvar(qtc_values)),
        'qtc_formula_bias': float(np.nanmax(qtc_values) - np.nanmin(qtc_values)),
    })

qtc_comparison = pd.DataFrame(records)
expected = {'record_id','beat_id','rr_ms','qtc_bazett','qtc_fridericia','qtc_framingham','qtc_hodges','qtc_formula_variance','qtc_formula_bias'}
assert expected.issubset(set(qtc_comparison.columns)), 'qtc_comparison schema mismatch'
assert qtc_comparison[['record_id','beat_id']].duplicated().sum() == 0

qtc_comparison.to_parquet(artifacts_dir / 'qtc_comparison.parquet', index=False)
print('Wrote qtc_comparison.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '07_cross_dataset_validation.ipynb',
            [
                mk_md(
                    'Notebook: 07_cross_dataset_validation.ipynb\n\nPurpose: Evaluate dataset-level shift and confidence stability evidence.\n\nInputs:\n- signal_quality_features.parquet\n- twave_features.parquet\n- measurement_reliability.parquet\n- qtc_comparison.parquet\n\nOutputs:\n- cross_dataset_results.parquet'
                ),
                mk_md(
                    '# 07 — Cross-Dataset Validation\n\nCompare dataset distributions and stability across evidence domains at dataset granularity.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import entropy
sys.path.insert(0, str(Path.cwd().parent / 'src'))

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
paths = {
    'signal_quality': artifacts_dir / 'signal_quality_features.parquet',
    'twave': artifacts_dir / 'twave_features.parquet',
    'measurement': artifacts_dir / 'measurement_reliability.parquet',
    'qtc': artifacts_dir / 'qtc_comparison.parquet',
}
frames = {k: pd.read_parquet(p) if p.exists() else pd.DataFrame() for k, p in paths.items()}

for key, df in frames.items():
    if 'record_id' in df.columns:
        df['dataset_name'] = df['record_id'].astype(str).str.split('/', 1).str[0]
        frames[key] = df

all_datasets = set()
for df in frames.values():
    if 'dataset_name' in df.columns:
        all_datasets.update(df['dataset_name'].unique())

results = []
for dataset_name in sorted(all_datasets):
    row = {'dataset_name': dataset_name}
    lead_shift = 0.0
    morphology_shift = 0.0
    qtc_std = 0.0

    if not frames['signal_quality'].empty:
        sq = frames['signal_quality']
        group = sq[sq['dataset_name'] == dataset_name]
        if not group.empty:
            counts = group['lead_id'].value_counts(normalize=True)
            global_counts = sq['lead_id'].value_counts(normalize=True)
            lead_shift = float(entropy(counts + 1e-12, global_counts.reindex(counts.index, fill_value=1e-12).values))

    if not frames['twave'].empty:
        tw = frames['twave']
        group = tw[tw['dataset_name'] == dataset_name]
        if not group.empty:
            counts = group['morphology_cluster'].value_counts(normalize=True)
            global_counts = tw['morphology_cluster'].value_counts(normalize=True)
            morphology_shift = float(entropy(counts + 1e-12, global_counts.reindex(counts.index, fill_value=1e-12).values))

    if not frames['qtc'].empty:
        qc = frames['qtc']
        group = qc[qc['dataset_name'] == dataset_name]
        if not group.empty and 'qtc_fridericia' in group.columns:
            qtc_std = float(np.nanstd(group['qtc_fridericia'].dropna()))

    row['shift_score'] = float(np.nanmean([lead_shift, morphology_shift, qtc_std]))
    row['lead_distribution_shift'] = lead_shift
    row['morphology_shift'] = morphology_shift
    row['confidence_stability_score'] = float(1.0 / (1.0 + qtc_std)) if qtc_std >= 0 else 0.0
    results.append(row)

cross_df = pd.DataFrame(results)
expected = {'dataset_name','shift_score','lead_distribution_shift','morphology_shift','confidence_stability_score'}
assert expected.issubset(set(cross_df.columns)), 'cross dataset result schema mismatch'
assert cross_df['dataset_name'].is_unique

cross_df.to_parquet(artifacts_dir / 'cross_dataset_results.parquet', index=False)
print('Wrote cross_dataset_results.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '08_failure_modes.ipynb',
            [
                mk_md(
                    'Notebook: 08_failure_modes.ipynb\n\nPurpose: Identify systematic failure modes that impact confidence.\n\nInputs:\n- signal_quality_features.parquet\n- delineation_features.parquet\n- twave_features.parquet\n- measurement_reliability.parquet\n\nOutputs:\n- failure_modes.parquet'
                ),
                mk_md(
                    '# 08 — Failure Modes\n\nDetect record-level failure categories using multi-domain artifact evidence.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
frames = {
    'signal_quality': pd.read_parquet(artifacts_dir / 'signal_quality_features.parquet') if (artifacts_dir / 'signal_quality_features.parquet').exists() else pd.DataFrame(),
    'delineation': pd.read_parquet(artifacts_dir / 'delineation_features.parquet') if (artifacts_dir / 'delineation_features.parquet').exists() else pd.DataFrame(),
    'twave': pd.read_parquet(artifacts_dir / 'twave_features.parquet') if (artifacts_dir / 'twave_features.parquet').exists() else pd.DataFrame(),
    'measurement': pd.read_parquet(artifacts_dir / 'measurement_reliability.parquet') if (artifacts_dir / 'measurement_reliability.parquet').exists() else pd.DataFrame(),
}

record_ids = set()
for df in frames.values():
    if 'record_id' in df.columns:
        record_ids.update(df['record_id'].astype(str).unique())

rows = []
for record_id in sorted(record_ids):
    sq = frames['signal_quality']
    de = frames['delineation']
    tw = frames['twave']
    mr = frames['measurement']

    sq_rec = sq[sq['record_id'] == record_id] if not sq.empty else pd.DataFrame()
    de_rec = de[de['record_id'] == record_id] if not de.empty else pd.DataFrame()
    tw_rec = tw[tw['record_id'] == record_id] if not tw.empty else pd.DataFrame()
    mr_rec = mr[mr['record_id'] == record_id] if not mr.empty else pd.DataFrame()

    failure_type = 'arrhythmia'
    score = 0.2
    confidence_impact = 0.8

    if not sq_rec.empty and sq_rec['signal_quality_score'].mean() < 0.5:
        failure_type = 'bw'
        score = float(1.0 - sq_rec['signal_quality_score'].mean())
        confidence_impact = score
    elif not sq_rec.empty and sq_rec['hfn_index'].mean() > 0.15:
        failure_type = 'hfn'
        score = float(sq_rec['hfn_index'].mean())
        confidence_impact = 0.6
    elif not sq_rec.empty and sq_rec['pli_index'].mean() > 0.03:
        failure_type = 'pli'
        score = float(sq_rec['pli_index'].mean())
        confidence_impact = 0.6
    elif not sq_rec.empty and 'electrode_motion_index' in sq_rec.columns and sq_rec['electrode_motion_index'].mean() > 0.4:
        failure_type = 'em'
        score = float(sq_rec['electrode_motion_index'].mean())
        confidence_impact = 0.6
    elif not tw_rec.empty and 't_end_ambiguity_score' in tw_rec.columns and tw_rec['t_end_ambiguity_score'].mean() > 0.4:
        failure_type = 'twave_ambiguity'
        score = float(tw_rec['t_end_ambiguity_score'].mean())
        confidence_impact = float(1.0 - tw_rec['t_end_ambiguity_score'].mean())
    elif not mr_rec.empty and mr_rec['lead_agreement_score'].mean() < 0.7:
        failure_type = 'lead_disagreement'
        score = float(1.0 - mr_rec['lead_agreement_score'].mean())
        confidence_impact = score
    elif not de_rec.empty and de_rec['boundary_confidence'].mean() < 0.7:
        failure_type = 'delineation_failure'
        score = float(1.0 - de_rec['boundary_confidence'].mean())
        confidence_impact = score

    rows.append({
        'record_id': record_id,
        'failure_type': failure_type,
        'failure_score': score,
        'confidence_impact': confidence_impact,
        'root_cause_rank': 1,
    })

failure_df = pd.DataFrame(rows)
expected = {'record_id','failure_type','failure_score','confidence_impact','root_cause_rank'}
assert expected.issubset(set(failure_df.columns)), 'failure modes schema mismatch'
assert failure_df['record_id'].is_unique

failure_df.to_parquet(artifacts_dir / 'failure_modes.parquet', index=False)
print('Wrote failure_modes.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '09_confidence_features.ipynb',
            [
                mk_md(
                    'Notebook: 09_confidence_features.ipynb\n\nPurpose: Assemble record-level confidence evidence from all permitted domains.\n\nInputs:\n- signal_quality_features.parquet\n- delineation_features.parquet\n- twave_features.parquet\n- measurement_reliability.parquet\n- clinical_context.parquet\n\nOutputs:\n- confidence_features.parquet'
                ),
                mk_md(
                    '# 09 — Confidence Feature Assembly\n\nAggregate lead- and beat-level evidence into the master record-level feature table for confidence modeling.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
frames = {
    'signal_quality': pd.read_parquet(artifacts_dir / 'signal_quality_features.parquet') if (artifacts_dir / 'signal_quality_features.parquet').exists() else pd.DataFrame(),
    'delineation': pd.read_parquet(artifacts_dir / 'delineation_features.parquet') if (artifacts_dir / 'delineation_features.parquet').exists() else pd.DataFrame(),
    'twave': pd.read_parquet(artifacts_dir / 'twave_features.parquet') if (artifacts_dir / 'twave_features.parquet').exists() else pd.DataFrame(),
    'measurement': pd.read_parquet(artifacts_dir / 'measurement_reliability.parquet') if (artifacts_dir / 'measurement_reliability.parquet').exists() else pd.DataFrame(),
    'clinical': pd.read_parquet(artifacts_dir / 'clinical_context.parquet') if (artifacts_dir / 'clinical_context.parquet').exists() else pd.DataFrame(),
}


def aggregations(series):
    if series.empty:
        return dict(mean=np.nan, std=np.nan, max=np.nan, p95=np.nan)
    values = pd.to_numeric(series.dropna(), errors='coerce')
    if values.empty:
        return dict(mean=np.nan, std=np.nan, max=np.nan, p95=np.nan)
    return dict(mean=float(values.mean()), std=float(values.std()), max=float(values.max()), p95=float(np.nanpercentile(values, 95)))

all_record_ids = set()
for df in frames.values():
    if 'record_id' in df.columns:
        all_record_ids.update(df['record_id'].astype(str).unique())

rows = []
for record_id in sorted(all_record_ids):
    row = {'record_id': record_id}
    clinical = frames['clinical']
    if not clinical.empty:
        rec = clinical[clinical['record_id'] == record_id]
        if not rec.empty:
            row['arrhythmia_flag'] = bool(rec['arrhythmia_flag'].iat[0])
            row['diagnostic_class'] = rec['diagnostic_class'].iat[0]
            row['dataset_origin'] = rec['dataset_origin'].iat[0]
        else:
            row['arrhythmia_flag'] = False
            row['diagnostic_class'] = np.nan
            row['dataset_origin'] = record_id.split('/', 1)[0] if '/' in record_id else 'unknown'
    else:
        row['arrhythmia_flag'] = False
        row['diagnostic_class'] = np.nan
        row['dataset_origin'] = record_id.split('/', 1)[0] if '/' in record_id else 'unknown'

    sq = frames['signal_quality']
    de = frames['delineation']
    tw = frames['twave']
    mr = frames['measurement']

    for col in ['hfn_index','pli_index','clipping_ratio','flatline_ratio','signal_quality_score']:
        agg = aggregations(sq[sq['record_id'] == record_id][col]) if not sq.empty else dict(mean=np.nan, std=np.nan, max=np.nan, p95=np.nan)
        row[f'mean_{col}'] = agg['mean']
        row[f'std_{col}'] = agg['std']
        row[f'max_{col}'] = agg['max']
        row[f'p95_{col}'] = agg['p95']

    boundary_conf = aggregations(de[de['record_id'] == record_id]['boundary_confidence']) if not de.empty else {'mean': np.nan, 'std': np.nan, 'max': np.nan, 'p95': np.nan}
    row['mean_boundary_confidence'] = boundary_conf['mean']
    row['std_boundary_confidence'] = boundary_conf['std']
    row['max_t_end_uncertainty_ms'] = aggregations(de[de['record_id'] == record_id]['t_end_uncertainty_ms'])['max'] if not de.empty else np.nan
    row['p95_t_end_uncertainty_ms'] = aggregations(de[de['record_id'] == record_id]['t_end_uncertainty_ms'])['p95'] if not de.empty else np.nan

    row['mean_t_end_ambiguity_score'] = aggregations(tw[tw['record_id'] == record_id]['t_end_ambiguity_score'])['mean'] if not tw.empty else np.nan
    row['max_t_end_ambiguity_score'] = aggregations(tw[tw['record_id'] == record_id]['t_end_ambiguity_score'])['max'] if not tw.empty else np.nan
    row['mean_morphology_confidence'] = aggregations(tw[tw['record_id'] == record_id]['morphology_confidence'])['mean'] if not tw.empty else np.nan

    row['mean_bsqi'] = aggregations(mr[mr['record_id'] == record_id]['bsqi'])['mean'] if not mr.empty else np.nan
    row['min_bsqi'] = aggregations(mr[mr['record_id'] == record_id]['bsqi'])['mean'] if not mr.empty else np.nan
    row['mean_wsqi'] = aggregations(mr[mr['record_id'] == record_id]['wsqi'])['mean'] if not mr.empty else np.nan
    row['min_wsqi'] = aggregations(mr[mr['record_id'] == record_id]['wsqi'])['mean'] if not mr.empty else np.nan
    row['mean_lead_agreement'] = aggregations(mr[mr['record_id'] == record_id]['lead_agreement_score'])['mean'] if not mr.empty else np.nan
    row['worst_lead_agreement'] = aggregations(mr[mr['record_id'] == record_id]['lead_agreement_score'])['max'] if not mr.empty else np.nan
    row['mean_beat_agreement'] = aggregations(mr[mr['record_id'] == record_id]['beat_agreement_score'])['mean'] if not mr.empty else np.nan
    row['worst_beat_agreement'] = aggregations(mr[mr['record_id'] == record_id]['beat_agreement_score'])['max'] if not mr.empty else np.nan
    row['qt_variance_leads'] = aggregations(mr[mr['record_id'] == record_id]['qt_variance_leads'])['mean'] if not mr.empty else np.nan
    row['qt_variance_beats'] = aggregations(mr[mr['record_id'] == record_id]['qt_variance_beats'])['mean'] if not mr.empty else np.nan

    rows.append(row)

confidence_features = pd.DataFrame(rows)
required = {
    'record_id','arrhythmia_flag','diagnostic_class','dataset_origin',
    'mean_hfn_index','std_hfn_index','max_hfn_index','p95_hfn_index',
    'mean_pli_index','std_pli_index','max_pli_index','p95_pli_index',
    'mean_clipping_ratio','std_clipping_ratio','max_clipping_ratio','p95_clipping_ratio',
    'mean_flatline_ratio','std_flatline_ratio','max_flatline_ratio','p95_flatline_ratio',
    'mean_signal_quality_score','std_signal_quality_score','max_signal_quality_score','p95_signal_quality_score',
    'mean_boundary_confidence','std_boundary_confidence','max_t_end_uncertainty_ms','p95_t_end_uncertainty_ms',
    'mean_t_end_ambiguity_score','max_t_end_ambiguity_score','mean_morphology_confidence',
    'mean_bsqi','min_bsqi','mean_wsqi','min_wsqi','mean_lead_agreement','worst_lead_agreement','mean_beat_agreement','worst_beat_agreement',
    'qt_variance_leads','qt_variance_beats',
}
missing = required.difference(set(confidence_features.columns))
assert not missing, f'missing required columns: {sorted(missing)}'
assert confidence_features['record_id'].is_unique

confidence_features.to_parquet(artifacts_dir / 'confidence_features.parquet', index=False)
print('Wrote confidence_features.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '10_confidence_model.ipynb',
            [
                mk_md(
                    'Notebook: 10_confidence_model.ipynb\n\nPurpose: Train calibrated confidence prediction models using record-level evidence.\n\nInputs:\n- confidence_features.parquet\n\nOutputs:\n- confidence_predictions.parquet'
                ),
                mk_md(
                    '# 10 — Confidence Model Training\n\nTrain and calibrate classification models that estimate the probability a QT measurement is trustworthy using the fused evidence table.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
sys.path.insert(0, str(Path.cwd().parent / 'src'))

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
confidence = pd.read_parquet(artifacts_dir / 'confidence_features.parquet')
feature_columns = [
    'mean_hfn_index','std_hfn_index','max_hfn_index','p95_hfn_index',
    'mean_pli_index','std_pli_index','max_pli_index','p95_pli_index',
    'mean_clipping_ratio','std_clipping_ratio','max_clipping_ratio','p95_clipping_ratio',
    'mean_flatline_ratio','std_flatline_ratio','max_flatline_ratio','p95_flatline_ratio',
    'mean_signal_quality_score','std_signal_quality_score','max_signal_quality_score','p95_signal_quality_score',
    'mean_boundary_confidence','std_boundary_confidence','max_t_end_uncertainty_ms','p95_t_end_uncertainty_ms',
    'mean_t_end_ambiguity_score','max_t_end_ambiguity_score','mean_morphology_confidence',
    'mean_bsqi','min_bsqi','mean_wsqi','min_wsqi','mean_lead_agreement','worst_lead_agreement',
    'mean_beat_agreement','worst_beat_agreement','qt_variance_leads','qt_variance_beats',
]
cat_columns = ['diagnostic_class', 'dataset_origin']
for col in cat_columns:
    if col not in confidence.columns:
        confidence[col] = np.nan
confidence['confidence_label'] = (
    (confidence['mean_lead_agreement'] >= 0.7) &
    (confidence['mean_beat_agreement'] >= 0.7) &
    (confidence['mean_bsqi'] >= 0.6) &
    (confidence['mean_wsqi'] >= 0.6)
).astype(int)

X = confidence[feature_columns + cat_columns].copy()
y = confidence['confidence_label'].copy()

from sklearn.compose import ColumnTransformer

numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler()),
])
cat_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse=False)),
])
preprocessor = ColumnTransformer([
    ('num', numeric_transformer, feature_columns),
    ('cat', cat_transformer, cat_columns),
])

models = [('RandomForest', RandomForestClassifier(n_estimators=100, random_state=42))]

try:
    import xgboost as xgb
    models.append(('XGBoost', xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)))
except Exception:
    pass

try:
    import lightgbm as lgb
    models.append(('LightGBM', lgb.LGBMClassifier(random_state=42)))
except Exception:
    pass

results = []
for name, model in models:
    if len(np.unique(y)) < 2:
        continue
    clf = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', model),
    ])
    calibrated = CalibratedClassifierCV(clf, cv=3, method='isotonic')
    calibrated.fit(X, y)
    preds = calibrated.predict_proba(X)[:, 1]
    results.append((name, calibrated, preds))

if not results:
    raise RuntimeError('No confidence model could be trained.')

name, model, preds = results[0]
confidence['confidence_probability'] = preds
confidence['model_name'] = name
confidence['calibration_method'] = 'isotonic'
confidence['pipeline_version'] = 'v1.0.0'
confidence[['record_id','confidence_probability','model_name','calibration_method','pipeline_version']].to_parquet(artifacts_dir / 'confidence_predictions.parquet', index=False)
print('Wrote confidence_predictions.parquet')
'''
                ),
            ],
        )
    )

    notebooks.append(
        (
            '11_final_results.ipynb',
            [
                mk_md(
                    'Notebook: 11_final_results.ipynb\n\nPurpose: Convert calibrated confidence probabilities into operational decisions and derive thresholds from validation evidence.\n\nInputs:\n- confidence_predictions.parquet\n- confidence_features.parquet\n\nOutputs:\n- decision_results.parquet'
                ),
                mk_md(
                    '# 11 — Decision Model\n\nOptimize thresholds empirically from validation data and assign ACCEPT, REVIEW, or REJECT labels.'
                ),
                mk_code(
                    '''import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd().parent / 'src'))

root_dir = Path.cwd().parent
artifacts_dir = root_dir / 'artifacts'
preds = pd.read_parquet(artifacts_dir / 'confidence_predictions.parquet')
conf = pd.read_parquet(artifacts_dir / 'confidence_features.parquet')

if 'confidence_label' not in conf.columns:
    conf['confidence_label'] = ((conf['mean_lead_agreement'] >= 0.7) & (conf['mean_beat_agreement'] >= 0.7) & (conf['mean_bsqi'] >= 0.6) & (conf['mean_wsqi'] >= 0.6)).astype(int)

merged = preds.merge(conf[['record_id','confidence_label']], on='record_id', how='left')
merged['confidence_label'] = merged['confidence_label'].fillna(0).astype(int)
probs = merged['confidence_probability'].astype(float).values
labels = merged['confidence_label'].values

thresholds = []
for low in np.linspace(0.0, 0.4, 5):
    for high in np.linspace(0.6, 1.0, 5):
        if high <= low:
            continue
        decision = np.where(probs >= high, 'ACCEPT', np.where(probs >= low, 'REVIEW', 'REJECT'))
        accept_mask = decision == 'ACCEPT'
        review_mask = decision == 'REVIEW'
        reject_mask = decision == 'REJECT'
        false_accept_rate = float(np.sum((labels == 0) & accept_mask) / max(1, np.sum(accept_mask)))
        error_capture_rate = float(np.sum((labels == 0) & (review_mask | reject_mask)) / max(1, np.sum(labels == 0)))
        thresholds.append({
            'low': float(low),
            'high': float(high),
            'false_accept_rate': false_accept_rate,
            'error_capture_rate': error_capture_rate,
        })

threshold_df = pd.DataFrame(thresholds)
selected = threshold_df.sort_values(['false_accept_rate', 'error_capture_rate']).iloc[0]
low = selected['low']
high = selected['high']
merged['decision_class'] = np.where(merged['confidence_probability'] >= high, 'ACCEPT', np.where(merged['confidence_probability'] >= low, 'REVIEW', 'REJECT'))
output = merged[['record_id','confidence_probability','decision_class']].copy()
output['pipeline_version'] = 'v1.0.0'
output.to_parquet(artifacts_dir / 'decision_results.parquet', index=False)
print('Wrote decision_results.parquet')
'''
                ),
            ],
        )
    )

    for name, cells in notebooks:
        write_notebook(name, cells)

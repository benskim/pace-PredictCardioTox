"""PhysioNet QT Database download and loading helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import wfdb

QT_DATABASE = "qtdb"

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_name(value: str, label: str) -> str:
    """Reject names that contain path separators or unsafe characters."""
    if not value or not _SAFE_NAME_RE.match(value):
        raise ValueError(
            f"{label} must be non-empty and contain only "
            f"alphanumeric characters, hyphens, or underscores; got {value!r}"
        )
    return value


def _qt_db_path(data_dir: str | Path) -> Path:
    """Return the local directory for the QT Database inside *data_dir*."""
    return Path(data_dir) / QT_DATABASE


def download_qt_database(
    data_dir: str | Path = "data/physionet",
    records: Iterable[str] | None = None,
    annotators: Iterable[str] | None = None,
) -> Path:
    """Download all or part of the PhysioNet QT Database with WFDB.

    Parameters
    ----------
    data_dir:
        Local base directory. QT Database files are stored in `data_dir/qtdb`.
    records:
        Optional record names such as `sel100` or `sel102`. If omitted, WFDB
        downloads the complete database.
    annotators:
        Optional annotation extensions, for example `pu0` or `pu1`.
    """
    if records:
        for rec in records:
            _validate_name(rec, "record name")
    if annotators:
        for ann in annotators:
            _validate_name(ann, "annotator")
    target = _qt_db_path(data_dir)
    target.mkdir(parents=True, exist_ok=True)
    wfdb.dl_database(
        QT_DATABASE,
        dl_dir=str(target),
        records=list(records) if records else "all",
        annotators=list(annotators) if annotators else "all",
    )
    return target


def discover_local_records(data_dir: str | Path = "data/physionet") -> list[str]:
    """Return record names discovered from local WFDB header files."""
    return sorted(path.stem for path in _qt_db_path(data_dir).glob("*.hea"))


def load_qt_record(record_name: str, data_dir: str | Path = "data/physionet") -> tuple[pd.DataFrame, dict]:
    """Load a QT Database record as a signal DataFrame plus metadata."""
    _validate_name(record_name, "record name")
    record_path = _qt_db_path(data_dir) / record_name
    record = wfdb.rdrecord(str(record_path))
    signals = pd.DataFrame(record.p_signal, columns=record.sig_name)
    signals.insert(0, "sample", signals.index.astype(int))
    signals.attrs["fs"] = record.fs
    signals.attrs["record_name"] = record_name
    metadata = {
        "record_name": record_name,
        "fs": record.fs,
        "signal_names": record.sig_name,
        "units": record.units,
        "comments": record.comments,
    }
    return signals, metadata


def load_qt_annotations(
    record_name: str,
    annotator: str = "pu0",
    data_dir: str | Path = "data/physionet",
) -> pd.DataFrame:
    """Load QT Database annotations into a tidy DataFrame."""
    _validate_name(record_name, "record name")
    _validate_name(annotator, "annotator")
    record_path = _qt_db_path(data_dir) / record_name
    annotation = wfdb.rdann(str(record_path), annotator)
    return pd.DataFrame(
        {
            "record_name": record_name,
            "annotator": annotator,
            "sample": annotation.sample,
            "symbol": annotation.symbol,
            "subtype": annotation.subtype,
            "chan": annotation.chan,
            "num": annotation.num,
            "aux_note": annotation.aux_note,
        }
    )

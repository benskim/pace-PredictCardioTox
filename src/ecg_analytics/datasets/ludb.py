"""Lobachevsky University Electrocardiography Database (LUDB) adapter.

LUDB provides 200 ten-second 12-lead ECG records with detailed delineation
annotations (P, QRS, T boundaries) making it ideal for wave-delineation
validation.

Records are distributed via PhysioNet and loaded with the WFDB library.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "ludb"
PHYSIONET_DB = "ludb"

# LUDB stores per-lead annotations with these extensions
_LEAD_ANNOTATORS = [
    "i",
    "ii",
    "iii",
    "avr",
    "avl",
    "avf",
    "v1",
    "v2",
    "v3",
    "v4",
    "v5",
    "v6",
]


class LUDBDataset:
    """Adapter for the LUDB database.

    Parameters
    ----------
    data_dir : str | Path
        Root directory.  Database files live under ``data_dir/ludb/``.
    """

    name = "ludb"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    def download(self, records: list[str] | None = None) -> Path:
        """Download LUDB from PhysioNet."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # Some LUDB record identifiers in the WFDB archive are nested under
        # a `data/` subdirectory (e.g. `data/1`, `data/2`). Accepting simple
        # numeric record ids ("1") is convenient for users, so map those to
        # the expected remote form automatically.
        records_to_pass = "all"
        if records:
            mapped = []
            for r in records:
                if isinstance(r, str) and r.isdigit() and "/" not in r:
                    mapped.append(f"data/{r}")
                else:
                    mapped.append(r)
            records_to_pass = mapped

        wfdb.dl_database(
            PHYSIONET_DB,
            dl_dir=str(self.db_dir),
            records=records_to_pass,
        )
        return self.db_dir

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        records = [
            p.with_suffix("").relative_to(self.db_dir).as_posix()
            for p in self.db_dir.glob("**/*.hea")
        ]
        return sorted(records)

    def load_record(self, record_id: str, annotator_leads: list[str] | None = None) -> ECGRecord:
        """Load a single LUDB record.

        Parameters
        ----------
        record_id : str
            Record name (e.g. ``"1"``).
        annotator_leads : list[str] | None
            Specific lead annotator extensions to load.  Defaults to all 12.
        """
        rec_path = str(self.db_dir / record_id)
        rec = wfdb.rdrecord(rec_path)
        signal = np.asarray(rec.p_signal, dtype=np.float64)

        leads = annotator_leads or _LEAD_ANNOTATORS
        annotations: list[Annotation] = []
        for lead_idx, lead_name in enumerate(leads):
            ann_file = self.db_dir / f"{record_id}.{lead_name}"
            if not ann_file.exists():
                continue
            try:
                ann = wfdb.rdann(rec_path, lead_name)
            except Exception:  # noqa: BLE001
                continue
            for samp, sym in zip(ann.sample, ann.symbol):
                annotations.append(
                    Annotation(
                        sample=int(samp),
                        symbol=sym,
                        label=sym,
                        lead=lead_idx,
                    )
                )

        return ECGRecord(
            record_id=record_id,
            signal=signal,
            fs=float(rec.fs),
            lead_names=list(rec.sig_name),
            annotations=annotations,
            metadata={
                "units": rec.units,
                "comments": getattr(rec, "comments", []),
                "database": DATABASE_NAME,
            },
        )

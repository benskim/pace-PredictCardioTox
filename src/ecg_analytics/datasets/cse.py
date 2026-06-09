"""CSE (Common Standards for Electrocardiography) Multilead Database adapter.

The CSE database is used for evaluating measurement accuracy of ECG analysis
programs.  Because CSE data is not freely redistributable, this adapter
expects the user to have already placed WFDB-formatted files under the
configured ``data_dir/cse/`` directory.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "cse"


class CSEDataset:
    """Adapter for CSE Multilead Database files in WFDB format.

    Parameters
    ----------
    data_dir : str | Path
        Root directory. Database files should be under ``data_dir/cse/``.
    """

    name = "cse"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        return sorted(p.stem for p in self.db_dir.glob("*.hea"))

    def load_record(
        self, record_id: str, annotator: str | None = None
    ) -> ECGRecord:
        """Load a single CSE record.

        Parameters
        ----------
        record_id : str
            Record name.
        annotator : str | None
            Optional annotation extension.
        """
        rec_path = str(self.db_dir / record_id)
        rec = wfdb.rdrecord(rec_path)
        signal = np.asarray(rec.p_signal, dtype=np.float64)

        annotations: list[Annotation] = []
        if annotator:
            ann_file = self.db_dir / f"{record_id}.{annotator}"
            if ann_file.exists():
                ann = wfdb.rdann(rec_path, annotator)
                for samp, sym in zip(ann.sample, ann.symbol):
                    annotations.append(
                        Annotation(sample=int(samp), symbol=sym, label=sym)
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

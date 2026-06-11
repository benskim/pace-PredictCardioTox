"""PhysioNet QT Database adapter.

Wraps the WFDB library to present QT Database records through the common
:class:`ECGRecord` interface.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "qtdb"

# Symbol → human label mapping for QT Database annotations
_SYMBOL_LABELS: dict[str, str] = {
    "p": "P-peak",
    "(": "wave-onset",
    ")": "wave-end",
    "N": "R-peak",
    "t": "T-peak",
}


class QTDBDataset:
    """Adapter for the PhysioNet QT Database.

    Parameters
    ----------
    data_dir : str | Path
        Root directory that contains (or will contain) a ``qtdb/`` subfolder
        with the downloaded WFDB files.
    """

    name = "qtdb"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    # ------------------------------------------------------------------
    # Download helpers
    # ------------------------------------------------------------------

    def download(
        self,
        records: list[str] | None = None,
        annotators: list[str] | None = None,
    ) -> Path:
        """Download the QT Database via WFDB."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        wfdb.dl_database(
            DATABASE_NAME,
            dl_dir=str(self.db_dir),
            records=records or "all",
            annotators=annotators or "all",
        )
        return self.db_dir

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        records = [
            p.with_suffix("").relative_to(self.db_dir).as_posix()
            for p in self.db_dir.glob("**/*.hea")
        ]
        return sorted(records)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_record(self, record_id: str, annotator: str = "pu0") -> ECGRecord:
        """Load a single QT Database record.

        Parameters
        ----------
        record_id : str
            Record name (e.g. ``"sel100"``).
        annotator : str
            Annotation extension (``"pu0"`` or ``"pu1"``).
        """
        rec_path = str(self.db_dir / record_id)
        rec = wfdb.rdrecord(rec_path)

        signal = np.asarray(rec.p_signal, dtype=np.float64)

        # Parse annotations
        annotations: list[Annotation] = []
        ann_path = self.db_dir / f"{record_id}.{annotator}"
        if ann_path.exists():
            ann = wfdb.rdann(rec_path, annotator)
            for samp, sym in zip(ann.sample, ann.symbol):
                annotations.append(
                    Annotation(
                        sample=int(samp),
                        symbol=sym,
                        label=_SYMBOL_LABELS.get(sym, sym),
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
                "comments": rec.comments,
                "database": DATABASE_NAME,
            },
        )

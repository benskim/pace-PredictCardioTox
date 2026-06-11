"""PTB-XL dataset adapter.

PTB-XL is a large-scale 12-lead ECG dataset with clinical labels and metadata.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "ptbxl"
PHYSIONET_DB = "ptb-xl"


class PTBXLDataset:
    """Adapter for the PTB-XL dataset.

    Parameters
    ----------
    data_dir : str | Path
        Root directory. Database files live under ``data_dir/ptbxl/``.
    """

    name = "ptbxl"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    def download(
        self,
        records: list[str] | None = None,
        annotators: list[str] | None = None,
        keep_subdirs: bool = True,
    ) -> Path:
        """Download PTB-XL from PhysioNet."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # PTB-XL uses nested patient directories (e.g. patient001/s0010_re).
        # Be defensive: if caller passed a top-level id, try a few plausible
        # variations before giving up so callers don't get raw 404 traces.
        candidates = [records] if records else [["all"]]
        if records:
            mapped = []
            for r in records:
                # If user passed a patient id like 's0010_re' try prefixing
                # with common patient folders.
                if isinstance(r, str) and r.startswith("s") and "_" in r:
                    mapped.append(f"patient001/{r}")
                    mapped.append(r)
                else:
                    mapped.append(r)
            candidates = [mapped]

        # Try several DB name variants in case of versioned hosting paths.
        db_name_candidates = [PHYSIONET_DB, f"{PHYSIONET_DB}/1.0.3", f"{PHYSIONET_DB}/1.0.2"]

        last_exc = None
        for db_name in db_name_candidates:
            for cand in candidates:
                try:
                    wfdb.dl_database(
                        db_name,
                        dl_dir=str(self.db_dir),
                        records=cand,
                        annotators=annotators or "all",
                        keep_subdirs=keep_subdirs,
                    )
                    return self.db_dir
                except Exception as e:
                    last_exc = e
                    continue

        raise RuntimeError(
            f"Could not download PTB-XL files for records={records!r}. Last error: {last_exc}"
        )

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        records = [
            p.with_suffix("").relative_to(self.db_dir).as_posix()
            for p in self.db_dir.glob("**/*.hea")
        ]
        return sorted(records)

    def load_record(self, record_id: str, annotator: str | None = None) -> ECGRecord:
        """Load a single PTB-XL record."""
        rec_path = str(self.db_dir / record_id)
        rec = wfdb.rdrecord(rec_path)
        signal = np.asarray(rec.p_signal, dtype=np.float64)

        return ECGRecord(
            record_id=record_id,
            signal=signal,
            fs=float(rec.fs),
            lead_names=list(rec.sig_name),
            annotations=[],
            metadata={
                "units": rec.units,
                "comments": getattr(rec, "comments", []),
                "database": DATABASE_NAME,
            },
        )

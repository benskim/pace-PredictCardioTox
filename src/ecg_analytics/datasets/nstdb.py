"""MIT-BIH Noise Stress Test Database (NSTDB) adapter.

NSTDB contains controlled noise recordings for robustness evaluation.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "nstdb"
PHYSIONET_DB = "nstdb"


class NSTDBDataset:
    """Adapter for the MIT-BIH Noise Stress Test Database.

    Parameters
    ----------
    data_dir : str | Path
        Root directory. Database files live under ``data_dir/nstdb/``.
    """

    name = "nstdb"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    def download(
        self,
        records: list[str] | None = None,
        annotators: list[str] | None = None,
        keep_subdirs: bool = True,
    ) -> Path:
        """Download NSTDB from PhysioNet."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # Defensive download: try a few common record-name mappings
        candidates = [records] if records else [["all"]]
        if records:
            mapped = []
            for r in records:
                if isinstance(r, str) and r.isdigit() and "/" not in r:
                    mapped.append(f"data/{r}")
                    mapped.append(r)
                else:
                    mapped.append(r)
            candidates = [mapped]

        # Also try a few likely database name variants (some PhysioNet
        # projects are hosted under versioned subpaths).
        db_name_candidates = [PHYSIONET_DB, f"{PHYSIONET_DB}/1.0.0", f"{PHYSIONET_DB}/1.0.1"]

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
                except Exception as e:  # catch NetFileNotFoundError and others
                    last_exc = e
                    # try next candidate
                    continue

        # If we reach here, none of the attempts succeeded. Do not raise raw
        # NetFileNotFoundError to callers — return the target directory and
        # surface a clear ValueError instead so notebooks and scripts don't
        # crash with low-level 404 traces.
        raise RuntimeError(
            f"Could not download NSTDB files for records={records!r}. Last error: {last_exc}"
        )

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        records = [
            p.with_suffix("").relative_to(self.db_dir).as_posix()
            for p in self.db_dir.glob("**/*.hea")
        ]
        return sorted(records)

    def load_record(self, record_id: str) -> ECGRecord:
        """Load a single NSTDB record."""
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

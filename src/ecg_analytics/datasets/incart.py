"""INCART Database adapter.

INCART provides 12-lead arrhythmia recordings for robustness analysis.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import wfdb

from .base import Annotation, ECGRecord

DATABASE_NAME = "incart"
PHYSIONET_DB = "incartdb"


class INCARTDataset:
    """Adapter for the INCART database.

    Parameters
    ----------
    data_dir : str | Path
        Root directory. Database files live under ``data_dir/incart/``.
    """

    name = "incart"

    def __init__(self, data_dir: str | Path = "data/physionet") -> None:
        self.data_dir = Path(data_dir)
        self.db_dir = self.data_dir / DATABASE_NAME

    def download(
        self,
        records: list[str] | None = None,
        annotators: list[str] | None = None,
        keep_subdirs: bool = True,
    ) -> Path:
        """Download INCART from PhysioNet."""
        self.db_dir.mkdir(parents=True, exist_ok=True)
        # Try a few candidate record formats to avoid raw 404s from WFDB
        candidates = [records] if records else [["all"]]
        if records:
            mapped = []
            for r in records:
                # INCART sometimes uses numeric or suffixed names like '100m'
                if isinstance(r, str) and r.endswith("m"):
                    mapped.append(r)
                elif isinstance(r, str) and r.isdigit():
                    mapped.append(r)
                    mapped.append(f"{r}m")
                else:
                    mapped.append(r)
            candidates = [mapped]

        # Try a few DB name variants as some PhysioNet projects expose
        # different versioned paths.
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
                except Exception as e:
                    last_exc = e
                    continue

        raise RuntimeError(
            f"Could not download INCART files for records={records!r}. Last error: {last_exc}"
        )

    def list_records(self) -> list[str]:
        """Return sorted record IDs found locally."""
        return sorted(p.stem for p in self.db_dir.glob("*.hea"))

    def load_record(self, record_id: str, annotator: str | None = None) -> ECGRecord:
        """Load a single INCART record."""
        rec_path = str(self.db_dir / record_id)
        rec = wfdb.rdrecord(rec_path)
        signal = np.asarray(rec.p_signal, dtype=np.float64)

        annotations: list[Annotation] = []
        if annotator:
            ann_file = self.db_dir / f"{record_id}.{annotator}"
            if ann_file.exists():
                ann = wfdb.rdann(rec_path, annotator)
                for samp, sym in zip(ann.sample, ann.symbol):
                    annotations.append(Annotation(sample=int(samp), symbol=sym, label=sym))

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

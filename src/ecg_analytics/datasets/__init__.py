"""Dataset adapters with a common ``ECGRecord`` interface.

Every adapter exposes the same API::

    record = dataset.load_record(record_id)
    signal = record.signal      # np.ndarray (samples, leads)
    annotations = record.annotations
    fs = record.fs
"""

from .base import Annotation, ECGRecord
from .incart import INCARTDataset
from .ludb import LUDBDataset
from .nstdb import NSTDBDataset
from .ptbxl import PTBXLDataset
from .qtdb import QTDBDataset

__all__ = [
    "Annotation",
    "ECGRecord",
    "INCARTDataset",
    "LUDBDataset",
    "NSTDBDataset",
    "PTBXLDataset",
    "QTDBDataset",
]

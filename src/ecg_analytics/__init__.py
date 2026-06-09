"""PredictCardioTox QTc Research — reusable ECG analytics library.

Subpackages
-----------
datasets
    Unified dataset adapters (QTDB, LUDB, CSE) behind a common ``ECGRecord`` API.
preprocessing
    Signal filtering, noise injection, and quality assessment.
delineation
    1-D U-Net wave segmentation model and inference pipeline.
qt
    QT interval measurement via the geometric tangent method.
qtc
    QTc correction formulas and longitudinal shift tracking.
validation
    Accuracy metrics, validation pipeline, and report generation.
visualization
    Publication-quality ECG and analytics plots.

Legacy top-level imports (backwards compatible)
-----------------------------------------------
The original ``alerts``, ``baseline``, ``physionet``, and ``qtc`` (flat)
modules are still importable from the package root.
"""

# Legacy flat-module re-exports (backwards compatible)
from .alerts import AlertRule, generate_qtc_alerts
from .baseline import baseline_summary
from .physionet import QT_DATABASE, discover_local_records, load_qt_annotations, load_qt_record

# Re-export the four formulas from the original flat qtc module
from .qtc_compat import qtc_bazett, qtc_framingham, qtc_fridericia, qtc_hodges

__all__ = [
    # Legacy
    "AlertRule",
    "QT_DATABASE",
    "baseline_summary",
    "discover_local_records",
    "generate_qtc_alerts",
    "load_qt_annotations",
    "load_qt_record",
    "qtc_bazett",
    "qtc_fridericia",
    "qtc_framingham",
    "qtc_hodges",
]

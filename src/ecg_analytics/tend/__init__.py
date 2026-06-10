"""T-end determination methods and multi-method agreement analysis.

Provides four independent T-end algorithms:

* **Tangent** — geometric tangent at maximum downslope
* **Threshold** — percentage-of-peak amplitude crossing
* **Derivative** — zero-crossing of smoothed first derivative
* **Wavelet** — CWT-based modulus-maxima approach

The :mod:`agreement` module compares all methods and produces a
*T-End Stability Score*.
"""

from .agreement import TEndAgreement, tend_stability_metrics, tend_stability_score
from .derivative import derivative_t_end
from .tangent import tangent_t_end
from .threshold import threshold_t_end
from .wavelet import wavelet_t_end

__all__ = [
    "TEndAgreement",
    "derivative_t_end",
    "tangent_t_end",
    "tend_stability_metrics",
    "tend_stability_score",
    "threshold_t_end",
    "wavelet_t_end",
]

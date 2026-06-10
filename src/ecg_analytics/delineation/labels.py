"""Wave-class label encoding / decoding for the delineation model."""

from __future__ import annotations

import numpy as np

# Class index → wave region name.  Index 0 is always background.
WAVE_CLASSES: dict[int, str] = {
    0: "background",
    1: "P-wave",
    2: "QRS",
    3: "T-wave",
}

_CLASS_COUNT = len(WAVE_CLASSES)

# Annotation symbol → class index mapping (PhysioNet / LUDB conventions)
_SYMBOL_TO_CLASS: dict[str, int] = {
    "p": 1,
    "(p": 1,
    "p)": 1,
    "N": 2,
    "Q": 2,
    "R": 2,
    "S": 2,
    "t": 3,
    "(t": 3,
    "t)": 3,
}


def encode_annotations(
    n_samples: int,
    annotations: list[tuple[int, str]],
    fs: float = 250.0,
    wave_half_width_ms: float = 50.0,
) -> np.ndarray:
    """Build a dense label mask from sparse fiducial annotations.

    Each fiducial point is expanded into a region of
    ``2 * wave_half_width_ms`` milliseconds centred on the annotated sample.

    Parameters
    ----------
    n_samples : int
        Length of the output mask.
    annotations : list of (sample_index, symbol)
        Sparse fiducial points.
    fs : float
        Sampling frequency.
    wave_half_width_ms : float
        Half-width of each annotated region in ms.

    Returns
    -------
    np.ndarray of shape (n_samples,) with dtype int
        Label mask with values in {0, 1, 2, 3}.
    """
    mask = np.zeros(n_samples, dtype=np.int64)
    half = int(wave_half_width_ms * fs / 1000)
    for samp, sym in annotations:
        cls = _SYMBOL_TO_CLASS.get(sym, 0)
        if cls == 0:
            continue
        lo = max(0, samp - half)
        hi = min(n_samples, samp + half + 1)
        mask[lo:hi] = cls
    return mask


def decode_mask(mask: np.ndarray) -> dict[str, list[tuple[int, int]]]:
    """Convert a dense label mask into start/end sample ranges per wave class.

    Returns
    -------
    dict mapping class names to lists of ``(start, end)`` sample ranges.
    """
    result: dict[str, list[tuple[int, int]]] = {
        name: [] for name in WAVE_CLASSES.values() if name != "background"
    }
    current_cls = 0
    start = 0
    for i, val in enumerate(mask):
        if val != current_cls:
            if current_cls != 0:
                name = WAVE_CLASSES.get(current_cls, "background")
                if name in result:
                    result[name].append((start, i - 1))
            current_cls = int(val)
            start = i
    # Close last segment
    if current_cls != 0:
        name = WAVE_CLASSES.get(current_cls, "background")
        if name in result:
            result[name].append((start, len(mask) - 1))
    return result

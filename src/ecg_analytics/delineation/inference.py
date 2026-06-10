"""High-level delineation inference pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from .labels import WAVE_CLASSES, decode_mask
from .unet import UNet1D


@dataclass
class DelineationResult:
    """Result of a delineation run on a single lead.

    Attributes
    ----------
    mask : np.ndarray
        Per-sample class prediction (int, shape ``(n_samples,)``).
    probabilities : np.ndarray
        Per-sample class probabilities (shape ``(n_samples, n_classes)``).
    regions : dict[str, list[tuple[int, int]]]
        Decoded wave regions as ``{class_name: [(start, end), ...]}``.
    """

    mask: np.ndarray
    probabilities: np.ndarray
    regions: dict[str, list[tuple[int, int]]] = field(default_factory=dict)


def delineate(
    signal: np.ndarray,
    model: UNet1D | None = None,
    device: str = "cpu",
) -> DelineationResult:
    """Run 1-D U-Net delineation on a single-lead ECG signal.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    model : UNet1D | None
        Trained model instance. If ``None``, a default (untrained) model is
        created — useful for pipeline testing but not for real predictions.
    device : str
        PyTorch device string.
    """
    if model is None:
        model = UNet1D(in_channels=1, n_classes=len(WAVE_CLASSES))

    model = model.to(device).eval()

    # Prepare input tensor: (1, 1, length)
    x = torch.tensor(signal, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)  # (1, n_classes, length)

    probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()  # (n_classes, length)
    probs = probs.T  # (length, n_classes)
    mask = np.argmax(probs, axis=1)
    regions = decode_mask(mask)

    return DelineationResult(mask=mask, probabilities=probs, regions=regions)

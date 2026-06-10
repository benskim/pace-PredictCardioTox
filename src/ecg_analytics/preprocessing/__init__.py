"""Signal preprocessing: filtering, noise injection, and quality assessment."""

from .filters import bandpass_filter, highpass_filter, notch_filter, remove_baseline_wander
from .noise import add_baseline_wander, add_emg_noise, add_motion_artifact, add_powerline_noise, inject_noise
from .quality import signal_quality_index, snr_estimate

__all__ = [
    "add_baseline_wander",
    "add_emg_noise",
    "add_motion_artifact",
    "add_powerline_noise",
    "bandpass_filter",
    "highpass_filter",
    "inject_noise",
    "notch_filter",
    "remove_baseline_wander",
    "signal_quality_index",
    "snr_estimate",
]

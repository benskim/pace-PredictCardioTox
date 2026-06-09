"""Tests for the preprocessing module (filters, noise, quality)."""

import numpy as np
import pytest

from ecg_analytics.preprocessing.filters import (
    bandpass_filter,
    highpass_filter,
    notch_filter,
    remove_baseline_wander,
)
from ecg_analytics.preprocessing.noise import (
    NOISE_FUNCTIONS,
    STANDARD_SNR_LEVELS,
    add_baseline_wander,
    add_emg_noise,
    add_motion_artifact,
    add_powerline_noise,
    inject_noise,
)
from ecg_analytics.preprocessing.quality import signal_quality_index, snr_estimate


class TestFilters:
    def test_bandpass_preserves_length(self):
        sig = np.random.randn(1000)
        out = bandpass_filter(sig, fs=250.0, low=0.5, high=40.0)
        assert len(out) == len(sig)

    def test_highpass_removes_dc(self):
        sig = np.ones(1000) * 5.0 + np.random.randn(1000) * 0.01
        out = highpass_filter(sig, fs=250.0, cutoff=0.5)
        assert abs(np.mean(out)) < 0.5

    def test_notch_at_50hz(self):
        fs = 500.0
        t = np.arange(0, 2, 1 / fs)
        sig = np.sin(2 * np.pi * 50 * t)  # pure 50 Hz
        out = notch_filter(sig, fs, freq=50.0)
        # Notch should substantially reduce 50 Hz energy
        assert np.std(out) < 0.2 * np.std(sig)

    def test_remove_baseline_wander_alias(self):
        sig = np.random.randn(1000)
        out = remove_baseline_wander(sig, fs=250.0)
        assert len(out) == len(sig)


class TestNoise:
    def _clean_signal(self, fs=250.0, dur=5.0):
        t = np.arange(0, dur, 1 / fs)
        return np.sin(2 * np.pi * 1.0 * t), fs

    def test_add_baseline_wander(self):
        sig, fs = self._clean_signal()
        noisy = add_baseline_wander(sig, fs, snr_db=12.0)
        assert noisy.shape == sig.shape
        assert not np.allclose(noisy, sig)

    def test_add_emg_noise(self):
        sig, fs = self._clean_signal()
        noisy = add_emg_noise(sig, fs, snr_db=12.0)
        assert noisy.shape == sig.shape

    def test_add_powerline_noise(self):
        sig, fs = self._clean_signal()
        noisy = add_powerline_noise(sig, fs, snr_db=12.0)
        assert noisy.shape == sig.shape

    def test_add_motion_artifact(self):
        sig, fs = self._clean_signal()
        noisy = add_motion_artifact(sig, fs, snr_db=12.0)
        assert noisy.shape == sig.shape

    def test_inject_noise_registry(self):
        sig, fs = self._clean_signal()
        for name in NOISE_FUNCTIONS:
            noisy = inject_noise(sig, fs, name, snr_db=12.0)
            assert noisy.shape == sig.shape

    def test_inject_noise_unknown_type(self):
        sig, fs = self._clean_signal()
        with pytest.raises(ValueError, match="Unknown noise type"):
            inject_noise(sig, fs, "does_not_exist")

    def test_standard_snr_levels(self):
        assert STANDARD_SNR_LEVELS == [24, 18, 12, 6, 0]


class TestQuality:
    def test_snr_estimate_clean(self):
        sig = np.sin(np.linspace(0, 10 * np.pi, 1000))
        snr = snr_estimate(sig)
        assert snr > 0

    def test_snr_with_explicit_noise(self):
        sig = np.ones(100) * 10.0
        noise = np.ones(100) * 0.01
        snr = snr_estimate(sig, noise=noise)
        assert snr > 50

    def test_signal_quality_index_keys(self):
        sig = np.random.randn(1000)
        sqi = signal_quality_index(sig, fs=250.0)
        assert "snr_db" in sqi
        assert "kurtosis" in sqi
        assert "baseline_drift" in sqi
        assert "flatline_fraction" in sqi

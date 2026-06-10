"""Tests for the QT measurement module (tangent, t_wave, measurement)."""

import numpy as np

from ecg_analytics.qt.measurement import QTMeasurement, measure_qt_intervals
from ecg_analytics.qt.t_wave import extract_t_wave_region, find_t_peak
from ecg_analytics.qt.tangent import tangent_t_end


class TestTWave:
    def test_extract_t_wave_region(self):
        signal = np.zeros(1000)
        start, end = extract_t_wave_region(signal, r_peak=200, fs=250.0)
        # Default offset 80ms → 20 samples at 250 Hz
        assert start == 200 + 20
        assert end > start

    def test_find_t_peak_with_clear_peak(self):
        # Build signal with a bump at sample 50
        signal = np.zeros(100)
        signal[45:55] = np.array([0.1, 0.3, 0.5, 0.7, 0.9, 1.0, 0.8, 0.6, 0.4, 0.2])
        peak = find_t_peak(signal, 40, 60)
        assert peak is not None
        assert 45 <= peak <= 55

    def test_find_t_peak_empty_window(self):
        signal = np.zeros(10)
        result = find_t_peak(signal, 8, 9)
        assert result is None


class TestTangent:
    def _make_t_wave(self, fs=500.0):
        """Create a Gaussian T-wave with known peak."""
        t = np.arange(0, 0.5, 1 / fs)
        peak_time = 0.15
        signal = 0.5 * np.exp(-((t - peak_time) ** 2) / (2 * 0.02 ** 2))
        t_peak = int(peak_time * fs)
        return signal, t_peak, fs

    def test_tangent_t_end_returns_int(self):
        signal, t_peak, fs = self._make_t_wave()
        t_end = tangent_t_end(signal, t_peak, fs, baseline=0.0)
        assert t_end is not None
        assert isinstance(t_end, int)
        assert t_end > t_peak

    def test_tangent_t_end_near_baseline(self):
        signal, t_peak, fs = self._make_t_wave()
        t_end = tangent_t_end(signal, t_peak, fs, baseline=0.0)
        if t_end is not None:
            assert signal[t_end] < 0.1  # Should be near baseline

    def test_tangent_returns_none_for_short_signal(self):
        signal = np.array([1.0, 0.5])
        result = tangent_t_end(signal, 0, 250.0)
        assert result is None


class TestMeasurement:
    def _synthetic_ecg(self, fs=500.0):
        """Multi-beat synthetic ECG."""
        t = np.arange(0, 5.0, 1 / fs)
        signal = np.zeros_like(t)
        for bt in [0.5, 1.5, 2.5, 3.5]:
            qrs = 1.5 * np.exp(-((t - bt) ** 2) / (2 * 0.004 ** 2))
            tw = 0.4 * np.exp(-((t - bt - 0.25) ** 2) / (2 * 0.02 ** 2))
            signal += qrs + tw
        return signal, fs

    def test_measure_returns_list(self):
        signal, fs = self._synthetic_ecg()
        results = measure_qt_intervals(signal, fs)
        assert isinstance(results, list)
        assert all(isinstance(m, QTMeasurement) for m in results)

    def test_measure_with_r_peaks(self):
        signal, fs = self._synthetic_ecg()
        r_peaks = np.array([int(0.5 * fs), int(1.5 * fs)])
        results = measure_qt_intervals(signal, fs, r_peaks=r_peaks)
        assert len(results) == 2

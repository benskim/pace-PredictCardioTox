"""Tests for the visualization module (smoke tests — check figures are created)."""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend

from ecg_analytics.visualization.ecg_plots import plot_ecg_signal, plot_multi_lead
from ecg_analytics.visualization.delineation_plots import plot_delineation_overlay
from ecg_analytics.visualization.validation_plots import (
    plot_bland_altman,
    plot_error_distribution,
    plot_error_heatmap,
)
from ecg_analytics.visualization.noise_plots import plot_noise_comparison, plot_noise_degradation


class TestECGPlots:
    def test_plot_ecg_signal(self):
        fig = plot_ecg_signal(np.random.randn(500), fs=250.0)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_plot_multi_lead(self):
        signals = np.random.randn(500, 3)
        fig = plot_multi_lead(signals, fs=250.0, lead_names=["I", "II", "III"])
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestDelineationPlots:
    def test_plot_delineation_overlay(self):
        signal = np.random.randn(200)
        mask = np.zeros(200, dtype=int)
        mask[50:70] = 1
        mask[80:100] = 2
        mask[120:160] = 3
        fig = plot_delineation_overlay(signal, mask, fs=250.0)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestValidationPlots:
    def test_bland_altman(self):
        pred = np.random.randn(50) + 400
        ref = pred + np.random.randn(50) * 2
        fig = plot_bland_altman(pred, ref)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_error_distribution(self):
        errors = np.random.randn(100) * 5
        fig = plot_error_distribution(errors)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_error_heatmap(self):
        errors = np.random.rand(3, 5) * 10
        fig = plot_error_heatmap(["BW", "EMG", "PLI"], [24, 18, 12, 6, 0], errors)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestNoisePlots:
    def test_noise_comparison(self):
        clean = np.sin(np.linspace(0, 10 * np.pi, 500))
        noisy = clean + np.random.randn(500) * 0.3
        fig = plot_noise_comparison(clean, noisy, fs=250.0, noise_label="EMG")
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_noise_degradation(self):
        fig = plot_noise_degradation(
            [24, 18, 12, 6, 0],
            {"BW": [1, 2, 4, 8, 16], "EMG": [2, 3, 5, 10, 20]},
        )
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

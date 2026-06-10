"""Tests for the delineation module (labels, U-Net, inference)."""

import numpy as np
import torch

from ecg_analytics.delineation.inference import DelineationResult, delineate
from ecg_analytics.delineation.labels import WAVE_CLASSES, decode_mask, encode_annotations
from ecg_analytics.delineation.unet import UNet1D


class TestLabels:
    def test_wave_classes(self):
        assert WAVE_CLASSES[0] == "background"
        assert WAVE_CLASSES[3] == "T-wave"

    def test_encode_annotations_empty(self):
        mask = encode_annotations(100, [])
        assert mask.shape == (100,)
        assert np.all(mask == 0)

    def test_encode_annotations_creates_regions(self):
        annotations = [(50, "t")]  # T-wave at sample 50
        mask = encode_annotations(200, annotations, fs=250.0, wave_half_width_ms=20.0)
        assert np.any(mask == 3)  # T-wave class
        assert mask[50] == 3

    def test_decode_mask_round_trip(self):
        mask = np.zeros(100, dtype=np.int64)
        mask[20:30] = 1  # P-wave
        mask[40:50] = 2  # QRS
        mask[60:80] = 3  # T-wave
        regions = decode_mask(mask)
        assert len(regions["P-wave"]) == 1
        assert len(regions["QRS"]) == 1
        assert len(regions["T-wave"]) == 1


class TestUNet1D:
    def test_output_shape(self):
        model = UNet1D(in_channels=1, n_classes=4, base_filters=16, depth=3)
        x = torch.randn(2, 1, 256)
        with torch.no_grad():
            out = model(x)
        assert out.shape[0] == 2
        assert out.shape[1] == 4
        # Length should be approximately 256 (may differ by padding)
        assert abs(out.shape[2] - 256) <= 8

    def test_model_parameters_count(self):
        model = UNet1D(in_channels=1, n_classes=4, base_filters=16, depth=3)
        n_params = sum(p.numel() for p in model.parameters())
        assert n_params > 0


class TestInference:
    def test_delineate_returns_result(self):
        signal = np.random.randn(512).astype(np.float32)
        result = delineate(signal)
        assert isinstance(result, DelineationResult)
        assert result.mask.shape == (512,)
        assert result.probabilities.shape == (512, 4)

    def test_delineate_with_model(self):
        model = UNet1D(in_channels=1, n_classes=4, base_filters=16, depth=3)
        signal = np.random.randn(256).astype(np.float32)
        result = delineate(signal, model=model)
        assert result.mask.shape[0] == 256

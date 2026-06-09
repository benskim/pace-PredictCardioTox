"""Tests for the datasets module (base data model)."""

import numpy as np

from ecg_analytics.datasets.base import Annotation, ECGRecord


def test_ecg_record_duration():
    signal = np.zeros((500, 2))
    rec = ECGRecord(record_id="test", signal=signal, fs=250.0)
    assert rec.duration_s == 2.0


def test_ecg_record_n_leads():
    signal = np.zeros((500, 3))
    rec = ECGRecord(record_id="test", signal=signal, fs=250.0, lead_names=["I", "II", "III"])
    assert rec.n_leads == 3


def test_ecg_record_lead_extraction():
    signal = np.column_stack([np.ones(100), np.ones(100) * 2])
    rec = ECGRecord(record_id="test", signal=signal, fs=100.0)
    np.testing.assert_array_equal(rec.lead(0), np.ones(100))
    np.testing.assert_array_equal(rec.lead(1), np.ones(100) * 2)


def test_ecg_record_1d_signal():
    signal = np.ones(100)
    rec = ECGRecord(record_id="test", signal=signal, fs=100.0)
    assert rec.n_leads == 1
    np.testing.assert_array_equal(rec.lead(), signal)


def test_annotation_creation():
    ann = Annotation(sample=42, symbol="t", label="T-peak", lead=0)
    assert ann.sample == 42
    assert ann.symbol == "t"

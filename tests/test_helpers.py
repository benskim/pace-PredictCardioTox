"""Tests for the shared _helpers module."""

import numpy as np
import pandas as pd
import pytest

from ecg_analytics._helpers import require_columns, to_positive_array


class TestToPositiveArray:
    def test_converts_list_to_array(self):
        result = to_positive_array([1.0, 2.0, 3.0], "values")
        np.testing.assert_array_equal(result, np.array([1.0, 2.0, 3.0]))

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="values must be positive"):
            to_positive_array([0.0], "values")

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="Heart rates must be positive"):
            to_positive_array([-5.0], "Heart rates")

    def test_accepts_scalar(self):
        result = to_positive_array(42.0, "x")
        assert result.shape == ()
        assert float(result) == 42.0


class TestRequireColumns:
    def test_passes_when_columns_present(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        require_columns(df, "a", "b")

    def test_raises_for_missing_column(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="Missing required column.*b"):
            require_columns(df, "a", "b")

    def test_raises_lists_all_missing(self):
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="x.*y"):
            require_columns(df, "x", "y")

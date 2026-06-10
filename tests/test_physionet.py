"""Unit tests for ecg_analytics.physionet — the least covered module (37%)."""

from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd

from ecg_analytics.physionet import (
    QT_DATABASE,
    discover_local_records,
    download_qt_database,
    load_qt_annotations,
    load_qt_record,
)


# ---------------------------------------------------------------------------
# download_qt_database
# ---------------------------------------------------------------------------

@patch("ecg_analytics.physionet.wfdb.dl_database")
def test_download_qt_database_creates_target_dir_and_calls_wfdb(mock_dl, tmp_path):
    result = download_qt_database(data_dir=tmp_path)

    assert result == tmp_path / QT_DATABASE
    assert result.is_dir()
    mock_dl.assert_called_once_with(
        QT_DATABASE,
        dl_dir=str(tmp_path / QT_DATABASE),
        records="all",
        annotators="all",
    )


@patch("ecg_analytics.physionet.wfdb.dl_database")
def test_download_qt_database_forwards_records_and_annotators(mock_dl, tmp_path):
    download_qt_database(
        data_dir=tmp_path,
        records=["sel100", "sel102"],
        annotators=["pu0"],
    )

    mock_dl.assert_called_once_with(
        QT_DATABASE,
        dl_dir=str(tmp_path / QT_DATABASE),
        records=["sel100", "sel102"],
        annotators=["pu0"],
    )


# ---------------------------------------------------------------------------
# discover_local_records
# ---------------------------------------------------------------------------

def test_discover_local_records_returns_sorted_stems(tmp_path):
    db_dir = tmp_path / QT_DATABASE
    db_dir.mkdir()
    (db_dir / "sel102.hea").touch()
    (db_dir / "sel100.hea").touch()
    (db_dir / "sel100.dat").touch()  # non-.hea file — should be ignored

    records = discover_local_records(data_dir=tmp_path)

    assert records == ["sel100", "sel102"]


def test_discover_local_records_returns_empty_when_no_headers(tmp_path):
    db_dir = tmp_path / QT_DATABASE
    db_dir.mkdir()

    assert discover_local_records(data_dir=tmp_path) == []


# ---------------------------------------------------------------------------
# load_qt_record
# ---------------------------------------------------------------------------

@patch("ecg_analytics.physionet.wfdb.rdrecord")
def test_load_qt_record_returns_dataframe_and_metadata(mock_rdrecord, tmp_path):
    mock_record = SimpleNamespace(
        p_signal=np.array([[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]),
        sig_name=["MLII", "V5"],
        fs=250,
        units=["mV", "mV"],
        comments=["test comment"],
    )
    mock_rdrecord.return_value = mock_record

    db_dir = tmp_path / QT_DATABASE
    db_dir.mkdir(parents=True)

    signals, metadata = load_qt_record("sel100", data_dir=tmp_path)

    mock_rdrecord.assert_called_once_with(str(db_dir / "sel100"))

    assert isinstance(signals, pd.DataFrame)
    assert list(signals.columns) == ["sample", "MLII", "V5"]
    assert len(signals) == 3
    assert signals["sample"].tolist() == [0, 1, 2]
    assert signals.attrs["fs"] == 250
    assert signals.attrs["record_name"] == "sel100"

    assert metadata["record_name"] == "sel100"
    assert metadata["fs"] == 250
    assert metadata["signal_names"] == ["MLII", "V5"]
    assert metadata["units"] == ["mV", "mV"]
    assert metadata["comments"] == ["test comment"]


# ---------------------------------------------------------------------------
# load_qt_annotations
# ---------------------------------------------------------------------------

@patch("ecg_analytics.physionet.wfdb.rdann")
def test_load_qt_annotations_returns_tidy_dataframe(mock_rdann, tmp_path):
    mock_ann = SimpleNamespace(
        sample=np.array([10, 50, 100]),
        symbol=["N", "p", "t"],
        subtype=np.array([0, 1, 0]),
        chan=np.array([0, 0, 0]),
        num=np.array([0, 0, 0]),
        aux_note=["", "wave_start", "wave_end"],
    )
    mock_rdann.return_value = mock_ann

    db_dir = tmp_path / QT_DATABASE
    db_dir.mkdir(parents=True)

    df = load_qt_annotations("sel100", annotator="pu0", data_dir=tmp_path)

    mock_rdann.assert_called_once_with(str(db_dir / "sel100"), "pu0")

    assert isinstance(df, pd.DataFrame)
    expected_cols = [
        "record_name", "annotator", "sample", "symbol",
        "subtype", "chan", "num", "aux_note",
    ]
    assert list(df.columns) == expected_cols
    assert len(df) == 3
    assert df["record_name"].unique().tolist() == ["sel100"]
    assert df["annotator"].unique().tolist() == ["pu0"]


@patch("ecg_analytics.physionet.wfdb.rdann")
def test_load_qt_annotations_defaults_to_pu0(mock_rdann, tmp_path):
    mock_rdann.return_value = SimpleNamespace(
        sample=np.array([1]),
        symbol=["N"],
        subtype=np.array([0]),
        chan=np.array([0]),
        num=np.array([0]),
        aux_note=[""],
    )
    db_dir = tmp_path / QT_DATABASE
    db_dir.mkdir(parents=True)

    load_qt_annotations("sel100", data_dir=tmp_path)

    mock_rdann.assert_called_once_with(str(db_dir / "sel100"), "pu0")

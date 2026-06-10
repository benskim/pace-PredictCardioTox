import pytest

from ecg_analytics.physionet import _validate_name


@pytest.mark.parametrize("name", ["sel100", "sel102", "sele0104", "rec-01", "my_record"])
def test_validate_name_accepts_safe_names(name: str) -> None:
    assert _validate_name(name, "record name") == name


@pytest.mark.parametrize(
    "name",
    [
        "../../etc/passwd",
        "../secret",
        "foo/bar",
        "foo\\bar",
        "",
        "sel 100",
        "sel.100",
        "name\x00null",
    ],
)
def test_validate_name_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match="record name must be non-empty"):
        _validate_name(name, "record name")

import pandas as pd
import pytest

from columns import ACTIVITY, CASE, TIME
from overview import activity_frequency, case_durations, overview
from validation import LogError, validate


def make_log(rows):
    df = pd.DataFrame(rows, columns=[CASE, ACTIVITY, TIME])
    df[TIME] = pd.to_datetime(df[TIME], utc=True)
    return df


def test_case_duration_ignores_row_order():
    df = make_log([
        ("A", "x", "2024-01-03 12:00"),
        ("A", "y", "2024-01-01 00:00"),
    ])
    assert case_durations(df)["days"].iloc[0] == 2.5


def test_mean_cycle_days():
    df = make_log([
        ("A", "x", "2024-01-01"), ("A", "y", "2024-01-02"),
        ("B", "x", "2024-01-01"), ("B", "y", "2024-01-04"),
    ])
    assert overview(df)["mean_cycle_days"] == 2


def test_cases_and_events_are_counted_separately():
    df = make_log([
        ("A", "x", "2024-01-01"), ("A", "x", "2024-01-02"), ("A", "y", "2024-01-03"),
        ("B", "x", "2024-01-01"),
    ])
    info = overview(df)
    assert info["cases"] == 2
    assert info["events"] == 4
    x = activity_frequency(df).set_index(ACTIVITY).loc["x"]
    assert x["events"] == 3
    assert x["cases"] == 2


def test_validate_requires_timestamp():
    df = make_log([("A", "x", "2024-01-01")]).drop(columns=[TIME])
    with pytest.raises(LogError):
        validate(df)


def test_validate_rejects_empty_log():
    with pytest.raises(LogError):
        validate(make_log([]))


def test_validate_reports_optional_columns():
    info = validate(make_log([("A", "x", "2024-01-01")]))
    assert info["has_lifecycle"] is False
    assert info["has_resource"] is False
import pytest

from ex1122 import eventually_follows, find_pair
from synthetic_log import LogBuilder

def test_cancelled_then_other_then_accepted_passes():
    log = LogBuilder().trace("C1", "O_Cancelled", "W_Call", "O_Accepted").build()
    result = eventually_follows(log)
    assert result["count"] == 1
    assert result["cases"] == ["C1"]
    assert result["evidence"][0]["i"] == 0
    assert result["evidence"][0]["j"] == 2


def test_accepted_then_cancelled_does_not_pass():
    log = LogBuilder().trace("C1", "O_Accepted", "O_Cancelled").build()
    result = eventually_follows(log)
    assert result["count"] == 0
    assert result["cases"] == []

def test_pattern_twice_in_one_case_counts_once():
    log = LogBuilder().trace(
        "C1", "O_Cancelled", "O_Accepted", "O_Cancelled", "O_Accepted"
    ).build()
    assert eventually_follows(log)["count"] == 1


def test_cancelled_and_accepted_in_different_cases_do_not_match():
    log = (LogBuilder()
           .trace("C1", "O_Cancelled")
           .trace("C2", "O_Accepted")
           .build())
    assert eventually_follows(log)["count"] == 0


def test_denominator_is_all_cases_and_percent():
    log = (LogBuilder()
           .trace("C1", "O_Cancelled", "O_Accepted")
           .trace("C2", "A_Submitted")
           .trace("C3", "O_Accepted")
           .trace("C4", "O_Cancelled")
           .build())
    result = eventually_follows(log)
    assert result["count"] == 1
    assert result["total"] == 4
    assert result["percent"] == pytest.approx(25.0)


def test_order_uses_timestamp_not_row_order():
    log = (LogBuilder()
           .case("C1")
           .event("O_Accepted", at="2024-01-05")
           .event("O_Cancelled", at="2024-01-01")
           .build())
    assert eventually_follows(log)["count"] == 1


def test_evidence_times_are_in_order():
    log = LogBuilder().trace("C1", "O_Cancelled", "W_Call", "O_Accepted").build()
    item = eventually_follows(log)["evidence"][0]
    assert item["first_time"] < item["second_time"]


def test_empty_log_has_zero_percent():
    log = LogBuilder().build()
    result = eventually_follows(log)
    assert result["count"] == 0
    assert result["total"] == 0
    assert result["percent"] == 0.0

def test_find_pair_positions():
    assert find_pair(["O_Cancelled", "X", "O_Accepted"]) == (0, 2)
    assert find_pair(["O_Accepted", "O_Cancelled"]) is None
    assert find_pair([]) is None

import pytest

from case_explorer import case_event_table, case_list, search_cases
from columns import CASE
from synthetic_log import LogBuilder


def sample():
    return (
        LogBuilder()
        .case("Application_1").event("A_Submitted", at="2024-01-01").event("O_Accepted", at="2024-01-03")
        .case("Application_2").event("A_Submitted", at="2024-01-02")
        .build()
    )


def test_case_list_one_row_per_case():
    table = case_list(sample())
    assert len(table) == 2
    row = table[table[CASE] == "Application_1"].iloc[0]
    assert row["events"] == 2
    assert row["start"] < row["end"]


def test_search_is_partial_and_case_insensitive():
    table = case_list(sample())
    assert list(search_cases(table, "application_2")[CASE]) == ["Application_2"]
    assert len(search_cases(table, "APPLICATION")) == 2
    assert len(search_cases(table, "")) == 2
    assert len(search_cases(table, "xyz")) == 0


def test_event_table_has_four_columns_in_time_order():
    events = case_event_table(sample(), "Application_1")
    assert list(events.columns) == ["time", "activity", "lifecycle", "resource"]
    assert list(events["activity"]) == ["A_Submitted", "O_Accepted"]


def test_event_table_sorted_by_time_not_row_order():
    log = (
        LogBuilder()
        .case("C1").event("late", at="2024-01-05").event("early", at="2024-01-01")
        .build()
    )
    assert list(case_event_table(log, "C1")["activity"]) == ["early", "late"]


def test_event_table_only_contains_selected_case():
    events = case_event_table(sample(), "Application_2")
    assert len(events) == 1


def test_empty_resource_becomes_empty_text():
    log = LogBuilder().case("C1").event("A", resource=None).build()
    events = case_event_table(log, "C1")
    assert events["resource"].iloc[0] == ""


def test_unknown_case_gives_empty_table():
    assert len(case_event_table(sample(), "tidak_ada")) == 0

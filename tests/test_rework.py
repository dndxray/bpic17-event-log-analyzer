import numpy as np

from columns import CASE
from rework import TARGET, repeated_complete, same_resource_complete
from synthetic_log import LogBuilder


def test_scheduled_twice_complete_once_not_in_1115():
    log = (LogBuilder().case("C1")
           .event(TARGET, "schedule").event(TARGET, "schedule")
           .event(TARGET, "complete").build())
    assert repeated_complete(log).count == 0


def test_two_complete_different_resource_passes_1115_not_1118():
    log = (LogBuilder().case("C1")
           .event(TARGET, resource="u1").event(TARGET, resource="u2").build())
    assert repeated_complete(log).case_ids == ["C1"]
    assert same_resource_complete(log).count == 0


def test_two_complete_same_resource_passes_both():
    log = (LogBuilder().case("C1")
           .event(TARGET, resource="u1").event(TARGET, resource="u1").build())
    assert repeated_complete(log).count == 1
    r = same_resource_complete(log)
    assert r.count == 1
    assert r.cases.iloc[0]["resource"] == "u1"
    assert r.cases.iloc[0]["n_by_resource"] == 2


def test_missing_resource_is_not_the_same_resource():
    log = (LogBuilder().case("C1")
           .event(TARGET, resource=None).event(TARGET, resource=None)
           .case("C2").event(TARGET, resource="").event(TARGET, resource="")
           .case("C3").event(TARGET, resource=np.nan).event(TARGET, resource=np.nan)
           .build())
    assert repeated_complete(log).count == 3      # tetap lolos 11.15
    assert same_resource_complete(log).count == 0  # tapi tidak 11.18


def test_case_with_three_complete_counts_once():
    log = LogBuilder().trace("C1", TARGET, TARGET, TARGET, resource="u1").build()
    assert repeated_complete(log).count == 1
    assert same_resource_complete(log).count == 1
    assert same_resource_complete(log).cases.iloc[0]["n_by_resource"] == 3


def test_abort_and_start_are_ignored():
    log = (LogBuilder().case("C1")
           .event(TARGET, "start").event(TARGET, "ate_abort")
           .event(TARGET, "complete").event(TARGET, "start").build())
    assert repeated_complete(log).count == 0


def test_other_activity_complete_twice_is_ignored():
    log = LogBuilder().trace("C1", "W_Call after offers", "W_Call after offers").build()
    assert repeated_complete(log).count == 0


def test_denominator_is_all_cases():
    log = (LogBuilder()
           .trace("C1", TARGET, TARGET)
           .trace("C2", "A_Submitted")
           .trace("C3", TARGET)
           .build())
    r = repeated_complete(log)
    assert (r.count, r.total_cases) == (1, 3)


def test_two_resources_each_twice_counts_case_once():
    log = (LogBuilder().case("C1")
           .event(TARGET, resource="u1").event(TARGET, resource="u1")
           .event(TARGET, resource="u2").event(TARGET, resource="u2").build())
    r = same_resource_complete(log)
    assert r.count == 1
    assert len(r.cases) == 2  # dua baris (case, resource), satu case


def test_1118_is_subset_of_1115():
    log = (LogBuilder()
           .case("C1").event(TARGET, resource="u1").event(TARGET, resource="u1")
           .case("C2").event(TARGET, resource="u1").event(TARGET, resource="u2")
           .case("C3").event(TARGET, resource="u1").build())
    assert set(same_resource_complete(log).case_ids) <= set(repeated_complete(log).case_ids)


def test_name_match_ignores_case_of_letters():
    log = LogBuilder().trace("C1", "W_Assess Potential Fraud", "W_Assess potential fraud").build()
    assert repeated_complete(log).count == 1


def test_same_timestamp_does_not_crash_and_keeps_file_order():
    log = (LogBuilder().case("C1")
           .event(TARGET, resource="u2", at="2024-01-01")
           .event(TARGET, resource="u1", at="2024-01-01").build())
    ev = repeated_complete(log).evidence
    assert list(ev["org:resource"]) == ["u2", "u1"]


def test_filter_does_not_mutate_input_log():
    log = LogBuilder().trace("C1", TARGET, TARGET).build()
    before = log.copy()
    repeated_complete(log)
    same_resource_complete(log)
    assert log.equals(before)

from pathlib import Path

import pytest

from columns import CASE
from exercise_11_7 import (
    analyze_exercise_11_7, case_events, cases_containing, cases_ending_with,
    order_events, overlap_accepted_refused, summary_frame,
)
from synthetic_log import LogBuilder


def by_code(df):
    return {r.code: r for r in analyze_exercise_11_7(df)}


def ids(result):
    return set(result.cases[CASE])


# --- skenario wajib dari tabel pengujian instruksi proyek -------------------

def test_accepted_twice_counts_case_once():
    log = (LogBuilder()
           .trace("C1", "O_Accepted", "W_X", "O_Accepted")
           .trace("C2", "A_Submitted")
           .build())
    c = by_code(log)["11.7 C"]
    assert c.count == 1
    assert ids(c) == {"C1"}
    assert c.cases["bukti"].iloc[0] == "2x O_Accepted"


def test_cancelled_in_the_middle_is_not_canceled_case():
    log = LogBuilder().trace("C1", "A_Submitted", "O_Cancelled", "W_Call", "O_Create Offer").build()
    e = by_code(log)["11.7 E"]
    assert e.count == 0
    assert len(cases_containing(log, "O_Cancelled")) == 1  # memang pernah muncul


def test_cancelled_last_is_canceled_case():
    log = LogBuilder().trace("C1", "A_Submitted", "O_Cancelled").build()
    e = by_code(log)["11.7 E"]
    assert ids(e) == {"C1"}
    assert "O_Cancelled" in e.cases["bukti"].iloc[0]


def test_refused_and_accepted_pass_both_contains_filters():
    log = LogBuilder().trace("C1", "O_Refused", "O_Accepted").build()
    r = by_code(log)
    assert ids(r["11.7 C"]) == {"C1"}
    assert ids(r["11.7 D"]) == {"C1"}
    assert overlap_accepted_refused(log) == 1


# --- cycle time -------------------------------------------------------------

def test_a_and_b_use_all_cases():
    log = (LogBuilder()
           .case("C1").event("x", at="2024-01-01").event("y", at="2024-01-03")
           .case("C2").event("x", at="2024-01-01").event("y", at="2024-01-05")
           .build())
    r = by_code(log)
    assert r["11.7 A"].count == 2
    assert r["11.7 B"].mean_days == pytest.approx(3.0)


def test_cycle_time_keeps_whole_case_not_only_matching_event():
    # O_Accepted di hari ke-1, tetapi case berlanjut sampai hari ke-11.
    log = (LogBuilder()
           .case("C1").event("A", at="2024-01-01").event("O_Accepted", at="2024-01-02")
           .event("W", at="2024-01-11")
           .build())
    c = by_code(log)["11.7 C"]
    assert c.mean_days == pytest.approx(10.0)


def test_group_mean_only_over_selected_cases():
    log = (LogBuilder()
           .case("C1").event("A", at="2024-01-01").event("O_Accepted", at="2024-01-03")
           .case("C2").event("A", at="2024-01-01").event("O_Accepted", at="2024-01-07")
           .case("C3").event("A", at="2024-01-01").event("B", at="2024-03-01")
           .build())
    r = by_code(log)
    assert r["11.7 C"].count == 2
    assert r["11.7 C"].mean_days == pytest.approx(4.0)
    assert r["11.7 C"].total_cases == 3


def test_empty_group_has_nan_mean_and_zero_count():
    log = LogBuilder().trace("C1", "A_Submitted").build()
    d = by_code(log)["11.7 D"]
    assert d.count == 0
    assert d.mean_days != d.mean_days  # NaN


# --- urutan event -----------------------------------------------------------

def test_endpoint_uses_timestamp_not_row_order():
    # Baris O_Cancelled ditulis terakhir di file, tetapi waktunya paling awal.
    log = (LogBuilder()
           .case("C1").event("W_Call", at="2024-01-05").event("O_Cancelled", at="2024-01-01")
           .build())
    assert by_code(log)["11.7 E"].count == 0


def test_equal_timestamps_fall_back_to_row_order():
    log = (LogBuilder()
           .case("C1").event("A", at="2024-01-01").event("O_Cancelled", at="2024-01-02")
           .event("W_Call", at="2024-01-02")
           .case("C2").event("A", at="2024-01-01").event("W_Call", at="2024-01-02")
           .event("O_Cancelled", at="2024-01-02")
           .build())
    assert set(cases_ending_with(log, "O_Cancelled")) == {"C2"}


def test_order_events_is_stable_across_interleaved_rows():
    log = (LogBuilder()
           .case("C1").event("a1", at="2024-01-01")
           .case("C2").event("b1", at="2024-01-01")
           .case("C1").event("a2", at="2024-01-02")
           .build())
    assert list(case_events(log, "C1")["concept:name"]) == ["a1", "a2"]
    assert list(order_events(log)[CASE]) == ["C1", "C1", "C2"]


# --- keluaran untuk ekspor / GUI -------------------------------------------

def test_summary_frame_has_denominator_and_rule():
    log = LogBuilder().trace("C1", "O_Accepted").trace("C2", "O_Refused").build()
    s = summary_frame(analyze_exercise_11_7(log))
    assert list(s["kode"]) == ["11.7 A", "11.7 B", "11.7 C", "11.7 D", "11.7 E"]
    assert (s["denominator_case"] == 2).all()
    assert s["aturan"].str.len().min() > 0


def test_cases_and_events_not_mixed():
    log = (LogBuilder()
           .trace("C1", "O_Accepted", "O_Accepted", "O_Accepted")
           .build())
    r = by_code(log)
    assert r["11.7 A"].count == 1          # 1 case, bukan 3 event
    assert r["11.7 C"].count == 1


# --- uji integrasi pada BPIC17 asli (dilewati bila file tidak ada) ----------

DATA = Path(__file__).resolve().parent.parent / "data" / "BPI_Challenge_2017.xes.gz"


@pytest.mark.skipif(not DATA.exists(), reason="dataset BPIC17 tidak ada di data/")
def test_bpic17_invariants():
    from loader import load_cached
    df, _ = load_cached(DATA)
    r = by_code(df)
    assert r["11.7 A"].count == df[CASE].nunique()
    assert r["11.7 C"].count <= df[df["concept:name"] == "O_Accepted"].shape[0]
    assert r["11.7 E"].count <= len(cases_containing(df, "O_Cancelled"))
    for item in r.values():
        assert item.count <= item.total_cases

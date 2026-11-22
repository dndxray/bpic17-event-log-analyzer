from pathlib import Path

import pandas as pd

from export import case_rows, collect_results, export_all, summary_rows
from rework import TARGET
from synthetic_log import LogBuilder


def sample():
    return (
        LogBuilder()
        .case("C1")
        .event("A_Submitted", at="2024-01-01").event("O_Accepted", at="2024-01-03")
        .case("C2")
        .event("O_Refused", at="2024-01-01").event("O_Accepted", at="2024-01-02")
        .case("C3")
        .event("O_Cancelled", at="2024-01-01")
        .event("W_Call", at="2024-01-02")
        .event("O_Accepted", at="2024-01-03")
        .case("C4")
        .event(TARGET, resource="u1", at="2024-01-01")
        .event(TARGET, resource="u1", at="2024-01-02")
        .case("C5")
        .event(TARGET, resource="u1", at="2024-01-01")
        .event(TARGET, resource="u2", at="2024-01-02")
        .build()
    )


def by_code(summary):
    return summary.set_index("kode")


def test_summary_contains_every_exercise():
    summary = summary_rows(sample())
    assert list(summary["kode"]) == [
        "11.7 A", "11.7 B", "11.7 C", "11.7 D", "11.7 E",
        "11.15", "11.18", "11.22",
    ]
    assert (summary["denominator_case"] == 5).all()


def test_summary_counts_match_the_analysis():
    summary = by_code(summary_rows(sample()))
    assert summary.loc["11.7 A", "jumlah_case"] == 5
    assert summary.loc["11.7 C", "jumlah_case"] == 3
    assert summary.loc["11.7 D", "jumlah_case"] == 1
    assert summary.loc["11.7 E", "jumlah_case"] == 0
    assert summary.loc["11.15", "jumlah_case"] == 2
    assert summary.loc["11.18", "jumlah_case"] == 1
    assert summary.loc["11.22", "jumlah_case"] == 1
    assert summary.loc["11.22", "persentase"] == 20.0


def test_case_rows_cover_exercises_with_matching_cases():
    rows = case_rows(sample())
    assert set(rows["kode"]) == {
        "11.7 A", "11.7 B", "11.7 C", "11.7 D",
        "11.15", "11.18", "11.22",
    }
    assert list(rows.columns) == ["kode", "case", "start", "end", "days", "keterangan"]


def test_case_rows_1118_keeps_resource_detail():
    rows = case_rows(sample())
    detail = rows[(rows["kode"] == "11.18") & (rows["case"] == "C4")].iloc[0]
    assert "resource=u1" in detail["keterangan"]
    assert "n=2" in detail["keterangan"]


def test_collect_results_reuses_all_exercises():
    results = collect_results(sample())
    assert len(results["exercise_11_7"]) == 5
    assert results["exercise_11_15"].count == 2
    assert results["exercise_11_18"].count == 1
    assert results["exercise_11_22"]["count"] == 1


def test_export_all_writes_all_csv_files(tmp_path):
    paths = export_all(sample(), tmp_path)
    names = {path.name for path in paths}
    assert names == {
        "ringkasan_jawaban.csv", "daftar_case.csv",
        "bukti_11_15.csv", "bukti_11_18.csv", "bukti_11_22.csv",
    }
    for path in paths:
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0


def test_exported_summary_is_readable_and_complete(tmp_path):
    export_all(sample(), tmp_path)
    summary = pd.read_csv(tmp_path / "ringkasan_jawaban.csv")
    assert len(summary) == 8
    assert "11.22" in set(summary["kode"])
    cases = pd.read_csv(tmp_path / "daftar_case.csv")
    assert "C4" in set(cases["case"])

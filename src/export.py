"""Ringkasan jawaban dan ekspor CSV untuk seluruh latihan.

Modul ini sengaja tidak bergantung pada Tkinter supaya mudah diuji. Semua angka
dihitung ulang dari DataFrame log aktif, bukan ditulis manual.
"""
from pathlib import Path

import pandas as pd

from columns import CASE
from ex1122 import eventually_follows
from exercise_11_7 import analyze_exercise_11_7
from overview import case_durations
from rework import repeated_complete, same_resource_complete

SECONDS_PER_DAY = 86400
SUMMARY_COLUMNS = [
    "kode", "pertanyaan", "aturan", "jumlah_case", "denominator_case",
    "persentase", "mean_cycle_time_hari",
]
CASE_COLUMNS = ["kode", "case", "start", "end", "days", "keterangan"]


def _percent(count, total):
    return count / total * 100 if total else 0.0


def _mean_days(durations, case_ids):
    subset = durations[durations[CASE].isin(case_ids)]
    return subset["days"].mean() if len(subset) else float("nan")


def collect_results(df):
    """Hitung semua latihan satu kali, lalu dipakai ulang oleh ringkasan/ekspor."""
    return {
        "exercise_11_7": analyze_exercise_11_7(df),
        "exercise_11_15": repeated_complete(df),
        "exercise_11_18": same_resource_complete(df),
        "exercise_11_22": eventually_follows(df),
        "durations": case_durations(df),
    }


def _summary_row(code, question, rule, count, total, mean_days):
    return {
        "kode": code,
        "pertanyaan": question,
        "aturan": rule,
        "jumlah_case": count,
        "denominator_case": total,
        "persentase": _percent(count, total),
        "mean_cycle_time_hari": mean_days,
    }


def summary_rows(df, results=None):
    """Satu baris ringkasan per jawaban latihan (11.7 A-E, 11.15, 11.18, 11.22)."""
    results = results or collect_results(df)
    durations = results["durations"]
    total = df[CASE].nunique()

    rows = []
    for result in results["exercise_11_7"]:
        rows.append(_summary_row(
            result.code, result.question, result.rule, result.count,
            result.total_cases, result.mean_days,
        ))

    for code, question, result in [
        ("11.15", "Case dengan aktivitas target complete minimal 2x",
         results["exercise_11_15"]),
        ("11.18", "Case dengan aktivitas target complete minimal 2x oleh resource sama",
         results["exercise_11_18"]),
    ]:
        rows.append(_summary_row(
            code, question, result.rule, result.count, result.total_cases,
            _mean_days(durations, result.case_ids),
        ))

    follows = results["exercise_11_22"]
    gaps = [
        (item["second_time"] - item["first_time"]).total_seconds() / SECONDS_PER_DAY
        for item in follows["evidence"]
    ]
    rows.append(_summary_row(
        "11.22",
        "Case dengan O_Cancelled lalu O_Accepted (eventually follows, i < j)",
        "Posisi i < j: O_Cancelled muncul lebih dulu daripada O_Accepted pada trace yang sama",
        follows["count"], follows["total"], sum(gaps) / len(gaps) if gaps else float("nan"),
    ))
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def _case_meta(durations):
    return {
        case: (start, end, days)
        for case, start, end, days in durations.itertuples(index=False)
    }


def case_rows(df, results=None):
    """Gabungan daftar case semua latihan dengan kolom yang seragam."""
    results = results or collect_results(df)
    meta = _case_meta(results["durations"])
    rows = []

    for result in results["exercise_11_7"]:
        for case, start, end, days, evidence in result.cases.itertuples(index=False):
            rows.append({
                "kode": result.code, "case": case, "start": start, "end": end,
                "days": days, "keterangan": evidence,
            })

    for case, n_complete in results["exercise_11_15"].cases.itertuples(index=False):
        start, end, days = meta.get(case, (pd.NaT, pd.NaT, float("nan")))
        rows.append({
            "kode": "11.15", "case": case, "start": start, "end": end,
            "days": days, "keterangan": f"n_complete={n_complete}",
        })

    for case, resource, n_by_resource in results["exercise_11_18"].cases.itertuples(index=False):
        start, end, days = meta.get(case, (pd.NaT, pd.NaT, float("nan")))
        rows.append({
            "kode": "11.18", "case": case, "start": start, "end": end,
            "days": days, "keterangan": f"resource={resource}; n={n_by_resource}",
        })

    for item in results["exercise_11_22"]["evidence"]:
        gap = (item["second_time"] - item["first_time"]).total_seconds() / SECONDS_PER_DAY
        rows.append({
            "kode": "11.22", "case": item["case"], "start": item["first_time"],
            "end": item["second_time"], "days": gap,
            "keterangan": f"posisi {item['i']} -> {item['j']}",
        })

    return pd.DataFrame(rows, columns=CASE_COLUMNS)


def evidence_frames(results):
    """Tabel bukti event untuk 11.15, 11.18, dan pasangan 11.22."""
    follows = pd.DataFrame([
        {
            CASE: item["case"], "i": item["i"], "j": item["j"],
            "first_time": item["first_time"], "second_time": item["second_time"],
        }
        for item in results["exercise_11_22"]["evidence"]
    ], columns=[CASE, "i", "j", "first_time", "second_time"])
    return {
        "bukti_11_15": results["exercise_11_15"].evidence,
        "bukti_11_18": results["exercise_11_18"].evidence,
        "bukti_11_22": follows,
    }


def _write(frame, path):
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def export_all(df, out_dir, results=None):
    """Tulis ringkasan, daftar case, dan bukti ke folder. Mengembalikan daftar file."""
    results = results or collect_results(df)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written = [
        _write(summary_rows(df, results), out_dir / "ringkasan_jawaban.csv"),
        _write(case_rows(df, results), out_dir / "daftar_case.csv"),
    ]
    for name, frame in evidence_frames(results).items():
        written.append(_write(frame, out_dir / f"{name}.csv"))
    return written

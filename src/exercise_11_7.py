"""Exercise 11.7 (A-E): jumlah case dan rata-rata cycle time per kelompok.

Semua angka dihitung dari DataFrame log (hasil pm4py.read_xes). Tidak ada angka
jawaban yang ditulis langsung di kode.

Aturan inti (sesuai instruksi proyek):
- Satu case dihitung SATU kali, berapa kali pun event pemicunya muncul.
- Cycle time = timestamp event terakhir - timestamp event pertama, dari SEMUA event
  case tersebut. Filter hanya memilih case; event tidak pernah dibuang sebelum
  durasi dihitung.
- "Contains" (C, D) dan "endpoint" (E) adalah dua aturan berbeda.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from columns import ACTIVITY, CASE, LIFECYCLE, RESOURCE, TIME
from overview import case_durations

ACCEPTED = "O_Accepted"
REFUSED = "O_Refused"
CANCELLED = "O_Cancelled"

POS = "_pos"  # posisi baris asli, dipakai sebagai pemutus seri timestamp


@dataclass
class GroupResult:
    code: str          # "11.7 A" ... "11.7 E"
    question: str
    rule: str          # aturan filter dalam kalimat, ditampilkan di GUI/ekspor
    count: int         # jumlah case lolos filter
    total_cases: int   # denominator (seluruh case di log aktif)
    mean_days: float   # rata-rata cycle time kelompok (hari); NaN jika kelompok kosong
    cases: pd.DataFrame  # kolom: case, start, end, days, bukti


def order_events(df):
    """Urutan event dalam trace: timestamp naik; bila sama, urutan baris di file.

    Urutan baris di file dipakai sebagai pemutus seri karena itu urutan aktual
    yang direkam log. Sort memakai kolom _pos agar hasilnya pasti deterministik.
    """
    ordered = df.assign(**{POS: np.arange(len(df))})
    ordered = ordered.sort_values([CASE, TIME, POS])
    return ordered.drop(columns=POS)


def cases_containing(df, activity):
    """Case yang memuat minimal satu event dengan concept:name == activity."""
    return pd.Index(df.loc[df[ACTIVITY] == activity, CASE].unique())


def cases_ending_with(df, activity):
    """Case yang event TERAKHIR-nya (menurut order_events) adalah activity."""
    last = order_events(df).drop_duplicates(CASE, keep="last")
    return pd.Index(last.loc[last[ACTIVITY] == activity, CASE])


def _build(code, question, rule, case_ids, durations, total, evidence):
    cases = durations[durations[CASE].isin(case_ids)].copy()
    cases["bukti"] = cases[CASE].map(evidence).fillna("")
    mean_days = cases["days"].mean() if len(cases) else float("nan")
    return GroupResult(code, question, rule, len(cases), total, mean_days,
                       cases.reset_index(drop=True))


def _contain_evidence(df, activity):
    counts = df.loc[df[ACTIVITY] == activity].groupby(CASE).size()
    return counts.map(lambda n: f"{n}x {activity}")


def _endpoint_evidence(df, activity):
    last = order_events(df).drop_duplicates(CASE, keep="last").set_index(CASE)
    last = last[last[ACTIVITY] == activity]
    return last[TIME].dt.strftime("%Y-%m-%d %H:%M:%S").map(
        lambda t: f"event terakhir = {activity} @ {t}")


def analyze_exercise_11_7(df):
    """Hitung kelima jawaban 11.7 A-E. Mengembalikan list GroupResult (urutan A..E)."""
    durations = case_durations(df)
    all_ids = pd.Index(durations[CASE])
    total = len(all_ids)

    return [
        _build("11.7 A", "Jumlah keseluruhan case",
               "Semua case unik pada log aktif",
               all_ids, durations, total, {}),
        _build("11.7 B", "Rata-rata cycle time seluruh case",
               "Semua case; durasi = event terakhir - event pertama",
               all_ids, durations, total, {}),
        _build("11.7 C", "Successful cases",
               f"Contains: minimal satu event {ACCEPTED}",
               cases_containing(df, ACCEPTED), durations, total,
               _contain_evidence(df, ACCEPTED)),
        _build("11.7 D", "Unsuccessful cases",
               f"Contains: minimal satu event {REFUSED}",
               cases_containing(df, REFUSED), durations, total,
               _contain_evidence(df, REFUSED)),
        _build("11.7 E", "Canceled cases",
               f"Endpoint: event TERAKHIR pada trace = {CANCELLED}",
               cases_ending_with(df, CANCELLED), durations, total,
               _endpoint_evidence(df, CANCELLED)),
    ]


def overlap_accepted_refused(df):
    """Jumlah case yang memuat O_Accepted DAN O_Refused (C dan D tidak eksklusif)."""
    return len(cases_containing(df, ACCEPTED).intersection(cases_containing(df, REFUSED)))


def summary_frame(results):
    """Ringkasan A-E sebagai DataFrame (siap diekspor ke CSV oleh Orang 5)."""
    return pd.DataFrame([{
        "kode": r.code,
        "pertanyaan": r.question,
        "aturan": r.rule,
        "jumlah_case": r.count,
        "denominator_case": r.total_cases,
        "mean_cycle_time_hari": r.mean_days,
    } for r in results])


def case_list_frame(result):
    """Daftar case terpilih satu soal (kolom: case, start, end, days, bukti)."""
    return result.cases


def case_events(df, case_id):
    """Urutan event satu case (untuk tombol 'buka rincian case')."""
    ordered = order_events(df[df[CASE] == case_id])
    cols = [c for c in (TIME, ACTIVITY, LIFECYCLE, RESOURCE) if c in ordered.columns]
    return ordered[cols].reset_index(drop=True)

"""Exercise 11.15 dan 11.18: aktivitas fraud yang diselesaikan berulang kali.

Aturan (sesuai instruksi proyek):
- Hanya event berlifecycle "complete" yang dihitung. schedule/start/suspend/resume/
  ate_abort/withdraw DIABAIKAN. Event tidak pernah dibuang dari log asli; filter ini
  hanya dipakai untuk menghitung.
- 11.15: case lolos bila jumlah complete aktivitas target >= 2.
- 11.18: case lolos bila >= 2 complete dilakukan resource YANG SAMA. Resource kosong
  (NaN / string kosong) tidak pernah dianggap resource yang sama.
- Satu case dihitung satu kali, berapa pun banyaknya pengulangan.
- Nama aktivitas dicocokkan tanpa membedakan huruf besar/kecil. Di BPIC17 nama aslinya
  "W_Assess potential fraud" sedangkan PDF soal menulis "W_Assess Potential Fraud".
"""
from dataclasses import dataclass

import pandas as pd

from columns import ACTIVITY, CASE, LIFECYCLE, RESOURCE, TIME
from exercise_11_7 import order_events

TARGET = "W_Assess potential fraud"
COMPLETE = "complete"
MIN_REPEAT = 2

EVIDENCE_COLUMNS = [CASE, ACTIVITY, LIFECYCLE, RESOURCE, TIME]


@dataclass
class ReworkResult:
    code: str             # "11.15" / "11.18"
    rule: str             # aturan dalam kalimat, ditampilkan di GUI/ekspor
    count: int            # jumlah case lolos (unik)
    total_cases: int      # denominator: seluruh case di log aktif
    cases: pd.DataFrame   # 11.15: case, n_complete | 11.18: case, resource, n_by_resource
    evidence: pd.DataFrame  # event complete yang terhitung (urutan trace)

    @property
    def case_ids(self):
        return list(dict.fromkeys(self.cases[CASE]))


def _norm(series):
    return series.astype("string").str.strip().str.casefold()


def complete_events(df, activity=TARGET):
    """Event aktivitas target berlifecycle complete, dalam urutan trace."""
    mask = (_norm(df[ACTIVITY]) == activity.strip().casefold()) & (
        _norm(df[LIFECYCLE]) == COMPLETE)
    return order_events(df.loc[mask.fillna(False)])[EVIDENCE_COLUMNS]


def repeated_complete(df, activity=TARGET, minimum=MIN_REPEAT):
    """Exercise 11.15: case dengan >= `minimum` complete aktivitas target."""
    events = complete_events(df, activity)
    counts = events.groupby(CASE, sort=False).size()
    hit = counts[counts >= minimum].rename("n_complete").reset_index()
    rule = (f"{activity} dengan lifecycle '{COMPLETE}' muncul >= {minimum}x dalam satu case "
            f"(event non-complete diabaikan)")
    return ReworkResult("11.15", rule, len(hit), df[CASE].nunique(), hit,
                        events[events[CASE].isin(hit[CASE])].reset_index(drop=True))


def same_resource_complete(df, activity=TARGET, minimum=MIN_REPEAT):
    """Exercise 11.18: case dengan >= `minimum` complete oleh resource yang sama."""
    events = complete_events(df, activity)
    named = events[events[RESOURCE].notna() & (events[RESOURCE].astype("string").str.strip() != "")]
    counts = named.groupby([CASE, RESOURCE], sort=False).size()
    hit = counts[counts >= minimum].rename("n_by_resource").reset_index()
    hit = hit.rename(columns={RESOURCE: "resource"})
    keys = set(zip(hit[CASE], hit["resource"]))
    in_hit = [(c, r) in keys for c, r in zip(named[CASE], named[RESOURCE])]
    rule = (f"{activity} lifecycle '{COMPLETE}' diselesaikan >= {minimum}x oleh resource yang "
            f"sama dalam satu case (resource kosong tidak dihitung)")
    return ReworkResult("11.18", rule, hit[CASE].nunique(), df[CASE].nunique(), hit,
                        named[in_hit].reset_index(drop=True))


if __name__ == "__main__":
    import sys

    from loader import load_cached

    df, _ = load_cached(sys.argv[1] if len(sys.argv) > 1 else "BPI Challenge 2017.xes")
    for fn in (repeated_complete, same_resource_complete):
        r = fn(df)
        print(f"[{r.code}] {r.count} dari {r.total_cases} case | {r.rule}")
        print(r.cases.head(), "\n")

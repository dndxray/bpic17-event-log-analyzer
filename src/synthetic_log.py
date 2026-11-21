"""Builder log sintetis untuk unit test (dipakai bersama seluruh anggota tim).

Contoh:
    log = (LogBuilder()
           .trace("C1", "A_Submitted", "O_Accepted")
           .case("C2").event("O_Refused", resource="u2").event("O_Accepted", at="2024-02-01")
           .build())

Hasilnya DataFrame berkolom sama dengan pm4py.read_xes:
case:concept:name, concept:name, time:timestamp (UTC), lifecycle:transition, org:resource.

Urutan baris = urutan pemanggilan .event(). Jika `at` tidak diisi, timestamp otomatis
naik 1 jam per event (global), sehingga urutan baris == urutan waktu.
"""
import pandas as pd

from columns import ACTIVITY, CASE, LIFECYCLE, RESOURCE, TIME

DEFAULT_START = "2024-01-01 00:00"


class LogBuilder:
    def __init__(self, start=DEFAULT_START):
        self._clock = pd.Timestamp(start, tz="UTC")
        self._current = None
        self._rows = []

    def case(self, case_id):
        self._current = case_id
        return self

    def event(self, activity, lifecycle="complete", resource="user1", at=None):
        if self._current is None:
            raise ValueError("Panggil .case(id) sebelum .event()")
        if at is None:
            self._clock += pd.Timedelta(hours=1)
            stamp = self._clock
        else:
            stamp = pd.Timestamp(at)
            stamp = stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")
        self._rows.append((self._current, activity, stamp, lifecycle, resource))
        return self

    def trace(self, case_id, *activities, **event_kwargs):
        """Pintasan: satu case dengan beberapa aktivitas berurutan."""
        self.case(case_id)
        for activity in activities:
            self.event(activity, **event_kwargs)
        return self

    def build(self):
        df = pd.DataFrame(self._rows, columns=[CASE, ACTIVITY, TIME, LIFECYCLE, RESOURCE])
        df[TIME] = pd.to_datetime(df[TIME], utc=True)
        return df

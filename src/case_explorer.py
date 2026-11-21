import pandas as pd

from columns import ACTIVITY, CASE, LIFECYCLE, RESOURCE, TIME

CASE_LIST_COLUMNS = [CASE, "events", "start", "end"]
EVENT_COLUMNS = ["time", "activity", "lifecycle", "resource"]


def case_list(df):
    """Satu baris per case: jumlah event, waktu mulai, waktu selesai."""
    grouped = df.groupby(CASE, sort=False)[TIME]
    table = pd.DataFrame(
        {
            "events": grouped.size(),
            "start": grouped.min(),
            "end": grouped.max(),
        }
    ).reset_index()
    return table.sort_values("start", kind="stable").reset_index(drop=True)


def search_cases(table, text):
    """Saring daftar case berdasarkan sebagian case ID (tanpa membedakan huruf besar/kecil)."""
    text = (text or "").strip().lower()
    if not text:
        return table
    return table[table[CASE].astype(str).str.lower().str.contains(text, regex=False)]


def case_event_table(df, case_id):
    """Event satu case, terurut waktu (urutan asli dipertahankan bila waktunya sama)."""
    events = df[df[CASE] == case_id].sort_values(TIME, kind="stable")
    result = pd.DataFrame(
        {
            "time": events[TIME].to_numpy(),
            "activity": events[ACTIVITY].to_numpy(),
            "lifecycle": events[LIFECYCLE].to_numpy() if LIFECYCLE in events else "",
            "resource": events[RESOURCE].to_numpy() if RESOURCE in events else "",
        }
    )
    result["time"] = pd.to_datetime(result["time"], utc=True)
    for column in ("lifecycle", "resource"):
        result[column] = result[column].fillna("").astype(str)
    return result[EVENT_COLUMNS]

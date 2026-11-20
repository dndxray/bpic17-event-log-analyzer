from pathlib import Path

from columns import ACTIVITY, CASE, LIFECYCLE, RESOURCE, TIME

REQUIRED = [CASE, ACTIVITY, TIME]


class LogError(Exception):
    pass


def check_file(path):
    path = Path(path)
    if not path.exists():
        raise LogError(f"File tidak ditemukan: {path}")
    if not path.name.lower().endswith((".xes", ".xes.gz")):
        raise LogError("File harus berformat .xes atau .xes.gz")


def validate(df):
    missing = [col for col in REQUIRED if col not in df.columns]
    if missing:
        raise LogError("Atribut wajib tidak ada: " + ", ".join(missing))
    if df.empty:
        raise LogError("Log tidak berisi event")
    return {
        "events": len(df),
        "cases": df[CASE].nunique(),
        "has_lifecycle": LIFECYCLE in df.columns,
        "has_resource": RESOURCE in df.columns,
    }
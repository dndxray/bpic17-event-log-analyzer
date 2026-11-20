import sys
import time
from pathlib import Path

import pandas as pd
import pm4py

from validation import LogError, check_file, validate


def load_event_log(path):
    check_file(path)
    start = time.perf_counter()
    try:
        df = pm4py.read_xes(str(path))
    except Exception as exc:
        raise LogError(f"Gagal membaca log: {exc}") from exc
    return df, time.perf_counter() - start


def load_cached(path):
    check_file(path)
    path = Path(path)
    cache = path.parent / (path.name + ".pkl")
    if cache.exists() and cache.stat().st_mtime >= path.stat().st_mtime:
        start = time.perf_counter()
        return pd.read_pickle(cache), time.perf_counter() - start
    df, elapsed = load_event_log(path)
    df.to_pickle(cache)
    return df, elapsed


if __name__ == "__main__":
    try:
        df, elapsed = load_cached(sys.argv[1])
        print(validate(df), f"{elapsed:.1f}s")
    except LogError as err:
        print(f"Error: {err}")
        sys.exit(1)
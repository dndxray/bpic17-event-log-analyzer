import sys

import pandas as pd

from columns import ACTIVITY, CASE, TIME

SECONDS_PER_DAY = 86400


def case_durations(df):
    grouped = df.groupby(CASE)[TIME]
    result = pd.DataFrame({"start": grouped.min(), "end": grouped.max()})
    result["days"] = (result["end"] - result["start"]).dt.total_seconds() / SECONDS_PER_DAY
    return result.reset_index()


def activity_frequency(df):
    grouped = df.groupby(ACTIVITY)
    result = pd.DataFrame({"events": grouped.size(), "cases": grouped[CASE].nunique()})
    return result.sort_values("events", ascending=False).reset_index()


def overview(df):
    durations = case_durations(df)
    return {
        "cases": df[CASE].nunique(),
        "events": len(df),
        "first_event": df[TIME].min(),
        "last_event": df[TIME].max(),
        "mean_cycle_days": durations["days"].mean(),
    }


if __name__ == "__main__":
    from loader import load_cached

    df, _ = load_cached(sys.argv[1])
    for key, value in overview(df).items():
        print(key, value)
    print(activity_frequency(df).head(5))
    print(case_durations(df).head())
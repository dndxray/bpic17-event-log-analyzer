import sys

from columns import ACTIVITY, CASE, TIME

FIRST = "O_Cancelled"
SECOND = "O_Accepted"


def find_pair(activities, first=FIRST, second=SECOND):
    for i in range(len(activities)):
        if activities[i] != first:
            continue
        for j in range(i + 1, len(activities)):
            if activities[j] == second:
                return i, j
    return None


def eventually_follows(df, first=FIRST, second=SECOND):
    ordered = df.sort_values(TIME, kind="stable")
    grouped = ordered.groupby(CASE, sort=False)

    total = 0
    matches = []
    for case_id, events in grouped:
        total += 1
        activities = events[ACTIVITY].tolist()
        pair = find_pair(activities, first, second)
        if pair is None:
            continue
        i, j = pair
        times = events[TIME].tolist()
        matches.append(
            {
                "case": case_id,
                "i": i,
                "j": j,
                "first_time": times[i],
                "second_time": times[j],
            }
        )

    count = len(matches)
    return {
        "count": count,
        "total": total,
        "percent": count / total * 100 if total else 0.0,
        "cases": [m["case"] for m in matches],
        "evidence": matches,
    }


if __name__ == "__main__":
    from loader import load_cached

    df, _ = load_cached(sys.argv[1] if len(sys.argv) > 1 else "BPI Challenge 2017.xes")
    result = eventually_follows(df)
    print(f"{result['count']} dari {result['total']} case ({result['percent']:.2f}%)")
    for item in result["evidence"][:5]:
        print(item)

import sys

from columns import ACTIVITY, LIFECYCLE, RESOURCE
from loader import load_cached
KEY_ACTIVITIES = ["O_Accepted", "O_Refused", "O_Cancelled", "W_Assess potential fraud"]
df, _ = load_cached(sys.argv[1])

print("resource kosong:", df[RESOURCE].isna().sum(), "dari", len(df), "event")
print("nama aktivitas berisi 'fraud':", sorted(a for a in df[ACTIVITY].unique() if "fraud" in a.lower()))

for name in KEY_ACTIVITIES:
    subset = df[df[ACTIVITY] == name]
    print(f"\n{name}: {len(subset)} event")
    if subset.empty:
        continue
    print(subset[LIFECYCLE].value_counts().to_string())
    print("resource kosong:", subset[RESOURCE].isna().sum())
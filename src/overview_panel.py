import tkinter as tk
from tkinter import ttk

from import_panel import ImportPanel
from overview import activity_frequency, overview
from worker import run_async

METRICS = [
    ("cases", "Total case"),
    ("events", "Total event"),
    ("first_event", "Event pertama (UTC)"),
    ("last_event", "Event terakhir (UTC)"),
    ("mean_cycle_days", "Rata-rata cycle time (hari)"),
]
TABLE_COLUMNS = [
    ("activity", "Aktivitas", 260, "w"),
    ("events", "Jumlah event", 110, "e"),
    ("cases", "Jumlah case", 110, "e"),
]


def compute(df):
    return overview(df), activity_frequency(df)


def thousands(number):
    return f"{number:,}".replace(",", ".")


class OverviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.values = {}
        for row, (key, text) in enumerate(METRICS):
            ttk.Label(self, text=text).grid(row=row, column=0, sticky="w", padx=(0, 12))
            self.values[key] = ttk.Label(self, text="-")
            self.values[key].grid(row=row, column=1, sticky="w")

        self.status = ttk.Label(self, text="")
        self.status.grid(row=len(METRICS), column=0, columnspan=2, sticky="w", pady=(6, 0))

        table_row = len(METRICS) + 1
        self.table = ttk.Treeview(
            self, columns=[c[0] for c in TABLE_COLUMNS], show="headings", height=12
        )
        for key, title, width, anchor in TABLE_COLUMNS:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=table_row, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        scroll.grid(row=table_row, column=2, sticky="ns", pady=(10, 0))
        self.rowconfigure(table_row, weight=1)
        self.columnconfigure(1, weight=1)

    def show(self, df):
        self.status.config(text="Menghitung...")
        run_async(self, compute, (df,), self.fill, self.fail)

    def fill(self, result):
        info, freq = result
        self.values["cases"].config(text=thousands(info["cases"]))
        self.values["events"].config(text=thousands(info["events"]))
        self.values["first_event"].config(text=info["first_event"].strftime("%Y-%m-%d %H:%M"))
        self.values["last_event"].config(text=info["last_event"].strftime("%Y-%m-%d %H:%M"))
        self.values["mean_cycle_days"].config(text=f"{info['mean_cycle_days']:.2f}")

        self.table.delete(*self.table.get_children())
        for activity, events, cases in freq.itertuples(index=False):
            self.table.insert("", "end", values=(activity, thousands(events), thousands(cases)))
        self.status.config(text="")

    def fail(self, error):
        self.status.config(text=f"Gagal menghitung: {error}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("BPIC17 Analyzer")
    root.geometry("760x540")
    panel = OverviewPanel(root)
    ImportPanel(root, on_loaded=lambda df, info: panel.show(df)).pack(fill="x")
    panel.pack(fill="both", expand=True)
    root.mainloop()
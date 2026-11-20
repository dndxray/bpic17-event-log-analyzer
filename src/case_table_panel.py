import tkinter as tk
from tkinter import ttk

from columns import CASE
from import_panel import ImportPanel
from overview import case_durations
from overview_panel import OverviewPanel
from worker import run_async

MAX_ROWS = 2000
COLUMNS = [
    ("case", "Case ID", 240, "w"),
    ("start", "Mulai (UTC)", 150, "w"),
    ("end", "Selesai (UTC)", 150, "w"),
    ("days", "Durasi (hari)", 100, "e"),
]


class CaseTablePanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.durations = None

        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Cari case ID:").pack(side="left")
        ttk.Entry(top, textvariable=self.query, width=30).pack(side="left", padx=8)
        self.info = ttk.Label(top, text="")
        self.info.pack(side="left")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.table = ttk.Treeview(body, columns=[c[0] for c in COLUMNS], show="headings")
        for key, title, width, anchor in COLUMNS:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def show(self, df):
        self.info.config(text="Menghitung...")
        run_async(self, case_durations, (df,), self.set_data, self.fail)

    def set_data(self, durations):
        self.durations = durations
        self.refresh()

    def fail(self, error):
        self.info.config(text=f"Gagal menghitung: {error}")

    def refresh(self):
        if self.durations is None:
            return
        data = self.durations
        text = self.query.get().strip().lower()
        if text:
            data = data[data[CASE].str.lower().str.contains(text, regex=False)]

        self.table.delete(*self.table.get_children())
        for case, start, end, days in data.head(MAX_ROWS).itertuples(index=False):
            self.table.insert("", "end", values=(
                case,
                start.strftime("%Y-%m-%d %H:%M"),
                end.strftime("%Y-%m-%d %H:%M"),
                f"{days:.2f}",
            ))
        self.info.config(text=f"Menampilkan {min(len(data), MAX_ROWS)} dari {len(data)} case")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("BPIC17 Analyzer")
    root.geometry("800x600")

    tabs = ttk.Notebook(root)
    overview_panel = OverviewPanel(tabs)
    case_panel = CaseTablePanel(tabs)
    tabs.add(overview_panel, text="Overview")
    tabs.add(case_panel, text="Daftar case")

    def on_loaded(df, info):
        overview_panel.show(df)
        case_panel.show(df)

    ImportPanel(root, on_loaded=on_loaded).pack(fill="x")
    tabs.pack(fill="both", expand=True)
    root.mainloop()
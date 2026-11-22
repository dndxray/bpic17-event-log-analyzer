import tkinter as tk
from tkinter import ttk

from columns import CASE
from exercise_11_7 import analyze_exercise_11_7, case_events, overlap_accepted_refused
from import_panel import ImportPanel
from worker import run_async

MAX_ROWS = 2000
SUMMARY_COLUMNS = [
    ("question", "Pertanyaan", 250, "w"),
    ("count", "Jumlah case", 75, "e"),
    ("mean", "Mean (hari)", 80, "e"),
]
CASE_COLUMNS = [
    ("case", "Case ID", 145, "w"),
    ("start", "Mulai (UTC)", 100, "w"),
    ("end", "Selesai (UTC)", 100, "w"),
    ("days", "Durasi (hari)", 70, "e"),
    ("bukti", "Bukti", 65, "w"),
]
SUMMARY_LABEL = "Jawaban A-E (klik baris untuk melihat case-nya)"
INFO_TEXT = "Klik dua kali sebuah case untuk melihat urutan event-nya"


def thousands(number):
    return f"{number:,}".replace(",", ".")


def make_tree(parent, columns, height):
    tree = ttk.Treeview(parent, columns=[c[0] for c in columns], show="headings", height=height)
    for key, title, width, anchor in columns:
        tree.heading(key, text=title)
        tree.column(key, width=width, minwidth=50, anchor=anchor, stretch=True)
    return tree


def wrap_to_width(label):
    """Lebar bungkus teks mengikuti lebar label, bukan angka tetap."""
    label.bind("<Configure>", lambda e: label.configure(wraplength=max(e.width - 4, 100)))


def compute(df):
    return analyze_exercise_11_7(df), overlap_accepted_refused(df)


class Exercise117Panel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.df = None
        self.results = []
        self.shown = None

        ttk.Label(self, text="Exercise 11.7 (A-E)", style="PageTitle.TLabel").pack(
            anchor="w", pady=(0, 4))
        self.status = ttk.Label(self, text="Muat file XES terlebih dahulu.",
                                style="Muted.TLabel", justify="left")
        self.status.pack(fill="x", pady=(0, 2))
        wrap_to_width(self.status)
        self.rule = ttk.Label(self, text="", justify="left", style="Muted.TLabel")
        self.rule.pack(fill="x", pady=(0, 6))
        wrap_to_width(self.rule)

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="Cari case ID:", style="Muted.TLabel").pack(side="left")
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.fill_cases())
        ttk.Entry(top, textvariable=self.query, width=24).pack(side="left", padx=8)
        self.note = ttk.Label(top, text="", style="Muted.TLabel")
        self.note.pack(side="left")

        # Dua tabel sejajar, dengan label di atas masing-masing.
        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=5, uniform="col")
        body.columnconfigure(1, weight=6, uniform="col")
        body.rowconfigure(1, weight=1)

        ttk.Label(body, text=SUMMARY_LABEL, style="Muted.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 4))
        self.info = ttk.Label(body, text=INFO_TEXT, style="Muted.TLabel")
        self.info.grid(row=0, column=1, sticky="w", pady=(0, 4), padx=(8, 0))

        left = ttk.Frame(body)
        left.grid(row=1, column=0, sticky="nsew")
        self.summary = make_tree(left, SUMMARY_COLUMNS, height=5)
        self.summary.pack(fill="both", expand=True)
        self.summary.bind("<<TreeviewSelect>>", self.on_select)

        right = ttk.Frame(body)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        self.cases = make_tree(right, CASE_COLUMNS, height=4)
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.cases.yview)
        self.cases.configure(yscrollcommand=scroll.set)
        self.cases.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.cases.bind("<Double-1>", self.open_case)

    def show(self, df):
        self.df = df
        self.status.config(text="Menghitung...")
        run_async(self, compute, (df,), self.fill, self.fail)

    def fail(self, error):
        self.status.config(text=f"Gagal menghitung: {error}")

    def fill(self, outcome):
        self.results, overlap = outcome
        self.summary.delete(*self.summary.get_children())
        for index, r in enumerate(self.results):
            mean = "-" if r.mean_days != r.mean_days else f"{r.mean_days:.2f}"
            self.summary.insert("", "end", iid=str(index),
                    values=(r.question, thousands(r.count), mean))
        total = self.results[0].total_cases
        self.status.config(
            text=f"Denominator: {thousands(total)} case. "
                 f"Case yang memuat O_Accepted DAN O_Refused: {thousands(overlap)} "
                 f"(C dan D tidak harus saling eksklusif)."
        )
        self.summary.selection_set("0")

    def on_select(self, _event):
        selected = self.summary.selection()
        if not selected:
            return
        self.shown = self.results[int(selected[0])]
        self.rule.config(text=f"Aturan: {self.shown.rule}")
        self.fill_cases()

    def fill_cases(self):
        if self.shown is None:
            return
        data = self.shown.cases
        text = self.query.get().strip().lower()
        if text:
            data = data[data[CASE].str.lower().str.contains(text, regex=False)]
        self.cases.delete(*self.cases.get_children())
        for case, start, end, days, bukti in data.head(MAX_ROWS).itertuples(index=False):
            self.cases.insert("", "end", values=(
                case, start.strftime("%Y-%m-%d %H:%M"), end.strftime("%Y-%m-%d %H:%M"),
                f"{days:.2f}", bukti))
        self.note.config(text=f"Menampilkan {min(len(data), MAX_ROWS)} dari {len(data)} case "
                              f"(ekspor CSV memuat semuanya)")

    def open_case(self, _event):
        item = self.cases.focus()
        if not item or self.df is None:
            return
        case_id = self.cases.item(item, "values")[0]
        events = case_events(self.df, case_id)
        window = tk.Toplevel(self)
        window.title(f"Rincian {case_id}")
        window.geometry("760x420")
        columns = [(c, c, 150, "w") for c in events.columns]
        tree = make_tree(window, columns, height=15)
        tree.pack(fill="both", expand=True)
        for row in events.itertuples(index=False):
            tree.insert("", "end", values=[str(v) for v in row])

    def reset(self):
        self.df = None
        self.results = []
        self.shown = None
        self.summary.delete(*self.summary.get_children())
        self.cases.delete(*self.cases.get_children())
        self.status.config(text="Muat file XES terlebih dahulu.")
        self.rule.config(text="")
        self.note.config(text="")
        self.query.set("")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("BPIC17 Analyzer - Exercise 11.7")
    root.geometry("1100x640")
    panel = Exercise117Panel(root)
    ImportPanel(root, on_loaded=lambda df, info: panel.show(df)).pack(fill="x")
    panel.pack(fill="both", expand=True)
    root.mainloop()

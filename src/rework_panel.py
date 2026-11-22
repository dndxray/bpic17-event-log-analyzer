import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from columns import CASE, RESOURCE
from rework import (TARGET, count_ignoring_lifecycle, repeated_complete,
                    same_resource_complete)
from worker import run_async

MAX_ROWS = 2000
EVIDENCE_COLUMNS = [
    ("no", "No", 40, "e"),
    ("time", "Timestamp (UTC)", 150, "w"),
    ("activity", "Aktivitas", 200, "w"),
    ("lifecycle", "Lifecycle", 90, "w"),
    ("resource", "Resource", 100, "w"),
]


def thousands(number):
    return f"{number:,}".replace(",", ".")


def make_table(parent, columns, height):
    frame = ttk.Frame(parent)
    table = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", height=height)
    for key, title, width, anchor in columns:
        table.heading(key, text=title)
        table.column(key, width=width, anchor=anchor)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=table.yview)
    table.configure(yscrollcommand=scroll.set)
    table.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return frame, table


class ReworkPanel(ttk.Frame):
    """Panel dasar 11.15 / 11.18. Subclass mengisi: title, case_columns, compute()."""

    title = ""
    case_columns = []

    def __init__(self, parent, on_open_case=None):
        super().__init__(parent, padding=10)
        self.result = None
        self.on_open_case = on_open_case

        ttk.Label(self, text=self.title, style="PageTitle.TLabel",
                  wraplength=640, justify="left").pack(anchor="w", pady=(0, 6))
        self.rule = ttk.Label(self, text="Muat file XES terlebih dahulu.", wraplength=640,
                              justify="left", style="Muted.TLabel")
        self.rule.pack(anchor="w", pady=(2, 6))

        summary = ttk.Frame(self)
        summary.pack(fill="x")
        self.labels = {}
        for row, (key, text) in enumerate([("count", "Jumlah case lolos"),
                                           ("total", "Total case (denominator)")]):
            ttk.Label(summary, text=text, style="Muted.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=2)
            self.labels[key] = ttk.Label(summary, text="-",
                                         font=("TkDefaultFont", 10, "bold"))
            self.labels[key].grid(row=row, column=1, sticky="w", pady=2)

        self.answer = ttk.Label(self, text="", font=("TkDefaultFont", 12, "bold"))
        self.answer.pack(anchor="w", pady=(6, 0))
        self.note = ttk.Label(self, text="", wraplength=640, justify="left",
                              style="Muted.TLabel")
        self.note.pack(anchor="w")
        self.status = ttk.Label(self, text="", style="Muted.TLabel")
        self.status.pack(anchor="w")

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(8, 4))
        ttk.Label(top, text="Cari case ID:", style="Muted.TLabel").pack(side="left")
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(top, textvariable=self.query, width=24).pack(side="left", padx=8)
        self.info = ttk.Label(top, text="", style="Muted.TLabel")
        self.info.pack(side="left")
        self.export_button = ttk.Button(top, text="Ekspor CSV", command=self.export_csv)
        self.export_button.pack(side="right")

        frame, self.table = make_table(self, self.case_columns, 7)
        frame.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", lambda _e: self.show_evidence())
        self.table.bind("<Double-1>", lambda _e: self.open_selected())

        self.evidence_title = ttk.Label(
            self, text="Klik baris untuk melihat event bukti (klik dua kali: buka di Case Explorer)",
            style="Muted.TLabel")
        self.evidence_title.pack(anchor="w", pady=(8, 4))
        frame, self.evidence_table = make_table(self, EVIDENCE_COLUMNS, 6)
        frame.pack(fill="both", expand=True)

    # --- diisi subclass -------------------------------------------------
    @staticmethod
    def compute(df):
        raise NotImplementedError

    # --- alur umum ------------------------------------------------------
    def show(self, df):
        self.status.config(text="Menghitung...")
        run_async(self, self.compute, (df,), self.set_result, self.fail)

    def fail(self, error):
        self.status.config(text=f"Gagal menghitung: {error}")

    def set_result(self, outcome):
        self.result, note = outcome
        r = self.result
        self.status.config(text="")
        self.rule.config(text=f"Aturan: {r.rule}")
        self.labels["count"].config(text=thousands(r.count))
        self.labels["total"].config(text=thousands(r.total_cases))
        self.answer.config(text=f"{thousands(r.count)} dari {thousands(r.total_cases)} case")
        self.note.config(text=note)
        self.refresh()

    def refresh(self):
        if self.result is None:
            return
        data = self.result.cases
        text = self.query.get().strip().lower()
        if text:
            data = data[data[CASE].str.lower().str.contains(text, regex=False)]
        self.table.delete(*self.table.get_children())
        for row in data.head(MAX_ROWS).itertuples(index=False):
            self.table.insert("", "end", values=tuple(row))
        self.info.config(text=f"Menampilkan {min(len(data), MAX_ROWS)} dari {len(data)} baris")

    def selected(self):
        sel = self.table.selection()
        return self.table.item(sel[0], "values") if sel and self.result is not None else None

    def evidence_for(self, values):
        ev = self.result.evidence
        ev = ev[ev[CASE] == values[0]]
        if len(values) > 2:  # 11.18: (case, resource, jumlah) -> hanya resource itu
            ev = ev[ev[RESOURCE] == values[1]]
        return ev

    def show_evidence(self):
        values = self.selected()
        if values is None:
            return
        ev = self.evidence_for(values)
        self.evidence_title.config(text=f"Bukti untuk {values[0]}: {len(ev)} event complete terhitung")
        self.evidence_table.delete(*self.evidence_table.get_children())
        for n, row in enumerate(ev.itertuples(index=False), start=1):
            case, activity, lifecycle, resource, time = row
            self.evidence_table.insert("", "end", values=(
                n, time.strftime("%Y-%m-%d %H:%M:%S"), activity, lifecycle, resource))

    def open_selected(self):
        values = self.selected()
        if values is not None and self.on_open_case is not None:
            self.on_open_case(values[0])

    def export_csv(self):
        if self.result is None:
            self.status.config(text="Belum ada hasil untuk diekspor.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile=f"exercise_{self.result.code}.csv",
            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        path = Path(path)
        evidence_path = path.with_name(path.stem + "_bukti" + path.suffix)
        self.result.cases.to_csv(path, index=False, encoding="utf-8-sig")
        self.result.evidence.to_csv(evidence_path, index=False, encoding="utf-8-sig")
        self.status.config(text=f"Tersimpan: {path.name} dan {evidence_path.name}")

    def reset(self):
        self.result = None
        self.status.config(text="")
        self.rule.config(text="Muat file XES terlebih dahulu.")
        self.labels["count"].config(text="-")
        self.labels["total"].config(text="-")
        self.answer.config(text="")
        self.note.config(text="")
        self.table.delete(*self.table.get_children())
        self.evidence_table.delete(*self.evidence_table.get_children())
        self.evidence_title.config(
            text="Klik baris untuk melihat event bukti (klik dua kali: buka di Case Explorer)")
        self.info.config(text="")
        self.query.set("")


class Ex1115Panel(ReworkPanel):
    title = f"Exercise 11.15: case dengan {TARGET} selesai (complete) minimal 2x"
    case_columns = [
        ("case", "Case ID", 260, "w"),
        ("n", "Jumlah complete", 130, "e"),
    ]

    @staticmethod
    def compute(df):
        result = repeated_complete(df)
        naive = count_ignoring_lifecycle(df)
        note = (f"Pembanding (BUKAN jawaban): tanpa filter lifecycle, {thousands(naive)} case punya "
                f">= 2 event aktivitas ini, karena schedule/start/suspend/resume ikut terhitung.")
        return result, note


class Ex1118Panel(ReworkPanel):
    title = f"Exercise 11.18: case dengan {TARGET} selesai minimal 2x oleh resource yang sama"
    case_columns = [
        ("case", "Case ID", 250, "w"),
        ("resource", "Resource", 130, "w"),
        ("n", "Jumlah complete oleh resource", 170, "e"),
    ]

    @staticmethod
    def compute(df):
        result = same_resource_complete(df)
        base = repeated_complete(df)
        note = (f"Dari {thousands(base.count)} case yang lolos 11.15, {thousands(result.count)} case "
                f"lolos 11.18 (dua complete oleh resource sama; resource kosong tidak dihitung).")
        return result, note

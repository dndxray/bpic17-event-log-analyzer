import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from columns import CASE, RESOURCE
from rework import (TARGET, count_ignoring_lifecycle, repeated_complete,
                    same_resource_complete)
from worker import run_async

MAX_ROWS = 2000
EVIDENCE_COLUMNS = [
    ("no", "No", 36, "e"),
    ("time", "Timestamp (UTC)", 140, "w"),
    ("activity", "Aktivitas", 190, "w"),
    ("lifecycle", "Lifecycle", 80, "w"),
    ("resource", "Resource", 80, "w"),
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

        self.heading = ttk.Label(self, text=self.title, style="PageTitle.TLabel",
                                 wraplength=640, justify="left")
        self.heading.pack(anchor="w", pady=(0, 2))
        self.rule = ttk.Label(self, text="Muat file XES terlebih dahulu.", wraplength=640,
                              justify="left", style="Muted.TLabel")
        self.rule.pack(anchor="w", pady=(0, 2))

        self.answer = ttk.Label(self, text="", font=("TkDefaultFont", 12, "bold"))
        self.answer.pack(anchor="w", pady=(2, 0))
        self.note = ttk.Label(self, text="", wraplength=640, justify="left",
                              style="Muted.TLabel")
        self.note.pack(anchor="w")

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(4, 4))
        ttk.Label(top, text="Cari case ID:", style="Muted.TLabel").pack(side="left")
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(top, textvariable=self.query, width=24).pack(side="left", padx=8)
        self.info = ttk.Label(top, text="", style="Muted.TLabel")
        self.info.pack(side="left")
        self.status = ttk.Label(top, text="", style="Muted.TLabel")
        self.status.pack(side="left", padx=12)
        self.export_button = ttk.Button(top, text="Ekspor CSV", command=self.export_csv)
        self.export_button.pack(side="right")

        # dua tabel berdampingan: kiri daftar case, kanan bukti event (hemat tinggi layar)
        tables = ttk.Frame(self)
        tables.pack(fill="both", expand=True)
        tables.columnconfigure(0, weight=5, uniform="tabel")
        tables.columnconfigure(1, weight=6, uniform="tabel")
        tables.rowconfigure(1, weight=1)

        ttk.Label(tables, text="Case yang lolos", style="Muted.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        frame, self.table = make_table(tables, self.case_columns, 3)
        frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        self.table.bind("<<TreeviewSelect>>", lambda _e: self.show_evidence())
        self.table.bind("<Double-1>", lambda _e: self.open_selected())

        self.evidence_title = ttk.Label(
            tables, text="Klik baris untuk melihat event bukti (klik dua kali: buka di Case Explorer)",
            style="Muted.TLabel")
        self.evidence_title.grid(row=0, column=1, sticky="w", pady=(0, 2))
        frame, self.evidence_table = make_table(tables, EVIDENCE_COLUMNS, 3)
        frame.grid(row=1, column=1, sticky="nsew")
        self.bind("<Configure>", self.fit_text)

    def fit_text(self, event):
        width = max(300, event.width - 40)
        for label in (self.heading, self.rule, self.note):
            label.config(wraplength=width)

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
        self.answer.config(text=(f"{thousands(r.count)} dari {thousands(r.total_cases)} case "
                                 f"(denominator: {thousands(r.total_cases)})"))
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
        ("case", "Case ID", 190, "w"),
        ("n", "Jumlah complete", 110, "e"),
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
        ("case", "Case ID", 170, "w"),
        ("resource", "Resource", 80, "w"),
        ("n", "Jumlah", 70, "e"),
    ]

    @staticmethod
    def compute(df):
        result = same_resource_complete(df)
        base = repeated_complete(df)
        note = (f"Dari {thousands(base.count)} case yang lolos 11.15, {thousands(result.count)} case "
                f"lolos 11.18 (dua complete oleh resource sama; resource kosong tidak dihitung).")
        return result, note

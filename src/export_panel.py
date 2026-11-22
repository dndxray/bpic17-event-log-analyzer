import tkinter as tk
from tkinter import filedialog, ttk

from export import collect_results, export_all, summary_rows
from worker import run_async

COLUMNS = [
    ("kode", "Kode", 60, "w"),
    ("pertanyaan", "Pertanyaan", 230, "w"),
    ("count", "Jumlah case", 80, "e"),
    ("total", "Denominator", 85, "e"),
    ("percent", "Persentase", 70, "e"),
    ("mean", "Mean cycle (hari)", 100, "e"),
]


def thousands(number):
    return f"{number:,}".replace(",", ".")


class ExportPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.df = None
        self.results = None

        ttk.Label(self, text="Ekspor hasil", style="PageTitle.TLabel").pack(
            anchor="w", pady=(0, 4))
        ttk.Label(
            self,
            text=("Ekspor ringkasan jawaban, daftar case, dan tabel bukti ke satu folder CSV. "
                  "Angka dihitung ulang dari log yang sedang aktif."),
            wraplength=640, justify="left", style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        self.status = ttk.Label(self, text="Muat file XES terlebih dahulu.", wraplength=640,
                                justify="left", style="Muted.TLabel")
        self.status.pack(anchor="w", pady=(0, 8))

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.table = ttk.Treeview(body, columns=[c[0] for c in COLUMNS], show="headings",
                                  height=10)
        for key, title, width, anchor in COLUMNS:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(10, 0))
        self.export_button = ttk.Button(buttons, text="Ekspor ke folder...",
                                        style="Accent.TButton", command=self.export)
        self.export_button.pack(side="left")
        ttk.Label(
            buttons,
            text="5 file CSV: ringkasan, daftar case, dan bukti.",
            style="Muted.TLabel",
        ).pack(side="left", padx=10)

    def show(self, df):
        self.df = df
        self.results = None
        self.status.config(text="Menghitung ringkasan...")
        run_async(self, collect_results, (df,), self.set_results, self.fail)

    def set_results(self, results):
        self.results = results
        summary = summary_rows(self.df, results)
        self.table.delete(*self.table.get_children())
        for row in summary.itertuples(index=False):
            code, question, _rule, count, total, percent, mean = row
            mean_text = "-" if mean != mean else f"{mean:.2f}"
            self.table.insert("", "end", values=(
                code, question, thousands(count), thousands(total),
                f"{percent:.2f}%".replace(".", ","), mean_text,
            ))
        self.status.config(text="Ringkasan siap diekspor.")

    def fail(self, error):
        self.status.config(text=f"Gagal menghitung: {error}")

    def export(self):
        if self.df is None or self.results is None:
            self.status.config(text="Belum ada hasil untuk diekspor.")
            return
        out_dir = filedialog.askdirectory(title="Pilih folder tujuan ekspor CSV")
        if not out_dir:
            return
        self.status.config(text="Mengekspor...")
        self.export_button.config(state="disabled")
        run_async(
            self, export_all, (self.df, out_dir, self.results),
            self.finish_export, self.fail_export,
        )

    def finish_export(self, paths):
        self.export_button.config(state="normal")
        names = ", ".join(path.name for path in paths)
        self.status.config(text=f"Tersimpan {len(paths)} file: {names}")

    def fail_export(self, error):
        self.export_button.config(state="normal")
        self.status.config(text=f"Gagal mengekspor: {error}")

    def reset(self):
        self.df = None
        self.results = None
        self.table.delete(*self.table.get_children())
        self.status.config(text="Muat file XES terlebih dahulu.")
        self.export_button.config(state="normal")

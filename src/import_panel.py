import tkinter as tk
from tkinter import filedialog, ttk

from loader import load_cached
from validation import LogError, validate
from worker import Worker


def _short_path(path, limit=55):
    text = str(path)
    return text if len(text) <= limit else "..." + text[-(limit - 3):]


class ImportPanel(ttk.Frame):
    def __init__(self, parent, on_loaded):
        super().__init__(parent, padding=0, style="Card.TFrame")
        self.on_loaded = on_loaded
        self.worker = None
        self._request = 0

        ttk.Label(self, text="Impor event log", style="CardHeading.TLabel").grid(
            row=0, column=0, sticky="w")
        self.file_label = ttk.Label(self, text="Belum ada file", style="CardMuted.TLabel")
        self.open_button = ttk.Button(self, text="Pilih file XES", style="Accent.TButton",
                                      command=self.choose_file)
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.status = ttk.Label(self, text="", style="CardMuted.TLabel")

        self.file_label.grid(row=0, column=1, padx=14, sticky="w")
        self.open_button.grid(row=0, column=2, sticky="e")
        self.progress.grid(row=1, column=0, columnspan=3, pady=(10, 0), sticky="ew")
        self.status.grid(row=2, column=0, columnspan=3, pady=(4, 0), sticky="w")
        self.columnconfigure(1, weight=1)

    def choose_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Event log XES", "*.xes *.xes.gz"), ("Semua file", "*.*")]
        )
        if not path:
            return
        self._request += 1
        request = self._request
        self.file_label.config(text=_short_path(path))
        self.status.config(text="Membaca log, mohon tunggu...")
        self.open_button.config(state="disabled")
        self.progress.start(10)
        self.worker = Worker(load_cached, (path,))
        self.worker.start()
        self.after(200, lambda: self.check_worker(request))

    def check_worker(self, request):
        if request != self._request:
            return
        outcome = self.worker.poll()
        if outcome is None:
            self.after(200, lambda: self.check_worker(request))
            return

        self.progress.stop()
        self.open_button.config(state="normal")
        kind, value = outcome
        if kind == "error":
            self.status.config(text=f"Gagal: {value}")
            return

        df, elapsed = value
        try:
            info = validate(df)
        except LogError as err:
            self.status.config(text=f"Gagal: {err}")
            return

        self.status.config(
            text=f"Berhasil ({elapsed:.1f} detik): {info['cases']} case, {info['events']} event"
        )
        self.on_loaded(df, info)

    def reset(self):
        self._request += 1
        self.worker = None
        self.progress.stop()
        self.progress.config(value=0)
        self.file_label.config(text="Belum ada file")
        self.status.config(text="")
        self.open_button.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("BPIC17 Analyzer")
    root.geometry("700x160")
    ImportPanel(root, on_loaded=lambda df, info: print(info)).pack(fill="x")
    root.mainloop()
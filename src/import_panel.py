import tkinter as tk
from tkinter import filedialog, ttk

from loader import load_cached
from validation import LogError, validate
from worker import Worker


class ImportPanel(ttk.Frame):
    def __init__(self, parent, on_loaded):
        super().__init__(parent, padding=10)
        self.on_loaded = on_loaded
        self.worker = None

        self.open_button = ttk.Button(self, text="Pilih file XES", command=self.choose_file)
        self.file_label = ttk.Label(self, text="Belum ada file")
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.status = ttk.Label(self, text="")

        self.open_button.grid(row=0, column=0, sticky="w")
        self.file_label.grid(row=0, column=1, padx=10, sticky="w")
        self.progress.grid(row=1, column=0, columnspan=2, pady=8, sticky="ew")
        self.status.grid(row=2, column=0, columnspan=2, sticky="w")
        self.columnconfigure(1, weight=1)

    def choose_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Event log XES", "*.xes *.xes.gz"), ("Semua file", "*.*")]
        )
        if not path:
            return
        self.file_label.config(text=path)
        self.status.config(text="Membaca log, mohon tunggu...")
        self.open_button.config(state="disabled")
        self.progress.start(10)
        self.worker = Worker(load_cached, (path,))
        self.worker.start()
        self.after(200, self.check_worker)

    def check_worker(self):
        outcome = self.worker.poll()
        if outcome is None:
            self.after(200, self.check_worker)
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


if __name__ == "__main__":
    root = tk.Tk()
    root.title("BPIC17 Analyzer")
    root.geometry("700x160")
    ImportPanel(root, on_loaded=lambda df, info: print(info)).pack(fill="x")
    root.mainloop()
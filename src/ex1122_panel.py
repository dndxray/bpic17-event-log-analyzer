import tkinter as tk
from tkinter import ttk

from ex1122 import FIRST, SECOND, eventually_follows
from theme import BORDER
from worker import run_async

MAX_ROWS = 2000
COLUMNS = [
    ("case", "Case ID", 180, "w"),
    ("first", f"{FIRST} (UTC)", 130, "w"),
    ("second", f"{SECOND} (UTC)", 130, "w"),
    ("days", "Jarak (hari)", 80, "e"),
    ("pos", "Posisi i -> j", 80, "e"),
]


def thousands(number):
    return f"{number:,}".replace(",", ".")


def fmt_time(value):
    return value.strftime("%Y-%m-%d %H:%M")


class Ex1122Panel(ttk.Frame):
    def __init__(self, parent, on_open_case=None):
        super().__init__(parent, padding=10)
        self.result = None
        self.on_open_case = on_open_case

        ttk.Label(
            self,
            text=f"Exercise 11.22: case yang punya {FIRST} lalu setelahnya {SECOND} (eventually follows, i < j)",
            wraplength=640, style="PageTitle.TLabel", justify="left",
        ).pack(anchor="w", pady=(0, 6))

        summary = ttk.Frame(self)
        summary.pack(fill="x", pady=(8, 0))
        self.labels = {}
        for row, (key, text) in enumerate([
            ("count", "Jumlah case lolos"),
            ("total", "Total case (denominator)"),
            ("percent", "Persentase"),
        ]):
            ttk.Label(summary, text=text, style="Muted.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=2)
            self.labels[key] = ttk.Label(summary, text="-",
                                         font=("TkDefaultFont", 10, "bold"))
            self.labels[key].grid(row=row, column=1, sticky="w", pady=2)

        self.answer = ttk.Label(self, text="", font=("TkDefaultFont", 12, "bold"))
        self.answer.pack(anchor="w", pady=(6, 0))
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

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)
        self.table = ttk.Treeview(body, columns=[c[0] for c in COLUMNS], show="headings", height=10)
        for key, title, width, anchor in COLUMNS:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor=anchor)
        scroll = ttk.Scrollbar(body, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.table.bind("<<TreeviewSelect>>", lambda _e: self.draw_timeline())
        self.table.bind("<Double-1>", lambda _e: self.open_selected())

        ttk.Label(
            self,
            text="Timeline pasangan terpilih (klik baris; klik dua kali untuk buka di Case Explorer)",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(8, 0))
        self.canvas = tk.Canvas(self, height=90, background="white", highlightthickness=1,
                                highlightbackground=BORDER)
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda _e: self.draw_timeline())

    def show(self, df):
        self.status.config(text="Menghitung...")
        run_async(self, eventually_follows, (df,), self.set_result, self.fail)

    def set_result(self, result):
        self.result = result
        self.status.config(text="")
        self.labels["count"].config(text=thousands(result["count"]))
        self.labels["total"].config(text=thousands(result["total"]))
        self.labels["percent"].config(text=f"{result['percent']:.2f}%".replace(".", ","))
        self.answer.config(
            text=f"{thousands(result['count'])} dari {thousands(result['total'])} case ({result['percent']:.2f}%)"
        )
        self.refresh()

    def fail(self, error):
        self.status.config(text=f"Gagal menghitung: {error}")

    def filtered(self):
        if self.result is None:
            return []
        text = self.query.get().strip().lower()
        evidence = self.result["evidence"]
        if text:
            evidence = [e for e in evidence if text in str(e["case"]).lower()]
        return evidence

    def refresh(self):
        if self.result is None:
            return
        data = self.filtered()
        self.table.delete(*self.table.get_children())
        for item in data[:MAX_ROWS]:
            days = (item["second_time"] - item["first_time"]).total_seconds() / 86400
            self.table.insert("", "end", iid=str(item["case"]), values=(
                item["case"],
                fmt_time(item["first_time"]),
                fmt_time(item["second_time"]),
                f"{days:.2f}",
                f"{item['i']} -> {item['j']}",
            ))
        self.info.config(text=f"Menampilkan {min(len(data), MAX_ROWS)} dari {len(data)} case")
        self.draw_timeline()

    def selected_item(self):
        selection = self.table.selection()
        if not selection or self.result is None:
            return None
        for item in self.result["evidence"]:
            if str(item["case"]) == selection[0]:
                return item
        return None

    def draw_timeline(self):
        self.canvas.delete("all")
        item = self.selected_item()
        if item is None:
            return
        width = max(self.canvas.winfo_width(), 300)
        left, right, y = 60, width - 60, 45
        self.canvas.create_line(left, y, right, y, width=3, fill="#888", arrow="last")
        self.canvas.create_oval(left - 6, y - 6, left + 6, y + 6, fill="#d9534f", outline="")
        self.canvas.create_oval(right - 6, y - 6, right + 6, y + 6, fill="#5cb85c", outline="")
        self.canvas.create_text(left, y - 18, text=FIRST, fill="#d9534f", anchor="w")
        self.canvas.create_text(right, y - 18, text=SECOND, fill="#5cb85c", anchor="e")
        self.canvas.create_text(left, y + 20, text=fmt_time(item["first_time"]), anchor="w")
        self.canvas.create_text(right, y + 20, text=fmt_time(item["second_time"]), anchor="e")
        days = (item["second_time"] - item["first_time"]).total_seconds() / 86400
        self.canvas.create_text((left + right) / 2, y + 20, text=f"{days:.2f} hari")

    def open_selected(self):
        item = self.selected_item()
        if item is not None and self.on_open_case is not None:
            self.on_open_case(item["case"])

    def reset(self):
        self.result = None
        self.status.config(text="")
        for label in self.labels.values():
            label.config(text="-")
        self.answer.config(text="")
        self.table.delete(*self.table.get_children())
        self.info.config(text="")
        self.canvas.delete("all")
        self.query.set("")


if __name__ == "__main__":
    from loader import load_cached

    root = tk.Tk()
    root.title("BPIC17 Analyzer - 11.22")
    root.geometry("820x640")
    panel = Ex1122Panel(root)
    panel.pack(fill="both", expand=True)
    panel.status.config(text="Membaca log, mohon tunggu...")
    run_async(
        root,
        lambda: load_cached("BPI Challenge 2017.xes")[0],
        (),
        panel.show,
        panel.fail,
    )
    root.mainloop()

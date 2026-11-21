import tkinter as tk
from tkinter import ttk

from case_explorer import case_event_table, case_list, search_cases
from columns import CASE
from worker import run_async

MAX_ROWS = 2000
CASE_COLUMNS = [
    ("case", "Case ID", 240, "w"),
    ("events", "Jumlah event", 100, "e"),
    ("start", "Mulai (UTC)", 140, "w"),
    ("end", "Selesai (UTC)", 140, "w"),
]
EVENT_COLUMNS = [
    ("no", "No", 50, "e"),
    ("time", "Timestamp (UTC)", 190, "w"),
    ("activity", "Aktivitas", 260, "w"),
    ("lifecycle", "Lifecycle", 100, "w"),
    ("resource", "Resource", 120, "w"),
]


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


class CaseExplorerPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.df = None
        self.cases = None

        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *_: self.refresh())

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Cari case ID:").pack(side="left")
        ttk.Entry(top, textvariable=self.query, width=30).pack(side="left", padx=8)
        self.info = ttk.Label(top, text="")
        self.info.pack(side="left")

        list_frame, self.case_table = make_table(self, CASE_COLUMNS, 8)
        list_frame.pack(fill="both", expand=True)
        self.case_table.bind("<<TreeviewSelect>>", lambda _e: self.show_selected())

        self.detail_title = ttk.Label(self, text="Pilih case untuk melihat urutan event")
        self.detail_title.pack(anchor="w", pady=(10, 4))
        detail_frame, self.event_table = make_table(self, EVENT_COLUMNS, 10)
        detail_frame.pack(fill="both", expand=True)

    def show(self, df):
        self.df = df
        self.info.config(text="Menghitung...")
        run_async(self, case_list, (df,), self.set_cases, self.fail)

    def set_cases(self, cases):
        self.cases = cases
        self.refresh()

    def fail(self, error):
        self.info.config(text=f"Gagal menghitung: {error}")

    def refresh(self):
        if self.cases is None:
            return
        data = search_cases(self.cases, self.query.get())
        self.case_table.delete(*self.case_table.get_children())
        for case, events, start, end in data.head(MAX_ROWS).itertuples(index=False):
            self.case_table.insert("", "end", iid=str(case), values=(
                case,
                events,
                start.strftime("%Y-%m-%d %H:%M"),
                end.strftime("%Y-%m-%d %H:%M"),
            ))
        self.info.config(text=f"Menampilkan {min(len(data), MAX_ROWS)} dari {len(data)} case")

    def show_selected(self):
        selection = self.case_table.selection()
        if selection and self.df is not None:
            self.show_case(selection[0])

    def show_case(self, case_id):
        events = case_event_table(self.df, case_id)
        self.detail_title.config(text=f"Case {case_id}: {len(events)} event")
        self.event_table.delete(*self.event_table.get_children())
        for number, (time, activity, lifecycle, resource) in enumerate(
            events.itertuples(index=False), start=1
        ):
            self.event_table.insert("", "end", values=(
                number, time.strftime("%Y-%m-%d %H:%M:%S"), activity, lifecycle, resource,
            ))

    def open_case(self, case_id):
        """Dipanggil panel lain (mis. 11.22) untuk langsung menampilkan satu case."""
        self.query.set(str(case_id))
        iid = str(case_id)
        if self.case_table.exists(iid):
            self.case_table.selection_set(iid)
            self.case_table.see(iid)
        elif self.df is not None:
            self.show_case(case_id)


if __name__ == "__main__":
    from loader import load_cached

    root = tk.Tk()
    root.title("BPIC17 Analyzer - Case Explorer")
    root.geometry("860x640")
    panel = CaseExplorerPanel(root)
    panel.pack(fill="both", expand=True)
    panel.info.config(text="Membaca log, mohon tunggu...")
    run_async(
        root,
        lambda: load_cached("BPI Challenge 2017.xes")[0],
        (),
        panel.show,
        panel.fail,
    )
    root.mainloop()

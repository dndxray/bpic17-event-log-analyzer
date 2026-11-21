"""Titik masuk aplikasi: python src/main.py"""
import tkinter as tk
from tkinter import ttk

from about import get_about_info
from case_explorer_panel import CaseExplorerPanel
from ex1122_panel import Ex1122Panel
from exercise_11_7_panel import Exercise117Panel
from import_panel import ImportPanel
from overview_panel import OverviewPanel
from rework_panel import Ex1115Panel, Ex1118Panel


class AboutPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=14)
        ttk.Label(self, text="BPIC17 Event Log Analyzer (Tahap 1)",
                  font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        for row, (key, value) in enumerate(get_about_info().items(), start=1):
            ttk.Label(self, text=key).grid(row=row, column=0, sticky="w", padx=(0, 16))
            ttk.Label(self, text=value).grid(row=row, column=1, sticky="w")


def main():
    root = tk.Tk()
    root.title("BPIC17 Event Log Analyzer")
    root.geometry("1040x780")

    tabs = ttk.Notebook(root)
    explorer = CaseExplorerPanel(tabs)

    def open_case(case_id):
        tabs.select(explorer)
        explorer.open_case(case_id)

    overview = OverviewPanel(tabs)
    ex117 = Exercise117Panel(tabs)
    ex1115 = Ex1115Panel(tabs, on_open_case=open_case)
    ex1118 = Ex1118Panel(tabs, on_open_case=open_case)
    ex1122 = Ex1122Panel(tabs, on_open_case=open_case)
    panels = [overview, ex117, ex1115, ex1118, ex1122, explorer]

    for panel, text in [(overview, "Overview"), (ex117, "Exercise 11.7"),
                        (ex1115, "Exercise 11.15"), (ex1118, "Exercise 11.18"),
                        (ex1122, "Exercise 11.22"), (explorer, "Case Explorer"),
                        (AboutPanel(tabs), "About")]:
        tabs.add(panel, text=text)

    def on_loaded(df, info):
        for panel in panels:
            panel.show(df)

    ImportPanel(root, on_loaded=on_loaded).pack(fill="x")
    tabs.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()

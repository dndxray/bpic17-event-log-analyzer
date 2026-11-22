"""Titik masuk aplikasi: python3 main.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import tkinter as tk
from tkinter import ttk

from about import get_about_info
from case_explorer_panel import CaseExplorerPanel
from ex1122_panel import Ex1122Panel
from exercise_11_7_panel import Exercise117Panel
from export_panel import ExportPanel
from import_panel import ImportPanel
from overview_panel import OverviewPanel
from rework_panel import Ex1115Panel, Ex1118Panel
from theme import (ACCENT, ACCENT_SOFT, FONT, HOVER, MUTED, SIDEBAR, TEXT, apply_theme)


class AboutPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=14)
        ttk.Label(self, text="Tentang aplikasi", style="PageTitle.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row, (key, value) in enumerate(get_about_info().items(), start=1):
            ttk.Label(self, text=key, style="Muted.TLabel").grid(
                row=row, column=0, sticky="nw", padx=(0, 20), pady=2)
            ttk.Label(self, text=value, wraplength=560, justify="left").grid(
                row=row, column=1, sticky="w", pady=2)


def main():
    root = tk.Tk()
    root.title("BPIC17 Event Log Analyzer")
    root.geometry("1180x820")
    root.minsize(1000, 700)
    apply_theme(root)

    shell = ttk.Frame(root, style="App.TFrame")
    shell.pack(fill="both", expand=True)

    sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=220)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    main_area = ttk.Frame(shell, style="App.TFrame")
    main_area.pack(side="left", fill="both", expand=True)

    header = ttk.Frame(main_area, style="Header.TFrame", padding=(24, 20, 24, 16))
    header.pack(fill="x")
    ttk.Label(header, text="BPIC17 Event Log Analyzer",
              style="Title.TLabel").pack(anchor="w")
    ttk.Label(header, text="Analisis event log proses pengajuan pinjaman",
              style="Subtitle.TLabel").pack(anchor="w", pady=(2, 0))
    ttk.Separator(main_area, orient="horizontal").pack(fill="x")

    content = ttk.Frame(main_area, style="App.TFrame", padding=(20, 16, 20, 20))
    content.rowconfigure(0, weight=1)
    content.columnconfigure(0, weight=1)
    content.grid_propagate(False)

    overview = OverviewPanel(content)
    ex117 = Exercise117Panel(content)
    explorer = CaseExplorerPanel(content)
    ex1115 = Ex1115Panel(content, on_open_case=lambda cid: open_case(cid))
    ex1118 = Ex1118Panel(content, on_open_case=lambda cid: open_case(cid))
    ex1122 = Ex1122Panel(content, on_open_case=lambda cid: open_case(cid))
    export_panel = ExportPanel(content)
    about = AboutPanel(content)
    data_panels = [overview, ex117, ex1115, ex1118, ex1122, explorer, export_panel]
    pages = data_panels + [about]
    for page in pages:
        page.grid(row=0, column=0, sticky="nsew")

    nav_buttons = {}
    current = {"page": overview}

    def show_page(panel):
        panel.tkraise()
        current["page"] = panel
        for page, button in nav_buttons.items():
            selected = page is panel
            button.configure(
                bg=ACCENT_SOFT if selected else SIDEBAR,
                fg=ACCENT if selected else TEXT,
                font=(FONT, 10, "bold") if selected else (FONT, 10),
            )

    def open_case(case_id):
        show_page(explorer)
        explorer.open_case(case_id)

    def add_section(text):
        ttk.Label(sidebar, text=text, style="SidebarSection.TLabel").pack(
            fill="x", padx=24, pady=(18, 6))

    def add_nav(text, panel):
        button = tk.Button(
            sidebar, text=text, anchor="w", relief="flat", bd=0,
            bg=SIDEBAR, fg=TEXT, activebackground=HOVER, activeforeground=TEXT,
            highlightthickness=0, font=(FONT, 10), padx=22, pady=8,
            cursor="hand2", command=lambda p=panel: show_page(p),
        )
        button.pack(fill="x", padx=10, pady=1)
        button.bind(
            "<Enter>",
            lambda _e, p=panel, b=button: b.config(bg=HOVER) if current["page"] is not p else None,
        )
        button.bind(
            "<Leave>",
            lambda _e, p=panel, b=button: b.config(
                bg=ACCENT_SOFT if current["page"] is p else SIDEBAR),
        )
        nav_buttons[panel] = button

    brand = ttk.Frame(sidebar, style="Sidebar.TFrame")
    brand.pack(fill="x", padx=22, pady=(22, 4))
    ttk.Label(brand, text="BPIC17", style="Brand.TLabel").pack(anchor="w")
    ttk.Label(brand, text="Event Log Analyzer", style="BrandSub.TLabel").pack(anchor="w")

    add_section("RINGKASAN")
    add_nav("Overview", overview)
    add_section("LATIHAN")
    add_nav("Exercise 11.7", ex117)
    add_nav("Exercise 11.15", ex1115)
    add_nav("Exercise 11.18", ex1118)
    add_nav("Exercise 11.22", ex1122)
    add_section("DATA & OUTPUT")
    add_nav("Case Explorer", explorer)
    add_nav("Ekspor", export_panel)
    add_section("LAINNYA")
    add_nav("About", about)

    footer = ttk.Frame(sidebar, style="Sidebar.TFrame")
    footer.pack(side="bottom", fill="x", padx=10, pady=(8, 14))
    ttk.Label(footer, text="Tahap 1 · BPIC17", style="SidebarMuted.TLabel").pack(
        anchor="w", padx=14, pady=(0, 8))
    close_button = tk.Button(
        footer, text="Tutup aplikasi", anchor="w", relief="flat", bd=0,
        bg=SIDEBAR, fg=MUTED, activebackground=HOVER, activeforeground=TEXT,
        highlightthickness=0, font=(FONT, 9), padx=14, pady=7,
        cursor="hand2", command=root.destroy,
    )
    close_button.pack(fill="x")
    close_button.bind("<Enter>", lambda _e: close_button.config(fg=TEXT))
    close_button.bind("<Leave>", lambda _e: close_button.config(fg=MUTED))

    import_card = ttk.Frame(main_area, style="Card.TFrame", padding=(20, 14))
    import_card.pack(fill="x", padx=20, pady=(16, 0))

    def on_loaded(df, info):
        state["df"] = df
        for panel in data_panels:
            panel.show(df)

    def rerun():
        if state["df"] is None:
            return
        for panel in data_panels:
            panel.show(state["df"])

    def reset():
        state["df"] = None
        for panel in data_panels:
            panel.reset()
        import_panel.reset()
        show_page(overview)

    state = {"df": None}
    import_panel = ImportPanel(import_card, on_loaded=on_loaded)
    import_panel.pack(fill="x")

    actions = ttk.Frame(main_area, style="App.TFrame")
    actions.pack(fill="x", padx=20, pady=(8, 0))
    ttk.Button(actions, text="Hitung ulang", command=rerun).pack(side="right")
    ttk.Button(actions, text="Reset", command=reset).pack(side="right", padx=(0, 6))

    content.pack(fill="both", expand=True)
    show_page(overview)
    root.mainloop()


if __name__ == "__main__":
    main()

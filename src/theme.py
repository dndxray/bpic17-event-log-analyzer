"""Tema visual aplikasi: palet warna, font, dan style ttk."""
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

BG = "#f4f6f8"
SURFACE = "#ffffff"
SIDEBAR = "#eef1f4"
BORDER = "#dde2e8"
TEXT = "#1f2933"
MUTED = "#6b7785"
ACCENT = "#0f766e"
ACCENT_DARK = "#115e59"
ACCENT_SOFT = "#e3f1ee"
HOVER = "#e4e9ee"
DISABLED = "#9aa5b1"

FONT = "TkDefaultFont"


def _choose_font(root):
    families = set(tkfont.families(root))
    for name in ("Inter", "Segoe UI", "SF Pro Text", "Helvetica Neue",
                 "Noto Sans", "DejaVu Sans"):
        if name in families:
            return name
    return "TkDefaultFont"


def apply_theme(root):
    """Pasang tema terang yang tenang dan konsisten untuk seluruh aplikasi."""
    global FONT
    FONT = _choose_font(root)
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont",
                 "TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont"):
        try:
            tkfont.nametofont(name).configure(family=FONT)
        except tk.TclError:
            pass
    tkfont.nametofont("TkDefaultFont").configure(size=10)

    root.configure(background=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=TEXT, font=(FONT, 10))
    style.configure("App.TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("Header.TFrame", background=SURFACE)
    style.configure("Sidebar.TFrame", background=SIDEBAR)

    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("PageTitle.TLabel", background=BG, foreground=TEXT,
                    font=(FONT, 14, "bold"))
    style.configure("Card.TLabel", background=SURFACE, foreground=TEXT)
    style.configure("CardMuted.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("CardHeading.TLabel", background=SURFACE, foreground=TEXT,
                    font=(FONT, 10, "bold"))
    style.configure("Title.TLabel", background=SURFACE, foreground=TEXT,
                    font=(FONT, 18, "bold"))
    style.configure("Subtitle.TLabel", background=SURFACE, foreground=MUTED,
                    font=(FONT, 10))
    style.configure("Sidebar.TLabel", background=SIDEBAR, foreground=TEXT)
    style.configure("SidebarMuted.TLabel", background=SIDEBAR, foreground=MUTED,
                    font=(FONT, 9))
    style.configure("SidebarSection.TLabel", background=SIDEBAR, foreground=MUTED,
                    font=(FONT, 8, "bold"))
    style.configure("Brand.TLabel", background=SIDEBAR, foreground=TEXT,
                    font=(FONT, 16, "bold"))
    style.configure("BrandSub.TLabel", background=SIDEBAR, foreground=MUTED,
                    font=(FONT, 9))

    style.configure("TButton", background=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=SURFACE, darkcolor=SURFACE,
                    relief="flat", borderwidth=1, padding=(12, 7))
    style.map("TButton",
              background=[("active", HOVER), ("disabled", BG)],
              foreground=[("disabled", DISABLED)],
              bordercolor=[("focus", ACCENT)])
    style.configure("Accent.TButton", background=ACCENT, foreground="#ffffff",
                    bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                    relief="flat", borderwidth=0, padding=(14, 8),
                    font=(FONT, 10, "bold"))
    style.map("Accent.TButton",
              background=[("active", ACCENT_DARK), ("disabled", DISABLED)],
              foreground=[("disabled", "#f4f6f8")])

    style.configure("TEntry", fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=(8, 6))
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, rowheight=30, borderwidth=0,
                    font=(FONT, 10))
    style.configure("Treeview.Heading", background="#f8fafb", foreground=MUTED,
                    relief="flat", borderwidth=0, padding=(8, 8),
                    font=(FONT, 9, "bold"))
    style.map("Treeview",
              background=[("selected", ACCENT_SOFT)],
              foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", HOVER)])

    style.configure("Horizontal.TProgressbar", background=ACCENT,
                    troughcolor=BORDER, bordercolor=BORDER, lightcolor=ACCENT,
                    darkcolor=ACCENT, thickness=6)
    style.configure("TScrollbar", background=SURFACE, troughcolor=BG,
                    bordercolor=BORDER, arrowcolor=MUTED, relief="flat")
    style.map("TScrollbar", background=[("active", HOVER)])
    style.configure("TSeparator", background=BORDER)
    return style

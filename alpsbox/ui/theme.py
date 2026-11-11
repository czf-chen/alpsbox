# -*- coding: utf-8 -*-
"""UI styling: palette, fonts, ttk theme."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class Palette:
    """Light, modern flat palette."""

    BG = "#f6f7f9"            # window background
    CARD = "#ffffff"          # card background
    BORDER = "#e3e6ea"        # border
    BORDER_STRONG = "#cfd4da"

    TEXT = "#1f2328"          # primary text
    TEXT_MUTED = "#6b7280"    # secondary text
    TEXT_FAINT = "#9aa1ab"    # even fainter

    ACCENT = "#2563eb"        # accent colour (blue)
    ACCENT_HOVER = "#1d4ed8"
    ACCENT_LIGHT = "#eff4ff"

    OK = "#1a7f37"
    OK_LIGHT = "#eaf6ec"
    WARN = "#9a6700"
    WARN_LIGHT = "#fff8e6"
    ERR = "#cf222e"
    ERR_LIGHT = "#fdeced"

    HEADER = "#ffffff"
    SIDEBAR = "#f0f2f5"
    SIDEBAR_ACTIVE = "#ffffff"

    ROW_ALT = "#fafbfc"


# Fonts (pick an available CJK sans-serif per platform)
def pick_fonts() -> dict:
    import tkinter.font as tkfont
    families = set(tkfont.families())
    for cand in ("Microsoft YaHei UI", "Microsoft YaHei", "微软雅黑",
                 "PingFang SC", "Noto Sans CJK SC", "WenQuanYi Micro Hei",
                 "DejaVu Sans"):
        if cand in families:
            base = cand
            break
    else:
        base = "TkDefaultFont"

    mono = "Consolas"
    if mono not in families:
        for cand in ("DejaVu Sans Mono", "Courier New", "Courier"):
            if cand in families:
                mono = cand
                break

    return {
        "base": (base, 9),
        "bold": (base, 9, "bold"),
        "small": (base, 8),
        "h1": (base, 15, "bold"),
        "h2": (base, 11, "bold"),
        "btn": (base, 10, "bold"),
        "mono": (mono, 9),
    }


def apply_theme(root: tk.Tk) -> dict:
    """Configure ttk styles and return the font dictionary."""
    F = pick_fonts()
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        pass

    P = Palette
    st.configure(".", font=F["base"], background=P.BG, foreground=P.TEXT)
    st.configure("TFrame", background=P.BG)
    st.configure("Card.TFrame", background=P.CARD, relief="flat")
    st.configure("Sidebar.TFrame", background=P.SIDEBAR)

    st.configure("TLabel", background=P.BG, foreground=P.TEXT, font=F["base"])
    st.configure("Card.TLabel", background=P.CARD)
    st.configure("H1.TLabel", background=P.BG, foreground=P.TEXT, font=F["h1"])
    st.configure("H2.TLabel", background=P.CARD, foreground=P.TEXT, font=F["h2"])
    st.configure("Muted.TLabel", background=P.BG, foreground=P.TEXT_MUTED,
                 font=F["small"])
    st.configure("CardMuted.TLabel", background=P.CARD, foreground=P.TEXT_MUTED,
                 font=F["small"])
    st.configure("Ok.TLabel", background=P.CARD, foreground=P.OK, font=F["bold"])
    st.configure("Warn.TLabel", background=P.CARD, foreground=P.WARN, font=F["bold"])
    st.configure("Err.TLabel", background=P.CARD, foreground=P.ERR, font=F["bold"])

    # ---- normal buttons ----
    st.configure("TButton", font=F["base"], padding=(12, 6),
                 background=P.CARD, foreground=P.TEXT,
                 borderwidth=1, relief="solid")
    st.map("TButton",
           background=[("active", "#eef0f3"), ("pressed", "#e4e7eb")],
           bordercolor=[("!disabled", P.BORDER_STRONG)])

    # ---- primary button ----
    st.configure("Accent.TButton", font=F["btn"], padding=(18, 9),
                 background=P.ACCENT, foreground="#ffffff",
                 borderwidth=0, relief="flat")
    st.map("Accent.TButton",
           background=[("active", P.ACCENT_HOVER), ("pressed", "#1a44c8"),
                       ("disabled", "#9bb4ef")],
           foreground=[("disabled", "#f0f4ff")])

    # ---- danger / secondary buttons ----
    st.configure("Ghost.TButton", font=F["base"], padding=(12, 6),
                 background=P.BG, foreground=P.TEXT_MUTED, borderwidth=0)
    st.map("Ghost.TButton", background=[("active", "#e8eaee")])

    st.configure("Danger.TButton", font=F["base"], padding=(12, 6),
                 background=P.CARD, foreground=P.ERR, borderwidth=1)
    st.map("Danger.TButton", background=[("active", P.ERR_LIGHT)])

    # ---- sidebar navigation buttons ----
    st.configure("Nav.TButton", font=F["base"], padding=(16, 11),
                 anchor="w", background=P.SIDEBAR, foreground=P.TEXT_MUTED,
                 borderwidth=0, relief="flat")
    st.map("Nav.TButton",
           background=[("active", "#e6e9ee")],
           foreground=[("active", P.TEXT)])
    st.configure("NavActive.TButton", font=F["bold"], padding=(16, 11),
                 anchor="w", background=P.SIDEBAR_ACTIVE, foreground=P.ACCENT,
                 borderwidth=0, relief="flat")
    st.map("NavActive.TButton", background=[("active", P.SIDEBAR_ACTIVE)])

    # ---- input widgets ----
    st.configure("TEntry", fieldbackground="#ffffff", foreground=P.TEXT,
                 bordercolor=P.BORDER_STRONG, padding=(6, 5),
                 insertcolor=P.TEXT)
    st.map("TEntry", bordercolor=[("focus", P.ACCENT)])
    st.configure("TSpinbox", fieldbackground="#ffffff", foreground=P.TEXT,
                 bordercolor=P.BORDER_STRONG, padding=(4, 4), arrowsize=12)

    st.configure("TCheckbutton", background=P.CARD, foreground=P.TEXT,
                 font=F["base"], padding=(2, 3))
    st.map("TCheckbutton", background=[("active", P.CARD)])
    st.configure("TRadiobutton", background=P.CARD, foreground=P.TEXT,
                 font=F["base"], padding=(2, 3))
    st.map("TRadiobutton", background=[("active", P.CARD)])

    # ---- group box ----
    st.configure("TLabelframe", background=P.CARD, bordercolor=P.BORDER,
                 borderwidth=1, relief="solid")
    st.configure("TLabelframe.Label", background=P.CARD, foreground=P.TEXT,
                 font=F["h2"])

    # ---- progress bar ----
    # Note: do not define a custom "Sub.TProgressbar" style -- ttk will look for
    # "Horizontal.Sub.TProgressbar" to resolve the layout and raise Layout not
    # found when it is missing. Both progress bars use TProgressbar and are
    # distinguished by their labels.
    st.configure("TProgressbar", background=P.ACCENT, troughcolor="#e9ecf1",
                 bordercolor="#e9ecf1", lightcolor=P.ACCENT,
                 darkcolor=P.ACCENT, thickness=8)

    # ---- tree view ----
    st.configure("Treeview", font=F["base"], rowheight=24,
                 background="#ffffff", fieldbackground="#ffffff",
                 foreground=P.TEXT, bordercolor=P.BORDER, borderwidth=1)
    st.configure("Treeview.Heading", font=F["bold"], background="#f3f5f8",
                 foreground=P.TEXT_MUTED, relief="flat", padding=(6, 7))
    st.map("Treeview.Heading", background=[("active", "#eaeef3")])
    st.map("Treeview", background=[("selected", P.ACCENT_LIGHT)],
           foreground=[("selected", P.TEXT)])

    # ---- separators ----
    st.configure("TSeparator", background=P.BORDER)

    return F

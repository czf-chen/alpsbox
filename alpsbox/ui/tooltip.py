# -*- coding: utf-8 -*-
"""Tooltip and help-icon widgets.

Tkinter has no native tooltip, so this module provides a lightweight one:
  * appears after the pointer rests on the widget for ``delay`` milliseconds
  * disappears immediately on leave or click
  * supports multi-line text (\\n)
  * attaches below the pointer and flips near screen edges
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..i18n import t as _T
from .theme import Palette
from .. import text_ui  # noqa: F401


class Tooltip:
    """Attach a tooltip to any widget."""

    def __init__(self, widget, text: str, delay: int = 450,
                 wraplength: int = 420, bg: str = "#2b3138"):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.bg = bg
        self._after_id = None
        self._tip = None

        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        # Clean up when the widget is destroyed
        widget.bind("<Destroy>", lambda e: self._hide(), add="+")

    # ---- internals ----
    def _schedule(self, _evt=None):
        self._cancel()
        self._after_id = self.widget.after(self.delay, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self._tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 14
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return

        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        try:
            tw.wm_attributes("-alpha", 0.97)
        except Exception:
            pass

        outer = tk.Frame(tw, background="#000000", bd=0)
        outer.pack()
        lbl = tk.Label(outer, text=self.text, justify="left",
                       background=self.bg, foreground="#ffffff",
                       font=("Microsoft YaHei UI", 9) if _has_yahei() else ("TkDefaultFont", 9),
                       wraplength=self.wraplength, padx=10, pady=7)
        lbl.pack(padx=1, pady=1)
        tw.update_idletasks()

        # Keep it on screen
        sw = tw.winfo_screenwidth()
        sh = tw.winfo_screenheight()
        w, h = tw.winfo_width(), tw.winfo_height()
        if x + w > sw - 8:
            x = max(8, sw - w - 8)
        if y + h > sh - 8:
            y = max(8, self.widget.winfo_rooty() - h - 8)
        tw.wm_geometry("+%d+%d" % (x, y))

        self._tip = tw

    def _hide(self, _evt=None):
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None

    def set_text(self, text: str):
        self.text = text


def _has_yahei() -> bool:
    try:
        import tkinter.font as tkfont
        return "Microsoft YaHei UI" in set(tkfont.families())
    except Exception:
        return False


class HelpDot(tk.Label):
    """Round "?" icon.

    * hover shows a short description
    * clicking opens the full help window by default (when no command is given)
    """

    def __init__(self, parent, text: str, bg: str = Palette.CARD,
                 command=None, size: int = 16, title: str = ""):
        super().__init__(parent, text="?", width=1, height=1,
                         background=bg, foreground=Palette.TEXT_FAINT,
                         font=("", size - 4, "bold"), cursor="hand2",
                         bd=0, highlightthickness=0)
        self._text = text
        self._title = title or t("ui.help_title")
        self._tip = Tooltip(self, text)
        self._command = command
        self.bind("<Enter>", self._hover_on, add="+")
        self.bind("<Leave>", self._hover_off, add="+")
        self.bind("<Button-1>", self._on_click, add="+")

    def _hover_on(self, _e=None):
        self.configure(foreground=Palette.ACCENT)

    def _hover_off(self, _e=None):
        self.configure(foreground=Palette.TEXT_FAINT)

    def _on_click(self, _e=None):
        # Hide the tooltip so it does not overlap the window
        try:
            self._tip._hide()
        except Exception:
            pass
        if self._command:
            self._command()
        else:
            show_help_window(self, self._title, self._text)

    def set_text(self, t: str):
        self._text = t
        self._tip.set_text(t)


def show_help_window(parent, title: str, content: str,
                     width: int = 620, height: int = 480):
    """Generic help window (independent of the gui module, callable anywhere)."""
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=Palette.CARD)
    try:
        win.transient(parent.winfo_toplevel())
    except Exception:
        pass
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w, h = min(width, sw - 100), min(height, sh - 100)
    win.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 3))
    win.minsize(420, 280)

    head = tk.Frame(win, bg=Palette.CARD)
    head.pack(fill="x", padx=18, pady=(14, 6))
    tk.Label(head, text=title, bg=Palette.CARD, fg=Palette.ACCENT,
             font=("", 11, "bold")).pack(side="left")

    body = tk.Frame(win, bg=Palette.CARD)
    body.pack(fill="both", expand=True, padx=18, pady=(0, 10))
    txt = tk.Text(body, wrap="word", bg="#fbfcfd", fg=Palette.TEXT,
                  relief="flat", padx=12, pady=10,
                  highlightbackground=Palette.BORDER, highlightthickness=1,
                  font=("", 9))
    sb = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)
    txt.insert("1.0", content)
    txt.configure(state="disabled")

    btn = ttk.Button(win, text=t("close"), command=win.destroy)
    btn.pack(pady=(0, 14))
    win.bind("<Escape>", lambda e: win.destroy())
    win.focus_set()
    return win


def labeled_with_help(parent, label: str, help_text: str,
                      bg: str = Palette.CARD, font=None,
                      width: int | None = None, on_help_click=None):
    """Build a "label + ?" group and return (frame, label_widget)."""
    f = tk.Frame(parent, background=bg)
    lb = tk.Label(f, text=label, background=bg, foreground=Palette.TEXT,
                  font=font or ("TkDefaultFont", 9), anchor="w")
    if width:
        lb.configure(width=width)
    lb.pack(side="left")
    dot = HelpDot(f, help_text, bg=bg, command=on_help_click)
    dot.pack(side="left", padx=(4, 0))
    return f, lb

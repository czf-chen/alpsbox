# -*- coding: utf-8 -*-
"""Generic UI widgets."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import Palette as P


class ScrollFrame(tk.Frame):
    """Vertically scrollable container.

    * content goes into ``self.inner``
    * the scrollbar is hidden while the content fits the visible height
    * mouse wheel is supported
    """

    def __init__(self, parent, bg: str = P.BG):
        super().__init__(parent, bg=bg)
        self._bg = bg

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll_set)

        self.canvas.pack(side="left", fill="both", expand=True)
        # The scrollbar starts hidden

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self._wheel_bound = False
        self.bind("<Enter>", self._bind_wheel)
        self.bind("<Leave>", self._unbind_wheel)

    # ---- events ----
    def _on_inner_configure(self, _evt=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._sync_scrollbar()

    def _on_canvas_configure(self, evt):
        self.canvas.itemconfigure(self._win, width=evt.width)
        self._sync_scrollbar()

    def _on_scroll_set(self, first, last):
        self.vsb.set(first, last)
        self._sync_scrollbar(float(first), float(last))

    def _sync_scrollbar(self, first=None, last=None):
        """Hide the scrollbar while the content fits."""
        if first is None or last is None:
            bbox = self.canvas.bbox("all")
            if not bbox:
                return
            need = bbox[3] - bbox[1]
            have = self.canvas.winfo_height()
            show = need > have + 4
        else:
            show = not (first <= 0.0 and last >= 1.0)
        if show and not self.vsb.winfo_ismapped():
            self.vsb.pack(side="right", fill="y")
        elif not show and self.vsb.winfo_ismapped():
            self.vsb.pack_forget()

    # ---- mouse wheel ----
    def _bind_wheel(self, _e=None):
        if self._wheel_bound:
            return
        self._wheel_bound = True
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", self._on_wheel)
        self.canvas.bind_all("<Button-5>", self._on_wheel)

    def _unbind_wheel(self, _e=None):
        if not self._wheel_bound:
            return
        self._wheel_bound = False
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                self.canvas.unbind_all(ev)
            except Exception:
                pass

    def _on_wheel(self, evt):
        try:
            if getattr(evt, "num", None) == 4:
                delta = -1
            elif getattr(evt, "num", None) == 5:
                delta = 1
            else:
                delta = -1 if evt.delta > 0 else 1
            self.canvas.yview_scroll(delta * 2, "units")
        except Exception:
            pass


class Banner(tk.Frame):
    """Top banner (success / warning / error) with an optional action link."""

    STYLES = {
        "ok": (P.OK_LIGHT, P.OK),
        "warn": (P.WARN_LIGHT, P.WARN),
        "err": (P.ERR_LIGHT, P.ERR),
        "info": (P.ACCENT_LIGHT, P.ACCENT),
    }

    def __init__(self, parent, text: str = "", kind: str = "info",
                 action_text: str | None = None, command=None,
                 font=None):
        bg, fg = self.STYLES.get(kind, self.STYLES["info"])
        super().__init__(parent, bg=bg, highlightbackground=fg,
                         highlightthickness=1)
        self._lbl = tk.Label(self, text=text, bg=bg, fg=fg, anchor="w",
                             justify="left", font=font, padx=10, pady=7)
        self._lbl.pack(side="left", fill="x", expand=True)
        self._btn = None
        if action_text and command:
            self._btn = tk.Button(self, text=action_text, bg=bg, fg=fg,
                                  activebackground=bg, activeforeground=fg,
                                  relief="flat", cursor="hand2", font=font,
                                  command=command, bd=0)
            self._btn.pack(side="right", padx=8)

    def set(self, text: str, kind: str = "info"):
        bg, fg = self.STYLES.get(kind, self.STYLES["info"])
        self.configure(bg=bg, highlightbackground=fg)
        self._lbl.configure(text=text, bg=bg, fg=fg)
        if self._btn:
            self._btn.configure(bg=bg, fg=fg, activebackground=bg, activeforeground=fg)

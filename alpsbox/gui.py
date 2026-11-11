# -*- coding: utf-8 -*-
"""ALPSbox graphical interface.

Layout:
    top     title + environment status + environment details
    left    side navigation (home / processing / ROI atlas / results / QC /
            log / help)
    body    the corresponding page
    bottom  overall progress bar + per-subject step progress bar

Key points:
    * the results table is persisted to ~/.alpsbox/session.json and restored
      automatically on restart
    * each "?" beside a parameter supports both a hover summary and a click
      that opens the full description
    * processing runs in a background thread so the UI stays responsive;
      stopping and closing both ask for confirmation, protecting a subject
      that is still running
    * every mention of the "reference implementation" (older documentation
      called it "official alps.sh") in the UI carries a formal citation:
      definitions and sources
      are in alpsbox/citations.py / docs/CITATIONS.md, and the GUI
      Help > References page lists the full references.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import time
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from . import qc as qcmod
from . import helptext
from .i18n import t
from . import i18n
from .batch import (collect_jobs, collect_results, preflight,
                    topup_layout_errors, write_preflight_report,
                    write_qc_report, write_summary)
from .config import detect_env
from .helptext import HELP
from .pipeline import AlspPipeline, AlspResult, PipelineOptions
from .roi import DEFAULT_RADIUS_MM
from .ui import session as sess
from .ui import recent
from .ui.theme import Palette as P, apply_theme
from .ui.tooltip import HelpDot, Tooltip, show_help_window
from .ui.widgets import ScrollFrame
from .ui.widgets2 import FigurePanel, RoiViewer, RoundButton, RoundedCard


class QueueWriter:
    def __init__(self, q):
        self.q = q

    def write(self, s):
        if s:
            self.q.put(("log", s))

    def flush(self):
        pass

    def isatty(self):
        return False


class App(tk.Tk):

    # Tk variables holding user input / advanced settings. They are recreated
    # when the UI is rebuilt for a language switch, so their values are
    # snapshotted and restored (otherwise a running/prepared job loses its
    # input folder and settings).
    _UI_STATE_VARS = (
        "mode", "var_in", "var_out", "var_threads", "var_unring",
        "var_regqc", "var_force", "var_workers", "roi_mode", "var_radius",
        "var_custom", "var_bet_f", "var_reg_cost", "var_template",
        "var_denoise", "var_topup", "var_topup_mode", "var_topup_second",
        "var_topup_config",
    )

    def __init__(self):
        super().__init__()
        self.title("ALPSbox  %s" % __version__)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(1320, max(1060, sw - 60))
        h = min(880, max(700, sh - 80))
        self.geometry("%dx%d+%d+%d" % (w, h, max(0, (sw - w) // 2),
                                       max(0, (sh - h) // 3)))
        self.minsize(1060, 680)
        self.configure(bg=P.BG)
        self.F = apply_theme(self)

        self.q = queue.Queue()
        self.worker = None
        self.stop_flag = threading.Event()
        self.env = None
        self.t_start = None
        self.current_subject = ""
        self.records = sess.load_session()
        sess.attach_qc(self.records)
        self._pages = {}
        self._nav = {}
        self._active = None
        self._closing = False
        self._run_mode = "single"
        self._qc_filter = "all"
        self._qc_reports = []
        self._last_out = ""
        self._lookup_root = recent.recall()

        self._build_header()
        self._build_statusbar()      # claim the bottom space first, otherwise body squeezes it out
        self._build_body()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(120, self._poll_queue)
        self.after(500, self._tick_clock)
        self._show_page("home")
        self._refresh_table()
        self._refresh_qc()
        self._set_qc_filter("all")
        self._log(t("log.started", __version__), "ok")
        if self.records:
            self._log(t("log.restored", len(self.records)), "muted")
        self._check_env_async()

    # =================================================================
    # language switching
    # =================================================================
    def _switch_lang(self, code):
        """Switch the UI language: save the preference, then rebuild the whole
        window; no process restart is needed."""
        if code == i18n.get_lang():
            return
        i18n.set_lang(code)
        self._rebuild_ui()

    def _snapshot_ui_state(self) -> dict:
        """Capture log text, progress and input-variable state before a rebuild."""
        st = {"log": "", "vars": {}, "page": self._active or "home",
              "adv_open": False}
        if hasattr(self, "txt"):
            try:
                st["log"] = self.txt.get("1.0", "end-1c")
            except Exception:
                pass
        for name in self._UI_STATE_VARS:
            var = getattr(self, name, None)
            if var is None:
                continue
            try:
                st["vars"][name] = var.get()
            except Exception:
                pass
        for name in ("pb_total", "pb_cur"):
            w = getattr(self, name, None)
            if w is not None:
                try:
                    st[name] = float(w["value"])
                except Exception:
                    pass
        for name in ("lbl_total", "lbl_cur", "lbl_elapsed"):
            w = getattr(self, name, None)
            if w is not None:
                try:
                    st[name] = str(w.cget("text"))
                except Exception:
                    pass
        ad = getattr(self, "_adv_open", None)
        if ad is not None:
            try:
                st["adv_open"] = bool(ad.get())
            except Exception:
                pass
        return st

    def _restore_ui_state(self, st: dict):
        """Restore the snapshotted state after the rebuilt widgets exist."""
        page = st.get("page") or "home"
        if page in self._pages:
            self._show_page(page)
        for name, value in (st.get("vars") or {}).items():
            var = getattr(self, name, None)
            if var is None:
                continue
            try:
                var.set(value)
            except Exception:
                pass
        # Mode-dependent label and controls that are not driven by traces.
        try:
            self.lbl_in.configure(
                text=t("proc.indir") if self.mode.get() == "single"
                else t("proc.rootdir"))
        except Exception:
            pass
        try:
            self._on_roi()
        except Exception:
            pass
        # Log history.
        text = st.get("log") or ""
        if text:
            try:
                if not text.endswith("\n"):
                    text += "\n"
                self.txt.configure(state="normal")
                self.txt.insert("1.0", text)
                self.txt.see("end")
                self.txt.configure(state="disabled")
            except Exception:
                pass
        # Progress bars / labels (the running worker keeps updating them).
        for name in ("pb_total", "pb_cur"):
            w = getattr(self, name, None)
            if w is not None and name in st:
                try:
                    w["value"] = st[name]
                except Exception:
                    pass
        for name in ("lbl_total", "lbl_cur", "lbl_elapsed"):
            w = getattr(self, name, None)
            if w is not None and name in st:
                try:
                    w.configure(text=st[name])
                except Exception:
                    pass
        try:
            self._update_clock()
        except Exception:
            pass
        for fn in (self._update_summary, self._update_adv_summary,
                   self._update_topup_ui):
            try:
                fn()
            except Exception:
                pass
        if st.get("adv_open"):
            try:
                self._toggle_advanced()
            except Exception:
                pass

    def _rebuild_ui(self):
        """Destroy and rebuild the whole UI, keeping the data, current page,
        log history and (while a job is running) the progress/input state."""
        state = self._snapshot_ui_state()
        keep_page = state.get("page") or "home"
        # Drop references to the old widgets first: otherwise hasattr is true
        # while the widget is already destroyed, and rebuilding raises
        # "invalid command name"
        for attr in ("badge", "lbl_session", "lbl_count", "txt", "tree",
                     "qc_tree", "lbl_th", "lbl_total", "lbl_elapsed",
                     "pb_total", "pb_cur", "lbl_cur", "lbl_summary",
                     "lbl_in", "lbl_qc_top", "roi_viewer", "_qc_panels",
                     "_adv_hdr", "_adv_body", "_adv_open", "spn_betf",
                     "cmb_cost", "ent_tpl", "btn_tpl", "var_bet_f",
                     "var_reg_cost", "var_template", "var_denoise",
                     "lbl_adv_cur", "btn_adv_reset", "_home_lang_btns"):
            if hasattr(self, attr):
                try:
                    delattr(self, attr)
                except Exception:
                    pass
        try:
            for w in self.winfo_children():
                w.destroy()
        except Exception:
            pass
        self._pages = {}
        self._nav = {}
        self._qc_stat = {}
        self._qc_btns = {}
        self._active = None
        self._build_header()
        self._build_statusbar()
        self._build_body()
        self._restore_ui_state(state)
        try:
            self._refresh_table()
            self._refresh_qc()
            self._set_qc_filter(self._qc_filter)
        except Exception:
            pass
        self._log(t("log.lang_switched",
                    i18n.LANGS.get(i18n.get_lang(), "")), "muted")

    # =================================================================
    # header
    # =================================================================
    def _build_header(self):
        hd = tk.Frame(self, bg=P.HEADER, height=58)
        hd.pack(fill="x", side="top")
        hd.pack_propagate(False)

        left = tk.Frame(hd, bg=P.HEADER)
        left.pack(side="left", padx=(20, 0), pady=11)
        tk.Label(left, text="ALPSbox", bg=P.HEADER, fg=P.ACCENT,
                 font=(self.F["h1"][0], 16, "bold")).pack(side="left")
        tk.Label(left, text=t("app.subtitle"), bg=P.HEADER,
                 fg=P.TEXT_MUTED, font=self.F["small"]).pack(side="left", padx=(11, 0))

        right = tk.Frame(hd, bg=P.HEADER)
        right.pack(side="right", padx=(0, 18), pady=11)

        self.badge = tk.Label(right, text="  " + t("env.checking") + "  ", bg="#eef0f3",
                              fg=P.TEXT_MUTED, font=self.F["small"], padx=6, pady=4)
        self.badge.pack(side="right", padx=(10, 0))

        HelpDot(right, HELP["env"], bg=P.HEADER,
                title=t("tip.env")).pack(
            side="right", padx=(6, 0))

        RoundButton(right, t("env.detail"), command=self._show_env_dialog,
                    variant="light", height=28, padx=12,
                    parent_bg=P.HEADER).pack(side="right", padx=(0, 6))
        RoundButton(right, t("refresh"), command=self._check_env_async,
                    variant="light", height=28, padx=12,
                    parent_bg=P.HEADER).pack(side="right")

        # Language switch: two small labels, the current language highlighted
        lang_wrap = tk.Frame(right, bg=P.HEADER)
        lang_wrap.pack(side="right", padx=(0, 12))
        cur = i18n.get_lang()
        for code, label in (("zh_CN", "中文"), ("en", "EN")):
            on = (code == cur)
            lb = tk.Label(lang_wrap, text=label, bg=P.HEADER,
                          fg=P.ACCENT if on else P.TEXT_FAINT,
                          font=(self.F["small"][0], self.F["small"][1],
                                "bold" if on else "normal"),
                          padx=6, pady=3, cursor="hand2")
            lb.pack(side="left")
            lb.bind("<Button-1>", lambda e, c=code: self._switch_lang(c))
            lb.bind("<Enter>", lambda e, w=lb: w.configure(fg=P.ACCENT))
            lb.bind("<Leave>", lambda e, w=lb, c=code: w.configure(
                fg=P.ACCENT if c == i18n.get_lang() else P.TEXT_FAINT))
        tk.Label(lang_wrap, text="|", bg=P.HEADER, fg=P.BORDER_STRONG,
                 font=self.F["small"]).pack(side="left", padx=2)

        tk.Frame(self, bg=P.BORDER, height=1).pack(fill="x", side="top")

    # =================================================================
    # body
    # =================================================================
    def _build_body(self):
        body = tk.Frame(self, bg=P.BG)
        body.pack(fill="both", expand=True, side="top")

        side = tk.Frame(body, bg=P.SIDEBAR, width=176)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Frame(side, bg=P.SIDEBAR, height=12).pack(fill="x")
        items = [("home", t("nav.home")),
                 ("process", t("nav.process")), ("roi", t("nav.roi")),
                 ("results", t("nav.results")),
                 ("qc", t("nav.qc")),
                 ("log", t("nav.log")), ("help", t("nav.help"))]
        for key, label in items:
            f = tk.Frame(side, bg=P.SIDEBAR, cursor="hand2")
            f.pack(fill="x", padx=(10, 10), pady=1)
            indicator = tk.Frame(f, bg=P.SIDEBAR, width=3)
            indicator.pack(side="left", fill="y")
            lb = tk.Label(f, text="   " + label, bg=P.SIDEBAR, fg=P.TEXT_MUTED,
                          font=self.F["base"], anchor="w", padx=10, pady=10,
                          cursor="hand2")
            lb.pack(side="left", fill="x", expand=True)
            for w in (f, lb):
                w.bind("<Button-1>", lambda e, k=key: self._show_page(k))
                w.bind("<Enter>", lambda e, k=key: self._nav_hover(k, True))
                w.bind("<Leave>", lambda e, k=key: self._nav_hover(k, False))
            self._nav[key] = (f, lb, indicator)

        bot = tk.Frame(side, bg=P.SIDEBAR)
        bot.pack(side="bottom", fill="x", pady=12, padx=14)
        self.lbl_session = tk.Label(bot, text="", bg=P.SIDEBAR, fg=P.TEXT_FAINT,
                                    font=self.F["small"], anchor="w", justify="left")
        self.lbl_session.pack(fill="x")

        tk.Frame(body, bg=P.BORDER, width=1).pack(side="left", fill="y")

        self.content = tk.Frame(body, bg=P.BG)
        self.content.pack(side="left", fill="both", expand=True)

        self._pages["home"] = self._page_home()
        self._pages["process"] = self._page_process()
        self._pages["roi"] = self._page_roi()
        self._pages["results"] = self._page_results()
        self._pages["qc"] = self._page_qc()
        self._pages["log"] = self._page_log()
        self._pages["help"] = self._page_help()

    def _nav_hover(self, key, on):
        f, lb, ind = self._nav[key]
        if self._active == key:
            return
        lb.configure(fg=P.TEXT if on else P.TEXT_MUTED)
        f.configure(bg="#e7eaef" if on else P.SIDEBAR)
        lb.configure(bg="#e7eaef" if on else P.SIDEBAR)

    def _show_page(self, key):
        for k, f in self._pages.items():
            f.pack_forget()
            nf, lb, ind = self._nav[k]
            nf.configure(bg=P.SIDEBAR)
            lb.configure(bg=P.SIDEBAR, fg=P.TEXT_MUTED, font=self.F["base"])
            ind.configure(bg=P.SIDEBAR)
        self._pages[key].pack(fill="both", expand=True, padx=18, pady=14)
        nf, lb, ind = self._nav[key]
        nf.configure(bg="#ffffff")
        lb.configure(bg="#ffffff", fg=P.ACCENT, font=self.F["bold"])
        ind.configure(bg=P.ACCENT)
        self._active = key

    def _card(self, parent, title=None, pady=(0, 12)):
        card = RoundedCard(parent, padding=(18, 15))
        card.pack(fill="x", pady=pady)
        if title:
            tk.Label(card.body, text=title, bg=P.CARD, fg=P.TEXT,
                     font=self.F["h2"], anchor="w").pack(fill="x", pady=(0, 10))
        return card.body

    # =================================================================
    # page: home (welcome / language selection)
    # =================================================================
    def _page_home(self):
        shell = tk.Frame(self.content, bg=P.BG)
        sc = ScrollFrame(shell, bg=P.BG)
        sc.pack(fill="both", expand=True)
        page = sc.inner

        # ---- Hero ----
        card = RoundedCard(page, padding=(36, 28))
        card.pack(fill="x", pady=(0, 14))
        body = card.body
        tk.Label(body, text="ALPSbox", bg=P.CARD, fg=P.ACCENT,
                 font=("", 30, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=t("home.tagline"), bg=P.CARD, fg=P.TEXT,
                 font=("", 15, "bold"), anchor="w", justify="left",
                 wraplength=900).pack(fill="x", pady=(4, 6))
        tk.Label(body, text=t("home.subtitle"), bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["base"], anchor="w", justify="left",
                 wraplength=900).pack(fill="x")
        tk.Label(body, text="GUI + CLI   ·   v%s" % __version__,
                 bg=P.CARD, fg=P.TEXT_FAINT,
                 font=self.F["small"], anchor="w").pack(fill="x",
                                                       pady=(10, 0))

        # ---- Language selection (first and most prominent) ----
        card = RoundedCard(page, padding=(30, 18))
        card.pack(fill="x", pady=(0, 14))
        body = card.body
        tk.Label(body, text=t("home.language"), bg=P.CARD, fg=P.ACCENT,
                 font=("", 15, "bold"), anchor="w").pack(fill="x")
        row = tk.Frame(body, bg=P.CARD)
        row.pack(fill="x", pady=(10, 4))
        self._home_lang_btns = {}
        cur = i18n.get_lang()
        for code, name in i18n.available_langs():
            b = RoundButton(
                row, name, command=lambda c=code: self._switch_lang(c),
                variant="accent" if code == cur else "light",
                height=40, padx=26, parent_bg=P.CARD)
            b.pack(side="left", padx=(0, 10))
            self._home_lang_btns[code] = b
        tk.Label(body, text=t("home.language_hint"), bg=P.CARD,
                 fg=P.TEXT_FAINT, font=self.F["small"],
                 anchor="w").pack(fill="x")

        # ---- Three-step start ----
        card = RoundedCard(page, padding=(30, 18))
        card.pack(fill="x", pady=(0, 14))
        body = card.body
        row = tk.Frame(body, bg=P.CARD)
        row.pack(fill="x")
        for i, (tt, dd) in enumerate((
                (t("home.step1_title"), t("home.step1_desc")),
                (t("home.step2_title"), t("home.step2_desc")),
                (t("home.step3_title"), t("home.step3_desc"))), 1):
            col = tk.Frame(row, bg=P.CARD)
            col.pack(side="left", fill="both", expand=True, padx=(0, 18))
            head = tk.Frame(col, bg=P.CARD)
            head.pack(fill="x")
            tk.Label(head, text=str(i), bg=P.ACCENT, fg="#ffffff",
                     font=("", 10, "bold"), width=2, height=1).pack(side="left")
            tk.Label(head, text=tt, bg=P.CARD, fg=P.TEXT,
                     font=("", 11, "bold"), anchor="w").pack(
                         side="left", padx=(8, 0))
            tk.Label(col, text=dd, bg=P.CARD, fg=P.TEXT_MUTED,
                     font=self.F["small"], anchor="w", justify="left",
                     wraplength=300).pack(fill="x", pady=(6, 0))
        b = RoundButton(body, t("home.get_started"),
                        command=lambda: self._show_page("process"),
                        variant="accent", height=44, padx=34,
                        parent_bg=P.CARD, font=("", 11, "bold"))
        self._home_start_btn = b
        b.pack(anchor="w", pady=(16, 2))

        # ---- privacy / scope ----
        card = RoundedCard(page, padding=(30, 18))
        card.pack(fill="x", pady=(0, 6))
        body = card.body
        tk.Label(body, text=t("home.privacy_title"), bg=P.CARD, fg=P.OK,
                 font=("", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=t("home.privacy"), bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"], anchor="w", justify="left",
                 wraplength=900).pack(fill="x", pady=(2, 10))
        tk.Label(body, text=t("home.not_title"), bg=P.CARD, fg=P.WARN,
                 font=("", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=t("home.not_body"), bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"], anchor="w", justify="left",
                 wraplength=900).pack(fill="x", pady=(2, 0))
        return shell

    # =================================================================
    # page: processing
    # =================================================================
    def _page_process(self):
        shell = tk.Frame(self.content, bg=P.BG)
        sc = ScrollFrame(shell, bg=P.BG)
        sc.pack(fill="both", expand=True)
        page = sc.inner

        # --- input ---
        box = self._card(page, t("proc.input"))
        r0 = tk.Frame(box, bg=P.CARD)
        r0.pack(fill="x")
        self.mode = tk.StringVar(value="single")
        ttk.Radiobutton(r0, text=t("proc.single"), variable=self.mode, value="single",
                        command=self._on_mode).pack(side="left", padx=(0, 3))
        HelpDot(r0, HELP["input_single"], title=t("tip.input_single")).pack(
            side="left", padx=(0, 24))
        ttk.Radiobutton(r0, text=t("proc.batch"), variable=self.mode,
                        value="batch", command=self._on_mode).pack(side="left", padx=(0, 3))
        HelpDot(r0, HELP["input_batch"],
                title=t("tip.input_batch")).pack(side="left")

        r1 = tk.Frame(box, bg=P.CARD)
        r1.pack(fill="x", pady=(12, 5))
        self.lbl_in = tk.Label(r1, text=t("proc.indir"), bg=P.CARD, fg=P.TEXT,
                               font=self.F["base"], anchor="w",
                               cursor="hand2")
        self.lbl_in.pack(side="left")
        self.lbl_in.bind("<Button-1>", lambda e: show_help_window(
            self, t("tip.input_single"),
            HELP["input_single" if self.mode.get() == "single" else "input_batch"]))
        HelpDot(r1, HELP["input_single"], title=t("tip.input_single")).pack(
            side="left", padx=(3, 8))
        self.var_in = tk.StringVar()
        e1 = ttk.Entry(r1, textvariable=self.var_in, font=self.F["base"])
        e1.pack(side="left", fill="x", expand=True, padx=(0, 7))
        Tooltip(e1, HELP["input_single"])
        RoundButton(r1, t("browse"), command=self._browse_input, variant="light",
                    height=30, padx=14).pack(side="left")

        r2 = tk.Frame(box, bg=P.CARD)
        r2.pack(fill="x", pady=(5, 0))
        tk.Label(r2, text=t("proc.outdir"), bg=P.CARD, fg=P.TEXT, font=self.F["base"],
                 anchor="w").pack(side="left")
        HelpDot(r2, HELP["outdir"], title=t("proc.outdir")).pack(side="left", padx=(3, 8))
        self.var_out = tk.StringVar()
        e2 = ttk.Entry(r2, textvariable=self.var_out, font=self.F["base"])
        e2.pack(side="left", fill="x", expand=True, padx=(0, 7))
        Tooltip(e2, HELP["outdir"])
        RoundButton(r2, t("browse"), command=self._browse_out, variant="light",
                    height=30, padx=14).pack(side="left")

        tk.Label(box, text=t("proc.hint"),
                 bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"], anchor="w",
                 justify="left", wraplength=980).pack(fill="x", pady=(10, 0))

        # --- parameters ---
        box2 = self._card(page, t("proc.params"))
        g1 = tk.Frame(box2, bg=P.CARD)
        g1.pack(fill="x")
        tk.Label(g1, text=t("proc.threads"), bg=P.CARD, fg=P.TEXT).pack(side="left")
        HelpDot(g1, HELP["threads"], title=t("proc.threads")).pack(side="left", padx=(3, 5))
        self.var_threads = tk.IntVar(value=4)
        sb1 = ttk.Spinbox(g1, from_=1, to=32, width=5, textvariable=self.var_threads)
        sb1.pack(side="left", padx=(0, 26))
        Tooltip(sb1, HELP["threads"])

        self.var_unring = tk.BooleanVar(value=True)
        cb1 = ttk.Checkbutton(g1, text=t("proc.unring"), variable=self.var_unring)
        cb1.pack(side="left")
        HelpDot(g1, HELP["unring"], title=t("proc.unring")).pack(side="left", padx=(3, 26))
        Tooltip(cb1, HELP["unring"])

        # Registration robustness QC (optional)
        self.var_regqc = tk.BooleanVar(value=False)
        cb_rq = ttk.Checkbutton(g1, text=t("proc.regqc"), variable=self.var_regqc)
        cb_rq.pack(side="left")
        HelpDot(g1, HELP["regqc"], title=t("proc.regqc")).pack(
            side="left", padx=(3, 26))
        Tooltip(cb_rq, HELP["regqc"])

        self.var_force = tk.BooleanVar(value=False)
        cb2 = ttk.Checkbutton(g1, text=t("proc.force"), variable=self.var_force)
        cb2.pack(side="left")
        HelpDot(g1, HELP["force"], title=t("proc.force")).pack(side="left", padx=(3, 0))
        Tooltip(cb2, HELP["force"])

        g2 = tk.Frame(box2, bg=P.CARD)
        g2.pack(fill="x", pady=(12, 0))
        tk.Label(g2, text=t("proc.workers"), bg=P.CARD, fg=P.TEXT).pack(side="left")
        HelpDot(g2, HELP["workers"], title=t("proc.workers")).pack(side="left", padx=(3, 5))
        self.var_workers = tk.IntVar(value=1)
        sb2 = ttk.Spinbox(g2, from_=1, to=8, width=5, textvariable=self.var_workers)
        sb2.pack(side="left", padx=(0, 9))
        Tooltip(sb2, HELP["workers"])
        tk.Label(g2, text=t("proc.workers_hint"), bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"]).pack(side="left")

        g3 = tk.Frame(box2, bg=P.CARD)
        g3.pack(fill="x", pady=(14, 0))
        tk.Label(g3, text=t("proc.roi_src"), bg=P.CARD, fg=P.TEXT).pack(side="left", padx=(0, 12))

        self.roi_mode = tk.StringVar(value="bundled")
        rb_a = ttk.Radiobutton(g3, text=t("proc.roi_bundled"), variable=self.roi_mode,
                               value="bundled", command=self._on_roi)
        rb_a.pack(side="left", padx=(0, 3))
        HelpDot(g3, HELP["roi_bundled"],
                title=t("tip.roi_bundled")).pack(side="left", padx=(0, 16))
        Tooltip(rb_a, HELP["roi_bundled"])

        rb_b = ttk.Radiobutton(g3, text=t("proc.roi_sphere"), variable=self.roi_mode,
                               value="sphere", command=self._on_roi)
        rb_b.pack(side="left", padx=(0, 3))
        self.var_radius = tk.DoubleVar(value=DEFAULT_RADIUS_MM)
        self.spn_radius = ttk.Spinbox(g3, from_=1.0, to=6.0, increment=0.5,
                                      width=5, textvariable=self.var_radius,
                                      state="disabled")
        self.spn_radius.pack(side="left", padx=(3, 2))
        tk.Label(g3, text=t("proc.roi_mm"), bg=P.CARD, fg=P.TEXT).pack(side="left", padx=(0, 3))
        HelpDot(g3, HELP["roi_sphere"],
                title=t("tip.roi_sphere")).pack(side="left", padx=(0, 16))
        Tooltip(self.spn_radius, HELP["roi_sphere"])

        rb_c = ttk.Radiobutton(g3, text=t("proc.roi_custom"), variable=self.roi_mode,
                               value="custom", command=self._on_roi)
        rb_c.pack(side="left")
        HelpDot(g3, HELP["roi_custom"],
                title=t("tip.roi_custom")).pack(side="left", padx=(3, 0))
        Tooltip(rb_c, HELP["roi_custom"])

        g4 = tk.Frame(box2, bg=P.CARD)
        g4.pack(fill="x", pady=(8, 0))
        self.var_custom = tk.StringVar()
        self.ent_custom = ttk.Entry(g4, textvariable=self.var_custom, state="disabled")
        self.ent_custom.pack(side="left", fill="x", expand=True, padx=(0, 7))
        self.btn_custom = RoundButton(g4, t("proc.choose"), command=self._browse_custom,
                                      variant="light", height=28, padx=12)
        self.btn_custom.pack(side="left")
        self.btn_custom.set_enabled(False)

        # --- advanced (collapsible drawer: detail parameters; the defaults are
        # the recommended values) ---
        adv = RoundedCard(page, padding=(18, 12))
        adv.pack(fill="x", pady=(0, 12))
        self._adv_open = tk.BooleanVar(value=False)
        self._adv_hdr = tk.Label(
            adv.body, text="▸  " + t("proc.advanced"), bg=P.CARD,
            fg=P.TEXT_MUTED, font=self.F["h2"], anchor="w", cursor="hand2")
        self._adv_hdr.pack(fill="x")
        self._adv_hdr.bind("<Button-1>", self._toggle_advanced)

        self._adv_body = tk.Frame(adv.body, bg=P.CARD)

        # Advanced parameters from the previous run (stored in ~/.alpsbox/prefs.json)
        _advp = {}
        try:
            _advp = (i18n.load_pref() or {}).get("adv", {}) or {}
        except Exception:
            _advp = {}

        # Row 1: bet -f
        a1 = tk.Frame(self._adv_body, bg=P.CARD)
        a1.pack(fill="x", pady=(10, 0))
        tk.Label(a1, text=t("proc.bet_f"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_bet_f = tk.DoubleVar(value=float(_advp.get("bet_f", 0.5)))
        self.spn_betf = ttk.Spinbox(a1, from_=0.10, to=1.00, increment=0.05,
                                    width=6, textvariable=self.var_bet_f)
        self.spn_betf.pack(side="left", padx=(0, 3))
        HelpDot(a1, t("tip.bet_f"), title=t("proc.bet_f")).pack(
            side="left", padx=(0, 18))
        Tooltip(self.spn_betf, t("tip.bet_f"))

        # Row 2: registration cost function
        a2 = tk.Frame(self._adv_body, bg=P.CARD)
        a2.pack(fill="x", pady=(10, 0))
        tk.Label(a2, text=t("proc.reg_cost"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_reg_cost = tk.StringVar(
            value=str(_advp.get("reg_cost", "normmi") or "normmi"))
        self.cmb_cost = ttk.Combobox(
            a2, textvariable=self.var_reg_cost, width=14, state="readonly",
            values=("normmi", "corratio", "mutualinfo", "ratiosquare"))
        self.cmb_cost.pack(side="left", padx=(0, 3))
        HelpDot(a2, t("tip.reg_cost"), title=t("proc.reg_cost")).pack(
            side="left", padx=(0, 18))
        Tooltip(self.cmb_cost, t("tip.reg_cost"))

        # Row 3: template
        a3 = tk.Frame(self._adv_body, bg=P.CARD)
        a3.pack(fill="x", pady=(10, 0))
        tk.Label(a3, text=t("proc.template"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_template = tk.StringVar(
            value=str(_advp.get("template", "") or ""))
        self.ent_tpl = ttk.Entry(a3, textvariable=self.var_template)
        self.ent_tpl.pack(side="left", fill="x", expand=True, padx=(0, 7))
        Tooltip(self.ent_tpl, t("tip.template"))
        self.btn_tpl = RoundButton(a3, t("proc.browse"),
                                   command=self._browse_template,
                                   variant="light", height=28, padx=12)
        self.btn_tpl.pack(side="left")
        HelpDot(a3, t("tip.template"), title=t("proc.template")).pack(
            side="left", padx=(6, 0))

        # Row 4: denoising
        a4 = tk.Frame(self._adv_body, bg=P.CARD)
        a4.pack(fill="x", pady=(10, 0))
        self.var_denoise = tk.BooleanVar(
            value=bool(_advp.get("denoise", False)))
        cb_dn = ttk.Checkbutton(a4, text=t("proc.denoise"),
                                variable=self.var_denoise)
        cb_dn.pack(side="left")
        HelpDot(a4, t("tip.denoise"), title=t("proc.denoise")).pack(
            side="left", padx=(6, 0))
        Tooltip(cb_dn, t("tip.denoise"))

        # Row 5: TOPUP (dual phase encoding, optional)
        t5 = tk.Frame(self._adv_body, bg=P.CARD)
        t5.pack(fill="x", pady=(12, 0))
        _tp = _advp.get("topup", {}) if isinstance(_advp.get("topup"), dict) else {}
        self.var_topup = tk.BooleanVar(value=bool(_tp.get("enabled", False)))
        cb_tp = ttk.Checkbutton(t5, text=t("proc.topup"),
                                variable=self.var_topup)
        cb_tp.pack(side="left")
        HelpDot(t5, HELP["topup"], title=t("proc.topup")).pack(
            side="left", padx=(6, 0))
        Tooltip(cb_tp, t("tip.topup"))

        # Row 6: second-DWI source (auto-detect vs manual file)
        t6 = tk.Frame(self._adv_body, bg=P.CARD)
        t6.pack(fill="x", pady=(8, 0))
        tk.Label(t6, text=t("proc.topup_mode"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_topup_mode = tk.StringVar(
            value=str(_tp.get("mode", "auto") or "auto"))
        self.rb_topup_auto = ttk.Radiobutton(
            t6, text=t("proc.topup_auto_mode"), value="auto",
            variable=self.var_topup_mode)
        self.rb_topup_auto.pack(side="left", padx=(0, 12))
        self.rb_topup_manual = ttk.Radiobutton(
            t6, text=t("proc.topup_manual_mode"), value="manual",
            variable=self.var_topup_mode)
        self.rb_topup_manual.pack(side="left")
        HelpDot(t6, HELP["topup"], title=t("proc.topup")).pack(
            side="left", padx=(6, 0))

        # Row 7: manual second-DWI file (single-subject mode only)
        t7 = tk.Frame(self._adv_body, bg=P.CARD)
        t7.pack(fill="x", pady=(8, 0))
        tk.Label(t7, text=t("proc.topup_second"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_topup_second = tk.StringVar(value="")
        self.ent_topup_second = ttk.Entry(t7,
                                          textvariable=self.var_topup_second)
        self.ent_topup_second.pack(side="left", fill="x", expand=True,
                                   padx=(0, 7))
        self.btn_topup_second = RoundButton(
            t7, t("proc.browse"), command=self._browse_topup_second,
            variant="light", height=28, padx=12)
        self.btn_topup_second.pack(side="left")

        # Row 8: TOPUP configuration file (blank = auto-detect b02b0.cnf)
        t8 = tk.Frame(self._adv_body, bg=P.CARD)
        t8.pack(fill="x", pady=(8, 0))
        tk.Label(t8, text=t("proc.topup_config"), bg=P.CARD, fg=P.TEXT,
                 width=18, anchor="w").pack(side="left")
        self.var_topup_config = tk.StringVar(
            value=str(_tp.get("config", "") or ""))
        self.ent_topup_cfg = ttk.Entry(t8,
                                       textvariable=self.var_topup_config)
        self.ent_topup_cfg.pack(side="left", fill="x", expand=True,
                                padx=(0, 7))
        Tooltip(self.ent_topup_cfg, t("tip.topup_config"))
        self.btn_topup_cfg = RoundButton(
            t8, t("proc.browse"), command=self._browse_topup_config,
            variant="light", height=28, padx=12)
        self.btn_topup_cfg.pack(side="left")
        HelpDot(t8, HELP["topup"], title=t("proc.topup")).pack(
            side="left", padx=(6, 0))

        # Row 9: live TOPUP status
        t9 = tk.Frame(self._adv_body, bg=P.CARD)
        t9.pack(fill="x", pady=(6, 0))
        self.lbl_topup = tk.Label(t9, text="", bg=P.CARD, fg=P.TEXT_FAINT,
                                  font=self.F["small"], anchor="w",
                                  justify="left")
        self.lbl_topup.pack(fill="x")

        # Row 10: restore recommended values + currently effective settings
        a5 = tk.Frame(self._adv_body, bg=P.CARD)
        a5.pack(fill="x", pady=(12, 0))
        self.btn_adv_reset = RoundButton(
            a5, t("proc.adv_reset"), command=self._reset_advanced,
            variant="light", height=28, padx=12)
        self.btn_adv_reset.pack(side="left")
        self.lbl_adv_cur = tk.Label(
            a5, text="", bg=P.CARD, fg=P.TEXT_FAINT,
            font=self.F["small"], anchor="w", justify="left")
        self.lbl_adv_cur.pack(side="left", padx=(12, 0))
        for _v in (self.var_bet_f, self.var_reg_cost, self.var_template,
                   self.var_denoise, self.var_topup, self.var_topup_mode,
                   self.var_topup_second, self.var_topup_config):
            try:
                _v.trace_add("write", self._update_adv_summary)
            except Exception:
                pass
        for _v in (self.var_topup, self.var_topup_mode):
            try:
                _v.trace_add("write", self._update_topup_ui)
            except Exception:
                pass
        self._update_topup_ui()
        self._update_adv_summary()

        tk.Label(self._adv_body, text=t("proc.advanced_hint"), bg=P.CARD,
                 fg=P.TEXT_FAINT, font=self.F["small"], anchor="w",
                 justify="left", wraplength=960).pack(fill="x", pady=(10, 2))

        # --- actions ---
        act = tk.Frame(page, bg=P.BG)
        act.pack(fill="x", pady=(2, 12))
        self.btn_go = RoundButton(act, t("proc.start"), command=self._start,
                                  variant="accent", height=38, padx=26,
                                  font=(self.F["base"][0], 10, "bold"))
        self.btn_go.pack(side="left")
        HelpDot(act, HELP["go"], bg=P.BG, title=t("proc.start")).pack(side="left", padx=(8, 20))

        self.btn_stop = RoundButton(act, t("proc.stop"), command=self._stop,
                                    variant="danger", height=38, padx=20)
        self.btn_stop.pack(side="left")
        self.btn_stop.set_enabled(False)

        pb = RoundButton(act, t("proc.preflight"), command=self._preflight_only,
                         variant="light", height=38, padx=20)
        pb.pack(side="left", padx=10)
        HelpDot(act, HELP["preflight"], bg=P.BG, title=t("proc.preflight")).pack(
            side="left", padx=(4, 0))

        # Processing pipeline overview: each step together with its methodological citation
        tk.Frame(act, bg=P.BG, width=14).pack(side="left")
        tk.Label(act, text=t("proc.pipeline"), bg=P.BG, fg=P.TEXT_MUTED,
                 font=self.F["small"]).pack(side="left")
        hd = HelpDot(act, HELP["pipeline"], bg=P.BG, title=t("proc.pipeline"))
        hd.pack(side="left", padx=(4, 0))
        Tooltip(hd, HELP["pipeline"])

        RoundButton(act, t("proc.clearlog"), command=self._clear_log, variant="ghost",
                    height=38, padx=16).pack(side="right")

        # --- summary ---
        box3 = self._card(page, t("proc.summary"), pady=(0, 6))
        self.lbl_summary = tk.Label(box3, bg=P.CARD, fg=P.TEXT, font=self.F["base"],
                                    anchor="nw", justify="left", wraplength=980,
                                    text=t("proc.summary_empty"))
        self.lbl_summary.pack(fill="x")

        self.var_in.trace_add("write", lambda *a: self._update_summary())
        self.var_out.trace_add("write", lambda *a: self._update_summary())
        self._update_summary()
        return shell

    def _update_summary(self):
        if not hasattr(self, "lbl_summary"):
            return
        indir = self.var_in.get().strip()
        outdir = self.var_out.get().strip()
        if not indir:
            self.lbl_summary.configure(
                fg=P.TEXT,
                text=t("proc.summary_empty"))
            return
        if not os.path.isdir(indir):
            self.lbl_summary.configure(
                fg=P.ERR,
                text=t("proc.dir_missing") + t("sep.colon") + indir)
            return
        try:
            if self.mode.get() == "batch":
                subs = [d for d in sorted(os.listdir(indir))
                        if os.path.isdir(os.path.join(indir, d))]
                n = len(subs)
                est = t("proc.est", n * 10, n * 15) if n else ""
                self.lbl_summary.configure(
                    fg=P.TEXT,
                    text="%s%s%s\n%s%s%s\n%s\n%s%s%s\n%s" % (
                        t("proc.mode"), t("sep.colon"),
                        t("msg.mode_batch"),
                        t("proc.rootdir"), t("sep.colon"), indir,
                        t("proc.found", n, n, est),
                        t("proc.out_to"), t("sep.colon"),
                        outdir or t("proc.not_set"),
                        t("proc.next_hint")))
            else:
                name = os.path.basename(os.path.normpath(indir))
                self.lbl_summary.configure(
                    fg=P.TEXT,
                    text="%s%s%s\n%s%s%s\n%s%s%s\n%s%s%s\n%s\n%s" % (
                        t("proc.mode"), t("sep.colon"),
                        t("proc.single"),
                        t("proc.indir"), t("sep.colon"), indir,
                        t("proc.subject_id"), t("sep.colon"), name,
                        t("proc.out_to"), t("sep.colon"),
                        os.path.join(outdir, name) if outdir
                        else t("proc.not_set"),
                        t("proc.est_time"),
                        t("proc.next_hint_single")))
        except Exception as e:
            self.lbl_summary.configure(
                fg=P.ERR, text=t("proc.read_fail") + t("sep.colon") + str(e))

    # =================================================================
    # page: ROI atlas
    # =================================================================
    def _page_roi(self):
        shell = tk.Frame(self.content, bg=P.BG)
        wrap = tk.Frame(shell, bg=P.BG)
        wrap.pack(fill="both", expand=True)

        left = tk.Frame(wrap, bg=P.BG)
        left.pack(side="left", fill="both", expand=True)
        card = RoundedCard(left, padding=(14, 12))
        card.pack(fill="both", expand=True)
        self.roi_viewer = RoiViewer(card.body, fsl_dir=self._fsl_dir(),
                                    bg=P.CARD, width=460, height=460)
        self.roi_viewer.pack(fill="both", expand=True)

        right = tk.Frame(wrap, bg=P.BG, width=430)
        right.pack(side="left", fill="y", padx=(14, 0))
        right.pack_propagate(False)

        info = self._card(right, t("roip.title"))
        head = tk.Frame(info, bg=P.CARD)
        head.pack(fill="x")
        tk.Label(head, text=t("roip.why"), bg=P.CARD, fg=P.ACCENT,
                 font=self.F["bold"], anchor="w").pack(side="left")
        HelpDot(head, HELP["roi_viewer"],
                title=t("tip.roi_viewer")).pack(
            side="left", padx=(4, 0))
        tk.Label(info, bg=P.CARD, fg=P.TEXT, font=self.F["base"], anchor="w",
                 justify="left", wraplength=370,
                 text=t("roip.why_body")
                 ).pack(fill="x", pady=(8, 0))

        tk.Label(info, bg=P.CARD, fg=P.ACCENT, font=self.F["bold"], anchor="w",
                 text=t("roip.idx")).pack(fill="x", pady=(12, 2))
        tk.Label(info, bg=P.CARD, fg=P.TEXT, font=self.F["base"], anchor="w",
                 justify="left", wraplength=370,
                 text=t("roip.idx_body")
                 ).pack(fill="x", pady=(0, 0))

        tb = self._card(right, t("roip.masks"))
        from .roi_preview import ROI_TITLE
        rows = [
            ("L_proj", ROI_TITLE["L_proj"], t("roip.fiber_proj"), "81"),
            ("R_proj", ROI_TITLE["R_proj"], t("roip.fiber_proj"), "81"),
            ("L_asso", ROI_TITLE["L_asso"], t("roip.fiber_asso"), "81"),
            ("R_asso", ROI_TITLE["R_asso"], t("roip.fiber_asso"), "81"),
        ]
        hdr = tk.Frame(tb, bg=P.CARD)
        hdr.pack(fill="x")
        for txt, wid in ((t("roip.col_name"), 14), (t("roip.col_anat"), 12), (t("roip.col_type"), 9), (t("roip.col_vox"), 6)):
            tk.Label(hdr, text=txt, bg=P.CARD, fg=P.TEXT_MUTED,
                     font=self.F["small"], width=wid, anchor="w").pack(side="left")
        for name, anat, fib, nv in rows:
            rr = tk.Frame(tb, bg=P.CARD)
            rr.pack(fill="x", pady=1)
            tk.Label(rr, text=name, bg=P.CARD, fg=P.TEXT,
                     font=self.F["mono"], width=14, anchor="w").pack(side="left")
            tk.Label(rr, text=anat, bg=P.CARD, fg=P.TEXT,
                     font=self.F["small"], width=12, anchor="w").pack(side="left")
            tk.Label(rr, text=fib, bg=P.CARD, fg=P.TEXT_MUTED,
                     font=self.F["small"], width=9, anchor="w").pack(side="left")
            tk.Label(rr, text=nv, bg=P.CARD, fg=P.TEXT,
                     font=self.F["small"], width=6, anchor="w").pack(side="left")

        tk.Label(tb, bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"],
                 anchor="w", justify="left", wraplength=370,
                 text=t("roip.note")
                 ).pack(fill="x", pady=(10, 0))
        return shell

    def _fsl_dir(self):
        if self.env and getattr(self.env, "fsl_dir", None):
            return self.env.fsl_dir
        return os.environ.get("FSLDIR")

    # =================================================================
    # page: results
    # =================================================================
    def _page_results(self):
        page = tk.Frame(self.content, bg=P.BG)

        bar = tk.Frame(page, bg=P.BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text=t("res.title"), bg=P.BG, fg=P.TEXT,
                 font=self.F["h2"]).pack(side="left")
        HelpDot(bar, HELP["results"], bg=P.BG, title=t("res.title")).pack(
            side="left", padx=(5, 0))
        self.lbl_count = tk.Label(bar, text="", bg=P.BG, fg=P.TEXT_MUTED,
                                  font=self.F["small"])
        self.lbl_count.pack(side="left", padx=(12, 0))

        RoundButton(bar, t("res.export_csv"), command=lambda: self._export("csv"),
                    variant="light", height=32, padx=16).pack(side="right", padx=(7, 0))
        RoundButton(bar, t("res.export_json"), command=lambda: self._export("json"),
                    variant="light", height=32, padx=16).pack(side="right", padx=(7, 0))
        # One-click HTML report
        RoundButton(bar, t("res.report"), command=self._make_report,
                    variant="primary", height=32, padx=16).pack(
                        side="right", padx=(7, 0))
        RoundButton(bar, t("res.import"), command=self._import_results,
                    variant="light", height=32, padx=16).pack(side="right", padx=(7, 0))
        RoundButton(bar, t("res.clear"), command=self._clear_results,
                    variant="danger", height=32, padx=16).pack(side="right")

        card = RoundedCard(page, padding=(2, 2))
        card.pack(fill="both", expand=True)
        host = card.body

        cols = sess.RESULT_COLUMNS
        heads = {
            "subject": t("col.subject"), "status": t("col.status"),
            "qc": t("col.qc"),
            "alps_L": "ALPS_L", "alps_R": "ALPS_R", "alps_mean": "ALPS_mean",
            "n_L_proj": "L_proj", "n_R_proj": "R_proj",
            "n_L_asso": "L_asso", "n_R_asso": "R_asso", "r_wm": "r_wm",
            "rms_rel_mean": t("col.jitter_mean"),
            "rms_rel_max": t("col.jitter_max"),
            "rms_abs_mean": t("col.drift_mean"),
            "rms_abs_max": t("col.drift_max"),
            "n_outlier": t("col.outlier_short"), "n_vol": t("col.n_vol"),
            "method": t("col.method"), "topup": t("col.topup"),
            "seconds": t("col.seconds"), "finished_at": t("col.finished"),
        }
        widths = {
            "subject": 124, "status": 190, "qc": 72, "alps_L": 78,
            "alps_R": 78, "alps_mean": 100, "n_L_proj": 58, "n_R_proj": 58,
            "n_L_asso": 58, "n_R_asso": 58, "r_wm": 58,
            "rms_rel_mean": 76, "rms_rel_max": 76,
            "rms_abs_mean": 76, "rms_abs_max": 76,
            "n_outlier": 50, "n_vol": 58, "method": 100, "topup": 150,
            "seconds": 68, "finished_at": 116,
        }
        self.tree = ttk.Treeview(host, columns=cols, show="headings", height=16)
        for c in cols:
            self.tree.heading(c, text=heads.get(c, c))
            # stretch=False keeps each column at its configured width and lets
            # the horizontal scrollbar handle the overflow; otherwise a narrow
            # window squeezes the leading columns down to a few pixels.
            self.tree.column(c, width=widths.get(c, 80), minwidth=widths.get(c, 80),
                             anchor="center", stretch=(c == "finished_at"))
        self.tree.column("subject", anchor="w")
        self.tree.column("status", anchor="w")
        ysb = ttk.Scrollbar(host, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(host, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("fail", foreground=P.ERR)
        self.tree.tag_configure("warn", foreground=P.WARN)
        self.tree.tag_configure("ok", foreground=P.OK)
        self.tree.tag_configure("odd", background=P.ROW_ALT)
        return page

    # =================================================================
    # page: QC
    # =================================================================
    def _page_qc(self):
        page = tk.Frame(self.content, bg=P.BG)

        # ---- overview ----
        top = self._card(page, t("qc.overview"), pady=(0, 2))
        row = tk.Frame(top, bg=P.CARD)
        row.pack(fill="x")

        self._qc_stat = {}
        specs = [("total", t("qc.total"), P.TEXT, "#eef0f3"),
                 ("ok", t("qc.pass"), P.OK, P.OK_LIGHT),
                 ("info", t("qc.info"), P.ACCENT, P.ACCENT_LIGHT),
                 ("warn", t("qc.warn"), P.WARN, P.WARN_LIGHT),
                 ("fail", t("qc.fail"), P.ERR, P.ERR_LIGHT)]
        for key, label, fg, bg in specs:
            cell = tk.Frame(row, bg=bg, highlightbackground=P.BORDER,
                            highlightthickness=1)
            cell.pack(side="left", padx=(0, 10))
            num = tk.Label(cell, text="0", bg=bg, fg=fg,
                           font=(self.F["h1"][0], 20, "bold"), width=4)
            num.pack(side="left", padx=(12, 0), pady=6)
            cap = tk.Label(cell, text=label, bg=bg, fg=P.TEXT_MUTED,
                           font=self.F["small"])
            cap.pack(side="left", padx=(2, 14))
            self._qc_stat[key] = num

        self.lbl_qc_top = tk.Label(top, bg=P.CARD, fg=P.TEXT, font=self.F["base"],
                                   anchor="w", justify="left", wraplength=980,
                                   text=t("qc.no_data"))
        self.lbl_qc_top.pack(fill="x", pady=(10, 0))

        # ---- toolbar ----
        bar = tk.Frame(page, bg=P.BG)
        bar.pack(fill="x", pady=(8, 8))
        tk.Label(bar, text=t("qc.detail"), bg=P.BG, fg=P.TEXT,
                 font=self.F["h2"]).pack(side="left")
        HelpDot(bar, HELP["qc"], bg=P.BG, title=t("tip.qc")).pack(
            side="left", padx=(5, 14))

        self._qc_btns = {}
        for key, label in (("all", t("qc.filter_all")), ("warn", t("qc.warn")),
                           ("fail", t("qc.fail")), ("ok", t("qc.pass"))):
            b = tk.Label(bar, text=label, bg=P.BG, fg=P.TEXT_MUTED,
                         font=self.F["small"], padx=10, pady=4, cursor="hand2")
            b.pack(side="left", padx=(0, 3))
            b.bind("<Button-1>", lambda e, k=key: self._set_qc_filter(k))
            b.bind("<Enter>", lambda e, w=b: w.configure(fg=P.ACCENT))
            b.bind("<Leave>", lambda e, w=b: w.configure(
                fg=P.ACCENT if self._qc_filter == w._fkey else P.TEXT_MUTED))
            b._fkey = key
            self._qc_btns[key] = b

        RoundButton(bar, t("qc.export"), command=self._export_qc,
                    variant="light", height=32, padx=16).pack(side="right")
        RoundButton(bar, t("qc.scatter"), command=self._show_scatter,
                    variant="light", height=32, padx=16).pack(side="right", padx=7)
        RoundButton(bar, t("qc.thresholds"), command=self._edit_thresholds,
                    variant="light", height=32, padx=16).pack(side="right")
        RoundButton(bar, t("qc.recheck"), command=self._refresh_qc,
                    variant="ghost", height=32, padx=16).pack(side="right", padx=7)

        # Current-threshold summary, so the pass/fail criteria stay visible
        self.lbl_th = tk.Label(page, bg=P.BG, fg=P.TEXT_MUTED,
                               font=self.F["small"], anchor="w")
        self.lbl_th.pack(fill="x", pady=(0, 6))
        self._update_threshold_label()

        # ---- detail table ----
        card = RoundedCard(page, padding=(2, 2))
        card.pack(fill="both", expand=True)
        host = card.body

        qcols = ("subject", "level", "r_wm", "roi", "rms_rel", "rms_abs",
                 "outlier", "method", "issues")
        qheads = (t("col.subject"), t("col.level"), t("col.r_wm"),
                  t("col.roi"), t("col.rel"), t("col.abs"),
                  t("col.outlier"), t("col.method"), t("col.issues"))
        qwidths = (128, 78, 88, 90, 96, 96, 82, 108, 400)

        self.qc_tree = ttk.Treeview(host, columns=qcols, show="headings", height=14)
        for c, h, w in zip(qcols, qheads, qwidths):
            self.qc_tree.heading(c, text=h)
            self.qc_tree.column(c, width=w, minwidth=w, anchor="center",
                                stretch=(c == "issues"))
        self.qc_tree.column("subject", anchor="w")
        self.qc_tree.column("issues", anchor="w")
        ysb = ttk.Scrollbar(host, orient="vertical", command=self.qc_tree.yview)
        xsb = ttk.Scrollbar(host, orient="horizontal", command=self.qc_tree.xview)
        self.qc_tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        self.qc_tree.pack(side="left", fill="both", expand=True)
        self.qc_tree.tag_configure("ok", foreground=P.OK)
        self.qc_tree.tag_configure("info", foreground=P.ACCENT)
        self.qc_tree.tag_configure("warn", foreground=P.WARN)
        self.qc_tree.tag_configure("fail", foreground=P.ERR)
        self.qc_tree.bind("<Double-1>", lambda e: self._show_qc_detail())
        self.qc_tree.bind("<Return>", lambda e: self._show_qc_detail())

        tk.Label(page, bg=P.BG, fg=P.TEXT_FAINT, font=self.F["small"],
                 anchor="w",
                 text=t("qc.dblclick_hint")
                 ).pack(fill="x", pady=(6, 0))
        return page

    def _update_threshold_label(self):
        if not hasattr(self, "lbl_th"):
            return
        th = qcmod.load_thresholds()
        self.lbl_th.configure(
            text=t("qc.thresholds_now") + qcmod.thresholds_summary(th))

    def _edit_thresholds(self):
        """Threshold settings dialog. Any change re-evaluates all results immediately."""
        th = qcmod.load_thresholds()
        win = tk.Toplevel(self)
        win.title(t("qc.th_title"))
        win.configure(bg=P.CARD)
        win.transient(self)
        win.geometry("660x620")
        win.minsize(600, 540)

        head = tk.Frame(win, bg=P.CARD)
        head.pack(fill="x", padx=20, pady=(16, 4))
        tk.Label(head, text=t("qc.thresholds"), bg=P.CARD, fg=P.ACCENT,
                 font=self.F["h2"]).pack(side="left")
        HelpDot(head, HELP["qc_thresholds"],
                title=t("tip.qc_thresholds")).pack(
            side="left", padx=(6, 0))

        tk.Label(win, bg=P.CARD, fg=P.TEXT_MUTED, font=self.F["small"],
                 anchor="w", justify="left", wraplength=600,
                 text=t("qc.th_hint")).pack(fill="x", padx=20, pady=(0, 8))

        # Scrollable so the dialog still fits on small screens
        sc = ScrollFrame(win, bg=P.CARD)
        sc.pack(fill="both", expand=True, padx=20)
        body = sc.inner

        v = {
            "r_wm_ok": tk.DoubleVar(value=th.r_wm_ok),
            "r_wm_fail": tk.DoubleVar(value=th.r_wm_fail),
            "rms_rel_warn": tk.DoubleVar(value=th.rms_rel_warn),
            "rms_rel_fail": tk.DoubleVar(value=th.rms_rel_fail),
            "rms_rel_max_warn": tk.DoubleVar(value=th.rms_rel_max_warn),
            "rms_rel_max_fail": tk.DoubleVar(value=th.rms_rel_max_fail),
            "rms_abs_warn": tk.DoubleVar(value=th.rms_abs_warn),
            "rms_abs_fail": tk.DoubleVar(value=th.rms_abs_fail),
            "rms_abs_max_warn": tk.DoubleVar(value=th.rms_abs_max_warn),
            "rms_abs_max_fail": tk.DoubleVar(value=th.rms_abs_max_fail),
            "outlier_warn": tk.DoubleVar(value=th.outlier_warn),
            "outlier_fail": tk.DoubleVar(value=th.outlier_fail),
            "alps_min": tk.DoubleVar(value=th.alps_min),
            "alps_max": tk.DoubleVar(value=th.alps_max),
            "roi_voxels": tk.IntVar(value=th.roi_voxels),
            "strict_roi_voxels": tk.BooleanVar(value=th.strict_roi_voxels),
            "flag_eddy_correct": tk.BooleanVar(value=th.flag_eddy_correct),
        }

        def section(title, hint=""):
            f = tk.Frame(body, bg=P.CARD)
            f.pack(fill="x", pady=(10, 2))
            tk.Frame(f, bg=P.BORDER, height=1).pack(fill="x", pady=(0, 6))
            tk.Label(f, text=title, bg=P.CARD, fg=P.TEXT,
                     font=self.F["bold"], anchor="w").pack(fill="x")
            if hint:
                tk.Label(f, text=hint, bg=P.CARD, fg=P.TEXT_FAINT,
                         font=self.F["small"], anchor="w", justify="left",
                         wraplength=560).pack(fill="x", pady=(2, 0))
            return body

        def row(parent, label, key, lo, hi, step, unit="", kind="float"):
            r = tk.Frame(parent, bg=P.CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=P.CARD, fg=P.TEXT, font=self.F["base"],
                     width=20, anchor="w").pack(side="left")
            kw = dict(from_=lo, to=hi, width=9, textvariable=v[key])
            if kind == "float":
                kw["increment"] = step
            tk.Spinbox(r, **kw).pack(side="left", padx=(0, 6))
            if unit:
                tk.Label(r, text=unit, bg=P.CARD, fg=P.TEXT_MUTED,
                         font=self.F["small"]).pack(side="left")

        p = section(t("qc.sec_reg"), t("qc.sec_reg_hint"))
        row(p, t("qc.row_rwm_ok"), "r_wm_ok", 0.50, 1.00, 0.01)
        row(p, t("qc.row_rwm_fail"), "r_wm_fail", 0.50, 1.00, 0.01)

        p = section(t("qc.sec_rel"), t("qc.sec_rel_hint"))
        row(p, t("qc.row_mean_warn"), "rms_rel_warn", 0.01, 3.0, 0.05, "mm")
        row(p, t("qc.row_mean_fail"), "rms_rel_fail", 0.01, 3.0, 0.05, "mm")
        row(p, t("qc.row_max_warn"), "rms_rel_max_warn", 0.01, 5.0, 0.10, "mm")
        row(p, t("qc.row_max_fail"), "rms_rel_max_fail", 0.01, 5.0, 0.10, "mm")

        p = section(t("qc.sec_abs"), t("qc.sec_abs_hint"))
        row(p, t("qc.row_mean_warn"), "rms_abs_warn", 0.01, 6.0, 0.05, "mm")
        row(p, t("qc.row_mean_fail"), "rms_abs_fail", 0.01, 6.0, 0.05, "mm")
        row(p, t("qc.row_max_warn"), "rms_abs_max_warn", 0.01, 8.0, 0.10, "mm")
        row(p, t("qc.row_max_fail"), "rms_abs_max_fail", 0.01, 8.0, 0.10, "mm")

        p = section(t("qc.sec_out"), t("qc.sec_out_hint"))
        row(p, t("qc.row_warn"), "outlier_warn", 0.0, 5.0, 0.10)
        row(p, t("qc.row_upper"), "outlier_fail", 0.0, 5.0, 0.10)

        p = section(t("qc.sec_alps"), t("qc.sec_alps_hint"))
        row(p, t("qc.row_lower"), "alps_min", 0.0, 5.0, 0.10)
        row(p, t("qc.row_upper"), "alps_max", 0.0, 5.0, 0.10)

        p = section(t("qc.sec_other"))
        row(p, t("qc.row_roi_voxels"), "roi_voxels", 1, 10000, 1,
            kind="int")
        rr = tk.Frame(p, bg=P.CARD)
        rr.pack(fill="x", pady=2)
        ttk.Checkbutton(rr, text=t("qc.chk_strict_roi"),
                        variable=v["strict_roi_voxels"]).pack(side="left")
        rr2 = tk.Frame(p, bg=P.CARD)
        rr2.pack(fill="x", pady=2)
        ttk.Checkbutton(rr2, text=t("qc.chk_flag_eddy"),
                        variable=v["flag_eddy_correct"]).pack(side="left")

        btns = tk.Frame(win, bg=P.CARD)
        btns.pack(fill="x", padx=20, pady=(8, 14))
        RoundButton(btns, t("qc.save_recheck"), variant="accent", height=36,
                    padx=20,
                    parent_bg=P.CARD,
                    command=lambda: self._apply_thresholds(win, v)).pack(side="left")
        RoundButton(btns, t("reset"), variant="light", height=36, padx=16,
                    parent_bg=P.CARD,
                    command=lambda: self._reset_thresholds(v)).pack(side="left", padx=8)
        RoundButton(btns, t("cancel"), variant="ghost", height=36, padx=16,
                    parent_bg=P.CARD, command=win.destroy).pack(side="right")
        win.bind("<Escape>", lambda e: win.destroy())

        # Keep references so external code (including tests) can read or prefill them
        self._th_vars = v
        self._th_win = win
        return win

    def _collect_thresholds(self, v):
        th = qcmod.QCThresholds()
        for k, var in v.items():
            try:
                setattr(th, k, var.get())
            except Exception:
                pass
        return th

    def _reset_thresholds(self, v):
        if not messagebox.askyesno(t("reset"), t("qc.confirm_reset")):
            return
        d = qcmod.QCThresholds()
        for k, var in v.items():
            try:
                var.set(getattr(d, k))
            except Exception:
                pass

    def _apply_thresholds(self, win, v):
        th = self._collect_thresholds(v)
        problems = th.validate()
        if problems:
            messagebox.showerror(t("qc.th_bad_title"),
                                 "\n".join(problems))
            return
        if not qcmod.save_thresholds(th):
            messagebox.showerror(t("msg.save_fail"),
                                 t("qc.save_fail_body", qcmod.CONFIG_FILE))
            return
        win.destroy()
        self._update_threshold_label()
        self._refresh_qc()
        self._refresh_table()
        messagebox.showinfo(t("log.saved"),
                            t("qc.saved_body", qcmod.CONFIG_FILE,
                              len(self.records)))

    def _set_qc_filter(self, key):
        self._qc_filter = key
        for k, b in self._qc_btns.items():
            b.configure(fg=P.ACCENT if k == key else P.TEXT_MUTED,
                        font=(self.F["small"][0], self.F["small"][1],
                              "bold" if k == key else "normal"))
        self._fill_qc_table()

    def _refresh_qc(self):
        """Re-evaluate the QC of every record."""
        self._qc_reports = sess.qc_reports(self.records)
        for r, rep in zip(self.records, self._qc_reports):
            r["qc"] = rep.level
        s = qcmod.summarize(self._qc_reports)
        for k, w in self._qc_stat.items():
            w.configure(text=str(s.get(k, 0)))
        if s["total"] == 0:
            self.lbl_qc_top.configure(
                text=t("qc.no_data"), fg=P.TEXT_MUTED)
        else:
            parts = [t("qc.summary", s["total"])]
            if s["warn"]:
                parts.append(t("qc.summary_warn", s["warn"]))
            if s["fail"]:
                parts.append(t("qc.summary_fail", s["fail"]))
            txt = t("sep.clause").join(parts) + t("sep.sentence")
            if s["top_issues"]:
                items = t("sep.item").join(
                    it + t("qc.count_paren", n)
                    for it, n in s["top_issues"][:3])
                txt += (t("qc.top_issue") + t("sep.colon") + items
                        + t("sep.sentence"))
            elif s["warn"] == 0 and s["fail"] == 0:
                txt += t("qc.all_pass")
            self.lbl_qc_top.configure(text=txt, fg=P.TEXT)
        self._fill_qc_table()

    def _fill_qc_table(self):
        for it in self.qc_tree.get_children():
            self.qc_tree.delete(it)
        for rec, rep in zip(self.records, self._qc_reports):
            if self._qc_filter != "all" and rep.level != self._qc_filter:
                continue
            roi = []
            for k in ("n_L_proj", "n_R_proj", "n_L_asso", "n_R_asso"):
                v = rec.get(k, "")
                roi.append("" if v in ("", None) else str(v))
            roi_txt = "/".join(roi) if any(roi) else "-"

            def pair(a, b):
                x = rec.get(a)
                y = rec.get(b)
                if x in ("", None) and y in ("", None):
                    return "-"
                fx = ("%.2f" % float(x)) if x not in ("", None) else "-"
                fy = ("%.2f" % float(y)) if y not in ("", None) else "-"
                return "%s / %s" % (fx, fy)

            # Backwards compatibility: older records only carry rms_mean / rms_max,
            # so show them as relative displacement
            rel = pair("rms_rel_mean", "rms_rel_max")
            if rel == "-":
                rel = pair("rms_mean", "rms_max")
            vals = (
                rep.subject,
                rep.label,
                ("%.3f" % float(rec["r_wm"])) if rec.get("r_wm") not in ("", None) else "-",
                roi_txt,
                rel,
                pair("rms_abs_mean", "rms_abs_max"),
                str(rec.get("n_outlier", "") or "-"),
                str(rec.get("method", "") or "-"),
                rep.summarize_line(),
            )
            self.qc_tree.insert("", "end", values=vals, tags=(rep.level,))

    def _show_qc_detail(self):
        sel = self.qc_tree.selection()
        if not sel:
            messagebox.showinfo(t("qc.select_title"), t("qc.select_body"))
            return
        subj = self.qc_tree.item(sel[0])["values"][0]
        rep = next((r for r in self._qc_reports if r.subject == subj), None)
        if rep is None:
            return
        rec = next((r for r in self.records if str(r.get("subject")) == subj), None)
        self._qc_detail_window(rep, rec)

    def _subject_out_dir(self, subject: str):
        """Locate a subject's output directory, used to read the raw eddy files."""
        roots = [self.var_out.get().strip(), self._last_out,
                 self._lookup_root, self._last_out]
        for cand in roots:
            if not cand:
                continue
            d = os.path.join(cand, subject)
            if os.path.isdir(d):
                return d
        return None

    def _qc_detail_window(self, rep, rec):
        """QC details: text report on the left, motion time course on the right.

        A draggable splitter separates the two; the figure re-renders at the
        panel's actual size and supports wheel zoom and drag panning.
        """
        win = tk.Toplevel(self)
        win.title("%s · %s" % (t("qcd.title"), rep.subject))
        win.configure(bg=P.CARD)
        win.transient(self)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h = min(1500, int(sw * 0.94)), min(900, int(sh * 0.90))
        win.geometry("%dx%d+%d+%d" % (w, h, (sw - w) // 2, (sh - h) // 3))
        win.minsize(860, 520)

        head = tk.Frame(win, bg=P.CARD)
        head.pack(fill="x", padx=18, pady=(14, 6))
        tk.Label(head, text=rep.subject, bg=P.CARD, fg=P.TEXT,
                 font=self.F["h2"]).pack(side="left")
        badge_bg, badge_fg = {
            "ok": (P.OK_LIGHT, P.OK), "info": (P.ACCENT_LIGHT, P.ACCENT),
            "warn": (P.WARN_LIGHT, P.WARN), "fail": (P.ERR_LIGHT, P.ERR),
        }.get(rep.level, ("#eef0f3", P.TEXT_MUTED))
        tk.Label(head, text=" %s " % rep.label, bg=badge_bg, fg=badge_fg,
                 font=self.F["bold"], padx=6, pady=3).pack(side="left", padx=(10, 0))
        tk.Label(head, bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"],
                 text=t("qcd.sash_hint")).pack(side="right")

        # ---- draggable splitter ----
        paned = tk.PanedWindow(win, orient="horizontal", bg=P.BORDER,
                               sashwidth=8, sashrelief="flat", bd=0,
                               handlepad=0, opaqueresize=True)
        paned.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        # Left: text
        left = tk.Frame(paned, bg=P.CARD)
        txt = tk.Text(left, wrap="word", bg="#fbfcfd", fg=P.TEXT, relief="flat",
                      padx=12, pady=10, font=self.F["base"],
                      highlightbackground=P.BORDER, highlightthickness=1)
        sb = ttk.Scrollbar(left, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True)
        txt.insert("1.0", qcmod.report_text(rep))
        txt.configure(state="disabled")

        # Right: figure
        right = tk.Frame(paned, bg=P.CARD)
        paned.add(left, minsize=220, stretch="never")
        paned.add(right, minsize=420, stretch="always")

        outdir = self._subject_out_dir(rep.subject)
        panel = None
        self._qc_panels = getattr(self, "_qc_panels", [])
        if outdir is None:
            tk.Label(right, bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"],
                     justify="left", wraplength=420, anchor="nw",
                     text=t("qcd.no_dir")).pack(fill="both", expand=True,
                                              padx=8, pady=8)
        else:
            def _render(w_px, h_px, _od=outdir, _sid=rep.subject):
                from .plotting import motion_timecourse
                # Fixed width in inches with dpi matched to the pixel width, so
                # the figure fills the panel while font proportions stay the same
                # and text never collapses when the panel resizes
                base_w = 9.2
                dpi = max(60, min(320, w_px / base_w))
                base_h = max(2.4, base_w * h_px / max(1, w_px))
                return motion_timecourse(_od, _sid,
                                         figsize=(base_w, base_h), dpi=dpi)

            panel = FigurePanel(right, _render, bg=P.CARD,
                                aspect=None, min_zoom=1.0, max_zoom=3.0)
            panel.pack(fill="both", expand=True)
            self._qc_panels.append(panel)
            tk.Label(right, bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"],
                     anchor="w", justify="left",
                     text=t("qcd.caption")).pack(fill="x", pady=(4, 0),
                                                padx=6)

        btns = tk.Frame(win, bg=P.CARD)
        btns.pack(fill="x", padx=18, pady=(0, 14))
        if panel is not None:
            RoundButton(btns, t("qcd.save_png"), variant="light", height=32,
                        padx=16,
                        parent_bg=P.CARD,
                        command=lambda: self._save_panel(panel, rep.subject)
                        ).pack(side="left")
        RoundButton(btns, t("qcd.copy_text"), variant="light", height=32,
                    padx=16,
                    parent_bg=P.CARD,
                    command=lambda: self._copy_text(qcmod.report_text(rep))
                    ).pack(side="left", padx=8)
        RoundButton(btns, t("close"), variant="accent", height=32, padx=16,
                    parent_bg=P.CARD, command=win.destroy).pack(side="right")
        win.bind("<Escape>", lambda e: win.destroy())

        # Initial split position: text 34%, figure 66%
        def place_sash():
            try:
                win.update_idletasks()
                paned.sash_place(0, int(w * 0.34), 0)
            except Exception:
                pass
            if panel is not None:
                panel.reload()
        win.after(60, place_sash)

    def _save_panel(self, panel, subject):
        img = panel.current_image()
        if img is None:
            messagebox.showinfo(t("msg.no_image"), t("fig.no_image"))
            return
        p = filedialog.asksaveasfilename(
            title=t("fig.save_qc_title"), defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile="qc_%s.png" % subject)
        if not p:
            return
        try:
            img.save(p, dpi=(110, 110))
            messagebox.showinfo(t("log.saved"), p)
        except Exception as e:
            messagebox.showerror(t("msg.save_fail"), str(e))

    def _copy_text(self, s):
        try:
            self.clipboard_clear()
            self.clipboard_append(s)
            messagebox.showinfo(t("msg.copied"), t("msg.copied_body"))
        except Exception as e:
            messagebox.showerror(t("msg.copy_fail"), str(e))

    def _show_scatter(self):
        """Cross-subject scatter plot with selectable X / Y variables."""
        if not self.records:
            messagebox.showinfo(t("msg.no_data"), t("msg.table_empty"))
            return
        try:
            from .plotting import GROUP_MODES, SCATTER_VARS
        except Exception as e:
            messagebox.showerror(t("msg.plot_unavailable"),
                                 t("msg.need_mpl", e))
            return

        win = tk.Toplevel(self)
        win.title(t("qc.scatter"))
        win.configure(bg=P.CARD)
        win.transient(self)
        win.geometry("900x720")
        win.minsize(740, 580)

        bar = tk.Frame(win, bg=P.CARD)
        bar.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(bar, text="X", bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"]).pack(side="left")
        keys = list(SCATTER_VARS.keys())
        vx = tk.StringVar(value="rms_rel_mean")
        vy = tk.StringVar(value="alps_mean")
        ttk.Combobox(bar, values=keys, textvariable=vx, width=17,
                     state="readonly").pack(side="left", padx=(4, 12))
        tk.Label(bar, text="Y", bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"]).pack(side="left")
        ttk.Combobox(bar, values=keys, textvariable=vy, width=17,
                     state="readonly").pack(side="left", padx=(4, 12))

        tk.Label(bar, text=t("sc.group"), bg=P.CARD, fg=P.TEXT_MUTED,
                 font=self.F["small"]).pack(side="left")
        vg = tk.StringVar(value="auto")
        gmodes = list(GROUP_MODES.items())
        cb = ttk.Combobox(bar, width=14, state="readonly",
                          values=[v for _, v in gmodes])
        cb.current(0)
        cb.pack(side="left", padx=(4, 0))
        # The dropdown shows the translated description; the key is read back
        def on_group(_e=None):
            idx = cb.current()
            vg.set(gmodes[idx][0] if 0 <= idx < len(gmodes) else "auto")
            redraw()
        cb.bind("<<ComboboxSelected>>", on_group)

        tk.Label(win, bg=P.CARD, fg=P.TEXT_FAINT, font=self.F["small"],
                 anchor="w", justify="left", wraplength=850,
                 text=t("sc.hint")).pack(fill="x", padx=16, pady=(0, 6))
        HelpDot(win, HELP["scatter"], bg=P.CARD,
                title=t("tip.scatter")).place(
            relx=1.0, x=-22, y=56)

        holder = tk.Frame(win, bg=P.CARD)
        holder.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        def _render(w_px, h_px):
            from .plotting import qc_scatter
            base_w = 7.4
            dpi = max(60, min(320, w_px / base_w))
            base_h = max(2.6, base_w * h_px / max(1, w_px))
            return qc_scatter(self.records, vx.get(), vy.get(),
                              group_mode=vg.get(),
                              figsize=(base_w, base_h), dpi=dpi)

        panel = FigurePanel(holder, _render, bg=P.CARD,
                            aspect=None, min_zoom=1.0, max_zoom=3.0)
        panel.pack(fill="both", expand=True)

        def redraw(*_):
            # Redraw when a variable or grouping changes; FigurePanel handles
            # panel-size changes itself
            panel._off = [0, 0]
            panel.reload()

        vx.trace_add("write", redraw)
        vy.trace_add("write", redraw)

        btns = tk.Frame(win, bg=P.CARD)
        btns.pack(fill="x", padx=16, pady=(0, 14))
        RoundButton(btns, t("fig.save_title"), variant="light", height=32,
                    padx=16,
                    parent_bg=P.CARD,
                    command=lambda: self._save_panel(panel, "scatter")
                    ).pack(side="left")
        RoundButton(btns, t("close"), variant="accent", height=32, padx=16,
                    parent_bg=P.CARD, command=win.destroy).pack(side="right")
        win.bind("<Escape>", lambda e: win.destroy())

        win.after(260, panel.reload)

    def _export_qc(self):
        if not self._qc_reports:
            messagebox.showinfo(t("msg.no_data"), t("qc.export_empty"))
            return
        p = filedialog.asksaveasfilename(
            title=t("qc.export"), defaultextension=".txt",
            filetypes=[(t("ft.text"), "*.txt")],
            initialfile="qc_report.txt")
        if not p:
            return
        try:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(qcmod.batch_report_text(self._qc_reports))
                fh.write("\n\n")
                fh.write("=" * 52 + "\n" + t("qc.per_subject") + "\n"
                         + "=" * 52 + "\n\n")
                for rep in self._qc_reports:
                    fh.write(qcmod.report_text(rep))
                    fh.write("\n\n")
            messagebox.showinfo(t("msg.exported"), p)
        except Exception as e:
            messagebox.showerror(t("msg.export_fail"), str(e))

    # =================================================================
    # page: log
    # =================================================================
    def _page_log(self):
        page = tk.Frame(self.content, bg=P.BG)
        bar = tk.Frame(page, bg=P.BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text=t("log.title"), bg=P.BG, fg=P.TEXT,
                 font=self.F["h2"]).pack(side="left")
        RoundButton(bar, t("clear"), command=self._clear_log, variant="ghost",
                    height=30, padx=14).pack(side="right")
        RoundButton(bar, t("log.save_as"), command=self._save_log, variant="light",
                    height=30, padx=14).pack(side="right", padx=7)

        card = RoundedCard(page, padding=(2, 2))
        card.pack(fill="both", expand=True)
        host = card.body
        self.txt = tk.Text(host, wrap="word", font=self.F["mono"], bg="#ffffff",
                           fg=P.TEXT, relief="flat", padx=12, pady=10,
                           insertbackground=P.TEXT, selectbackground=P.ACCENT_LIGHT,
                           spacing1=1, spacing3=2)
        sb = ttk.Scrollbar(host, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt.pack(side="left", fill="both", expand=True)
        self.txt.tag_configure("err", foreground=P.ERR)
        self.txt.tag_configure("warn", foreground=P.WARN)
        self.txt.tag_configure("ok", foreground=P.OK)
        self.txt.tag_configure("muted", foreground=P.TEXT_FAINT)
        self.txt.tag_configure("cmd", foreground="#7b8794")
        self.txt.tag_configure("hdr", foreground=P.ACCENT, font=self.F["bold"])
        self.txt.configure(state="disabled")
        return page

    # =================================================================
    # page: help
    # =================================================================
    def _page_help(self):
        page = tk.Frame(self.content, bg=P.BG)
        card = RoundedCard(page, padding=(10, 10))
        card.pack(fill="both", expand=True)
        host = card.body

        nb = ttk.Notebook(host)
        nb.pack(fill="both", expand=True)

        def tab(title, content):
            f = tk.Frame(nb, bg=P.CARD)
            nb.add(f, text="  %s  " % title)
            t = tk.Text(f, wrap="word", font=self.F["base"], bg="#ffffff",
                        fg=P.TEXT, relief="flat", padx=20, pady=16,
                        spacing1=1, spacing3=3, cursor="arrow")
            sb = ttk.Scrollbar(f, orient="vertical", command=t.yview)
            t.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            t.pack(side="left", fill="both", expand=True)
            t.tag_configure("h", foreground=P.ACCENT, font=self.F["h2"],
                            spacing1=16, spacing3=6)
            t.tag_configure("cmd", font=self.F["mono"], foreground="#0a3069",
                            background="#f6f8fa", lmargin1=22, lmargin2=22)
            for line in content.split("\n"):
                s = line.rstrip()
                if s and not s.startswith(" ") and len(s) < 26 and \
                        not s.endswith("。") and not s.endswith("：") and \
                        not s.startswith("-") and not s.startswith("1") and \
                        not s.startswith("2") and not s.startswith("3") and \
                        not s.startswith("4") and not s.startswith("5"):
                    # A short standalone line without a trailing full stop is treated as a heading
                    t.insert("end", s + "\n", "h")
                elif s.startswith("    "):
                    t.insert("end", s + "\n", "cmd")
                else:
                    t.insert("end", s + "\n")
            t.configure(state="disabled")
            return f

        for key in helptext.PAGES_ORDER:
            title, content = helptext.page(key)
            tab(title, content)
        return page

    # =================================================================
    # status bar
    # =================================================================
    def _build_statusbar(self):
        outer = tk.Frame(self, bg=P.CARD, height=96)
        outer.pack(fill="x", side="bottom")
        outer.pack_propagate(False)
        tk.Frame(outer, bg=P.BORDER, height=1).pack(fill="x", side="top")

        top = tk.Frame(outer, bg=P.CARD)
        top.pack(fill="x", padx=20, pady=(11, 3))
        self.lbl_total = tk.Label(top, text=t("ready"), bg=P.CARD, fg=P.TEXT,
                                  font=self.F["base"], anchor="w")
        self.lbl_total.pack(side="left")
        self.lbl_elapsed = tk.Label(top, text="", bg=P.CARD, fg=P.TEXT_FAINT,
                                    font=self.F["small"], anchor="e")
        self.lbl_elapsed.pack(side="right")

        self.pb_total = ttk.Progressbar(outer, mode="determinate", maximum=100)
        self.pb_total.pack(fill="x", padx=20, pady=(4, 10))

        row3 = tk.Frame(outer, bg=P.CARD)
        row3.pack(fill="x", padx=20, pady=(0, 13))
        self.lbl_cur = tk.Label(row3, text=t("prog.current_none"), bg=P.CARD,
                                fg=P.TEXT_MUTED, font=self.F["small"],
                                anchor="w", width=36)
        self.lbl_cur.pack(side="left")
        self.pb_cur = ttk.Progressbar(row3, mode="determinate", maximum=100)
        self.pb_cur.pack(side="left", fill="x", expand=True, padx=(8, 0))

        self._update_session_label()

    def _update_session_label(self):
        n = len(self.records)
        if hasattr(self, "lbl_session"):
            self.lbl_session.configure(
                text=((t("prog.session", n) + "\n" + t("prog.autosave"))) if n
                else t("prog.session_empty"))
        if hasattr(self, "lbl_count"):
            self.lbl_count.configure(text=t("res.count", n))

    # =================================================================
    # logging
    # =================================================================
    def _log(self, msg, tag=""):
        if not hasattr(self, "txt"):
            return
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n", tag)
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _classify(self, t):
        if t.startswith("      $"):
            return "cmd"
        if t.startswith("    [") and "]" in t[:9]:
            return "hdr"
        low = t.lower()
        if any(k in low for k in ("失败", "错误", "error", "[错误]", "traceback",
                                  "异常", "failed", "exception")):
            return "err"
        if any(k in low for k in ("警告", "注意", "warn", "warning")):
            return "warn"
        if ("完成" in t and "alps" in low) or " 成功" in t or \
                " done" in low or low.startswith("done"):
            return "ok"
        if t.startswith("        ") or t.startswith("      "):
            return "muted"
        return ""

    def _clear_log(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")

    def _save_log(self):
        p = filedialog.asksaveasfilename(title=t("log.save_title"),
                                         defaultextension=".txt",
                                         filetypes=[(t("ft.text"), "*.txt")],
                                         initialfile="alpsbox_log.txt")
        if p:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(self.txt.get("1.0", "end"))
            messagebox.showinfo(t("log.saved"), p)

    # =================================================================
    # environment
    # =================================================================
    def _check_env_async(self):
        self.badge.configure(text="  " + t("env.checking") + "  ", bg="#eef0f3", fg=P.TEXT_MUTED)

        def work():
            # Note: this runs on a worker thread and must not touch Tkinter
            # directly (not even after(), which raises "main thread is not in
            # main loop"). Everything goes through the queue.
            try:
                env = detect_env(verbose=False)
                self.env = env
                self.q.put(("log", env.summary()))
                self.q.put(("env", env))
            except Exception as e:
                self.q.put(("log", t("env.check_err", e)))
                self.q.put(("envfail", str(e)))

        threading.Thread(target=work, daemon=True).start()

    def _set_badge(self, env):
        if env.ok:
            self.badge.configure(text="  %s  " % t("env.ok"),
                                 bg=P.OK_LIGHT, fg=P.OK)
        else:
            self.badge.configure(text="  %s  " % t("env.bad"),
                                 bg=P.ERR_LIGHT, fg=P.ERR)
        # Refresh the ROI figure once the environment is ready (it may need the
        # template path)
        try:
            self.roi_viewer.reload(self._fsl_dir())
        except Exception:
            pass

    def _show_env_dialog(self):
        env = self.env
        if env is None:
            show_help_window(self, t("env.detail"), t("env.not_ready"))
            return
        body = env.summary()
        if not env.ok:
            body += ("\n\n" + "=" * 56 + "\n" + t("env.fix_title") + "\n"
                     + "=" * 56 + "\n" + t("env.fix_body"))
        win = show_help_window(self, t("env.detail"), body, width=780, height=580)
        btns = tk.Frame(win, bg=P.CARD)
        btns.pack(fill="x", padx=18, pady=(0, 14))
        RoundButton(btns, t("env.copy"), variant="light", height=32, padx=16,
                    parent_bg=P.CARD,
                    command=lambda: self._copy_env(env)).pack(side="left")
        RoundButton(btns, t("refresh"), variant="accent", height=32, padx=16,
                    parent_bg=P.CARD,
                    command=lambda: (win.destroy(), self._check_env_async())
                    ).pack(side="left", padx=8)
        RoundButton(btns, t("close"), variant="ghost", height=32, padx=16,
                    parent_bg=P.CARD, command=win.destroy).pack(side="right")

    def _copy_env(self, env):
        try:
            self.clipboard_clear()
            self.clipboard_append(env.summary())
            messagebox.showinfo(t("msg.copied"), t("env.copied_body"))
        except Exception as e:
            messagebox.showerror(t("msg.copy_fail"), str(e))

    # =================================================================
    # interaction
    # =================================================================
    def _on_mode(self):
        single = self.mode.get() == "single"
        self.lbl_in.configure(text=t("proc.indir") if single else t("proc.rootdir"))
        self.var_in.set("")
        self._update_summary()
        try:
            self._update_topup_ui()
        except Exception:
            pass

    def _on_roi(self):
        m = self.roi_mode.get()
        self.spn_radius.configure(state="normal" if m == "sphere" else "disabled")
        self.ent_custom.configure(state="normal" if m == "custom" else "disabled")
        self.btn_custom.set_enabled(m == "custom")

    def _browse_input(self):
        if self.mode.get() == "single":
            d = filedialog.askdirectory(title=t("proc.pick_indir"))
        else:
            d = filedialog.askdirectory(title=t("proc.pick_root"))
        if d:
            self.var_in.set(d)
            if not self.var_out.get():
                self.var_out.set(os.path.join(d, "alps_results"))

    def _toggle_advanced(self, _e=None):
        """Expand / collapse the advanced-parameter drawer."""
        if getattr(self, "_adv_open", None) is None:
            return
        if self._adv_open.get():
            self._adv_body.pack_forget()
            self._adv_open.set(False)
            self._adv_hdr.configure(text="▸  " + t("proc.advanced"))
        else:
            self._adv_body.pack(fill="x")
            self._adv_open.set(True)
            self._adv_hdr.configure(text="▾  " + t("proc.advanced"))

    def _browse_template(self):
        """Choose a custom registration template (NIfTI)."""
        p = filedialog.askopenfilename(
            title=t("proc.template"),
            filetypes=[(t("misc.nii_filter"), "*.nii *.nii.gz"), ("*", "*")])
        if p:
            self.var_template.set(p)

    def _browse_topup_second(self):
        """Pick the second DWI NIfTI used for TOPUP (manual mode)."""
        p = filedialog.askopenfilename(
            title=t("proc.topup_second"),
            filetypes=[(t("misc.nii_filter"), "*.nii *.nii.gz"), ("*", "*")])
        if p:
            self.var_topup_second.set(p)

    def _browse_topup_config(self):
        """Pick a TOPUP configuration file (b02b0.cnf)."""
        p = filedialog.askopenfilename(
            title=t("proc.topup_config"),
            filetypes=[("b02b0.cnf", "b02b0*.cnf"), ("*", "*")])
        if p:
            self.var_topup_config.set(p)

    def _update_topup_ui(self, *_a):
        """Enable/disable the TOPUP controls and show the current mode."""
        if not hasattr(self, "var_topup"):
            return
        enabled = bool(self.var_topup.get())
        batch = (self.mode.get() == "batch")
        try:
            if batch and self.var_topup_mode.get() == "manual":
                self.var_topup_mode.set("auto")
        except Exception:
            pass
        manual = (enabled and not batch
                  and self.var_topup_mode.get() == "manual")
        try:
            self.ent_topup_second.configure(
                state="normal" if manual else "disabled")
            self.btn_topup_second.set_enabled(manual)
            self.ent_topup_cfg.configure(
                state="normal" if enabled else "disabled")
            self.btn_topup_cfg.set_enabled(enabled)
            self.rb_topup_auto.configure(
                state="normal" if enabled else "disabled")
            self.rb_topup_manual.configure(
                state="disabled" if (batch or not enabled) else "normal")
        except Exception:
            pass
        if not enabled:
            txt = t("topup.status.off")
        elif batch:
            txt = t("topup.status.batch")
        elif manual:
            txt = t("topup.status.manual")
        else:
            txt = t("topup.status.auto")
        try:
            self.lbl_topup.configure(text=txt)
        except Exception:
            pass
        self._update_adv_summary()

    def _topup_settings(self):
        """Read and validate the TOPUP controls; return a settings dict or None."""
        if not hasattr(self, "var_topup") or not bool(self.var_topup.get()):
            return None
        cfg = self.var_topup_config.get().strip() or None
        if cfg and not os.path.isfile(cfg):
            raise ValueError(t("msg.topup_cfg_missing", cfg))
        batch = (self.mode.get() == "batch")
        mode = "auto" if batch else (self.var_topup_mode.get() or "auto")
        nii2 = self.var_topup_second.get().strip()
        if mode == "manual":
            if not nii2:
                raise ValueError(t("msg.topup_second_missing"))
            if not os.path.isfile(nii2):
                raise ValueError(t("msg.topup_second_notfound", nii2))
        return {"mode": mode, "nii2": nii2, "config": cfg}

    def _update_adv_summary(self, *_a):
        """Refresh the "currently effective settings" line (live on every change)."""
        lbl = getattr(self, "lbl_adv_cur", None)
        if lbl is None:
            return
        try:
            betf = float(self.var_bet_f.get())
        except Exception:
            betf = float("nan")
        cost = self.var_reg_cost.get() or "normmi"
        tpl = (self.var_template.get() or "").strip()
        tpl_s = os.path.basename(tpl) if tpl else "JHU-ICBM-FA-1mm"
        try:
            den = t("on") if bool(self.var_denoise.get()) else t("off")
        except Exception:
            den = "?"
        try:
            tp_on = bool(self.var_topup.get())
            tp_mode = self.var_topup_mode.get() if tp_on else ""
            tp_cfg = self.var_topup_config.get().strip() if tp_on else ""
        except Exception:
            tp_on, tp_mode, tp_cfg = False, "", ""
        if tp_on:
            tp_s = "%s(%s)" % (t("on"), tp_mode or "auto")
        else:
            tp_s = t("off")
        default = (abs(betf - 0.5) < 1e-9 and cost == "normmi"
                   and not tpl and den == t("off")
                   and not tp_on and not tp_cfg)
        txt = "bet_f=%.2f / %s / %s / denoise=%s / topup=%s" % (
            betf, cost, tpl_s, den, tp_s)
        if default:
            txt += t("proc.adv_recommended")
        else:
            txt += t("proc.adv_nondefault")
        try:
            lbl.configure(text=t("proc.adv_current") % txt,
                          fg=P.TEXT_FAINT if default else P.WARN)
        except Exception:
            pass

    def _reset_advanced(self):
        """Restore the recommended defaults for the advanced parameters."""
        try:
            self.var_bet_f.set(0.5)
            self.var_reg_cost.set("normmi")
            self.var_template.set("")
            self.var_denoise.set(False)
            self.var_topup.set(False)
            self.var_topup_mode.set("auto")
            self.var_topup_second.set("")
            self.var_topup_config.set("")
        except Exception:
            return
        try:
            i18n.save_pref({"adv": {"bet_f": 0.5, "reg_cost": "normmi",
                                    "template": "", "denoise": False,
                                    "topup": {"enabled": False, "mode": "auto",
                                              "config": ""}}})
        except Exception:
            pass
        self._update_topup_ui()
        self._update_adv_summary()
        self._log(t("proc.adv_reset") + ": bet_f=0.50 / normmi / "
                 "JHU-ICBM-FA-1mm / denoise=" + t("off")
                 + " / topup=" + t("off"), "muted")

    def _browse_out(self):
        d = filedialog.askdirectory(title=t("proc.pick_out"))
        if d:
            self.var_out.set(d)

    def _browse_custom(self):
        fs = filedialog.askopenfilenames(
            title=t("proc.pick_roi"),
            filetypes=[("NIfTI", "*.nii *.nii.gz"), (t("ft.all"), "*.*")])
        if fs:
            self.var_custom.set(",".join(fs))

    # =================================================================
    # queue
    # =================================================================
    def _poll_queue(self):
        try:
            n = 0
            while n < 500:
                tag, payload = self.q.get_nowait()
                if tag == "log":
                    self._append_raw(payload)
                elif tag == "progress":
                    self._set_progress(*payload)
                elif tag == "step":
                    self._set_step(*payload)
                elif tag == "record":
                    self._on_record(payload)
                elif tag == "env":
                    self._set_badge(payload)
                elif tag == "envfail":
                    self.badge.configure(text="  %s  " % t("env.fail"),
                                         bg=P.ERR_LIGHT,
                                         fg=P.ERR)
                elif tag == "done":
                    self._on_done(*payload)
                n += 1
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _append_raw(self, text):
        for ln in text.splitlines():
            if not ln.strip():
                self._log("")
                continue
            self._log(ln, self._classify(ln))
            s = ln.strip()
            if s.startswith("[") and "]" in s[:6]:
                try:
                    k = int(s[1:s.index("]")])
                    if 1 <= k <= 10:
                        self._set_step(k / 10.0, s[s.index("]") + 1:].strip()[:40])
                except Exception:
                    pass

    def _set_progress(self, frac, text):
        self.pb_total["value"] = max(0.0, min(100.0, frac * 100))
        self.lbl_total.configure(text=text)
        self._update_clock()

    def _tick_clock(self):
        """Refresh the elapsed time once per second.

        Progress messages are sparse (the eddy step can run for a quarter of an
        hour without a new message), so updating the timer only from
        _set_progress would leave it stuck at 0:00.
        """
        self._update_clock()
        self.after(1000, self._tick_clock)

    def _update_clock(self):
        if not self.t_start:
            return
        running = self.worker is not None and self.worker.is_alive()
        el = time.time() - self.t_start
        txt = "%s %s" % (t("prog.elapsed") if running
                         else t("prog.total_time"), _hms(el))
        self.lbl_elapsed.configure(text=txt)

    def _set_step(self, frac, text):
        self.pb_cur["value"] = max(0.0, min(100.0, frac * 100))
        self.lbl_cur.configure(text=t("prog.current_fmt")
                                    % (self.current_subject or t("none"), text))
        # For a single subject the overall progress equals the step progress;
        # otherwise the total progress bar would stay stuck at 15%
        if self._run_mode == "single":
            self.pb_total["value"] = max(0.0, min(100.0, frac * 100))

    # =================================================================
    # results
    # =================================================================
    def _on_record(self, rec):
        self.records = sess.merge_records(self.records, [rec])
        sess.attach_qc(self.records)
        sess.save_session(self.records)
        sess.append_history([rec])
        self._refresh_table()
        self._refresh_qc()

    def _qc_level_for(self, rec) -> str:
        """Look up the re-evaluated QC level for a subject by name (language
        independent); return an empty string when there is no match."""
        subj = str(rec.get("subject", ""))
        for rep in getattr(self, "_qc_reports", []) or []:
            if str(getattr(rep, "subject", "")) == subj:
                return getattr(rep, "level", "") or ""
        return ""

    def _refresh_table(self):
        for it in self.tree.get_children():
            self.tree.delete(it)
        for i, rec in enumerate(self.records):
            vals = []
            for c in sess.RESULT_COLUMNS:
                v = rec.get(c, "")
                if c == "status":
                    low = str(v or "").strip().lower()
                    if str(v or "").startswith("成功") or low in (
                            "ok", "success", "done"):
                        v = t("qcx.status_ok")
                    elif str(v or "").startswith("失败") or low in (
                            "failed", "fail"):
                        v = t("ui.status_failed")
                if c == "qc":
                    v = sess.qc_label(v)
                vals.append("" if v is None else
                            ("%.4f" % v if isinstance(v, float) else v))
            tag = ""
            st = str(rec.get("status", ""))
            ok_status = (not st) or st.startswith("成功") or \
                st.lower().startswith(("ok", "success", "done"))
            if st and not ok_status:
                tag = "fail"
            else:
                # Prefer the re-evaluated QCReport.level (language independent);
                # older records have no report, so fall back to the zh/en label
                # mapping to keep row colouring working in the English UI.
                lv = self._qc_level_for(rec)
                if not lv:
                    lv = {"通过": "ok", "需注意": "warn", "不合格": "fail",
                          "提示": "info", "pass": "ok", "ok": "ok",
                          "warn": "warn", "check": "warn",
                          "fail": "fail", "info": "info"}.get(
                              str(rec.get("qc", "")).strip().lower())
                if lv == "warn":
                    tag = "warn"
                elif lv == "fail":
                    tag = "fail"
                elif i % 2:
                    tag = "odd"
            self.tree.insert("", "end", values=vals, tags=(tag,) if tag else ())
        self._update_session_label()

    def _clear_results(self):
        if not self.records:
            return
        if not messagebox.askyesno(
                t("res.clear"),
                t("msg.confirm_clear", len(self.records))):
            return
        self.records = []
        sess.save_session(self.records)
        self._refresh_table()
        self._refresh_qc()
        self._log(t("log.results_cleared"), "muted")

    def _import_results(self):
        p = filedialog.askopenfilename(
            title=t("res.import_title"),
            filetypes=[(t("ft.table_json"), "*.csv *.json *.tsv *.txt"),
                       (t("ft.all"), "*.*")])
        if not p:
            return
        recs, msg = sess.import_file(p)
        if not recs:
            messagebox.showerror(t("msg.import_fail"), msg)
            return
        before = len(self.records)
        self.records = sess.merge_records(self.records, recs)
        sess.attach_qc(self.records)
        sess.save_session(self.records)
        # Remember the directory of the imported file so motion plots can later
        # find each subject's raw eddy files relative to it
        self._lookup_root = os.path.dirname(os.path.abspath(p))
        recent.remember(self._lookup_root)
        self._refresh_table()
        self._refresh_qc()
        messagebox.showinfo(
            t("msg.import_done"),
            t("msg.import_done_body", msg, len(self.records), before))
        self._log(t("log.import_results", msg), "ok")

    def _make_report(self):
        """Build the HTML report in one click (with a plain-language verdict);
        the browser can print it to PDF."""
        if not self.records:
            messagebox.showinfo(t("msg.no_data"), t("msg.table_empty"))
            return
        try:
            from . import report as _report
        except Exception as e:
            messagebox.showerror(t("res.report"), str(e))
            return
        p = filedialog.asksaveasfilename(
            title=t("res.report"), defaultextension=".html",
            filetypes=[("HTML", "*.html")], initialfile="alps_report.html")
        if not p:
            return
        try:
            _report.build_batch_html(self.records, p)
        except Exception as e:
            messagebox.showerror(t("res.report"), str(e))
            return
        messagebox.showinfo(
            t("res.report"),
            t("msg.report_done", p, len(self.records)))
        self._log(t("msg.report_done", p, len(self.records)), "ok")

    def _export(self, kind):
        if not self.records:
            messagebox.showinfo(t("msg.no_data"), t("msg.table_empty"))
            return
        if kind == "csv":
            p = filedialog.asksaveasfilename(
                title=t("res.export_csv"), defaultextension=".csv",
                filetypes=[("CSV", "*.csv")], initialfile="alps_summary.csv")
            if p:
                sess.export_csv(self.records, p)
        else:
            p = filedialog.asksaveasfilename(
                title=t("res.export_json"), defaultextension=".json",
                filetypes=[("JSON", "*.json")], initialfile="alps_summary.json")
            if p:
                sess.export_json(self.records, p)
        if p:
            messagebox.showinfo(t("msg.exported"), p)

    # =================================================================
    # preflight
    # =================================================================
    def _preflight_only(self):
        from .inputs import discover
        indir = self.var_in.get().strip()
        if not indir or not os.path.isdir(indir):
            messagebox.showerror(t("msg.input_invalid"),
                                 t("msg.input_invalid_body"))
            return
        # Tk variables must be read on the main thread; the worker below only
        # uses the resulting plain dict.
        try:
            topup = self._topup_settings()
        except ValueError as e:
            messagebox.showerror(t("msg.topup_invalid"), str(e))
            return
        self._show_page("log")
        self._log("")
        self._log("=" * 58)
        self._log(t("log.preflight", time.strftime("%H:%M:%S")))
        self._log("=" * 58)
        mode = self.mode.get()
        out = self.var_out.get().strip() or os.path.join(indir, "alps_results")

        def work():
            if mode == "batch":
                jobs = collect_jobs(indir, out)
                good, bad = preflight(
                    jobs, topup_auto=bool(topup and topup["mode"] == "auto"))
                layout_errors = (topup_layout_errors(good, bad)
                                 if topup else [])
                if layout_errors:
                    self.q.put(("log", t("batch.topup.layout_header")))
                    for e in layout_errors:
                        self.q.put(("log", "  - " + e))
                self.q.put(("log", t("log.job_count", len(jobs))))
                for j in bad:
                    self.q.put(("log", t(
                        "log.missing", j.subject,
                        j.error.split("\n")[0][:80])))
                for j in good:
                    d = j.dwi
                    ok_json = (t("log.yes") if (d and d.has_eddy_metadata)
                               else t("log.no"))
                    pe = d.json_info.get("PhaseEncodingDirection", "-") if d else "-"
                    self.q.put(("log", t("log.runnable", j.subject,
                                         ok_json, pe)))
                    if topup and j.topup:
                        self.q.put(("log", "    " + j.topup))
                self.q.put(("log", t("log.preflight_sum", len(good),
                                     len(bad))))
            else:
                try:
                    d = discover(indir)
                    self.q.put(("log", t(
                        "log.found_dwi", os.path.basename(d.nii))))
                    if topup:
                        from .inputs import (attach_second_from_nii,
                                            auto_attach_topup)
                        try:
                            if topup["mode"] == "manual":
                                ok, why = attach_second_from_nii(
                                    d, topup["nii2"])
                            else:
                                ok, why = auto_attach_topup(
                                    d, indir, search_siblings=True)
                        except Exception as e:
                            self.q.put(("log", t("msg.topup_second_invalid",
                                                 e)))
                            ok, why = False, str(e)
                        if not ok:
                            self.q.put(("log", t("misc.dwi.topup_off", why)))
                    self.q.put(("log", d.describe()))
                except Exception as e:
                    self.q.put(("log", t("log.missing_one", e)))

        threading.Thread(target=work, daemon=True).start()

    # =================================================================
    # run
    # =================================================================
    def _start(self):
        if self.worker and self.worker.is_alive():
            return
        if self.env is None or not self.env.ok:
            messagebox.showerror(
                t("env.bad"),
                t("env.not_ok_body"))
            self._show_page("help")
            return
        indir = self.var_in.get().strip()
        outdir = self.var_out.get().strip()
        if not indir or not os.path.isdir(indir):
            messagebox.showerror(t("msg.input_invalid"),
                                 t("msg.input_missing_body"))
            return
        if not outdir:
            messagebox.showerror(t("msg.output_invalid"),
                                 t("msg.output_invalid_body"))
            return
        try:
            topup = self._topup_settings()
        except ValueError as e:
            messagebox.showerror(t("msg.topup_invalid"), str(e))
            return
        custom = None
        if self.roi_mode.get() == "custom":
            custom = [x for x in self.var_custom.get().split(",") if x.strip()]
            if len(custom) != 4:
                messagebox.showerror(
                    t("msg.roi_invalid"),
                    t("msg.roi_invalid_body"))
                return
        opts = PipelineOptions(
            radius=float(self.var_radius.get()),
            topup_config=(topup["config"] if topup else None),
            unring=bool(self.var_unring.get()),
            regqc=bool(getattr(self, "var_regqc",
                               tk.BooleanVar(value=False)).get()),
            use_bundled_roi=(self.roi_mode.get() == "bundled"),
            custom_rois=custom,
            threads=int(self.var_threads.get()),
            force=bool(self.var_force.get()),
            bet_f=float(getattr(self, "var_bet_f",
                                tk.DoubleVar(value=0.5)).get()),
            reg_cost=str(getattr(self, "var_reg_cost",
                                 tk.StringVar(value="normmi")).get()),
            template=(self.var_template.get().strip() or None)
            if hasattr(self, "var_template") else None,
            denoise=bool(getattr(self, "var_denoise",
                                 tk.BooleanVar(value=False)).get()),
        )
        # Remember the advanced parameters for the next session
        try:
            i18n.save_pref({"adv": {
                "bet_f": float(getattr(self, "var_bet_f",
                                       tk.DoubleVar(value=0.5)).get()),
                "reg_cost": str(getattr(self, "var_reg_cost",
                                        tk.StringVar(value="normmi")).get()),
                "template": (self.var_template.get().strip()
                             if hasattr(self, "var_template") else ""),
                "denoise": bool(getattr(self, "var_denoise",
                                        tk.BooleanVar(value=False)).get()),
                "topup": {
                    "enabled": bool(getattr(self, "var_topup",
                                            tk.BooleanVar(value=False)).get()),
                    "mode": str(getattr(self, "var_topup_mode",
                                        tk.StringVar(value="auto")).get()),
                    "config": (self.var_topup_config.get().strip()
                               if hasattr(self, "var_topup_config") else ""),
                },
            }})
        except Exception:
            pass
        mode = self.mode.get()
        self._run_mode = mode
        self._last_out = outdir
        self.stop_flag.clear()
        self.btn_go.set_enabled(False)
        self.btn_stop.set_enabled(True)
        self.t_start = time.time()
        self.pb_total["value"] = 0
        self.pb_cur["value"] = 0
        self.lbl_cur.configure(
            text="%s%s%s" % (t("prog.current"), t("sep.colon"),
                             t("proc.preparing")))
        self._show_page("log")
        self._log("")
        self._log("=" * 58)
        self._log(t("log.start", time.strftime("%H:%M:%S"),
                    t("msg.mode_batch") if mode == "batch"
                    else t("msg.mode_single")))
        self._log("  %s%s%s" % (t("msg.input"), t("sep.colon"), indir))
        self._log("  %s%s%s" % (t("msg.output"), t("sep.colon"), outdir))
        self._log("=" * 58)
        self.worker = threading.Thread(
            target=self._run_worker,
            args=(indir, outdir, opts, mode, topup), daemon=True)
        self.worker.start()

    def _run_worker(self, indir, outdir, opts, mode, topup=None):
        old = sys.stdout
        sys.stdout = QueueWriter(self.q)
        try:
            if mode == "batch":
                jobs = collect_jobs(indir, outdir)
                if not jobs:
                    self.q.put(("log", t("log.no_subdirs")))
                    self.q.put(("done", ([], outdir)))
                    return
                if not opts.force:
                    done = [j for j in jobs if os.path.isfile(
                        os.path.join(j.out_dir, "alps_result.json"))]
                    if done:
                        self.q.put(("log",
                                    t("log.skipped_done", len(done))))
                        jobs = [j for j in jobs if j not in done]
                if not jobs:
                    self.q.put(("log", t("log.all_done")))
                    self.q.put(("done", ([], outdir)))
                    return
                good, bad = preflight(
                    jobs, topup_auto=bool(topup and topup["mode"] == "auto"))
                layout_errors = (topup_layout_errors(good, bad)
                                 if topup else [])
                try:
                    report = write_preflight_report(good, bad, outdir,
                                                    layout_errors)
                    self.q.put(("log", t("cli.batch.report", report)))
                except Exception:
                    pass
                for j in bad:
                    self.q.put(("log", t(
                        "log.skipped", j.subject,
                        j.error.split("\n")[0][:80])))
                    self.q.put(("record", {
                        "subject": j.subject,
                        "status": j.error.split("\n")[0][:120],
                        "finished_at": time.strftime("%Y-%m-%d %H:%M")}))
                if layout_errors:
                    self.q.put(("log", t("batch.topup.layout_header")))
                    for e in layout_errors:
                        self.q.put(("log", "  - " + e))
                    self.q.put(("log", t("cli.batch.blocked")))
                    self.q.put(("done", ([], outdir)))
                    return
                if topup:
                    for j in good:
                        if j.topup:
                            self.q.put(("log", "    " + j.topup))
                total = len(good)
                self.q.put(("log", t("log.batch_total", total)))
                pipe = AlspPipeline(self.env, opts)
                results = []
                for i, j in enumerate(good, 1):
                    if self.stop_flag.is_set():
                        self.q.put(("log",
                                    t("msg.stopped", i - 1, total)))
                        break
                    self.current_subject = j.subject
                    self.q.put(("step", (0.0, t("proc.preparing"))))
                    self.q.put(("progress", (100.0 * (i - 1) / max(total, 1),
                                             "%d/%d  %s" % (i, total, j.subject))))
                    self.q.put(("log", ""))
                    self.q.put(("log", "=" * 58))
                    self.q.put(("log", "[%d/%d] %s   %s"
                                % (i, total, j.subject, time.strftime("%H:%M:%S"))))
                    self.q.put(("log", "=" * 58))
                    r = pipe.run(j.subject, j.dwi, j.out_dir)
                    results.append(r)
                    self.q.put(("record", sess.result_to_record(r)))
                    el = time.time() - self.t_start
                    eta = (el / i) * (total - i) if i else 0
                    self.q.put(("progress", (100.0 * i / max(total, 1),
                                             t("prog.batch_line",
                                               i, total, _hms(el),
                                               _hms(eta)))))
                    self.q.put(("step", (1.0, t("proc.completed"))))
                try:
                    os.makedirs(outdir, exist_ok=True)
                    all_results = collect_results(outdir, results)
                    write_summary(all_results,
                                  os.path.join(outdir, "alps_summary.csv"))
                    txt = write_qc_report(all_results,
                                          os.path.join(outdir, "qc_report.txt"))
                    self.q.put(("log", ""))
                    self.q.put(("log", txt))
                except Exception as e:
                    self.q.put(("log", t("log.summary_fail", e)))
                self.q.put(("done", (results, outdir)))
            else:
                from .inputs import discover
                name = os.path.basename(os.path.normpath(indir))
                self.current_subject = name
                self.q.put(("progress", (5.0, t("proc.checking_input"))))
                try:
                    dwi = discover(indir)
                except Exception as e:
                    self.q.put(("log", t("log.discover_fail", e)))
                    self.q.put(("record", {
                        "subject": name, "status": str(e)[:120],
                        "finished_at": time.strftime("%Y-%m-%d %H:%M")}))
                    self.q.put(("done", ([], outdir)))
                    return
                if topup:
                    from .inputs import (TopupPairError,
                                        attach_second_from_nii,
                                        auto_attach_topup)
                    try:
                        if topup["mode"] == "manual":
                            ok, why = attach_second_from_nii(
                                dwi, topup["nii2"])
                        else:
                            ok, why = auto_attach_topup(
                                dwi, indir, search_siblings=True)
                    except TopupPairError as e:
                        msg = t("msg.topup_second_invalid", e)
                        self.q.put(("log", msg))
                        self.q.put(("record", {
                            "subject": name, "status": msg[:120],
                            "finished_at": time.strftime(
                                "%Y-%m-%d %H:%M")}))
                        self.q.put(("done", ([], outdir)))
                        return
                    except Exception as e:
                        ok, why = False, str(e)
                    if not ok:
                        if topup["mode"] == "manual":
                            msg = t("msg.topup_second_invalid", why)
                            self.q.put(("log", msg))
                            self.q.put(("record", {
                                "subject": name, "status": msg[:120],
                                "finished_at": time.strftime(
                                    "%Y-%m-%d %H:%M")}))
                            self.q.put(("done", ([], outdir)))
                            return
                        self.q.put(("log", t("misc.dwi.topup_off", why)))
                self.q.put(("log", dwi.describe()))
                out_sub = os.path.join(outdir, name)
                self.q.put(("progress", (15.0, t("proc.starting", name))))
                pipe = AlspPipeline(self.env, opts)
                r = pipe.run(name, dwi, out_sub)
                self.q.put(("record", sess.result_to_record(r)))
                try:
                    os.makedirs(outdir, exist_ok=True)
                    write_summary([r], os.path.join(outdir, "alps_summary.csv"))
                except Exception:
                    pass
                self.q.put(("step", (1.0, t("proc.completed"))))
                self.q.put(("progress",
                            (100.0, t("proc.completed") if r.ok
                             else t("proc.failed"))))
                self.q.put(("done", ([r], outdir)))
        except Exception:
            self.q.put(("log", t("log.internal_error")
                        + traceback.format_exc()))
            self.q.put(("done", ([], outdir)))
        finally:
            sys.stdout = old

    def _on_done(self, results, outdir):
        self.btn_go.set_enabled(True)
        self.btn_stop.set_enabled(False)
        ok = sum(1 for r in results if getattr(r, "ok", False))
        tot = len(results)
        el = time.time() - self.t_start if self.t_start else 0
        self._log("")
        self._log("=" * 58)
        if tot:
            self._log(t("msg.done_ok", ok, tot, _hms(el)),
                      "ok" if ok == tot else "warn")
        else:
            self._log(t("msg.done_none", _hms(el)), "muted")
        self._log(t("msg.result_dir") + t("sep.colon") + outdir)
        self._log("=" * 58)
        self.lbl_total.configure(
            text=t("prog.done", ok, tot, _hms(el)))
        self.current_subject = ""
        self.lbl_cur.configure(text=t("prog.current_none"))
        self.pb_cur["value"] = 0
        self._update_clock()
        self._refresh_qc()
        if tot:
            self._show_page("results")

    def _stop(self):
        if not (self.worker and self.worker.is_alive()):
            return
        if messagebox.askyesno(
                t("msg.stop_title"),
                t("msg.confirm_stop")):
            self.stop_flag.set()
            self._log(t("msg.stop_req"), "warn")

    # =================================================================
    # shutdown
    # =================================================================
    def _on_close(self):
        if self._closing:
            return
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno(
                    t("msg.busy_title"),
                    t("msg.confirm_close")):
                return
            self.stop_flag.set()
        try:
            sess.save_session(self.records)
        except Exception:
            pass
        self._closing = True
        self.destroy()


def _hms(sec):
    sec = int(max(0, sec))
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))


def main(lang=None):
    """Start the GUI. An explicit language code (CLI --lang) wins; otherwise the
    saved preference or the system language is used."""
    if lang in i18n.LANGS:
        i18n.set_lang(lang, save=False)
    else:
        i18n.init_lang()
    App().mainloop()


if __name__ == "__main__":
    main()

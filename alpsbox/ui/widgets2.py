# -*- coding: utf-8 -*-
"""Rounded cards, rounded buttons and the interactive ROI view."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..i18n import t
from .theme import Palette as P
from .. import text_ui  # noqa: F401


def _round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    """Draw a rounded rectangle on a canvas (polygon approximation, high smoothness)."""
    r = max(0, min(r, abs(x2 - x1) // 2, abs(y2 - y1) // 2))
    pts = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


class RoundedCard(tk.Frame):
    """Card container with rounded corners and a hairline border. Content goes
    into ``.body``.

    With auto_height=True the card height follows its content (pack it into the
    parent with pack(fill='x')).
    """

    def __init__(self, parent, bg: str = P.CARD, radius: int = 10,
                 border: str = P.BORDER, outer_bg: str = P.BG,
                 padding=(16, 14), shadow: bool = True,
                 auto_height: bool = True):
        super().__init__(parent, bg=outer_bg, highlightthickness=0, bd=0)
        self._bg = bg
        self._radius = radius
        self._border = border
        self._pad = padding
        self._shadow = shadow
        self._auto_h = auto_height

        self.canvas = tk.Canvas(self, bg=outer_bg, highlightthickness=0, bd=0,
                                height=60)
        self.canvas.pack(fill="both", expand=True)

        self.body = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")

        self.canvas.bind("<Configure>", self._redraw)
        self.body.bind("<Configure>", self._on_body)

    def _on_body(self, _evt=None):
        if self._auto_h:
            px, py = self._pad
            h = max(20, self.body.winfo_reqheight() + 2 * py + 4)
            if abs(int(self.canvas.cget("height")) - h) > 2:
                self.canvas.configure(height=h)
        self._redraw()

    def _redraw(self, _evt=None):
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w <= 2 or h <= 2:
            return
        c.delete("chrome")
        r = self._radius
        pad = 3 if self._shadow else 0
        if self._shadow:
            _round_rect(c, pad + 1, pad + 2, w - 1, h - 1, r,
                        fill="#e9ebef", outline="", tags="chrome")
        _round_rect(c, 0, 0, w - pad - 1, h - pad - 1, r,
                    fill=self._bg, outline=self._border, width=1, tags="chrome")
        c.tag_lower("chrome")
        px, py = self._pad
        c.coords(self._win, px, py)
        c.itemconfigure(self._win, width=max(10, w - pad - 2 * px))


class RoundButton(tk.Canvas):
    """Rounded button with hover highlight and hand cursor."""

    VARIANTS = {
        "accent": dict(fill=P.ACCENT, hover=P.ACCENT_HOVER, fg="#ffffff",
                       border=P.ACCENT),
        "light": dict(fill=P.CARD, hover="#eef1f5", fg=P.TEXT,
                      border=P.BORDER_STRONG),
        "ghost": dict(fill=P.BG, hover="#e8eaee", fg=P.TEXT_MUTED, border=P.BG),
        "danger": dict(fill=P.CARD, hover=P.ERR_LIGHT, fg=P.ERR,
                       border=P.BORDER_STRONG),
        "ok": dict(fill=P.OK, hover="#166b2e", fg="#ffffff", border=P.OK),
    }

    def __init__(self, parent, text: str, command=None, variant: str = "light",
                 radius: int = 8, font=None, width: int = 0, height: int = 34,
                 padx: int = 18, parent_bg: str = None, enabled: bool = True):
        self._bg = parent_bg or P.BG
        super().__init__(parent, bg=self._bg, highlightthickness=0, bd=0,
                         cursor="hand2" if enabled else "arrow")
        self._text = text
        self._cmd = command
        self._v = self.VARIANTS.get(variant, self.VARIANTS["light"])
        self._r = radius
        self._font = font or ("TkDefaultFont", 9)
        self._padx = padx
        self._h = height
        self._enabled = enabled
        self._hover = False
        self._pressed = False
        self._fixed_w = width

        self._measure()
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    # ---- geometry ----
    def _measure(self):
        f = tk.font.Font(font=self._font) if hasattr(tk, "font") else None
        try:
            import tkinter.font as tkfont
            f = tkfont.Font(font=self._font)
            tw = f.measure(self._text)
            th = f.metrics("linespace")
        except Exception:
            tw, th = len(self._text) * 9, 14
        self._tw, self._th = tw, th
        w = self._fixed_w or (tw + 2 * self._padx)
        self.configure(width=w, height=self._h)

    # ---- drawing ----
    def _draw(self):
        self.delete("all")
        w = self.winfo_width() or int(self.configure("width")[3])
        h = self.winfo_height() or self._h
        if w <= 2 or h <= 2:
            return
        if not self._enabled:
            fill, border, fg = "#eef0f3", P.BORDER, P.TEXT_FAINT
        else:
            fill = (P.ACCENT_HOVER if self._pressed else
                    (self._v["hover"] if self._hover else self._v["fill"]))
            border = self._v["border"]
            fg = self._v["fg"]
        _round_rect(self, 0, 0, w - 1, h - 1, self._r,
                    fill=fill, outline=border, width=1)
        self.create_text(w // 2, h // 2 + 1, text=self._text, fill=fg,
                         font=self._font)

    # ---- events ----
    def _on_enter(self, _e):
        if self._enabled:
            self._hover = True
            self._draw()

    def _on_leave(self, _e):
        self._hover = False
        self._pressed = False
        self._draw()

    def _on_press(self, _e):
        if self._enabled:
            self._pressed = True
            self._draw()

    def _on_release(self, _e):
        if not self._enabled:
            return
        was = self._pressed
        self._pressed = False
        self._draw()
        if was and self._cmd:
            self._cmd()

    # ---- API ----
    def set_enabled(self, on: bool):
        self._enabled = bool(on)
        self.configure(cursor="hand2" if on else "arrow")
        self._draw()

    def set_text(self, t: str):
        self._text = t
        self._measure()
        self._draw()


class FigurePanel(tk.Frame):
    """Zoomable, pannable image panel.

    Unlike scaling a bitmap, this panel **re-renders at the target pixel size**
    whenever the size or zoom level changes, so text stays sharp at any zoom.

    render_fn(width_px, height_px) -> PIL.Image
    """

    def __init__(self, parent, render_fn, bg: str = P.CARD,
                 aspect: float = None, dpi: int = 100,
                 min_zoom: float = 1.0, max_zoom: float = 4.0,
                 toolbar: bool = True):
        """aspect=None fills the panel at its actual ratio; a number centres the
        image at that aspect ratio."""
        super().__init__(parent, bg=bg)
        self._bg = bg
        self._render_fn = render_fn
        self._aspect = (None if aspect is None else max(0.2, float(aspect)))
        self._dpi = dpi
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom
        self._zoom = 1.0
        self._job = None
        self._img = None
        self._photo = None
        self._drag = None
        self._off = [0, 0]          # image top-left offset from the canvas centre
        self.last_error = None

        if toolbar:
            bar = tk.Frame(self, bg=bg)
            bar.pack(fill="x", pady=(0, 4))
            for txt, cmd in ((t("fig.fit"), self.fit),
                             (t("fig.zoom_in"), lambda: self.zoom_by(1.25)),
                             (t("fig.zoom_out"), lambda: self.zoom_by(1 / 1.25))):
                b = tk.Label(bar, text=txt, bg=bg, fg=P.TEXT_MUTED,
                             font=("TkDefaultFont", 9), padx=8, pady=3,
                             cursor="hand2")
                b.pack(side="left", padx=(0, 2))
                b.bind("<Button-1>", lambda e, c=cmd: c())
                b.bind("<Enter>", lambda e, w=b: w.configure(fg=P.ACCENT))
                b.bind("<Leave>", lambda e, w=b: w.configure(fg=P.TEXT_MUTED))
            self.lbl_zoom = tk.Label(bar, text="100%", bg=bg, fg=P.TEXT_FAINT,
                                     font=("TkDefaultFont", 8))
            self.lbl_zoom.pack(side="right", padx=(0, 4))
            tk.Label(bar, bg=bg, fg=P.TEXT_FAINT, font=("TkDefaultFont", 8),
                     text=t("fig.hint")).pack(side="right", padx=(0, 10))

        self.canvas = tk.Canvas(self, bg="#ffffff", highlightthickness=0, bd=0,
                                cursor="fleur")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag", None))
        # On Linux, middle-button / wheel dragging also pans
        self.canvas.bind("<ButtonPress-2>", self._on_press)
        self.canvas.bind("<B2-Motion>", self._on_drag)

    # ---------------- rendering ----------------
    def _target_px(self):
        W = max(320, self.canvas.winfo_width())
        H = max(200, self.canvas.winfo_height())
        a = self._aspect
        if a is None:
            w, h = W, H
        else:
            if W / float(H) > a:
                h = H
                w = h * a
            else:
                w = W
                h = w / a
        return max(240, int(w * self._zoom)), max(140, int(h * self._zoom))

    def reload(self):
        """Re-render (called when the data or the size changes)."""
        self._job = None
        w, h = self._target_px()
        try:
            img = self._render_fn(w, h)
        except Exception as e:
            self.last_error = str(e)
            self.canvas.delete("all")
            self.canvas.create_text(16, 16, anchor="nw", fill="#ffb4b4",
                                    width=max(200, w - 32),
                                    text=t("ui.plot_fail", e),
                                    font=("TkDefaultFont", 9))
            return
        self.last_error = None
        self._img = img
        self._show()

    def _show(self):
        if self._img is None:
            return
        try:
            from PIL import ImageTk
        except Exception:
            return
        self._photo = ImageTk.PhotoImage(self._img)
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        cx = cw // 2 + self._off[0]
        cy = ch // 2 + self._off[1]
        self.canvas.delete("all")
        self.canvas.create_image(cx, cy, image=self._photo, anchor="center")
        if hasattr(self, "lbl_zoom"):
            self.lbl_zoom.configure(text="%d%%" % round(self._zoom * 100))

    def _schedule(self, delay=220):
        if self._job is not None:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        self._job = self.after(delay, self.reload)

    def _on_configure(self, evt=None):
        # Re-layout on splitter drags or window resizes; debounce the re-render
        self._schedule(260)

    # ---------------- zoom ----------------
    def fit(self):
        self._zoom = 1.0
        self._off = [0, 0]
        self._schedule(10)

    def zoom_by(self, k):
        self._set_zoom(self._zoom * k)

    def _set_zoom(self, z):
        z = max(self._min_zoom, min(self._max_zoom, float(z)))
        if abs(z - self._zoom) < 1e-3:
            return
        self._zoom = z
        self._schedule(60)

    def _on_wheel(self, evt):
        if getattr(evt, "num", None) == 4:
            k = 1.2
        elif getattr(evt, "num", None) == 5:
            k = 1 / 1.2
        else:
            k = 1.2 if evt.delta > 0 else 1 / 1.2
        self.zoom_by(k)

    # ---------------- pan ----------------
    def _on_press(self, evt):
        self._drag = (evt.x, evt.y, self._off[0], self._off[1])

    def _on_drag(self, evt):
        if not self._drag:
            return
        x0, y0, ox, oy = self._drag
        self._off = [ox + (evt.x - x0), oy + (evt.y - y0)]
        self._show()

    # ---------------- save ----------------
    def current_image(self):
        return self._img


class RoiViewer(tk.Frame):
    """Interactive ROI view: hover highlight, click selection, wheel zoom and
    view switching."""

    def __init__(self, parent, fsl_dir: Optional[str] = None,
                 bg: str = P.CARD, width: int = 420, height: int = 420):
        super().__init__(parent, bg=bg)
        self._bg = bg
        self._fsl = fsl_dir
        self._views = {}
        self._plane = "axial"
        self._zoom = 2.0
        self._imgtk = None
        self._photo = None
        self._selected = None
        self._hover = None
        self._labels = None
        self._ox = self._oy = 0       # image top-left position on the canvas
        self._iw = self._ih = 0
        self._pan = [0, 0]            # pan offset produced by user dragging
        self._drag = None

        try:
            from ..roi_preview import ROI_TITLE
            self._titles = ROI_TITLE
        except Exception:
            self._titles = {}

        # Top toolbar
        bar = tk.Frame(self, bg=bg)
        bar.pack(fill="x", pady=(0, 6))
        self._btns = {}
        for key, label in (("axial", t("roi.axial")), ("coronal", t("roi.coronal"))):
            b = tk.Label(bar, text=label, bg=bg, fg=P.TEXT_MUTED,
                         font=("TkDefaultFont", 9), padx=10, pady=4,
                         cursor="hand2")
            b.pack(side="left", padx=(0, 4))
            b.bind("<Button-1>", lambda e, k=key: self.set_plane(k))
            b.bind("<Enter>", lambda e, w=b: w.configure(fg=P.ACCENT))
            b.bind("<Leave>", lambda e, w=b: w.configure(
                fg=P.ACCENT if self._plane == w._plane else P.TEXT_MUTED))
            b._plane = key
            self._btns[key] = b

        self.lbl_info = tk.Label(bar, text="", bg=bg, fg=P.TEXT_FAINT,
                                 font=("TkDefaultFont", 8), anchor="e")
        self.lbl_info.pack(side="right")

        # Canvas
        self.canvas = tk.Canvas(self, bg="#20242a", highlightthickness=0,
                                bd=0, width=width, height=height,
                                cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel)
        self.canvas.bind("<Button-5>", self._on_wheel)
        self.canvas.bind("<Configure>", lambda e: self._render())
        # Middle-button drag pans; the left button still selects ROIs
        self.canvas.bind("<ButtonPress-2>", self._pan_press)
        self.canvas.bind("<B2-Motion>", self._pan_drag)
        self.canvas.bind("<ButtonRelease-2>", lambda e: setattr(self, "_drag", None))

        # Legend
        self.legend = tk.Frame(self, bg=bg)
        self.legend.pack(fill="x", pady=(6, 0))
        self._legend_items = {}

        self.lbl_hint = tk.Label(self, bg=bg, fg=P.TEXT_FAINT,
                                 font=("TkDefaultFont", 8), anchor="w",
                                 justify="left")
        self.lbl_hint.pack(fill="x", pady=(4, 0))
        self.lbl_hint.configure(
            text=t("roi.hover_hint"))

        self._build_legend()
        self._highlight_plane(self._plane)

    # ---------- legend ----------
    def _build_legend(self):
        try:
            from ..roi_preview import ROI_ORDER, ROI_COLOR, ROI_TITLE
        except Exception:
            return
        for name in ROI_ORDER:
            row = tk.Frame(self.legend, bg=self._bg, cursor="hand2")
            row.pack(side="left", padx=(0, 12))
            r, g, b = ROI_COLOR[name]
            sw = tk.Frame(row, bg="#%02x%02x%02x" % (r, g, b), width=11, height=11)
            sw.pack(side="left", padx=(0, 4))
            lb = tk.Label(row, text=ROI_TITLE[name], bg=self._bg, fg=P.TEXT_MUTED,
                          font=("TkDefaultFont", 8))
            lb.pack(side="left")
            for w in (row, sw, lb):
                w.bind("<Enter>", lambda e, n=name: self._set_hover(n))
                w.bind("<Leave>", lambda e: self._set_hover(None))
                w.bind("<Button-1>", lambda e, n=name: self._select(n))
            self._legend_items[name] = (row, sw, lb)

    # ---------- orientation ----------
    def set_plane(self, plane: str):
        if plane == self._plane:
            return
        self._plane = plane
        self._highlight_plane(plane)
        self._render()

    def _highlight_plane(self, plane):
        for k, w in self._btns.items():
            w.configure(fg=P.ACCENT if k == plane else P.TEXT_MUTED,
                        font=("TkDefaultFont", 9, "bold" if k == plane else "normal"))

    # ---------- data ----------
    def _get_view(self):
        if self._plane in self._views:
            return self._views[self._plane]
        from ..roi_preview import build_slice
        v = build_slice(self._fsl, self._plane, zoom=self._zoom)
        self._views[self._plane] = v
        return v

    def reload(self, fsl_dir: Optional[str] = None):
        if fsl_dir:
            self._fsl = fsl_dir
        self._views.clear()
        self._render()

    # ---------- rendering ----------
    def _render(self):
        try:
            v = self._get_view()
        except Exception as e:
            self.canvas.delete("all")
            self.canvas.create_text(12, 12, anchor="nw", fill="#ffb4b4",
                                    text=t("ui.roi_preview_unavailable", e),
                                    font=("TkDefaultFont", 9), width=380)
            return
        self._labels = v.labels
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 4 or ch <= 4:
            return
        try:
            from PIL import Image, ImageTk
        except Exception:
            return

        img = v.image
        if self._hover:
            img = self._apply_hover(img, v)
        if self._selected:
            img = self._draw_selection(img, v)

        # Scale uniformly to fit the canvas
        scale = min(cw / img.width, ch / img.height)
        nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
        disp = img.resize((nw, nh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(disp)
        self._iw, self._ih = nw, nh
        self._ox = (cw - nw) // 2 + self._pan[0]
        self._oy = (ch - nh) // 2 + self._pan[1]

        self.canvas.delete("all")
        # Checkerboard backdrop
        self.canvas.create_rectangle(self._ox, self._oy,
                                     self._ox + nw, self._oy + nh,
                                     fill="#15181d", outline="")
        self.canvas.create_image(self._ox, self._oy, image=self._photo,
                                 anchor="nw")

        note = v.note or ""
        sub = "%s  %s %d" % (
            t("roi.axial") if v.plane == "axial" else t("roi.coronal"),
            t("roi.layer"), v.slice_idx)
        if v.is_projection:
            sub += t("ui.projection_note")
        self.lbl_info.configure(text=(note or sub))

    def _apply_hover(self, img, v):
        try:
            from PIL import Image
            import numpy as np
            from ..roi_preview import ROI_ORDER, ROI_COLOR_HI
            k = ROI_ORDER.index(self._hover) + 1
            a = np.array(img, dtype=np.uint8)
            m = v.labels == k
            if m.any():
                a[m] = np.array(ROI_COLOR_HI[self._hover], np.uint8)
            return Image.fromarray(a)
        except Exception:
            return img

    def _draw_selection(self, img, v):
        try:
            from PIL import Image, ImageDraw
            from ..roi_preview import ROI_ORDER, ROI_COLOR
            k = ROI_ORDER.index(self._selected) + 1
            im = img.copy()
            d = ImageDraw.Draw(im)
            col = ROI_COLOR[self._selected]
            line = (16, int(self._zoom * 2.4))
            # A crosshair in canvas coordinates would shift with zoom, so fall
            # back to a simple marker (the box is drawn during rendering)
            self._sel_box = (v.labels == k)
            return im
        except Exception:
            return img

    # ---------- interaction ----------
    def _canvas_to_voxel(self, x, y):
        if not self._iw or not self._ih:
            return None
        ix, iy = x - self._ox, y - self._oy
        if not (0 <= ix < self._iw and 0 <= iy < self._ih):
            return None
        r = int(iy * self._labels.shape[0] / self._ih)
        c = int(ix * self._labels.shape[1] / self._iw)
        r = max(0, min(self._labels.shape[0] - 1, r))
        c = max(0, min(self._labels.shape[1] - 1, c))
        return r, c

    def _on_motion(self, evt):
        rv = self._canvas_to_voxel(evt.x, evt.y)
        if rv is None:
            self._set_hover(None)
            return
        k = int(self._labels[rv])
        name = None
        if k > 0:
            try:
                from ..roi_preview import ROI_ORDER
                name = ROI_ORDER[k - 1]
            except Exception:
                name = None
        self._set_hover(name)
        self.canvas.configure(cursor="hand2" if name else "crosshair")

    def _on_leave(self, _e=None):
        self._set_hover(None)
        self.canvas.configure(cursor="crosshair")

    def _on_click(self, evt):
        rv = self._canvas_to_voxel(evt.x, evt.y)
        if rv is None:
            return
        k = int(self._labels[rv])
        if k > 0:
            from ..roi_preview import ROI_ORDER
            self._select(ROI_ORDER[k - 1])
        else:
            self._select(None)

    def _on_wheel(self, evt):
        delta = 1 if getattr(evt, "num", None) == 5 else (
            -1 if getattr(evt, "num", None) == 4 else (-1 if evt.delta > 0 else 1))
        self._zoom = min(6.0, max(1.0, self._zoom + 0.5 * delta))
        self._views.clear()
        if self._zoom <= 1.0:
            self._pan = [0, 0]
        self._render()

    def _pan_press(self, evt):
        self._drag = (evt.x, evt.y, self._pan[0], self._pan[1])

    def _pan_drag(self, evt):
        if not self._drag:
            return
        x0, y0, px, py = self._drag
        self._pan = [px + (evt.x - x0), py + (evt.y - y0)]
        self._render()

    def fit(self):
        """Reset to fit the window and centre the image."""
        self._zoom = 2.0
        self._pan = [0, 0]
        self._views.clear()
        self._render()

    def _set_hover(self, name):
        if name == self._hover:
            return
        self._hover = name
        for k, (row, sw, lb) in self._legend_items.items():
            on = (k == name)
            lb.configure(fg=P.TEXT if on else P.TEXT_MUTED,
                         font=("TkDefaultFont", 8, "bold" if on else "normal"))
        self._render()

    def _select(self, name):
        self._selected = name
        for k, (row, sw, lb) in self._legend_items.items():
            on = (k == name)
            lb.configure(fg=P.ACCENT if on else P.TEXT_MUTED,
                         font=("TkDefaultFont", 8, "bold" if on else "normal"))
        self._render()
        if name:
            try:
                from ..roi_preview import ROI_TITLE, ROI_LATIN, ROI_FIBER
                self.lbl_hint.configure(
                    text="%s（%s）：%s。" % (ROI_TITLE[name], ROI_LATIN[name],
                                            ROI_FIBER[name]))
            except Exception:
                pass

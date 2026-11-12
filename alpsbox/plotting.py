# -*- coding: utf-8 -*-
"""QC plots: head-motion time course and cross-subject scatter.

In-figure text follows the current interface language (the ``qcx.plot.*``
strings). Chinese mode requires a usable Chinese font on this machine: common
Chinese fonts that also carry Latin glyphs are preferred (Microsoft YaHei,
PingFang, Source Han Sans, WenQuanYi, AR PL, etc.) and are set explicitly as the
matplotlib font, which avoids missing glyphs when text such as "mm/%" is mixed
in. If no such font is installed, in-figure text automatically stays in English
rather than degenerating into missing-glyph boxes (the English interface and
English figures are still recommended, especially for publication).

All functions return a PIL.Image, so Tkinter can display them directly and they
can also be written straight to disk.
"""
from __future__ import annotations

import os
from typing import List, Optional

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")                       # render without a display
    import matplotlib.pyplot as plt
except Exception:                               # pragma: no cover
    plt = None

from . import rescan, text_qc
from .i18n import get_lang, t
from .text_qc import LangDict

# Shared colour palette, consistent with the interface
C_ABS = "#2563eb"
C_REL = "#0d9d8c"
C_WARN = "#9a6700"
C_FAIL = "#cf222e"
C_OUT = "#e5484d"
C_GRID = "#e3e6ea"
C_TEXT = "#1f2328"

# ---------------------------------------------------------------------
# In-figure text: follows the interface language, falls back to English when no
# Chinese font is available
# ---------------------------------------------------------------------
# Only Chinese fonts that also carry Latin glyphs are listed; fonts such as
# Droid Sans Fallback lack Latin glyphs and would produce missing glyphs in
# mixed text, so they are deliberately omitted.
_CJK_FONTS = ("Microsoft YaHei", "PingFang SC", "Hiragino Sans GB",
              "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei",
              "SimHei", "AR PL SungtiL GB", "AR PL Mingti2L Big5")
_cjk_font: list = []          # cache: empty until probed, then [None] or [name]


def _font_for_cjk() -> Optional[str]:
    """Find the name of a Chinese font that also carries Latin glyphs; return
    None if there is none."""
    if not _cjk_font:
        found = None
        try:
            from matplotlib import font_manager
            names = {f.name for f in font_manager.fontManager.ttflist}
            found = next((n for n in _CJK_FONTS if n in names), None)
        except Exception:                        # pragma: no cover
            found = None
        _cjk_font.append(found)
    return _cjk_font[0]


def _zh_figures() -> bool:
    """Whether in-figure text is Chinese: the interface is Chinese and a usable
    Chinese font is installed."""
    return get_lang() == "zh_CN" and _font_for_cjk() is not None


def _lbl(key: str, *args) -> str:
    """Get in-figure text (falls back to the English original when no Chinese
    font is available)."""
    if _zh_figures():
        return t(key, *args)
    return text_qc.english(key, *args)


def _use_lang_font() -> None:
    """Set the in-figure font for the current language: switch to a Chinese font
    in Chinese mode and restore the default font in English mode."""
    try:
        default = matplotlib.rcParamsDefault
        if _zh_figures():
            matplotlib.rcParams["font.family"] = [_font_for_cjk()]
            matplotlib.rcParams["axes.unicode_minus"] = False
        else:
            matplotlib.rcParams["font.family"] = default["font.family"]
            matplotlib.rcParams["axes.unicode_minus"] = \
                default["axes.unicode_minus"]
    except Exception:                            # pragma: no cover
        pass


def _ready() -> bool:
    return plt is not None


def _style(ax):
    ax.grid(True, color=C_GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c9ced6")
    ax.tick_params(colors="#6b7280", labelsize=8)


def _to_image(fig):
    from PIL import Image
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())
    img = Image.fromarray(buf[:, :, :3].copy())
    plt.close(fig)
    return img


# ---------------------------------------------------------------------
# Single subject: head motion over time
# ---------------------------------------------------------------------
def motion_timecourse(subject_dir: str, subject: str = "",
                      thresholds=None, figsize=(9.2, 4.6), dpi=110):
    """Plot the motion time course of one subject.

    Top panel: absolute motion (relative to volume 1), with warn/fail threshold
    lines
    Bottom panel: relative motion (relative to the previous volume), with
    threshold lines
    Both panels mark the volumes judged to be outliers for this subject with
    vertical bands.
    """
    if not _ready():
        raise RuntimeError(t("qcx.plot.need_mpl"))
    _use_lang_font()

    from .qc import load_thresholds
    T = thresholds or load_thresholds()

    st = rescan.read_motion(subject_dir, subject)
    if not st.ok:
        raise RuntimeError(t("qcx.plot.no_motion"))

    x = np.arange(1, st.n_vol + 1)
    a = np.array(st.abs_series, float)
    r = np.array(st.rel_series, float)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=figsize, dpi=dpi, sharex=True,
        gridspec_kw={"height_ratios": [1.15, 1.0], "hspace": 0.18},
        constrained_layout=True)

    # ---- Top: absolute motion ----
    ax1.plot(x, a, color=C_ABS, lw=1.6, marker="o", ms=3.2, zorder=3)
    ax1.fill_between(x, 0, a, color=C_ABS, alpha=0.10, zorder=1)
    ax1.axhline(T.rms_abs_warn, color=C_WARN, ls="--", lw=1.1, zorder=2,
                label=_lbl("qcx.plot.legend_warn", T.rms_abs_warn))
    ax1.axhline(T.rms_abs_fail, color=C_FAIL, ls="--", lw=1.1, zorder=2,
                label=_lbl("qcx.plot.legend_fail", T.rms_abs_fail))
    ax1.set_ylabel(_lbl("qcx.plot.abs_ylabel"), fontsize=9, color=C_TEXT)
    title = _lbl("qcx.plot.motion_title", subject or st.subject, st.n_vol)
    if st.outliers:
        vols = sorted({v for v, _ in st.outliers})
        shown = ", ".join(map(str, vols[:12])) + ("…" if len(vols) > 12 else "")
        title += _lbl("qcx.plot.outlier_vols", shown)
    ax1.set_title(title, fontsize=10.5, color=C_TEXT, loc="left", pad=8)
    # Leave headroom at the top so annotations do not overlap the data or the
    # threshold lines
    top1 = max(T.rms_abs_fail * 1.30, float(a.max()) * 1.30, 0.1)
    ax1.set_ylim(0, top1)
    ax1.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2,
               handlelength=1.6, columnspacing=1.2)
    ax1.text(0.995, 0.965, _lbl("qcx.plot.mean_max", st.abs_mean, st.abs_max),
             transform=ax1.transAxes, ha="right", va="top",
             fontsize=8, color=C_ABS)
    _style(ax1)

    # ---- Bottom: relative motion ----
    ax2.bar(x, r, color=C_REL, width=0.72, alpha=0.85, zorder=3)
    ax2.axhline(T.rms_rel_warn, color=C_WARN, ls="--", lw=1.1, zorder=4,
                label=_lbl("qcx.plot.legend_warn", T.rms_rel_warn))
    ax2.axhline(T.rms_rel_max_warn, color=C_WARN, ls=":", lw=1.0, zorder=4,
                label=_lbl("qcx.plot.legend_warn_max", T.rms_rel_max_warn))
    ax2.set_ylabel(_lbl("qcx.plot.rel_ylabel"), fontsize=9, color=C_TEXT)
    ax2.set_xlabel(_lbl("qcx.plot.xlabel"), fontsize=9, color=C_TEXT)
    top2 = max(T.rms_rel_max_warn * 1.35, float(r.max()) * 1.35, 0.1)
    ax2.set_ylim(0, top2)
    ax2.legend(loc="upper left", fontsize=7.5, frameon=False, ncol=2,
               handlelength=1.6, columnspacing=1.2)
    ax2.text(0.995, 0.965, _lbl("qcx.plot.mean_max", st.rel_mean, st.rel_max),
             transform=ax2.transAxes, ha="right", va="top",
             fontsize=8, color=C_REL)
    _style(ax2)

    # ---- Mark the outlier volumes ----
    if st.outliers:
        vols = sorted({v for v, _ in st.outliers})
        for ax in (ax1, ax2):
            for v in vols:
                ax.axvspan(v - 0.45, v + 0.45, color=C_OUT, alpha=0.13, zorder=0)

    ax2.set_xlim(0.4, st.n_vol + 0.6)
    if st.n_vol <= 30:
        ax2.set_xticks(x)
        ax2.tick_params(axis="x", labelsize=7)

    return _to_image(fig)


# ---------------------------------------------------------------------
# Single subject: registration/ROI overview (for the HTML report)
# ---------------------------------------------------------------------
ROI_OVERVIEW_FILES = {
    "L_proj": "L_SCR.nii.gz",
    "R_proj": "R_SCR.nii.gz",
    "L_asso": "L_SLF.nii.gz",
    "R_asso": "R_SLF.nii.gz",
}
ROI_OVERVIEW_COLORS = {
    "L_proj": (229, 72, 77),
    "R_proj": (247, 104, 8),
    "L_asso": (13, 116, 206),
    "R_asso": (13, 157, 140),
}


def registration_overview(subject_dir: str, subject: str = "",
                          figsize=(9.6, 3.2), dpi=120):
    """Show registered FA in template space with the four ROI masks.

    This is a visual QC figure: it lets the reader inspect whether the
    FA->template registration and the ROI placement look plausible, instead of
    relying only on r_wm.  It needs the pipeline output ``FA_in_mni.nii.gz``;
    the ROI masks are the same bundled masks used for the ALPS calculation.

    Returns a PIL.Image.  Caller is responsible for embedding/saving it.
    """
    if not _ready():
        raise RuntimeError(t("qcx.plot.need_mpl"))
    try:
        import nibabel as nib
    except Exception:                                # pragma: no cover
        raise RuntimeError(t("qcx.roi.need_nibabel"))
    from .roi import package_roi_dir

    fa_path = os.path.join(subject_dir, "FA_in_mni.nii.gz")
    if not os.path.isfile(fa_path):
        raise RuntimeError(t("qcx.plot.no_fa"))
    fa_img = nib.load(fa_path)
    fa = np.squeeze(np.asanyarray(fa_img.dataobj)).astype(np.float32)
    if fa.ndim != 3:
        raise RuntimeError(t("qcx.plot.reg_shape"))

    masks = {}
    for name, fn in ROI_OVERVIEW_FILES.items():
        p = os.path.join(package_roi_dir(), fn)
        if not os.path.isfile(p):
            raise RuntimeError(t("qcx.plot.roi_missing_s", fn))
        masks[name] = np.asanyarray(nib.load(p).dataobj) > 0.5
    if any(m.shape != fa.shape for m in masks.values()):
        raise RuntimeError(t("qcx.plot.reg_shape"))

    allm = np.zeros(fa.shape, bool)
    for m in masks.values():
        allm |= m
    idx = np.argwhere(allm)
    if idx.size == 0:
        raise RuntimeError(t("qcx.plot.reg_shape"))

    # A common square field of view (in mm) for the three views, so the ROI
    # positions are directly comparable instead of filling each panel.
    vox = np.sqrt((fa_img.affine[:3, :3] ** 2).sum(axis=0))
    center = (idx.min(axis=0) + idx.max(axis=0)) / 2.0
    span_mm = float(np.max((idx.max(axis=0) - idx.min(axis=0) + 1) * vox))
    side_mm = span_mm + 28.0
    half = np.maximum(4, (side_mm / 2.0 / np.maximum(vox, 1e-6)).astype(int))
    lo = np.maximum(0, np.floor(center).astype(int) - half)
    hi = np.minimum(np.array(fa.shape) - 1, np.floor(center).astype(int) + half)
    z = int(np.argmax(allm.sum(axis=(0, 1))))
    y = int(np.argmax(allm.sum(axis=(0, 2))))
    x = int(np.argmax(allm.sum(axis=(1, 2))))

    panels = [
        (_lbl("qcx.plot.reg_axial"),
         fa[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, z].T,
         {k: m[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, z].T
          for k, m in masks.items()}),
        (_lbl("qcx.plot.reg_coronal"),
         fa[lo[0]:hi[0] + 1, y, lo[2]:hi[2] + 1].T,
         {k: m[lo[0]:hi[0] + 1, y, lo[2]:hi[2] + 1].T
          for k, m in masks.items()}),
        (_lbl("qcx.plot.reg_sagittal"),
         fa[x, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1].T,
         {k: m[x, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1].T
          for k, m in masks.items()}),
    ]

    _use_lang_font()
    fig, axes = plt.subplots(1, 3, figsize=figsize, dpi=dpi,
                             constrained_layout=True)
    vmax = 1.0
    pos = fa[fa > 0]
    if pos.size:
        vmax = max(float(np.percentile(pos, 98)), 1e-6)

    for ax, (title, img, roi_slices) in zip(axes, panels):
        ax.imshow(img, cmap="gray", vmin=0, vmax=vmax, origin="lower",
                  interpolation="nearest")
        overlay = np.zeros(img.shape + (4,), np.float32)
        for name, rr in roi_slices.items():
            c = np.array(ROI_OVERVIEW_COLORS[name], np.float32) / 255.0
            overlay[rr, :3] = c
            overlay[rr, 3] = 0.45
        ax.imshow(overlay, origin="lower", interpolation="nearest")
        # ROI outlines improve visibility on the FA background
        union = np.zeros(img.shape, bool)
        for rr in roi_slices.values():
            union |= rr
        if union.any():
            try:
                ax.contour(union.astype(float), levels=[0.5],
                           colors="#ffffff", linewidths=0.45)
            except Exception:
                pass
        ax.set_title(title, fontsize=9.5, color=C_TEXT, pad=4)
        ax.set_xticks([])
        ax.set_yticks([])
    subj = subject or os.path.basename(os.path.normpath(subject_dir))
    fig.suptitle(_lbl("qcx.plot.reg_title", subj), fontsize=10.5,
                 color=C_TEXT, x=0.01, ha="left")
    return _to_image(fig)


# ---------------------------------------------------------------------
# Cross-subject scatter
# ---------------------------------------------------------------------
# Keys are the field names in the record (a data contract, not translated);
# values are the display names of the axes. LangDict translates on lookup and
# follows the in-figure font fallback rule.
SCATTER_VARS = LangDict({
    "alps_mean": "qcx.plot.var_alps_mean",
    "alps_L": "qcx.plot.var_alps_L",
    "alps_R": "qcx.plot.var_alps_R",
    "r_wm": "qcx.plot.var_r_wm",
    "rms_abs_mean": "qcx.plot.var_abs_mean",
    "rms_abs_max": "qcx.plot.var_abs_max",
    "rms_rel_mean": "qcx.plot.var_rel_mean",
    "rms_rel_max": "qcx.plot.var_rel_max",
    "n_outlier": "qcx.plot.var_outlier",
    "n_vol": "qcx.plot.var_vol",
    "seconds": "qcx.plot.var_seconds",
}, tr=_lbl)


def _num(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
        return None if (f != f) else f
    except (TypeError, ValueError):
        return None


def _get(rec: dict, key: str):
    """Look up values tolerantly with respect to letter case.

    Session records use lower case (alps_L), whereas the shell summary table uses
    upper case (ALPS_L); both are handled here so that neither side needs a
    special case.
    """
    for k in (key, key.upper(), key.lower()):
        if k in rec:
            return rec[k]
    # Case-insensitive match, field by field
    low = key.lower()
    for k, v in rec.items():
        if str(k).lower() == low:
            return v
    return None


def _subject_of(rec: dict) -> str:
    for k in ("subject", "id", "Subject", "ID"):
        v = rec.get(k)
        if v not in (None, ""):
            return str(v)
    return ""


def _group_of(name: str) -> str:
    """Compatibility with older callers: equivalent to grouping by ID prefix."""
    return subject_prefix(name)


# ---------------------------------------------------------------------
# Grouping: no cohort structure is assumed
# ---------------------------------------------------------------------
# Grouping modes: keys are internal mode names (the group_of argument, not
# translated), values are the text shown in the interface.
GROUP_MODES = LangDict({
    "auto": "qcx.plot.group_auto",
    "column": "qcx.plot.group_column",
    "none": "qcx.plot.group_none",
})

# Generic palette, cycled in group order; not tied to any specific study
PALETTE = ["#2563eb", "#f76808", "#0d9d8c", "#7c3aed", "#cf222e",
           "#9a6700", "#0ea5e9", "#db2777", "#65a30d", "#64748b"]


def subject_prefix(name: str) -> str:
    """Take the first segment of the ID as the group name.

    demoA_01 -> demoA, sub-01 -> sub, S001 -> S001.
    This works for any naming convention, with no need to know in advance which
    groups exist in the cohort.
    """
    name = str(name or "").strip()
    if not name:
        return ""
    for sep in ("_", "-", "."):
        if sep in name:
            head = name.split(sep)[0]
            if head:
                return head
    return name


def group_of(rec: dict, mode: str = "auto") -> str:
    """Return the group label for the requested mode; an empty string means no
    grouping."""
    if mode == "none":
        return ""
    if mode == "column":
        for k in ("group", "Group", "GROUP", "cohort", "Cohort"):
            v = rec.get(k)
            if v not in (None, ""):
                return str(v)
        # Without a group column, fall back to the prefix instead of raising
        return subject_prefix(_subject_of(rec))
    return subject_prefix(_subject_of(rec))


def qc_scatter(records: List[dict], x_key: str = "rms_rel_mean",
               y_key: str = "alps_mean", figsize=(7.4, 5.2), dpi=110,
               label_points: bool = False, group_mode: str = "auto"):
    """Cross-subject scatter: relation between two QC or result variables.

    group_mode : 'auto' by ID prefix / 'column' use the group column / 'none'
    no grouping
    """
    if not _ready():
        raise RuntimeError(t("qcx.plot.need_mpl"))
    _use_lang_font()

    pts = []
    for rec in records:
        xv, yv = _num(_get(rec, x_key)), _num(_get(rec, y_key))
        if xv is None or yv is None:
            continue
        sid = _subject_of(rec)
        pts.append((xv, yv, sid, group_of(rec, group_mode)))
    if not pts:
        raise RuntimeError(t("qcx.plot.no_points"))

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, constrained_layout=True)
    groups = sorted({p[3] for p in pts})
    for gi, g in enumerate(groups):
        sub = [p for p in pts if p[3] == g]
        col = PALETTE[gi % len(PALETTE)]
        label = (_lbl("qcx.plot.group_all", len(sub)) if not g
                 else _lbl("qcx.plot.group_n", g, len(sub)))
        ax.scatter([p[0] for p in sub], [p[1] for p in sub],
                   s=38, color=col,
                   edgecolors="white", linewidths=0.7, alpha=0.9,
                   label=label, zorder=3)

    # Correlation coefficient
    xs = np.array([p[0] for p in pts], float)
    ys = np.array([p[1] for p in pts], float)
    try:
        rr = float(np.corrcoef(xs, ys)[0, 1])
        n = len(xs)
        # p-value of the t test, avoiding a scipy dependency
        if abs(rr) < 1.0 and n > 2:
            t = rr * np.sqrt((n - 2) / (1 - rr * rr))
            p = _t_p(t, n - 2)
        else:
            p = 0.0
        ax.text(0.02, 0.98,
                "r = %.3f   p = %.3f   n = %d" % (rr, p, n),
                transform=ax.transAxes, va="top", ha="left",
                fontsize=8.5, color=C_TEXT)
        # Least-squares fit line
        if abs(rr) > 0.05:
            k, b = np.polyfit(xs, ys, 1)
            xr = np.linspace(xs.min(), xs.max(), 50)
            ax.plot(xr, k * xr + b, color="#9aa1ab", lw=1.0, ls="--", zorder=2)
    except Exception:
        pass

    if label_points:
        for xv, yv, sid, _ in pts:
            ax.annotate(sid, (xv, yv), fontsize=6.2, color="#6b7280",
                        xytext=(3, 3), textcoords="offset points")

    ax.set_xlabel(SCATTER_VARS.get(x_key, x_key), fontsize=9.5, color=C_TEXT)
    ax.set_ylabel(SCATTER_VARS.get(y_key, y_key), fontsize=9.5, color=C_TEXT)
    ax.set_title(_lbl("qcx.plot.scatter_title"), fontsize=10.5,
                 color=C_TEXT, loc="left", pad=8)
    ax.legend(fontsize=7.5, frameon=False, loc="best")
    _style(ax)
    return _to_image(fig)


def _t_p(t: float, df: int) -> float:
    """Two-sided t-test p-value (no scipy dependency; continued fraction of the
    incomplete beta function)."""
    import math
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    return _betai(df / 2.0, 0.5, x)


def _betai(a: float, b: float, x: float) -> float:
    import math
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return math.exp(lbeta) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta) * _betacf(b, a, 1 - x) / b


def _betacf(a: float, b: float, x: float) -> float:
    import math
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


# ---------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------
def save_image(img, path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path, dpi=(110, 110))
    return path

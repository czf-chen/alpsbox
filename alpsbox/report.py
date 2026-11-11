# -*- coding: utf-8 -*-
"""Automatic interpretation and one-click HTML reports.

Design goals:
  - alps.sh only outputs a CSV, so a user who is handed ALPS = 1.55 has no idea
    what it means;
  - this module combines "result + QC + reference range" into one plain-language
    conclusion, and generates a single-file HTML report that can be e-mailed or
    printed to PDF directly.

Basis of the reference values:
  - Only published data are used: Taoka 2017 (the original paper), cognitively
    normal controls, ALPS = 1.35 +/- 0.20.
  - A wider plausible range is also given (see below); it is only used to point
    out clearly abnormal values.
  No diagnostic claim is made - ALPS currently has no accepted diagnostic
  threshold. Cohort data held inside this tool are not used as a reference
  either, since external users cannot obtain them.

Note on citation conventions: ALPS has no official standard implementation. The
"References" block of the HTML report lists the ALPS method (Taoka 2017), tensor
reorientation (Alexander 2001 / Tatekawa 2023), and the software citation for
what this repository calls the "reference implementation" (gbarisano/alps, MIT
License) together with its companion paper (Liu & Barisano 2024). All sources
are defined in alpsbox/citations.py.
"""
from __future__ import annotations

import base64
import contextlib
import datetime
import io
import json
import math
import os

from . import citations as _C
from . import i18n
from . import text_report  # noqa: F401  registers the rpt.* strings
from .i18n import t

# For display: Chinese verdict values stored in result records -> i18n keys
# (the data itself is not modified)
_QC_VALUE_KEYS = {
    # Chinese (historical data / current data values)
    "通过": "qc.pass", "提示": "qc.info", "需注意": "qc.warn",
    "不合格": "qc.fail",
    # English (values written into new records under the English UI)
    "pass": "qc.pass", "ok": "qc.pass",
    "info": "qc.info",
    "check": "qc.warn", "warn": "qc.warn",
    "fail": "qc.fail", "failed": "qc.fail",
}

# Chinese captions used by cli.py when collecting images -> string keys
_CAPTION_KEYS = {"ROI 位置": "rpt.caption.roi", "头动曲线": "rpt.caption.motion"}


@contextlib.contextmanager
def _lang_ctx(lang):
    """Explicit language context: lang=None means follow i18n.get_lang()."""
    if lang is None or lang == i18n.get_lang() or lang not in i18n.LANGS:
        yield
        return
    prev = i18n.get_lang()
    i18n.set_lang(lang, save=False)
    try:
        yield
    finally:
        i18n.set_lang(prev, save=False)


def _disp(value, default="—"):
    """Replace the Chinese verdict value in a record with the display text of the
    current language (the data itself is not modified)."""
    s = default if value is None or value == "" else str(value)
    key = _QC_VALUE_KEYS.get(s) or _QC_VALUE_KEYS.get(s.lower())
    return t(key) if key else s


# Reference distribution from the literature (mean, SD, source)
# Used only to compare this subject with published data; not a diagnostic or
# normality criterion.
REF_TAOKA = (1.35, 0.20, "Taoka 2017, 认知正常对照")

# Wide range used for interpretation: there is no accepted diagnostic
# threshold, so this only reports whether the value falls in the usual range
PLAUSIBLE_LO, PLAUSIBLE_HI = 1.00, 2.10

# ----------------------------------------------------------- references
# The sources are all provided by citations.py; it does not cover the two
# tensor-reorientation papers or the English note on the ROI masks, so they are
# added here (the Chinese report uses citations.CITATION_ROI_MASKS verbatim).
_TATEKAWA_REF = (
    "Tatekawa H, Matsushita S, Ueda D, Takita H, Horiuchi D, Atsukawa N, "
    "Morishita Y, Tsukamoto T, Shimono T, Miki Y. Improved reproducibility "
    "of diffusion tensor image analysis along the perivascular space "
    "(DTI-ALPS) index: an analysis of reorientation technique of the "
    "OASIS-3 dataset. Jpn J Radiol. 2023;41(4):393-400. "
    "doi:10.1007/s11604-022-01370-2"
)

_ALEXANDER_REF = (
    "Alexander DC, Pierpaoli C, Basser PJ, Gee JC. Spatial transformations "
    "of diffusion tensor magnetic resonance images. IEEE Trans Med Imaging. "
    "2001;20(11):1131-1139. doi:10.1109/42.963816"
)

_CITATION_ROI_MASKS_EN = (
    "Bundled ROI masks reproduced from the " + _C.ROI_SOURCE_DIR + "/ directory "
    "of the reference implementation (Barisano G. alps, GitHub, " + _C.REPO_URL
    + ", commit " + _C.REPO_COMMIT + "; " + _C.ACCESS_DATE + "). "
    + _C.MIT_NOTE + ". 2.5 mm radius spheres (5 mm diameter), consistent with "
    "Taoka 2017; this default was set by the reference implementation's "
    "2025-05-28 update notice, 81 voxels per ROI. License text: "
    "LICENSE_Barisano_alps.txt."
)


def _reference_list(lang: str) -> list:
    """Entries for the references section of the report (one paragraph each:
    method -> reorientation -> software -> paper -> masks)."""
    roi = _C.CITATION_ROI_MASKS if lang == "zh_CN" else _CITATION_ROI_MASKS_EN
    return [_C.CITATION_ALPS_METHOD, _TATEKAWA_REF, _ALEXANDER_REF,
            _C.CITATION_REF_SOFTWARE, _C.CITATION_REF_PAPER, roi]


def _num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


def zscore(v, ref):
    m, s, _ = ref
    return (v - m) / s if s else float("nan")


_QC_LEVEL_ALIASES = {
    "ok": "ok", "pass": "ok", "通过": "ok",
    "info": "info", "提示": "info",
    "warn": "warn", "check": "warn", "caution": "warn", "需注意": "warn",
    "fail": "fail", "failed": "fail", "不合格": "fail",
}


def _level_of(text: str) -> str:
    """Normalise the human-readable QC/regqc label in a record (English or
    Chinese) to ok/info/warn/fail."""
    return _QC_LEVEL_ALIASES.get(str(text or "").strip().lower(), "")


def interpret(rec: dict, lang: str | None = None) -> dict:
    """Turn one record into a plain-language conclusion.

    Returns {verdict, level, lines[str], refs}.
    level: ok / info / warn / fail
    lang=None follows i18n.get_lang() ("en" / "zh_CN").
    """
    with _lang_ctx(lang):
        return _interpret(rec)


def _interpret(rec: dict) -> dict:
    v = _num(rec.get("alps_mean"))
    qc = str(rec.get("qc", "") or "")
    lines = []
    refs = {"taoka": REF_TAOKA[:2] + (t("rpt.ref.taoka"),)}

    if v is None:
        return {"verdict": t("rpt.verdict.noalps"), "level": "fail",
                "lines": [t("rpt.line.noalps")],
                "refs": refs}

    # --- Numeric interpretation (no diagnosis, only where the value lies) ---
    z_t = zscore(v, REF_TAOKA)
    in_plausible = PLAUSIBLE_LO <= v <= PLAUSIBLE_HI

    lines.append(t("rpt.line.alps_index") % v)
    lines.append("")
    lines.append(t("rpt.line.compare_head"))
    lines.append(t("rpt.line.ref_taoka") % (z_t, z_t))
    if in_plausible:
        lines.append(t("rpt.line.plausible") % (PLAUSIBLE_LO, PLAUSIBLE_HI))
    else:
        lines.append(t("rpt.line.implausible") % (PLAUSIBLE_LO, PLAUSIBLE_HI))

    # --- Left-right asymmetry ---
    L = _num(rec.get("alps_L"))
    R = _num(rec.get("alps_R"))
    if L and R:
        asym = abs(L - R) / max(L, R) * 100
        lines.append("")
        lines.append(t("rpt.line.asym") % (L, R, asym))
        if asym > 15:
            lines.append(t("rpt.line.asym_large"))

    # --- QC highlights ---
    lines.append("")
    lines.append(t("rpt.line.qc_head"))
    rwm = _num(rec.get("r_wm"))
    if rwm is not None:
        if rwm >= 0.95:
            lines.append(t("rpt.line.rwm_good") % rwm)
        elif rwm >= 0.90:
            lines.append(t("rpt.line.rwm_ok") % rwm)
        else:
            lines.append(t("rpt.line.rwm_bad") % rwm)

    rel = _num(rec.get("rms_rel_mean"))
    if rel is not None:
        if rel < 0.25:
            lines.append(t("rpt.line.motion_low") % rel)
        elif rel < 0.50:
            lines.append(t("rpt.line.motion_mid") % rel)
        else:
            lines.append(t("rpt.line.motion_high") % rel)

    nout = _num(rec.get("n_outlier"))
    nvol = _num(rec.get("n_vol"))
    if nout is not None and nvol:
        pct = 100.0 * nout / nvol
        if pct <= 10:
            lines.append(t("rpt.line.outlier_ok") % (nout, nvol, pct))
        else:
            lines.append(t("rpt.line.outlier_high") % (nout, nvol, pct))

    method = str(rec.get("method", ""))
    if method and "correct" in method:
        lines.append(t("rpt.line.eddy_correct"))

    # Registration robustness (only with --regqc)
    rq = _num(rec.get("regqc_range_pct"))
    if rq is not None:
        lvl = _level_of(rec.get("regqc_level", ""))
        if lvl == "ok":
            lines.append(t("rpt.line.regqc_pass") % rq)
        elif lvl == "info":
            lines.append(t("rpt.line.regqc_info") % rq)
        else:
            lines.append(t("rpt.line.regqc_warn") % rq)

    if qc:
        lines.append(t("rpt.line.qc_value") % _disp(qc))

    # --- Overall verdict ---
    qc_level = _level_of(qc)
    level = "ok"
    if qc_level == "fail" or not in_plausible:
        level = "fail"
    elif qc_level == "warn":
        level = "warn"
    elif qc_level == "info":
        level = "info"

    verdict_map = {
        "ok": "rpt.verdict.ok",
        "info": "rpt.verdict.info",
        "warn": "rpt.verdict.warn",
        "fail": "rpt.verdict.fail",
    }
    return {"verdict": t(verdict_map[level]), "level": level,
            "lines": lines, "refs": refs, "value": v}


# ---------------------------------------------------------------- HTML
_CSS = """
body{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
     margin:0;padding:28px 34px;color:#222;background:#fff;line-height:1.5}
h1{font-size:22px;margin:0 0 4px;color:#1a56db}
h2{font-size:15px;margin:22px 0 8px;padding-bottom:5px;
   border-bottom:1px solid #e3e7ee;color:#333}
.sub{color:#777;font-size:12px;margin-bottom:18px}
table{border-collapse:collapse;font-size:12.5px;margin:6px 0}
th,td{border:1px solid #e3e7ee;padding:5px 10px;text-align:left}
th{background:#f6f8fb;font-weight:600}
.val{font-family:Consolas,monospace}
.badge{display:inline-block;padding:3px 10px;border-radius:11px;
       font-size:12px;font-weight:600}
.ok{background:#e6f6ec;color:#186b35}
.info{background:#e8f1fe;color:#1a4f9c}
.warn{background:#fff5e5;color:#8a5300}
.fail{background:#fdeaea;color:#9b1c1c}
.verdict{font-size:16px;margin:10px 0 4px}
pre{background:#f6f8fb;border:1px solid #e3e7ee;padding:10px 12px;
    border-radius:6px;font-size:12px;white-space:pre-wrap;line-height:1.55}
.note{font-size:11.5px;color:#888;margin-top:6px}
ol.refs{margin:6px 0 4px 18px;padding:0;font-size:12px;line-height:1.65}
ol.refs li{margin:0 0 9px 0;padding-left:4px}
img{max-width:100%;border:1px solid #e3e7ee;border-radius:5px;margin-top:6px}
"""


def _img_tag(path, max_w=None):
    if not path or not os.path.isfile(path):
        return ""
    try:
        b = open(path, "rb").read()
        b64 = base64.b64encode(b).decode()
        style = ' style="max-width:%dpx"' % max_w if max_w else ""
        return '<img src="data:image/png;base64,%s"%s>' % (b64, style)
    except Exception:
        return ""


def build_html(rec: dict, out_path: str, images: dict | None = None,
               title: str | None = None, lang: str | None = None) -> str:
    """Generate the single-file HTML report (printable to PDF from a browser).

    title=None uses the default title of the current language; lang=None follows
    i18n.get_lang().
    """
    with _lang_ctx(lang):
        return _build_html(rec, out_path, images, title)


def _build_html(rec: dict, out_path: str, images: dict | None = None,
                title: str | None = None) -> str:
    images = images or {}
    title = title or t("rpt.title.single")
    it = interpret(rec)
    v = _num(rec.get("alps_mean"))
    L = _num(rec.get("alps_L"))
    R = _num(rec.get("alps_R"))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def f(x, nd=4):
        y = _num(x)
        return "—" if y is None else ("%.*f" % (nd, y))

    rows_main = [
        (t("rpt.row.subject"), rec.get("subject", "—")),
        (t("rpt.row.time"), now),
        (t("rpt.row.method"), rec.get("method", "—")),
        (t("rpt.row.nvol"), str(rec.get("n_vol", "—"))),
        (t("rpt.row.alps_L"), "<span class=val>%s</span>" % f(L, 3)),
        (t("rpt.row.alps_R"), "<span class=val>%s</span>" % f(R, 3)),
        (t("rpt.row.alps_mean"), "<span class=val><b>%s</b></span>" % f(v, 3)),
    ]

    diff_rows = [
        (t("rpt.row.dxx_L_proj"), f(rec.get("dxx_L_proj"), 6)),
        (t("rpt.row.dyy_L_proj"), f(rec.get("dyy_L_proj"), 6)),
        (t("rpt.row.dxx_L_asso"), f(rec.get("dxx_L_asso"), 6)),
        (t("rpt.row.dzz_L_asso"), f(rec.get("dzz_L_asso"), 6)),
        (t("rpt.row.dxx_R_proj"), f(rec.get("dxx_R_proj"), 6)),
        (t("rpt.row.dyy_R_proj"), f(rec.get("dyy_R_proj"), 6)),
        (t("rpt.row.dxx_R_asso"), f(rec.get("dxx_R_asso"), 6)),
        (t("rpt.row.dzz_R_asso"), f(rec.get("dzz_R_asso"), 6)),
    ]

    qc_rows = [
        (t("rpt.qc.rwm"), f(rec.get("r_wm"), 3)),
        (t("rpt.qc.rel_mean"), f(rec.get("rms_rel_mean"), 3)),
        (t("rpt.qc.rel_max"), f(rec.get("rms_rel_max"), 3)),
        (t("rpt.qc.abs_mean"), f(rec.get("rms_abs_mean"), 3)),
        (t("rpt.qc.abs_max"), f(rec.get("rms_abs_max"), 3)),
        (t("rpt.qc.outlier_n"), str(rec.get("n_outlier", "—"))),
        (t("rpt.qc.verdict"), _disp(rec.get("qc", "—"))),
    ]

    # Registration robustness (--regqc)
    if _num(rec.get("regqc_range_pct")) is not None:
        qc_rows.extend([
            (t("rpt.qc.regqc_range"), f(rec.get("regqc_range_pct"), 2)),
            (t("rpt.qc.regqc_maxdev"), f(rec.get("regqc_max_dev_pct"), 2)),
            (t("rpt.qc.regqc_level"),
             _disp(str(rec.get("regqc_level", "—") or "—"))),
        ])

    # T1-assisted registration (only with --t1; an experimental paired
    # comparison that does not affect the main result)
    if str(rec.get("t1_assisted", "") or "") == "ok":
        qc_rows.extend([
            (t("rpt.qc.t1_alps"), f(rec.get("alps_t1"), 3)),
            (t("rpt.qc.t1_rwm"), f(rec.get("r_wm_t1"), 3)),
            (t("rpt.qc.t1_regqc_range"), f(rec.get("regqc_t1_range_pct"), 2)),
        ])

    def table(rows, w1="38%"):
        h = ('<table><tr><th style="width:%s">%s</th><th>%s</th></tr>'
             % (w1, t("rpt.table.item"), t("rpt.table.value")))
        for k, val in rows:
            h += "<tr><td>%s</td><td>%s</td></tr>" % (k, val)
        return h + "</table>"

    level = it["level"]
    body = []
    body.append("<h1>%s</h1>" % title)
    body.append('<div class="sub">%s</div>' % t("rpt.sub.generated", now))
    body.append('<div class="verdict"><span class="badge %s">%s</span> '
                '&nbsp;%s</div>'
                % (level, _disp(rec.get("qc", "—")), it["verdict"]))

    body.append("<h2>%s</h2>" % t("rpt.h.results"))
    body.append(table(rows_main))

    body.append("<h2>%s</h2>" % t("rpt.h.verdict"))
    body.append("<pre>%s</pre>" % "\n".join(it["lines"]))
    body.append('<div class="note">%s</div>' % t("rpt.note.no_threshold"))

    body.append("<h2>%s</h2>" % t("rpt.h.diffusivity"))
    body.append(table([(a, "<span class=val>%s</span>"
                        % (("—" if b == "—" else "%.4f" % (float(b) * 1000))))
                       for a, b in diff_rows]))

    body.append("<h2>%s</h2>" % t("rpt.h.qc"))
    body.append(table(qc_rows))

    if images:
        body.append("<h2>%s</h2>" % t("rpt.h.images"))
        for cap, p in images.items():
            tag = _img_tag(p, max_w=760)
            if tag:
                ckey = _CAPTION_KEYS.get(cap)
                body.append("<div style='margin:10px 0'><b>%s</b>%s</div>"
                            % (t(ckey) if ckey else cap, tag))

    # ---- Processing settings (read from the result record, tolerant of old
    # results; defaults are used when a field is missing) ----
    def _g(key, default="—"):
        v = rec.get(key)
        if v is None or v == "":
            return default
        return v

    def _fmt_num(v):
        try:
            return "%.2f" % float(v)
        except Exception:
            return str(v)

    bet_f = _fmt_num(_g("bet_f", "0.50"))
    reg_cost = _g("reg_cost", "normmi")
    unring = _g("unring", "on")
    denoise = _g("denoise", "off")
    template = _g("template") or "JHU-ICBM-FA-1mm"

    body.append('<h2>%s</h2>' % t("rpt.h.method"))
    body.append("<pre>%s</pre>" % t("rpt.method.block", template, reg_cost,
                                    unring, denoise, bet_f))
    body.append('<div class="note">%s</div>' % t("rpt.note.method"))

    # ---- 7. References (one item each, so they do not merge into a single
    # block; sources in citations.py) ----
    body.append("<h2>%s</h2>" % t("rpt.h.refs"))
    _refs = _reference_list(i18n.get_lang())
    body.append('<ol class="refs">%s</ol>'
                % "".join("<li>%s</li>" % r for r in _refs))
    body.append('<div class="note">%s</div>' % t("rpt.note.term"))

    lang_attr = "en" if i18n.get_lang() == "en" else "zh-CN"
    html = ('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">'
            "<title>%s</title><style>%s</style></head><body>%s</body></html>"
            % (lang_attr, title, _CSS, "\n".join(body)))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path


def build_from_result_json(json_path: str, out_html: str | None = None,
                           images: dict | None = None,
                           lang: str | None = None) -> str:
    """Build the report directly from alps_result.json (lang=None follows
    i18n.get_lang())."""
    rec = json.load(open(json_path, encoding="utf-8"))
    if out_html is None:
        out_html = os.path.join(os.path.dirname(json_path),
                                "%s_report.html" % rec.get("subject", "alps"))
    return build_html(rec, out_html, images=images, lang=lang)


def build_batch_html(results: list, out_path: str, title: str | None = None,
                     lang: str | None = None) -> str:
    """Summary HTML for several subjects analysed at once (counts and a
    per-subject table only).

    This tool only computes single-subject ALPS plus QC; group-level statistics
    are a downstream task, so the report gives no mean/SD/range of ALPS.
    """
    with _lang_ctx(lang):
        return _build_batch_html(results, out_path, title)


def _build_batch_html(results: list, out_path: str,
                      title: str | None = None) -> str:
    title = title or t("rpt.title.batch")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = []
    n_ok = 0
    for r in results:
        if not r.get("ok"):
            rows.append((r.get("subject", "?"), t("rpt.batch.failed"),
                         "—", "—", "—", "—"))
            continue
        n_ok += 1
        it = interpret(r)
        rows.append((r.get("subject", "?"), _disp(r.get("qc", "—")),
                     "%.3f" % float(r["alps_L"]),
                     "%.3f" % float(r["alps_R"]),
                     "<b>%.3f</b>" % float(r["alps_mean"]),
                     it["verdict"]))
    tbl = ('<table><tr><th>%s</th><th>%s</th><th>ALPS_L</th>'
           "<th>ALPS_R</th><th>ALPS_mean</th><th>%s</th></tr>"
           % (t("rpt.batch.th_subject"), t("rpt.batch.th_qc"),
              t("rpt.batch.th_conclusion")))
    for row in rows:
        tbl += "<tr>" + "".join("<td>%s</td>" % c for c in row) + "</tr>"
    tbl += "</table>"
    # Keep only the subject and success counts; group-level statistics should
    # be done downstream on the exported CSV/JSON
    count = "<pre>%s</pre>" % t("rpt.batch.count", len(results), n_ok)
    lang_attr = "en" if i18n.get_lang() == "en" else "zh-CN"
    html = ('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8">'
            "<title>%s</title><style>%s</style></head><body>"
            "<h1>%s</h1><div class='sub'>ALPSbox · %s</div>"
            "<h2>%s</h2>%s<h2>%s</h2>%s</body></html>"
            % (lang_attr, title, _CSS, title, now, t("rpt.h.summary"), count,
               t("rpt.h.per_subject"), tbl))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path

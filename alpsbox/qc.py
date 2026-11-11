# -*- coding: utf-8 -*-
"""Quality control: turns the metrics collected by the pipeline into a verdict of
pass / info / check / fail and suggests what to do about it.

Design principles
-----------------
* Thresholds live in QCThresholds; they can be edited in the interface and are
  saved to ~/.alpsbox/qc_config.json.
* Four verdict levels: ok (pass), info (note, does not affect use), warn (worth
  a look), fail (not recommended for use).
* QC is a derived result and is not written into session.json, so historical
  results can be re-evaluated after the thresholds are changed.

Terminology and citations: "reference implementation" in the comments (called
"official alps.sh" in older documentation) refers specifically to gbarisano/alps
(GitHub, commit e6f58e7, MIT License); the full citation is in
alpsbox/citations.py. The default thresholds follow methodological common sense
and common practice rather than rules laid down by the reference implementation,
and can be tuned per cohort.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from . import text_qc  # noqa: F401  (registers the qcx.* strings)
from .i18n import t
from .text_qc import LangDict

# ---------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------
@dataclass
class QCThresholds:
    """All adjustable thresholds. Field names are the configuration keys."""

    # The bundled reference ROIs are 2.5 mm radius spheres, deliberately built
    # to contain 81 voxels each. A deviation in voxel count means the template
    # space is inconsistent, or that the user changed a custom sphere radius.
    roi_voxels: int = 81

    # r_wm is the correlation between the registered FA and the JHU template
    # (fslcc). The thresholds are pragmatic defaults chosen from common
    # experience with 1.5 mm / 3T data, not an accepted standard; they can be
    # adjusted per cohort in the interface.
    r_wm_ok: float = 0.80          # >= this value: pass
    r_wm_fail: float = 0.77        # < this value: fail

    # eddy_movement_rms from eddy has two columns with different physical
    # meanings, which must be judged separately:
    #
    #   absolute motion = displacement relative to the first volume; it shows
    #                     how far the scan drifted overall. It accumulates with
    #                     scan duration, so sequences with different numbers of
    #                     volumes are not directly comparable.
    #   relative motion = displacement relative to the previous volume, similar
    #                     to fMRI FD; it does not accumulate with duration, so
    #                     relative motion should be used for comparisons across
    #                     protocols or groups.
    rms_rel_warn: float = 0.25
    rms_rel_fail: float = 0.40
    rms_rel_max_warn: float = 0.80
    rms_rel_max_fail: float = 1.20

    # The absolute-motion thresholds are kept loose because they depend on scan
    # duration and should not be set too tightly.
    rms_abs_warn: float = 1.00
    rms_abs_fail: float = 1.60
    rms_abs_max_warn: float = 2.20
    rms_abs_max_fail: float = 3.20

    # Outlier slice count as a fraction of the volume count. Clean data are
    # around 0.2-0.3 slices per volume.
    outlier_warn: float = 0.50
    outlier_fail: float = 1.00

    # Plausible range for ALPS. Literature values are roughly 1.3-1.7; the
    # bounds here are widened so that valid data are not flagged by mistake.
    alps_min: float = 0.60
    alps_max: float = 2.50

    # Whether using eddy_correct counts as "check" (it does not reorient
    # tensors and has a known bias).
    flag_eddy_correct: bool = True

    # Whether the ROI voxel counts are compared strictly with roi_voxels.
    # Custom spheres with a different radius necessarily differ in voxel count,
    # so this check can be switched off.
    strict_roi_voxels: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "QCThresholds":
        th = cls()
        for k, v in (d or {}).items():
            if not hasattr(th, k):
                continue
            cur = getattr(th, k)
            try:
                if isinstance(cur, bool):
                    setattr(th, k, bool(v))
                elif isinstance(cur, int):
                    setattr(th, k, int(v))
                else:
                    setattr(th, k, float(v))
            except (TypeError, ValueError):
                pass
        return th

    def validate(self) -> List[str]:
        """Check the logical relations between the thresholds and return a list
        of problems."""
        problems = []
        if self.r_wm_fail > self.r_wm_ok:
            problems.append(t("qcx.v.r_wm_order"))
        if self.rms_rel_fail < self.rms_rel_warn:
            problems.append(t("qcx.v.rel_mean"))
        if self.rms_rel_max_fail < self.rms_rel_max_warn:
            problems.append(t("qcx.v.rel_max"))
        if self.rms_abs_fail < self.rms_abs_warn:
            problems.append(t("qcx.v.abs_mean"))
        if self.rms_abs_max_fail < self.rms_abs_max_warn:
            problems.append(t("qcx.v.abs_max"))
        if self.outlier_fail < self.outlier_warn:
            problems.append(t("qcx.v.outlier"))
        if self.alps_min >= self.alps_max:
            problems.append(t("qcx.v.alps_range"))
        if self.roi_voxels <= 0:
            problems.append(t("qcx.v.roi_voxels"))
        for name, v in ((t("qcx.vn.r_wm_ok"), self.r_wm_ok),
                        (t("qcx.vn.r_wm_fail"), self.r_wm_fail),
                        (t("qcx.vn.rel_mean"), self.rms_rel_warn),
                        (t("qcx.vn.abs_mean"), self.rms_abs_warn),
                        (t("qcx.vn.alps_min"), self.alps_min)):
            if v != v:  # NaN
                problems.append(t("qcx.v.nan", name))
        return problems


DEFAULT_THRESHOLDS = QCThresholds()

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".alpsbox")
CONFIG_FILE = os.path.join(CONFIG_DIR, "qc_config.json")

_cached: Optional[QCThresholds] = None


def load_thresholds(reload: bool = False) -> QCThresholds:
    """Load the thresholds saved by the user; fall back to the defaults when no
    configuration file exists."""
    global _cached
    if _cached is not None and not reload:
        return _cached
    th = QCThresholds()
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as fh:
                th = QCThresholds.from_dict(json.load(fh))
    except Exception:
        th = QCThresholds()
    _cached = th
    return th


def save_thresholds(th: QCThresholds) -> bool:
    """Save the thresholds to ~/.alpsbox/qc_config.json."""
    global _cached
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp = CONFIG_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(th.to_dict(), fh, ensure_ascii=False, indent=1)
        os.replace(tmp, CONFIG_FILE)
        _cached = th
        return True
    except Exception:
        return False


def reset_thresholds() -> QCThresholds:
    global _cached
    _cached = QCThresholds()
    try:
        if os.path.isfile(CONFIG_FILE):
            os.remove(CONFIG_FILE)
    except Exception:
        pass
    return _cached


def thresholds_summary(th: Optional[QCThresholds] = None) -> str:
    """One-line threshold summary for the interface (English and Chinese)."""
    th = th or load_thresholds()
    args = (th.r_wm_ok, th.rms_rel_warn, th.rms_rel_max_warn,
            th.rms_abs_warn, th.rms_abs_max_warn)
    if th.strict_roi_voxels:
        return t("qc.th_line", args[0], args[1], args[2], args[3], args[4],
                 th.roi_voxels)
    return t("qc.th_line_noroi", *args)


# ---------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------
LEVELS = ("ok", "info", "warn", "fail")
# Labels for display: they default to the Chinese originals and are translated
# into the current language on lookup (see text_qc.LangDict). The level keys
# ok/info/warn/fail are unchanged.
LEVEL_LABEL = LangDict({
    "ok": "qcx.level.ok",
    "info": "qcx.level.info",
    "warn": "qcx.level.warn",
    "fail": "qcx.level.fail",
})
LEVEL_ORDER = {"ok": 0, "info": 1, "warn": 2, "fail": 3}


def _num(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


@dataclass
class QCCheck:
    key: str
    label: str
    value: str
    level: str
    detail: str = ""
    advice: str = ""


@dataclass
class QCReport:
    subject: str
    level: str = "ok"
    checks: List[QCCheck] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)   # check / fail
    notes: List[str] = field(default_factory=list)    # info only

    @property
    def label(self) -> str:
        return LEVEL_LABEL.get(self.level, self.level)

    def summarize_line(self) -> str:
        if self.issues:
            s = t("qcx.join_semicolon").join(self.issues[:3])
            return s + ("…" if len(self.issues) > 3 else "")
        if self.notes:
            s = t("qcx.join_semicolon").join(self.notes[:2])
            return (t("qcx.note_prefix") + s
                    + ("…" if len(self.notes) > 2 else ""))
        return t("qcx.all_normal")

    # Kept as an alias so external callers keep working
    summary_line = summarize_line


def evaluate(rec: dict, th: Optional[QCThresholds] = None) -> QCReport:
    """Run the QC verdict on a single result record."""
    T = th or load_thresholds()
    subj = str(rec.get("subject", "") or t("qcx.unnamed"))
    r = QCReport(subject=subj)
    issues: List[str] = []

    def worst(level: str):
        if LEVEL_ORDER.get(level, 0) > LEVEL_ORDER.get(r.level, 0):
            r.level = level

    def add(key, label, value, level, detail="", advice=""):
        r.checks.append(QCCheck(key, label, value, level, detail, advice))
        worst(level)

    # ---- 1. Whether processing succeeded ----
    # The status field is data (written by the pipeline/session), not interface
    # wording: here it is only recognised as a success/failure signal. A
    # recognised success is always displayed in the current language, while
    # failure reasons with details are passed through verbatim (the writer
    # decides their language).
    st = str(rec.get("status", "") or "")
    if st:
        ok_run = st.startswith(("成功", "success", "Success", "ok", "OK",
                            "done", "Done"))
    else:
        # Some sources have no status column (e.g. summary tables written by
        # the shell pipeline); infer success from whether result values exist,
        # otherwise the whole batch would be judged as failed.
        ok_run = _num(rec.get("alps_mean")) is not None
    # Only a bare "success" is reworded into the current language; statuses
    # that carry details (e.g. failure reasons) are shown verbatim.
    if ok_run and st in ("", "成功", "success", "Success", "ok", "OK",
                        "done", "Done"):
        st = t("qcx.status_ok")
    elif not st:
        st = t("qcx.status_unknown")
    add("run", t("qcx.chk.run"), st, "ok" if ok_run else "fail",
        t("qcx.d.run"))
    if not ok_run:
        issues.append(t("qcx.i.run_failed"))
        r.issues = issues
        r.level = "fail"
        return r

    # ---- 2. ROI voxel count ----
    keys = ("n_L_proj", "n_R_proj", "n_L_asso", "n_R_asso")
    roi_n = {k: _num(rec.get(k)) for k in keys}
    if any(v is not None for v in roi_n.values()):
        txt = " / ".join(str(int(v)) if v is not None else "-"
                         for v in roi_n.values())
        zeros = [k for k, v in roi_n.items() if v is not None and v <= 0]
        bad = [k for k, v in roi_n.items()
               if v is not None and v != T.roi_voxels]
        if zeros:
            add("roi", t("qcx.chk.roi"), txt, "fail",
                t("qcx.d.roi_empty", T.roi_voxels),
                t("qcx.a.roi_empty"))
            issues.append(t("qcx.i.roi_empty"))
        elif bad and T.strict_roi_voxels:
            add("roi", t("qcx.chk.roi"), txt, "warn",
                t("qcx.d.roi_bad", T.roi_voxels, len(bad)),
                t("qcx.a.roi_bad"))
            issues.append(t("qcx.i.roi_bad"))
        else:
            add("roi", t("qcx.chk.roi"), txt, "ok",
                t("qcx.d.roi_ok", T.roi_voxels)
                if T.strict_roi_voxels else t("qcx.d.roi_skip"))
    else:
        add("roi", t("qcx.chk.roi"), "-", "info", t("qcx.d.roi_missing"))

    # ---- 3. Registration quality ----
    rw = _num(rec.get("r_wm"))
    if rw is None:
        add("r_wm", t("qcx.chk.r_wm"), t("qcx.untested"), "info",
            t("qcx.d.r_wm_missing"))
    elif rw >= T.r_wm_ok:
        add("r_wm", t("qcx.chk.r_wm"), "%.3f" % rw, "ok",
            t("qcx.d.r_wm_ok", rw))
    elif rw >= T.r_wm_fail:
        add("r_wm", t("qcx.chk.r_wm"), "%.3f" % rw, "warn",
            t("qcx.d.r_wm_warn", rw, T.r_wm_ok),
            t("qcx.a.r_wm_warn"))
        issues.append(t("qcx.i.r_wm_warn"))
    else:
        add("r_wm", t("qcx.chk.r_wm"), "%.3f" % rw, "fail",
            t("qcx.d.r_wm_fail", rw, T.r_wm_fail),
            t("qcx.a.r_wm_fail"))
        issues.append(t("qcx.i.r_wm_fail"))

    # ---- 4. Head motion: absolute and relative motion judged separately ----
    a_mean = _num(rec.get("rms_abs_mean"))
    a_max = _num(rec.get("rms_abs_max"))
    r_mean = _num(rec.get("rms_rel_mean"))
    r_max = _num(rec.get("rms_rel_max"))
    # Backwards compatibility with old records (early versions only had
    # rms_mean / rms_max, which were relative motion)
    if r_mean is None:
        r_mean = _num(rec.get("rms_mean"))
    if r_max is None:
        r_max = _num(rec.get("rms_max"))

    if all(v is None for v in (a_mean, a_max, r_mean, r_max)):
        add("motion", t("qcx.chk.motion"), t("qcx.untested"), "info",
            t("qcx.d.motion_missing"))
    else:
        # Relative motion: does not accumulate with scan duration and is
        # comparable across groups, so it serves as the primary criterion
        if r_mean is None and r_max is None:
            add("motion_rel", t("qcx.chk.motion_rel"), t("qcx.untested"),
                "info", t("qcx.d.motion_rel_missing"))
        else:
            txt = "%s / %s mm" % (
                "%.3f" % r_mean if r_mean is not None else "-",
                "%.3f" % r_max if r_max is not None else "-")
            if (r_mean is not None and r_mean >= T.rms_rel_fail) or \
               (r_max is not None and r_max >= T.rms_rel_max_fail):
                add("motion_rel", t("qcx.chk.motion_rel_mm"), txt, "fail",
                    t("qcx.d.motion_rel_fail",
                      T.rms_rel_fail, T.rms_rel_max_fail),
                    t("qcx.a.motion_rel_fail"))
                issues.append(t("qcx.i.jitter_big"))
            elif (r_mean is not None and r_mean >= T.rms_rel_warn) or \
                    (r_max is not None and r_max >= T.rms_rel_max_warn):
                add("motion_rel", t("qcx.chk.motion_rel_mm"), txt, "warn",
                    t("qcx.d.motion_rel_warn",
                      T.rms_rel_warn, T.rms_rel_max_warn),
                    t("qcx.a.motion_rel_warn"))
                issues.append(t("qcx.i.jitter_slight"))
            else:
                add("motion_rel", t("qcx.chk.motion_rel_mm"), txt, "ok",
                    t("qcx.d.motion_rel_ok"))

        # Absolute motion: accumulates with scan duration, used for reference
        # only, hence the loose thresholds
        if a_mean is None and a_max is None:
            add("motion_abs", t("qcx.chk.motion_abs"), t("qcx.untested"),
                "info", t("qcx.d.motion_abs_missing"))
        else:
            txt = "%s / %s mm" % (
                "%.3f" % a_mean if a_mean is not None else "-",
                "%.3f" % a_max if a_max is not None else "-")
            if (a_mean is not None and a_mean >= T.rms_abs_fail) or \
               (a_max is not None and a_max >= T.rms_abs_max_fail):
                add("motion_abs", t("qcx.chk.motion_abs_mm"), txt, "warn",
                    t("qcx.d.motion_abs_fail",
                      T.rms_abs_fail, T.rms_abs_max_fail),
                    t("qcx.a.motion_abs_fail"))
                issues.append(t("qcx.i.drift_big"))
            elif (a_mean is not None and a_mean >= T.rms_abs_warn) or \
                    (a_max is not None and a_max >= T.rms_abs_max_warn):
                add("motion_abs", t("qcx.chk.motion_abs_mm"), txt, "info",
                    t("qcx.d.motion_abs_warn",
                      T.rms_abs_warn, T.rms_abs_max_warn),
                    t("qcx.a.motion_abs_warn"))
                r.notes.append(t("qcx.n.drift_val", a_mean)
                               if a_mean is not None else t("qcx.n.drift"))
            else:
                add("motion_abs", t("qcx.chk.motion_abs_mm"), txt, "ok",
                    t("qcx.d.motion_abs_ok"))

    # ---- 5. Outlier slices ----
    no = _num(rec.get("n_outlier"))
    nv = _num(rec.get("n_vol"))
    if no is None:
        add("outlier", t("qcx.chk.outlier"), t("qcx.untested"), "info",
            t("qcx.d.outlier_missing"))
    elif nv and nv > 0:
        ratio = no / nv
        txt = t("qcx.count_per_vol", int(no), ratio)
        if ratio >= T.outlier_fail:
            add("outlier", t("qcx.chk.outlier"), txt, "warn",
                t("qcx.d.outlier_hi", ratio, T.outlier_fail),
                t("qcx.a.outlier_hi"))
            issues.append(t("qcx.i.outlier_big"))
        elif ratio >= T.outlier_warn:
            add("outlier", t("qcx.chk.outlier"), txt, "warn",
                t("qcx.d.outlier_hi", ratio, T.outlier_warn))
            issues.append(t("qcx.i.outlier_slight"))
        else:
            add("outlier", t("qcx.chk.outlier"), txt, "ok",
                t("qcx.d.outlier_ok"))
    else:
        add("outlier", t("qcx.chk.outlier"),
            t("qcx.count_slices", int(no)), "ok")

    # ---- 6. Correction method ----
    method = str(rec.get("method", "") or "")
    if not method:
        add("method", t("qcx.chk.method"), t("qcx.status_unknown"), "info")
    elif "eddy_correct" in method:
        lv = "warn" if T.flag_eddy_correct else "info"
        add("method", t("qcx.chk.method"), method, lv,
            t("qcx.d.method_eddy_correct"),
            t("qcx.a.method_eddy_correct"))
        if T.flag_eddy_correct:
            issues.append(t("qcx.i.eddy_correct"))
    elif "cpu" in method:
        add("method", t("qcx.chk.method"), method, "info",
            t("qcx.d.method_cpu"))
        r.notes.append(t("qcx.n.cpu_eddy"))
    else:
        add("method", t("qcx.chk.method"), method, "ok",
            t("qcx.d.method_ok"))

    # ---- 7. Plausibility of the ALPS values ----
    for k, nm in (("alps_mean", "qcx.chk.alps_mean"),
                  ("alps_L", "qcx.chk.alps_L"),
                  ("alps_R", "qcx.chk.alps_R")):
        v = _num(rec.get(k))
        name = t(nm)
        if v is None:
            add("alps_" + k, name, t("qcx.missing"), "warn",
                t("qcx.d.alps_missing"))
            issues.append(t("qcx.i.alps_missing", name))
            continue
        if not (T.alps_min <= v <= T.alps_max):
            add("alps_" + k, name, "%.4f" % v, "warn",
                t("qcx.d.alps_range", T.alps_min, T.alps_max),
                t("qcx.a.alps_range"))
            issues.append(t("qcx.i.alps_range", name))
        else:
            add("alps_" + k, name, "%.4f" % v, "ok")

    r.issues = issues
    return r


def evaluate_all(records: List[dict], th: Optional[QCThresholds] = None) -> List[QCReport]:
    T = th or load_thresholds()
    return [evaluate(r, T) for r in records]


def summarize(reports: List[QCReport]) -> dict:
    from collections import Counter
    cnt = Counter(r.level for r in reports)
    issue_cnt = Counter()
    for r in reports:
        for it in r.issues:
            issue_cnt[it] += 1
    return {
        "total": len(reports),
        "ok": cnt.get("ok", 0),
        "info": cnt.get("info", 0),
        "warn": cnt.get("warn", 0),
        "fail": cnt.get("fail", 0),
        "top_issues": issue_cnt.most_common(5),
    }


def report_text(rep: QCReport, th: Optional[QCThresholds] = None) -> str:
    """Detailed QC report for a single subject (plain text, copyable)."""
    T = th or load_thresholds()
    lines = [t("qcx.r.subject", rep.subject),
             t("qcx.r.overall", rep.label),
             t("qcx.r.thresholds", thresholds_summary(T)),
             "=" * 36, ""]
    for c in rep.checks:
        mark = {"ok": t("qcx.mark.ok"), "info": t("qcx.mark.info"),
                "warn": t("qcx.mark.warn"),
                "fail": t("qcx.mark.fail")}.get(c.level, "[?]")
        lines.append(t("qcx.r.check_line", mark, c.label, c.value))
        if c.detail:
            lines.append("        %s" % c.detail)
        if c.advice and c.level in ("warn", "fail"):
            lines.append(t("qcx.r.advice", c.advice))
        lines.append("")
    lines.append("-" * 36)
    lines.append(t("qcx.r.attention", t("qcx.join_enum").join(rep.issues))
                 if rep.issues else t("qcx.r.no_attention"))
    return "\n".join(lines)


def batch_report_text(reports: List[QCReport], th: Optional[QCThresholds] = None) -> str:
    """QC report for the whole batch."""
    T = th or load_thresholds()
    s = summarize(reports)
    lines = [t("qcx.b.title"), "=" * 52,
             t("qcx.b.total", s["total"]),
             t("qcx.b.counts", s["ok"], s["info"], s["warn"], s["fail"]),
             t("qcx.r.thresholds", thresholds_summary(T)),
             ""]
    if s["top_issues"]:
        lines.append(t("qcx.b.top_issues"))
        for it, n in s["top_issues"]:
            lines.append(t("qcx.b.issue_line", it, n))
        lines.append("")
    bad = [r for r in reports if r.level in ("warn", "fail")]
    if bad:
        lines.append(t("qcx.b.bad_subjects"))
        lines.append("")
        for r in sorted(bad, key=lambda x: -LEVEL_ORDER.get(x.level, 0)):
            lines.append("%s  %s" % (r.label, r.subject))
            for it in r.issues:
                lines.append("        %s" % it)
    else:
        lines.append(t("qcx.b.all_pass"))
    return "\n".join(lines)

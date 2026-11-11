# -*- coding: utf-8 -*-
"""Registration robustness QC.

Purpose
-------
ALPS depends on reorienting the tensor from subject space to template space,
so small errors in the registration matrix propagate straight into the
results. This module perturbs the registration matrix slightly and quantifies
how sensitive a subject's ALPS is to registration -- information that an
overall correlation such as r_wm cannot express.

What this module does
---------------------
Perturb the registration matrix 12 times, each time re-transforming the tensor
to template space with vecreg and recomputing ALPS with the same ROI set, then
report:

  · range_pct   : range of ALPS under perturbation, as a percentage of the baseline
  · max_dev_pct : largest deviation of ALPS from the baseline, in percent

Bands (practical thresholds; tune them per cohort)
  · < 6%   : registration robust
  · 6-10%  : warning
  · > 10%  : needs attention

Implementation notes
--------------------
This module **does not depend on numpy**: it only reads, writes and multiplies
4x4 affine matrices plus a little statistics, in pure Python. So `--regqc`
still works when the python3 on PATH is shadowed by another interpreter (for
example the python3 shipped with MRtrix3) and numpy is unavailable.
"""
from __future__ import annotations

import math
import os
import subprocess

from . import text_cli  # noqa: F401  (registers cli./misc. message keys)
from .i18n import t

PERTURB_DEG = 0.5
PERTURB_MM = 0.5
RANGE_INFO = 6.0
RANGE_WARN = 10.0

# Canonical band values written to alps_result.json / CSV: they stay in a fixed
# form across interface languages, and level_label() localizes them for display.
LEVEL_ZH = {"ok": "通过", "info": "提示", "warn": "需注意"}
_LEVEL_KEYS = {"ok": "misc.regqc.level_ok", "info": "misc.regqc.level_info",
               "warn": "misc.regqc.level_warn"}
_LEVEL_ALIASES = {"通过": "ok", "pass": "ok", "ok": "ok",
                  "提示": "info", "info": "info",
                  "需注意": "warn", "check": "warn", "warn": "warn"}


def level_label(value: str) -> str:
    """Localize a regqc band value (Chinese data value or code) for display."""
    code = _LEVEL_ALIASES.get(str(value or "").strip().lower(), "ok")
    return t(_LEVEL_KEYS[code])


IDENTITY4 = [[1.0, 0.0, 0.0, 0.0],
             [0.0, 1.0, 0.0, 0.0],
             [0.0, 0.0, 1.0, 0.0],
             [0.0, 0.0, 0.0, 1.0]]


def _run(cmd, env, timeout=300):
    """Run a command and return (ok, stdout)."""
    try:
        p = subprocess.run([str(c) for c in cmd], capture_output=True,
                           text=True, timeout=timeout, env=env)
        return p.returncode == 0, (p.stdout or "")
    except Exception:
        return False, ""


def _mat_mul(A, B):
    """Multiply two 4x4 matrices in pure Python."""
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def _copy_mat(M):
    return [list(row) for row in M]


def _load_mat(path):
    """Read a 4x4 FSL affine matrix (16 whitespace-separated numbers)."""
    vals = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            for tok in line.replace(",", " ").split():
                vals.append(float(tok))
    if len(vals) < 16:
        raise ValueError(t("misc.regqc.mat_short", path))
    vals = vals[:16]
    return [vals[0:4], vals[4:8], vals[8:12], vals[12:16]]


def _save_mat(path, M):
    """Write a 4x4 matrix the FSL way (4 numbers per row, tab-separated).

    17 significant digits keep the double round-trip lossless (FSL only
    requires whitespace-separated numbers when reading).
    """
    with open(path, "w", encoding="utf-8") as fh:
        for row in M:
            fh.write("\t".join("%.17g" % v for v in row) + "\n")


def _perturbations(M, deg=PERTURB_DEG, mm=PERTURB_MM):
    """Build 12 small perturbations: +/-deg about each axis and +/-mm along each axis."""
    out = []
    axis_pairs = [(1, 2), (0, 2), (0, 1)]
    for ax in range(3):
        for sign in (+1, -1):
            rad = math.radians(deg) * sign
            c, s = math.cos(rad), math.sin(rad)
            i, j = axis_pairs[ax]
            R = _copy_mat(IDENTITY4)
            R[i][i] = c
            R[j][j] = c
            R[i][j] = -s
            R[j][i] = s
            out.append(("rot%d%+d" % (ax, sign), _mat_mul(R, M)))
            T = _copy_mat(M)
            T[ax][3] += sign * mm
            out.append(("trans%d%+d" % (ax, sign), T))
    return out


def sensitivity(env, tensor, mat, template, roi_files, work_dir):
    """Compute registration robustness.

    Parameters
    ----------
    env      : subprocess environment dict (FSLDIR / PATH / FSLOUTPUTTYPE)
    tensor   : tensor in native space (4D, 6 components)
    mat      : path of the FA -> template affine matrix
    template : path of the template
    roi_files: dict keyed L_proj/R_proj/L_asso/R_asso, values are NIfTI masks
    work_dir : directory for the perturbation intermediates

    Returns a dict; on failure it returns {"error": ...}.
    """
    os.makedirs(work_dir, exist_ok=True)
    try:
        M = _load_mat(mat)
    except Exception as e:
        return {"error": t("misc.regqc.load_fail", e)}

    def alps_with(matrix_path, tag):
        tm = os.path.join(work_dir, "regqc_%s_tensor.nii.gz" % tag)
        if not os.path.isfile(tm):
            ok, _ = _run(["vecreg", "-i", tensor, "-o", tm, "-r", template,
                          "-t", matrix_path], env, timeout=600)
            if not ok:
                return None
        vals = {}
        for cname, cidx in (("dxx", 0), ("dyy", 3), ("dzz", 5)):
            f = os.path.join(work_dir, "regqc_%s_%s.nii.gz" % (tag, cname))
            if not os.path.isfile(f):
                ok, _ = _run(["fslroi", tm, f, str(cidx), "1"], env)
                if not ok:
                    return None
            for rk, rf in roi_files.items():
                ok, out = _run(["fslstats", f, "-k", rf, "-m"], env)
                if not ok or not out.strip():
                    return None
                try:
                    vals["%s_%s" % (cname, rk)] = float(out.split()[0])
                except Exception:
                    return None
        try:
            L = ((vals["dxx_L_proj"] + vals["dxx_L_asso"]) / 2.0) / \
                ((vals["dyy_L_proj"] + vals["dzz_L_asso"]) / 2.0)
            R = ((vals["dxx_R_proj"] + vals["dxx_R_asso"]) / 2.0) / \
                ((vals["dyy_R_proj"] + vals["dzz_R_asso"]) / 2.0)
        except ZeroDivisionError:
            return None
        return (L + R) / 2.0

    base = alps_with(mat, "base")
    if base is None:
        return {"error": t("misc.regqc.base_fail")}

    vals = [base]
    for name, Mp in _perturbations(M):
        mp = os.path.join(work_dir, "regqc_%s.mat" % name)
        _save_mat(mp, Mp)
        v = alps_with(mp, name)
        if v is not None:
            vals.append(v)

    if len(vals) < 3:
        return {"error": t("misc.regqc.too_few", len(vals))}

    vmin, vmax = min(vals), max(vals)
    rng = (vmax - vmin) / base * 100.0
    maxdev = max(abs(v - base) for v in vals) / base * 100.0

    # The stored data value is kept fixed (it is written into alps_result.json
    # / CSV, so it stays stable across languages); level_label() localizes it
    # for display in the current language.
    if rng >= RANGE_WARN:
        level, code = LEVEL_ZH["warn"], "warn"
        note = t("misc.regqc.note_warn")
    elif rng >= RANGE_INFO:
        level, code = LEVEL_ZH["info"], "info"
        note = t("misc.regqc.note_info")
    else:
        level, code = LEVEL_ZH["ok"], "ok"
        note = t("misc.regqc.note_ok")

    return {
        "base": float(base),
        "n_perturb": int(len(vals) - 1),
        "min": float(vmin),
        "max": float(vmax),
        "range_pct": float(rng),
        "max_dev_pct": float(maxdev),
        "level": level,
        "level_code": code,
        "note": note,
        "perturb_deg": PERTURB_DEG,
        "perturb_mm": PERTURB_MM,
    }

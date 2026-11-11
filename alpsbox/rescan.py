# -*- coding: utf-8 -*-
"""Recompute QC metrics from existing eddy output, without re-running the pipeline.

Purpose
-------
1. Correcting legacy results: some earlier result files read the second column
   of ``eddy_movement_rms`` as the absolute displacement while naming the field
   ``rms_abs_*``. This module recomputes the values from the raw eddy output
   using the correct columns.
2. Filling gaps: when a subject's ``alps_result.json`` lacks QC fields, they can
   be filled in on their own.

Meaning of the two columns in the eddy output (verified against
``eddy_parameters``):
    column 1 = absolute displacement relative to the first volume, in mm
    column 2 = displacement relative to the previous volume, in mm

This module only reads files. It calls no FSL command and touches no GPU
memory, so hundreds of subjects are processed within seconds.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from . import text_pipeline  # noqa: F401  (registers pipe.* message keys)
from .i18n import t


@dataclass
class MotionStats:
    """Head-motion statistics for one subject."""

    subject: str = ""
    n_vol: int = 0
    # Absolute displacement relative to the reference volume
    abs_mean: float = float("nan")
    abs_max: float = float("nan")
    abs_median: float = float("nan")
    # Displacement relative to the previous volume
    rel_mean: float = float("nan")
    rel_max: float = float("nan")
    rel_median: float = float("nan")
    # Full time series, for plotting
    abs_series: List[float] = field(default_factory=list)
    rel_series: List[float] = field(default_factory=list)
    # Outlier slices: (volume index, slice index)
    outliers: List[tuple] = field(default_factory=list)
    n_slice_total: int = 0
    source: str = ""

    @property
    def ok(self) -> bool:
        return self.n_vol > 0


def find_motion_file(subject_dir: str) -> Optional[str]:
    """Locate eddy_movement_rms inside an output directory."""
    cands = [
        os.path.join(subject_dir, "eddy_out.eddy_movement_rms"),
        os.path.join(subject_dir, "eddy_out_movement_rms"),
        os.path.join(subject_dir, "eddy_movement_rms"),
    ]
    for c in cands:
        if os.path.isfile(c):
            return c
    hits = glob.glob(os.path.join(subject_dir, "*.eddy_movement_rms"))
    return hits[0] if hits else None


def find_outlier_report(subject_dir: str) -> Optional[str]:
    for name in ("eddy_out.eddy_outlier_report", "eddy_outlier_report"):
        p = os.path.join(subject_dir, name)
        if os.path.isfile(p):
            return p
    return None


def read_motion(subject_dir: str, subject: str = "") -> MotionStats:
    """Read motion and outlier information for one subject."""
    st = MotionStats(subject=subject or os.path.basename(
        os.path.normpath(subject_dir)))

    p = find_motion_file(subject_dir)
    if p:
        try:
            M = np.loadtxt(p)
            if M.ndim == 1:
                M = M.reshape(1, -1)
            if M.size and M.shape[1] >= 2:
                # Column 1 is absolute, column 2 is relative
                a = M[:, 0].astype(float)
                r = M[:, 1].astype(float)
                st.abs_series = [float(x) for x in a]
                st.rel_series = [float(x) for x in r]
                st.n_vol = len(a)
                st.abs_mean = float(a.mean())
                st.abs_max = float(a.max())
                st.abs_median = float(np.median(a))
                st.rel_mean = float(r.mean())
                st.rel_max = float(r.max())
                st.rel_median = float(np.median(r))
                st.source = p
        except Exception:
            pass

    rep = find_outlier_report(subject_dir)
    if rep:
        import re
        try:
            max_slice = 0
            for ln in open(rep, encoding="utf-8", errors="ignore"):
                m = re.search(r"Slice (\d+) in scan (\d+)", ln)
                if m:
                    sl, sc = int(m.group(1)), int(m.group(2))
                    st.outliers.append((sc, sl))
                    max_slice = max(max_slice, sl)
            st.n_slice_total = max_slice
        except Exception:
            pass
    return st


def find_subject_dirs(root: str) -> List[str]:
    """Find every subdirectory of root that contains eddy_movement_rms."""
    out = []
    if not os.path.isdir(root):
        return out
    # Check root itself first
    if find_motion_file(root):
        return [root]
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if os.path.isdir(d) and find_motion_file(d):
            out.append(d)
    return out


def scan(root: str) -> List[MotionStats]:
    """Scan a result root directory and return motion statistics per subject."""
    return [read_motion(d) for d in find_subject_dirs(root)]


# ---------------------------------------------------------------------
# Write the recomputed values back
# ---------------------------------------------------------------------
QC_KEYS = ("rms_abs_mean", "rms_abs_max", "rms_rel_mean", "rms_rel_max",
           "n_outlier", "n_slice_total")


def update_row_txt(subject_dir: str, st: MotionStats,
                   backup: bool = True) -> bool:
    """Update alps_row.txt (a single-line TSV) written by the shell pipeline.

    Some older result directories hold only an alps_row.txt instead of an
    alps_result.json; its column order matches the summary table.
    """
    p = os.path.join(subject_dir, "alps_row.txt")
    if not os.path.isfile(p):
        return False
    try:
        with open(p, encoding="utf-8") as fh:
            parts = fh.read().rstrip("\n").split("\t")
    except Exception:
        return False
    if len(parts) < 20:
        return False
    if backup:
        try:
            shutil.copy2(p, p + ".bak")
        except Exception:
            pass
    # Legacy column order: id r_wm L R mean dxxLp dyyLp dxxLa dzzLa dxxRp dyyRp dxxRa dzzRa
    #                      n_roi n_vol rms_abs_mean rms_rel_mean rms_abs_max n_outlier method
    parts[15] = _fmt0(st.abs_mean)
    parts[16] = _fmt0(st.rel_mean)
    parts[17] = _fmt0(st.abs_max)
    parts[18] = str(len(st.outliers))
    # Append rms_rel_max and n_slice_total
    parts = parts[:20] + [_fmt0(st.rel_max), str(st.n_slice_total or "")]
    try:
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("\t".join(parts) + "\n")
        return True
    except Exception:
        return False


def _fmt0(v: float) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return "0.0"
    return "%.4f" % v


def update_result_json(subject_dir: str, st: MotionStats,
                       backup: bool = True) -> bool:
    """Write the recomputed QC values back into alps_result.json."""
    p = os.path.join(subject_dir, "alps_result.json")
    if not os.path.isfile(p):
        return False
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception:
        return False
    if backup:
        try:
            shutil.copy2(p, p + ".bak")
        except Exception:
            pass
    d["rms_abs_mean"] = _clean(st.abs_mean)
    d["rms_abs_max"] = _clean(st.abs_max)
    d["rms_rel_mean"] = _clean(st.rel_mean)
    d["rms_rel_max"] = _clean(st.rel_max)
    d["n_outlier"] = len(st.outliers)
    if st.n_slice_total:
        d["n_slice_total"] = st.n_slice_total
    d["n_vol"] = st.n_vol or d.get("n_vol", 0)
    try:
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def _clean(v: float):
    if v is None or (isinstance(v, float) and v != v):
        return None
    return round(float(v), 6)


def update_tsv(tsv_path: str, stats: List[MotionStats],
               out_path: Optional[str] = None) -> str:
    """Rewrite the motion columns of a TSV, matching rows by id.

    The existing column order and all other content are kept; only
    rms_abs_mean / rms_abs_max / rms_rel_mean / rms_rel_max / n_outlier are
    replaced, and n_slice_total is appended at the end when missing.
    """
    import csv
    by_id = {s.subject: s for s in stats}
    if not os.path.isfile(tsv_path):
        raise FileNotFoundError(tsv_path)

    with open(tsv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
        cols = list(rows[0].keys()) if rows else []

    for c in ("rms_abs_mean", "rms_abs_max", "rms_rel_mean", "rms_rel_max"):
        if c not in cols:
            cols.append(c)
    if "n_slice_total" not in cols:
        cols.append("n_slice_total")

    hit = 0
    for row in rows:
        sid = row.get("id") or row.get("subject") or ""
        st = by_id.get(sid)
        if st is None or not st.ok:
            continue
        row["rms_abs_mean"] = _fmt(st.abs_mean)
        row["rms_abs_max"] = _fmt(st.abs_max)
        row["rms_rel_mean"] = _fmt(st.rel_mean)
        row["rms_rel_max"] = _fmt(st.rel_max)
        row["n_outlier"] = str(len(st.outliers))
        row["n_slice_total"] = str(st.n_slice_total or "")
        hit += 1

    out_path = out_path or tsv_path
    tmp = out_path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, delimiter="\t",
                           restval="", extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    os.replace(tmp, out_path)
    return out_path


def _fmt(v: float) -> str:
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return "%.6f" % v


def summary_table(stats: List[MotionStats]) -> str:
    """Short summary for the terminal."""
    ok = [s for s in stats if s.ok]
    lines = [t("pipe.rescan.scanned") % (len(stats), len(ok))]
    if not ok:
        return "\n".join(lines)
    def stat(vals):
        a = np.array([v for v in vals if v == v], float)
        if a.size == 0:
            return "n/a"
        return t("pipe.rescan.stat") % (a.mean(), a.max(), np.median(a))
    lines.append("")
    lines.append(t("pipe.rescan.abs_line")
                 % stat([s.abs_mean for s in ok]))
    lines.append(t("pipe.rescan.rel_line")
                 % stat([s.rel_mean for s in ok]))
    lines.append("")
    lines.append(t("pipe.rescan.abs_dist"))
    mx = np.array([s.abs_max for s in ok], float)
    for q in (50, 75, 90, 95, 100):
        lines.append(t("pipe.rescan.pct") % (q, np.percentile(mx, q)))
    lines.append(t("pipe.rescan.rel_dist"))
    rx = np.array([s.rel_max for s in ok], float)
    for q in (50, 75, 90, 95, 100):
        lines.append(t("pipe.rescan.pct") % (q, np.percentile(rx, q)))
    return "\n".join(lines)

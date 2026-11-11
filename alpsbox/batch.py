# -*- coding: utf-8 -*-
"""Batch scheduler: queueing, resuming, failure isolation and parallel control."""
from __future__ import annotations

import csv
import glob
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from . import text_pipeline  # noqa: F401  (registers pipe.* message keys)
from .config import EnvStatus
from .i18n import t
from .inputs import discover, DwiiInput
from .pipeline import AlspPipeline, AlspResult, PipelineOptions


@dataclass
class SubjectJob:
    subject: str
    subject_dir: str
    out_dir: str
    dwi: Optional[DwiiInput] = None
    error: str = ""
    topup: str = ""          # TOPUP status for logging (on / skipped reason)


def collect_jobs(root: str, out_root: str, pattern: str = "*") -> list:
    """Treat every subdirectory of root as one subject."""
    jobs = []
    for d in sorted(glob.glob(os.path.join(root, pattern))):
        if not os.path.isdir(d):
            continue
        name = os.path.basename(os.path.normpath(d))
        jobs.append(SubjectJob(
            subject=name,
            subject_dir=d,
            out_dir=os.path.join(out_root, name),
        ))
    return jobs


def collect_results(out_root: str, results: Optional[list] = None) -> list:
    """Merge this run's results with the alps_result.json files already in the
    output root (deduplicated by subject).

    A resumed run only returns the subjects processed in this run; writing them
    straight into alps_summary.csv would make the subjects finished earlier
    vanish from the summary. This function makes the summary cover every result
    in the output root.
    """
    merged = {}
    for r in results or []:
        if getattr(r, "subject", ""):
            merged[r.subject] = r
    for jp in sorted(glob.glob(os.path.join(out_root, "*",
                                           "alps_result.json"))):
        try:
            rec = json.load(open(jp, encoding="utf-8"))
        except Exception:
            continue
        subj = str(rec.get("subject", "") or "")
        if subj and subj not in merged:
            try:
                merged[subj] = AlspResult.from_record(rec)
            except Exception:
                continue
    return [merged[k] for k in sorted(merged)]


def preflight(jobs: list, topup_auto: bool = False) -> tuple:
    """Discover the inputs of a whole batch. Returns (usable jobs, failed jobs).

    With *topup_auto* each subject folder is also scanned for a reversed
    phase-encoding DWI set; when one exists it is attached to the job (TOPUP).
    A missing second series is not an error: that subject runs single-PE.
    """
    good, bad = [], []
    for j in jobs:
        try:
            j.dwi = discover(j.subject_dir)
            if topup_auto:
                from .inputs import auto_attach_topup
                ok, why = auto_attach_topup(j.dwi, j.subject_dir)
                if ok:
                    j.topup = t("misc.dwi.topup_on",
                                j.dwi.pe_direction, j.dwi.pe_direction2)
                else:
                    j.topup = t("misc.dwi.topup_off", why)
            good.append(j)
        except Exception as e:
            j.error = "%s: %s" % (type(e).__name__, e)
            bad.append(j)
    return good, bad


def run_batch(jobs: list, env: EnvStatus, opts: PipelineOptions,
              workers: int = 1, resume: bool = True) -> list:
    """Run the batch.

    With workers > 1 the subjects run in parallel; GPU memory limits usually
    make 1-2 the practical range.
    """
    pipeline = AlspPipeline(env, opts)
    results = []
    total = len(jobs)

    if workers <= 1:
        for i, j in enumerate(jobs, 1):
            print("\n" + "=" * 68)
            print(" [%d/%d] %s   %s" % (i, total, j.subject, time.strftime("%H:%M:%S")))
            print("=" * 68)
            r = pipeline.run(j.subject, j.dwi, j.out_dir)
            results.append(r)
            print(r.summary())
        return results

    # Parallel
    def _one(j, idx):
        print(t("pipe.batch.start") % (idx, total, j.subject))
        return pipeline.run(j.subject, j.dwi, j.out_dir)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_one, j, i): j for i, j in enumerate(jobs, 1)}
        for f in as_completed(futs):
            j = futs[f]
            try:
                r = f.result()
            except Exception as e:
                r = AlspResult(subject=j.subject, ok=False, error=str(e))
            results.append(r)
            print(r.summary())
    results.sort(key=lambda r: r.subject)
    return results


def write_summary(results: list, out_path: str):
    """Write the results as one table (CSV with a UTF-8 BOM, so Excel opens it correctly)."""
    if not results:
        return
    rows = [r.to_row() for r in results]
    # Union of columns (n_roi_* can differ)
    cols = list(rows[0].keys())
    for r in rows[1:]:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    # Put subject first and error last
    cols = ["subject"] + [c for c in cols if c not in ("subject", "error")] + ["error"]

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_qc_report(results: list, out_path: str, expect_voxels: int = 81,
                    max_rms: float = 0.5, min_r_wm: float = 0.77):
    """Generate a human-readable QC report (plain text, no extra dependency).

    Message strings follow ``i18n.get_lang()``; the content is the per-subject
    QC warnings plus the necessary counts, deliberately excluding cohort/group
    descriptive statistics (group analysis belongs downstream).
    """
    lines = []
    lines.append("=" * 78)
    lines.append(t("pipe.qcr.title") % time.strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("=" * 78)
    ok = [r for r in results if r.ok]
    bad = [r for r in results if not r.ok]
    lines.append(t("pipe.qcr.total") % (len(results), len(ok), len(bad)))
    lines.append("")

    if bad:
        lines.append("-" * 78)
        lines.append(t("pipe.qcr.failed"))
        lines.append("-" * 78)
        for r in bad:
            lines.append("  %-20s %s" % (r.subject, r.error[:100]))
        lines.append("")

    # Method distribution
    lines.append("-" * 78)
    lines.append(t("pipe.qcr.methods"))
    lines.append("-" * 78)
    from collections import Counter
    c = Counter((r.method or "?").split(" ")[0] for r in ok)
    for k, v in c.most_common():
        lines.append("  %-16s %d" % (k, v))
    lines.append("")

    # TOPUP usage (recorded only by results produced with dual-PE support;
    # old result files simply show as unknown)
    tp = Counter((str(getattr(r, "topup", "") or "unknown")).split(" (")[0]
                 for r in ok)
    if tp:
        lines.append("-" * 78)
        lines.append(t("pipe.qcr.topup"))
        lines.append("-" * 78)
        for k, v in tp.most_common():
            lines.append(t("pipe.qcr.topup_line") % (k or "unknown", v))
        lines.append("")

    # QC warnings
    lines.append("-" * 78)
    lines.append(t("pipe.qcr.warnings"))
    lines.append("-" * 78)
    n_warn = 0
    for r in ok:
        msgs = []
        for k, v in (r.n_roi or {}).items():
            if v != expect_voxels:
                msgs.append(t("pipe.qcr.warn_roi") % (k, v, expect_voxels))
        if r.r_wm == r.r_wm and r.r_wm < min_r_wm:
            msgs.append(t("pipe.qcr.warn_rwm") % (r.r_wm, min_r_wm))
        if r.rms_abs_max == r.rms_abs_max and r.rms_abs_max > max_rms:
            msgs.append(t("pipe.qcr.warn_rms") % (r.rms_abs_max, max_rms))
        if msgs:
            n_warn += 1
            lines.append(t("pipe.qcr.warn_subject") % r.subject)
            for m in msgs:
                lines.append("           %s" % m)
    if n_warn == 0:
        lines.append(t("pipe.qcr.no_warn"))
    lines.append("")

    # Note: group-level descriptive statistics (cohort mean/SD/range) do not
    # belong in a per-subject QC report and are intentionally omitted here;
    # use the summary table (alps_summary.csv) or the report from report.py for
    # group statistics.
    lines.append("=" * 78)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return "\n".join(lines)

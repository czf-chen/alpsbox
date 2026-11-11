# -*- coding: utf-8 -*-
"""Result session persistence: keeps the results table across runs and
supports import/export.

Storage location: ~/.alpsbox/
  session.json    -- all results of the current session (auto-saved)
  history.jsonl   -- append-only history (never deleted, for traceability)
"""
from __future__ import annotations

import csv
import json
import os
import time
from dataclasses import asdict
from typing import List, Optional
from ..i18n import t
from .. import text_ui  # noqa: F401

SESSION_DIR = os.path.join(os.path.expanduser("~"), ".alpsbox")
SESSION_FILE = os.path.join(SESSION_DIR, "session.json")
HISTORY_FILE = os.path.join(SESSION_DIR, "history.jsonl")

# Columns used by the results table (definition order is display order)
# Status and QC sit right after the subject so they stay visible while scrolling
RESULT_COLUMNS = [
    "subject", "status", "qc", "alps_L", "alps_R", "alps_mean",
    "n_L_proj", "n_R_proj", "n_L_asso", "n_R_asso",
    "r_wm", "rms_rel_mean", "rms_rel_max", "rms_abs_mean", "rms_abs_max",
    "n_outlier", "n_vol", "method", "topup", "seconds", "finished_at",
]


def ensure_dir() -> str:
    os.makedirs(SESSION_DIR, exist_ok=True)
    return SESSION_DIR


def _fmt(v, nd=4):
    if v is None:
        return ""
    if isinstance(v, float):
        if v != v:          # NaN
            return ""
        return round(v, nd)
    return v


_STATUS_OK = ("成功", "ok", "success", "done")
_STATUS_FAIL = ("失败", "failed", "fail", "error")


def canonical_status(value) -> str:
    """Return 'ok' or 'failed' for a status value (legacy values included)."""
    s = str(value or "").strip()
    low = s.lower()
    if s.startswith("成功") or low in _STATUS_OK:
        return "ok"
    if s.startswith("失败") or low in _STATUS_FAIL:
        return "failed"
    return s


def result_to_record(r) -> dict:
    """Convert an AlspResult into a serialisable record."""
    nroi = r.n_roi or {}
    status = "ok" if r.ok else (r.error[:120] if r.error else "failed")
    return {
        "subject": r.subject,
        "alps_L": _fmt(r.alps_L),
        "alps_R": _fmt(r.alps_R),
        "alps_mean": _fmt(r.alps_mean),
        "n_L_proj": nroi.get("L_proj", ""),
        "n_R_proj": nroi.get("R_proj", ""),
        "n_L_asso": nroi.get("L_asso", ""),
        "n_R_asso": nroi.get("R_asso", ""),
        "r_wm": _fmt(r.r_wm, 3),
        "rms_abs_mean": _fmt(r.rms_abs_mean, 3),
        "rms_abs_max": _fmt(r.rms_abs_max, 3),
        "rms_rel_mean": _fmt(r.rms_rel_mean, 3),
        "rms_rel_max": _fmt(r.rms_rel_max, 3),
        "n_outlier": r.n_outlier,
        "n_slice_total": getattr(r, "n_slice_total", ""),
        "n_vol": r.n_vol,
        "method": r.method,
        "topup": getattr(r, "topup", ""),
        "topup_config": getattr(r, "topup_config", ""),
        "seconds": _fmt(r.seconds, 1),
        "status": status,
        "finished_at": time.strftime("%Y-%m-%d %H:%M"),
    }


def save_session(records: List[dict]) -> bool:
    try:
        ensure_dir()
        tmp = SESSION_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                       "records": records}, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, SESSION_FILE)
        return True
    except Exception:
        return False


def load_session() -> List[dict]:
    try:
        if not os.path.isfile(SESSION_FILE):
            return []
        with open(SESSION_FILE, encoding="utf-8") as fh:
            d = json.load(fh)
        if isinstance(d, dict):
            return list(d.get("records", []))
        if isinstance(d, list):
            return d
    except Exception:
        pass
    return []


def append_history(records: List[dict]) -> None:
    """Append to the history file (for traceability; unaffected by "clear")."""
    try:
        ensure_dir()
        with open(HISTORY_FILE, "a", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------
# Import / export
# ---------------------------------------------------------------------
def export_csv(records: List[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    records = [dict(r) for r in records]
    for r in records:
        if r.get("status"):
            r["status"] = canonical_status(r["status"])
    cols = [c for c in RESULT_COLUMNS if any(c in r for r in records)] or RESULT_COLUMNS
    # Add any extra columns that may be present
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval="", extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r)


def export_json(records: List[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "records": records}, fh, ensure_ascii=False, indent=1)


def _coerce(rec: dict) -> dict:
    """Convert imported string values back to numbers and normalise column
    names to a canonical case.

    Column names differ between sources: session records use lower case
    (alps_L), while the shell summary table uses upper case (ALPS_L) and calls
    the subject column ``id``. Everything is normalised to one canonical set
    here so downstream modules only ever see a single naming scheme.
    """
    # Map lower case -> canonical column name
    canon = {c.lower(): c for c in RESULT_COLUMNS}
    canon["id"] = "subject"
    canon["name"] = "subject"

    out = {}
    for k, v in rec.items():
        lk = str(k).strip().lower()
        key = canon.get(lk, str(k).strip())
        if key in ("subject", "method", "topup", "topup_config", "status",
                   "finished_at", "qc"):
            out[key] = "" if v is None else str(v)
            if key == "status":
                out[key] = canonical_status(out[key])
            continue
        if v is None or v == "":
            out[key] = ""
            continue
        try:
            f = float(v)
            out[key] = int(f) if key.startswith("n_") else f
        except (TypeError, ValueError):
            out[key] = v

    # The shell summary table carries a single aggregated n_roi value; expand it
    # onto the four ROIs, otherwise QC reports the per-ROI voxel counts as missing
    if "n_roi" in out and "n_L_proj" not in out:
        try:
            n = int(float(out["n_roi"]))
            if n > 0:
                for k in ("n_L_proj", "n_R_proj", "n_L_asso", "n_R_asso"):
                    out[k] = n
        except (TypeError, ValueError):
            pass
    return out


def import_file(path: str) -> tuple[List[dict], str]:
    """Import results from CSV / JSON / TSV.

    Returns
    -------
    (records, message)
    """
    if not os.path.isfile(path):
        return [], t("ui.file_missing")
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".json":
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
            recs = d.get("records", d) if isinstance(d, dict) else d
            if not isinstance(recs, list):
                return [], t("ui.bad_json")
            recs = [_coerce(r) for r in recs if isinstance(r, dict)]
            return recs, t("ui.import_json", len(recs))

        # CSV / TSV
        delim = "\t" if ext in (".tsv", ".txt") else ","
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh, delimiter=delim)
            recs = [_coerce(r) for r in reader if any((v or "").strip() for v in r.values())]
        if not recs:
            return [], t("ui.no_data_rows")
        if "subject" not in recs[0] and "id" in recs[0]:
            for r in recs:
                r["subject"] = r.pop("id", "")
        return recs, t("ui.import_n", len(recs), ext.lstrip(".").upper())
    except Exception as e:
        return [], t("ui.read_fail", e)


def merge_records(old: List[dict], new: List[dict]) -> List[dict]:
    """Merge by subject: new records override old ones (kept in new order)."""
    idx = {}
    out = []
    for r in old:
        s = str(r.get("subject", ""))
        if s in idx:
            out[idx[s]] = r
        else:
            idx[s] = len(out)
            out.append(r)
    for r in new:
        s = str(r.get("subject", ""))
        if s in idx:
            out[idx[s]] = r
        else:
            idx[s] = len(out)
            out.append(r)
    return out


QC_LEVEL_KEYS = {"ok": "qc.pass", "info": "qc.info",
                 "warn": "qc.warn", "fail": "qc.fail"}
_QC_LEVEL_ALIASES = {
    "ok": "ok", "pass": "ok", "通过": "ok",
    "info": "info", "提示": "info",
    "warn": "warn", "check": "warn", "caution": "warn", "需注意": "warn",
    "fail": "fail", "failed": "fail", "不合格": "fail",
}


def qc_level(value) -> str:
    """Normalize a stored QC value (code or localized label) to a level."""
    return _QC_LEVEL_ALIASES.get(str(value or "").strip().lower(), "")


def qc_label(value) -> str:
    """Localize a stored QC value for display in the current language."""
    from ..i18n import t
    lv = qc_level(value)
    return t(QC_LEVEL_KEYS[lv]) if lv else str(value or "")


def attach_qc(records: List[dict]) -> List[dict]:
    """Add the qc field to every record.

    QC is a derived result and is not persisted: it is recomputed after each
    load. The stored value is the canonical level code (ok/info/warn/fail), so
    session files and CSV exports are language-independent; the GUI localizes
    it when rendering.
    """
    from .. import qc as _qc
    th = _qc.load_thresholds()
    for r in records:
        try:
            r["qc"] = _qc.evaluate(r, th).level
        except Exception:
            r["qc"] = ""
    return records


def qc_reports(records: List[dict]):
    """Return QCReport objects in record order."""
    from .. import qc as _qc
    return [_qc.evaluate(r) for r in records]

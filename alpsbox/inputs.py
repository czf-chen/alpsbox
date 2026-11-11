# -*- coding: utf-8 -*-
"""Input discovery: find the four DWI inputs of a subject directory robustly.

Edge cases handled here:
  1. The directory contains both .nii and .nii.gz -> sort by path length, so the
     shorter name wins
  2. ROI files are mixed in (projection.nii.gz / associatioin.nii.gz spelling
     variants) -> **hard requirement: a same-stem .bval and .bvec must exist**,
     which is the decisive test
  3. The json may sit outside DTI1/, or be named SE2_xxx_3.json (a different
     stem from the nii) -> search recursively, preferring entries whose
     SeriesDescription mentions DTI/DWI
  4. Some directories have no json at all -> report that explicitly instead of
     silently degrading
"""
from __future__ import annotations

import glob
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from . import text_cli  # noqa: F401  (registers cli./misc. message keys)
from .i18n import t


@dataclass
class DwiiInput:
    """The four DWI inputs of one subject.

    Optional second DWI: it **must use the opposite phase-encoding direction**
    to the first one (for example PA first, AP second), and the first volume of
    both series must be b0. Once a second set is supplied, the pipeline runs
    TOPUP first to correct susceptibility distortion and then runs eddy with
    --topup (equivalent to -i/-j/-k/-n of gbarisano/alps.sh).
    """
    nii: str
    bval: str
    bvec: str
    json: Optional[str] = None
    json_info: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    # Optional: second DWI with reversed phase encoding (for TOPUP)
    nii2: Optional[str] = None
    bval2: Optional[str] = None
    bvec2: Optional[str] = None
    json2: Optional[str] = None
    json_info2: dict = field(default_factory=dict)

    @property
    def has_dual_pe(self) -> bool:
        """Whether a reversed phase-encoding series is available for TOPUP."""
        return bool(self.nii2 and os.path.isfile(str(self.nii2)))

    @property
    def pe_direction(self) -> str:
        return str(self.json_info.get("PhaseEncodingDirection", "") or "")

    @property
    def pe_direction2(self) -> str:
        return str(self.json_info2.get("PhaseEncodingDirection", "") or "")

    def check_dual_pe(self) -> tuple:
        """Check whether the dual-PE input is usable. Returns (ok, reason)."""
        if not self.has_dual_pe:
            return False, t("misc.dwi.no_second")
        if not (self.bval2 and self.bvec2):
            return False, t("misc.dwi.second_incomplete")
        p1 = self.pe_direction.rstrip("-")
        p2 = self.pe_direction2.rstrip("-")
        if not p1 or not p2:
            return False, t("misc.dwi.pe_missing")
        if p1 != p2:
            return False, t("misc.dwi.pe_other_axis",
                            self.pe_direction, self.pe_direction2)
        if self.pe_direction == self.pe_direction2:
            return False, t("misc.dwi.pe_same", self.pe_direction)
        return True, "OK"

    @property
    def stem(self) -> str:
        for suf in (".nii.gz", ".nii"):
            if self.nii.endswith(suf):
                return self.nii[: -len(suf)]
        return self.nii

    @property
    def has_eddy_metadata(self) -> bool:
        """Whether a full eddy run is possible (needs phase-encoding direction + readout time)."""
        return bool(self.json_info.get("PhaseEncodingDirection")
                    and self.json_info.get("TotalReadoutTime") is not None)

    def describe(self) -> str:
        lines = ["    DWI  : %s" % os.path.basename(self.nii),
                 "    bval : %s" % os.path.basename(self.bval),
                 "    bvec : %s" % os.path.basename(self.bvec)]
        if self.json:
            lines.append("    json : %s" % os.path.basename(self.json))
            lines.append("            PE=%s  TRT=%s" % (
                self.json_info.get("PhaseEncodingDirection", "?"),
                self.json_info.get("TotalReadoutTime", "?")))
        else:
            lines.append(t("misc.dwi.json_missing"))
        for n in self.notes:
            lines.append(t("misc.dwi.note_line", n))
        return "\n".join(lines)


def _stem_of(p: str) -> str:
    for suf in (".nii.gz", ".nii"):
        if p.endswith(suf):
            return p[: -len(suf)]
    return p


def _rank_nii_candidates(paths: list) -> list:
    """Sort strategy: shorter names first (so that long ROI names such as
    xxx_projection.nii.gz are not picked). Ties are broken lexicographically to
    keep the result deterministic."""
    return sorted(paths, key=lambda p: (len(p), p))


def find_json_for(dwi: DwiiInput, search_root: str) -> tuple[Optional[str], dict, list]:
    """Find the matching BIDS sidecar json for a DWI series.

    Strategy, in priority order:
      1. a .json with the same stem as the nii (the standard dcm2niix output)
      2. any json in the same directory that carries PhaseEncodingDirection
      3. a recursive search, preferring SeriesDescription/ProtocolName with DTI/DWI
    """
    notes = []
    d = os.path.dirname(dwi.nii)
    stem = _stem_of(dwi.nii)

    # 1) Same stem
    p = stem + ".json"
    if os.path.isfile(p):
        info = _load_json(p, notes)
        if info is not None:
            return p, info, notes

    # 2) Any json in the same directory
    cands = sorted(glob.glob(os.path.join(d, "*.json")))
    for c in cands:
        info = _load_json(c, notes)
        if info and "PhaseEncodingDirection" in info:
            notes.append(t("misc.dwi.json_name_mismatch", os.path.basename(c)))
            return c, info, notes

    # 3) Recursive search
    cands = sorted(glob.glob(os.path.join(search_root, "**", "*.json"), recursive=True))
    scored = []
    for c in cands:
        info = _load_json(c, [])
        if not info or "PhaseEncodingDirection" not in info:
            continue
        desc = str(info.get("SeriesDescription", "")).upper()
        proto = str(info.get("ProtocolName", "")).upper()
        score = 0
        if "DTI" in desc or "DIFF" in desc:
            score += 10
        if "DTI" in proto or "DIFF" in proto:
            score += 5
        if os.path.dirname(c) == d:
            score += 3
        scored.append((score, c, info))
    if scored:
        scored.sort(key=lambda x: (-x[0], x[1]))
        score, c, info = scored[0]
        notes.append(t("misc.dwi.json_in_subdir", os.path.relpath(c, search_root)))
        return c, info, notes

    return None, {}, notes


def _load_json(p: str, notes: list) -> Optional[dict]:
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        if not isinstance(d, dict):
            notes.append(t("misc.dwi.json_not_dict", os.path.basename(p)))
            return None
        return d
    except Exception as e:
        notes.append(t("misc.dwi.json_unreadable", os.path.basename(p), e))
        return None


def read_json_info(p: str) -> dict:
    """Read a BIDS json sidecar; used by external callers (e.g. --json2)."""
    info = _load_json(p, [])
    return info or {}


def discover(subject_dir: str, deep: bool = True) -> DwiiInput:
    """Discover the DWI inputs under subject_dir.

    Raises
    ------
    FileNotFoundError
        When no nii with a matching bval+bvec exists.
    """
    if not os.path.isdir(subject_dir):
        raise FileNotFoundError(t("misc.dwi.no_dir", subject_dir))

    pattern = os.path.join(subject_dir, "**", "*.nii*") if deep \
        else os.path.join(subject_dir, "*.nii*")
    all_nii = [p for p in glob.glob(pattern, recursive=deep) if p.endswith((".nii", ".nii.gz"))]

    if not all_nii:
        raise FileNotFoundError(t("misc.dwi.no_nii", subject_dir))

    # ★ Hard requirement: the same-stem bval + bvec must both exist
    valid = []
    for p in _rank_nii_candidates(all_nii):
        st = _stem_of(p)
        if os.path.isfile(st + ".bval") and os.path.isfile(st + ".bvec"):
            valid.append(p)

    if not valid:
        listing = "\n      ".join(os.path.basename(x) for x in _rank_nii_candidates(all_nii)[:10])
        raise FileNotFoundError(t("misc.dwi.no_valid", len(all_nii), listing))

    # Take the shortest name and note it when several candidates exist
    notes = []
    if len(valid) > 1:
        notes.append(t("misc.dwi.multi_valid", len(valid),
                       os.path.basename(valid[0])))

    nii = valid[0]
    stem = _stem_of(nii)
    dwi = DwiiInput(nii=nii, bval=stem + ".bval", bvec=stem + ".bvec", notes=notes)

    # Locate the json sidecar
    jp, info, jnotes = find_json_for(dwi, subject_dir)
    dwi.json = jp
    dwi.json_info = info
    dwi.notes.extend(jnotes)

    # Check whether the json is sufficient for eddy
    if jp and not dwi.has_eddy_metadata:
        dwi.notes.append(t("misc.dwi.no_eddy_meta"))

    return dwi


def validate_bvec_bval(dwi: DwiiInput) -> list:
    """Check bval/bvec consistency (columns = volumes). Returns warnings."""
    warns = []
    try:
        bvals = open(dwi.bval).read().split()
        n_bval = len(bvals)
    except Exception as e:
        return [t("misc.dwi.bval_unreadable", e)]
    try:
        bvec_lines = [ln for ln in open(dwi.bvec).read().splitlines() if ln.strip()]
        n_bvec = len(bvec_lines[0].split()) if bvec_lines else 0
    except Exception as e:
        return [t("misc.dwi.bvec_unreadable", e)]

    if n_bval == 0:
        warns.append(t("misc.dwi.bval_empty"))
    if n_bvec == 0:
        warns.append(t("misc.dwi.bvec_empty"))
    if n_bval and n_bvec and n_bval != n_bvec:
        warns.append(t("misc.dwi.count_mismatch", n_bval, n_bvec))
    if len(bvec_lines) != 3:
        warns.append(t("misc.dwi.bvec_3rows", len(bvec_lines)))
    return warns

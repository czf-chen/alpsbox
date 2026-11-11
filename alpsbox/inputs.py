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

import difflib
import glob
import json
import os
import re
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
        if self.has_dual_pe:
            lines.append("    DWI2 : %s" % os.path.basename(str(self.nii2)))
            if self.json2:
                lines.append("    json2: %s" % os.path.basename(str(self.json2)))
                lines.append("            PE2=%s  TRT2=%s" % (
                    self.json_info2.get("PhaseEncodingDirection", "?"),
                    self.json_info2.get("TotalReadoutTime", "?")))
            else:
                lines.append(t("misc.dwi.json2_missing"))
            ok, why = self.check_dual_pe()
            if ok:
                lines.append("    " + t("misc.dwi.topup_on",
                                        self.pe_direction, self.pe_direction2))
            else:
                lines.append("    " + t("misc.dwi.topup_off", why))
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


def discover_all(subject_dir: str, deep: bool = True) -> list:
    """Return every complete DWI set under *subject_dir*.

    Each entry is a :class:`DwiiInput` with its BIDS json sidecar resolved the
    same way as :func:`discover`. Used to find the reversed phase-encoding
    series for TOPUP when several DWI sets share one subject folder.
    """
    if not os.path.isdir(subject_dir):
        raise FileNotFoundError(t("misc.dwi.no_dir", subject_dir))

    pattern = os.path.join(subject_dir, "**", "*.nii*") if deep \
        else os.path.join(subject_dir, "*.nii*")
    all_nii = [p for p in glob.glob(pattern, recursive=deep)
               if p.endswith((".nii", ".nii.gz"))]

    out = []
    for nii in _rank_nii_candidates(all_nii):
        stem = _stem_of(nii)
        if not (os.path.isfile(stem + ".bval")
                and os.path.isfile(stem + ".bvec")):
            continue
        d = DwiiInput(nii=nii, bval=stem + ".bval", bvec=stem + ".bvec")
        jp, info, jnotes = find_json_for(d, subject_dir)
        d.json = jp
        d.json_info = info
        d.notes.extend(jnotes)
        out.append(d)
    return out


def find_reversed_dwi(primary: DwiiInput, candidates: list) -> tuple:
    """Pick the candidate whose phase-encoding direction is opposite to *primary*.

    Returns ``(second, reason)``; ``second`` is None when no usable pair exists
    and ``reason`` is a human-readable explanation.
    """
    others = [c for c in candidates
              if os.path.abspath(c.nii) != os.path.abspath(primary.nii)]
    if not others:
        return None, t("misc.dwi.no_second")
    reasons = []
    for c in others:
        p1, p2 = primary.pe_direction, c.pe_direction
        if not p1 or not p2:
            reasons.append(t("misc.dwi.pe_missing"))
            continue
        if p1.rstrip("-") != p2.rstrip("-"):
            reasons.append(t("misc.dwi.pe_other_axis", p1, p2))
            continue
        if p1 == p2:
            reasons.append(t("misc.dwi.pe_same", p1))
            continue
        return c, "OK"
    return None, reasons[0] if reasons else t("misc.dwi.no_second")


def attach_second(primary: DwiiInput, second: DwiiInput) -> DwiiInput:
    """Attach a discovered second DWI set to *primary* as the TOPUP input."""
    primary.nii2 = second.nii
    primary.bval2 = second.bval
    primary.bvec2 = second.bvec
    primary.json2 = second.json
    primary.json_info2 = dict(second.json_info or {})
    return primary


def attach_explicit_second(primary: DwiiInput, nii2: str, bval2: str,
                           bvec2: str, json2: str) -> tuple:
    """Attach a second DWI set given explicitly by file paths (CLI ``--dwi2``...).

    All four files are required: the json is needed for the phase-encoding
    direction and readout time. Returns ``(ok, reason)``.
    """
    if not (nii2 and bval2 and bvec2 and json2):
        return False, t("misc.dwi.second_incomplete")
    for label, path in (("nii", nii2), ("bval", bval2),
                        ("bvec", bvec2), ("json", json2)):
        if not path or not os.path.isfile(path):
            return False, t("misc.dwi.second_file_missing", label, path)
    second = DwiiInput(nii=nii2, bval=bval2, bvec=bvec2, json=json2,
                       json_info=read_json_info(json2))
    attach_second(primary, second)
    return primary.check_dual_pe()


def attach_second_from_nii(primary: DwiiInput, nii2: str) -> tuple:
    """Attach a second DWI chosen by its NIfTI path (GUI file picker).

    The companion .bval/.bvec must share the NIfTI base name; the json is
    resolved like the main input. Returns ``(ok, reason)``.
    """
    if not nii2 or not os.path.isfile(nii2):
        return False, t("misc.dwi.second_nii_missing", nii2)
    stem = _stem_of(nii2)
    bval2, bvec2 = stem + ".bval", stem + ".bvec"
    if not os.path.isfile(bval2) or not os.path.isfile(bvec2):
        return False, t("misc.dwi.second_incomplete_named",
                        os.path.basename(nii2))
    second = DwiiInput(nii=nii2, bval=bval2, bvec=bvec2)
    jp, info, jnotes = find_json_for(second, os.path.dirname(nii2))
    second.json = jp
    second.json_info = info
    second.notes.extend(jnotes)
    attach_second(primary, second)
    return primary.check_dual_pe()


# Folder-name tokens that mark a phase-encoding direction. Used only for the
# guarded sibling search below; acquisition names differ between sites.
_PE_NAME_TOKENS = frozenset((
    "ap", "pa", "rl", "lr", "col", "row", "a2p", "p2a", "r2l", "l2r",
    "col2row", "row2col", "apra", "paap", "fwd", "rev", "forward", "reverse",
))


def _name_tokens(name: str) -> list:
    return [x for x in re.split(r"[^a-z0-9]+", (name or "").lower()) if x]


def _name_stem(name: str) -> str:
    """Folder name without PE tokens (used to compare two PE-variant folders)."""
    return "".join(x for x in _name_tokens(name) if x not in _PE_NAME_TOKENS)


def _names_are_pe_variants(a: str, b: str) -> bool:
    """Heuristic: two sibling folder names look like AP/PA variants of one series."""
    ta, tb = _name_tokens(a), _name_tokens(b)
    if not any(x in _PE_NAME_TOKENS for x in ta):
        return False
    if not any(x in _PE_NAME_TOKENS for x in tb):
        return False
    sa, sb = _name_stem(a), _name_stem(b)
    if not sa or not sb:
        return True
    return difflib.SequenceMatcher(None, sa, sb).ratio() >= 0.6


def _find_sibling_reversed(primary: DwiiInput, subject_dir: str) -> tuple:
    """Search immediate sibling folders for a reversed-PE series.

    Returns ``(second, sibling_name, reason)``. This is intentionally
    conservative: it only runs for single-subject mode, only when the parent
    folder is small (a few series, not a cohort root), and only when the sibling
    name looks like the other PE variant of the selected series.
    """
    me = os.path.abspath(subject_dir)
    parent = os.path.dirname(me)
    if parent == me:
        return None, "", t("misc.dwi.sibling_none")
    try:
        names = sorted(os.listdir(parent))
    except OSError:
        return None, "", t("misc.dwi.sibling_none")
    sibs = []
    for n in names:
        p = os.path.join(parent, n)
        if n.startswith(".") or not os.path.isdir(p):
            continue
        if os.path.abspath(p) == me:
            continue
        sibs.append(p)
    if not sibs:
        return None, "", t("misc.dwi.sibling_none")
    if len(sibs) > 4:
        return None, "", t("misc.dwi.sibling_too_many", len(sibs))
    me_name = os.path.basename(me)
    best = None
    best_name = ""
    best_score = -1.0
    for sib in sibs:
        sib_name = os.path.basename(sib)
        if not _names_are_pe_variants(me_name, sib_name):
            continue
        try:
            candidates = discover_all(sib, deep=True)
        except Exception:
            continue
        for cand in candidates:
            p1, p2 = primary.pe_direction, cand.pe_direction
            if not p1 or not p2:
                continue
            if p1.rstrip("-") != p2.rstrip("-") or p1 == p2:
                continue
            score = difflib.SequenceMatcher(
                None, _name_stem(me_name), _name_stem(sib_name)).ratio()
            if score > best_score:
                best, best_name, best_score = cand, sib_name, score
    if best is None:
        return None, "", t("misc.dwi.sibling_no_match")
    return best, best_name, ""


def auto_attach_topup(primary: DwiiInput, subject_dir: str,
                      deep: bool = True, search_siblings: bool = False) -> tuple:
    """Find and attach a reversed-PE series for TOPUP automatically.

    Used by batch mode, the GUI's "auto-detect" option and ``run --topup-auto``.
    A missing second series is not an error: the caller continues with single-PE
    eddy. With *search_siblings* (single-subject mode only) immediate sibling
    folders are checked as well, which covers the common structure where an AP
    and a PA export sit next to each other. Returns ``(ok, reason)``.
    """
    try:
        candidates = discover_all(subject_dir, deep)
    except Exception as e:
        return False, str(e)
    second, why = find_reversed_dwi(primary, candidates)
    sibling = ""
    if second is None and search_siblings:
        second, sibling, why = _find_sibling_reversed(primary, subject_dir)
    if second is None:
        return False, why
    attach_second(primary, second)
    if sibling:
        primary.notes.append(t("misc.dwi.sibling_used", sibling))
    return primary.check_dual_pe()


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

# -*- coding: utf-8 -*-
"""ROI management.

Two sources:
  1. Reference ROIs bundled with the package (copied from the open-source
     reference implementation gbarisano/alps, MIT License)
     location: alpsbox/data/ROIs_JHU_ALPS/
     L_SCR.nii.gz / R_SCR.nii.gz / L_SLF.nii.gz / R_SLF.nii.gz
     81 voxels each (spheres of 2.5 mm radius on the @1mm JHU-ICBM-FA template)
     provenance, license and sha256: data/ROIs_JHU_ALPS/PROVENANCE.md
  2. Spheres that the user defines on the JHU-ICBM-FA-1mm template
     (center coordinates + radius)

**The formal citation for the reference implementation is in `alpsbox/citations.py`:**
    Barisano G. alps: Bash script to compute DTI-ALPS (alps.sh). GitHub
    repository. https://github.com/gbarisano/alps. Commit
    e6f58e7c1b882a799b613e91fe15bab940dc4cd3 (2025-09-12).
    Accessed 2026-11-11. MIT License.
    Companion paper: Liu X, Barisano G, et al. Aging and Disease.
    2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2

Anatomical naming (identical to the reference script):
    SCR = superior corona radiata  (projection fibers)
    SLF = superior longitudinal fasciculus  (association fibers)

Mandatory ROI order (required by the ALPS formula):
    [0] L_proj = L_SCR   [1] R_proj = R_SCR
    [2] L_asso = L_SLF   [3] R_asso = R_SLF
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from .i18n import t
from . import text_roi  # noqa: F401  (registers roim.* message keys)

ROI_ORDER = ["L_proj", "R_proj", "L_asso", "R_asso"]

# Reference implementation file name -> internal ROI name
_BUNDLED_FILES = {
    "L_proj": "L_SCR.nii.gz",
    "R_proj": "R_SCR.nii.gz",
    "L_asso": "L_SLF.nii.gz",
    "R_asso": "R_SLF.nii.gz",
}

# Anatomical labels (used in reports/logs; resolved in the active language)
class _LangMap(dict):
    def __init__(self, keys):
        super().__init__({k: "" for k in keys})
        self._keys = keys

    def __getitem__(self, k):
        return t(self._keys.get(k, k))

    def get(self, k, default=None):
        if k in self._keys:
            return t(self._keys[k])
        return default


ROI_ANATOMY = _LangMap({"L_proj": "roim.anat.L_proj",
                        "R_proj": "roim.anat.R_proj",
                        "L_asso": "roim.anat.L_asso",
                        "R_asso": "roim.anat.R_asso"})

# Default sphere centers (MNI 152 coordinates, aligned with the bundled ROIs)
DEFAULT_CENTERS = {
    "L_proj": (-26, -16, 27),
    "R_proj": (26, -16, 27),
    "L_asso": (-38, -16, 27),
    "R_asso": (38, -16, 27),
}
DEFAULT_RADIUS_MM = 2.5
# Theoretical voxel count for a 2.5 mm sphere on a 1 mm grid
EXPECTED_VOXELS_2P5MM = 81


def package_roi_dir() -> str:
    """Return the directory that holds the bundled ROIs."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "ROIs_JHU_ALPS")


@dataclass
class RoiSet:
    """Paths of one set of four ROIs (template space)."""
    paths: dict           # name -> .nii.gz path
    space: str            # "template"
    source: str           # "bundled" | "generated" | "custom"

    def get(self, name: str) -> str:
        return self.paths[name]

    def ordered(self) -> list:
        return [self.paths[n] for n in ROI_ORDER]

    def describe(self) -> str:
        lines = [t("roim.desc.source", self.source, self.space)]
        for n in ROI_ORDER:
            lines.append("      %-8s %s" % (n, os.path.basename(self.paths[n])))
            lines.append(t("roim.desc.anatomy", ROI_ANATOMY[n]))
        return "\n".join(lines)


def load_bundled() -> RoiSet:
    """Use the reference ROIs bundled with the package (recommended)."""
    d = package_roi_dir()
    paths = {}
    missing = []
    for name, fn in _BUNDLED_FILES.items():
        p = os.path.join(d, fn)
        if not os.path.isfile(p):
            missing.append(fn)
        paths[name] = p
    if missing:
        raise FileNotFoundError(
            t("roim.err.bundled_missing", missing, d))
    return RoiSet(paths=paths, space="template", source="bundled")


def load_custom(paths: list) -> RoiSet:
    """Four user-supplied ROIs; the order must be L_proj, R_proj, L_asso, R_asso."""
    if len(paths) != 4:
        raise ValueError(t("roim.err.custom_count", len(paths)))
    for p in paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(t("roim.err.file_missing", p))
    return RoiSet(paths=dict(zip(ROI_ORDER, paths)), space="template", source="custom")


def generate_spheres(template: str, out_dir: str, radius: float = DEFAULT_RADIUS_MM,
                     centers: Optional[dict] = None, runner=None) -> RoiSet:
    """Generate four spheres on the template (needs a runner for fslmaths).

    Use this only when the bundled ROIs are unsuitable, or to change the radius.
    """
    import numpy as np
    import nibabel as nib

    if runner is None:
        raise ValueError(t("roim.err.need_runner"))

    centers = centers or DEFAULT_CENTERS
    img = nib.load(template)
    inv = np.linalg.inv(img.affine)
    os.makedirs(out_dir, exist_ok=True)

    paths = {}
    for name in ROI_ORDER:
        x, y, z = centers[name]
        vox = inv.dot(np.array([x, y, z, 1.0]))[:3]
        i, j, k = (int(round(v)) for v in vox)
        out = os.path.join(out_dir, "%s.nii.gz" % name)
        # Build the sphere with fslmaths (same approach as the reference script)
        runner.run(["fslmaths", template, "-mul", "0", "-add", "0", "_s"], quiet=True)
        runner.run(["fslmaths", "_s", "-add", "1", "-roi", i, 1, j, 1, k, 1, 0, 1, "_v"],
                   quiet=True)
        runner.run(["fslmaths", "_v", "-kernel", "sphere", radius,
                    "-fmean", "-bin", "-thr", "0.5", out], quiet=True)
        for tmp in ("_s.nii.gz", "_v.nii.gz"):
            if os.path.isfile(os.path.join(runner.workdir, tmp)):
                os.remove(os.path.join(runner.workdir, tmp))
        paths[name] = out

    return RoiSet(paths=paths, space="template", source="generated")


def check_roi_sanity(runner, roi_set: RoiSet) -> dict:
    """Count the voxels of every ROI and return {name: voxel_count}."""
    from .fsl import fslstats_voxels
    out = {}
    for name in ROI_ORDER:
        n = fslstats_voxels(runner, roi_set.get(name))
        out[name] = n
    return out

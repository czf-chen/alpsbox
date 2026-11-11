# -*- coding: utf-8 -*-
"""ROI preview: interactive slices generated from the JHU template and ROI masks.

Design notes
------------
* The background image is the JHU-ICBM-FA-1mm template shipped with FSL. That
  template is subject to the FSL licence (non-commercial use only, no
  redistribution), so this module reads it at run time from the local $FSLDIR
  only and neither bundles it nor writes it into the ALPSbox data directory.
* If the template is unavailable locally, the preview degrades to a plain grey
  background with ROI outlines; functionality is unaffected.
* The returned labels array has the same size as the displayed image and is used
  to decide on mouse hover which ROI lies under the cursor.
* The three views are handled as follows:
    - axial    : single slice (all ROIs lie on the same z slice, so all four are
                 visible)
    - coronal  : single slice (all ROIs lie on the same z slice, so all four are
                 visible)
    - sagittal : maximum intensity projection along the left-right direction
                 (the four ROIs sit at different x, so one slice cannot show
                 them all)
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

from . import text_qc  # noqa: F401  (registers the qcx.* strings)
from .i18n import t

try:
    import nibabel as nib
except Exception:                                    # pragma: no cover
    nib = None

try:
    from PIL import Image
except Exception:                                    # pragma: no cover
    Image = None


ROI_ORDER = ["L_proj", "R_proj", "L_asso", "R_asso"]

ROI_LATIN = {
    "L_proj": "Superior corona radiata, left",
    "R_proj": "Superior corona radiata, right",
    "L_asso": "Superior longitudinal fasciculus, left",
    "R_asso": "Superior longitudinal fasciculus, right",
}
# Display names for the fibre types are looked up per language; see
# ROI_FIBER at the end of the file (i18n keys roi.fiber_*).
ROI_COLOR = {
    "L_proj": (229, 72, 77),
    "R_proj": (247, 104, 8),
    "L_asso": (13, 116, 206),
    "R_asso": (13, 157, 140),
}
ROI_COLOR_HI = {
    "L_proj": (255, 150, 153),
    "R_proj": (255, 176, 100),
    "L_asso": (95, 172, 244),
    "R_asso": (86, 205, 190),
}

_FILES = {
    "L_proj": "L_SCR.nii.gz",
    "R_proj": "R_SCR.nii.gz",
    "L_asso": "L_SLF.nii.gz",
    "R_asso": "R_SLF.nii.gz",
}


@dataclass
class SliceView:
    image: "Image.Image"
    labels: np.ndarray
    plane: str
    slice_idx: int
    voxel_size_mm: float
    has_template: bool
    note: str = ""
    is_projection: bool = False


def roi_dir() -> str:
    from .roi import package_roi_dir
    return package_roi_dir()


def find_fa_template(fsl_dir: Optional[str]) -> Optional[str]:
    cands = []
    if fsl_dir:
        cands.append(os.path.join(fsl_dir, "data", "atlases", "JHU",
                                  "JHU-ICBM-FA-1mm.nii.gz"))
    env = os.environ.get("FSLDIR")
    if env:
        cands.append(os.path.join(env, "data", "atlases", "JHU",
                                  "JHU-ICBM-FA-1mm.nii.gz"))
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def load_masks() -> tuple:
    if nib is None:
        raise RuntimeError(t("qcx.roi.need_nibabel"))
    masks, aff, shape = {}, None, None
    d = roi_dir()
    for name in ROI_ORDER:
        f = os.path.join(d, _FILES[name])
        if not os.path.isfile(f):
            raise FileNotFoundError(t("qcx.roi.files_missing", f))
        im = nib.load(f)
        masks[name] = np.asanyarray(im.dataobj) > 0.5
        if aff is None:
            aff, shape = im.affine, im.shape
    return masks, aff, shape


def build_slice(fsl_dir: Optional[str], plane: str = "axial",
                zoom: float = 2.0, pad_mm: float = 16.0,
                square_mm: Optional[float] = None) -> SliceView:
    """Generate a single slice with the ROIs overlaid.

    plane : 'axial' | 'coronal' | 'sagittal'
    zoom  : output pixel magnification factor
    pad_mm: margin left around the ROI bounding box
    square_mm : forced side length of the square field of view; when None, use
                the smallest square that holds all ROIs
    """
    if Image is None:
        raise RuntimeError(t("qcx.roi.need_pillow"))

    masks, aff, shape = load_masks()
    vox = np.sqrt((aff[:3, :3] ** 2).sum(axis=0))
    vox_mm = float(vox.mean())

    # Overall bounding box of the ROIs
    allm = np.zeros(shape, bool)
    for m in masks.values():
        allm |= m
    idx = np.argwhere(allm)
    lo0, hi0 = idx.min(axis=0), idx.max(axis=0)
    center = (lo0 + hi0) / 2.0

    # Square field of view
    if square_mm is None:
        span = float(np.max((hi0 - lo0) * vox)) + 2 * pad_mm
        square_mm = span
    half_vox = int(round((square_mm / 2.0) / vox_mm))
    lo = np.maximum(0, (center - half_vox).astype(int))
    hi = np.minimum(np.array(shape) - 1, (center + half_vox).astype(int))

    axis_map = {"sagittal": 0, "coronal": 1, "axial": 2}
    sl = int(round(center[axis_map[plane]]))

    if plane == "axial":
        # rows = y (anterior -> posterior), columns = x (left -> right)
        sub_sl = (slice(None), slice(None), sl)
        lab = np.zeros((hi[1] - lo[1] + 1, hi[0] - lo[0] + 1), np.int16)
        for k, name in enumerate(ROI_ORDER, 1):
            lab[masks[name][lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, sl].T] = k
        bg = _template_slice(fsl_dir, plane, sl, lo, hi)
    elif plane == "coronal":
        # rows = z (superior -> inferior), columns = x (left -> right)
        lab = np.zeros((hi[2] - lo[2] + 1, hi[0] - lo[0] + 1), np.int16)
        for k, name in enumerate(ROI_ORDER, 1):
            lab[masks[name][lo[0]:hi[0] + 1, sl, lo[2]:hi[2] + 1].T] = k
        bg = _template_slice(fsl_dir, plane, sl, lo, hi)
    else:
        # Sagittal: maximum intensity projection along x, rows = z, columns = y
        lab = np.zeros((hi[2] - lo[2] + 1, hi[1] - lo[1] + 1), np.int16)
        for k, name in enumerate(ROI_ORDER, 1):
            slab = masks[name][lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
            proj = slab.any(axis=0)                 # (ny, nz)
            lab[proj.T] = k
        bg = _template_projection(fsl_dir, lo, hi)

    lab = lab[::-1, :]                              # flip to radiological view

    note = ""
    if bg is None:
        bg = np.full(lab.shape, 0.4, np.float32)
        note = t("qcx.roi.no_template")

    rgb = _compose(bg, lab)

    img = Image.fromarray(rgb, "RGB")
    if zoom and abs(zoom - 1.0) > 1e-6:
        nw = max(1, int(round(img.width * zoom)))
        nh = max(1, int(round(img.height * zoom)))
        img = img.resize((nw, nh), Image.NEAREST)

    labels = _resample_labels(lab, img.height, img.width)

    return SliceView(image=img, labels=labels, plane=plane, slice_idx=sl,
                     voxel_size_mm=vox_mm, has_template=bg is not None,
                     note=note, is_projection=(plane == "sagittal"))


def _compose(bg: np.ndarray, lab: np.ndarray) -> np.ndarray:
    g = np.clip(bg, 0, 1)
    rgb = np.stack([g * 232 + 14, g * 232 + 16, g * 238 + 22], axis=-1)
    a = 0.55
    for k, name in enumerate(ROI_ORDER, 1):
        m = lab == k
        if not m.any():
            continue
        col = np.array(ROI_COLOR[name], float)
        rgb[m] = rgb[m] * (1 - a) + col * a
    for k, name in enumerate(ROI_ORDER, 1):
        e = _edge(lab == k)
        rgb[e] = np.array(ROI_COLOR[name], float)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _edge(mask: np.ndarray) -> np.ndarray:
    m = mask.astype(np.uint8)
    er = m.copy()
    er[1:, :] &= m[:-1, :]
    er[:-1, :] &= m[1:, :]
    er[:, 1:] &= m[:, :-1]
    er[:, :-1] &= m[:, 1:]
    return (m - er).astype(bool)


def _resample_labels(lab: np.ndarray, H: int, W: int) -> np.ndarray:
    if lab.shape == (H, W):
        return lab
    yy = np.clip((np.arange(H) * lab.shape[0] / H).astype(int), 0, lab.shape[0] - 1)
    xx = np.clip((np.arange(W) * lab.shape[1] / W).astype(int), 0, lab.shape[1] - 1)
    return lab[yy][:, xx]


def _load_fa(fsl_dir):
    if nib is None:
        return None
    p = find_fa_template(fsl_dir)
    if not p:
        return None
    try:
        return np.asanyarray(nib.load(p).dataobj).astype(np.float32)
    except Exception:
        return None


def _norm(s: np.ndarray) -> np.ndarray:
    pos = s[s > 0]
    vmax = float(np.percentile(pos, 98)) if pos.size else 1.0
    return np.clip(s / max(vmax, 1e-6), 0, 1)


def _template_slice(fsl_dir, plane, sl, lo, hi) -> Optional[np.ndarray]:
    d = _load_fa(fsl_dir)
    if d is None:
        return None
    try:
        if plane == "axial":
            s = d[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, sl].T
        elif plane == "coronal":
            s = d[lo[0]:hi[0] + 1, sl, lo[2]:hi[2] + 1].T
        else:
            s = d[sl, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1].T
        return _norm(s[::-1, :])
    except Exception:
        return None


def _template_projection(fsl_dir, lo, hi) -> Optional[np.ndarray]:
    d = _load_fa(fsl_dir)
    if d is None:
        return None
    try:
        blk = d[lo[0]:hi[0] + 1, lo[1]:hi[1] + 1, lo[2]:hi[2] + 1]
        s = blk.max(axis=0).T                       # (nz, ny)
        return _norm(s[::-1, :])
    except Exception:
        return None


# ROI names are looked up per language
_ROI_TITLE_KEYS = {"L_proj": "roi.L_proj", "R_proj": "roi.R_proj",
                   "L_asso": "roi.L_asso", "R_asso": "roi.R_asso"}
_ROI_FIBER_KEYS = {"L_proj": "roi.fiber_proj", "R_proj": "roi.fiber_proj",
                   "L_asso": "roi.fiber_asso", "R_asso": "roi.fiber_asso"}


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


ROI_TITLE = _LangMap(_ROI_TITLE_KEYS)
ROI_FIBER = _LangMap(_ROI_FIBER_KEYS)

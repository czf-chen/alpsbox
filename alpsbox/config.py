# -*- coding: utf-8 -*-
"""Environment detection and configuration: locate FSL / MRtrix3 / dcm2niix and validate them.

Design notes:
  * FSL is not bundled, only detected (the FSL license forbids redistribution)
  * When something is missing, give clear installation guidance instead of an
    obscure error
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from . import text_cli  # noqa: F401  (registers cli./misc. message keys)
from .i18n import t


# Essential FSL commands (the pipeline fails if any of them is missing)
FSL_REQUIRED = ["eddy", "bet", "dtifit", "flirt", "vecreg",
                "fslroi", "fslmaths", "fslstats", "fslval"]
# Optional but recommended
FSL_OPTIONAL = ["eddy_cuda", "eddy_cuda11.0", "eddy_openmp",
                "fdt_rotate_bvecs", "fslcc"]


@dataclass
class EnvStatus:
    """Result of the environment check."""
    fsl_dir: Optional[str] = None
    mrtrix_dir: Optional[str] = None
    dcm2niix: Optional[str] = None
    fsl_found: dict = field(default_factory=dict)     # cmd -> full path, or None
    fsl_missing: list = field(default_factory=list)
    eddy_binary: Optional[str] = None                  # the eddy binary that will actually be used
    mrtrix_has_mrdegibbs: bool = False
    mrtrix_has_dwidenoise: bool = False
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        lines = []
        lines.append("=" * 68)
        lines.append(t("misc.env.title"))
        lines.append("=" * 68)
        lines.append("  FSLDIR      : %s" % (self.fsl_dir or t("misc.env.not_found")))
        lines.append("  MRtrix3     : %s"
                     % (self.mrtrix_dir or t("misc.env.not_found_unring")))
        lines.append("  dcm2niix    : %s"
                     % (self.dcm2niix or t("misc.env.not_found_dicom")))
        lines.append(t("misc.env.eddy_use", self.eddy_binary or t("misc.env.unknown")))
        lines.append("")
        lines.append(t("misc.env.fsl_required"))
        for c in FSL_REQUIRED:
            p = self.fsl_found.get(c)
            lines.append("    %s %-16s %s" % ("OK " if p else "-- ", c,
                                              p or t("misc.env.missing")))
        if self.fsl_missing:
            lines.append("")
            lines.append(t("misc.env.missing_list", ", ".join(self.fsl_missing)))
        if self.warnings:
            lines.append("")
            for w in self.warnings:
                lines.append(t("misc.env.warn_line", w))
        if self.errors:
            lines.append("")
            for e in self.errors:
                lines.append(t("misc.env.error_line", e))
        lines.append("=" * 68)
        return "\n".join(lines)


def _which_in(cmd: str, extra_paths: list) -> Optional[str]:
    """Look up an executable on PATH and in extra directories."""
    p = shutil.which(cmd)
    if p:
        return p
    for d in extra_paths:
        cand = os.path.join(d, cmd)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def _fsl_version(fsl_dir: str) -> Optional[str]:
    """Try to read the FSL version string."""
    for name in ("etc/fslconf/fslversion", "etc/fslversion"):
        p = os.path.join(fsl_dir, name)
        if os.path.isfile(p):
            try:
                return open(p).read().strip()
            except Exception:
                pass
    return None


def detect_env(fsl_dir: Optional[str] = None, verbose: bool = False) -> EnvStatus:
    """Detect the runtime environment.

    Parameters
    ----------
    fsl_dir : str, optional
        Explicit FSLDIR; otherwise inferred from the FSLDIR environment
        variable or from PATH.
    verbose : bool
        Print the detection report immediately.
    """
    st = EnvStatus()

    # ---- FSL ----
    cand_dir = fsl_dir or os.environ.get("FSLDIR")
    if cand_dir and not os.path.isdir(cand_dir):
        st.warnings.append(t("misc.env.fsldir_missing", cand_dir))
        cand_dir = None
    if not cand_dir:
        # Infer FSLDIR from the eddy found on PATH
        p = shutil.which("eddy")
        if p:
            # .../fsl/bin/eddy -> .../fsl
            cand_dir = os.path.dirname(os.path.dirname(os.path.realpath(p)))
    st.fsl_dir = cand_dir

    extra = []
    if cand_dir:
        extra = [os.path.join(cand_dir, "bin"),
                 os.path.join(cand_dir, "share", "fsl", "bin")]

    for c in FSL_REQUIRED + FSL_OPTIONAL:
        st.fsl_found[c] = _which_in(c, extra)
    st.fsl_missing = [c for c in FSL_REQUIRED if not st.fsl_found[c]]

    # ---- eddy binary selection: GPU first ----
    for name in ("eddy_cuda", "eddy_cuda11.0", "eddy_cuda12.0", "eddy_openmp", "eddy"):
        if st.fsl_found.get(name):
            st.eddy_binary = st.fsl_found[name]
            break

    # ---- MRtrix3 ----
    # Check PATH first, then a few common install locations (many users install
    # into ~/mrtrix3 without modifying PATH)
    mg = shutil.which("mrdegibbs")
    if not mg:
        for cand in (os.path.expanduser("~/mrtrix3/bin"),
                     "/usr/local/mrtrix3/bin", "/opt/mrtrix3/bin",
                     "/usr/lib/mrtrix3/bin"):
            p = os.path.join(cand, "mrdegibbs")
            if os.path.isfile(p) and os.access(p, os.X_OK):
                mg = p
                break
    if mg:
        st.mrtrix_has_mrdegibbs = True
        # .../mrtrix3/bin/mrdegibbs -> .../mrtrix3
        st.mrtrix_dir = os.path.dirname(os.path.dirname(os.path.realpath(mg)))
    else:
        st.warnings.append(t("misc.env.no_mrdegibbs"))

    # Denoising uses dwidenoise (MRtrix3). The MRtrix3 documentation requires
    # denoising before unringing, because unringing alters the noise structure
    # and therefore degrades the dwidenoise estimate.
    dw = shutil.which("dwidenoise")
    if not dw and st.mrtrix_dir:
        p = os.path.join(st.mrtrix_dir, "bin", "dwidenoise")
        if os.path.isfile(p):
            dw = p
    st.mrtrix_has_dwidenoise = bool(dw)

    # ---- dcm2niix ----
    st.dcm2niix = shutil.which("dcm2niix")

    # ---- Determine errors ----
    if not st.fsl_dir:
        st.errors.append(t("misc.env.no_fsl"))
    elif st.fsl_missing:
        st.errors.append(t("misc.env.fsl_missing_cmds", ", ".join(st.fsl_missing)))
    if not st.eddy_binary:
        st.errors.append(t("misc.env.no_eddy"))

    if st.fsl_dir:
        v = _fsl_version(st.fsl_dir)
        if v:
            st.warnings.append(t("misc.env.fsl_version", v))

    if verbose:
        print(st.summary())
    return st


def make_env(st: EnvStatus, threads: int = 4) -> dict:
    """Build the subprocess environment so that FSL/MRtrix3 are found."""
    env = os.environ.copy()
    paths = []
    if st.mrtrix_dir:
        paths.append(os.path.join(st.mrtrix_dir, "bin"))
    if st.fsl_dir:
        env["FSLDIR"] = st.fsl_dir
        env.setdefault("FSLOUTPUTTYPE", "NIFTI_GZ")
        paths.insert(0, os.path.join(st.fsl_dir, "bin"))
        paths.insert(1, os.path.join(st.fsl_dir, "share", "fsl", "bin"))
    env["PATH"] = os.pathsep.join(paths + [env.get("PATH", "")])
    env["OMP_NUM_THREADS"] = str(threads)
    env["MRTRIX_NTHREADS"] = str(threads)
    # Prevent FSL commands from launching a GUI
    env["FSLOUTPUTTYPE"] = env.get("FSLOUTPUTTYPE", "NIFTI_GZ")
    return env

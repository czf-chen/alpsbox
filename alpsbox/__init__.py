# =====================================================================
# ALPSbox — automated DTI-ALPS processing toolbox
# =====================================================================
# A CLI-first DTI-ALPS processing package:
#   DICOM/NIfTI -> unringing -> eddy -> dtifit -> registration -> tensor
#   reorientation -> ROI extraction -> ALPS index -> quality control
#
# Design principles:
#   1. We only orchestrate; FSL is not bundled (FSL licence forbids
#      redistribution and is non-commercial).
#   2. ROI masks are reproduced from gbarisano/alps (MIT); see
#      data/ROIs_JHU_ALPS/PROVENANCE.md for source, licence and sha256.
#   3. Every intermediate product is kept on disk, so runs can resume.
#   4. Input discovery is strict: a dMRI volume must have matching
#      bval/bvec files.
#
# References (see docs/CITATIONS.md for full citations):
#   Taoka T, et al. Jpn J Radiol. 2017;35(4):172-178.
#   Liu X, Barisano G, et al. Aging and Disease. 2024;15(4):1885-1898.
# =====================================================================

__version__ = "1.0.0"
__author__ = "ALPSbox contributors"

__all__ = ["__version__"]

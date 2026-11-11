# -*- coding: utf-8 -*-
"""Formal citations and third-party provenance (single source of truth).

If you only want to cite this tool, the authoritative files are
``CITATION.cff`` and ``docs/CITATIONS.md`` at the repository root.
This module is the single source of truth for the provenance of
"the ALPS method / the reference implementation / the ROI masks";
source comments, the GUI help, reports and the documentation all
quote it from here. **Change provenance here only.**

Terminology (important, to avoid ambiguity)
-------------------------------------------
The ALPS index has **no official standard or certified
implementation**. When this repository says "reference
implementation" -- older documentation also wrote "official
implementation" / "official alps.sh" -- it **always** means the
``alps.sh`` of the open-source repository below:

    Barisano G. alps: Bash script to compute DTI-ALPS (alps.sh).
    GitHub repository. https://github.com/gbarisano/alps.
    Commit e6f58e7c1b882a799b613e91fe15bab940dc4cd3 (2025-09-12).
    Accessed 2026-11-11. MIT License.

The companion paper (the repository README asks you to cite it whenever the
script is used):

    Liu X, Barisano G, et al. Cross-vendor test-retest validation of
    diffusion tensor image analysis along the perivascular space (DTI-ALPS)
    for evaluating glymphatic system function. Aging and Disease.
    2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2

The ALPS method itself comes from:

    Taoka T, et al. Evaluation of glymphatic system activity with the
    diffusion MR technique: diffusion tensor image analysis along the
    perivascular space (DTI-ALPS) in Alzheimer's disease cases.
    Japanese Journal of Radiology. 2017;35(4):172-178.
    doi:10.1007/s11604-017-0617-z

Bundled ROI masks
-----------------
The four masks under ``alpsbox/data/ROIs_JHU_ALPS/``
(``L_SCR.nii.gz``, ``R_SCR.nii.gz``, ``L_SLF.nii.gz``,
``R_SLF.nii.gz``) are copied from the ``ROIs_JHU_ALPS/`` directory
of the repository above (MIT License, Copyright (c) 2023 Giuseppe
Barisano; the full licence text is in
``LICENSE_Barisano_alps.txt``). That repository's 2025-05-28
update changed the default ROI from a 5 mm radius to a 2.5 mm
radius (a 5 mm diameter, consistent with Taoka 2017), 81 voxels
per ROI. Source and checksums are recorded in
``alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md``.

Differences from this tool's defaults (as of the commit above)
--------------------------------------------------------------
The reference implementation runs with **different** defaults, so
always compare parameter settings like for like:

=============  ==========================  =================================
Item           Reference impl. default     ALPSbox default
=============  ==========================  =================================
Tensor         ``-f 1`` (flirt/applywarp)  vecreg (equivalent ``-f 2``)
Preprocessing  ``-d 1`` denoise + unring   unring only (equivalent ``-d 3``)
eddy binary    ``-e 1`` eddy_cpu           GPU eddy (``--threads``/GPU)
Reg. cost      flirt default corratio      normmi
ROI            2.5 mm sphere (2025-05-28)  same bundled masks
=============  ==========================  =================================

The cross-implementation comparison in ``docs/VALIDATION.md``
runs that repository's ``alps.sh`` after a
local parameter-alignment patch (``-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2``,
with the registration cost patched to normmi); the patch was used for that
validation only and does not change what the reference implementation releases.
"""
from __future__ import annotations

# =====================================================================
# Identity (change the version/commit here only)
# =====================================================================
REPO_URL = "https://github.com/gbarisano/alps"
REPO_COMMIT = "e6f58e7c1b882a799b613e91fe15bab940dc4cd3"
REPO_COMMIT_DATE = "2025-09-12"
REPO_FILE_ALPS_SH_BLOB = "d48e29198d061b0dc496c68e0ed086da9fe8747c"
ACCESS_DATE = "2026-11-11"
ROI_SOURCE_DIR = "ROIs_JHU_ALPS"
ROI_NOTE = ("2.5 mm 半径球（5 mm 直径），与 Taoka 2017 一致；"
            "该默认值由参考实现 2025-05-28 更新说明确立，每个 ROI 81 体素")
MIT_NOTE = "MIT License, Copyright (c) 2023 Giuseppe Barisano"

# =====================================================================
# Formal citations (full form: never omit title/journal/year after the
# authors; volume(issue):pages/DOI or URL)
# =====================================================================
CITATION_ALPS_METHOD = (
    "Taoka T, Masutani Y, Kawai H, Nakane T, Matsuoka K, Yasuno F, "
    "Kishimoto T, Naganawa S. Evaluation of glymphatic system activity with "
    "the diffusion MR technique: diffusion tensor image analysis along the "
    "perivascular space (DTI-ALPS) in Alzheimer's disease cases. Japanese "
    "Journal of Radiology. 2017;35(4):172-178. doi:10.1007/s11604-017-0617-z"
)

CITATION_REF_SOFTWARE = (
    "Barisano G. alps: Bash script to compute DTI-ALPS (alps.sh). GitHub "
    "repository. %s. Commit %s (%s). Accessed %s. MIT License."
    % (REPO_URL, REPO_COMMIT, REPO_COMMIT_DATE, ACCESS_DATE)
)

CITATION_REF_PAPER = (
    "Liu X, Barisano G, et al. Cross-vendor test-retest validation of "
    "diffusion tensor image analysis along the perivascular space (DTI-ALPS) "
    "for evaluating glymphatic system function. Aging and Disease. "
    "2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2"
)

CITATION_ROI_MASKS = (
    "Bundled ROI masks reproduced from the " + ROI_SOURCE_DIR + "/ directory "
    "of the reference implementation (Barisano G. alps, GitHub, " + REPO_URL
    + ", commit " + REPO_COMMIT + "; " + ACCESS_DATE + "). " + MIT_NOTE + ". "
    + ROI_NOTE + ". License text: LICENSE_Barisano_alps.txt."
)

CITATION_TAOKA_SHORT_ZH = "Taoka 2017, Jpn J Radiol 35(4):172-178, " \
                          "doi:10.1007/s11604-017-0617-z"

CITATION_TOPUP = (
    "Andersson JLR, Skare S, Ashburner J. How to correct susceptibility "
    "distortions in spin-echo echo-planar images: application to diffusion "
    "tensor imaging. NeuroImage. 2003;20(2):870-888. "
    "doi:10.1016/S1053-8119(03)00336-7"
)

# =====================================================================
# Common combinations (quoted directly by the GUI / reports / source
# comments so the wording never drifts)
# =====================================================================
SHORT_REF_ZH = ("参考实现 = gbarisano/alps（%s，commit %s，%s；MIT）；"
                "配套论文：Liu & Barisano 2024, doi:10.14336/AD.2023.0321-2"
                % (REPO_URL, REPO_COMMIT[:7], REPO_COMMIT_DATE))

SHORT_REF_EN = ("Reference implementation = gbarisano/alps (%s, commit %s, "
                "%s; MIT); accompanying paper: Liu & Barisano 2024, "
                "doi:10.14336/AD.2023.0321-2"
                % (REPO_URL, REPO_COMMIT[:7], REPO_COMMIT_DATE))

# Used by the "References:" block at the end of GUI help and reports
# (everything after the colon must carry the full provenance)
REFERENCE_CITATION_ZH = (
    "本仓库中的「参考实现」专指：%s（%s，commit %s，%s，MIT License）；"
    "配套论文：%s；ALPS 方法原始文献：%s。"
    % (CITATION_REF_SOFTWARE.split(". GitHub")[0],
       REPO_URL, REPO_COMMIT[:7], REPO_COMMIT_DATE,
       CITATION_REF_PAPER, CITATION_ALPS_METHOD)
)

REFERENCE_CITATION_EN = (
    "In this repository, 'reference implementation' refers specifically to "
    "Barisano G. alps (alps.sh), GitHub, %s, commit %s (%s), MIT License; "
    "accompanying paper: %s; original ALPS method: %s."
    % (REPO_URL, REPO_COMMIT, REPO_COMMIT_DATE,
       CITATION_REF_PAPER, CITATION_ALPS_METHOD)
)


def reference_citation(lang: str = "zh_CN") -> str:
    """The "reference implementation" citation, full provenance (zh/en)."""
    return REFERENCE_CITATION_EN if lang == "en" else REFERENCE_CITATION_ZH


def short_reference(lang: str = "zh_CN") -> str:
    """One-line short form (for space-constrained GUI hints)."""
    return SHORT_REF_EN if lang == "en" else SHORT_REF_ZH


def ref_defaults_table() -> list:
    """Reference implementation defaults vs this tool's defaults
    (for docs/help-page rendering)."""
    return [
        ("张量变换", "flirt/applywarp 直接变换（-f 1，不重定向）",
         "vecreg（等价 -f 2）"),
        ("预处理", "去噪 + 去振铃（-d 1）", "只去振铃（等价 -d 3），去噪可选"),
        ("eddy 程序", "eddy_cpu（-e 1）", "GPU eddy（自动探测）"),
        ("配准代价", "flirt 默认 corratio", "normmi（可用 --reg-cost 切换）"),
        ("ROI", "2.5 mm 半径球（2025-05-28 起）", "同一套随包掩膜"),
    ]


# =====================================================================
# Layout: one reference per paragraph, numbered, blank line between
# entries (shared by GUI/reports/docs)
# =====================================================================
def format_citations(entries, numbering: bool = True) -> str:
    """Lay complete citations out as a one-reference-per-paragraph block.

    - each entry is its own paragraph, separated by a blank line;
    - with numbering enabled, entries are prefixed [1] [2] ...;
    - nothing is wrapped inside an entry; the display side wraps it (GUI text
      boxes and browsers both do).
    """
    blocks = []
    for i, e in enumerate(entries, 1):
        # collapse extra whitespace but keep the citation complete
        e = " ".join(str(e).split())
        blocks.append(("[%d] " % i if numbering else "") + e)
    return "\n\n".join(blocks)


def reference_entries() -> list:
    """For the "References" page/report: software -> companion paper ->
    method."""
    return [CITATION_REF_SOFTWARE, CITATION_REF_PAPER, CITATION_ALPS_METHOD]


def gui_tip_block(lang: str = "zh_CN") -> str:
    """Citation block appended to GUI hint texts such as the
    advanced-parameter tips (software + companion paper)."""
    header = "文献：\n\n" if lang != "en" else "References:\n\n"
    return "\n\n" + header + format_citations(
        [CITATION_REF_SOFTWARE, CITATION_REF_PAPER])


def topup_block(lang: str = "zh_CN") -> str:
    """Citation block for the TOPUP option (dual phase encoding, FSL topup)."""
    header = "文献：\n\n" if lang != "en" else "References:\n\n"
    return "\n\n" + header + format_citations([CITATION_TOPUP])


def roi_block(lang: str = "zh_CN") -> str:
    """Theory and provenance citation block for the ROI-mask help
    (method/software/paper/masks)."""
    header = "文献：\n\n" if lang != "en" else "References:\n\n"
    return "\n\n" + header + format_citations(
        [CITATION_ALPS_METHOD, CITATION_REF_SOFTWARE, CITATION_REF_PAPER,
         CITATION_ROI_MASKS])


def refs_html(lang: str = "en") -> str:
    """Citation block for reports and web pages (ordered list with
    hanging indent)."""
    items = "".join("<li>%s</li>" % e for e in reference_entries())
    return '<ol class="refs">%s</ol>' % items

# Citations and provenance

[English](CITATIONS.md) | [简体中文](zh-CN/CITATIONS.md)

This page lists the formal citations and third-party provenance for ALPSbox.
If you only need to know **what to cite**, see §1. If you want to know exactly
what "reference implementation" means in this repository, see §2.

---

## 1. Citing ALPSbox

Until a paper is published, cite the software as:

> ALPSbox contributors. *ALPSbox: one-click DTI-ALPS processing with quality
> control and HTML reports.* Version 1.0.0. GitHub; 2026.
> https://github.com/your-org/alpsbox

A machine-readable `CITATION.cff` is provided in the repository root (GitHub
shows a "Cite this repository" button). Once a journal paper is published,
please cite that paper instead — the software citation remains useful as a
tool reference.

---

## 2. What "reference implementation" means

**ALPS has no official or standard-certified implementation.** Throughout this
repository, "reference implementation" (called "official alps.sh" in older
documentation) always means the following open-source project:

[1] Barisano G. *alps: Bash script to compute DTI-ALPS (alps.sh)*.
GitHub repository. https://github.com/gbarisano/alps.
Commit e6f58e7c1b882a799b613e91fe15bab940dc4cd3 (2025-09-12).
Accessed 2026-11-11. MIT License.

That repository asks users to also cite its accompanying paper:

[2] Liu X, Barisano G, et al. Cross-vendor test-retest validation of diffusion
tensor image analysis along the perivascular space (DTI-ALPS) for evaluating
glymphatic system function. *Aging and Disease*.
2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2

The ALPS method itself was introduced by:

[3] Taoka T, Masutani Y, Kawai H, Nakane T, Matsuoka K, Yasuno F, Kishimoto T, Naganawa S.
Evaluation of glymphatic system activity with the diffusion MR technique:
diffusion tensor image analysis along the perivascular space (DTI-ALPS) in
Alzheimer's disease cases. *Japanese Journal of Radiology*.
2017;35(4):172-178. doi:10.1007/s11604-017-0617-z

### 2.1 Reference defaults vs ALPSbox defaults

The reference implementation's default settings differ from ALPSbox:

| Item | Reference default | ALPSbox default |
|---|---|---|
| Tensor to template | `-f 1`: flirt/applywarp, **no reorientation** | `vecreg` (equivalent to `-f 2`) |
| Preprocessing | `-d 1`: denoise + unring | unring only (equivalent to `-d 3`); denoise optional |
| eddy program | `-e 1`: eddy_cpu | GPU eddy when available |
| Registration cost | flirt default `corratio` | `normmi` (switchable with `--reg-cost`) |
| ROI | 2.5 mm radius spheres (since 2025-05-28) | the same bundled masks |

Any statement of the form "differs from the reference by X%" therefore must
name the settings used on both sides. The cross-implementation validation in
[VALIDATION.md](VALIDATION.md) ran the reference script with parameter-alignment
patches (`-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2`, cost patched to normmi);
the patches are documented in the validation record.

---

## 3. Bundled ROI masks

`alpsbox/data/ROIs_JHU_ALPS/` contains four masks reproduced from the
`ROIs_JHU_ALPS/` directory of the reference implementation
(MIT License, Copyright (c) 2023 Giuseppe Barisano; full text in
[`LICENSE_Barisano_alps.txt`](../LICENSE_Barisano_alps.txt)):

- 2.5 mm radius spheres (= 5 mm diameter, matching Taoka 2017), on the
  `JHU-ICBM-FA-1mm` template in FSL, 81 voxels per ROI;
- the 2.5 mm default dates from the reference implementation's 2025-05-28
  update (previously 5 mm radius);
- per-file sha256 checksums and the verification procedure are in
  [`alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md`](../alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md).

---

## 4. Citations by processing step

| Step | Reference |
|---|---|
| Gibbs unringing (mrdegibbs) | Kellner E, Dhital B, Kiselev VG, Reisert M. Gibbs-ringing artifact removal based on local subvoxel-shifts. *Magnetic Resonance in Medicine*. 2016;76(5):1574-1581. doi:10.1002/mrm.26054 |
| Eddy current / motion / outlier replacement (eddy, --repol) | Andersson JLR, Sotiropoulos SN. An integrated approach to correction for off-resonance effects and subject movement in diffusion MR imaging. *NeuroImage*. 2016;125:1063-1078. doi:10.1016/j.neuroimage.2015.10.019 |
| Brain extraction (bet) | Smith SM. Fast robust automated brain extraction. *Human Brain Mapping*. 2002;17(3):143-155. doi:10.1002/hbm.10062 |
| Tensor fitting (dtifit) | Basser PJ, Mattiello J, LeBihan D. MR diffusion tensor spectroscopy and imaging. *Biophysical Journal*. 1994;66(1):259-267. doi:10.1016/S0006-3495(94)80775-1 |
| Linear registration (flirt) | Jenkinson M, Bannister P, Brady M, Smith S. Improved optimization for the robust and accurate linear registration and motion correction of brain images. *NeuroImage*. 2002;17(2):825-841. doi:10.1006/nimg.2002.1132 |
| Tensor reorientation (vecreg, T' = R·T·Rᵀ) | Alexander DC, Pierpaoli C, Basser PJ, Gee JC. Spatial transformations of diffusion tensor magnetic resonance images. *IEEE Transactions on Medical Imaging*. 2001;20(11):1131-1139. doi:10.1109/42.963816 |
| Registration robustness / geometry confounds (used by `--regqc`) | Ajouz A, et al. Automatic determination of glymphatic flow with the DTI-ALPS-index along the principal axis system in native imaging space corrects for head and fiber orientation. *Magnetic Resonance in Medicine*. 2026;95(2):1110-1122. doi:10.1002/mrm.70082; Schilling KG, et al. White matter geometry confounds diffusion tensor imaging along perivascular space (DTI-ALPS) measures. *Human Brain Mapping*. 2025;46(10):e70282. doi:10.1002/hbm.70282 |
| Reliability / spatial consistency of DTI-ALPS (QC context) | Qiu E, et al. Reliability and spatial consistency of MR diffusion tensor imaging measures along the cerebral perivascular space. *Journal of Neuroimaging*. 2025;35(5):e70086. doi:10.1111/jon.70086 |
| Motion QC (framewise displacement) | Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen SE. Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion. *NeuroImage*. 2012;59(3):2142-2154. doi:10.1016/j.neuroimage.2011.10.018 |
| Reproducibility of reorientation (vecreg) | Tatekawa H, Matsushita S, Ueda D, Takita H, Horiuchi D, Atsukawa N, Morishita Y, Tsukamoto T, Shimono T, Miki Y. Improved reproducibility of diffusion tensor image analysis along the perivascular space (DTI-ALPS) index: an analysis of reorientation technique of the OASIS-3 dataset. *Japanese Journal of Radiology*. 2023;41(4):393-400. doi:10.1007/s11604-022-01370-2 |
| ALPS index definition | Taoka T, et al. 2017 (see §2, [3]) |
| TOPUP distortion correction | Andersson JLR, Skare S, Ashburner J. How to correct susceptibility distortions in spin-echo echo-planar images: application to diffusion tensor imaging. *NeuroImage*. 2003;20(2):870-888. doi:10.1016/S1053-8119(03)00336-7 |

---

## 5. Third-party software

ALPSbox does not bundle FSL or MRtrix3; it calls separately installed programs.

- **FSL** — Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, Smith SM. FSL.
  *NeuroImage*. 2012;62(2):782-790. doi:10.1016/j.neuroimage.2011.09.015.
  Licence: non-commercial use, redistribution not permitted.
- **MRtrix3** — Tournier JD, Smith R, Raffelt D, Tabbara R, Dhollander T,
  Pietsch M, Christiaens D, Jeurissen B, Yeh CH, Connelly A. MRtrix3: A fast,
  flexible and open software framework for medical image processing and
  visualisation. *NeuroImage*. 2019;202:116137.
  doi:10.1016/j.neuroimage.2019.116137.
- **dcm2niix** (optional) — Li X, Morgan PS, Ashburner J, Smith J, Rorden C.
  The first step for neuroimaging data analysis: DICOM to NIfTI conversion.
  *Journal of Neuroscience Methods*. 2016;264:47-56.
  doi:10.1016/j.jneumeth.2016.03.001.

---

## 6. What we did and did not do

- **Not done**: we did not propose a new ALPS definition and did not modify the
  reference implementation; that project remains the work of Giuseppe Barisano
  (MIT Licence).
- **Done**: an independent Python implementation (FSL orchestration + GUI + QC
  + reports), validated against the parameter-aligned reference implementation
  on 30 external subjects (r = 0.994; see [VALIDATION.md](VALIDATION.md)).
- If a paper cites only the reference implementation and omits Taoka 2017, the
  methodological source is incomplete; if it cites only Taoka 2017 without the
  reference implementation, the exact implementation is not reproducible.
  Please cite both.

---

## 7. Dataset used in validation

The external validation cohort is the public UCLA Consortium for
Neuropsychiatric Phenomics LA5c Study, distributed as OpenNeuro dataset
`ds000030` (CC0 licence; accessed 2026-11-11):

- Poldrack RA, Congdon E, Triplett W, Gorgolewski KJ, Karlsgodt KH, Mumford JA,
  Sabb FW, Freimer NB, London ED, Cannon TD, Bilder RM. A phenome-wide
  examination of neural and cognitive function. *Scientific Data*.
  2016;3:160110. doi:10.1038/sdata.2016.110
- UCLA Consortium for Neuropsychiatric Phenomics LA5c Study. *OpenNeuro*.
  Dataset `ds000030`, version 1.0.0.
  doi:10.18112/openneuro.ds000030.v1.0.0
  (https://openneuro.org/datasets/ds000030)

The internal validation cohort is not redistributed (subject privacy); only
aggregate results are reported in [VALIDATION.md](VALIDATION.md). Per-subject
ALPS parameters were recorded by the tool in each `alps_result.json`; the full
experiment records are available from the authors on request.

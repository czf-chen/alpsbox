# ROI mask provenance and licence

The four ALPS ROI masks in this directory are **not original to ALPSbox**.
They were reproduced from the `ROIs_JHU_ALPS/` directory of the open-source
reference implementation **gbarisano/alps**:

- **Software**: Barisano G. *alps: Bash script to compute DTI-ALPS (alps.sh)*.
  GitHub repository. <https://github.com/gbarisano/alps>.
  Commit `e6f58e7c1b882a799b613e91fe15bab940dc4cd3` (2025-09-12).
  Accessed 2026-11-11. **MIT License**.
- **Companion paper** (required by that repository's README when using the
  script): Liu X, Barisano G, et al. Cross-vendor test-retest validation of
  diffusion tensor image analysis along the perivascular space (DTI-ALPS) for
  evaluating glymphatic system function. *Aging and Disease*.
  2024;15(4):1885-1898. doi:[10.14336/AD.2023.0321-2](https://doi.org/10.14336/AD.2023.0321-2)
- **Original ALPS method paper**: Taoka T, et al. Evaluation of glymphatic
  system activity with the diffusion MR technique: diffusion tensor image
  analysis along the perivascular space (DTI-ALPS) in Alzheimer's disease
  cases. *Japanese Journal of Radiology*. 2017;35(4):172-178.
  doi:[10.1007/s11604-017-0617-z](https://doi.org/10.1007/s11604-017-0617-z)
- **Full licence text**: see `LICENSE_Barisano_alps.txt` in the repository root
  (MIT License, Copyright (c) 2023 Giuseppe Barisano).

## Mask specification

| File | Anatomy | Voxels | sha256 |
|---|---|---|---|
| `L_SCR.nii.gz` | Left projection fibres (superior corona radiata) | 81 | `20c1ffd62c349aab3d2775735d46c2d6368a9fc50e567d5688721d164c28046c` |
| `R_SCR.nii.gz` | Right projection fibres (superior corona radiata) | 81 | `6389228ac11f5b1ea7233db82a66174a59ba3672c99d36b798de989a5243b199` |
| `L_SLF.nii.gz` | Left association fibres (superior longitudinal fasciculus) | 81 | `e487cad947663c311109bb15b5876b9e824f0ee6f25169c0f1b398cdc6eeb8c2` |
| `R_SLF.nii.gz` | Right association fibres (superior longitudinal fasciculus) | 81 | `79ef530240a88558339de1f1d84643700c77469da9b9d1c658a74ed80a389e15` |
| `all_ROIs.nii.gz` | All four merged (overlay preview only) | 324 | `8ac404733a32c9b97e293c78519b3f53eaafe63e9874b7eada20cb5d97d49e55` |

The masks are **2.5 mm radius spheres (= 5 mm diameter, matching Taoka 2017)**
in the space of FSL's `JHU-ICBM-FA-1mm.nii.gz` template. The reference
implementation changed its default ROI from 5 mm radius to 2.5 mm radius on
2025-05-28 (see the UPDATES section of its repository README).

## Source verification

- The reference-script copy used for verification (not distributed with this
  package) has git blob SHA `d48e29198d061b0dc496c68e0ed086da9fe8747c`,
  identical to `alps.sh` on the GitHub repository's `main` branch at commit
  `e6f58e7`.
- The cross-implementation comparison used that script with a
  **parameter-alignment patch** (`-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2`, with
  the registration cost patched to `normmi`); see the cross-implementation
  section of [docs/VALIDATION.md](../../../docs/VALIDATION.md).

## Requirement when publishing

If you use ALPSbox in research, please **also cite** the reference
implementation (software + companion paper) and the original ALPS method paper,
and state in your Methods section that the ROI masks come from
gbarisano/alps (MIT).

# Validation summary

[English](VALIDATION.md) | [简体中文](zh-CN/VALIDATION.md)

This page tells the validation story in the order we asked the questions:

1. **Is ALPSbox numerically the same measurement as the reference implementation?**
2. **What actually changes ALPS, and which factors matter most?**
3. **Does the quality control add useful information?**

All experimental parameters are listed in §5. The external validation cohort is
public data (OpenNeuro `ds000030`); the internal cohort is not redistributed
(subject privacy), but full per-experiment records are available from the
authors on request.

---

## 1. Same measurement as the reference implementation

**Claim: ALPSbox computes the established DTI-ALPS index, not a new algorithm.**

- The deterministic parts are identical to the parameter-matched reference
  implementation (`gbarisano/alps`, MIT): unringed DWI (md5), brain mask voxels,
  ROI masks (81 voxels each), ROI centroids, and the ALPS formula
  `mean(Dxx_proj, Dxx_asso) / mean(Dyy_proj, Dzz_asso)`.
- On **30 healthy controls from the fully external OpenNeuro ds000030**
  dataset, with processing parameters aligned (`-d 3 -e eddy_cuda11.0 -r 2.5
  -t 1 -f 2` in the reference script, registration cost patched to `normmi`):
  Pearson **r = 0.994**, **ICC = 0.994**, mean absolute difference **1.52%**;
  all 30 subjects within 5%.
- Eddy's own repeat-run variability on the same input is **2.04%** (max 4.11%
  across repeats), so the cross-implementation agreement is at the noise floor
  of the measurement. A same-subject parameter-aligned check gave a 0.70%
  difference, also inside this noise.

**Conclusion:** the number is the same measurement; differences from the
reference come from processing settings, not from a different formula.

---

## 2. What changes ALPS — ordered by importance

ALPS is a ratio of diffusion-tensor components after registration, so any
choice that changes the tensor, the mask or the registration changes the value.
In our experiments the practical importance is:

| # | Factor | Experiment | Observed effect on ALPS |
|---|---|---|---|
| 1 | **Registration route** (direct FA→template vs a two-step compound transform) | paired, 10 controls | median \|ΔALPS\| **16%**; registration quality worse in all 10 |
| 2 | **Brain-extraction threshold** `bet -f` 0.5 vs 0.3 | 24 controls; replicated on 15 external subjects | mean **11.2%**, median 6.7%, max **43.9%**; replication: low-`r_wm` group median 5.8% vs 1.3% |
| 3 | **Small registration-matrix errors** (the `--regqc` metric) | 24 controls, 12 perturbations of ±0.5° / ±0.5 mm | ALPS range **6.6–12.0%** |
| 4 | **Registration cost function** `normmi` vs `corratio` | 5 external subjects | mean \|ΔALPS\| **5.9%**, max 14.1% |
| 5 | **TOPUP distortion correction** on vs off | 1 subject with real PA/AP data | **−4.43%** (single subject; direction, not a generalisable magnitude) |
| 6 | **eddy non-determinism** (repeat runs of the same input) | 3 internal subjects | **2.04%** (max 4.11%) — the noise floor |

Reading the table from top to bottom is the practical message: **registration
choices matter most, then the brain-extraction threshold; eddy's repeat-run
noise is the smallest term and sets the resolution with which any difference
can be interpreted.**

This is why ALPSbox records the full processing definition in every
`alps_result.json`/report, and why it offers the registration-robustness QC
(`--regqc`): ALPS values are only comparable when the processing definition is
fixed and reported.

---

## 3. Does the quality control help?

**Claim: the QC checks identify subjects whose ALPS should not be trusted
without review.**

- Registration quality (`r_wm`, the FA–template correlation) predicts how
  sensitive a subject's ALPS is to preprocessing: in the 15-subject external
  replication, changing the `bet` threshold moved ALPS by a median of **5.8%**
  in the low-`r_wm` group vs **1.3%** in the high-`r_wm` group; correlation
  **r = −0.69**, and the partial correlation controlling for head motion is
  **−0.77**.
- `--regqc` measures registration sensitivity per subject directly: a subject
  whose ALPS changes 6–12% under a ±0.5° / ±0.5 mm perturbation cannot support
  fine-grained between-subject claims, whatever its ALPS value.
- The eight QC categories (registration quality, frame-wise motion, absolute
  drift, outlier slices, correction method, ROI voxel counts, ALPS
  plausibility, registration robustness; processing status is reported
  separately) turn these diagnostics into pass/info/caution/fail grades with
  actionable advice, so a whole cohort can be screened quickly.

**Conclusion:** QC is not decoration: it flags the subjects and settings that
change the answer.

---

## 4. What this means for users

- Use one fixed processing definition within a study and report it — every
  result file produced by ALPSbox records it.
- Keep `bet -f`, registration cost and template constant across subjects;
  report them in the methods section.
- Use `--regqc` (or at least `r_wm`) to identify registration-fragile subjects;
  do not compare ALPS values across different processing definitions or
  acquisition protocols without re-validation.
- The tool does not replace the reference implementation for pure replication
  runs; it makes the same measurement practical for cohorts (see
  [WHY_ALPSBOX.md](WHY_ALPSBOX.md)).

---

## 5. Experimental parameters

Unless stated otherwise, every experiment used the ALPSbox default processing
definition:

| Item | Setting |
|---|---|
| Data | 3T, single-shell DTI, b = 1000 s/mm² |
| Internal cohort | 1.5 mm isotropic, 64 directions, healthy controls |
| External cohort | OpenNeuro **ds000030**, 1.98 mm in-plane, healthy controls |
| Input | NIfTI DWI + bval/bvec + BIDS JSON sidecar |
| Distortion / motion correction | FSL `eddy` (CUDA build) with `--repol` |
| Gibbs unringing | MRtrix3 `mrdegibbs`; denoising (`dwidenoise`) off |
| Brain extraction | `bet -f 0.5` (FSL and reference-implementation default) |
| Tensor fit | `dtifit --save_tensor` (single tensor) |
| FA → template registration | FLIRT 12 DOF, cost `normmi`, target `JHU-ICBM-FA-1mm` |
| Tensor reorientation | `vecreg` (`T' = R·T·Rᵀ`) |
| ROI definition | bundled 2.5 mm-radius spheres (81 voxels each) |
| Software | ALPSbox 1.0.0, FSL 6.0.x, MRtrix3 (release current at the time) |

Every `alps_result.json` written by the tool records the effective definition
actually used for that subject (`bet_f`, `reg_cost`, `template`, `unring`,
`denoise`, eddy `method`), so a parameter table can be reconstructed from the
output itself.

| Experiment | n | Data | Deviations from the default definition |
|---|---|---|---|
| Reference implementation, same subject, parameters aligned | 4 | internal cohort | reference `alps.sh` run with `-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2`; its registration cost patched to `normmi`; ALPSbox side used defaults |
| Reference implementation, fully external cohort | 30 | ds000030 | same parameter-aligned reference run as above |
| Registration-route comparison (paired) | 10 | internal cohort | direct FA→template route vs a two-step compound transform; otherwise default |
| Registration-matrix sensitivity (`--regqc`) | 24 | internal cohort | 12 perturbations of ±0.5° / ±0.5 mm around the registration matrix |
| Brain-extraction threshold (`bet -f`) 0.5 vs 0.3 | 24 | internal cohort | only `bet -f` changed |
| Brain-extraction threshold, external replication | 15 | ds000030 | only `bet -f` changed; group split by `r_wm`; motion as covariate |
| Registration cost `normmi` vs `corratio` | 5 | external (ds000030) | only the FLIRT cost function changed |
| eddy non-determinism | 3 | internal cohort | identical inputs, repeated `eddy_cuda` runs |
| TOPUP on real PA/AP data | 1 | internal cohort | second opposite-phase-encoding DWI; TOPUP on vs off |

**Data availability.** The external cohort is the public OpenNeuro dataset
`ds000030` (CC0; citation in [CITATIONS.md](CITATIONS.md) §7). The internal
cohort is not redistributed for privacy reasons; aggregate results and every
experimental parameter are listed above, and full records are available from
the authors on request.

---

## 6. Scope and limitations

- Validation cohorts are single-site, 3T, single-shell (b = 1000), 1.5 mm
  (internal) and 1.98 mm (external) data. ALPS values are not comparable across
  protocols without explicit re-validation.
- The reference implementation was executed with parameter-alignment patches
  for the cross-implementation comparison; its default settings differ
  (`-f 1`, denoise+unring, corratio). See [CITATIONS.md](CITATIONS.md) §2.1.
- Group-level statistical analyses are intentionally outside the tool;
  validation used per-subject values only.
- The TOPUP comparison is a single subject; it indicates the direction and
  approximate size of the effect but is not a generalisable estimate.
- The reference implementation's own README notes that its default `eddy_cpu`
  path has larger run-to-run variability than the GPU path used here; small
  difference thresholds must therefore be interpreted carefully.

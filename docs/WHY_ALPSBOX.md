# Why ALPSbox?

[English](WHY_ALPSBOX.md) | [简体中文](zh-CN/WHY_ALPSBOX.md)

**Short answer**: numerically, ALPSbox agrees with the reference implementation
within eddy noise (0.70% on the same subject with aligned settings; r = 0.994 on
30 external subjects). The difference is in the workflow a study needs: the
reference implementation is a command-line script for one subject at a time,
while ALPSbox adds validated batch processing, quality control, a printable
report, and a recorded processing definition for every subject.

---

## 1. Numerical agreement

The most widely used open-source reference implementation for DTI-ALPS is
[gbarisano/alps](https://github.com/gbarisano/alps) (`alps.sh`, MIT, commit
`e6f58e7`). With parameters aligned (the reference script needs
`-d 3 -e eddy_cuda11.0 -r 2.5 -t 1 -f 2` plus a `normmi` cost patch; its default
settings are different, see [CITATIONS.md](CITATIONS.md) §2.1), the
deterministic intermediates are identical (unringed DWI, brain mask, ROI masks,
ROI voxel counts and the formula), and on 30 fully external subjects the
per-subject agreement is r = 0.994 (ICC 0.994, mean absolute difference 1.52%)
— inside eddy's own 2.04% repeat-run noise. This is the established DTI-ALPS
index, not a new algorithm; the details and all parameters are in
[VALIDATION.md](VALIDATION.md) §1.

## 2. What ALPSbox adds

| Dimension | ALPSbox | Reference implementation |
|---|---|---|
| GUI with automatic input discovery | yes | no |
| One-command, resumable batch over a cohort | yes | no (one subject per call) |
| QC across 8 categories, with grades and actionable warnings | yes | no |
| **Registration-robustness QC (`--regqc`)** | **yes** | no |
| One-click human-readable HTML report (printable to PDF) | yes | no (CSV only) |
| Processing definition recorded in every result | yes | no |
| Bilingual GUI / CLI / HTML reports (English / Chinese) | yes | no |
| Tensor reorientation with `vecreg` in the default route | yes | no (default `-f 1`) |
| Denoising / TOPUP | yes | yes |
| Group statistics | **no (by design)** | no |

On the default tensor route: transforming a diffusion tensor between spaces
requires reorientation, `T' = R·T·Rᵀ` (Alexander et al. 2001); Tatekawa et al.
2023 reported improved reproducibility when reorientation is used. ALPSbox
therefore uses `vecreg` by default, while the reference script's default is
`-f 1` (no reorientation); with `-f 2` the reference script does the same thing.
This is a documented difference in the processing definition, not a claim that
one tool is "more correct" — report whichever definition you use.

## 3. Reproducibility as a feature

For a study, the value is not only the ALPS number but knowing how it was
produced. Every subject's `alps_result.json` and HTML report record the
effective processing definition (`bet_f`, registration cost, template, unringing,
denoising, eddy method, ROI voxel counts, all QC values), and a finished cohort
can be re-summarised or re-reported without re-running the pipeline. Validation
numbers and the parameters of every validation experiment are listed in
[VALIDATION.md](VALIDATION.md).

## 4. What ALPSbox deliberately does not do

- It does not implement group comparisons or pre/post statistics. Export the
  per-subject CSV/JSON and use a statistics package; keeping the tool focused is
  the point.
- It does not claim to be an official or standard implementation; ALPS has no
  such standard. See [CITATIONS.md](CITATIONS.md) for terminology and citations.
- It does not replace FSL/MRtrix3; it orchestrates them and checks the results.

## 5. When the reference implementation may be the better choice

- You process a single subject on a machine where setting up Python packages is
  not worth it, and you are comfortable editing shell parameters.
- You need the reference script's exact default definition (`-f 1`, denoising +
  unringing, `corratio`) for a direct replication.
- You only need a CSV with the ALPS value and nothing else.

In those cases use `alps.sh`. ALPSbox is intended for running cohorts, checking
data quality, and keeping a reportable processing record.

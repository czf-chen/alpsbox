# Changelog

All notable public changes are documented here. The project starts its public
version history at v1.0.0; internal research iterations are not part of this
repository's history.

## [Unreleased]

### Documentation and platform support

- Quick start, installation guide, FAQ and in-app help now cover Linux and
  macOS as first-class platforms (native FSL, `bash run_gui.sh`, Tk/tkinter
  notes) instead of describing only the Windows/WSL path.
- `run_gui.sh` is marked executable in the repository, and the CLI's
  GUI-launch-failure hint now distinguishes WSL from native Linux/macOS.

## [1.0.0] — 2026-11-11

First public release.

### Core (per-subject processing)

- One-click pipeline per subject or per cohort: DICOM/NIfTI input → Gibbs
  unringing → eddy (GPU/CPU, with `--repol`) → bet → dtifit → FA→template
  registration (12 DOF) → **vecreg tensor reorientation** → ROI extraction →
  ALPS index.
- Batch mode with resumable runs; summary CSV and QC text generated automatically.
- Optional TOPUP distortion correction with a second (opposite phase-encoding) DWI.

### Quality control

- QC across eight categories of checks, with four grades
  (pass / info / caution / fail) and
  actionable advice: registration correlation `r_wm`, frame-wise motion,
  absolute drift, outlier slices, correction method, ROI voxel counts, ALPS
  plausibility, and a **registration-robustness metric (`--regqc`)** that the
  reference implementation does not provide.
- Configurable QC thresholds.

### Reports and exports

- Single-file HTML report with values, QC, interpretation and full citations
  (printable to PDF); the report follows the interface language.
- `alps_summary.csv`, per-subject `alps_result.json`, `qc_report.txt`.

### GUI and CLI

- Seven-page GUI (Home / Process / ROI map / Results / QC / Log / Help) with
  **language selection on the home page** (English default; Chinese available).
- Fully bilingual user-facing output (English / Chinese): interface, CLI output,
  processing logs, QC text and HTML reports. `--lang {auto,en,zh_CN}` is
  available on the CLI; the GUI follows the selected language.
- Help content with formal citations for every method.
- CLI: `check`, `dryrun`, `run`, `batch`, `rescan`, `report`, `gui`.

### Packaging and citation

- MIT-licensed code; bundled ROI masks reproduced under MIT from
  gbarisano/alps with provenance and sha256 checksums.
- `CITATION.cff`, `docs/CITATIONS.md`, per-method citations in code, GUI and report.

### Tests

- Unit tests that do not require FSL: input discovery, report rendering,
  citation/provenance audit, batch resume behaviour, GUI smoke tests.

# Changelog

All notable public changes are documented here. The project starts its public
version history at v1.0.0; internal research iterations are not part of this
repository's history.

## [Unreleased]

### TOPUP (dual phase encoding)

- TOPUP susceptibility-distortion correction is now available in the GUI as well
  as the CLI. Process page → Advanced → TOPUP: single-subject mode can auto-detect
  a reversed phase-encoding series or take a manually chosen second DWI; batch
  mode checks every subject folder automatically.
- Fixed: single-subject auto-detect now also finds the reversed series when
  the AP and PA exports sit in sibling folders (it looks at a few same-parent
  folders whose names match; the log names the sibling used). Batch mode keeps
  the strict inside-each-subject-folder rule to avoid cross-subject pairing.
- Fixed: the GUI "Check inputs" preflight read Tk variables from a worker
  thread; TOPUP settings are now resolved on the main thread before the worker
  starts.
- Fixed: a cached single-PE result is no longer reused when the input now has a
  reversed-PE series; it is reprocessed with TOPUP automatically.
- Fixed: switching the UI language while a job is running now keeps the log
  history, progress bars, elapsed time and the prepared input/output/advanced
  settings; previously the window was rebuilt empty and the running job looked
  frozen until the next progress message.
- New CLI options: `run --dwi2/--bval2/--bvec2/--json2` (explicit second set),
  `batch --topup-auto` (per-subject auto pairing) and `--topup-config` (use a
  TOPUP configuration other than FSL's automatically located b02b0.cnf).
  Passing `--dwi2` to batch is no longer silently ignored.
- GUI safety: "Check inputs" is now a required, highlighted step. Start is
  disabled until the current input/TOPUP settings pass preflight; changing the
  input folder, mode or TOPUP settings invalidates the check and disables Start
  again. The process page shows a coloured status banner (unchecked / checking /
  passed / warnings / failed), so organisational errors are caught before any
  processing starts.
- Batch safety: before processing, batch preflight now blocks a layout where
  one subject's AP/PA series are organized as two separate subject folders
  (clear error + `preflight_report.txt` + GUI/CLI log), and checks every TOPUP
  pair for a consistent b-value scheme, b-vectors, JSON acquisition metadata and
  image geometry. Inconsistent/mixed pairs are blocked with an explanation
  instead of being silently used or silently skipped. Nested AP/PA folders
  inside one subject folder remain valid and produce one result folder per
  subject. BIDS JSON has no patient identifiers, so identical-protocol data from
  different subjects cannot be distinguished automatically — this limitation is
  documented.
- TOPUP provenance is recorded in `alps_result.json` / `alps_summary.csv`
  (`topup`, `topup_config`), shown in the HTML report's processing definition,
  counted in the QC report and added to the GUI results table.
- Help pages, tooltips, README/FAQ (English and Chinese) document the dual-PE
  input format, GUI/CLI usage, parameters and troubleshooting; the TOPUP method
  citation (Andersson 2003) is included in the references.

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

# FAQ and troubleshooting

[English](FAQ.md) | [简体中文](zh-CN/FAQ.md)

---

## Before anything else

Run the environment check:

```bash
alpsbox check
```

It reports whether FSL, MRtrix3, dcm2niix and the required FSL tools are visible,
and prints the exact commands that are missing.

---

## Installation / environment

**`alpsbox: command not found`**
Install the package into the current environment (`pip install -e .` from the
repository) and reload the shell (`source ~/.bashrc`). If it still fails, check
the absolute path with `python -m alpsbox --help`.

**`FSLDIR not set` / `FSL not found`**
Source the FSL configuration file: `source $FSLDIR/etc/fslconf/fsl.sh`.
If FSL is installed in a non-default location, pass `--fsl-dir /path/to/fsl`.

**`mrdegibbs` not found**
MRtrix3 is optional. Unringing is skipped with a warning; ALPS values are still
produced but the processing definition differs. Install MRtrix3 if you need the
recommended default.

**Danger: MRtrix3's `bin` must not shadow system Python**
Some MRtrix3 distributions ship a `python3` binary. Put FSL's `bin` first in
`PATH`, and do not put MRtrix3's `bin` before `/usr/bin`. Otherwise ALPSbox may
run under a Python without `numpy`/`nibabel`.

---

## Input data

**"No DWI found"**
Each subject folder needs one matched set: `*.nii(.gz)` + same-named `.bval` +
same-named `.bvec`. The base names must match exactly. Subfolders are searched.

**Where do I enable TOPUP, and why was TOPUP skipped?**
TOPUP is for a second DWI with the opposite phase-encoding direction (AP + PA).
GUI: Process page → **Advanced → TOPUP** (single: auto-detect or choose the
second DWI; batch: automatic per-subject detection). Single-subject auto-detect
looks inside the selected folder first; if the AP and PA series were exported as
two sibling folders, it also checks a few sibling folders of the same parent
(when the names look like PE variants of one series) and logs which folder it
used. If the parent contains many subjects, select the parent folder containing
both series or choose the second DWI manually. Re-running a subject that was
previously processed without TOPUP is handled automatically: the stale
single-PE result is detected and reprocessed with TOPUP (no need to delete the
old result by hand).

**Why is the Start button disabled / why must I "Check inputs" first?**
The input check is a required, highlighted step. It only matches files and runs
no image processing, but it catches missing/mismatched inputs, TOPUP subject
layout errors (e.g. one subject's AP/PA split into two subject folders) and
inconsistent AP/PA pairs before any processing. Start is enabled only after the
check passes; changing the input folder, mode or TOPUP settings invalidates the
check. The process page shows a coloured status bar (unchecked / checking /
passed / warnings / failed).

**How must a TOPUP batch be organized?**
One immediate subfolder of the cohort root = one subject, and one subject gets
one result folder. Put both PE series inside that subject folder (e.g. `AP/` and
`PA/` subfolders, or the two series side by side). If two *subject* folders look
like the AP/PA series of one subject, batch preflight stops before processing and
writes `preflight_report.txt` with the reason — merge them into one subject
folder and rerun. Pair consistency (b-value scheme, b-vectors, JSON acquisition
metadata and image geometry) is checked; an obviously inconsistent/mixed pair is
blocked instead of being used. Note that BIDS JSON has no patient identifiers, so
two subjects with an identical protocol/geometry cannot be distinguished
automatically: the tool catches inconsistencies, not every mis-filed subject. CLI: `--dwi2/--bval2/
--bvec2/--json2` for `run`, `--topup-auto` for `batch`, `--topup-config` for a
custom `b02b0.cnf`. It is skipped when no reversed-PE series exists, when either
JSON lacks `PhaseEncodingDirection`/`TotalReadoutTime`, when both series use the
same direction, or when `b02b0.cnf` cannot be found. The log and the `topup`
column in `alps_summary.csv` / `alps_result.json` give the reason; the second set
must be NIfTI + `.bval` + `.bvec` + `.json` (convert DICOM with dcm2niix first).

**`TotalReadoutTime out of range`**
The BIDS sidecar must give `TotalReadoutTime` in seconds (typically 0.01–0.2).
Some converters write milliseconds; fix the JSON.

**`bvec columns != number of volumes`**
`bval`/`bvec` do not match the DWI. Run `alpsbox dryrun` to list mismatches.

**No `.json` sidecar**
Full `eddy` cannot run without `PhaseEncodingDirection`/`TotalReadoutTime`.
The tool falls back to `eddy_correct`, which has known biases; those subjects are
flagged in QC and should not be mixed with eddy-corrected subjects downstream.

---

## Processing

**eddy takes 10–20 minutes**
Normal. eddy dominates runtime (~80%). Threads do not help much; a CUDA GPU does.

**A run was interrupted**
Just start the same batch again: subjects with `alps_result.json` are skipped.
Use `--force` only when you want to recompute.

**`ROI voxel count != 81`**
The template-space registration failed or the data were resampled. Check
`FA_in_mni.nii.gz` and the QC page; if you intentionally use a custom ROI radius,
turn off the strict ROI-voxel check in the QC thresholds.

**Should I enable `--regqc`?**
For research use, yes: it quantifies how strongly ALPS depends on the
registration matrix (12 perturbations) and adds 1–2 minutes per subject. It is
the main QC dimension that ALPS values are usually reported without.

---

## Results

**Is my ALPS value "normal"?**
ALPS has no accepted diagnostic threshold. Reference values (~1.35–1.70 in
healthy adults, protocol-dependent) are shown for orientation only; always
report the processing parameters together with the values.

**Can I compare my values with published studies?**
Only if the acquisition and preprocessing match closely. bet threshold,
registration cost, template and ROI scheme all change ALPS by several percent
(and more in fragile subjects). The report records the parameters actually used.

**Can I run group statistics with this tool?**
No — this tool produces per-subject values and QC only. Export the CSV/JSON and
run group analyses downstream.

---

## GUI and launchers

**Double-clicking `ALPSbox-GUI.bat` shows "[ERROR] Could not resolve this
folder inside WSL" / "Could not find an accessible WSL distribution"**

This error appears when Windows cannot pass the launcher's folder path to a
working WSL distribution. Check in order:

1. `wsl -l -v` — is a distribution installed and in `Running`/`Stopped` state
   (not `Installing`)? If none: `wsl --install -d Ubuntu` (admin PowerShell,
   then reboot).
2. Is your distribution the default one? If not, either make it default
   (`wsl -s <name>`) or set `setx ALPSBOX_WSL_DISTRO <name>` once, then open a
   new window and double-click again. Common Ubuntu/Debian names are tried
   automatically; `<name>` must be exact (e.g. `Ubuntu-24.04`, no quotes).
3. Is the ALPSbox folder on a local drive? Network/UNC paths cannot always be
   converted to a WSL path; move the folder to `C:\...` or `D:\...`.
4. Make sure `run_gui.sh` is in the same folder as the `.bat` file.

The launcher also supports `set ALPSBOX_DRY_RUN=1` before launching: it then
only resolves the WSL path and exits (useful for diagnosis).

**How do I change the language?**
The tool starts in English (the default). Choose 简体中文 on the GUI home page
to switch the running session: the interface, processing log, QC text and the
generated HTML reports follow it. On the command line, add `--lang en` or
`--lang zh_CN` to any subcommand (the default is English).

**The GUI window does not appear (WSL)**
WSLg is required (Windows 11). Check `echo $DISPLAY`; if empty, use the CLI or
upgrade WSL.

**The GUI does not start on Linux or macOS**
On Linux a graphical session is required: `echo $DISPLAY` must print a value
(X11, or Wayland with XWayland). On macOS check that Python has Tk with
`python3 -c "import tkinter; print(tkinter.TkVersion)"`; the python.org installer
includes Tk, Homebrew Python needs the matching `python-tk` formula. When it
fails, `bash run_gui.sh` prints the log path and the FSL/Python it detected, and
the full launch log is `~/.alpsbox/gui.log`.

**The batch takes a long time on my laptop**
This is GPU/CPU-bound, not a bug. 66-volume data take roughly 10–15 min per
subject; 18-volume data are faster.

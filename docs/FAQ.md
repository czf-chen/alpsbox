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

## GUI and Windows launcher

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
upgrade WSL. On Linux a normal X/Wayland session is required.

**The batch takes a long time on my laptop**
This is GPU/CPU-bound, not a bug. 66-volume data take roughly 10–15 min per
subject; 18-volume data are faster.

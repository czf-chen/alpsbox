# Installation

ALPSbox is pure Python and runs on Windows (via WSL), Linux and macOS.
The only real constraint is **FSL**, which must be installed separately
(ALPSbox never bundles or redistributes it).

> 中文详细安装指南（含 Windows 逐步截图路径）：[zh-CN/INSTALL.md](zh-CN/INSTALL.md)

---

## 1. Requirements

| Component | Required | Purpose |
|---|---|---|
| Python 3.10+ | yes | runs ALPSbox; the Python dependencies (NumPy, nibabel, Pillow, matplotlib) are installed by `pip install -e .` |
| FSL 6.0.3+ | yes | eddy, bet, dtifit, flirt, vecreg, fslroi, fslmaths, fslstats, fslval |
| MRtrix3 | recommended | Gibbs unringing (`mrdegibbs`) |
| dcm2niix | optional | DICOM → NIfTI conversion |
| fslcc | recommended | registration quality QC (`r_wm`); ships with FSL |
| tkinter | GUI only | part of Python on Windows/macOS; on Linux `sudo apt install python3-tk` |

ALPSbox calls these programs; **it does not include FSL or MRtrix3**. The
Python dependencies are listed in `pyproject.toml` and `requirements.txt`.

---

## 2. Linux / WSL

### 2.1 Install FSL

```bash
# official installer (non-commercial licence)
wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/fslinstaller.py
python3 fslinstaller.py          # default: ~/fsl
source ~/fsl/etc/fslconf/fsl.sh
```

### 2.2 Install MRtrix3 (recommended)

```bash
conda create -n mrtrix3 -c conda-forge mrtrix3
conda activate mrtrix3
```

> Do **not** put MRtrix3's `bin` first in `PATH`: it ships its own `python3`
> which may shadow the system Python that ALPSbox needs.

### 2.3 Install ALPSbox

```bash
git clone https://github.com/czf-chen/alpsbox.git
cd alpsbox
pip install -e .            # installs the Python dependencies
# or, without installing the package: pip install -r requirements.txt
alpsbox check
```

`alpsbox check` verifies FSL, MRtrix3, dcm2niix and reports what is missing.

### 2.4 Start the GUI

```bash
bash run_gui.sh        # same launcher as on macOS; auto-detects FSL and MRtrix3
# or
alpsbox gui
```

The tool starts in English; the home page lets you switch to 简体中文 for the
running session (processing logs, QC text and HTML reports follow). On the
command line, `--lang en` / `--lang zh_CN` switches the language for that run.

WSLg (Windows 11) is required for the GUI on Windows; on Linux a normal X/Wayland
session is enough. Windows users can instead double-click `ALPSbox-GUI.bat`.
`run_gui.sh` is the no-hard-coded-paths launcher for Linux and macOS; the macOS
steps are in section 3.

---

## 3. macOS (Intel and Apple Silicon)

No WSL is needed: FSL, ALPSbox and the GUI run natively on macOS, on both Intel
and Apple Silicon Macs.

### 3.1 Install FSL

Use FSL's own installer (non-commercial licence; FSL is not distributed with
ALPSbox):

```bash
curl -Ls https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/getfsl.sh | sh -s
# wait for "FSL successfully installed", then close and reopen Terminal
fsl-config --version          # should print 6.0.3 or newer
```

If `fsl-config` is still not found after reopening Terminal, add this line to
`~/.zshrc` (FSLDIR defaults to `~/fsl`) and open a new terminal:

```bash
. $FSLDIR/etc/fslconf/fsl.sh
```

### 3.2 Python and tkinter

ALPSbox needs Python 3.10+ and, for the GUI, Tk. The python.org macOS installer
includes Tk; Homebrew Python does not, so install the matching `python-tk`
formula in that case. Verify with:

```bash
python3 --version
python3 -c "import tkinter; print(tkinter.TkVersion)"
```

### 3.3 Install ALPSbox

```bash
git clone https://github.com/czf-chen/alpsbox.git
cd alpsbox
python3 -m pip install -e .
alpsbox check
```

### 3.4 Start the GUI / CLI

```bash
bash run_gui.sh              # auto-detects FSL/MRtrix3; macOS needs no DISPLAY
# or
alpsbox gui
```

The CLI commands are identical to Linux (section 2.3).

### 3.5 Optional tools and performance

- MRtrix3 (`mrdegibbs`) is optional. The conda channels used in section 2.2 do
  not currently ship macOS builds; use the macOS binaries from
  <https://www.mrtrix.org/download/> (or build from source). If it is missing,
  unringing is skipped with a warning and the ALPS calculation is unaffected.
- `dcm2niix` is optional (`brew install dcm2niix`); it is only needed for DICOM
  input.
- There is no CUDA `eddy` on macOS, so `eddy` runs on the CPU and is roughly
  5–10× slower than a CUDA build. Everything else works identically.

---

## 4. Windows: double-click launcher and WSL setup

Native Windows is **not supported out of the box**: FSL does not provide a
Windows build. The supported path is WSL2 + WSLg (section 2). Once FSL and
`python3-tk` are installed inside WSL, start the GUI by double-clicking
`ALPSbox-GUI.bat` in the ALPSbox folder (any local drive).

The launcher converts its own folder to a WSL path and starts `run_gui.sh`
inside the default WSL distribution. It does not hard-code a distribution
name. If your Linux distribution is not the default one, do one of the
following once:

```bat
:: make it the default distribution
wsl -s Ubuntu-24.04

:: or tell only the launcher (open a new window afterwards)
setx ALPSBOX_WSL_DISTRO Ubuntu-24.04
wsl -l -v      REM list the exact names
```

Keep the launcher and `run_gui.sh` in the same folder. Do not close the black
console window while the GUI is running. The same GUI can also be started from
inside WSL with `bash run_gui.sh` or `alpsbox gui`.

---

## 5. Verify the install

```bash
alpsbox check                          # environment report
alpsbox gui                            # GUI smoke test
alpsbox run /path/to/sub_001 --out /tmp/demo_run   # real DWI input
```

The bundled `examples/demo_synthetic_cohort/` is synthetic data for trying the
GUI's result-import view only; it contains no DWI and is not for analysis.

---

## 6. Troubleshooting

See [FAQ.md](FAQ.md). The most common issues are:

- `alpsbox: command not found` — `pip install -e .` then `source ~/.bashrc`
- `FSLDIR not set` — `source ~/fsl/etc/fslconf/fsl.sh`
- `mrdegibbs` missing — MRtrix3 is optional; unringing is skipped with a warning
- GUI window does not appear — WSLg unavailable; use Windows 11 WSL or CLI
- `TotalReadoutTime out of range` — check the BIDS sidecar units (seconds, not ms)

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
alpsbox gui
```

The tool starts in English; the home page lets you switch to 简体中文 for the
running session (processing logs, QC text and HTML reports follow). On the
command line, `--lang en` / `--lang zh_CN` switches the language for that run.

WSLg (Windows 11) is required for the GUI on Windows; on Linux a normal X/Wayland
session is enough. Windows users can instead double-click `ALPSbox-GUI.bat`.

---

## 3. macOS

Install FSL with the FSL project's own installer (the `fslinstaller.py` script
from the FSL download page, see section 2.1); FSL is not distributed with
ALPSbox. MRtrix3 is available through Homebrew or conda. The GUI runs natively
on macOS. CUDA acceleration is not available, so `eddy` runs on CPU and is
roughly 5–10× slower than on a CUDA GPU; everything else works identically.

```bash
# FSL: use the FSL installer from section 2.1
brew install mrtrix 2>/dev/null        # MRtrix3 (recommended, optional)
git clone https://github.com/czf-chen/alpsbox.git
cd alpsbox && pip install -e . && alpsbox check && alpsbox gui
```

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

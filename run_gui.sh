#!/bin/bash
# =====================================================================
# ALPSbox GUI launcher
#
# Assumes nothing about where ALPSbox or FSL are installed: everything is
# auto-detected. Run directly:
#     bash run_gui.sh
# or let Windows call it through ALPSbox-GUI.bat.
#
# Log: ~/.alpsbox/gui.log
# =====================================================================

# ---- locate this script's directory (follow symlinks) ----
SELF="$0"
while [ -L "$SELF" ]; do
    DIR=$(cd -P "$(dirname "$SELF")" && pwd)
    SELF=$(readlink "$SELF")
    case "$SELF" in
        /*) ;;
        *) SELF="$DIR/$SELF" ;;
    esac
done
HERE=$(cd -P "$(dirname "$SELF")" && pwd)

LOG_DIR="$HOME/.alpsbox"
LOG="$LOG_DIR/gui.log"
mkdir -p "$LOG_DIR" 2>/dev/null

{
    echo "================================================================"
    echo "ALPSbox GUI start  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  whoami = $(whoami)"
    echo "  HERE   = $HERE"
    echo "  uname  = $(uname -srm)"
} >> "$LOG"

# ---- detect FSL ----
if [ -z "$FSLDIR" ]; then
    for cand in "$HOME/fsl" /usr/local/fsl /opt/fsl /opt/fsl-6.0.7 \
                "$HOME/fsl-6.0.7" /usr/share/fsl; do
        if [ -x "$cand/bin/eddy" ] || [ -f "$cand/etc/fslconf/fsl.sh" ]; then
            export FSLDIR="$cand"
            break
        fi
    done
fi
if [ -n "$FSLDIR" ] && [ -f "$FSLDIR/etc/fslconf/fsl.sh" ]; then
    # shellcheck disable=SC1090
    . "$FSLDIR/etc/fslconf/fsl.sh" 2>/dev/null
fi
[ -n "$FSLDIR" ] && export PATH="$FSLDIR/bin:$FSLDIR/share/fsl/bin:$PATH"
export FSLOUTPUTTYPE="${FSLOUTPUTTYPE:-NIFTI_GZ}"
echo "  FSLDIR = ${FSLDIR:-not found}" >> "$LOG"

# ---- detect MRtrix3 (optional) ----
if [ -z "$MRtrix3_HOME" ] && ! command -v mrdegibbs >/dev/null 2>&1; then
    for cand in "$HOME/mrtrix3" /usr/local/mrtrix3 /opt/mrtrix3 \
                "$HOME/miniforge3/envs/mrtrix"; do
        if [ -x "$cand/bin/mrdegibbs" ]; then
            export MRtrix3_HOME="$cand"
            export PATH="$cand/bin:$PATH"
            break
        fi
    done
fi
echo "  MRtrix3 = ${MRtrix3_HOME:-not found, unringing will be skipped}" >> "$LOG"

# ---- display (WSLg / X11 / macOS) ----
case "$(uname -s)" in
    Darwin)
        :   # macOS needs no DISPLAY
        ;;
    *)
        if [ -z "$DISPLAY" ] && [ -d /mnt/wslg ]; then
            export DISPLAY=:0
        fi
        ;;
esac
echo "  DISPLAY = ${DISPLAY:-not set (or not needed)}" >> "$LOG"

# ---- locate Python: prefer the local venv, then system ----
PY=""
for cand in "$HERE/.venv/bin/python3" "$(command -v python3)" \
            "$FSLDIR/bin/python3" "$FSLDIR/bin/python" \
            /usr/bin/python3 /opt/homebrew/bin/python3; do
    [ -z "$cand" ] && continue
    if "$cand" -c "import tkinter, numpy, nibabel" >/dev/null 2>&1; then
        PY="$cand"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "[error] no Python found with tkinter, numpy and nibabel." | tee -a "$LOG"
    echo "        On Linux:  sudo apt install -y python3-tk" | tee -a "$LOG"
    echo "        On macOS:  brew install python-tk" | tee -a "$LOG"
    exit 2
fi
echo "  PYTHON  = $PY" >> "$LOG"

# ---- make sure the package can be imported ----
if ! "$PY" -c "import alpsbox" >> "$LOG" 2>&1; then
    export PYTHONPATH="$HERE:$PYTHONPATH"
    if ! "$PY" -c "import alpsbox" >> "$LOG" 2>&1; then
        echo "[error] cannot import alpsbox. Install it first:" | tee -a "$LOG"
        echo "        cd $HERE && $PY -m pip install -e ." | tee -a "$LOG"
        echo "        full log: $LOG" | tee -a "$LOG"
        exit 4
    fi
fi

echo "Starting, please wait..."
"$PY" -m alpsbox gui 2>&1 | tee -a "$LOG"
RC=${PIPESTATUS[0]}

{
    echo "----------------------------------------------------------------"
    echo "GUI exit  code=$RC  $(date '+%H:%M:%S')"
} >> "$LOG"

if [ "$RC" != "0" ]; then
    echo ""
    echo "[startup failed] exit code $RC, last log lines:"
    tail -25 "$LOG"
fi
exit $RC

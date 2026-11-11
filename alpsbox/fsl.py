# -*- coding: utf-8 -*-
"""Thin wrappers around FSL commands: one subprocess path, logging, failure handling.

Note: "consistent with the reference implementation (gbarisano/alps)" in the
code comments means aligned with alps.sh of https://github.com/gbarisano/alps
(commit e6f58e7, MIT); see alpsbox/citations.py for the full citation.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from typing import Optional

from . import text_cli  # noqa: F401  (registers cli./misc. message keys)
from .i18n import t


class CommandError(RuntimeError):
    def __init__(self, cmd: list, returncode: int, log_path: Optional[str], tail: str = ""):
        self.cmd = cmd
        self.returncode = returncode
        self.log_path = log_path
        self.tail = tail
        super().__init__(
            t("misc.fsl.cmd_failed", returncode,
              " ".join(str(c) for c in cmd), log_path, tail))


@dataclass
class Runner:
    """Command runner that logs what it runs."""
    env: dict
    workdir: str
    log_path: str = ""
    verbose: bool = True
    _log_fh: Optional[object] = field(default=None, repr=False)

    def __post_init__(self):
        if self.log_path:
            os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
            self._log_fh = open(self.log_path, "a", encoding="utf-8")

    def close(self):
        if self._log_fh:
            self._log_fh.close()
            self._log_fh = None

    def _log(self, msg: str):
        if self.verbose:
            print(msg, flush=True)
        if self._log_fh:
            self._log_fh.write(msg + "\n")
            self._log_fh.flush()

    def run(self, cmd: list, check: bool = True, quiet: bool = False,
            timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Run a command; raise CommandError on failure."""
        os.makedirs(self.workdir, exist_ok=True)
        cmd_str = " ".join(str(c) for c in cmd)
        if not quiet:
            self._log("      $ " + cmd_str[:180])
        t0 = time.time()
        try:
            r = subprocess.run(
                [str(c) for c in cmd],
                cwd=self.workdir,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as e:
            raise CommandError(cmd, 127, self.log_path,
                               t("misc.fsl.exe_not_found", e))
        dt = time.time() - t0

        if self._log_fh:
            self._log_fh.write("--- CMD: %s\n" % cmd_str)
            if r.stdout:
                self._log_fh.write("--- STDOUT:\n%s\n" % r.stdout[-4000:])
            if r.stderr:
                self._log_fh.write("--- STDERR:\n%s\n" % r.stderr[-4000:])
            self._log_fh.flush()

        if r.returncode != 0:
            if check:
                tail = (r.stderr or r.stdout or "")[-800:]
                raise CommandError(cmd, r.returncode, self.log_path, tail)
            self._log(t("misc.fsl.exit_ignored", r.returncode))
        elif not quiet:
            self._log("        ok (%.1fs)" % dt)
        return r

    def capture(self, cmd: list, check: bool = True) -> str:
        """Run a command and return its stdout, stripped."""
        r = self.run(cmd, check=check, quiet=True)
        return (r.stdout or "").strip()


def fslval(runner: Runner, path: str, key: str) -> str:
    """Read one fslval entry."""
    return runner.capture([runner.env.get("FSLBOX_FSLVAL", "fslval"), path, key])


def n_volumes(runner: Runner, nii: str) -> int:
    """Number of volumes in a 4D image."""
    raw = fslval(runner, nii, "dim4")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        raise RuntimeError(t("misc.fsl.nvol_parse", raw))
    return int(digits)


def fslstats_mean(runner: Runner, nii: str) -> float:
    """Mean over the whole image (plain fslstats -M, no mask)."""
    out = runner.capture(["fslstats", nii, "-M"])
    return float(out.split()[0])


def fslstats_masked_mean(runner: Runner, vol: str, mask: str) -> float:
    """Non-zero mean inside a mask via -k (matches alps.sh of gbarisano/alps)."""
    out = runner.capture(["fslstats", vol, "-k", mask, "-m"])
    return float(out.split()[0])


def fslstats_voxels(runner: Runner, mask: str) -> int:
    """Number of voxels in a mask."""
    out = runner.capture(["fslstats", mask, "-V"])
    return int(float(out.split()[0]))

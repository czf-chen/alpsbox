# -*- coding: utf-8 -*-
"""acqp / index generation -- required inputs for a full eddy run.

acqp format expected by FSL eddy (FSL source: EddyHelperClasses.cpp:173-183):
    one line = "x y z readouttime"
    - pevec must be a unit axis vector (eddy does not support oblique phase encoding)
    - rotime must lie in [0.01, 0.2] seconds, otherwise it raises
      "AcqPara::AcqPara: Unrealistic read-out time"

Field sources: the BIDS sidecar json produced by dcm2niix
    PhaseEncodingDirection : "i"/"i-"/"j"/"j-"/"k"/"k-"
    TotalReadoutTime       : seconds
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from . import text_cli  # noqa: F401  (registers cli./misc. message keys)
from .i18n import t

# Hard limits imposed by FSL (hardcoded in the FSL source)
ROTIME_MIN = 0.01
ROTIME_MAX = 0.2

# BIDS -> unit axis vector
_PE_MAP = {
    "i": (1.0, 0.0, 0.0), "i-": (-1.0, 0.0, 0.0),
    "j": (0.0, 1.0, 0.0), "j-": (0.0, -1.0, 0.0),
    "k": (0.0, 0.0, 1.0), "k-": (0.0, 0.0, -1.0),
}


@dataclass
class AcqpResult:
    acqp_path: str
    index_path: str
    pe_vec: tuple
    rotime: float
    n_volumes: int


class AcqpError(ValueError):
    pass


def resolve_readout_time(info: dict) -> float:
    """Return TotalReadoutTime from the json sidecar, falling back to EffectiveEchoSpacing."""
    trt = info.get("TotalReadoutTime")
    if trt is not None:
        try:
            return float(trt)
        except (TypeError, ValueError):
            pass

    ees = info.get("EffectiveEchoSpacing")
    npe = info.get("ReconMatrixPE") or info.get("AcquisitionMatrixPE")
    if ees is not None and npe:
        # FSL convention: TRT = EES * (nPE - 1)
        return float(ees) * (float(npe) - 1.0)

    raise AcqpError(t("misc.acqp.no_trt"))


def parse_pe(info: dict) -> tuple:
    """Convert PhaseEncodingDirection to a unit axis vector."""
    ped = info.get("PhaseEncodingDirection")
    if not ped:
        raise AcqpError(t("misc.acqp.no_pe"))
    ped = str(ped).strip()
    if ped not in _PE_MAP:
        raise AcqpError(t("misc.acqp.bad_pe", ped))
    return _PE_MAP[ped]


def write_acqp_index(info: dict, n_volumes: int, out_dir: str,
                     prefix: str = "") -> AcqpResult:
    """Write acqp.txt and index.txt.

    Parameters
    ----------
    info : dict
        Contents of the BIDS sidecar.
    n_volumes : int
        Fourth dimension of the DWI series.
    out_dir : str
        Output directory.
    prefix : str
        Prefix for the file names, so that several subjects can share one
        directory.
    """
    vec = parse_pe(info)
    rotime = resolve_readout_time(info)

    if not (ROTIME_MIN <= rotime <= ROTIME_MAX):
        raise AcqpError(t("misc.acqp.rotime_range", rotime, ROTIME_MIN, ROTIME_MAX))

    if n_volumes <= 0:
        raise AcqpError(t("misc.acqp.bad_nvol", n_volumes))

    os.makedirs(out_dir, exist_ok=True)
    acqp = os.path.join(out_dir, prefix + "acqp.txt")
    index = os.path.join(out_dir, prefix + "index.txt")

    with open(acqp, "w") as fh:
        fh.write("%g %g %g %.9g\n" % (vec[0], vec[1], vec[2], rotime))
    with open(index, "w") as fh:
        fh.write("\n".join(["1"] * n_volumes) + "\n")

    return AcqpResult(acqp_path=acqp, index_path=index,
                      pe_vec=vec, rotime=rotime, n_volumes=n_volumes)

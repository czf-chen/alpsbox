# -*- coding: utf-8 -*-
"""Unit tests for TOPUP input pairing and provenance (no FSL needed).

Run directly (as CI does)::

    python tests/test_topup_pairing.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from alpsbox import i18n                       # noqa: E402
from alpsbox.batch import collect_jobs, preflight  # noqa: E402
from alpsbox.inputs import (DwiiInput, attach_explicit_second,  # noqa: E402
                            attach_second_from_nii, auto_attach_topup,
                            discover, discover_all, find_reversed_dwi)
from alpsbox.pipeline import (AlspPipeline, AlspResult,  # noqa: E402
                              PipelineOptions)

i18n.set_lang("en", save=False)

_FAILS = []


def check(cond, label):
    if cond:
        print("  OK   %s" % label)
    else:
        print("  FAIL %s" % label)
        _FAILS.append(label)


def make_set(folder, stem, pe):
    """Create a minimal NIfTI/bval/bvec/json DWI set (data content unused)."""
    os.makedirs(folder, exist_ok=True)
    nii = os.path.join(folder, stem + ".nii.gz")
    open(nii, "wb").close()
    with open(os.path.join(folder, stem + ".bval"), "w") as fh:
        fh.write("0 1000 1000\n")
    with open(os.path.join(folder, stem + ".bvec"), "w") as fh:
        fh.write("0 1 0\n0 0 1\n1 0 0\n")
    with open(os.path.join(folder, stem + ".json"), "w") as fh:
        json.dump({"PhaseEncodingDirection": pe, "TotalReadoutTime": 0.05}, fh)
    return nii


def test_discovery_and_pairing():
    print("== dual-PE discovery / pairing ==")
    with tempfile.TemporaryDirectory() as d:
        make_set(d, "dwi_AP", "j-")
        make_set(d, "dwi_PA", "j")
        primary = discover(d)
        all_sets = discover_all(d)
        check(len(all_sets) == 2, "both DWI sets discovered")
        second, why = find_reversed_dwi(primary, all_sets)
        check(second is not None, "opposite-PE candidate found")
        ok, why = auto_attach_topup(primary, d)
        check(ok, "auto pair attaches a usable TOPUP input")
        check(primary.has_dual_pe, "has_dual_pe is true after pairing")
        check(primary.pe_direction == "j-" and primary.pe_direction2 == "j",
              "opposite PE directions recorded")
        check(primary.check_dual_pe()[0], "check_dual_pe accepts the pair")

    print("== same-direction series are not used ==")
    with tempfile.TemporaryDirectory() as d:
        make_set(d, "dwi_AP1", "j-")
        make_set(d, "dwi_AP2", "j-")
        ok, why = auto_attach_topup(discover(d), d)
        check(not ok, "same-PE pair rejected")

    print("== single series is not an error ==")
    with tempfile.TemporaryDirectory() as d:
        make_set(d, "dwi_AP", "j-")
        ok, why = auto_attach_topup(discover(d), d)
        check(not ok, "single set -> TOPUP not applicable (no exception)")

    print("== manual second-set validation ==")
    with tempfile.TemporaryDirectory() as d:
        make_set(d, "dwi_AP", "j-")
        nii2 = make_set(d, "dwi_PA", "j")
        primary = discover(d)
        ok, why = attach_second_from_nii(primary, nii2)
        check(ok, "attach second NIfTI by path (same-stem bval/bvec found)")
        os.remove(os.path.join(d, "dwi_PA.bval"))
        primary2 = discover(d)
        ok, why = attach_second_from_nii(primary2, nii2)
        check(not ok, "missing same-stem bval is rejected")

    with tempfile.TemporaryDirectory() as d:
        make_set(d, "dwi_AP", "j-")
        nii2 = make_set(d, "dwi_PA", "j")
        primary = discover(d)
        ok, why = attach_explicit_second(
            primary, nii2, os.path.join(d, "dwi_PA.bval"),
            os.path.join(d, "dwi_PA.bvec"), os.path.join(d, "missing.json"))
        check(not ok, "explicit TOPUP files must exist (json missing)")


def test_batch_auto_pairing():
    print("== batch preflight auto pairing ==")
    with tempfile.TemporaryDirectory() as root:
        out = os.path.join(root, "out")
        make_set(os.path.join(root, "sub-01", "AP"), "dwi", "j-")
        make_set(os.path.join(root, "sub-01", "PA"), "dwi", "j")
        make_set(os.path.join(root, "sub-02"), "dwi", "j-")
        jobs = collect_jobs(root, out)
        good, bad = preflight(jobs, topup_auto=True)
        check(len(good) == 2 and not bad, "preflight finds both subjects")
        by_name = {j.subject: j for j in good}
        check(by_name["sub-01"].dwi.has_dual_pe,
              "auto pairing attaches the reversed series")
        check(not by_name["sub-02"].dwi.has_dual_pe,
              "single-PE subject stays single-PE")
        check("TOPUP" in by_name["sub-01"].topup,
              "batch job records the TOPUP status")
        jobs2 = collect_jobs(root, out)
        good2, _ = preflight(jobs2)  # default off
        check(all(not j.dwi.has_dual_pe for j in good2),
              "auto pairing is off by default")


class _FakeRunner:
    """Collect commands and create the fieldcoef file when topup 'runs'."""

    def __init__(self):
        self.cmds = []

    def run(self, argv, check=True, quiet=False):
        self.cmds.append(list(argv))
        if argv and argv[0] == "topup":
            for a in argv:
                if a.startswith("--out="):
                    open(a.split("=", 1)[1] + "_fieldcoef.nii.gz", "wb").close()
        return None


def test_pipeline_topup_step():
    print("== pipeline _maybe_topup (fake runner, no FSL) ==")
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        fsl = os.path.join(d, "fsl")
        cfgdir = os.path.join(fsl, "etc", "flirtsch")
        os.makedirs(cfgdir)
        cfg = os.path.join(cfgdir, "b02b0.cnf")
        open(cfg, "w").close()
        out = os.path.join(d, "out")
        os.makedirs(out)
        cur = os.path.join(d, "AP.nii.gz")
        nii2 = os.path.join(d, "PA.nii.gz")
        open(cur, "wb").close()
        open(nii2, "wb").close()
        dwi = DwiiInput(nii=cur, bval=cur.replace(".nii.gz", ".bval"),
                        bvec=cur.replace(".nii.gz", ".bvec"),
                        json_info={"PhaseEncodingDirection": "j-",
                                   "TotalReadoutTime": 0.05},
                        nii2=nii2, bval2="b2", bvec2="v2",
                        json_info2={"PhaseEncodingDirection": "j",
                                    "TotalReadoutTime": 0.05})
        pipe = AlspPipeline.__new__(AlspPipeline)
        pipe.env = SimpleNamespace(fsl_dir=fsl, mrtrix_has_dwidenoise=False,
                                   mrtrix_has_mrdegibbs=False)
        pipe.opts = PipelineOptions(unring=False, denoise=False)
        res = AlspResult(subject="s1")
        runner = _FakeRunner()
        prefix = pipe._maybe_topup(runner, dwi, cur, out, res)
        check(prefix is not None and prefix.endswith("my_topup_results"),
              "TOPUP returns the eddy --topup prefix")
        check(res.topup == "on", "result records topup=on")
        check(res.topup_config == "b02b0.cnf",
              "result records the b02b0.cnf basename")
        topup = [c for c in runner.cmds if c and c[0] == "topup"]
        check(len(topup) == 1, "topup command executed once")
        check(any(a.startswith("--config=") and a.endswith("b02b0.cnf")
                  for a in topup[0]), "topup uses the auto-detected config")
        check(any(a.startswith("--datain=") for a in topup[0]),
              "topup gets acqparams via --datain")

    # explicit config and missing-config behaviour
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "out")
        os.makedirs(out)
        cur = os.path.join(d, "AP.nii.gz")
        nii2 = os.path.join(d, "PA.nii.gz")
        open(cur, "wb").close()
        open(nii2, "wb").close()
        custom = os.path.join(d, "my_b02b0.cnf")
        open(custom, "w").close()
        dwi = DwiiInput(nii=cur, bval="b", bvec="v",
                        json_info={"PhaseEncodingDirection": "j-",
                                   "TotalReadoutTime": 0.05},
                        nii2=nii2, bval2="b2", bvec2="v2",
                        json_info2={"PhaseEncodingDirection": "j",
                                    "TotalReadoutTime": 0.05})
        pipe = AlspPipeline.__new__(AlspPipeline)
        pipe.env = SimpleNamespace(fsl_dir="", mrtrix_has_dwidenoise=False,
                                   mrtrix_has_mrdegibbs=False)
        pipe.opts = PipelineOptions(unring=False, denoise=False,
                                    topup_config=custom)
        res = AlspResult(subject="s2")
        runner = _FakeRunner()
        pipe._maybe_topup(runner, dwi, cur, out, res)
        topup = [c for c in runner.cmds if c and c[0] == "topup"]
        check(res.topup == "on" and res.topup_config == "my_b02b0.cnf",
              "explicit TOPUP config is used")
        check(any(a == "--config=" + custom for a in topup[0]),
              "topup command carries the explicit config")

        pipe.opts = PipelineOptions(unring=False, denoise=False,
                                    topup_config=os.path.join(d, "nope.cnf"))
        res2 = AlspResult(subject="s3")
        out2 = os.path.join(d, "out2")
        os.makedirs(out2)
        pipe._maybe_topup(_FakeRunner(), dwi, cur, out2, res2)
        check(str(res2.topup).startswith("skipped"),
              "missing explicit config is reported, not fatal")

    # no dual-PE input -> off
    with tempfile.TemporaryDirectory() as d:
        dwi = DwiiInput(nii=os.path.join(d, "x.nii.gz"), bval="b", bvec="v")
        pipe = AlspPipeline.__new__(AlspPipeline)
        pipe.env = SimpleNamespace(fsl_dir="", mrtrix_has_dwidenoise=False,
                                   mrtrix_has_mrdegibbs=False)
        pipe.opts = PipelineOptions(unring=False, denoise=False)
        res = AlspResult(subject="s4")
        prefix = pipe._maybe_topup(_FakeRunner(), dwi, dwi.nii, d, res)
        check(prefix is None and res.topup.startswith("off"),
              "no reversed-PE input -> TOPUP off")


def test_sibling_pairing():
    """AP/PA exports often sit in sibling folders; single mode searches them."""
    print("== sibling-folder auto pairing (single-subject exports) ==")
    with tempfile.TemporaryDirectory() as root:
        ap = os.path.join(root, "dMRI_AP_1.5mm")
        pa = os.path.join(root, "dMRI_PA_1.5mm")
        make_set(ap, "ap", "j-")
        make_set(pa, "pa", "j")
        primary = discover(ap)
        ok, why = auto_attach_topup(primary, ap)  # default: no sibling search
        check(not ok, "sibling search is off by default (batch mode)")
        primary = discover(ap)
        ok, why = auto_attach_topup(primary, ap, search_siblings=True)
        check(ok, "single-subject mode finds the reversed series in a sibling")
        check(primary.has_dual_pe, "paired primary has dual-PE input")
        check(any("sibling" in n for n in primary.notes),
              "a note records that the sibling folder was used")
        overlap = discover_all(pa)
        check(any(os.path.abspath(c.nii) == os.path.abspath(primary.nii2)
                  for c in overlap), "the attached series comes from the PA folder")

    # Too many subfolders -> refuse to guess (cohort-root safety)
    with tempfile.TemporaryDirectory() as root:
        ap = os.path.join(root, "dMRI_AP")
        pa = os.path.join(root, "dMRI_PA")
        make_set(ap, "ap", "j-")
        make_set(pa, "pa", "j")
        for i in range(4):
            make_set(os.path.join(root, "other_%d" % i), "dwi", "j-")
        primary = discover(ap)
        ok, why = auto_attach_topup(primary, ap, search_siblings=True)
        check(not ok, "large parent folders are not searched (wrong-subject risk)")
        check("subfolders" in why or "子文件夹" in why,
              "the reason explains why the sibling search was skipped")

    # Unrelated folder names are not paired even with an opposite PE direction
    with tempfile.TemporaryDirectory() as root:
        d1 = os.path.join(root, "series_01")
        d2 = os.path.join(root, "series_02")
        make_set(d1, "dwi", "j-")
        make_set(d2, "dwi", "j")
        ok, why = auto_attach_topup(discover(d1), d1, search_siblings=True)
        check(not ok, "unrelated folder names are not auto-paired")


def test_topup_aware_resume():
    """A cached single-PE result must not hide a now-available TOPUP input."""
    print("== TOPUP-aware resume ==")
    import alpsbox.pipeline as pm
    from types import SimpleNamespace

    class DummyRunner:
        def __init__(self, *a, **kw):
            pass

        def close(self):
            pass

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "out")
        os.makedirs(out)
        nii2 = os.path.join(d, "PA.nii.gz")
        open(nii2, "wb").close()
        dwi = DwiiInput(nii=nii2, bval="b", bvec="v", nii2=nii2,
                        bval2="b2", bvec2="v2",
                        json_info={"PhaseEncodingDirection": "j-"},
                        json_info2={"PhaseEncodingDirection": "j"})
        pipe = AlspPipeline.__new__(AlspPipeline)
        pipe.opts = PipelineOptions(unring=False)
        pipe.env = SimpleNamespace(fsl_dir="", mrtrix_has_dwidenoise=False,
                                   mrtrix_has_mrdegibbs=False)
        pipe.sub_env = None
        calls = []
        pipe._run_body = (lambda runner, subject, dwi, out_dir, res:
                          (calls.append(1), setattr(res, "ok", True))[0])
        with open(os.path.join(out, "alps_result.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"subject": "s1", "ok": True, "method": "eddy_gpu",
                       "topup": "off (no reversed-PE input)",
                       "alps_L": "1.0"}, fh)
        old_runner = pm.fslmod.Runner
        pm.fslmod.Runner = DummyRunner
        try:
            pipe.run("s1", dwi, out)
        finally:
            pm.fslmod.Runner = old_runner
        check(calls == [1], "cached single-PE result is reprocessed when TOPUP input appears")

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "out")
        os.makedirs(out)
        nii2 = os.path.join(d, "PA.nii.gz")
        open(nii2, "wb").close()
        dwi = DwiiInput(nii=nii2, bval="b", bvec="v", nii2=nii2,
                        bval2="b2", bvec2="v2",
                        json_info={"PhaseEncodingDirection": "j-"},
                        json_info2={"PhaseEncodingDirection": "j"})
        pipe = AlspPipeline.__new__(AlspPipeline)
        pipe.opts = PipelineOptions(unring=False)
        pipe.env = SimpleNamespace(fsl_dir="", mrtrix_has_dwidenoise=False,
                                   mrtrix_has_mrdegibbs=False)
        pipe.sub_env = None
        calls = []
        pipe._run_body = (lambda runner, subject, dwi, out_dir, res:
                          (calls.append(1), setattr(res, "ok", True))[0])
        with open(os.path.join(out, "alps_result.json"), "w",
                  encoding="utf-8") as fh:
            json.dump({"subject": "s2", "ok": True, "method": "eddy_gpu",
                       "topup": "on", "topup_config": "b02b0.cnf",
                       "alps_L": "1.0"}, fh)
        r = pipe.run("s2", dwi, out)
        check(calls == [], "cached TOPUP result is reused")
        check(r.method.endswith("(cached)") and r.topup == "on",
              "cached TOPUP provenance preserved")


def test_provenance_fields():
    print("== TOPUP provenance fields ==")
    r = AlspResult(subject="s1", ok=True, method="eddy_gpu",
                   topup="on", topup_config="b02b0.cnf")
    row = r.to_row()
    check(row.get("topup") == "on", "to_row records topup=on")
    check(row.get("topup_config") == "b02b0.cnf",
          "to_row records topup_config")
    back = AlspResult.from_record(row)
    check(back.topup == "on" and back.topup_config == "b02b0.cnf",
          "from_record restores TOPUP provenance")
    check("topup_config" in PipelineOptions.__dataclass_fields__,
          "PipelineOptions has topup_config")
    check("topup" in AlspResult.FIELDS and "topup_config" in AlspResult.FIELDS,
          "FIELDS include TOPUP columns")


def test_cli_help():
    print("== CLI options ==")
    env = dict(os.environ, PYTHONPATH=ROOT)
    run_help = subprocess.run(
        [sys.executable, "-m", "alpsbox", "--lang", "en", "run", "--help"],
        cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    batch_help = subprocess.run(
        [sys.executable, "-m", "alpsbox", "--lang", "en", "batch", "--help"],
        cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    out = (run_help.stdout or "") + (run_help.stderr or "")
    bout = (batch_help.stdout or "") + (batch_help.stderr or "")
    check("--dwi2" in out and "--json2" in out,
          "run --help lists explicit TOPUP files")
    check("--topup-auto" in out and "--topup-config" in out,
          "run --help lists TOPUP switches")
    check("--topup-auto" in bout and "--topup-config" in bout,
          "batch --help lists TOPUP switches")
    check("--dwi2" not in bout,
          "batch --help does not advertise per-file --dwi2 (auto pairing only)")


def main():
    test_discovery_and_pairing()
    test_batch_auto_pairing()
    test_sibling_pairing()
    test_pipeline_topup_step()
    test_topup_aware_resume()
    test_provenance_fields()
    test_cli_help()
    print()
    if _FAILS:
        print("RESULT: FAIL (%d)" % len(_FAILS))
        for f in _FAILS:
            print("  !", f)
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

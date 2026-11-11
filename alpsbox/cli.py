# -*- coding: utf-8 -*-
"""Command-line entry point.

Usage examples
--------------
    # environment check
    alpsbox check

    # single subject
    alpsbox run /path/to/sub_001 --out ./results/sub_001

    # batch (one subject per sub-directory of the root directory)
    alpsbox batch /path/to/cohort --out ./results --workers 1

    # only check that inputs can be found, without processing
    alpsbox dryrun /path/to/cohort

Citations and third-party sources
---------------------------------
ALPS method: Taoka T, et al. Japanese Journal of Radiology.
2017;35(4):172-178. doi:10.1007/s11604-017-0617-z

The "reference implementation" refers specifically to the open-source
repository gbarisano/alps; "official alps.sh" is an older documentation
name for it (https://github.com/gbarisano/alps, commit e6f58e7, 2025-09-12,
MIT License); the companion paper it requires: Liu X, Barisano G, et al.
Aging and Disease. 2024;15(4):1885-1898. doi:10.14336/AD.2023.0321-2
(ALPS has no official standard implementation; this tool neither bundles
nor modifies that repository's code; the ROI masks shipped with this package
are copied from it, MIT License).
Full citations are in the repository's CITATION.cff, docs/CITATIONS.md,
alpsbox/data/ROIs_JHU_ALPS/PROVENANCE.md and the GUI Help > References page.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time

from . import __version__
from . import i18n, text_cli  # noqa: F401  (text_cli registers the cli./misc. strings)
from .batch import (collect_jobs, collect_results, preflight, run_batch,
                    write_qc_report, write_summary)
from .config import detect_env
from .i18n import t
from .inputs import discover
from .pipeline import AlspPipeline, PipelineOptions
from .roi import DEFAULT_RADIUS_MM

# Accepted --lang values; auto follows the saved preference and the system
# language (without writing a preference)
_LANG_CHOICES = ("auto", "en", "zh_CN")


def _add_common(p: argparse.ArgumentParser):
    p.add_argument("--fsl-dir", default=None, help=t("cli.opt.fsl_dir"))
    p.add_argument("--threads", type=int, default=4,
                   help=t("cli.opt.threads"))
    p.add_argument("--no-unring", action="store_true",
                   help=t("cli.opt.no_unring"))
    p.add_argument("--denoise", action="store_true",
                   help=t("cli.opt.denoise"))
    p.add_argument("--bet-f", type=float, default=0.5,
                   help=t("cli.opt.bet_f"))
    p.add_argument("--reg-cost", "--cost", dest="reg_cost",
                   default="normmi",
                   choices=["normmi", "corratio", "mutualinfo", "ratiosquare"],
                   help=t("cli.opt.reg_cost"))
    # T1-assisted path is kept for internal comparisons only: it parses but is
    # not listed in --help or the docs.
    p.add_argument("--t1", default=None, help=argparse.SUPPRESS)
    p.add_argument("--t1-mat", dest="t1_mat", default=None,
                   help=argparse.SUPPRESS)
    p.add_argument("--regqc", action="store_true",
                   help=t("cli.opt.regqc"))
    # ---- optional: second DWI with reversed phase encoding, for TOPUP ----
    p.add_argument("--dwi2", default=None,
                   help=t("cli.opt.dwi2"))
    p.add_argument("--bval2", default=None, help=t("cli.opt.bval2"))
    p.add_argument("--bvec2", default=None, help=t("cli.opt.bvec2"))
    p.add_argument("--json2", default=None, help=t("cli.opt.json2"))
    p.add_argument("--radius", type=float, default=DEFAULT_RADIUS_MM,
                   help=t("cli.opt.radius"))
    p.add_argument("--no-bundled-roi", "--no-official-roi",
                   dest="no_bundled_roi", action="store_true",
                   help=t("cli.opt.no_bundled_roi"))
    p.add_argument("--custom-rois", default=None,
                   help=t("cli.opt.custom_rois"))
    p.add_argument("--template", default=None,
                   help=t("cli.opt.template"))
    p.add_argument("--no-html", action="store_true",
                   help=t("cli.opt.no_html"))
    p.add_argument("--force", action="store_true",
                   help=t("cli.opt.force"))


def cmd_check(args) -> int:
    env = detect_env(args.fsl_dir, verbose=True)
    if not env.ok:
        print(t("cli.check.bad"))
        return 1
    print(t("cli.check.ok"))
    return 0


def cmd_dryrun(args) -> int:
    env = detect_env(args.fsl_dir, verbose=True)
    jobs = collect_jobs(args.root, args.out)
    print(t("cli.dryrun.found", len(jobs)))
    good, bad = preflight(jobs)
    print("=" * 68)
    print(t("cli.dryrun.header"))
    print("=" * 68)
    for j in good:
        print("\n  [OK] %s" % j.subject)
        print(j.dwi.describe())
    for j in bad:
        print("\n  [FAIL] %s" % j.subject)
        print("         %s" % j.error.replace("\n", "\n         "))
    print(t("cli.dryrun.summary", len(good), len(jobs)))
    return 0 if not bad else 2


def _make_opts(args) -> PipelineOptions:
    custom = None
    if args.custom_rois:
        custom = [x.strip() for x in args.custom_rois.split(",") if x.strip()]
    return PipelineOptions(
        radius=args.radius,
        unring=not args.no_unring,
        denoise=getattr(args, "denoise", False),
        regqc=getattr(args, "regqc", False),
        bet_f=float(getattr(args, "bet_f", 0.5)),
        reg_cost=getattr(args, "reg_cost", "normmi"),
        t1=getattr(args, "t1", None),
        t1_mat=getattr(args, "t1_mat", None),
        use_bundled_roi=not args.no_bundled_roi,
        custom_rois=custom,
        threads=args.threads,
        template=args.template,
        force=args.force,
    )


def _numpy_ok() -> bool:
    try:
        import numpy  # noqa: F401
        return True
    except Exception:
        return False


def _warn_numpy_missing() -> None:
    """Explain clearly when the interpreter lacks numpy (a common cause is
    another python3 shadowing the intended one on PATH)."""
    if _numpy_ok():
        return
    print(t("cli.numpy.warn", sys.executable))


def cmd_run(args) -> int:
    _warn_numpy_missing()
    env = detect_env(args.fsl_dir, verbose=False)
    if not env.ok:
        print(env.summary())
        return 1
    print(env.summary())

    try:
        dwi = discover(args.subject_dir)
    except Exception as e:
        print(t("cli.err.discover", e))
        return 2

    # Optional: attach the reversed phase-encoding dataset (for TOPUP)
    if getattr(args, "dwi2", None):
        from .inputs import read_json_info as _rji
        dwi.nii2 = args.dwi2
        dwi.bval2 = args.bval2
        dwi.bvec2 = args.bvec2
        dwi.json2 = args.json2
        if args.json2:
            try:
                dwi.json_info2 = _rji(args.json2)
            except Exception as e:
                print(t("cli.warn.read_json", args.json2, e))
        ok, why = dwi.check_dual_pe()
        print(t("cli.dual.header", os.path.basename(args.dwi2)))
        print("  TOPUP: %s" % (t("cli.dual.on", why) if ok
                               else t("cli.dual.off") + why))

    name = args.name or os.path.basename(os.path.normpath(args.subject_dir))
    out = args.out or os.path.join("alps_results", name)

    print(t("cli.run.subject", name))
    print(dwi.describe())

    pipe = AlspPipeline(env, _make_opts(args))
    r = pipe.run(name, dwi, out)
    print("\n" + "=" * 68)
    print(r.summary())
    print("=" * 68)
    print(t("cli.run.outdir", os.path.abspath(out)))

    # Build the single-subject report automatically and print the verdict
    if r.ok and not getattr(args, "no_html", False):
        try:
            from . import report as _report
            jp = os.path.join(out, "alps_result.json")
            if os.path.isfile(jp):
                hp = os.path.join(out, "report.html")
                _report.build_from_result_json(jp, hp)
                it = _report.interpret(json.load(open(jp, encoding="utf-8")))
                print("\n" + "-" * 68)
                print(t("cli.run.verdict", it["verdict"]))
                print("-" * 68)
                for ln in it["lines"]:
                    print(" " + ln)
                print(t("cli.run.report", os.path.abspath(hp)))
        except Exception as e:
            print(t("cli.warn.report", e))
    return 0 if r.ok else 3


def cmd_batch(args) -> int:
    _warn_numpy_missing()
    env = detect_env(args.fsl_dir, verbose=False)
    if not env.ok:
        print(env.summary())
        return 1
    print(env.summary())

    jobs = collect_jobs(args.root, args.out)
    if not jobs:
        print(t("cli.err.no_subdirs", args.root))
        return 2
    n_found = len(jobs)
    print(t("cli.batch.found", n_found))

    # Resume support: subjects with existing results may be skipped (unless --force)
    done = []
    if not args.force:
        done = [j for j in jobs
                if os.path.isfile(os.path.join(j.out_dir, "alps_result.json"))]
        if done and not args.no_resume:
            print(t("cli.batch.skipped", len(done)))
            jobs = [j for j in jobs if j not in done]

    os.makedirs(args.out, exist_ok=True)
    csv_path = os.path.join(args.out, "alps_summary.csv")
    qc_path = os.path.join(args.out, "qc_report.txt")

    good, bad = preflight(jobs)
    print(t("cli.batch.preflight", len(good), len(bad)))
    for j in bad:
        print(t("cli.batch.skip_row", j.subject,
                j.error.split("\n")[0][:80]))

    if not good:
        # Resume re-entry: every subject is already done -- do not fail, just
        # rebuild the summary table
        if done and len(done) == n_found:
            all_results = collect_results(args.out, [])
            write_summary(all_results, csv_path)
            report = write_qc_report(all_results, qc_path)
            print("\n" + "=" * 68)
            print(t("cli.batch.all_done", n_found))
            print("=" * 68)
            print(report)
            print(t("cli.batch.csv", os.path.abspath(csv_path)))
            print(t("cli.batch.qc", os.path.abspath(qc_path)))
            return 0
        print(t("cli.err.no_good"))
        return 2

    t0 = time.time()
    results = run_batch(good, env, _make_opts(args),
                        workers=args.workers)
    dt = time.time() - t0

    # Save: merge this run's results with those already in the output directory
    # so earlier subjects do not drop out of the summary after a resume
    all_results = collect_results(args.out, results)
    write_summary(all_results, csv_path)
    report = write_qc_report(all_results, qc_path)

    print("\n" + "=" * 68)
    print(t("cli.batch.done", dt / 60))
    print("=" * 68)
    print(report)
    print(t("cli.batch.csv_n", os.path.abspath(csv_path),
            len(all_results)))
    print(t("cli.batch.qc", os.path.abspath(qc_path)))

    # Generate the HTML report automatically
    if not getattr(args, "no_html", False):
        try:
            from . import report as _report
            recs = []
            for p in sorted(glob.glob(os.path.join(args.out, "*",
                                                   "alps_result.json"))):
                try:
                    recs.append(json.load(open(p, encoding="utf-8")))
                except Exception:
                    pass
            if recs:
                hp = os.path.join(args.out, "report.html")
                _report.build_batch_html(recs, hp)
                print(t("cli.batch.report", os.path.abspath(hp)))
        except Exception as e:
            print(t("cli.warn.report", e))
    return 0


def cmd_rescan(args) -> int:
    """Recompute QC metrics from existing eddy output without re-running processing."""
    from . import rescan

    root = args.root
    if not os.path.isdir(root):
        print(t("cli.err.no_dir", root))
        return 2

    print("=" * 68)
    print(t("cli.rescan.header", os.path.abspath(root)))
    print("=" * 68)

    stats = rescan.scan(root)
    if not stats:
        print(t("cli.rescan.none"))
        return 3

    print(rescan.summary_table(stats))

    if args.json:
        n_json, n_row = 0, 0
        for s in stats:
            d = os.path.join(root, s.subject)
            if rescan.update_result_json(d, s, backup=not args.no_backup):
                n_json += 1
            if rescan.update_row_txt(d, s, backup=not args.no_backup):
                n_row += 1
        if n_json:
            print(t("cli.rescan.json_updated", n_json))
        if n_row:
            print(t("cli.rescan.row_updated", n_row))
        if not n_json and not n_row:
            print(t("cli.rescan.nothing"))

    if args.tsv:
        if not os.path.isfile(args.tsv):
            print(t("cli.rescan.tsv_missing", args.tsv))
        else:
            out = args.tsv_out or args.tsv
            try:
                rescan.update_tsv(args.tsv, stats, out)
                print(t("cli.rescan.tsv_written", os.path.abspath(out)))
            except Exception as e:
                print(t("cli.err.tsv_write", e))

    if not args.json and not args.tsv:
        print(t("cli.rescan.scan_only"))
    return 0


def cmd_report(args) -> int:
    """Build HTML reports (single subject or whole batch) in one step; they can
    be printed to PDF straight from the browser."""
    if not _numpy_ok():
        _warn_numpy_missing()
        print(t("cli.err.report_numpy"))
        return 1
    from . import report

    root = args.root
    if not os.path.isdir(root):
        print(t("cli.err.no_dir", root))
        return 2

    # A single-subject directory? Or a results root directory?
    single = os.path.join(root, "alps_result.json")
    if os.path.isfile(single):
        out = args.out or os.path.join(root, "report.html")
        images = {}
        # Collect the images sitting next to the result file
        for nm, cap in (("roi_view.png", t("cli.report.cap_roi")),
                        ("motion.png", t("cli.report.cap_motion"))):
            p = os.path.join(root, nm)
            if os.path.isfile(p):
                images[cap] = p
        p = report.build_from_result_json(single, out, images=images)
        print(t("cli.report.single", os.path.abspath(p)))
        return 0

    # Batch mode
    import glob
    import json
    js = sorted(glob.glob(os.path.join(root, "*", "alps_result.json")))
    if not js:
        print(t("cli.err.no_result_json", root))
        return 3
    recs = []
    for p in js:
        try:
            recs.append(json.load(open(p, encoding="utf-8")))
        except Exception as e:
            print(t("cli.report.skip_row", p, e))
    out = args.out or os.path.join(root, "batch_report.html")
    p = report.build_batch_html(recs, out)
    print(t("cli.report.batch", os.path.abspath(p), len(recs)))
    return 0


def _in_wsl() -> bool:
    """Return True when running inside Windows Subsystem for Linux."""
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        with open("/proc/version", encoding="utf-8", errors="ignore") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def cmd_gui(args) -> int:
    """Launch the graphical interface."""
    try:
        from .gui import main as gui_main
    except ImportError as e:
        print(t("cli.err.gui_import", e))
        print(t("cli.gui.tk_hint"))
        return 1
    try:
        code = getattr(args, "lang", "auto")
        gui_main(None if code in (None, "auto") else code)
    except Exception as e:
        print(t("cli.err.gui_start", e))
        if _in_wsl():
            print(t("cli.gui.wsl_hint"))
        else:
            print(t("cli.gui.display_hint"))
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="alpsbox",
        description=t("cli.description", __version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=t("cli.epilog"),
    )
    ap.add_argument("--version", action="version", version="alpsbox %s" % __version__)
    ap.add_argument("--lang", choices=_LANG_CHOICES, default="auto",
                    help=t("cli.opt.lang"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("gui", help=t("cli.cmd.gui"))
    p.set_defaults(func=cmd_gui)

    p = sub.add_parser("check", help=t("cli.cmd.check"))
    _add_common(p)
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("dryrun", help=t("cli.cmd.dryrun"))
    p.add_argument("root", help=t("cli.arg.root_batch"))
    p.add_argument("--out", default="alps_results")
    _add_common(p)
    p.set_defaults(func=cmd_dryrun)

    p = sub.add_parser("run", help=t("cli.cmd.run"))
    p.add_argument("subject_dir", help=t("cli.arg.subject_dir"))
    p.add_argument("--out", default=None, help=t("cli.arg.out"))
    p.add_argument("--name", default=None, help=t("cli.arg.name"))
    _add_common(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("batch", help=t("cli.cmd.batch"))
    p.add_argument("root", help=t("cli.arg.batch_root"))
    p.add_argument("--out", default="alps_results")
    p.add_argument("--workers", type=int, default=1,
                   help=t("cli.arg.workers"))
    p.add_argument("--no-resume", action="store_true",
                   help=t("cli.arg.no_resume"))
    _add_common(p)
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("rescan", help=t("cli.cmd.rescan"))
    p.add_argument("root", help=t("cli.arg.rescan_root"))
    p.add_argument("--json", action="store_true",
                   help=t("cli.arg.json"))
    p.add_argument("--tsv", default=None, help=t("cli.arg.tsv"))
    p.add_argument("--tsv-out", default=None,
                   help=t("cli.arg.tsv_out"))
    p.add_argument("--no-backup", action="store_true",
                   help=t("cli.arg.no_backup"))
    p.set_defaults(func=cmd_rescan)

    p = sub.add_parser("report", help=t("cli.cmd.report"))
    p.add_argument("root", help=t("cli.arg.report_root"))
    p.add_argument("--out", default=None, help=t("cli.arg.out_html"))
    p.set_defaults(func=cmd_report)

    # Also accept --lang after the subcommand: the language was already decided
    # during the main() prescan, so this only keeps argparse from complaining
    # (it never overrides the language already set).
    for _sp in sub.choices.values():
        _sp.add_argument("--lang", choices=_LANG_CHOICES,
                         default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    return ap


def _prescan_lang(argv=None) -> str:
    """Determine the language before the parser is built so that --help and
    error messages use the same language.

    auto (the default) follows the saved preference and the system language
    without writing a user preference; an explicit --lang only affects the
    current run and likewise does not write a preference.
    """
    raw = list(sys.argv[1:] if argv is None else argv)
    code = None
    for i, a in enumerate(raw):
        if a == "--lang" and i + 1 < len(raw):
            code = raw[i + 1]
        elif a.startswith("--lang="):
            code = a.split("=", 1)[1]
    if code and code != "auto" and code in i18n.LANGS:
        i18n.set_lang(code, save=False)
    else:
        i18n.init_lang()
    return i18n.get_lang()


def main(argv=None) -> int:
    _prescan_lang(argv)
    ap = build_parser()
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

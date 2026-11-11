# -*- coding: utf-8 -*-
"""Generate a synthetic demo cohort for the "Import results" button.

Outputs
-------
examples/demo_synthetic_cohort/
    README.md
    demo_synthetic_summary.csv          <- import this file in the GUI
    demoA_01/eddy_out.eddy_movement_rms
    demoA_01/eddy_out.eddy_outlier_report
    ...

All values are produced by this script with a fixed random seed; none of them
belong to a real subject.
"""
import csv
import os
import random
import math

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "examples", "demo_synthetic_cohort")

N_VOL = 40
SLICES = 88

# Subjects: (ID, group name, scenario)
# The scenario determines motion shape and QC metrics, so that different QC
# grades can be demonstrated.
SUBJECTS = [
    ("demoA_01", "groupA", "clean"),
    ("demoA_02", "groupA", "clean"),
    ("demoA_03", "groupA", "jittery"),
    ("demoA_04", "groupA", "clean"),
    ("demoA_05", "groupA", "drift"),
    ("demoB_01", "groupB", "clean"),
    ("demoB_02", "groupB", "badreg"),
    ("demoB_03", "groupB", "clean"),
    ("demoB_04", "groupB", "outliers"),
    ("demoB_05", "groupB", "clean"),
]


def gen_motion(scn: str, rng: random.Random):
    """Return (absolute displacement, relative displacement) series.

    The shape follows real eddy output: most subjects settle in one position
    during the first one or two volumes and then keep a small random walk of a
    few tens to a few hundred micrometres. Units: millimetres.
    """
    if scn == "drift":
        base = rng.uniform(0.15, 0.25)
        step = 0.012
        slope = 0.050          # pushes abs_mean above 1.0 -> "large drift"
    elif scn == "jittery":
        base = rng.uniform(0.25, 0.40)
        step = 0.010
        slope = 0.0
    else:
        base = rng.uniform(0.18, 0.45)
        step = 0.012
        slope = 0.0

    absv = [0.0]
    settle_at = rng.choice((2, 3))
    for i in range(1, N_VOL):
        if i == settle_at:
            v = base                      # settling motion
        elif i < settle_at:
            v = base * i / settle_at
        else:
            v = absv[-1] + rng.gauss(0, step)
            if scn == "drift":
                v += slope
            if scn == "jittery" and i in (9, 10, 11, 26, 27):
                v += rng.uniform(0.60, 0.90)   # large enough to trigger the jitter threshold
            if scn == "jittery" and i in (12, 28):
                v -= rng.uniform(0.55, 0.80)
        absv.append(max(0.0, v))

    rel = [0.0]
    for i in range(1, N_VOL):
        d = abs(absv[i] - absv[i - 1])
        rel.append(max(0.0, d + abs(rng.gauss(0, 0.010))))
    return absv, rel


def gen_outliers(scn: str, rng: random.Random):
    """Return [(scan, slice), ...]; scan is 1-based."""
    out = []
    if scn == "outliers":
        vols = rng.sample(range(2, N_VOL + 1), 12)
        for v in vols:
            for s in rng.sample(range(1, SLICES + 1), rng.randint(1, 3)):
                out.append((v, s))
    elif scn == "jittery":
        for v in (10, 11, 26):
            out.append((v, rng.randint(10, 70)))
    else:
        # Clean subjects still have a few outliers, which matches real data
        for v in rng.sample(range(2, N_VOL + 1), 2):
            out.append((v, rng.randint(1, SLICES)))
    return sorted(out)


def write_motion(path: str, absv, rel):
    with open(path, "w", encoding="utf-8") as fh:
        for a, r in zip(absv, rel):
            fh.write("%.8f  %.8f  \n" % (a, r))


def write_outliers(path: str, outs, rng):
    with open(path, "w", encoding="utf-8") as fh:
        for sc, sl in outs:
            dev = rng.uniform(-20, -4)
            fh.write("Slice %d in scan %d is an outlier with mean %.4f standard "
                     "deviations off, and mean squared %.4f standard deviations "
                     "off.\n" % (sl, sc, dev, abs(dev) * rng.uniform(0.5, 20)))


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20261023)

    rows = []
    for sid, grp, scn in SUBJECTS:
        d = os.path.join(OUT, sid)
        os.makedirs(d, exist_ok=True)
        absv, rel = gen_motion(scn, rng)
        outs = gen_outliers(scn, rng)
        write_motion(os.path.join(d, "eddy_out.eddy_movement_rms"), absv, rel)
        write_outliers(os.path.join(d, "eddy_out.eddy_outlier_report"), outs, rng)

        n = len(absv)
        abs_mean = sum(absv) / n
        abs_max = max(absv)
        rel_mean = sum(rel) / n
        rel_max = max(rel)

        # ALPS and registration quality: different levels per scenario
        base = rng.uniform(1.44, 1.72)
        if scn == "badreg":
            r_wm = round(rng.uniform(0.86, 0.89), 3)
            alps_mean = round(base * rng.uniform(0.72, 0.82), 4)   # bad registration -> abnormal value
        else:
            r_wm = round(rng.uniform(0.972, 0.998), 3)
            alps_mean = round(base, 4)
        alps_L = round(alps_mean * rng.uniform(0.97, 1.03), 4)
        alps_R = round(alps_mean * 2 - alps_L, 4)

        rows.append({
            "subject": sid,
            "status": "ok",
            "group": grp,
            "ALPS_L": alps_L,
            "ALPS_R": alps_R,
            "ALPS_mean": alps_mean,
            "r_wm": r_wm,
            "n_L_proj": 81, "n_R_proj": 81, "n_L_asso": 81, "n_R_asso": 81,
            "rms_abs_mean": round(abs_mean, 4),
            "rms_abs_max": round(abs_max, 4),
            "rms_rel_mean": round(rel_mean, 4),
            "rms_rel_max": round(rel_max, 4),
            "n_outlier": len(outs),
            "n_vol": n,
            "method": "eddy_gpu",
            "seconds": round(rng.uniform(420, 720), 1),
            "finished_at": "2026-01-01 12:00",
        })

    csv_path = os.path.join(OUT, "demo_synthetic_summary.csv")
    cols = list(rows[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("Output directory:", OUT)
    print("Subjects:", len(rows))
    print("CSV:", csv_path)
    for r in rows:
        print("  %-10s %-7s ALPS_mean=%.4f r_wm=%.3f drift=%.3f/%.3f "
              "jitter=%.3f/%.3f outliers=%d"
              % (r["subject"], r["group"], r["ALPS_mean"], r["r_wm"],
                 r["rms_abs_mean"], r["rms_abs_max"],
                 r["rms_rel_mean"], r["rms_rel_max"], r["n_outlier"]))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""The ALPS processing pipeline -- the core module.

Terminology and citations: "the reference implementation" means the open-source
project gbarisano/alps (GitHub, commit e6f58e7, 2025-09-12, MIT License;
companion paper Liu & Barisano 2024, doi:10.14336/AD.2023.0321-2). The formal
citation, together with a comparison of "reference-implementation defaults vs.
the defaults of this tool", is given in alpsbox/citations.py; every
"consistent with the reference implementation" in this module refers to the
behavior of the commit listed above.

Full chain (every step keeps its intermediates, so a run can be resumed):

    DWI(4D) + bval + bvec + json
        |
        [1] mrdegibbs      Gibbs ringing removal (optional, requires MRtrix3)
        |
        [2] eddy --repol   eddy currents + motion + outlier slice replacement
                           (GPU first, falling back to CPU / eddy_correct)
        |
        [3] bet            b0 -> brain mask
        |
        [4] dtifit         tensor fit, --save_tensor
        |
        [5] flirt          12 DOF, FA -> JHU-ICBM-FA-1mm
        |
        [6] vecreg         ★ tensor reorientation (T' = R T R^T, Alexander 2001)
        |
        [7] fslroi         extract Dxx(0) / Dyy(3) / Dzz(5)
        |
        [8] fslstats -k    mean inside the four ROIs
        |
        [9] ALPS formula   mean(Dxx_proj, Dxx_asso) / mean(Dyy_proj, Dzz_asso)

Mathematical basis (step [6] cannot be skipped):
    A diffusion tensor is a second-order tensor, so registering it to a
    template requires reorientation as T' = R·T·Rᵀ.
    vecreg reference documentation:
      "Vector images cannot be registered by simply applying a transformation ...
       The corresponding vectors have to be reoriented accordingly
       (see D. Alexander 2001)."
    Alexander DC, Pierpaoli C, Basser PJ, Gee JC. Spatial transformations of
    diffusion tensor magnetic resonance images. IEEE Trans Med Imaging.
    2001;20(11):1131-1139. doi:10.1109/42.963816
    Tatekawa H, Matsushita S, Ueda D, Takita H, Horiuchi D, Atsukawa N, Morishita Y,
    Tsukamoto T, Shimono T, Miki Y. Improved reproducibility of diffusion tensor
    image analysis along the perivascular space (DTI-ALPS) index: an analysis of
    reorientation technique of the OASIS-3 dataset. Jpn J Radiol.
    2023;41(4):393-400. doi:10.1007/s11604-022-01370-2 (reporting that
    reorientation improved the ICC from 0.52 to 0.85)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from . import acqp as acqp_mod
from . import fsl as fslmod
from . import roi as roi_mod
from . import text_pipeline  # noqa: F401  (registers pipe.* message keys)
from .config import EnvStatus, make_env
from .i18n import t
from .inputs import DwiiInput, validate_bvec_bval


# ---------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------
@dataclass
class AlspResult:
    subject: str
    ok: bool = False
    method: str = ""            # eddy_gpu / eddy_cpu / eddy_correct / none
    reg_cost: str = ""          # registration cost function (normmi / corratio ...)
    # Full processing provenance (for reproducibility)
    bet_f: float = float("nan")  # bet brain-extraction threshold
    unring: str = ""            # on / off
    denoise: str = ""           # on / off
    template: str = ""          # registration template (basename)
    # TOPUP (dual phase encoding) provenance. Values: "on", "off (...)",
    # "skipped: <reason>", "failed", "not used (...)".
    topup: str = ""
    topup_config: str = ""      # basename of the b02b0.cnf actually used
    # T1-assisted registration (optional, for paired comparisons; the main result is unaffected)
    t1_assisted: str = ""       # ok / skip:... / error:...
    alps_t1: float = float("nan")
    r_wm_t1: float = float("nan")
    regqc_t1_range_pct: float = float("nan")
    regqc_t1_max_dev_pct: float = float("nan")
    regqc_t1_level: str = ""
    error: str = ""
    # The eight components
    dxx_L_proj: float = float("nan")
    dyy_L_proj: float = float("nan")
    dxx_L_asso: float = float("nan")
    dzz_L_asso: float = float("nan")
    dxx_R_proj: float = float("nan")
    dyy_R_proj: float = float("nan")
    dxx_R_asso: float = float("nan")
    dzz_R_asso: float = float("nan")
    # Indices
    alps_L: float = float("nan")
    alps_R: float = float("nan")
    alps_mean: float = float("nan")
    # QC
    n_roi: dict = field(default_factory=dict)
    r_wm: float = float("nan")
    n_vol: int = 0
    # eddy_movement_rms has two columns:
    #   column 1 = absolute displacement relative to the first volume (total drift)
    #   column 2 = displacement relative to the previous volume
    #              (volume-to-volume jitter, comparable to FD in fMRI)
    # The two columns mean different things; keep both, never just one.
    rms_abs_mean: float = float("nan")
    rms_abs_max: float = float("nan")
    rms_rel_mean: float = float("nan")
    rms_rel_max: float = float("nan")
    n_outlier: int = 0
    n_slice_total: int = 0
    # Registration robustness QC (optional, enabled with --regqc)
    # Perturbs the registration matrix 12 times by +/-0.5 deg and +/-0.5 mm to
    # quantify how sensitive ALPS is to registration.
    regqc_range_pct: float = float("nan")
    regqc_max_dev_pct: float = float("nan")
    regqc_level: str = ""
    # Timing
    seconds: float = 0.0

    FIELDS = ["subject", "ok", "method", "topup", "reg_cost", "bet_f",
              "unring", "denoise", "template", "topup_config",
              "alps_L", "alps_R", "alps_mean",
              "dxx_L_proj", "dyy_L_proj", "dxx_L_asso", "dzz_L_asso",
              "dxx_R_proj", "dyy_R_proj", "dxx_R_asso", "dzz_R_asso",
              "r_wm", "n_vol",
              "rms_abs_mean", "rms_abs_max", "rms_rel_mean", "rms_rel_max",
              "n_outlier", "n_slice_total",
              "regqc_range_pct", "regqc_max_dev_pct", "regqc_level",
              "t1_assisted", "alps_t1", "r_wm_t1",
              "regqc_t1_range_pct", "regqc_t1_max_dev_pct", "regqc_t1_level",
              "seconds", "error"]

    def to_row(self) -> dict:
        d = {}
        for f in self.FIELDS:
            v = getattr(self, f, "")
            if isinstance(v, float):
                v = "" if v != v else "%.6f" % v      # NaN -> empty
            d[f] = v
        for k, n in self.n_roi.items():
            d["n_roi_%s" % k] = n
        return d

    @classmethod
    def from_record(cls, rec: dict) -> "AlspResult":
        """Rebuild a result object from an alps_result.json record (used when summarizing a resumed run).

        Numbers in the JSON are stored as strings (nan becomes an empty string);
        they are converted here safely according to the field type
        (float/int/bool/str). Fields that fail to parse keep their defaults.
        """
        r = cls(subject=str(rec.get("subject", "")))
        for f in cls.FIELDS:
            if f == "subject" or f not in rec:
                continue
            raw = rec.get(f)
            if raw is None or raw == "":
                continue
            cur = getattr(r, f, "")
            try:
                if isinstance(cur, bool):
                    r.__dict__[f] = bool(raw)
                elif isinstance(cur, int):
                    r.__dict__[f] = int(float(raw))
                elif isinstance(cur, float):
                    r.__dict__[f] = float(raw)
                else:
                    r.__dict__[f] = str(raw)
            except (TypeError, ValueError):
                continue
        nro = {}
        for k, v in rec.items():
            if k.startswith("n_roi_"):
                try:
                    nro[k[len("n_roi_"):]] = int(v)
                except (TypeError, ValueError):
                    pass
        if nro:
            r.n_roi = nro
        return r

    def summary(self) -> str:
        if not self.ok:
            return "  %-18s FAILED: %s" % (self.subject, self.error[:90])
        return ("  %-18s ALPS_L=%.4f ALPS_R=%.4f mean=%.4f  [%s]  %.1fs"
                % (self.subject, self.alps_L, self.alps_R, self.alps_mean,
                   self.method, self.seconds))


# ---------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------
@dataclass
class PipelineOptions:
    radius: float = roi_mod.DEFAULT_RADIUS_MM
    unring: bool = True
    denoise: bool = False               # dwidenoise denoising (MRtrix3); off by default, see notes
    # bet -f parameter (brain-extraction threshold). 0.5 is the FSL default and
    # also what gbarisano/alps.sh uses; 0.3 is another common setting (larger
    # brain mask). The default stays at 0.5 to match common practice.
    bet_f: float = 0.5
    # flirt cost function for the FA -> template registration.
    #   normmi   = default of this tool
    #   corratio = the flirt default, and what gbarisano/alps.sh uses
    # The choice changes the registration and therefore ALPS; switch it with
    # --reg-cost.
    reg_cost: str = "normmi"
    # Structural-image assisted registration (experimental, for paired comparisons):
    #   when given, ALPS is computed a second time in the same run using the
    #   composite matrix "FA->T1 (6 DOF) -> T1->JHU-FA (12 DOF)" and stored in
    #   alps_t1 / r_wm_t1 / regqc_t1_*; the main result is unaffected.
    #   The T1 image must already be brain-extracted (bet).
    t1: Optional[str] = None
    # Precomputed "T1 -> template" affine matrix (4x4, FSL format).
    # When given, no on-the-fly T1 -> template registration is performed (direct
    # cross-modal registration is error-prone); the matrix is composed with
    # FA -> T1 instead. A composed T1 -> MNI -> template matrix is recommended.
    t1_mat: Optional[str] = None
    regqc: bool = False                 # registration robustness QC (12 perturbations, ~1-2 min each)
    use_bundled_roi: bool = True
    custom_rois: Optional[list] = None
    threads: int = 4
    template: Optional[str] = None      # default: $FSLDIR/data/atlases/JHU/JHU-ICBM-FA-1mm.nii.gz
    # TOPUP configuration file (FSL b02b0.cnf). None = search $FSLDIR
    # automatically; an explicit path lets users pick a different config.
    topup_config: Optional[str] = None
    keep_intermediate: bool = True
    force: bool = False                 # ignore existing results and re-run


class AlspPipeline:
    """Single-subject ALPS processing."""

    def __init__(self, env: EnvStatus, opts: PipelineOptions):
        self.env = env
        self.opts = opts
        self.sub_env = make_env(env, opts.threads)

    # ---------- Helpers ----------
    def _template(self) -> str:
        if self.opts.template:
            tpl = self.opts.template
        else:
            assert self.env.fsl_dir, t("pipe.fsl_dir_unset")
            tpl = os.path.join(self.env.fsl_dir, "data", "atlases",
                               "JHU", "JHU-ICBM-FA-1mm.nii.gz")
        if not os.path.isfile(tpl):
            raise FileNotFoundError(
                t("pipe.err_no_template") % tpl)
        return tpl

    # ---------- Main flow ----------
    def run(self, subject: str, dwi: DwiiInput, out_dir: str) -> AlspResult:
        t_start = time.time()
        res = AlspResult(subject=subject)
        # Record the full processing provenance (for reproducibility and cross-study comparison)
        res.reg_cost = self.opts.reg_cost
        res.bet_f = float(self.opts.bet_f)
        res.unring = "on" if self.opts.unring else "off"
        res.denoise = "on" if self.opts.denoise else "off"
        try:
            if self.opts.template:
                res.template = os.path.basename(self.opts.template)
            else:
                res.template = "default(JHU-ICBM-FA-1mm)"
        except Exception:
            res.template = ""
        # TOPUP is only attempted when a reversed phase-encoding series is
        # attached to the input; _maybe_topup() refines this status.
        res.topup = ("not applied" if getattr(dwi, "has_dual_pe", False)
                     else "off (no reversed-PE input)")
        os.makedirs(out_dir, exist_ok=True)

        # Resume: reuse an existing result unless force is set
        cached = os.path.join(out_dir, "alps_result.json")
        if os.path.isfile(cached) and not self.opts.force:
            try:
                d = json.load(open(cached, encoding="utf-8"))
                fieldcoef = os.path.join(
                    out_dir, "my_topup_results_fieldcoef.nii.gz")
                cached_topup = str(d.get("topup", "") or "")
                # A cached result produced without TOPUP must not be reused when
                # the input now carries a reversed phase-encoding series: that
                # would silently keep a single-PE result after the user enabled
                # TOPUP (e.g. after the sibling-folder pairing was fixed).
                # Results from older versions have no topup field; their TOPUP
                # output file is used as evidence.
                stale = (getattr(dwi, "has_dual_pe", False)
                         and not cached_topup.startswith("on")
                         and not os.path.isfile(fieldcoef))
                if stale:
                    print(t("pipe.topup_cached_stale"))
                else:
                    for k, v in d.items():
                        if hasattr(res, k) and k != "subject":
                            setattr(res, k, v)
                    res.subject = subject
                    res.method = str(res.method) + " (cached)"
                    if not getattr(res, "topup", ""):
                        res.topup = ("on (cached)" if os.path.isfile(fieldcoef)
                                     else "off (no reversed-PE input)")
                    return res
            except Exception:
                pass

        runner = fslmod.Runner(
            env=self.sub_env,
            workdir=out_dir,
            log_path=os.path.join(out_dir, "pipeline.log"),
            verbose=True,
        )
        try:
            self._run_body(runner, subject, dwi, out_dir, res)
            res.ok = True
        except Exception as e:
            res.ok = False
            res.error = "%s: %s" % (type(e).__name__, e)
        finally:
            runner.close()
            res.seconds = time.time() - t_start

        # Persist the result
        try:
            with open(cached, "w", encoding="utf-8") as fh:
                json.dump(res.to_row(), fh, ensure_ascii=False, indent=1)
        except Exception:
            pass
        return res

    # ---------- Pipeline steps ----------
    def _run_body(self, runner, subject, dwi: DwiiInput, out_dir: str, res: AlspResult):
        template = self._template()
        J = lambda *a: os.path.join(out_dir, *a)

        # ---- 0. Input validation ----
        for w in validate_bvec_bval(dwi):
            print(t("pipe.warn_line") % w)
        print(t("pipe.step.input"))
        print(dwi.describe())

        cur = dwi.nii
        res.n_vol = fslmod.n_volumes(runner, cur)
        print(t("pipe.n_vol") % res.n_vol)

        # ---- 0.5 Denoising (optional) ----
        # The MRtrix3 documentation requires dwidenoise to run *before*
        # mrdegibbs, because mrdegibbs changes the spatial structure of the
        # noise and invalidates the PCA estimate in dwidenoise.
        # Off by default, following the original Taoka 2017 pipeline, which did
        # not denoise; enable it with --denoise when needed.
        if self.opts.denoise:
            if not getattr(self.env, "mrtrix_has_dwidenoise", False):
                print(t("pipe.denoise_skip"))
            else:
                den = J("dwi_denoised.nii.gz")
                if not os.path.isfile(den):
                    print(t("pipe.denoise_run"))
                    runner.run(["dwidenoise", cur, den, "-nthreads",
                                str(self.opts.threads)])
                cur = den

        # ---- 1. Gibbs ringing removal ----
        if self.opts.unring:
            if not self.env.mrtrix_has_mrdegibbs:
                print(t("pipe.unring_skip_no_mrtrix"))
            else:
                unring = J("dwi_unring.nii.gz")
                if not os.path.isfile(unring):
                    print(t("pipe.unring_run"))
                    runner.run(["mrdegibbs", "-nshifts", "20", "-axes", "0,1",
                                cur, unring])
                cur = unring
        else:
            print(t("pipe.unring_skip_opt"))

        # ---- 2. Eddy current / motion correction ----
        eddy_out = J("dwi_eddy.nii.gz")
        if not os.path.isfile(eddy_out):
            print(t("pipe.eddy_run"))
            res.method = self._do_eddy(runner, dwi, cur, out_dir, res)
            cur = eddy_out
        else:
            print(t("pipe.eddy_cached"))
            m = J("method.txt")
            res.method = open(m).read().strip() if os.path.isfile(m) else "cached"

        bvec_use = J("bvec_eddy")
        if not os.path.isfile(bvec_use):
            raise RuntimeError(t("pipe.err_bvec_missing") % bvec_use)
        # bvec size check (an all-zero bvec makes dtifit fail silently)
        self._check_bvec(runner, bvec_use, cur)

        # ---- 3. Brain mask ----
        mask = J("eddy_mask.nii.gz")
        if not os.path.isfile(mask):
            print(t("pipe.step.bet"))
            b0 = J("_b0.nii.gz")
            runner.run(["fslroi", cur, b0, 0, 1], quiet=True)
            # -f 0.5 is the FSL bet default and also what gbarisano/alps.sh
            # uses (the reference implementation runs `bet2 b0 b0_brain -m`,
            # i.e. with the default F value of 0.5). Keeping 0.5 matches both
            # the FSL default and the reference implementation, which helps
            # cross-study comparison.
            runner.run(["bet", b0, J("_b0b"), "-f", "%.2f" % self.opts.bet_f, "-m"])
            runner.run(["fslmaths", J("_b0b_mask"), "-bin", mask], quiet=True)
            for fn in ("_b0.nii.gz", "_b0b.nii.gz", "_b0b_mask.nii.gz"):
                if os.path.isfile(J(fn)):
                    os.remove(J(fn))

        # ---- 4. dtifit ----
        tensor = J("dti_tensor.nii.gz")
        if not os.path.isfile(tensor):
            print(t("pipe.step.dtifit"))
            runner.run(["dtifit", "-k", cur, "-o", J("dti"), "-m", mask,
                        "-r", bvec_use, "-b", dwi.bval, "--save_tensor"])
        if not os.path.isfile(tensor):
            raise RuntimeError(t("pipe.err_no_tensor") % tensor)

        # ---- 5. FA -> template ----
        mat = J("fa2mni.mat")
        if not os.path.isfile(mat):
            print(t("pipe.step.flirt")
                  % self.opts.reg_cost)
            runner.run(["flirt", "-in", J("dti_FA.nii.gz"), "-ref", template,
                        "-omat", mat, "-out", J("FA_in_mni.nii.gz"),
                        "-dof", "12", "-cost", self.opts.reg_cost,
                        "-searchrx", "-90", "90", "-searchry", "-90", "90",
                        "-searchrz", "-90", "90"])

        # ---- 6. Tensor reorientation (critical) ----
        tensor_mni = J("tensor_mni.nii.gz")
        if not os.path.isfile(tensor_mni):
            print(t("pipe.step.vecreg"))
            runner.run(["vecreg", "-i", tensor, "-o", tensor_mni,
                        "-r", template, "-t", mat])

        # ---- 7. Diagonal components ----
        for nm, ix in (("dxx", 0), ("dyy", 3), ("dzz", 5)):
            f = J("%s_mni.nii.gz" % nm)
            if not os.path.isfile(f):
                runner.run(["fslroi", tensor_mni, f, ix, 1], quiet=True)

        # ---- 8. ROI ----
        print(t("pipe.step.roi"))
        if self.opts.custom_rois:
            roiset = roi_mod.load_custom(self.opts.custom_rois)
        elif self.opts.use_bundled_roi:
            roiset = roi_mod.load_bundled()
        else:
            roiset = roi_mod.generate_spheres(
                template, J("rois"), self.opts.radius, runner=runner)
        print(roiset.describe())

        nro = roi_mod.check_roi_sanity(runner, roiset)
        res.n_roi = nro
        bad = {k: v for k, v in nro.items() if v == 0}
        if bad:
            raise RuntimeError(t("pipe.err_roi_empty") % bad)
        print(t("pipe.roi_voxels") % nro)

        # ---- 9. Component means ----
        print(t("pipe.step.fslstats"))
        vals = {}
        for rn in roi_mod.ROI_ORDER:
            rf = roiset.get(rn)
            for nm in ("dxx", "dyy", "dzz"):
                vals[(nm, rn)] = fslmod.fslstats_masked_mean(
                    runner, J("%s_mni.nii.gz" % nm), rf)
                print("        %-8s %-8s = %.9f" % (rn, nm, vals[(nm, rn)]))

        res.dxx_L_proj = vals[("dxx", "L_proj")]
        res.dyy_L_proj = vals[("dyy", "L_proj")]
        res.dxx_L_asso = vals[("dxx", "L_asso")]
        res.dzz_L_asso = vals[("dzz", "L_asso")]
        res.dxx_R_proj = vals[("dxx", "R_proj")]
        res.dyy_R_proj = vals[("dyy", "R_proj")]
        res.dxx_R_asso = vals[("dxx", "R_asso")]
        res.dzz_R_asso = vals[("dzz", "R_asso")]

        # ---- 10. ALPS ----
        res.alps_L = self._alps(res.dxx_L_proj, res.dxx_L_asso,
                                res.dyy_L_proj, res.dzz_L_asso)
        res.alps_R = self._alps(res.dxx_R_proj, res.dxx_R_asso,
                                res.dyy_R_proj, res.dzz_R_asso)
        res.alps_mean = (res.alps_L + res.alps_R) / 2.0
        print("    [9] ALPS_L=%.6f  ALPS_R=%.6f  mean=%.6f"
              % (res.alps_L, res.alps_R, res.alps_mean))

        # ---- 10.5 Registration robustness QC (optional) ----
        if getattr(self.opts, "regqc", False):
            self._run_regqc(runner, res, out_dir, template, roiset, J)

        # ---- 10.6 T1-assisted registration (optional, paired comparison; main result unchanged) ----
        if getattr(self.opts, "t1", None):
            self._run_t1_assisted(runner, res, out_dir, template, roiset, J)

        # ---- 11. QC ----
        self._collect_qc(runner, out_dir, res, template, J)

    def _run_t1_assisted(self, runner, res, out_dir, template, roiset, J):
        """Recompute ALPS with T1-assisted registration (experimental, paired comparison).

        S2 = FA -> T1 (6 DOF) -> T1 -> JHU-FA (12 DOF); the composite matrix is
        then used for vecreg reorientation. S2 shares the whole preprocessing of
        the main result S1 (the same eddy output and tensor), so the difference
        between the two arms reflects the registration method alone.
        """
        t1 = self.opts.t1
        print(t("pipe.step.t1"))
        if not t1 or not os.path.isfile(t1):
            res.t1_assisted = "skip: T1 file not found"
            print(t("pipe.t1_skip_missing") % t1)
            return
        try:
            from .regqc import _load_mat, _mat_mul, _save_mat
        except Exception as e:
            res.t1_assisted = "error: regqc helpers %s" % e
            return

        # FA -> T1 (same subject, same session; 6 DOF is enough)
        mat_fa2t1 = J("fa2t1.mat")
        if not os.path.isfile(mat_fa2t1):
            runner.run(["flirt", "-in", J("dti_FA.nii.gz"), "-ref", t1,
                        "-omat", mat_fa2t1, "-dof", "6",
                        "-cost", self.opts.reg_cost,
                        "-searchrx", "-90", "90", "-searchry", "-90", "90",
                        "-searchrz", "-90", "90"])
        # T1 -> FA template:
        #   prefer the precomputed matrix (--t1-mat; a composed
        #   T1 -> MNI -> template matrix is recommended);
        #   otherwise run a direct cross-modal registration on the fly
        #   (error-prone, fallback only).
        mat_t12tpl = J("t12mni.mat")
        preset = getattr(self.opts, "t1_mat", None)
        if preset and os.path.isfile(preset):
            try:
                import shutil
                shutil.copyfile(preset, mat_t12tpl)
                print(t("pipe.t1_mat_preset")
                      % os.path.basename(preset))
            except Exception as e:
                res.t1_assisted = "error: copy t1_mat %s" % e
                print(t("pipe.t1_fail_copy") % e)
                return
        elif not os.path.isfile(mat_t12tpl):
            print(t("pipe.t1_warn_no_mat"))
            runner.run(["flirt", "-in", t1, "-ref", template,
                        "-omat", mat_t12tpl, "-dof", "12",
                        "-cost", self.opts.reg_cost,
                        "-searchrx", "-90", "90", "-searchry", "-90", "90",
                        "-searchrz", "-90", "90"])
        if not (os.path.isfile(mat_fa2t1) and os.path.isfile(mat_t12tpl)):
            res.t1_assisted = "error: flirt failed"
            print(t("pipe.t1_fail_flirt"))
            return

        # Compose: M = M_T1->template · M_FA->T1
        mat_comb = J("fa2mni_t1.mat")
        try:
            M1 = _load_mat(mat_fa2t1)
            M2 = _load_mat(mat_t12tpl)
            _save_mat(mat_comb, _mat_mul(M2, M1))
        except Exception as e:
            res.t1_assisted = "error: compose %s" % e
            print(t("pipe.t1_fail_compose") % e)
            return

        # Tensor reorientation (same vecreg path as S1, only the matrix differs)
        tm = J("tensor_mni_t1.nii.gz")
        if not os.path.isfile(tm):
            runner.run(["vecreg", "-i", J("dti_tensor.nii.gz"), "-o", tm,
                        "-r", template, "-t", mat_comb])
        for nm, ix in (("dxx", 0), ("dyy", 3), ("dzz", 5)):
            runner.run(["fslroi", tm, J("%s_mni_t1.nii.gz" % nm), ix, 1],
                       quiet=True)

        # ROI means + ALPS
        try:
            vals = {}
            for rn in roi_mod.ROI_ORDER:
                rf = roiset.get(rn)
                for nm in ("dxx", "dyy", "dzz"):
                    vals[(nm, rn)] = fslmod.fslstats_masked_mean(
                        runner, J("%s_mni_t1.nii.gz" % nm), rf)
            L = self._alps(vals[("dxx", "L_proj")], vals[("dxx", "L_asso")],
                           vals[("dyy", "L_proj")], vals[("dzz", "L_asso")])
            R = self._alps(vals[("dxx", "R_proj")], vals[("dxx", "R_asso")],
                           vals[("dyy", "R_proj")], vals[("dzz", "R_asso")])
            res.alps_t1 = (L + R) / 2.0
        except Exception as e:
            res.t1_assisted = "error: alps %s" % e
            print(t("pipe.t1_fail_alps") % e)
            return

        # Registration quality: FA warped by the composite matrix, correlated with the template
        try:
            fa_t1 = J("FA_in_mni_t1.nii.gz")
            runner.run(["flirt", "-in", J("dti_FA.nii.gz"), "-ref", template,
                        "-init", mat_comb, "-out", fa_t1, "-applyxfm"],
                       quiet=True)
            out = runner.capture(["fslcc", "-t", "0.2", "-p", "6",
                                  template, fa_t1])
            toks = out.split()
            if toks:
                res.r_wm_t1 = float(toks[-1])
        except Exception:
            pass

        # Robustness QC under the T1 registration (optional; shares the ROI set with the main result)
        if getattr(self.opts, "regqc", False):
            try:
                from . import regqc as regqc_mod
                roi_files = {}
                for rn in roi_mod.ROI_ORDER:
                    try:
                        roi_files[rn] = roiset.get(rn)
                    except Exception:
                        pass
                r = regqc_mod.sensitivity(
                    self.sub_env, J("dti_tensor.nii.gz"), mat_comb,
                    template, roi_files, J("regqc_t1"))
                if "error" not in r:
                    res.regqc_t1_range_pct = r["range_pct"]
                    res.regqc_t1_max_dev_pct = r["max_dev_pct"]
                    res.regqc_t1_level = r["level"]
            except Exception as e:
                print(t("pipe.t1_regqc_skip") % e)

        res.t1_assisted = "ok"
        print(t("pipe.t1_done")
              % (res.alps_t1, res.alps_mean, res.r_wm_t1))
        if res.regqc_t1_range_pct == res.regqc_t1_range_pct:
            print(t("pipe.t1_regqc")
                  % (res.regqc_t1_range_pct, res.regqc_range_pct))

    def _run_regqc(self, runner, res, out_dir, template, roiset, J):
        """Perturb the registration matrix and quantify how sensitive ALPS is to registration.

        Applying +/-0.5 deg and +/-0.5 mm perturbations to the registration
        matrix quantifies the sensitivity of ALPS to registration, which flags
        subjects whose results are particularly registration-sensitive.
        """
        print(t("pipe.step.regqc"))
        try:
            from . import regqc as regqc_mod
        except Exception as e:      # e.g. numpy missing from the interpreter (older implementations)
            print(t("pipe.regqc_skip_import") % e)
            return
        roi_files = {}
        for rn in roi_mod.ROI_ORDER:
            try:
                roi_files[rn] = roiset.get(rn)
            except Exception:
                pass
        if len(roi_files) != 4:
            print(t("pipe.regqc_skip_roi"))
            return
        try:
            r = regqc_mod.sensitivity(
                self.sub_env, J("dti_tensor.nii.gz"), J("fa2mni.mat"),
                template, roi_files, J("regqc"))
        except Exception as e:
            print(t("pipe.regqc_skip") % e)
            return
        if "error" in r:
            print(t("pipe.regqc_skip") % r["error"])
            return
        res.regqc_range_pct = r["range_pct"]
        res.regqc_max_dev_pct = r["max_dev_pct"]
        res.regqc_level = r["level"]
        print(t("pipe.regqc_base")
              % (r["base"], r["min"], r["max"]))
        print(t("pipe.regqc_summary")
              % (r["range_pct"], r["max_dev_pct"],
                 regqc_mod.level_label(r.get("level", "")), r["note"]))

    # ---------- eddy branches ----------
    def _do_eddy(self, runner, dwi: DwiiInput, cur: str, out_dir: str,
                 res: AlspResult) -> str:
        J = lambda *a: os.path.join(out_dir, *a)
        eddy_out = J("dwi_eddy.nii.gz")

        if dwi.has_eddy_metadata:
            try:
                a = acqp_mod.write_acqp_index(dwi.json_info, res.n_vol, out_dir)
                print("        acqp: %g %g %g %.9g  -> %s"
                      % (a.pe_vec[0], a.pe_vec[1], a.pe_vec[2], a.rotime,
                         os.path.basename(a.acqp_path)))
            except acqp_mod.AcqpError as e:
                print(t("pipe.acqp_warn") % e)
                print(t("pipe.acqp_fallback"))
                return self._do_eddy_correct(runner, dwi, cur, out_dir, res)

            mask = J("eddy_mask_pre.nii.gz")
            runner.run(["fslroi", cur, J("_e0.nii.gz"), 0, 1], quiet=True)
            runner.run(["bet", J("_e0.nii.gz"), J("_e0b"), "-f", "%.2f" % self.opts.bet_f, "-m"], quiet=True)
            runner.run(["fslmaths", J("_e0b_mask"), "-bin", mask], quiet=True)

            # ---- TOPUP (only when a reversed phase-encoding series is provided) ----
            topup_base = self._maybe_topup(runner, dwi, cur, out_dir, res)

            # ★ FSL eddy requires the "--key=value" form; spaces make it print usage and exit
            base = ["--imain=%s" % cur, "--mask=%s" % mask,
                    "--acqp=%s" % a.acqp_path, "--index=%s" % a.index_path,
                    "--bvecs=%s" % dwi.bvec, "--bvals=%s" % dwi.bval,
                    "--out=%s" % J("eddy_out"), "--repol"]
            if topup_base:
                base.append("--topup=%s" % topup_base)

            # Prefer the GPU build
            gpu = None
            for name in ("eddy_cuda", "eddy_cuda11.0", "eddy_cuda12.0"):
                if self.env.fsl_found.get(name):
                    gpu = name
                    break

            def _try(cmd_name, extra, tag):
                """Run eddy once; return a method tag on success."""
                argv = ([cmd_name, "diffusion"] if cmd_name != "eddy"
                        else ["eddy"]) + base + extra
                r = runner.run(argv, check=False)
                if os.path.isfile(J("eddy_out.nii.gz")):
                    self._finalize_eddy(out_dir)
                    print(t("pipe.eddy_done_tag")
                          % (tag, "".join(" " + e for e in extra)))
                    return tag
                self._report_eddy_failure(cmd_name, r)
                return None

            def _not_shelled(r):
                """Tell whether this is FSL's "Data not shelled" error.

                Multi-shell data (e.g. b=0/500/1000/3000) makes the shell
                detection in eddy fail on some FSL versions; adding
                --data_is_shelled skips the detection. The problem has been
                observed with real multi-shell data (e.g. a 4-shell acquisition
                on a UIH uMR 890).
                """
                if r is None:
                    return False
                err = ((r.stderr or "") + (r.stdout or "")).lower()
                return "not shelled" in err or "not_shelled" in err

            last_r = None
            if gpu:
                last_r = runner.run([gpu, "diffusion"] + base, check=False)
                if os.path.isfile(J("eddy_out.nii.gz")):
                    self._finalize_eddy(out_dir)
                    print(t("pipe.eddy_done_gpu") % gpu)
                    return "eddy_gpu"
                if _not_shelled(last_r):
                    print(t("pipe.eddy_not_shelled"))
                    m = _try(gpu, ["--data_is_shelled"], "eddy_gpu_shelled")
                    if m:
                        return m
                self._report_eddy_failure(gpu, last_r)
                print(t("pipe.eddy_warn_gpu_fallback") % gpu)

            last_r = runner.run(["eddy"] + base, check=False)
            if os.path.isfile(J("eddy_out.nii.gz")):
                self._finalize_eddy(out_dir)
                print(t("pipe.eddy_done_cpu"))
                return "eddy_cpu"
            if _not_shelled(last_r):
                print(t("pipe.eddy_not_shelled"))
                m = _try("eddy", ["--data_is_shelled"], "eddy_cpu_shelled")
                if m:
                    return m
            self._report_eddy_failure("eddy", last_r)

            print(t("pipe.eddy_warn_fallback"))
            print(t("pipe.eddy_correct_note"))
            return self._do_eddy_correct(runner, dwi, cur, out_dir, res)

        # No json sidecar -> eddy_correct
        print(t("pipe.eddy_no_json"))
        return self._do_eddy_correct(runner, dwi, cur, out_dir, res)

    def _maybe_topup(self, runner, dwi, cur: str, out_dir: str, res):
        """Run TOPUP for distortion correction when a reversed phase-encoding DWI exists.

        Returns the topup output prefix (for eddy --topup=), or None when TOPUP
        is not needed.

        Principle (Andersson, Skare & Ashburner 2003):
          the same brain scanned once in each of two opposite PE directions
          gives two b0 images whose geometric distortions point in opposite
          directions. topup jointly estimates an off-resonance field that
          corrects both b0 images back to the true geometry, and that field is
          then handed to eddy.

        Equivalent to the -i/-j/-k/-n options of gbarisano/alps.sh.
        """
        if not getattr(dwi, "has_dual_pe", False):
            res.topup = "off (no reversed-PE input)"
            return None
        J = lambda *a: os.path.join(out_dir, *a)
        if os.path.isfile(J("my_topup_results_fieldcoef.nii.gz")):
            print(t("pipe.topup_reuse"))
            res.topup = "on (cached)"
            return J("my_topup_results")

        ok, why = dwi.check_dual_pe()
        if not ok:
            print(t("pipe.topup_skip") % why)
            res.topup = "skipped: %s" % why
            return None

        env = self.env
        cfg = None
        explicit = getattr(self.opts, "topup_config", None)
        if explicit:
            if os.path.isfile(explicit):
                cfg = explicit
            else:
                print(t("pipe.topup_cfg_missing") % explicit)
                res.topup = "skipped: TOPUP config not found (%s)" % explicit
                return None
        else:
            for c in ("b02b0.cnf", "b02b0_1.cnf"):
                p = os.path.join(env.fsl_dir or "", "etc", "flirtsch", c)
                if os.path.isfile(p):
                    cfg = p
                    break
            if cfg is None:
                # Older FSL releases keep it under src/topup
                for root in (os.path.join(env.fsl_dir or "", "src", "topup"),
                             os.path.join(env.fsl_dir or "", "share", "fsl", "etc")):
                    if os.path.isdir(root):
                        for dirpath, _, files in os.walk(root):
                            for f in files:
                                if f.startswith("b02b0"):
                                    cfg = os.path.join(dirpath, f)
                                    break
                            if cfg:
                                break
                    if cfg:
                        break
        if cfg is None:
            print(t("pipe.topup_skip_cfg"))
            res.topup = "skipped: no b02b0.cnf found"
            return None
        res.topup_config = os.path.basename(cfg)
        if explicit:
            print(t("pipe.topup_cfg") % cfg)

        print(t("pipe.topup_start"))
        print(t("pipe.topup_pe")
              % (dwi.pe_direction, dwi.pe_direction2))

        # 1. Preprocess the second DWI identically (denoise/unring) so both noise levels match
        cur2 = dwi.nii2
        if getattr(self.opts, "denoise", False) and getattr(
                env, "mrtrix_has_dwidenoise", False):
            d2 = J("dwi2_denoised.nii.gz")
            if not os.path.isfile(d2):
                runner.run(["dwidenoise", cur2, d2, "-nthreads",
                            str(self.opts.threads)])
            cur2 = d2
        if getattr(self.opts, "unring", True) and getattr(
                env, "mrtrix_has_mrdegibbs", False):
            u2 = J("dwi2_unring.nii.gz")
            if not os.path.isfile(u2):
                runner.run(["mrdegibbs", "-nshifts", "20", "-axes", "0,1",
                            cur2, u2])
            cur2 = u2

        # 2. Take the first b0 of each series
        b0_1 = J("_topup_b0_1.nii.gz")
        b0_2 = J("_topup_b0_2.nii.gz")
        runner.run(["fslroi", cur, b0_1, "0", "1"], quiet=True)
        runner.run(["fslroi", cur2, b0_2, "0", "1"], quiet=True)

        # 3. Merge into one 4D image (topup expects both b0 groups in a single imain)
        b0s = J("_topup_b0s.nii.gz")
        runner.run(["fslmerge", "-t", b0s, b0_1, b0_2], quiet=True)

        # 4. acqparams: topup expects "x y z readout", with (x,y,z) a signed PE direction vector
        def _pe_vec(s: str):
            s = (s or "").strip()
            axis = s.rstrip("-")
            sign = -1.0 if s.endswith("-") else 1.0
            v = {"i": [1.0, 0.0, 0.0],
                 "j": [0.0, 1.0, 0.0],
                 "k": [0.0, 0.0, 1.0]}.get(axis, [0.0, 1.0, 0.0])
            return [sign * x for x in v]

        acq = J("topup_acqparams.txt")
        trt1 = float(dwi.json_info.get("TotalReadoutTime", 0.05))
        trt2 = float(dwi.json_info2.get("TotalReadoutTime", trt1))
        v1, v2 = _pe_vec(dwi.pe_direction), _pe_vec(dwi.pe_direction2)
        with open(acq, "w") as fh:
            fh.write("%.0f %.0f %.0f %.8f\n" % (v1[0], v1[1], v1[2], trt1))
            fh.write("%.0f %.0f %.0f %.8f\n" % (v2[0], v2[1], v2[2], trt2))

        # 5. topup
        pre = J("my_topup_results")
        runner.run(["topup", "--imain=%s" % b0s, "--datain=%s" % acq,
                    "--config=%s" % cfg, "--out=%s" % pre,
                    "--iout=%s" % J("my_hifi_b0.nii.gz")])
        if not os.path.isfile(pre + "_fieldcoef.nii.gz"):
            print(t("pipe.topup_fail"))
            res.topup = "failed"
            return None
        res.topup = "on"
        print(t("pipe.topup_done") % os.path.basename(pre))
        # eddy --index must refer to rows of the two datasets, but eddy uses
        # only the first one, so the index is rewritten to all 1s (pointing at
        # the first row of acqp). Note that the acqp read by eddy is still the
        # single-dataset one; TOPUP only supplies the field.
        return pre

    def _report_eddy_failure(self, name: str, r):
        """Print diagnostic information when eddy fails (instead of falling back silently)."""
        if r is None:
            return
        err = (r.stderr or "") + (r.stdout or "")
        print(t("pipe.eddy_diag_head") % (name, r.returncode))
        if "Usage:" in err or "Compulsory arguments" in err:
            print(t("pipe.eddy_diag_reason"))
        for ln in [l for l in err.splitlines() if l.strip()][:6]:
            print("        | %s" % ln[:150])
        print("        ---------------------------------")

    def _finalize_eddy(self, out_dir: str):
        J = lambda *a: os.path.join(out_dir, *a)
        if os.path.isfile(J("eddy_out.nii.gz")):
            os.replace(J("eddy_out.nii.gz"), J("dwi_eddy.nii.gz"))
        for src, dst in (("eddy_out.eddy_rotated_bvecs", "bvec_eddy"),):
            if os.path.isfile(J(src)):
                os.replace(J(src), J(dst))

    def _do_eddy_correct(self, runner, dwi, cur, out_dir, res) -> str:
        J = lambda *a: os.path.join(out_dir, *a)
        if getattr(dwi, "has_dual_pe", False) and getattr(
                res, "topup", "") in ("", "not applied"):
            res.topup = "not used (eddy_correct fallback)"
        runner.run(["eddy_correct", cur, J("dwi_ec"), "0"])
        if os.path.isfile(J("dwi_ec.nii.gz")):
            os.replace(J("dwi_ec.nii.gz"), J("dwi_eddy.nii.gz"))
        # eddy_correct does not rotate the bvecs; do it manually
        fdt = self.env.fsl_found.get("fdt_rotate_bvecs")
        if not fdt:
            raise RuntimeError(t("pipe.err_fdt_rotate"))
        runner.run(["bash", fdt, dwi.bvec, J("bvec_eddy"), J("dwi_ec.ecclog")])
        print(t("pipe.eddy_correct_done"))
        with open(J("method.txt"), "w") as fh:
            fh.write("eddy_correct")
        return "eddy_correct"

    # ---------- Validation ----------
    @staticmethod
    def _check_bvec(runner, bvec: str, dwi_eddy: str):
        """The bvec must be 3 rows x N columns and must not be all zeros."""
        lines = [ln for ln in open(bvec).read().splitlines() if ln.strip()]
        if len(lines) != 3:
            raise RuntimeError(t("pipe.err_bvec_rows") % (len(lines), bvec))
        ncol = len(lines[0].split())
        nd = fslmod.n_volumes(runner, dwi_eddy)
        if ncol != nd:
            raise RuntimeError(t("pipe.err_bvec_cols")
                               % (ncol, nd, bvec))
        total = sum(abs(float(x)) for ln in lines for x in ln.split())
        if total < 1e-6:
            raise RuntimeError(t("pipe.err_bvec_zero") % bvec)

    # ---------- ALPS formula ----------
    @staticmethod
    def _alps(dxx_proj: float, dxx_asso: float,
              dyy_proj: float, dzz_asso: float) -> float:
        """Taoka 2017 formula (matches lines 732-734 of alps.sh in gbarisano/alps)."""
        num = (dxx_proj + dxx_asso) / 2.0
        den = (dyy_proj + dzz_asso) / 2.0
        return num / den if den else float("nan")

    # ---------- QC ----------
    def _collect_qc(self, runner, out_dir: str, res: AlspResult,
                    template: str, J):
        print(t("pipe.step.qc"))
        # r_wm: correlation between FA and the template (a registration metric)
        # fslcc prints three columns: `1 1 0.944022`
        #   the first two are the indices of the compared inputs (always 1 1),
        #   and the correlation is in the *last* column.
        # Taking split()[0] would always yield 1.0, so read the last column.
        try:
            fa = J("FA_in_mni.nii.gz")
            if os.path.isfile(fa) and self.env.fsl_found.get("fslcc"):
                out = runner.capture(["fslcc", "-t", "0.2", "-p", "6",
                                      template, fa])
                toks = out.split()
                if toks:
                    res.r_wm = float(toks[-1])
        except Exception:
            pass
        # Motion and outliers: parsed by rescan so that the values match the backfill path
        from .rescan import read_motion
        st = read_motion(out_dir, res.subject)
        if st.ok:
            res.n_vol = st.n_vol
            res.rms_abs_mean = st.abs_mean
            res.rms_abs_max = st.abs_max
            res.rms_rel_mean = st.rel_mean
            res.rms_rel_max = st.rel_max
        res.n_outlier = len(st.outliers)
        res.n_slice_total = st.n_slice_total
        print(t("pipe.qc_abs")
              % (res.rms_abs_mean, res.rms_abs_max))
        print(t("pipe.qc_rel")
              % (res.rms_rel_mean, res.rms_rel_max))
        print(t("pipe.qc_outlier") % res.n_outlier)
